from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from bson import ObjectId
from app.database.mongodb import mongodb
from app.database.neo4j import neo4j
from app.database.redis import redis_manager
from app.models.collaboration import Collaboration


class CollaborationService:
    @staticmethod
    def record_coauthorship(researcher1_id: str, researcher2_id: str, publication_id: Optional[str] = None) -> Tuple[
        bool, str]:
        researcher1_data = mongodb.get_researcher(researcher1_id)
        researcher2_data = mongodb.get_researcher(researcher2_id)

        if not researcher1_data or not researcher2_data:
            return False, "One or both researchers not found"

        if researcher1_data.get('profile_status') != 'approved' or researcher2_data.get('profile_status') != 'approved':
            return False, "Both researchers must have approved profiles"

        if publication_id:
            publication_data = mongodb.get_publication(publication_id)
            if not publication_data:
                return False, "Publication not found"

        count = neo4j.create_coauthorship(researcher1_id, researcher2_id, publication_id)

        if count == 0:
            return False, "Failed to record coauthorship"

        redis_manager.track_activity(researcher1_id, 'record_coauthorship', {
            'with_researcher_id': researcher2_id,
            'with_researcher_name': researcher2_data['name'],
            'publication_id': publication_id,
            'new_collaboration_count': count,
            'timestamp': datetime.utcnow().isoformat()
        })

        redis_manager.cache_delete_pattern(f"researcher_relationships:*")
        redis_manager.cache_delete(f"all_relationships")
        redis_manager.cache_delete(f"relationship_statistics")

        return True, f"Coauthorship recorded successfully. Total collaborations: {count}"

    @staticmethod
    def record_supervision(supervisor_id: str, student_id: str, project_id: Optional[str] = None) -> Tuple[bool, str]:
        supervisor_data = mongodb.get_researcher(supervisor_id)
        student_data = mongodb.get_researcher(student_id)

        if not supervisor_data or not student_data:
            return False, "Supervisor or student not found"

        if supervisor_data.get('profile_status') != 'approved' or student_data.get('profile_status') != 'approved':
            return False, "Both researchers must have approved profiles"

        if project_id:
            project_data = mongodb.get_project(project_id)
            if not project_data:
                return False, "Project not found"

        count = neo4j.create_supervision(supervisor_id, student_id)

        if count == 0:
            return False, "Failed to record supervision"

        redis_manager.track_activity(supervisor_id, 'record_supervision', {
            'student_id': student_id,
            'student_name': student_data['name'],
            'project_id': project_id,
            'new_collaboration_count': count,
            'timestamp': datetime.utcnow().isoformat()
        })

        redis_manager.cache_delete_pattern(f"*:{student_id}:*")
        redis_manager.cache_delete_pattern(f"*:{supervisor_id}:*")
        redis_manager.cache_delete(f"all_relationships")
        redis_manager.cache_delete(f"relationship_statistics")

        return True, f"Supervision recorded successfully. Total supervisions: {count}"

    @staticmethod
    def record_teamwork(researcher1_id: str, researcher2_id: str, project_id: Optional[str] = None) -> Tuple[bool, str]:
        researcher1_data = mongodb.get_researcher(researcher1_id)
        researcher2_data = mongodb.get_researcher(researcher2_id)

        if not researcher1_data or not researcher2_data:
            return False, "One or both researchers not found"

        if researcher1_data.get('profile_status') != 'approved' or researcher2_data.get('profile_status') != 'approved':
            return False, "Both researchers must have approved profiles"

        if project_id:
            project_data = mongodb.get_project(project_id)
            if not project_data:
                return False, "Project not found"

        count = neo4j.create_teamwork(researcher1_id, researcher2_id, project_id)

        if count == 0:
            return False, "Failed to record teamwork"

        redis_manager.track_activity(researcher1_id, 'record_teamwork', {
            'with_researcher_id': researcher2_id,
            'with_researcher_name': researcher2_data['name'],
            'project_id': project_id,
            'new_collaboration_count': count,
            'timestamp': datetime.utcnow().isoformat()
        })

        redis_manager.cache_delete_pattern(f"researcher_relationships:*")
        redis_manager.cache_delete(f"all_relationships")
        redis_manager.cache_delete(f"relationship_statistics")

        return True, f"Teamwork recorded successfully. Total teamwork collaborations: {count}"

    @staticmethod
    def record_project_participation(researcher_id: str, project_id: str, role: str = "participant") -> Tuple[
        bool, str]:
        researcher_data = mongodb.get_researcher(researcher_id)
        project_data = mongodb.get_project(project_id)

        if not researcher_data:
            return False, "Researcher not found"
        if not project_data:
            return False, "Project not found"

        if researcher_data.get('profile_status') != 'approved':
            return False, "Researcher profile must be approved"

        success = neo4j.create_project_participation(researcher_id, project_id)

        if not success:
            return False, "Failed to record project participation"

        redis_manager.track_activity(researcher_id, 'record_project_participation', {
            'project_id': project_id,
            'project_title': project_data['title'],
            'role': role,
            'timestamp': datetime.utcnow().isoformat()
        })

        redis_manager.cache_delete(f"project_details:{project_id}")
        redis_manager.cache_delete_pattern(f"researcher_relationships:*")
        redis_manager.cache_delete(f"all_relationships")

        return True, f"Project participation recorded successfully"

    @staticmethod
    def record_authorship(researcher_id: str, publication_id: str, author_order: int = 1) -> Tuple[bool, str]:
        researcher_data = mongodb.get_researcher(researcher_id)
        publication_data = mongodb.get_publication(publication_id)

        if not researcher_data:
            return False, "Researcher not found"
        if not publication_data:
            return False, "Publication not found"

        if researcher_data.get('profile_status') != 'approved':
            return False, "Researcher profile must be approved"

        success = neo4j.create_authorship(researcher_id, publication_id, author_order)

        if not success:
            return False, "Failed to record authorship"

        redis_manager.track_activity(researcher_id, 'record_authorship', {
            'publication_id': publication_id,
            'publication_title': publication_data.get('title', 'Unknown'),
            'author_order': author_order,
            'timestamp': datetime.utcnow().isoformat()
        })

        redis_manager.cache_delete(f"publication_details:{publication_id}")
        redis_manager.cache_delete_pattern(f"researcher_relationships:*")
        redis_manager.cache_delete(f"all_relationships")

        return True, f"Authorship recorded successfully"

    @staticmethod
    def record_produced_relationship(project_id: str, publication_id: str) -> Tuple[bool, str]:
        project_data = mongodb.get_project(project_id)
        publication_data = mongodb.get_publication(publication_id)

        if not project_data:
            return False, "Project not found"
        if not publication_data:
            return False, "Publication not found"

        success = neo4j.create_produced_relationship(project_id, publication_id)

        if not success:
            return False, "Failed to record produced relationship"

        redis_manager.track_activity(project_data.get('creator_id', 'system'), 'record_produced_relationship', {
            'project_id': project_id,
            'project_title': project_data.get('title', 'Unknown'),
            'publication_id': publication_id,
            'publication_title': publication_data.get('title', 'Unknown'),
            'timestamp': datetime.utcnow().isoformat()
        })

        redis_manager.cache_delete(f"project_details:{project_id}")
        redis_manager.cache_delete(f"publication_details:{publication_id}")
        redis_manager.cache_delete(f"all_relationships")

        return True, f"Produced relationship recorded successfully"

    @staticmethod
    def get_all_relationships() -> List[Dict[str, Any]]:
        cache_key = "all_relationships"
        cached = redis_manager.cache_get(cache_key)
        if cached:
            return cached

        relationships = neo4j.get_all_relationships()

        if not relationships:
            return []

        enhanced_relationships = []
        for rel in relationships:
            if rel.get('relationship_type') in ['CO_AUTHORED_WITH', 'TEAMWORK_WITH']:
                researcher1_data = mongodb.get_researcher(rel.get('researcher1_id', ''))
                researcher2_data = mongodb.get_researcher(rel.get('researcher2_id', ''))
                if researcher1_data and researcher2_data:
                    enhanced_rel = {
                        **rel,
                        'researcher1_name': researcher1_data['name'],
                        'researcher2_name': researcher2_data['name'],
                        'researcher1_email': researcher1_data['email'],
                        'researcher2_email': researcher2_data['email']
                    }
                    enhanced_relationships.append(enhanced_rel)
            elif rel.get('relationship_type') in ['SUPERVISED', 'PARTICIPATED_IN', 'AUTHORED']:
                researcher_id = rel.get('researcher_id') or rel.get('start_id')
                researcher_data = mongodb.get_researcher(researcher_id) if researcher_id else None

                if researcher_data:
                    if 'project_id' in rel:
                        project_data = mongodb.get_project(rel['project_id'])
                        if project_data:
                            enhanced_rel = {
                                **rel,
                                'researcher_name': researcher_data['name'],
                                'project_title': project_data['title']
                            }
                            enhanced_relationships.append(enhanced_rel)
                    elif 'publication_id' in rel:
                        publication_data = mongodb.get_publication(rel['publication_id'])
                        if publication_data:
                            enhanced_rel = {
                                **rel,
                                'researcher_name': researcher_data['name'],
                                'publication_title': publication_data['title'],
                                'author_order': rel.get('author_order', 1)
                            }
                            enhanced_relationships.append(enhanced_rel)
            elif rel.get('relationship_type') == 'PRODUCED':
                project_data = mongodb.get_project(rel.get('project_id', ''))
                publication_data = mongodb.get_publication(rel.get('publication_id', ''))
                if project_data and publication_data:
                    enhanced_rel = {
                        **rel,
                        'project_title': project_data['title'],
                        'publication_title': publication_data['title']
                    }
                    enhanced_relationships.append(enhanced_rel)

        redis_manager.cache_set(cache_key, enhanced_relationships, 300)
        return enhanced_relationships

    @staticmethod
    def get_relationships_by_type(relationship_type: str) -> List[Dict[str, Any]]:
        cache_key = f"relationships_by_type:{relationship_type}"
        cached = redis_manager.cache_get(cache_key)
        if cached:
            return cached

        relationships = neo4j.get_relationships_by_type(relationship_type)

        if not relationships:
            return []

        enhanced_relationships = []
        for rel in relationships:
            if relationship_type in ['CO_AUTHORED_WITH', 'TEAMWORK_WITH']:
                researcher1_data = mongodb.get_researcher(rel.get('researcher1_id', ''))
                researcher2_data = mongodb.get_researcher(rel.get('researcher2_id', ''))
                if researcher1_data and researcher2_data:
                    enhanced_rel = {
                        **rel,
                        'relationship_type': relationship_type,
                        'researcher1_name': researcher1_data['name'],
                        'researcher2_name': researcher2_data['name'],
                        'researcher1_email': researcher1_data['email'],
                        'researcher2_email': researcher2_data['email']
                    }
                    enhanced_relationships.append(enhanced_rel)
            elif relationship_type in ['SUPERVISED', 'PARTICIPATED_IN', 'AUTHORED']:
                researcher_id = rel.get('researcher_id') or rel.get('start_id')
                researcher_data = mongodb.get_researcher(researcher_id) if researcher_id else None

                if researcher_data:
                    if 'project_id' in rel:
                        project_data = mongodb.get_project(rel['project_id'])
                        if project_data:
                            enhanced_rel = {
                                **rel,
                                'relationship_type': relationship_type,
                                'researcher_name': researcher_data['name'],
                                'project_title': project_data['title']
                            }
                            enhanced_relationships.append(enhanced_rel)
                    elif 'publication_id' in rel:
                        publication_data = mongodb.get_publication(rel['publication_id'])
                        if publication_data:
                            enhanced_rel = {
                                **rel,
                                'relationship_type': relationship_type,
                                'researcher_name': researcher_data['name'],
                                'publication_title': publication_data['title'],
                                'author_order': rel.get('author_order', 1)
                            }
                            enhanced_relationships.append(enhanced_rel)
            elif relationship_type == 'PRODUCED':
                project_data = mongodb.get_project(rel.get('project_id', ''))
                publication_data = mongodb.get_publication(rel.get('publication_id', ''))
                if project_data and publication_data:
                    enhanced_rel = {
                        **rel,
                        'relationship_type': relationship_type,
                        'project_title': project_data['title'],
                        'publication_title': publication_data['title']
                    }
                    enhanced_relationships.append(enhanced_rel)

        redis_manager.cache_set(cache_key, enhanced_relationships, 300)
        return enhanced_relationships

    @staticmethod
    def get_researcher_relationships(researcher_id: str) -> List[Dict[str, Any]]:
        cache_key = f"researcher_relationships:{researcher_id}"
        cached = redis_manager.cache_get(cache_key)
        if cached:
            return cached

        relationships = neo4j.get_researcher_relationships(researcher_id)

        if not relationships:
            return []

        enhanced_relationships = []
        for rel in relationships:
            enhanced_rel = {**rel}

            if 'other_id' in rel:
                other_data = mongodb.get_researcher(rel['other_id'])
                if other_data:
                    enhanced_rel.update({
                        'other_name': other_data['name'],
                        'other_email': other_data['email'],
                        'other_department': other_data['department']
                    })

            if 'project_id' in rel:
                project_data = mongodb.get_project(rel['project_id'])
                if project_data:
                    enhanced_rel['project_title'] = project_data['title']

            if 'publication_id' in rel:
                publication_data = mongodb.get_publication(rel['publication_id'])
                if publication_data:
                    enhanced_rel['publication_title'] = publication_data['title']

            enhanced_relationships.append(enhanced_rel)

        redis_manager.cache_set(cache_key, enhanced_relationships, 300)
        return enhanced_relationships

    @staticmethod
    def get_relationship_statistics() -> Dict[str, Any]:
        cache_key = "relationship_statistics"
        cached = redis_manager.cache_get(cache_key)
        if cached:
            return cached

        total_researchers = mongodb.db.researchers.count_documents({
            'profile_status': 'approved'
        })
        total_projects = mongodb.db.projects.count_documents({})
        total_publications = mongodb.db.publications.count_documents({})

        relationship_counts = {
            'SUPERVISED': 0,
            'PARTICIPATED_IN': 0,
            'TEAMWORK_WITH': 0,
            'AUTHORED': 0,
            'CO_AUTHORED_WITH': 0,
            'PRODUCED': 0
        }

        for rel_type in relationship_counts.keys():
            relationships = CollaborationService.get_relationships_by_type(rel_type)
            relationship_counts[rel_type] = len(relationships)

        enhanced_stats = {
            'total_researchers': total_researchers,
            'total_projects': total_projects,
            'total_publications': total_publications,
            'relationship_counts': relationship_counts,
            'average_collaborations_per_researcher': sum(relationship_counts.values()) / max(1, total_researchers)
        }

        redis_manager.cache_set(cache_key, enhanced_stats, 300)
        return enhanced_stats

    @staticmethod
    def get_collaboration_network_stats():
        try:
            stats = CollaborationService.get_relationship_statistics()
            return stats
        except Exception as e:
            print(f"Error getting collaboration network stats: {e}")
            return None

    @staticmethod
    def get_most_collaborative_pairs(limit=10):
        try:
            query = """
            MATCH (r1:Researcher)-[rel:CO_AUTHORED_WITH]-(r2:Researcher)
            WHERE r1.id < r2.id
            RETURN 
                r1.id AS researcher1_id,
                r1.name AS researcher1_name,
                r2.id AS researcher2_id,
                r2.name AS researcher2_name,
                rel.collaboration_count AS collaboration_count,
                rel.publications AS publications,
                rel.last_collaboration AS last_collaboration
            ORDER BY rel.collaboration_count DESC
            LIMIT $limit
            """

            pairs = []
            with neo4j.driver.session() as session:
                result = session.run(query, limit=limit)
                for record in result:
                    pairs.append({
                        'researcher1_id': record['researcher1_id'],
                        'researcher1_name': record['researcher1_name'],
                        'researcher2_id': record['researcher2_id'],
                        'researcher2_name': record['researcher2_name'],
                        'relationship_type': 'CO_AUTHORED_WITH',
                        'collaboration_count': record['collaboration_count'],
                        'publications_count': len(record['publications']) if record['publications'] else 0,
                        'last_collaboration': record['last_collaboration']
                    })

            return pairs
        except Exception as e:
            print(f"Error getting collaborative pairs: {e}")
            return []

    @staticmethod
    def get_most_active_teams(limit=10):
        try:
            query = """
            MATCH (r1:Researcher)-[rel:TEAMWORK_WITH]-(r2:Researcher)
            WHERE r1.id < r2.id
            RETURN 
                r1.id AS researcher1_id,
                r1.name AS researcher1_name,
                r2.id AS researcher2_id,
                r2.name AS researcher2_name,
                rel.collaboration_count AS collaboration_count,
                rel.projects AS projects,
                rel.last_collaboration AS last_collaboration
            ORDER BY rel.collaboration_count DESC
            LIMIT $limit
            """

            teams = []
            with neo4j.driver.session() as session:
                result = session.run(query, limit=limit)
                for record in result:
                    teams.append({
                        'researcher1_id': record['researcher1_id'],
                        'researcher1_name': record['researcher1_name'],
                        'researcher2_id': record['researcher2_id'],
                        'researcher2_name': record['researcher2_name'],
                        'relationship_type': 'TEAMWORK_WITH',
                        'collaboration_count': record['collaboration_count'],
                        'projects_count': len(record['projects']) if record['projects'] else 0,
                        'last_collaboration': record['last_collaboration']
                    })

            return teams
        except Exception as e:
            print(f"Error getting active teams: {e}")
            return []

    @staticmethod
    def cache_collaboration_pairs(limit: int = 20, ttl: int = 600):
        try:
            pairs = CollaborationService.get_most_collaborative_pairs(limit)
            cache_key = f"collaboration_pairs:{limit}"
            redis_manager.cache_set(cache_key, pairs, ttl)

            teams = CollaborationService.get_most_active_teams(limit)
            teams_key = f"active_teams:{limit}"
            redis_manager.cache_set(teams_key, teams, ttl)

            return True
        except Exception as e:
            print(f"Error caching collaboration data: {e}")
            return False

    @staticmethod
    def get_cached_collaboration_pairs(limit: int = 20):
        try:
            cache_key = f"collaboration_pairs:{limit}"
            return redis_manager.cache_get(cache_key)
        except:
            pass
        return None

    @staticmethod
    def get_researcher_collaboration_summary(researcher_id: str) -> Dict[str, Any]:
        cache_key = f"collab_summary:{researcher_id}"
        cached = redis_manager.cache_get(cache_key)
        if cached:
            return cached

        relationships = CollaborationService.get_researcher_relationships(researcher_id)

        summary = {
            'total_relationships': len(relationships),
            'by_type': {},
            'top_collaborators': [],
            'recent_collaborations': []
        }

        for rel in relationships:
            rel_type = rel.get('relationship_type', 'UNKNOWN')
            if rel_type not in summary['by_type']:
                summary['by_type'][rel_type] = 0
            summary['by_type'][rel_type] += 1

        coauthors = [r for r in relationships if r.get('relationship_type') == 'CO_AUTHORED_WITH']
        coauthors.sort(key=lambda x: x.get('collaboration_count', 0), reverse=True)
        summary['top_collaborators'] = coauthors[:5]

        recent = [r for r in relationships if 'last_collaboration' in r and r['last_collaboration']]
        recent.sort(key=lambda x: x['last_collaboration'], reverse=True)
        summary['recent_collaborations'] = recent[:5]

        redis_manager.cache_set(cache_key, summary, 300)

        return summary

    @staticmethod
    def delete_relationship(relationship_type: str, relationship_data: Dict[str, Any], deleter_id: str) -> Tuple[
        bool, str]:
        try:
            if relationship_type == 'CO_AUTHORED_WITH':
                if 'researcher1_id' in relationship_data and 'researcher2_id' in relationship_data:
                    with neo4j.driver.session() as session:
                        result = session.run("""
                            MATCH (r1:Researcher {id: $id1})-[rel:CO_AUTHORED_WITH]-(r2:Researcher {id: $id2})
                            DELETE rel
                            RETURN count(rel) as deleted
                        """, id1=relationship_data['researcher1_id'], id2=relationship_data['researcher2_id'])

                        record = result.single()
                        if record and record['deleted'] > 0:
                            redis_manager.track_activity(deleter_id, 'delete_relationship', {
                                'relationship_type': relationship_type,
                                'relationship_data': relationship_data,
                                'timestamp': datetime.utcnow().isoformat()
                            })
                            redis_manager.cache_delete_pattern("*")
                            return True, "Coauthorship relationship deleted"

            elif relationship_type == 'SUPERVISED':
                if 'supervisor_id' in relationship_data and 'student_id' in relationship_data:
                    with neo4j.driver.session() as session:
                        result = session.run("""
                            MATCH (supervisor:Researcher {id: $supervisor_id})-[rel:SUPERVISED]->(student:Researcher {id: $student_id})
                            DELETE rel
                            RETURN count(rel) as deleted
                        """, supervisor_id=relationship_data['supervisor_id'],
                                             student_id=relationship_data['student_id'])

                        record = result.single()
                        if record and record['deleted'] > 0:
                            redis_manager.track_activity(deleter_id, 'delete_relationship', {
                                'relationship_type': relationship_type,
                                'relationship_data': relationship_data,
                                'timestamp': datetime.utcnow().isoformat()
                            })
                            redis_manager.cache_delete_pattern("*")
                            return True, "Supervision relationship deleted"

            elif relationship_type == 'TEAMWORK_WITH':
                if 'researcher1_id' in relationship_data and 'researcher2_id' in relationship_data:
                    with neo4j.driver.session() as session:
                        result = session.run("""
                            MATCH (r1:Researcher {id: $id1})-[rel:TEAMWORK_WITH]-(r2:Researcher {id: $id2})
                            DELETE rel
                            RETURN count(rel) as deleted
                        """, id1=relationship_data['researcher1_id'], id2=relationship_data['researcher2_id'])

                        record = result.single()
                        if record and record['deleted'] > 0:
                            redis_manager.track_activity(deleter_id, 'delete_relationship', {
                                'relationship_type': relationship_type,
                                'relationship_data': relationship_data,
                                'timestamp': datetime.utcnow().isoformat()
                            })
                            redis_manager.cache_delete_pattern("*")
                            return True, "Teamwork relationship deleted"

            elif relationship_type == 'PARTICIPATED_IN':
                if 'researcher_id' in relationship_data and 'project_id' in relationship_data:
                    with neo4j.driver.session() as session:
                        result = session.run("""
                            MATCH (r:Researcher {id: $researcher_id})-[rel:PARTICIPATED_IN]->(p:Project {id: $project_id})
                            DELETE rel
                            RETURN count(rel) as deleted
                        """, researcher_id=relationship_data['researcher_id'],
                                             project_id=relationship_data['project_id'])

                        record = result.single()
                        if record and record['deleted'] > 0:
                            redis_manager.track_activity(deleter_id, 'delete_relationship', {
                                'relationship_type': relationship_type,
                                'relationship_data': relationship_data,
                                'timestamp': datetime.utcnow().isoformat()
                            })
                            redis_manager.cache_delete_pattern("*")
                            return True, "Project participation deleted"

            elif relationship_type == 'AUTHORED':
                if 'researcher_id' in relationship_data and 'publication_id' in relationship_data:
                    with neo4j.driver.session() as session:
                        result = session.run("""
                            MATCH (r:Researcher {id: $researcher_id})-[rel:AUTHORED]->(pub:Publication {id: $publication_id})
                            DELETE rel
                            RETURN count(rel) as deleted
                        """, researcher_id=relationship_data['researcher_id'],
                                             publication_id=relationship_data['publication_id'])

                        record = result.single()
                        if record and record['deleted'] > 0:
                            redis_manager.track_activity(deleter_id, 'delete_relationship', {
                                'relationship_type': relationship_type,
                                'relationship_data': relationship_data,
                                'timestamp': datetime.utcnow().isoformat()
                            })
                            redis_manager.cache_delete_pattern("*")
                            return True, "Authorship relationship deleted"

            elif relationship_type == 'PRODUCED':
                if 'project_id' in relationship_data and 'publication_id' in relationship_data:
                    with neo4j.driver.session() as session:
                        result = session.run("""
                            MATCH (p:Project {id: $project_id})-[rel:PRODUCED]->(pub:Publication {id: $publication_id})
                            DELETE rel
                            RETURN count(rel) as deleted
                        """, project_id=relationship_data['project_id'],
                                             publication_id=relationship_data['publication_id'])

                        record = result.single()
                        if record and record['deleted'] > 0:
                            redis_manager.track_activity(deleter_id, 'delete_relationship', {
                                'relationship_type': relationship_type,
                                'relationship_data': relationship_data,
                                'timestamp': datetime.utcnow().isoformat()
                            })
                            redis_manager.cache_delete_pattern("*")
                            return True, "Produced relationship deleted"

            else:
                return False, f"Unknown relationship type: {relationship_type}"

            return False, f"Failed to delete {relationship_type} relationship"

        except Exception as e:
            print(f"Error deleting relationship: {e}")
            return False, f"Error deleting relationship: {e}"

    @staticmethod
    def get_six_relationships_summary() -> Dict[str, Any]:
        try:
            total_researchers = mongodb.db.researchers.count_documents({
                'profile_status': 'approved'
            })
            total_projects = mongodb.db.projects.count_documents({})
            total_publications = mongodb.db.publications.count_documents({})

            relationship_counts = {
                'CO_AUTHORED_WITH': 0,
                'SUPERVISED': 0,
                'TEAMWORK_WITH': 0,
                'PARTICIPATED_IN': 0,
                'AUTHORED': 0,
                'PRODUCED': 0
            }

            with neo4j.driver.session() as session:
                for rel_type in relationship_counts.keys():
                    result = session.run(f"""
                        MATCH ()-[r:{rel_type}]-()
                        RETURN count(r) as count
                    """)
                    record = result.single()
                    if record:
                        relationship_counts[rel_type] = record['count']

            relationships_defined = [
                {
                    'name': 'CO_AUTHORED_WITH',
                    'description': 'Researcher co-authored with another researcher',
                    'count': relationship_counts.get('CO_AUTHORED_WITH', 0)
                },
                {
                    'name': 'SUPERVISED',
                    'description': 'Researcher supervised another researcher',
                    'count': relationship_counts.get('SUPERVISED', 0)
                },
                {
                    'name': 'TEAMWORK_WITH',
                    'description': 'Researcher worked with another researcher on project',
                    'count': relationship_counts.get('TEAMWORK_WITH', 0)
                },
                {
                    'name': 'PARTICIPATED_IN',
                    'description': 'Researcher participated in project',
                    'count': relationship_counts.get('PARTICIPATED_IN', 0)
                },
                {
                    'name': 'AUTHORED',
                    'description': 'Researcher authored publication',
                    'count': relationship_counts.get('AUTHORED', 0)
                },
                {
                    'name': 'PRODUCED',
                    'description': 'Project produced publication',
                    'count': relationship_counts.get('PRODUCED', 0)
                }
            ]

            summary = {
                'relationship_counts': relationship_counts,
                'entity_counts': {
                    'researchers': total_researchers,
                    'projects': total_projects,
                    'publications': total_publications
                },
                'relationships_defined': relationships_defined,
                'total_relationships': sum(relationship_counts.values()),
                'has_six_relationships': len(relationships_defined) == 6
            }

            return summary

        except Exception as e:
            print(f"Error getting relationships summary: {e}")
            return {}