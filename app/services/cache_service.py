from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from bson import ObjectId
from app.database.mongodb import mongodb
from app.database.neo4j import neo4j
from app.database.redis import redis_manager
from app.models.project import Project
from app.models.collaboration import CollaborationType


class ProjectService:
    @staticmethod
    def create_project(creator_id: str, project_data: Dict[str, Any]) -> Tuple[bool, str, Optional[str]]:
        """Create new project - FIXED VERSION"""
        print(f"[DEBUG] Creating project for creator: {creator_id}")
        print(f"[DEBUG] Project data: {project_data.get('title', 'No title')}")

        # Validate required fields
        required_fields = ['title', 'description']
        for field in required_fields:
            if field not in project_data or not project_data[field]:
                return False, None, f"Missing required field: {field}"

        # Get creator info
        creator_data = mongodb.get_researcher(creator_id)
        if not creator_data:
            return False, None, "Creator not found"

        if creator_data.get('profile_status') != 'approved':
            return False, None, "Researcher profile not approved"

        # Prepare project data
        project_data['creator_id'] = creator_id
        project_data['creator_name'] = creator_data['name']

        # Ensure participants list exists and includes creator
        participants = project_data.get('participants', [])
        if creator_id not in participants:
            participants.append(creator_id)
        project_data['participants'] = participants

        # Set defaults
        project_data.setdefault('status', 'active')
        project_data.setdefault('start_date', datetime.utcnow().date().isoformat())
        project_data.setdefault('research_area', 'General Research')
        project_data.setdefault('tags', [])
        project_data.setdefault('budget', 0.0)
        project_data.setdefault('funding_source', '')
        project_data.setdefault('related_publications', [])
        project_data.setdefault('created_at', datetime.utcnow())
        project_data.setdefault('updated_at', datetime.utcnow())

        print(f"[DEBUG] Prepared project data with {len(participants)} participants")

        try:
            # Create in MongoDB
            project_dict = project_data.copy()
            result = mongodb.db.projects.insert_one(project_dict)
            project_id = str(result.inserted_id)

            print(f"[DEBUG] MongoDB project created: {project_id}")

            # Update creator's projects list
            mongodb.update_researcher(creator_id, {
                '$push': {'projects': project_id}
            })
            print(f"[DEBUG] Updated creator's projects list")

            # Create Neo4j node if driver exists
            from app.database.neo4j import neo4j
            if neo4j.driver:
                try:
                    neo4j.create_project_node({
                        'id': project_id,
                        'title': project_data['title'],
                        'creator_id': creator_id,
                        'status': project_data['status']
                    })
                    print(f"[DEBUG] Neo4j project node created")

                    # Create participation relationship for creator
                    neo4j.create_project_participation(creator_id, project_id)
                    print(f"[DEBUG] Neo4j participation relationship created")
                except Exception as e:
                    print(f"[DEBUG] Neo4j creation warning: {e}")
                    # Continue even if Neo4j fails

            # Add other participants
            for participant_id in participants:
                if participant_id != creator_id:
                    try:
                        mongodb.update_researcher(participant_id, {
                            '$push': {'projects': project_id}
                        })

                        if neo4j.driver:
                            neo4j.create_project_participation(participant_id, project_id)

                        print(f"[DEBUG] Added participant: {participant_id}")
                    except Exception as e:
                        print(f"[DEBUG] Warning adding participant {participant_id}: {e}")

            # Track activity
            from app.database.redis import redis_manager
            try:
                redis_manager.track_activity(creator_id, 'create_project', {
                    'project_id': project_id,
                    'project_title': project_data['title'],
                    'timestamp': datetime.utcnow().isoformat()
                })
            except:
                pass

            print(f"[DEBUG] Project creation completed successfully")
            return True, project_id, "Project created successfully"

        except Exception as e:
            print(f"[ERROR] Project creation failed: {e}")
            import traceback
            traceback.print_exc()
            return False, None, f"Error creating project: {str(e)}"

    @staticmethod
    def get_project_details(project_id: str) -> Optional[Dict[str, Any]]:
        cache_key = f"project_details:{project_id}"
        cached = redis_manager.cache_get(cache_key)
        if cached:
            return cached

        project_data = mongodb.get_project(project_id)

        if not project_data:
            return None

        project_data['_id'] = str(project_data['_id'])

        participants_details = []
        for participant_id in project_data.get('participants', []):
            researcher_data = mongodb.get_researcher(participant_id)
            if researcher_data:
                researcher_data['_id'] = str(researcher_data['_id'])

                with neo4j.driver.session() as session:
                    result = session.run("""
                        MATCH (r:Researcher {id: $researcher_id})-[rel:PARTICIPATED_IN]->(p:Project {id: $project_id})
                        RETURN rel.role as role, rel.joined_at as joined_at
                    """, researcher_id=participant_id, project_id=project_id)

                    record = result.single()
                    role = 'participant'
                    joined_at = None
                    if record:
                        role = record['role'] or 'participant'
                        joined_at = record['joined_at']

                participants_details.append({
                    'id': participant_id,
                    'name': researcher_data['name'],
                    'email': researcher_data['email'],
                    'department': researcher_data['department'],
                    'role': role,
                    'joined_at': joined_at,
                    'profile_status': researcher_data.get('profile_status', 'pending')
                })

        publications_details = []
        for pub_id in project_data.get('related_publications', []):
            pub_data = mongodb.get_publication(pub_id)
            if pub_data:
                pub_data['_id'] = str(pub_data['_id'])
                publications_details.append({
                    'id': pub_id,
                    'title': pub_data.get('title', 'Unknown'),
                    'year': pub_data.get('year', 'Unknown'),
                    'journal': pub_data.get('journal', 'Unknown')
                })

        supervisor_info = None
        with neo4j.driver.session() as session:
            result = session.run("""
                MATCH (r:Researcher)-[rel:SUPERVISES]->(p:Project {id: $project_id})
                RETURN r.id as supervisor_id
            """, project_id=project_id)

            record = result.single()
            if record:
                supervisor_id = record['supervisor_id']
                supervisor_data = mongodb.get_researcher(supervisor_id)
                if supervisor_data:
                    supervisor_info = {
                        'id': supervisor_id,
                        'name': supervisor_data['name'],
                        'email': supervisor_data['email']
                    }

        collaboration_network = []
        with neo4j.driver.session() as session:
            result = session.run("""
                MATCH (r1:Researcher)-[rel:TEAMWORK_WITH]-(r2:Researcher)
                WHERE $project_id IN rel.projects
                RETURN r1.id as researcher1_id, r2.id as researcher2_id, 
                       rel.collaboration_count as collaboration_count,
                       rel.last_collaboration as last_collaboration
            """, project_id=project_id)

            for record in result:
                collaboration_network.append({
                    'researcher1_id': record['researcher1_id'],
                    'researcher2_id': record['researcher2_id'],
                    'collaboration_count': record['collaboration_count'],
                    'last_collaboration': record['last_collaboration']
                })

        project_details = {
            'project_info': project_data,
            'participants': participants_details,
            'publications': publications_details,
            'supervisor': supervisor_info,
            'collaboration_network': collaboration_network,
            'participants_count': len(participants_details),
            'publications_count': len(publications_details)
        }

        redis_manager.cache_set(cache_key, project_details, 600)

        return project_details

    @staticmethod
    def add_participant_to_project(project_id: str, researcher_id: str, adder_id: str) -> Tuple[bool, str]:
        project_data = mongodb.get_project(project_id)
        if not project_data:
            return False, "Project not found"

        researcher_data = mongodb.get_researcher(researcher_id)
        if not researcher_data:
            return False, "Researcher not found"

        if researcher_data.get('profile_status') != 'approved':
            return False, "Researcher profile not approved"

        adder_data = mongodb.get_researcher(adder_id)
        if not adder_data:
            return False, "Adder not found"

        if adder_id != project_data['creator_id'] and adder_data.get('role') != 'admin':
            return False, "Only project creator or admin can add participants"

        if researcher_id in project_data.get('participants', []):
            return False, "Researcher is already a participant"

        success = mongodb.add_project_participant(project_id, researcher_id)

        if not success:
            return False, "Failed to add participant"

        mongodb.update_researcher(researcher_id, {
            '$push': {'projects': project_id}
        })

        neo4j.create_participation_relationship(researcher_id, project_id)

        current_participants = project_data.get('participants', []) + [researcher_id]
        for participant_id in current_participants:
            if participant_id != researcher_id:
                neo4j.create_teamwork_relationship(researcher_id, participant_id, project_id)

        redis_manager.track_activity(adder_id, 'add_project_participant', {
            'project_id': project_id,
            'added_researcher_id': researcher_id,
            'added_researcher_name': researcher_data['name'],
            'timestamp': datetime.utcnow().isoformat()
        })

        redis_manager.cache_delete(f"project_details:{project_id}")

        return True, f"Researcher {researcher_data['name']} added to project"

    @staticmethod
    def remove_participant_from_project(project_id: str, researcher_id: str, remover_id: str) -> Tuple[bool, str]:
        project_data = mongodb.get_project(project_id)
        if not project_data:
            return False, "Project not found"

        if researcher_id == project_data['creator_id']:
            return False, "Cannot remove project creator"

        remover_data = mongodb.get_researcher(remover_id)
        if not remover_data:
            return False, "Remover not found"

        if remover_id != project_data['creator_id'] and remover_data.get('role') != 'admin':
            return False, "Only project creator or admin can remove participants"

        if researcher_id not in project_data.get('participants', []):
            return False, "Researcher is not a participant"

        success = mongodb.remove_project_participant(project_id, researcher_id)

        if not success:
            return False, "Failed to remove participant"

        mongodb.update_researcher(researcher_id, {
            '$pull': {'projects': project_id}
        })

        with neo4j.driver.session() as session:
            session.run("""
                MATCH (r:Researcher {id: $researcher_id})-[rel:PARTICIPATED_IN]->(p:Project {id: $project_id})
                DELETE rel
            """, researcher_id=researcher_id, project_id=project_id)

        redis_manager.track_activity(remover_id, 'remove_project_participant', {
            'project_id': project_id,
            'removed_researcher_id': researcher_id,
            'timestamp': datetime.utcnow().isoformat()
        })

        redis_manager.cache_delete(f"project_details:{project_id}")

        return True, "Participant removed from project"

    @staticmethod
    def get_projects_by_researcher(researcher_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        query = {'participants': researcher_id}
        if status:
            query['status'] = status

        projects_cursor = mongodb.db.projects.find(query).sort('created_at', -1)
        projects = []

        for project in projects_cursor:
            project['_id'] = str(project['_id'])

            project['participants_count'] = len(project.get('participants', []))

            is_supervisor = False
            with neo4j.driver.session() as session:
                result = session.run("""
                    MATCH (r:Researcher {id: $researcher_id})-[rel:SUPERVISES]->(p:Project {id: $project_id})
                    RETURN COUNT(rel) as is_supervisor
                """, researcher_id=researcher_id, project_id=str(project['_id']))

                record = result.single()
                is_supervisor = record['is_supervisor'] > 0 if record else False

            if project['creator_id'] == researcher_id:
                project['user_role'] = 'creator'
            elif is_supervisor:
                project['user_role'] = 'supervisor'
            else:
                with neo4j.driver.session() as session:
                    result = session.run("""
                        MATCH (r:Researcher {id: $researcher_id})-[rel:PARTICIPATED_IN]->(p:Project {id: $project_id})
                        RETURN rel.role as role
                    """, researcher_id=researcher_id, project_id=str(project['_id']))

                    record = result.single()
                    project['user_role'] = record['role'] if record else 'participant'

            projects.append(project)

        return projects

    @staticmethod
    def search_projects(query: str, filters: Optional[Dict] = None, limit: int = 20) -> List[Dict[str, Any]]:
        if not filters:
            filters = {}

        search_query = {}

        if query:
            search_query['$or'] = [
                {'title': {'$regex': query, '$options': 'i'}},
                {'description': {'$regex': query, '$options': 'i'}},
                {'research_area': {'$regex': query, '$options': 'i'}},
                {'tags': {'$regex': query, '$options': 'i'}}
            ]

        if 'status' in filters:
            search_query['status'] = filters['status']

        if 'research_area' in filters:
            search_query['research_area'] = {'$regex': filters['research_area'], '$options': 'i'}

        if 'start_date_from' in filters:
            search_query['start_date'] = {'$gte': filters['start_date_from']}

        if 'start_date_to' in filters:
            if 'start_date' not in search_query:
                search_query['start_date'] = {}
            search_query['start_date']['$lte'] = filters['start_date_to']

        if 'creator_id' in filters:
            search_query['creator_id'] = filters['creator_id']

        projects_cursor = mongodb.db.projects.find(search_query).sort('created_at', -1).limit(limit)
        projects = []

        for project in projects_cursor:
            project['_id'] = str(project['_id'])
            project['participants_count'] = len(project.get('participants', []))

            with neo4j.driver.session() as session:
                result = session.run("""
                    MATCH (p:Project {id: $project_id})
                    OPTIONAL MATCH (pub:Publication)<-[:PRODUCED]-(p)
                    RETURN COUNT(pub) as publication_count
                """, project_id=str(project['_id']))

                record = result.single()
                project['publication_count'] = record['publication_count'] if record else 0

            projects.append(project)

        return projects

    @staticmethod
    def update_project_status(project_id: str, new_status: str, updater_id: str) -> Tuple[bool, str]:
        valid_statuses = ['active', 'completed', 'pending', 'cancelled']
        if new_status not in valid_statuses:
            return False, f"Invalid status. Must be one of: {', '.join(valid_statuses)}"

        success = mongodb.update_project(project_id, {
            'status': new_status,
            'updated_at': datetime.utcnow()
        })

        if not success:
            return False, "Failed to update project status"

        neo4j.update_project_status(project_id, new_status)

        redis_manager.track_activity(updater_id, 'update_project_status', {
            'project_id': project_id,
            'new_status': new_status,
            'timestamp': datetime.utcnow().isoformat()
        })

        redis_manager.cache_delete(f"project_details:{project_id}")

        return True, f"Project status updated to {new_status}"

    @staticmethod
    def delete_project(project_id: str, deleter_id: str) -> Tuple[bool, str]:
        try:
            project_data = mongodb.get_project(project_id)
            if not project_data:
                return False, "Project not found"

            if deleter_id != project_data['creator_id']:
                deleter_data = mongodb.get_researcher(deleter_id)
                if not deleter_data or deleter_data.get('role') != 'admin':
                    return False, "Only project creator or admin can delete project"

            with neo4j.driver.session() as session:
                session.run("""
                    MATCH (p:Project {id: $project_id})-[rel]-()
                    DELETE rel
                """, project_id=project_id)

                session.run("""
                    MATCH (p:Project {id: $project_id})
                    DELETE p
                """, project_id=project_id)

            result = mongodb.db.projects.delete_one({'_id': ObjectId(project_id)})

            if result.deleted_count > 0:
                for participant_id in project_data.get('participants', []):
                    mongodb.update_researcher(participant_id, {
                        '$pull': {'projects': project_id}
                    })

                redis_manager.track_activity(deleter_id, 'delete_project', {
                    'project_id': project_id,
                    'project_title': project_data.get('title', 'Unknown'),
                    'timestamp': datetime.utcnow().isoformat()
                })

                redis_manager.cache_delete(f"project_details:{project_id}")

                return True, "Project deleted successfully"
            else:
                return False, "Failed to delete project"
        except Exception as e:
            print(f"Error deleting project: {e}")
            return False, f"Error deleting project: {e}"

    @staticmethod
    def link_publication_to_project(project_id: str, publication_id: str, linker_id: str) -> Tuple[bool, str]:
        project_data = mongodb.get_project(project_id)
        if not project_data:
            return False, "Project not found"

        publication_data = mongodb.get_publication(publication_id)
        if not publication_data:
            return False, "Publication not found"

        if linker_id not in project_data.get('participants', []):
            linker_data = mongodb.get_researcher(linker_id)
            if not linker_data or linker_data.get('role') != 'admin':
                return False, "Only project participants or admin can link publications"

        success = mongodb.update_project(project_id, {
            '$addToSet': {'related_publications': publication_id}
        })

        if not success:
            return False, "Failed to link publication"

        neo4j.create_produced_relationship(project_id, publication_id)

        redis_manager.track_activity(linker_id, 'link_publication_to_project', {
            'project_id': project_id,
            'publication_id': publication_id,
            'timestamp': datetime.utcnow().isoformat()
        })

        redis_manager.cache_delete(f"project_details:{project_id}")

        return True, "Publication linked to project"

    @staticmethod
    def get_project_statistics(project_id: str) -> Dict[str, Any]:
        cache_key = f"project_stats:{project_id}"
        cached = redis_manager.cache_get(cache_key)
        if cached:
            return cached

        project_data = mongodb.get_project(project_id)
        if not project_data:
            return {}

        stats = {
            'participants_count': len(project_data.get('participants', [])),
            'publications_count': len(project_data.get('related_publications', [])),
            'status': project_data.get('status', 'unknown'),
            'duration_days': 0
        }

        try:
            start_date = datetime.strptime(project_data.get('start_date', ''), '%Y-%m-%d').date()
            end_date_str = project_data.get('end_date')
            if end_date_str:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                stats['duration_days'] = (end_date - start_date).days
            else:
                stats['duration_days'] = (datetime.utcnow().date() - start_date).days
        except:
            pass

        with neo4j.driver.session() as session:
            result = session.run("""
                MATCH (p:Project {id: $project_id})
                OPTIONAL MATCH (p)-[:PRODUCED]->(pub:Publication)
                RETURN COUNT(DISTINCT pub) as neo4j_publication_count
            """, project_id=project_id)

            record = result.single()
            if record:
                stats['neo4j_publication_count'] = record['neo4j_publication_count']

        redis_manager.cache_set(cache_key, stats, 300)

        return stats