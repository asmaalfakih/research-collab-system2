from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from bson import ObjectId
from app.database.mongodb import mongodb
from app.database.neo4j import neo4j
from app.database.redis import redis_manager
from app.models.publication import Publication, Author
from app.models.collaboration import CollaborationType


class PublicationService:
    """Service for managing research publications"""

    @staticmethod
    def create_publication(creator_id: str, publication_data: Dict[str, Any]) -> Tuple[bool, str, Optional[str]]:
        """Create a new publication"""
        # Validate required fields
        required_fields = ['title', 'authors', 'year']
        for field in required_fields:
            if field not in publication_data or not publication_data[field]:
                return False, None, f"Missing required field: {field}"

        # Verify creator is in authors list
        creator_in_authors = False
        authors_list = []

        for i, author_data in enumerate(publication_data['authors']):
            if not isinstance(author_data, dict):
                return False, None, f"Author {i + 1} must be a dictionary"

            if 'researcher_id' not in author_data or 'name' not in author_data:
                return False, None, f"Author {i + 1} missing required fields"

            if author_data['researcher_id'] == creator_id:
                creator_in_authors = True

            # Create author object
            author = Author(
                researcher_id=author_data['researcher_id'],
                name=author_data['name'],
                order=author_data.get('order', i + 1),
                affiliation=author_data.get('affiliation', ''),
                contribution=author_data.get('contribution', '')
            )
            authors_list.append(author)

        if not creator_in_authors:
            return False, None, "Creator must be one of the authors"

        # Replace authors list
        publication_data['authors'] = authors_list

        # Set default values
        publication_data.setdefault('status', 'published')
        publication_data.setdefault('keywords', [])
        publication_data.setdefault('related_projects', [])

        # Create publication object and validate
        publication = Publication(**publication_data)
        errors = publication.validate()

        if errors:
            return False, None, "; ".join(errors)

        # Save to MongoDB
        publication_dict = publication.to_dict()
        publication_id = mongodb.create_publication(publication_dict)

        if not publication_id:
            return False, None, "Failed to create publication"

        # Update researchers by adding publication
        for author in authors_list:
            mongodb.update_researcher(author.researcher_id, {
                '$push': {'publications': publication_id}
            })

        # Create co-authorship relationships in Neo4j
        author_ids = [author.researcher_id for author in authors_list]
        neo4j.create_coauthorship(publication_id, author_ids)

        # Update related projects
        for project_id in publication_data['related_projects']:
            mongodb.update_project(project_id, {
                '$push': {'related_publications': publication_id}
            })

        # Log activity
        redis_manager.track_activity(creator_id, 'create_publication', {
            'publication_id': publication_id,
            'publication_title': publication.title,
            'timestamp': datetime.utcnow().isoformat()
        })

        return True, publication_id, "Publication created successfully"

    @staticmethod
    def get_publication_details(publication_id: str) -> Optional[Dict[str, Any]]:
        """Get publication details"""
        # Try to get from cache
        cache_key = f"publication_details:{publication_id}"
        cached = redis_manager.cache_get(cache_key)
        if cached:
            return cached

        # Search in MongoDB
        publication_cursor = mongodb.db.publications.find_one({'_id': ObjectId(publication_id)})

        if not publication_cursor:
            return None

        publication_data = publication_cursor
        publication_data['_id'] = str(publication_data['_id'])

        # Get complete author details
        authors_details = []
        for author in publication_data.get('authors', []):
            if isinstance(author, dict):
                researcher_id = author.get('researcher_id')
                if researcher_id:
                    researcher_data = mongodb.get_researcher(researcher_id)
                    if researcher_data:
                        author_details = {
                            'id': researcher_id,
                            'name': researcher_data['name'],
                            'email': researcher_data['email'],
                            'department': researcher_data['department'],
                            'order': author.get('order', 1),
                            'affiliation': author.get('affiliation', ''),
                            'contribution': author.get('contribution', '')
                        }
                        authors_details.append(author_details)

        # Get related projects data
        projects_details = []
        for project_id in publication_data.get('related_projects', []):
            project_data = mongodb.get_project(project_id)
            if project_data:
                projects_details.append({
                    'id': project_id,
                    'title': project_data.get('title', 'Unknown'),
                    'status': project_data.get('status', 'unknown')
                })

        # Build complete details
        publication_details = {
            'publication_info': publication_data,
            'authors': authors_details,
            'projects': projects_details,
            'citation_apa': Publication(**publication_data).get_citation('apa'),
            'citation_mla': Publication(**publication_data).get_citation('mla')
        }

        # Store in cache for 10 minutes
        redis_manager.cache_set(cache_key, publication_details, 600)

        return publication_details

    @staticmethod
    def get_publications_by_researcher(researcher_id: str, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get researcher's publications"""
        # Build query
        query = {'authors.researcher_id': researcher_id}
        if year:
            query['year'] = year

        # Search in MongoDB
        publications_cursor = mongodb.db.publications.find(query).sort('year', -1)
        publications = []

        for pub in publications_cursor:
            pub['_id'] = str(pub['_id'])

            # Add author count
            pub['authors_count'] = len(pub.get('authors', []))

            # Add authorship role (main author or co-author)
            for author in pub.get('authors', []):
                if isinstance(author, dict) and author.get('researcher_id') == researcher_id:
                    pub['author_role'] = 'first_author' if author.get('order', 99) == 1 else 'co_author'
                    break

            publications.append(pub)

        return publications

    @staticmethod
    def search_publications(query: str, filters: Optional[Dict] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Search for publications"""
        if not filters:
            filters = {}

        # Build search query
        search_query = {}

        if query:
            search_query['$or'] = [
                {'title': {'$regex': query, '$options': 'i'}},
                {'abstract': {'$regex': query, '$options': 'i'}},
                {'keywords': {'$regex': query, '$options': 'i'}},
                {'journal': {'$regex': query, '$options': 'i'}}
            ]

        # Add filters
        if 'year_from' in filters:
            search_query['year'] = {'$gte': filters['year_from']}

        if 'year_to' in filters:
            if 'year' not in search_query:
                search_query['year'] = {}
            search_query['year']['$lte'] = filters['year_to']

        if 'journal' in filters:
            search_query['journal'] = {'$regex': filters['journal'], '$options': 'i'}

        if 'status' in filters:
            search_query['status'] = filters['status']

        # Search
        publications_cursor = mongodb.db.publications.find(search_query).sort('year', -1).limit(limit)
        publications = []

        for pub in publications_cursor:
            pub['_id'] = str(pub['_id'])
            pub['authors_count'] = len(pub.get('authors', []))
            publications.append(pub)

        return publications

    @staticmethod
    def update_publication_citation(publication_id: str, increment: bool = True) -> bool:
        """Update citation count"""
        try:
            if increment:
                mongodb.db.publications.update_one(
                    {'_id': ObjectId(publication_id)},
                    {'$inc': {'citation_count': 1}}
                )
            else:
                mongodb.db.publications.update_one(
                    {'_id': ObjectId(publication_id)},
                    {'$inc': {'citation_count': -1}}
                )
            return True
        except:
            return False

    @staticmethod
    def track_publication_view(publication_id: str) -> bool:
        """Track publication view"""
        try:
            mongodb.db.publications.update_one(
                {'_id': ObjectId(publication_id)},
                {'$inc': {'views': 1}}
            )
            return True
        except:
            return False