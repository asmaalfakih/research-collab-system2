from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import PyMongoError, DuplicateKeyError
from datetime import datetime
from bson import ObjectId
import json
from typing import Optional, List, Dict, Any
from .connection import DatabaseConfig
from colorama import Fore, Style

class MongoDBManager:

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_mongodb()
        return cls._instance

    def _init_mongodb(self):
        config = DatabaseConfig.get_mongodb_config()

        try:
            self.client = MongoClient(
                config['uri'],
                serverSelectionTimeoutMS=config['timeout']
            )
            self.db = self.client[config['db_name']]

            self.client.admin.command('ping')
            print(f"{Fore.GREEN}PASS: MongoDB connected to database: {config['db_name']}")

            self._setup_collections()

        except Exception as e:
            print(f"{Fore.RED}FAIL: MongoDB connection failed: {e}")
            self.client = None
            self.db = None

    def _setup_collections(self):
        collections = {
            'researchers': [
                {'key': [('email', 1)], 'unique': True, 'name': 'email_unique'},
                {'key': [('research_interests', 1)], 'name': 'interests_idx'},
                {'key': [('profile_status', 1)], 'name': 'status_idx'},
                {'key': [('department', 1)], 'name': 'department_idx'}
            ],
            'projects': [
                {'key': [('title', 1)], 'name': 'title_idx'},
                {'key': [('status', 1)], 'name': 'status_idx'},
                {'key': [('start_date', -1)], 'name': 'start_date_idx'},
                {'key': [('participants', 1)], 'name': 'participants_idx'}
            ],
            'publications': [
                {'key': [('title', 1)], 'name': 'title_idx'},
                {'key': [('year', -1)], 'name': 'year_idx'},
                {'key': [('doi', 1)], 'unique': True, 'name': 'doi_unique'},
                {'key': [('authors.researcher_id', 1)], 'name': 'authors_idx'}
            ],
            'admins': [
                {'key': [('email', 1)], 'unique': True, 'name': 'admin_email_unique'}
            ],
            'logs': [
                {'key': [('timestamp', -1)], 'name': 'timestamp_idx'},
                {'key': [('user_id', 1)], 'name': 'user_id_idx'},
                {'key': [('action', 1)], 'name': 'action_idx'}
            ]
        }

        for collection_name, indexes in collections.items():
            if collection_name not in self.db.list_collection_names():
                self.db.create_collection(collection_name)

            existing_indexes = self.db[collection_name].index_information()
            for index in indexes:
                index_name = index.get('name', '_'.join([f[0] for f in index['key']]))
                if index_name not in existing_indexes:
                    try:
                        self.db[collection_name].create_index(
                            index['key'],
                            unique=index.get('unique', False),
                            name=index_name
                        )
                    except Exception as e:
                        print(f"{Fore.YELLOW}WARN: Could not create index {index_name}: {e}")

    def create_researcher(self, researcher_data: Dict) -> Optional[str]:
        try:
            researcher_data['created_at'] = datetime.utcnow()
            researcher_data['updated_at'] = datetime.utcnow()

            result = self.db.researchers.insert_one(researcher_data)
            return str(result.inserted_id)
        except DuplicateKeyError:
            print(f"{Fore.RED}FAIL: Email already exists")
            return None
        except PyMongoError as e:
            print(f"{Fore.RED}FAIL: Error creating researcher: {e}")
            return None

    def get_researcher(self, researcher_id: str) -> Optional[Dict]:
        try:
            researcher = self.db.researchers.find_one({'_id': ObjectId(researcher_id)})
            if researcher:
                researcher['_id'] = str(researcher['_id'])
            return researcher
        except PyMongoError as e:
            print(f"{Fore.RED}FAIL: Error getting researcher: {e}")
            return None

    def get_researcher_by_email(self, email: str) -> Optional[Dict]:
        try:
            researcher = self.db.researchers.find_one({'email': email})
            if researcher:
                researcher['_id'] = str(researcher['_id'])
            return researcher
        except PyMongoError as e:
            print(f"{Fore.RED}FAIL: Error getting researcher by email: {e}")
            return None

    def update_researcher(self, researcher_id: str, update_data: Dict) -> bool:
        try:
            update_operation = {'$set': {'updated_at': datetime.utcnow()}}

            for key, value in update_data.items():
                if isinstance(value, dict) and key.startswith('$'):
                    if key not in update_operation:
                        update_operation[key] = {}
                    update_operation[key].update(value)
                else:
                    if '$set' not in update_operation:
                        update_operation['$set'] = {}
                    update_operation['$set'][key] = value

            result = self.db.researchers.update_one(
                {'_id': ObjectId(researcher_id)},
                update_operation
            )
            return result.modified_count > 0
        except PyMongoError as e:
            print(f"{Fore.RED}FAIL: Error updating researcher: {e}")
            return False

    def delete_researcher(self, researcher_id: str) -> bool:
        try:
            result = self.db.researchers.update_one(
                {'_id': ObjectId(researcher_id)},
                {'$set': {'profile_status': 'deleted', 'updated_at': datetime.utcnow()}}
            )
            return result.modified_count > 0
        except PyMongoError as e:
            print(f"{Fore.RED}FAIL: Error deleting researcher: {e}")
            return False

    def search_researchers(self, query: Dict, limit: int = 20) -> List[Dict]:
        try:
            researchers = self.db.researchers.find(query).limit(limit)
            result = []
            for researcher in researchers:
                researcher['_id'] = str(researcher['_id'])
                result.append(researcher)
            return result
        except PyMongoError as e:
            print(f"{Fore.RED}FAIL: Error searching researchers: {e}")
            return []

    def create_project(self, project_data: Dict) -> Optional[str]:
        try:
            project_data['created_at'] = datetime.utcnow()
            project_data['updated_at'] = datetime.utcnow()

            result = self.db.projects.insert_one(project_data)
            return str(result.inserted_id)
        except PyMongoError as e:
            print(f"{Fore.RED}FAIL: Error creating project: {e}")
            return None

    def get_project(self, project_id: str) -> Optional[Dict]:
        try:
            project = self.db.projects.find_one({'_id': ObjectId(project_id)})
            if project:
                project['_id'] = str(project['_id'])
            return project
        except PyMongoError as e:
            print(f"{Fore.RED}FAIL: Error getting project: {e}")
            return None

    def update_project(self, project_id: str, update_data: Dict) -> bool:
        try:
            update_data['updated_at'] = datetime.utcnow()
            result = self.db.projects.update_one(
                {'_id': ObjectId(project_id)},
                {'$set': update_data}
            )
            return result.modified_count > 0
        except PyMongoError as e:
            print(f"{Fore.RED}FAIL: Error updating project: {e}")
            return False

    def add_project_participant(self, project_id: str, researcher_id: str) -> bool:
        try:
            result = self.db.projects.update_one(
                {'_id': ObjectId(project_id)},
                {'$addToSet': {'participants': researcher_id}}
            )
            return result.modified_count > 0
        except PyMongoError as e:
            print(f"{Fore.RED}FAIL: Error adding participant: {e}")
            return False

    def create_publication(self, publication_data: Dict) -> Optional[str]:
        try:
            publication_data['created_at'] = datetime.utcnow()
            publication_data['updated_at'] = datetime.utcnow()

            result = self.db.publications.insert_one(publication_data)
            return str(result.inserted_id)
        except PyMongoError as e:
            print(f"{Fore.RED}FAIL: Error creating publication: {e}")
            return None

    def get_publications_by_researcher(self, researcher_id: str) -> List[Dict]:
        try:
            publications = self.db.publications.find({
                'authors.researcher_id': researcher_id
            })
            result = []
            for pub in publications:
                pub['_id'] = str(pub['_id'])
                result.append(pub)
            return result
        except PyMongoError as e:
            print(f"{Fore.RED}FAIL: Error getting publications: {e}")
            return []

    def get_researcher_stats(self, researcher_id: str) -> Dict:
        try:
            projects_count = self.db.projects.count_documents({
                'participants': researcher_id
            })

            publications_count = self.db.publications.count_documents({
                'authors.researcher_id': researcher_id
            })

            return {
                'projects_count': projects_count,
                'publications_count': publications_count
            }
        except PyMongoError as e:
            print(f"{Fore.RED}FAIL: Error getting stats: {e}")
            return {'projects_count': 0, 'publications_count': 0}

    def get_top_researchers(self, limit: int = 10) -> List[Dict]:
        try:
            pipeline = [
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
                        'name': 1,
                        'email': 1,
                        'department': 1,
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

            result = list(self.db.researchers.aggregate(pipeline))
            for item in result:
                item['_id'] = str(item['_id'])
            return result
        except PyMongoError as e:
            print(f"{Fore.RED}FAIL: Error getting top researchers: {e}")
            return []

    def get_pending_researchers(self) -> List[Dict]:
        try:
            researchers = self.db.researchers.find({
                'profile_status': 'pending'
            })
            result = []
            for researcher in researchers:
                researcher['_id'] = str(researcher['_id'])
                result.append(researcher)
            return result
        except PyMongoError as e:
            print(f"{Fore.RED}FAIL: Error getting pending researchers: {e}")
            return []

    def approve_researcher(self, researcher_id: str) -> bool:
        try:
            result = self.db.researchers.update_one(
                {'_id': ObjectId(researcher_id)},
                {'$set': {'profile_status': 'approved', 'updated_at': datetime.utcnow()}}
            )
            return result.modified_count > 0
        except PyMongoError as e:
            print(f"{Fore.RED}FAIL: Error approving researcher: {e}")
            return False

    def log_activity(self, user_id: str, action: str, details: Dict = None) -> bool:
        try:
            log_entry = {
                'user_id': user_id,
                'action': action,
                'details': details or {},
                'timestamp': datetime.utcnow(),
                'ip_address': '127.0.0.1'
            }
            self.db.logs.insert_one(log_entry)
            return True
        except PyMongoError as e:
            print(f"{Fore.RED}FAIL: Error logging activity: {e}")
            return False

    def close(self):
        if self.client:
            self.client.close()
            print("MongoDB connection closed")

mongodb = MongoDBManager()

def get_pending_researchers(self):
    try:
        researchers = self.db.researchers.find({
            'profile_status': 'pending'
        })
        result = []
        for researcher in researchers:
            researcher['_id'] = str(researcher['_id'])
            result.append(researcher)
        return result
    except PyMongoError as e:
        print(f"{Fore.RED}FAIL: Error getting pending researchers: {e}")
        return []

    def create_admin(self, admin_data: Dict) -> Optional[str]:
        try:
            admin_data['created_at'] = datetime.utcnow()
            admin_data['updated_at'] = datetime.utcnow()

            result = self.db.admins.insert_one(admin_data)
            return str(result.inserted_id)
        except DuplicateKeyError:
            print(f"{Fore.RED}FAIL: Email already exists for admin")
            return None
        except PyMongoError as e:
            print(f"{Fore.RED}FAIL: Error creating admin: {e}")
            return None

    def get_admin_by_email(self, email: str) -> Optional[Dict]:
        try:
            admin = self.db.admins.find_one({'email': email})
            if admin:
                admin['_id'] = str(admin['_id'])
            return admin
        except PyMongoError as e:
            print(f"{Fore.RED}FAIL: Error getting admin by email: {e}")
            return None

    def get_admin(self, admin_id: str) -> Optional[Dict]:
        try:
            admin = self.db.admins.find_one({'_id': ObjectId(admin_id)})
            if admin:
                admin['_id'] = str(admin['_id'])
            return admin
        except PyMongoError as e:
            print(f"{Fore.RED}FAIL: Error getting admin: {e}")
            return None

    def update_admin(self, admin_id: str, update_data: Dict) -> bool:
        try:
            update_data['updated_at'] = datetime.utcnow()
            result = self.db.admins.update_one(
                {'_id': ObjectId(admin_id)},
                {'$set': update_data}
            )
            return result.modified_count > 0
        except PyMongoError as e:
            print(f"{Fore.RED}FAIL: Error updating admin: {e}")
            return False

    def create_admin(self, admin_data: Dict) -> Optional[str]:
        try:
            admin_data['created_at'] = datetime.utcnow()
            admin_data['updated_at'] = datetime.utcnow()

            result = self.db.admins.insert_one(admin_data)
            return str(result.inserted_id)
        except DuplicateKeyError:
            print(f"{Fore.RED}FAIL: Email already exists for admin")
            return None
        except PyMongoError as e:
            print(f"{Fore.RED}FAIL: Error creating admin: {e}")
            return None

    def get_admin_by_email(self, email: str) -> Optional[Dict]:
        try:
            admin = self.db.admins.find_one({'email': email})
            if admin:
                admin['_id'] = str(admin['_id'])
            return admin
        except PyMongoError as e:
            print(f"{Fore.RED}FAIL: Error getting admin by email: {e}")
            return None

    def get_admin(self, admin_id: str) -> Optional[Dict]:
        try:
            admin = self.db.admins.find_one({'_id': ObjectId(admin_id)})
            if admin:
                admin['_id'] = str(admin['_id'])
            return admin
        except PyMongoError as e:
            print(f"{Fore.RED}FAIL: Error getting admin: {e}")
            return None

    def update_admin(self, admin_id: str, update_data: Dict) -> bool:
        try:
            update_data['updated_at'] = datetime.utcnow()
            result = self.db.admins.update_one(
                {'_id': ObjectId(admin_id)},
                {'$set': update_data}
            )
            return result.modified_count > 0
        except PyMongoError as e:
            print(f"{Fore.RED}FAIL: Error updating admin: {e}")
            return False