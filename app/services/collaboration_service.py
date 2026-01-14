from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from bson import ObjectId
from app.database.mongodb import mongodb
from app.database.neo4j import neo4j
from app.database.redis import redis_manager
from app.models.collaboration import Collaboration


class CollaborationService:
    @staticmethod
    def record_coauthorship(researcher1_id: str, researcher2_id: str, publication_id: Optional[str] = None) -> Tuple[bool, str]:
        researcher1_data = mongodb.get_researcher(researcher1_id)
        researcher2_data = mongodb.get_researcher(researcher2_id)

        if not researcher1_data or not researcher2_data:
            return False, "One or both researchers not found"

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

        return True, f"Coauthorship recorded successfully. Total collaborations: {count}"

    @staticmethod
    def record_supervision(supervisor_id: str, student_id: str) -> Tuple[bool, str]:
        supervisor_data = mongodb.get_researcher(supervisor_id)
        student_data = mongodb.get_researcher(student_id)

        if not supervisor_data or not student_data:
            return False, "Supervisor or student not found"

        count = neo4j.create_supervision(supervisor_id, student_id)

        if count == 0:
            return False, "Failed to record supervision"

        redis_manager.track_activity(supervisor_id, 'record_supervision', {
            'student_id': student_id,
            'student_name': student_data['name'],
            'new_collaboration_count': count,
            'timestamp': datetime.utcnow().isoformat()
        })

        return True, f"Supervision recorded successfully. Total supervisions: {count}"

    @staticmethod
    def record_teamwork(researcher1_id: str, researcher2_id: str, project_id: Optional[str] = None) -> Tuple[bool, str]:
        researcher1_data = mongodb.get_researcher(researcher1_id)
        researcher2_data = mongodb.get_researcher(researcher2_id)

        if not researcher1_data or not researcher2_data:
            return False, "One or both researchers not found"

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

        return True, f"Teamwork recorded successfully. Total teamwork collaborations: {count}"

    @staticmethod
    def record_project_participation(researcher_id: str, project_id: str) -> Tuple[bool, str]:
        researcher_data = mongodb.get_researcher(researcher_id)
        project_data = mongodb.get_project(project_id)

        if not researcher_data:
            return False, "Researcher not found"
        if not project_data:
            return False, "Project not found"

        success = neo4j.create_project_participation(researcher_id, project_id)

        if not success:
            return False, "Failed to record project participation"

        redis_manager.track_activity(researcher_id, 'record_project_participation', {
            'project_id': project_id,
            'project_title': project_data['title'],
            'timestamp': datetime.utcnow().isoformat()
        })

        return True, f"Project participation recorded successfully"

    @staticmethod
    def get_all_relationships() -> List[Dict[str, Any]]:
        cache_key = "all_relationships"
        cached = redis_manager.cache_get(cache_key)
        if cached:
            return cached

        relationships = neo4j.get_all_relationships()

        enhanced_relationships = []
        for rel in relationships:
            researcher1_data = mongodb.get_researcher(rel['researcher1_id'])
            researcher2_data = mongodb.get_researcher(rel['researcher2_id'])

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
                    }
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

        enhanced_relationships = []
        for rel in relationships:
            researcher1_data = mongodb.get_researcher(rel['researcher1_id'])
            researcher2_data = mongodb.get_researcher(rel['researcher2_id'])

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

        redis_manager.cache_set(cache_key, enhanced_relationships, 300)
        return enhanced_relationships

    @staticmethod
    def get_researcher_relationships(researcher_id: str) -> List[Dict[str, Any]]:
        cache_key = f"researcher_relationships:{researcher_id}"
        cached = redis_manager.cache_get(cache_key)
        if cached:
            return cached

        relationships = neo4j.get_researcher_relationships(researcher_id)

        enhanced_relationships = []
        for rel in relationships:
            other_data = mongodb.get_researcher(rel['other_id'])
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

        redis_manager.cache_set(cache_key, enhanced_relationships, 300)
        return enhanced_relationships

    @staticmethod
    def get_relationship_statistics() -> Dict[str, Any]:
        cache_key = "relationship_statistics"
        cached = redis_manager.cache_get(cache_key)
        if cached:
            return cached

        stats = neo4j.get_relationship_stats()

        total_researchers = mongodb.db.researchers.count_documents({
            'profile_status': 'approved'
        })

        enhanced_stats = {
            **stats,
            'total_researchers': total_researchers,
            'coauthorship_percentage': (stats.get('total_coauthorships', 0) / max(1, total_researchers)) * 100,
            'supervision_percentage': (stats.get('total_supervisions', 0) / max(1, total_researchers)) * 100,
            'teamwork_percentage': (stats.get('total_teamworks', 0) / max(1, total_researchers)) * 100
        }

        redis_manager.cache_set(cache_key, enhanced_stats, 300)
        return enhanced_stats
    @staticmethod
    def get_collaboration_network_stats():
        """Get collaboration network statistics"""
        try:
            stats = CollaborationService.get_relationship_statistics()
            return stats
        except:
            return None

    @staticmethod
    def get_most_collaborative_pairs(limit=10):
        """Get most collaborative pairs"""
        try:
            pairs = CollaborationService.get_all_relationships()
            if pairs:
                sorted_pairs = sorted(pairs, key=lambda x: x.get('collaboration_count', 0), reverse=True)
                return sorted_pairs[:limit]
            return []
        except:
            return []