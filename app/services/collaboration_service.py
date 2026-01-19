from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from bson import ObjectId
from app.database import mongodb_cluster, neo4j_cluster, redis_cluster
from app.models.collaboration import Collaboration
from app.services.cluster_service import ClusterService


class CollaborationService:
    """Service for managing collaborations with cluster support"""

    @staticmethod
    def record_coauthorship(researcher1_id: str, researcher2_id: str, publication_id: Optional[str] = None) -> Tuple[
        bool, str]:
        """Record coauthorship across clusters"""
        # Verify researchers exist
        researcher1_data = mongodb_cluster.get_researcher(researcher1_id)
        researcher2_data = mongodb_cluster.get_researcher(researcher2_id)

        if not researcher1_data or not researcher2_data:
            return False, "One or both researchers not found"

        try:
            # Record in Neo4j cluster
            count = neo4j_cluster.create_coauthorship(researcher1_id, researcher2_id, publication_id)

            if count == 0:
                return False, "Failed to record coauthorship in graph"

            # Also store in MongoDB for analytics
            collaboration_data = {
                'researcher1_id': researcher1_id,
                'researcher2_id': researcher2_id,
                'type': 'CO_AUTHORED_WITH',
                'count': count,
                'publication_id': publication_id,
                'recorded_at': datetime.utcnow(),
                'cluster_recorded': True
            }

            mongodb_cluster.db.collaborations.update_one(
                {
                    'researcher1_id': researcher1_id,
                    'researcher2_id': researcher2_id,
                    'type': 'CO_AUTHORED_WITH'
                },
                {'$set': collaboration_data},
                upsert=True
            )

            # Clear relevant caches
            cache_patterns = [
                'all_relationships',
                'relationships_by_type:CO_AUTHORED_WITH',
                f'researcher_relationships:{researcher1_id}',
                f'researcher_relationships:{researcher2_id}',
                'relationship_statistics',
                f'researcher_profile:{researcher1_id}',
                f'researcher_profile:{researcher2_id}'
            ]

            for pattern in cache_patterns:
                redis_cluster.cache_delete(pattern)

            # Log activity
            redis_cluster.track_activity(researcher1_id, 'record_coauthorship', {
                'with_researcher_id': researcher2_id,
                'with_researcher_name': researcher2_data['name'],
                'publication_id': publication_id,
                'new_collaboration_count': count,
                'timestamp': datetime.utcnow().isoformat(),
                'cluster_operation': True
            })

            return True, f"Coauthorship recorded successfully. Total collaborations: {count}"

        except Exception as e:
            failure_response = ClusterService.handle_cluster_failure(
                'neo4j', 'record_coauthorship', e
            )
            return False, f"Recording failed: {failure_response['error']}"

    @staticmethod
    def record_supervision(supervisor_id: str, student_id: str) -> Tuple[bool, str]:
        """Record supervision relationship"""
        supervisor_data = mongodb_cluster.get_researcher(supervisor_id)
        student_data = mongodb_cluster.get_researcher(student_id)

        if not supervisor_data or not student_data:
            return False, "Supervisor or student not found"

        try:
            count = neo4j_cluster.create_supervision(supervisor_id, student_id)

            if count == 0:
                return False, "Failed to record supervision"

            # Store in MongoDB
            collaboration_data = {
                'researcher1_id': supervisor_id,
                'researcher2_id': student_id,
                'type': 'SUPERVISED',
                'count': count,
                'recorded_at': datetime.utcnow(),
                'direction': 'supervisor_to_student'
            }

            mongodb_cluster.db.collaborations.update_one(
                {
                    'researcher1_id': supervisor_id,
                    'researcher2_id': student_id,
                    'type': 'SUPERVISED'
                },
                {'$set': collaboration_data},
                upsert=True
            )

            # Clear caches
            cache_patterns = [
                'relationships_by_type:SUPERVISED',
                f'researcher_relationships:{supervisor_id}',
                f'researcher_relationships:{student_id}'
            ]

            for pattern in cache_patterns:
                redis_cluster.cache_delete(pattern)

            redis_cluster.track_activity(supervisor_id, 'record_supervision', {
                'student_id': student_id,
                'student_name': student_data['name'],
                'new_collaboration_count': count,
                'timestamp': datetime.utcnow().isoformat()
            })

            return True, f"Supervision recorded successfully. Total supervisions: {count}"

        except Exception as e:
            print(f"Error recording supervision: {e}")
            return False, f"Failed to record supervision: {e}"

    @staticmethod
    def record_teamwork(researcher1_id: str, researcher2_id: str, project_id: Optional[str] = None) -> Tuple[bool, str]:
        """Record teamwork relationship"""
        researcher1_data = mongodb_cluster.get_researcher(researcher1_id)
        researcher2_data = mongodb_cluster.get_researcher(researcher2_id)

        if not researcher1_data or not researcher2_data:
            return False, "One or both researchers not found"

        try:
            count = neo4j_cluster.create_teamwork(researcher1_id, researcher2_id, project_id)

            if count == 0:
                return False, "Failed to record teamwork"

            # Store in MongoDB
            collaboration_data = {
                'researcher1_id': researcher1_id,
                'researcher2_id': researcher2_id,
                'type': 'TEAMWORK_WITH',
                'count': count,
                'project_id': project_id,
                'recorded_at': datetime.utcnow()
            }

            mongodb_cluster.db.collaborations.update_one(
                {
                    'researcher1_id': researcher1_id,
                    'researcher2_id': researcher2_id,
                    'type': 'TEAMWORK_WITH'
                },
                {'$set': collaboration_data},
                upsert=True
            )

            # Clear caches
            cache_patterns = [
                'relationships_by_type:TEAMWORK_WITH',
                f'researcher_relationships:{researcher1_id}',
                f'researcher_relationships:{researcher2_id}'
            ]

            for pattern in cache_patterns:
                redis_cluster.cache_delete(pattern)

            redis_cluster.track_activity(researcher1_id, 'record_teamwork', {
                'with_researcher_id': researcher2_id,
                'with_researcher_name': researcher2_data['name'],
                'project_id': project_id,
                'new_collaboration_count': count,
                'timestamp': datetime.utcnow().isoformat()
            })

            return True, f"Teamwork recorded successfully. Total teamwork collaborations: {count}"

        except Exception as e:
            print(f"Error recording teamwork: {e}")
            return False, f"Failed to record teamwork: {e}"

    @staticmethod
    def get_all_relationships() -> List[Dict[str, Any]]:
        """Get all relationships from Neo4j cluster with caching"""
        cache_key = "all_relationships"
        cached = redis_cluster.cache_get(cache_key)

        if cached:
            cached['source'] = 'redis_cache'
            return cached.get('data', [])

        try:
            relationships = neo4j_cluster.get_all_relationships()

            enhanced_relationships = []
            for rel in relationships:
                researcher1_data = mongodb_cluster.get_researcher(rel['researcher1_id'])
                researcher2_data = mongodb_cluster.get_researcher(rel['researcher2_id'])

                if researcher1_data and researcher2_data:
                    enhanced_rel = {
                        **rel,
                        'researcher1_details': {
                            'name': researcher1_data['name'],
                            'email': researcher1_data['email'],
                            'department': researcher1_data['department']
                        },
                        'researcher2_details': {
                            'name': researcher2_data['name'],
                            'email': researcher2_data['email'],
                            'department': researcher2_data['department']
                        },
                        'fetched_at': datetime.utcnow().isoformat()
                    }
                    enhanced_relationships.append(enhanced_rel)

            # Prepare cache data
            cache_data = {
                'data': enhanced_relationships,
                'timestamp': datetime.utcnow().isoformat(),
                'source': 'neo4j_cluster',
                'count': len(enhanced_relationships)
            }

            # Cache for 5 minutes
            redis_cluster.cache_set(cache_key, cache_data, 300)

            return enhanced_relationships

        except Exception as e:
            print(f"Error getting relationships from Neo4j: {e}")

            # Fallback to MongoDB
            try:
                relationships = list(mongodb_cluster.db.collaborations.find())
                for rel in relationships:
                    rel['_id'] = str(rel['_id'])

                return relationships
            except:
                return []

    @staticmethod
    def get_relationships_by_type(relationship_type: str) -> List[Dict[str, Any]]:
        """Get relationships by specific type"""
        cache_key = f"relationships_by_type:{relationship_type}"
        cached = redis_cluster.cache_get(cache_key)

        if cached:
            return cached

        try:
            relationships = neo4j_cluster.get_relationships_by_type(relationship_type)

            enhanced_relationships = []
            for rel in relationships:
                researcher1_data = mongodb_cluster.get_researcher(rel['researcher1_id'])
                researcher2_data = mongodb_cluster.get_researcher(rel['researcher2_id'])

                if researcher1_data and researcher2_data:
                    enhanced_rel = {
                        **rel,
                        'relationship_type': relationship_type,
                        'researcher1_details': {
                            'name': researcher1_data['name'],
                            'email': researcher1_data['email']
                        },
                        'researcher2_details': {
                            'name': researcher2_data['name'],
                            'email': researcher2_data['email']
                        }
                    }
                    enhanced_relationships.append(enhanced_rel)

            redis_cluster.cache_set(cache_key, enhanced_relationships, 300)
            return enhanced_relationships

        except Exception as e:
            print(f"Error getting relationships by type: {e}")

            # Fallback to MongoDB
            try:
                relationships = list(mongodb_cluster.db.collaborations.find({
                    'type': relationship_type
                }))
                for rel in relationships:
                    rel['_id'] = str(rel['_id'])

                return relationships
            except:
                return []

    @staticmethod
    def get_researcher_relationships(researcher_id: str) -> List[Dict[str, Any]]:
        """Get all relationships for a researcher"""
        cache_key = f"researcher_relationships:{researcher_id}"
        cached = redis_cluster.cache_get(cache_key)

        if cached:
            return cached

        try:
            relationships = neo4j_cluster.get_researcher_relationships(researcher_id)

            enhanced_relationships = []
            for rel in relationships:
                other_data = mongodb_cluster.get_researcher(rel['other_id'])
                if other_data:
                    enhanced_rel = {
                        **rel,
                        'other_details': {
                            'name': other_data['name'],
                            'email': other_data['email'],
                            'department': other_data['department']
                        }
                    }
                    enhanced_relationships.append(enhanced_rel)

            redis_cluster.cache_set(cache_key, enhanced_relationships, 300)
            return enhanced_relationships

        except Exception as e:
            print(f"Error getting researcher relationships: {e}")
            return []

    @staticmethod
    def get_relationship_statistics() -> Dict[str, Any]:
        """Get relationship statistics from clusters"""
        cache_key = "relationship_statistics"
        cached = redis_cluster.cache_get(cache_key)

        if cached:
            cached['source'] = 'redis_cache'
            return cached

        try:
            # Get from Neo4j
            stats = neo4j_cluster.get_relationship_stats()

            # Get from MongoDB for additional data
            total_researchers = mongodb_cluster.db.researchers.count_documents({
                'profile_status': 'approved'
            })

            enhanced_stats = {
                **stats,
                'total_researchers': total_researchers,
                'coauthorship_percentage': (stats.get('total_coauthorships', 0) / max(1, total_researchers)) * 100,
                'supervision_percentage': (stats.get('total_supervisions', 0) / max(1, total_researchers)) * 100,
                'teamwork_percentage': (stats.get('total_teamworks', 0) / max(1, total_researchers)) * 100,
                'source': 'neo4j_cluster',
                'calculated_at': datetime.utcnow().isoformat()
            }

            # Cache for 10 minutes
            redis_cluster.cache_set(cache_key, enhanced_stats, 600)

            return enhanced_stats

        except Exception as e:
            print(f"Error getting relationship stats: {e}")

            # Fallback to MongoDB
            try:
                stats = {
                    'total_coauthorships': mongodb_cluster.db.collaborations.count_documents({
                        'type': 'CO_AUTHORED_WITH'
                    }),
                    'total_supervisions': mongodb_cluster.db.collaborations.count_documents({
                        'type': 'SUPERVISED'
                    }),
                    'total_teamworks': mongodb_cluster.db.collaborations.count_documents({
                        'type': 'TEAMWORK_WITH'
                    }),
                    'source': 'mongodb_fallback'
                }

                return stats
            except:
                return {}

    @staticmethod
    def get_collaboration_network_stats():
        """Get collaboration network statistics"""
        try:
            stats = CollaborationService.get_relationship_statistics()
            stats['network_healthy'] = stats.get('total_coauthorships', 0) > 0
            return stats
        except:
            return None

    @staticmethod
    def get_most_collaborative_pairs(limit=10):
        """Get most collaborative pairs"""
        try:
            pairs = CollaborationService.get_all_relationships()
            if pairs:
                sorted_pairs = sorted(pairs,
                                      key=lambda x: x.get('collaboration_count', 0),
                                      reverse=True
                                      )
                return sorted_pairs[:limit]
            return []
        except:
            return []