from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from bson import ObjectId
from app.database.mongodb import mongodb
from app.database.neo4j import neo4j
from app.database.redis import redis_manager
from app.models.publication import Publication, Author
from app.models.collaboration import CollaborationType


class PublicationService:
    @staticmethod
    def create_publication(creator_id: str, publication_data: Dict[str, Any]) -> Tuple[bool, str, Optional[str]]:
        required_fields = ['title', 'authors', 'year']
        for field in required_fields:
            if field not in publication_data or not publication_data[field]:
                return False, None, f"Missing required field: {field}"

        creator_in_authors = False
        authors_list = []

        for i, author_data in enumerate(publication_data['authors']):
            if not isinstance(author_data, dict):
                return False, None, f"Author {i + 1} must be a dictionary"

            if 'researcher_id' not in author_data or 'name' not in author_data:
                return False, None, f"Author {i + 1} missing required fields"

            if author_data['researcher_id'] == creator_id:
                creator_in_authors = True

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

        publication_data['authors'] = authors_list

        publication_data.setdefault('status', 'published')
        publication_data.setdefault('keywords', [])
        publication_data.setdefault('related_projects', [])

        publication = Publication(**publication_data)
        errors = publication.validate()

        if errors:
            return False, None, "; ".join(errors)

        publication_dict = publication.to_dict()
        publication_id = mongodb.create_publication(publication_dict)

        if not publication_id:
            return False, None, "Failed to create publication"

        for author in authors_list:
            mongodb.update_researcher(author.researcher_id, {
                '$push': {'publications': publication_id}
            })

        author_ids = [author.researcher_id for author in authors_list]
        for j in range(len(author_ids)):
            for k in range(j + 1, len(author_ids)):
                researcher1_id = author_ids[j]
                researcher2_id = author_ids[k]
                neo4j.create_coauthorship(researcher1_id, researcher2_id, publication_id)

        for i, author_id in enumerate(author_ids, 1):
            neo4j.create_authorship(author_id, publication_id, i)

        for project_id in publication_data['related_projects']:
            mongodb.update_project(project_id, {
                '$push': {'related_publications': publication_id}
            })

            neo4j.create_produced_relationship(project_id, publication_id)

        redis_manager.track_activity(creator_id, 'create_publication', {
            'publication_id': publication_id,
            'publication_title': publication.title,
            'timestamp': datetime.utcnow().isoformat()
        })

        return True, publication_id, "Publication created successfully"

    @staticmethod
    def get_publication_details(publication_id: str) -> Optional[Dict[str, Any]]:
        cache_key = f"publication_details:{publication_id}"
        cached = redis_manager.cache_get(cache_key)
        if cached:
            return cached

        publication_cursor = mongodb.db.publications.find_one({'_id': ObjectId(publication_id)})

        if not publication_cursor:
            return None

        publication_data = publication_cursor
        publication_data['_id'] = str(publication_data['_id'])

        authors_details = []
        for author in publication_data.get('authors', []):
            if isinstance(author, dict):
                researcher_id = author.get('researcher_id')
                if researcher_id:
                    researcher_data = mongodb.get_researcher(researcher_id)
                    if researcher_data:
                        author_order = author.get('order', 1)

                        with neo4j.driver.session() as session:
                            result = session.run("""
                                MATCH (r:Researcher {id: $researcher_id})-[rel:AUTHORED]->(pub:Publication {id: $publication_id})
                                RETURN rel.author_order as neo4j_order
                            """, researcher_id=researcher_id, publication_id=publication_id)

                            record = result.single()
                            if record and record['neo4j_order']:
                                author_order = record['neo4j_order']

                        author_details = {
                            'id': researcher_id,
                            'name': researcher_data['name'],
                            'email': researcher_data['email'],
                            'department': researcher_data['department'],
                            'order': author_order,
                            'affiliation': author.get('affiliation', ''),
                            'contribution': author.get('contribution', '')
                        }
                        authors_details.append(author_details)

        projects_details = []
        for project_id in publication_data.get('related_projects', []):
            project_data = mongodb.get_project(project_id)
            if project_data:
                projects_details.append({
                    'id': project_id,
                    'title': project_data.get('title', 'Unknown'),
                    'status': project_data.get('status', 'unknown')
                })

        coauthors_info = []
        with neo4j.driver.session() as session:
            result = session.run("""
                MATCH (r1:Researcher)-[rel:CO_AUTHORED_WITH]-(r2:Researcher)
                WHERE $publication_id IN rel.publications
                RETURN r1.id as researcher1_id, r2.id as researcher2_id, rel.collaboration_count as collaboration_count
            """, publication_id=publication_id)

            for record in result:
                coauthors_info.append({
                    'researcher1_id': record['researcher1_id'],
                    'researcher2_id': record['researcher2_id'],
                    'collaboration_count': record['collaboration_count']
                })

        produced_by = []
        with neo4j.driver.session() as session:
            result = session.run("""
                MATCH (p:Project)-[rel:PRODUCED]->(pub:Publication {id: $publication_id})
                RETURN p.id as project_id
            """, publication_id=publication_id)

            for record in result:
                produced_by.append(record['project_id'])

        publication_details = {
            'publication_info': publication_data,
            'authors': authors_details,
            'projects': projects_details,
            'coauthors_info': coauthors_info,
            'produced_by': produced_by,
            'citation_apa': Publication(**publication_data).get_citation('apa'),
            'citation_mla': Publication(**publication_data).get_citation('mla')
        }

        redis_manager.cache_set(cache_key, publication_details, 600)

        return publication_details

    @staticmethod
    def get_publications_by_researcher(researcher_id: str, year: Optional[int] = None) -> List[Dict[str, Any]]:
        query = {'authors.researcher_id': researcher_id}
        if year:
            query['year'] = year

        publications_cursor = mongodb.db.publications.find(query).sort('year', -1)
        publications = []

        for pub in publications_cursor:
            pub['_id'] = str(pub['_id'])
            pub['authors_count'] = len(pub.get('authors', []))

            author_order = None
            for author in pub.get('authors', []):
                if isinstance(author, dict) and author.get('researcher_id') == researcher_id:
                    author_order = author.get('order', 99)
                    break

            with neo4j.driver.session() as session:
                result = session.run("""
                    MATCH (r:Researcher {id: $researcher_id})-[rel:AUTHORED]->(pub:Publication {id: $publication_id})
                    RETURN rel.author_order as neo4j_order
                """, researcher_id=researcher_id, publication_id=str(pub['_id']))

                record = result.single()
                if record and record['neo4j_order']:
                    author_order = record['neo4j_order']

            if author_order == 1:
                pub['author_role'] = 'first_author'
            elif author_order:
                pub['author_role'] = f'co_author_{author_order}'
            else:
                pub['author_role'] = 'co_author'

            publications.append(pub)

        return publications

    @staticmethod
    def search_publications(query: str, filters: Optional[Dict] = None, limit: int = 20) -> List[Dict[str, Any]]:
        if not filters:
            filters = {}

        search_query = {}

        if query:
            search_query['$or'] = [
                {'title': {'$regex': query, '$options': 'i'}},
                {'abstract': {'$regex': query, '$options': 'i'}},
                {'keywords': {'$regex': query, '$options': 'i'}},
                {'journal': {'$regex': query, '$options': 'i'}}
            ]

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

        publications_cursor = mongodb.db.publications.find(search_query).sort('year', -1).limit(limit)
        publications = []

        for pub in publications_cursor:
            pub['_id'] = str(pub['_id'])
            pub['authors_count'] = len(pub.get('authors', []))
            publications.append(pub)

        return publications

    @staticmethod
    def get_researcher_authored_publications(researcher_id: str) -> List[Dict[str, Any]]:
        try:
            with neo4j.driver.session() as session:
                result = session.run("""
                    MATCH (r:Researcher {id: $researcher_id})-[rel:AUTHORED]->(pub:Publication)
                    RETURN pub.id as publication_id, rel.author_order as author_order
                    ORDER BY rel.author_order
                """, researcher_id=researcher_id)

                publication_ids = []
                for record in result:
                    publication_ids.append(record['publication_id'])

                if not publication_ids:
                    return []

                publications = []
                for pub_id in publication_ids:
                    pub_data = mongodb.db.publications.find_one({'_id': ObjectId(pub_id)})
                    if pub_data:
                        pub_data['_id'] = str(pub_data['_id'])
                        publications.append(pub_data)

                return publications
        except Exception as e:
            print(f"Error getting authored publications: {e}")
            return []

    @staticmethod
    def update_publication_citation(publication_id: str, increment: bool = True) -> bool:
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
        try:
            mongodb.db.publications.update_one(
                {'_id': ObjectId(publication_id)},
                {'$inc': {'views': 1}}
            )
            return True
        except:
            return False

    @staticmethod
    def delete_publication(publication_id: str, deleter_id: str) -> Tuple[bool, str]:
        try:
            publication_data = mongodb.db.publications.find_one({'_id': ObjectId(publication_id)})
            if not publication_data:
                return False, "Publication not found"

            with neo4j.driver.session() as session:
                session.run("""
                    MATCH ()-[rel:AUTHORED]->(pub:Publication {id: $publication_id})
                    DELETE rel
                """, publication_id=publication_id)

                session.run("""
                    MATCH ()-[rel:PRODUCED]->(pub:Publication {id: $publication_id})
                    DELETE rel
                """, publication_id=publication_id)

                session.run("""
                    MATCH (r1:Researcher)-[rel:CO_AUTHORED_WITH]-(r2:Researcher)
                    WHERE $publication_id IN rel.publications
                    SET rel.publications = [pub_id IN rel.publications WHERE pub_id <> $publication_id]
                """, publication_id=publication_id)

            result = mongodb.db.publications.delete_one({'_id': ObjectId(publication_id)})

            if result.deleted_count > 0:
                for author in publication_data.get('authors', []):
                    if isinstance(author, dict):
                        researcher_id = author.get('researcher_id')
                        if researcher_id:
                            mongodb.update_researcher(researcher_id, {
                                '$pull': {'publications': publication_id}
                            })

                redis_manager.track_activity(deleter_id, 'delete_publication', {
                    'publication_id': publication_id,
                    'publication_title': publication_data.get('title', 'Unknown'),
                    'timestamp': datetime.utcnow().isoformat()
                })

                redis_manager.cache_delete(f"publication_details:{publication_id}")

                return True, "Publication deleted successfully"
            else:
                return False, "Failed to delete publication"
        except Exception as e:
            print(f"Error deleting publication: {e}")
            return False, f"Error deleting publication: {e}"