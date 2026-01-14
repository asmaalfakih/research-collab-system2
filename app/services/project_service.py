from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from bson import ObjectId
from app.database.mongodb import mongodb
from app.database.neo4j import neo4j
from app.database.redis import redis_manager
from app.models.project import Project
from app.models.collaboration import CollaborationType


class ProjectService:
    """Service for managing research projects"""

    @staticmethod
    def create_project(creator_id: str, project_data: Dict[str, Any]) -> Tuple[bool, str, Optional[str]]:
        """Create a new project"""
        # Validate required fields
        required_fields = ['title', 'description']
        for field in required_fields:
            if field not in project_data or not project_data[field]:
                return False, None, f"Missing required field: {field}"

        # Get creator data
        creator_data = mongodb.get_researcher(creator_id)
        if not creator_data:
            return False, None, "Creator not found"

        # Prepare project data
        project_data['creator_id'] = creator_id
        project_data['creator_name'] = creator_data['name']
        project_data.setdefault('participants', [creator_id])
        project_data.setdefault('status', 'active')
        project_data.setdefault('start_date', datetime.utcnow().date().isoformat())

        # Create project object and validate
        project = Project(**project_data)
        errors = project.validate()

        if errors:
            return False, None, "; ".join(errors)

        # Save to MongoDB
        project_dict = project.to_dict()
        project_id = mongodb.create_project(project_dict)

        if not project_id:
            return False, None, "Failed to create project"

        # Update researcher by adding project
        mongodb.update_researcher(creator_id, {
            '$push': {'projects': project_id}
        })

        # Create project team in Neo4j if there are participants
        if len(project.participants) > 1:
            neo4j.create_project_team(project_id, project.participants)

        # Log activity
        redis_manager.track_activity(creator_id, 'create_project', {
            'project_id': project_id,
            'project_title': project.title,
            'timestamp': datetime.utcnow().isoformat()
        })

        return True, project_id, "Project created successfully"

    @staticmethod
    def get_project_details(project_id: str) -> Optional[Dict[str, Any]]:
        """Get project details"""
        # Try to get from cache
        cache_key = f"project_details:{project_id}"
        cached = redis_manager.cache_get(cache_key)
        if cached:
            return cached

        # Get from MongoDB
        project_data = mongodb.get_project(project_id)

        if not project_data:
            return None

        # Get participant details
        participants_details = []
        for participant_id in project_data.get('participants', []):
            researcher_data = mongodb.get_researcher(participant_id)
            if researcher_data:
                participants_details.append({
                    'id': participant_id,
                    'name': researcher_data['name'],
                    'email': researcher_data['email'],
                    'department': researcher_data['department']
                })

        # Get related publications data
        publications_details = []
        for pub_id in project_data.get('related_publications', []):
            # TODO: Add query to get publication details
            publications_details.append({
                'id': pub_id,
                'title': f"Publication {pub_id}"  # Temporary
            })

        # Build complete details
        project_details = {
            'project_info': project_data,
            'participants': participants_details,
            'publications': publications_details,
            'participants_count': len(participants_details),
            'publications_count': len(publications_details)
        }

        # Store in cache for 5 minutes
        redis_manager.cache_set(cache_key, project_details, 300)

        return project_details

    @staticmethod
    def add_participant_to_project(project_id: str, researcher_id: str, adder_id: str) -> Tuple[bool, str]:
        """Add researcher to project"""
        # Verify project exists
        project_data = mongodb.get_project(project_id)
        if not project_data:
            return False, "Project not found"

        # Verify researcher exists
        researcher_data = mongodb.get_researcher(researcher_id)
        if not researcher_data:
            return False, "Researcher not found"

        # Verify adder is project creator or admin
        adder_data = mongodb.get_researcher(adder_id)
        if not adder_data:
            return False, "Adder not found"

        if (adder_id != project_data['creator_id'] and
                adder_data['role'] != 'admin'):
            return False, "Only project creator or admin can add participants"

        # Add participant in MongoDB
        success = mongodb.add_project_participant(project_id, researcher_id)

        if not success:
            return False, "Failed to add participant"

        # Update researcher's project list
        mongodb.update_researcher(researcher_id, {
            '$push': {'projects': project_id}
        })

        # Update project team in Neo4j
        current_participants = project_data.get('participants', [])
        current_participants.append(researcher_id)
        neo4j.create_project_team(project_id, current_participants)

        # Log activity
        redis_manager.track_activity(adder_id, 'add_project_participant', {
            'project_id': project_id,
            'added_researcher_id': researcher_id,
            'added_researcher_name': researcher_data['name'],
            'timestamp': datetime.utcnow().isoformat()
        })

        return True, f"Researcher {researcher_data['name']} added to project"

    @staticmethod
    def get_projects_by_researcher(researcher_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get researcher's projects"""
        # Build query
        query = {'participants': researcher_id}
        if status:
            query['status'] = status

        # Search in MongoDB
        projects_cursor = mongodb.db.projects.find(query)
        projects = []

        for project in projects_cursor:
            project['_id'] = str(project['_id'])

            # Add participant count
            project['participants_count'] = len(project.get('participants', []))

            # Add user role (creator or participant)
            if project['creator_id'] == researcher_id:
                project['user_role'] = 'creator'
            else:
                project['user_role'] = 'participant'

            projects.append(project)

        return projects

    @staticmethod
    def search_projects(query: str, filters: Optional[Dict] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Search for projects"""
        if not filters:
            filters = {}

        # Build search query
        search_query = {}

        if query:
            search_query['$or'] = [
                {'title': {'$regex': query, '$options': 'i'}},
                {'description': {'$regex': query, '$options': 'i'}},
                {'research_area': {'$regex': query, '$options': 'i'}},
                {'tags': {'$regex': query, '$options': 'i'}}
            ]

        # Add filters
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

        # Search
        projects_cursor = mongodb.db.projects.find(search_query).limit(limit)
        projects = []

        for project in projects_cursor:
            project['_id'] = str(project['_id'])
            project['participants_count'] = len(project.get('participants', []))
            projects.append(project)

        return projects

    @staticmethod
    def update_project_status(project_id: str, new_status: str, updater_id: str) -> Tuple[bool, str]:
        """Update project status"""
        # Validate new status
        valid_statuses = ['active', 'completed', 'pending', 'cancelled']
        if new_status not in valid_statuses:
            return False, f"Invalid status. Must be one of: {', '.join(valid_statuses)}"

        # Update in MongoDB
        success = mongodb.update_project(project_id, {
            'status': new_status,
            'updated_at': datetime.utcnow()
        })

        if not success:
            return False, "Failed to update project status"

        # Log activity
        redis_manager.track_activity(updater_id, 'update_project_status', {
            'project_id': project_id,
            'new_status': new_status,
            'timestamp': datetime.utcnow().isoformat()
        })

        return True, f"Project status updated to {new_status}"