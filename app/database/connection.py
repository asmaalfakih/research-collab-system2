import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project path to sys.path
sys.path.append(str(Path(__file__).parent.parent.parent))

load_dotenv()


class DatabaseConfig:
    """Database settings from .env file"""

    @staticmethod
    def get_mongodb_config():
        return {
            'uri': os.getenv('MONGODB_URI', 'mongodb://localhost:27017'),
            'db_name': os.getenv('MONGODB_DB_NAME', 'research_collab_db'),
            'timeout': 5000
        }

    @staticmethod
    def get_neo4j_config():
        return {
            'uri': os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
            'username': os.getenv('NEO4J_USERNAME', 'neo4j'),
            'password': os.getenv('NEO4J_PASSWORD', 'research123'),
            'database': os.getenv('NEO4J_DATABASE', 'neo4j')
        }

    @staticmethod
    def get_redis_config():
        return {
            'host': os.getenv('REDIS_HOST', 'localhost'),
            'port': int(os.getenv('REDIS_PORT', 6379)),
            'password': os.getenv('REDIS_PASSWORD'),
            'username': os.getenv('REDIS_USERNAME', 'default'),
            'ssl': os.getenv('REDIS_SSL', 'False').lower() == 'true',
            'decode_responses': True
        }