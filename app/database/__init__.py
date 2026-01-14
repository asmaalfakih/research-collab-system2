from .mongodb import mongodb
from .neo4j import neo4j
from .redis import redis_manager

__all__ = ['mongodb', 'neo4j', 'redis_manager']


class DatabaseManager:
    """Unified Manager for All Databases"""

    @staticmethod
    def check_all_connections():
        """Check all database connections"""
        results = {}

        # Check MongoDB
        if mongodb.client:
            try:
                mongodb.client.admin.command('ping')
                results['mongodb'] = {
                    'status': 'connected',
                    'database': mongodb.db.name,
                    'collections': mongodb.db.list_collection_names()
                }
            except Exception as e:
                results['mongodb'] = {'status': 'error', 'message': str(e)}
        else:
            results['mongodb'] = {'status': 'disconnected'}

        # Check Neo4j
        if neo4j.driver:
            try:
                with neo4j.driver.session() as session:
                    session.run("RETURN 1")
                    result = session.run("MATCH (n) RETURN count(n) AS count")
                    count = result.single()["count"]
                    results['neo4j'] = {
                        'status': 'connected',
                        'node_count': count
                    }
            except Exception as e:
                results['neo4j'] = {'status': 'error', 'message': str(e)}
        else:
            results['neo4j'] = {'status': 'disconnected'}

        # Check Redis
        if redis_manager.is_connected():
            try:
                info = redis_manager.get_system_stats()
                results['redis'] = {
                    'status': 'connected',
                    'info': info
                }
            except Exception as e:
                results['redis'] = {'status': 'error', 'message': str(e)}
        else:
            results['redis'] = {'status': 'disconnected'}

        return results

    @staticmethod
    def close_all():
        """Close all connections"""
        if mongodb.client:
            mongodb.close()
        if neo4j.driver:
            neo4j.close()
        if redis_manager.client:
            redis_manager.close()
        print("All database connections closed")


# Create global instance
db_manager = DatabaseManager()