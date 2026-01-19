from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from bson import ObjectId
from app.database import mongodb_cluster, neo4j_cluster, redis_cluster
from app.models.project import Project
from app.services.cluster_service import ClusterService


class ProjectService:
    """Service for managing research projects with cluster support"""

    @staticmethod
    def create_project(creator_id: str, project_data: Dict[str, Any]) -> Tuple[bool, str, Optional[str]]:
        """Create a new project across clusters"""
        # Validate required fields
        required_fields = ['title', 'description']
        for field in required_fields:
            if field not in project_data or not project_data[field]:
                return False, None, f"Missing required field: {field}"

        # Check cluster health
        if not ClusterService.is_cluster_healthy():
            return False, None, "System is in degraded mode. Please try again later."

        # Get creator data
        creator_data = mongodb_cluster.get_researcher(creator_id)
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

        try:
            # Save to MongoDB
            project_dict = project.to_dict()
            project_id = mongodb_cluster.create_project(project_dict)

            if not project_id:
                return False, None, "Failed to create project"

            # Update researcher's project list
            mongodb_cluster.update_researcher(creator_id, {
                '$push': {'projects': project_id}
            })

            # Create project relationships in Neo4j
            try:
                # Create project participation for all participants
                for participant_id in project.participants:
                    neo4j_cluster.create_project_participation(participant_id, project_id)

                # Create teamwork relationships between participants
                participants = project.participants
                for i in range(len(participants)):
                    for j in range(i + 1, len(participants)):
                        neo4j_cluster.create_teamwork(
                            participants[i],
                            participants[j],
                            project_id
                        )
            except Exception as e:
                print(f"Warning: Could not create Neo4j relationships: {e}")

            # Clear related caches
            cache_patterns = [
                f"project_details:{project_id}",
                f"projects_by_researcher:{creator_id}:*",
                "recent_projects"
            ]

            for pattern in cache_patterns:
                redis_cluster.cache_delete(pattern)

            # Log activity
            redis_cluster.track_activity(creator_id, 'create_project', {
                'project_id': project_id,
                'project_title': project.title,
                'timestamp': datetime.utcnow().isoformat(),
                'cluster_operation': True
            })

            return True, project_id, "Project created successfully across clusters"

        except Exception as e:
            failure_response = ClusterService.handle_cluster_failure(
                'mongodb', 'project_create', e
            )
            return False, None, f"Creation failed: {failure_response['error']}"

    @staticmethod
    def get_project_details(project_id: str) -> Optional[Dict[str, Any]]:
        """Get project details from distributed sources"""
        # Try cache first
        cache_key = f"project_details:{project_id}"
        cached = redis_cluster.cache_get(cache_key)

        if cached:
            cached['source'] = 'redis_cache'
            return cached

        # Get from MongoDB
        project_data = mongodb_cluster.get_project(project_id)

        if not project_data:
            return None

        # Get participant details
        participants_details = []
        for participant_id in project_data.get('participants', []):
            researcher_data = mongodb_cluster.get_researcher(participant_id)
            if researcher_data:
                participants_details.append({
                    'id': participant_id,
                    'name': researcher_data['name'],
                    'email': researcher_data['email'],
                    'department': researcher_data['department']
                })

        # Get Neo4j relationship data if available
        collaboration_data = []
        try:
            # Get collaboration counts between participants
            participants = project_data.get('participants', [])
            if len(participants) > 1:
                # This would be a Neo4j query in production
                pass
        except Exception as e:
            print(f"Warning: Could not get Neo4j data: {e}")

        # Build complete details
        project_details = {
            'source': 'mongodb_primary',
            'cache_hit': False,
            'project_info': project_data,
            'participants': participants_details,
            'participants_count': len(participants_details),
            'collaboration_data': collaboration_data,
            'fetched_at': datetime.utcnow().isoformat()
        }

        # Store in cache for 5 minutes
        redis_cluster.cache_set(cache_key, project_details, 300)

        return project_details

    @staticmethod
    def add_participant_to_project(project_id: str, researcher_id: str, adder_id: str) -> Tuple[bool, str]:
        """Add researcher to project across clusters"""
        # Verify project exists
        project_data = mongodb_cluster.get_project(project_id)
        if not project_data:
            return False, "Project not found"

        # Verify researcher exists
        researcher_data = mongodb_cluster.get_researcher(researcher_id)
        if not researcher_data:
            return False, "Researcher not found"

        # Verify adder has permission
        adder_data = mongodb_cluster.get_researcher(adder_id)
        if not adder_data:
            return False, "Adder not found"

        if (adder_id != project_data['creator_id'] and
                adder_data['role'] != 'admin'):
            return False, "Only project creator or admin can add participants"

        try:
            # Add participant in MongoDB
            success = mongodb_cluster.add_project_participant(project_id, researcher_id)

            if not success:
                return False, "Failed to add participant"

            # Update researcher's project list
            mongodb_cluster.update_researcher(researcher_id, {
                '$push': {'projects': project_id}
            })

            # Update Neo4j relationships
            try:
                # Create project participation
                neo4j_cluster.create_project_participation(researcher_id, project_id)

                # Create teamwork with existing participants
                existing_participants = project_data.get('participants', [])
                for participant_id in existing_participants:
                    if participant_id != researcher_id:
                        neo4j_cluster.create_teamwork(participant_id, researcher_id, project_id)
            except Exception as e:
                print(f"Warning: Could not update Neo4j: {e}")

            # Clear caches
            cache_patterns = [
                f"project_details:{project_id}",
                f"projects_by_researcher:{researcher_id}:*",
                f"projects_by_researcher:{adder_id}:*"
            ]

            for pattern in cache_patterns:
                redis_cluster.cache_delete(pattern)

            # Log activity
            redis_cluster.track_activity(adder_id, 'add_project_participant', {
                'project_id': project_id,
                'added_researcher_id': researcher_id,
                'added_researcher_name': researcher_data['name'],
                'timestamp': datetime.utcnow().isoformat(),
                'cluster_operation': True
            })

            return True, f"Researcher {researcher_data['name']} added to project across clusters"

        except Exception as e:
            failure_response = ClusterService.handle_cluster_failure(
                'mongodb', 'add_participant', e
            )
            return False, f"Failed to add participant: {failure_response['error']}"

    @staticmethod
    def get_projects_by_researcher(researcher_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get researcher's projects with caching"""
        cache_key = f"projects_by_researcher:{researcher_id}:{status or 'all'}"
        cached = redis_cluster.cache_get(cache_key)

        if cached:
            return cached

        # Build query
        query = {'participants': researcher_id}
        if status:
            query['status'] = status

        # Search in MongoDB
        projects_cursor = mongodb_cluster.db.projects.find(query)
        projects = []

        for project in projects_cursor:
            project['_id'] = str(project['_id'])

            # Add participant count
            project['participants_count'] = len(project.get('participants', []))

            # Add user role
            if project['creator_id'] == researcher_id:
                project['user_role'] = 'creator'
            else:
                project['user_role'] = 'participant'

            # Add cluster metadata
            project['fetched_at'] = datetime.utcnow().isoformat()

            projects.append(project)

        # Cache for 3 minutes
        redis_cluster.cache_set(cache_key, projects, 180)

        return projects

    @staticmethod
    def search_projects(query: str, filters: Optional[Dict] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Search for projects with cluster optimization"""
        if not filters:
            filters = {}

        # Try cache for common searches
        cache_key = f"project_search:{query}:{hash(str(filters))}:{limit}"
        cached = redis_cluster.cache_get(cache_key)

        if cached:
            return cached

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
        projects_cursor = mongodb_cluster.db.projects.find(search_query).limit(limit)
        projects = []

        for project in projects_cursor:
            project['_id'] = str(project['_id'])
            project['participants_count'] = len(project.get('participants', []))
            project['search_fetched'] = datetime.utcnow().isoformat()
            projects.append(project)

        # Cache for 2 minutes
        redis_cluster.cache_set(cache_key, projects, 120)

        return projects

    @staticmethod
    def update_project_status(project_id: str, new_status: str, updater_id: str) -> Tuple[bool, str]:
        """Update project status across clusters"""
        # Validate new status
        valid_statuses = ['active', 'completed', 'pending', 'cancelled']
        if new_status not in valid_statuses:
            return False, f"Invalid status. Must be one of: {', '.join(valid_statuses)}"

        try:
            # Update in MongoDB
            success = mongodb_cluster.update_project(project_id, {
                'status': new_status,
                'updated_at': datetime.utcnow(),
                'status_changed_by': updater_id,
                'status_changed_at': datetime.utcnow()
            })

            if not success:
                return False, "Failed to update project status"

            # Clear caches
            cache_patterns = [
                f"project_details:{project_id}",
                f"projects_by_researcher:*:{new_status}",
                f"projects_by_researcher:*:all"
            ]

            for pattern in cache_patterns:
                # Note: Redis cluster might not support pattern deletion efficiently
                # In production, you'd use SCAN or maintain a key index
                redis_cluster.cache_delete(pattern)

            # Log activity
            redis_cluster.track_activity(updater_id, 'update_project_status', {
                'project_id': project_id,
                'new_status': new_status,
                'timestamp': datetime.utcnow().isoformat(),
                'cluster_operation': True
            })

            return True, f"Project status updated to {new_status} across clusters"

        except Exception as e:
            failure_response = ClusterService.handle_cluster_failure(
                'mongodb', 'update_status', e
            )
            return False, f"Update failed: {failure_response['error']}"