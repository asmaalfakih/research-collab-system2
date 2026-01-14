from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from bson import ObjectId
from app.database.mongodb import mongodb
from app.database.neo4j import neo4j
from app.database.redis import redis_manager
from app.models.researcher import Researcher
from app.utils.validators import validate_email, validate_phone


class ResearcherService:
    """Service for managing researchers"""

    @staticmethod
    def get_researcher_profile(researcher_id: str) -> Optional[Dict[str, Any]]:
        """Get researcher profile"""
        # Try to get from cache first
        cached_profile = redis_manager.cache_get(f"researcher_profile:{researcher_id}")
        if cached_profile:
            return cached_profile

        # Get from MongoDB
        researcher_data = mongodb.get_researcher(researcher_id)

        if not researcher_data:
            return None

        # Get statistics
        stats = mongodb.get_researcher_stats(researcher_id)

        # Get collaborators from Neo4j
        collaborators = neo4j.get_researcher_collaborators(researcher_id)

        # Build profile
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
                'last_login': researcher_data.get('last_login')
            },
            'statistics': {
                'projects_count': stats['projects_count'],
                'publications_count': stats['publications_count'],
                'collaborators_count': len(collaborators),
                'login_count': researcher_data.get('login_count', 0)
            },
            'collaborators': collaborators[:10],  # Only first 10 collaborators
            'activity_score': len(collaborators) * 5 + stats['projects_count'] * 10 + stats['publications_count'] * 15
        }

        # Store in cache for 5 minutes
        redis_manager.cache_set(f"researcher_profile:{researcher_id}", profile, 300)

        return profile

    @staticmethod
    def update_researcher_profile(researcher_id: str, update_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Update researcher profile"""
        # Validate data
        if 'email' in update_data and not validate_email(update_data['email']):
            return False, "Invalid email format"

        if 'contact' in update_data:
            contact = update_data['contact']
            if 'phone' in contact and not validate_phone(contact['phone']):
                return False, "Invalid phone number format"

        # Update in MongoDB
        update_data['updated_at'] = datetime.utcnow()
        success = mongodb.update_researcher(researcher_id, update_data)

        if not success:
            return False, "Failed to update profile"

        # Update in Neo4j if relevant data
        neo4j_update = {}
        if 'name' in update_data:
            neo4j_update['name'] = update_data['name']
        if 'department' in update_data:
            neo4j_update['department'] = update_data['department']

        if neo4j_update:
            neo4j.update_researcher_node(researcher_id, neo4j_update)

        # Remove profile from cache
        redis_manager.cache_delete(f"researcher_profile:{researcher_id}")

        # Log activity
        redis_manager.track_activity(researcher_id, 'profile_update', {
            'fields_updated': list(update_data.keys()),
            'timestamp': datetime.utcnow().isoformat()
        })

        return True, "Profile updated successfully"

    @staticmethod
    def search_researchers(query: str, filters: Optional[Dict] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Search for researchers"""
        if not filters:
            filters = {}

        # Build search query
        search_query = {}

        if query:
            search_query['$or'] = [
                {'name': {'$regex': query, '$options': 'i'}},
                {'email': {'$regex': query, '$options': 'i'}},
                {'department': {'$regex': query, '$options': 'i'}},
                {'research_interests': {'$regex': query, '$options': 'i'}}
            ]

        # Add filters
        if 'department' in filters:
            search_query['department'] = {'$regex': filters['department'], '$options': 'i'}

        if 'research_interests' in filters:
            search_query['research_interests'] = {'$in': [filters['research_interests']]}

        if 'profile_status' in filters:
            search_query['profile_status'] = filters['profile_status']

        # Add condition to not show deleted accounts
        search_query['profile_status'] = {'$ne': 'deleted'}

        # Search in MongoDB
        researchers = mongodb.search_researchers(search_query, limit)

        # Add statistics for each researcher
        for researcher in researchers:
            researcher_id = str(researcher['_id'])
            stats = mongodb.get_researcher_stats(researcher_id)
            researcher['stats'] = stats

        return researchers

    @staticmethod
    def get_top_researchers(limit: int = 10) -> List[Dict[str, Any]]:
        """Get top researchers"""
        # Try to get from cache first
        cache_key = f"top_researchers:{limit}"
        cached = redis_manager.cache_get(cache_key)
        if cached:
            return cached

        # Get from MongoDB
        top_researchers = mongodb.get_top_researchers(limit)

        # Store in cache for 10 minutes
        redis_manager.cache_set(cache_key, top_researchers, 600)

        return top_researchers

    @staticmethod
    def get_researcher_collaboration_network(researcher_id: str, depth: int = 2) -> Dict[str, Any]:
        """Get researcher collaboration network"""
        # Get from Neo4j
        network = neo4j.get_researcher_network(researcher_id, depth)

        if not network or not network['central_researcher']:
            return {'error': 'Researcher not found'}

        # Add additional details from MongoDB
        for connection in network['connections']:
            researcher_data = mongodb.get_researcher(connection['researcher_id'])
            if researcher_data:
                connection['email'] = researcher_data['email']
                connection['department'] = researcher_data['department']
                connection['research_interests'] = researcher_data['research_interests']
                connection['profile_status'] = researcher_data['profile_status']

        return network

    @staticmethod
    def suggest_collaborators(researcher_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Suggest potential collaborators"""
        # Get researcher data
        researcher_data = mongodb.get_researcher(researcher_id)

        if not researcher_data:
            return []

        # Find researchers with similar research interests
        suggestions = neo4j.find_research_partners(
            researcher_id,
            researcher_data['research_interests']
        )

        # Sort by collaboration probability
        sorted_suggestions = sorted(
            suggestions,
            key=lambda x: (x['has_collaborated'], -x['collaboration_count']),
            reverse=True
        )

        return sorted_suggestions[:limit]

    @staticmethod
    def delete_researcher(researcher_id: str, admin_id: str) -> Tuple[bool, str]:
        """Delete researcher (by admin)"""
        # Verify researcher exists
        researcher_data = mongodb.get_researcher(researcher_id)

        if not researcher_data:
            return False, "Researcher not found"

        # Don't allow deleting admin accounts
        if researcher_data['role'] == 'admin':
            return False, "Cannot delete admin accounts"

        # Update account status to deleted
        success = mongodb.update_researcher(researcher_id, {
            'profile_status': 'deleted',
            'updated_at': datetime.utcnow()
        })

        if not success:
            return False, "Failed to delete researcher"

        # Log activity
        redis_manager.track_activity(admin_id, 'delete_researcher', {
            'target_researcher_id': researcher_id,
            'target_name': researcher_data['name'],
            'timestamp': datetime.utcnow().isoformat()
        })

        return True, "Researcher deleted successfully"