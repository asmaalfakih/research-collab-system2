from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from bson import ObjectId
from app.database.mongodb import mongodb
from app.database.neo4j import neo4j
from app.database.redis import redis_manager
from app.models.researcher import Researcher
from app.utils.validators import validate_email, validate_phone


class ResearcherService:
    @staticmethod
    def get_researcher_profile(researcher_id: str) -> Optional[Dict[str, Any]]:
        try:
            cached_profile = redis_manager.cache_get(f"researcher_profile:{researcher_id}")
            if cached_profile:
                return cached_profile
        except:
            pass

        researcher_data = mongodb.get_researcher(researcher_id)

        if not researcher_data:
            return None

        researcher_data['_id'] = str(researcher_data['_id'])

        projects_count = len(researcher_data.get('projects', []))
        publications_count = len(researcher_data.get('publications', []))

        collaborators = []
        with neo4j.driver.session() as session:
            result = session.run("""
                MATCH (r1:Researcher {id: $researcher_id})-[rel:CO_AUTHORED_WITH]-(r2:Researcher)
                RETURN r2.id as collaborator_id, rel.collaboration_count as collaboration_count
                ORDER BY rel.collaboration_count DESC
                LIMIT 10
            """, researcher_id=researcher_id)

            for record in result:
                collaborator_data = mongodb.get_researcher(record['collaborator_id'])
                if collaborator_data:
                    collaborators.append({
                        'id': record['collaborator_id'],
                        'name': collaborator_data['name'],
                        'collaboration_count': record['collaboration_count']
                    })

        login_count = researcher_data.get('login_count', 0)

        profile = {
            'basic_info': {
                'name': researcher_data['name'],
                'email': researcher_data['email'],
                'department': researcher_data['department'],
                'profile_status': researcher_data['profile_status'],
                'role': researcher_data['role'],
                'research_interests': researcher_data['research_interests'],
                'contact': researcher_data.get('contact', {}),
                'created_at': researcher_data['created_at'],
                'last_login': researcher_data.get('last_login'),
                'id': researcher_id
            },
            'statistics': {
                'projects_count': projects_count,
                'publications_count': publications_count,
                'collaborators_count': len(collaborators),
                'login_count': login_count
            },
            'collaborators': collaborators,
            'activity_score': len(collaborators) * 5 + projects_count * 10 + publications_count * 15
        }

        try:
            redis_manager.cache_set(f"researcher_profile:{researcher_id}", profile, 300)
        except:
            pass

        return profile

    @staticmethod
    def update_researcher_profile(researcher_id: str, update_data: Dict[str, Any]) -> Tuple[bool, str]:
        if 'email' in update_data and not validate_email(update_data['email']):
            return False, "Invalid email format"

        if 'contact' in update_data:
            contact = update_data['contact']
            if 'phone' in contact and not validate_phone(contact['phone']):
                return False, "Invalid phone number format"

        update_data['updated_at'] = datetime.utcnow()

        allowed_fields = ['name', 'email', 'department', 'research_interests', 'contact', 'bio']
        filtered_data = {k: v for k, v in update_data.items() if k in allowed_fields}

        if not filtered_data:
            return False, "No valid fields to update"

        success = mongodb.update_researcher(researcher_id, filtered_data)

        if not success:
            return False, "Failed to update profile"

        neo4j_update = {}
        if 'name' in filtered_data:
            neo4j_update['name'] = filtered_data['name']
        if 'department' in filtered_data:
            neo4j_update['department'] = filtered_data['department']

        if neo4j_update:
            with neo4j.driver.session() as session:
                session.run("""
                    MATCH (r:Researcher {id: $researcher_id})
                    SET r += $update_data
                """, researcher_id=researcher_id, update_data=neo4j_update)

        try:
            redis_manager.cache_delete(f"researcher_profile:{researcher_id}")
            redis_manager.track_activity(researcher_id, 'profile_update', {
                'fields_updated': list(filtered_data.keys()),
                'timestamp': datetime.utcnow().isoformat()
            })
        except:
            pass

        return True, "Profile updated successfully"

    @staticmethod
    def search_researchers(query: str, filters: Optional[Dict] = None, limit: int = 20) -> List[Dict[str, Any]]:
        if not filters:
            filters = {}

        search_query = {}

        if query:
            search_query['$or'] = [
                {'name': {'$regex': query, '$options': 'i'}},
                {'email': {'$regex': query, '$options': 'i'}},
                {'department': {'$regex': query, '$options': 'i'}},
                {'research_interests': {'$regex': query, '$options': 'i'}}
            ]

        if 'department' in filters:
            search_query['department'] = {'$regex': filters['department'], '$options': 'i'}

        if 'research_interests' in filters:
            search_query['research_interests'] = {'$in': [filters['research_interests']]}

        if 'profile_status' in filters:
            search_query['profile_status'] = filters['profile_status']

        search_query['profile_status'] = {'$ne': 'deleted'}

        researchers_cursor = mongodb.db.researchers.find(search_query).limit(limit)
        researchers = []

        for researcher in researchers_cursor:
            researcher['_id'] = str(researcher['_id'])

            projects_count = len(researcher.get('projects', []))
            publications_count = len(researcher.get('publications', []))

            researcher['stats'] = {
                'projects_count': projects_count,
                'publications_count': publications_count
            }

            researchers.append(researcher)

        return researchers

    @staticmethod
    def get_top_researchers(limit: int = 10) -> List[Dict[str, Any]]:
        try:
            pipeline = [
                {
                    '$match': {
                        'profile_status': {'$ne': 'deleted'}
                    }
                },
                {
                    '$lookup': {
                        'from': 'publications',
                        'localField': '_id',
                        'foreignField': 'authors.researcher_id',
                        'as': 'publications_info'
                    }
                },
                {
                    '$lookup': {
                        'from': 'projects',
                        'localField': '_id',
                        'foreignField': 'participants',
                        'as': 'projects_info'
                    }
                },
                {
                    '$project': {
                        '_id': {'$toString': '$_id'},
                        'name': 1,
                        'email': 1,
                        'department': 1,
                        'profile_status': 1,
                        'research_interests': 1,
                        'publications_count': {'$size': '$publications_info'},
                        'projects_count': {'$size': '$projects_info'},
                        'total_score': {
                            '$add': [
                                {'$multiply': [{'$size': '$publications_info'}, 3]},
                                {'$multiply': [{'$size': '$projects_info'}, 2]}
                            ]
                        }
                    }
                },
                {'$sort': {'total_score': -1}},
                {'$limit': limit}
            ]

            result = list(mongodb.db.researchers.aggregate(pipeline))
            return result
        except Exception as e:
            print(f"Error getting top researchers: {e}")
            return []

    @staticmethod
    def get_researcher_collaboration_network(researcher_id: str, depth: int = 2) -> Dict[str, Any]:
        with neo4j.driver.session() as session:
            result = session.run("""
                MATCH (start:Researcher {id: $researcher_id})
                CALL apoc.path.subgraphAll(start, {
                    relationshipFilter: "CO_AUTHORED_WITH|TEAMWORK_WITH",
                    minLevel: 1,
                    maxLevel: $depth
                })
                YIELD nodes, relationships
                RETURN nodes, relationships
            """, researcher_id=researcher_id, depth=depth)

            record = result.single()

            if not record:
                return {'nodes': [], 'connections': [], 'central_researcher': None}

            central_researcher_data = mongodb.get_researcher(researcher_id)
            central_researcher = {
                'id': researcher_id,
                'name': central_researcher_data['name'] if central_researcher_data else 'Unknown',
                'type': 'central'
            } if central_researcher_data else None

            nodes = []
            connections = []
            node_ids = set()

            for node in record['nodes']:
                node_id = node['id']
                if node_id not in node_ids:
                    node_data = mongodb.get_researcher(node_id)
                    if node_data:
                        nodes.append({
                            'id': node_id,
                            'name': node['name'],
                            'type': 'researcher',
                            'department': node_data['department'],
                            'profile_status': node_data['profile_status']
                        })
                        node_ids.add(node_id)

            for rel in record['relationships']:
                source_id = rel.start_node['id']
                target_id = rel.end_node['id']

                source_data = mongodb.get_researcher(source_id)
                target_data = mongodb.get_researcher(target_id)

                if source_data and target_data:
                    connections.append({
                        'source_id': source_id,
                        'target_id': target_id,
                        'source_name': source_data['name'],
                        'target_name': target_data['name'],
                        'type': rel.type,
                        'collaboration_count': rel['collaboration_count'] if 'collaboration_count' in rel else 1,
                        'last_collaboration': rel['last_collaboration'] if 'last_collaboration' in rel else None
                    })

        network = {
            'central_researcher': central_researcher,
            'nodes': nodes,
            'connections': connections,
            'total_nodes': len(nodes),
            'total_connections': len(connections),
            'depth': depth
        }

        return network

    @staticmethod
    def suggest_collaborators(researcher_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        researcher_data = mongodb.get_researcher(researcher_id)

        if not researcher_data:
            return []

        research_interests = researcher_data.get('research_interests', [])

        if not research_interests:
            return []

        suggestions = []

        with neo4j.driver.session() as session:
            result = session.run("""
                MATCH (r:Researcher)
                WHERE r.id <> $researcher_id 
                AND r.profile_status = 'approved'
                RETURN r.id as researcher_id, r.name as name,
                       size([interest IN $interests WHERE interest IN r.research_interests]) as common_interests_count
                ORDER BY common_interests_count DESC
                LIMIT $limit
            """, researcher_id=researcher_id, interests=research_interests, limit=limit * 2)

            for record in result:
                collaborator_id = record['researcher_id']
                common_interests = record['common_interests_count']

                has_collaborated = False
                collaboration_count = 0

                collab_result = session.run("""
                    MATCH (r1:Researcher {id: $researcher1})-[rel:CO_AUTHORED_WITH]-(r2:Researcher {id: $researcher2})
                    RETURN COUNT(rel) as has_collaboration, 
                           COALESCE(rel.collaboration_count, 0) as collaboration_count
                """, researcher1=researcher_id, researcher2=collaborator_id)

                collab_record = collab_result.single()
                if collab_record:
                    has_collaborated = collab_record['has_collaboration'] > 0
                    collaboration_count = collab_record['collaboration_count'] or 0

                suggestions.append({
                    'id': collaborator_id,
                    'name': record['name'],
                    'common_interests_count': common_interests,
                    'has_collaborated': has_collaborated,
                    'collaboration_count': collaboration_count
                })

        sorted_suggestions = sorted(
            suggestions,
            key=lambda x: (x['has_collaborated'], x['common_interests_count'], -x['collaboration_count']),
            reverse=True
        )

        return sorted_suggestions[:limit]

    @staticmethod
    def delete_researcher(researcher_id: str, admin_id: str) -> Tuple[bool, str]:
        """Simple direct delete - MongoDB only"""
        try:
            # Find researcher
            researcher = mongodb.db.researchers.find_one({'_id': ObjectId(researcher_id)})
            if not researcher:
                return False, "Researcher not found"

            if researcher.get('role') == 'admin':
                return False, "Cannot delete admin accounts"

            name = researcher.get('name', 'Unknown')
            email = researcher.get('email', '')

            # Simple soft delete
            new_email = f"{email}_DELETED_{int(datetime.utcnow().timestamp())}"

            result = mongodb.db.researchers.update_one(
                {'_id': ObjectId(researcher_id)},
                {'$set': {
                    'profile_status': 'deleted',
                    'updated_at': datetime.utcnow(),
                    'deleted_by': admin_id,
                    'deleted_at': datetime.utcnow(),
                    'old_email': email,
                    'email': new_email
                }}
            )

            if result.modified_count == 0:
                return False, "Failed to delete researcher"

            return True, f"Researcher '{name}' has been deleted"

        except Exception as e:
            return False, f"Error deleting researcher: {str(e)}"

    @staticmethod
    def cache_researcher_data(researcher_id: str, data: Dict[str, Any], ttl: int = 300):
        try:
            cache_key = f"researcher:{researcher_id}"
            redis_manager.cache_set(cache_key, data, ttl)
        except:
            pass

    @staticmethod
    def get_cached_researcher(researcher_id: str) -> Optional[Dict[str, Any]]:
        try:
            cache_key = f"researcher:{researcher_id}"
            return redis_manager.cache_get(cache_key)
        except:
            pass
        return None

    @staticmethod
    def cache_top_researchers(limit: int = 10, ttl: int = 600):
        try:
            top_researchers = ResearcherService.get_top_researchers(limit)
            cache_key = f"top_researchers:{limit}"
            redis_manager.cache_set(cache_key, top_researchers, ttl)
            return True
        except:
            pass
        return False

    @staticmethod
    def get_researcher_statistics(researcher_id: str) -> Dict[str, Any]:
        cache_key = f"researcher_stats:{researcher_id}"
        cached = redis_manager.cache_get(cache_key)
        if cached:
            return cached

        researcher_data = mongodb.get_researcher(researcher_id)
        if not researcher_data:
            return {}

        stats = {
            'projects_count': len(researcher_data.get('projects', [])),
            'publications_count': len(researcher_data.get('publications', [])),
            'profile_status': researcher_data.get('profile_status', 'pending'),
            'research_interests_count': len(researcher_data.get('research_interests', [])),
            'login_count': researcher_data.get('login_count', 0)
        }

        with neo4j.driver.session() as session:
            result = session.run("""
                MATCH (r:Researcher {id: $researcher_id})
                OPTIONAL MATCH (r)-[auth:AUTHORED]->(pub:Publication)
                OPTIONAL MATCH (r)-[part:PARTICIPATED_IN]->(p:Project)
                OPTIONAL MATCH (r)-[sup:SUPERVISES]->(sp:Project)
                OPTIONAL MATCH (r)-[coauth:CO_AUTHORED_WITH]-(collab:Researcher)
                OPTIONAL MATCH (r)-[team:TEAMWORK_WITH]-(partner:Researcher)
                RETURN COUNT(DISTINCT pub) as total_publications,
                       COUNT(DISTINCT p) as total_projects,
                       COUNT(DISTINCT sp) as supervised_projects,
                       COUNT(DISTINCT collab) as coauthors_count,
                       COUNT(DISTINCT partner) as teammates_count,
                       SUM(CASE WHEN auth.author_order = 1 THEN 1 ELSE 0 END) as first_author_count
            """, researcher_id=researcher_id)

            record = result.single()
            if record:
                stats.update({
                    'neo4j_publications': record['total_publications'],
                    'neo4j_projects': record['total_projects'],
                    'supervised_projects': record['supervised_projects'],
                    'coauthors_count': record['coauthors_count'],
                    'teammates_count': record['teammates_count'],
                    'first_author_count': record['first_author_count'] or 0
                })

        redis_manager.cache_set(cache_key, stats, 300)

        return stats

    @staticmethod
    def get_top_collaborators(researcher_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        cache_key = f"top_collaborators:{researcher_id}:{limit}"
        cached = redis_manager.cache_get(cache_key)
        if cached:
            return cached

        with neo4j.driver.session() as session:
            result = session.run("""
                MATCH (r1:Researcher {id: $researcher_id})-[rel:CO_AUTHORED_WITH]-(r2:Researcher)
                RETURN r2.id as collaborator_id, rel.collaboration_count as collaboration_count,
                       rel.publications as publications
                ORDER BY rel.collaboration_count DESC
                LIMIT $limit
            """, researcher_id=researcher_id, limit=limit)

            collaborators = []
            for record in result:
                collaborator_data = mongodb.get_researcher(record['collaborator_id'])
                if collaborator_data:
                    collaborators.append({
                        'id': record['collaborator_id'],
                        'name': collaborator_data['name'],
                        'department': collaborator_data.get('department', ''),
                        'collaboration_count': record['collaboration_count'],
                        'publications_together': len(record['publications']) if record['publications'] else 0
                    })

        redis_manager.cache_set(cache_key, collaborators, 600)

        return collaborators

    @staticmethod
    def get_activity_timeline(researcher_id: str, days: int = 30) -> List[Dict[str, Any]]:
        cache_key = f"activity_timeline:{researcher_id}:{days}"
        cached = redis_manager.cache_get(cache_key)
        if cached:
            return cached

        activities = redis_manager.get_user_activities(researcher_id, days)

        timeline = []
        for activity in activities:
            timeline.append({
                'type': activity.get('action', 'unknown'),
                'timestamp': activity.get('timestamp'),
                'details': activity.get('details', {})
            })

        timeline.sort(key=lambda x: x['timestamp'], reverse=True)

        redis_manager.cache_set(cache_key, timeline, 300)

        return timeline

    @staticmethod
    def update_researcher_status(researcher_id: str, new_status: str, updater_id: str) -> Tuple[bool, str]:
        valid_statuses = ['pending', 'approved', 'rejected', 'suspended']
        if new_status not in valid_statuses:
            return False, f"Invalid status. Must be one of: {', '.join(valid_statuses)}"

        updater_data = mongodb.get_researcher(updater_id)
        if not updater_data or updater_data.get('role') != 'admin':
            return False, "Only admin can update researcher status"

        success = mongodb.update_researcher(researcher_id, {
            'profile_status': new_status,
            'updated_at': datetime.utcnow()
        })

        if not success:
            return False, "Failed to update researcher status"

        with neo4j.driver.session() as session:
            session.run("""
                MATCH (r:Researcher {id: $researcher_id})
                SET r.profile_status = $status
            """, researcher_id=researcher_id, status=new_status)

        redis_manager.track_activity(updater_id, 'update_researcher_status', {
            'researcher_id': researcher_id,
            'new_status': new_status,
            'timestamp': datetime.utcnow().isoformat()
        })

        redis_manager.cache_delete(f"researcher_profile:{researcher_id}")
        redis_manager.cache_delete(f"researcher_stats:{researcher_id}")

        return True, f"Researcher status updated to {new_status}"

    # ====== هنا الدالة المصححة ======

    @staticmethod
    def delete_researcher_safe(researcher_identifier: str, admin_id: str) -> Tuple[bool, str]:
        """حذف آمن للباحث - يعمل مع ID أو Email"""
        try:
            print(f"[SAFE DELETE] Starting for: {researcher_identifier}")

            # 1. البحث عن الباحث
            researcher = None

            # المحاولة الأولى: البحث باستخدام ObjectId
            if ObjectId.is_valid(researcher_identifier):
                try:
                    researcher = mongodb.db.researchers.find_one(
                        {'_id': ObjectId(researcher_identifier)}
                    )
                    print(f"[SAFE DELETE] Found by ObjectId")
                except:
                    pass

            # المحاولة الثانية: البحث باستخدام Email
            if not researcher:
                researcher = mongodb.db.researchers.find_one(
                    {'email': researcher_identifier}
                )
                if researcher:
                    print(f"[SAFE DELETE] Found by email")

            # المحاولة الثالثة: البحث بالاسم (بديل)
            if not researcher:
                researchers = list(mongodb.db.researchers.find(
                    {'name': {'$regex': f'.*{researcher_identifier}.*', '$options': 'i'}}
                ).limit(1))
                if researchers:
                    researcher = researchers[0]
                    print(f"[SAFE DELETE] Found by name search")

            if not researcher:
                return False, "ERROR: Researcher not found"

            # الحصول على الـ ID الصحيح
            researcher_id = str(researcher['_id'])
            name = researcher.get('name', 'Unknown')
            email = researcher.get('email', '')
            old_status = researcher.get('profile_status', 'active')

            # التحقق إذا كان الباحث محذوفاً بالفعل
            if old_status == 'deleted':
                return False, f"WARNING: Researcher '{name}' is already deleted"

            # التحقق إذا كان المدير يحاول حذف نفسه
            if researcher_id == admin_id:
                return False, "ERROR: You cannot delete your own account"

            print(f"[SAFE DELETE] Processing: {name} ({email}) - ID: {researcher_id}")

            # 2. الحذف الناعم في MongoDB
            new_email = f"deleted_{email}_{int(datetime.utcnow().timestamp())}"

            update_result = mongodb.db.researchers.update_one(
                {'_id': ObjectId(researcher_id)},
                {'$set': {
                    'profile_status': 'deleted',
                    'email': new_email,
                    'old_email': email,
                    'updated_at': datetime.utcnow(),
                    'deleted_at': datetime.utcnow(),
                    'deleted_by': admin_id
                }}
            )

            if update_result.modified_count == 0:
                return False, "ERROR: Failed to update researcher status"

            print(f"[SAFE DELETE] MongoDB soft delete successful")

            # 3. تنظيف المشاريع
            try:
                projects_updated = mongodb.db.projects.update_many(
                    {'participants': researcher_id},
                    {'$pull': {'participants': researcher_id}}
                )
                print(f"[SAFE DELETE] Removed from {projects_updated.modified_count} projects")
            except Exception as e:
                print(f"[SAFE DELETE] Projects cleanup warning: {e}")

            # 4. تنظيف المنشورات
            try:
                publications = list(mongodb.db.publications.find({'authors.researcher_id': researcher_id}))
                for pub in publications:
                    # إزالة المؤلف من قائمة المؤلفين
                    new_authors = []
                    for author in pub.get('authors', []):
                        if isinstance(author, dict) and author.get('researcher_id') != researcher_id:
                            new_authors.append(author)

                    mongodb.db.publications.update_one(
                        {'_id': pub['_id']},
                        {'$set': {'authors': new_authors}}
                    )
                print(f"[SAFE DELETE] Removed from {len(publications)} publications")
            except Exception as e:
                print(f"[SAFE DELETE] Publications cleanup warning: {e}")

            # 5. تنظيف Neo4j (اختياري)
            if neo4j and hasattr(neo4j, 'driver') and neo4j.driver:
                try:
                    with neo4j.driver.session() as session:
                        # حذف العقدة والعلاقات
                        session.run("""
                            MATCH (r:Researcher {id: $researcher_id})
                            DETACH DELETE r
                        """, researcher_id=researcher_id)

                        print(f"[SAFE DELETE] Neo4j cleanup completed")
                except Exception as e:
                    print(f"[SAFE DELETE] Neo4j cleanup warning: {e}")
            else:
                print(f"[SAFE DELETE] Neo4j not available, skipping")

            # 6. تنظيف Redis Cache
            try:
                if redis_manager and redis_manager.is_connected():
                    # حذف جميع المفاتيح المتعلقة بالباحث
                    patterns = [
                        f"*researcher*{researcher_id}*",
                        f"*{researcher_id}*",
                        f"*{email}*",
                        f"*{name.replace(' ', '*')}*"
                    ]

                    keys_to_delete = []
                    for pattern in patterns:
                        try:
                            keys = redis_manager.client.keys(pattern)
                            keys_to_delete.extend(keys)
                        except:
                            pass

                    if keys_to_delete:
                        redis_manager.client.delete(*set(keys_to_delete))
                        print(f"[SAFE DELETE] Cleared {len(set(keys_to_delete))} cache keys")
            except Exception as e:
                print(f"[SAFE DELETE] Redis cleanup warning: {e}")

            return True, f"SUCCESS: Researcher '{name}' has been deleted successfully"

        except Exception as e:
            error_msg = f"[SAFE DELETE] ERROR: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return False, f"ERROR: System error: {str(e)}"

    # ====== الدوال المساعدة ======

    @staticmethod
    def delete_researcher_by_email(email: str, admin_id: str) -> Tuple[bool, str]:
        """حذف الباحث باستخدام الإيميل فقط"""
        return ResearcherService.delete_researcher_safe(email, admin_id)

    @staticmethod
    def delete_researcher_by_id(researcher_id: str, admin_id: str) -> Tuple[bool, str]:
        """حذف الباحث باستخدام الـ ID فقط"""
        return ResearcherService.delete_researcher_safe(researcher_id, admin_id)