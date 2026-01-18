from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from app.database.redis import redis_manager
from app.database.mongodb import mongodb
from colorama import Fore, Style

class CacheService:
    @staticmethod
    def cache_system_stats(ttl: int = 300) -> bool:
        if not redis_manager.is_connected():
            return False

        try:
            stats = {
                'timestamp': datetime.utcnow().isoformat(),
                'researchers_count': mongodb.db.researchers.count_documents({}),
                'projects_count': mongodb.db.projects.count_documents({}),
                'publications_count': mongodb.db.publications.count_documents({}),
                'admins_count': mongodb.db.admins.count_documents({})
            }

            redis_manager.cache_set("system:stats", stats, ttl)
            print(f"{Fore.GREEN}Cached system stats")
            return True
        except Exception as e:
            print(f"{Fore.RED}Error caching stats: {e}")
            return False

    @staticmethod
    def get_cached_stats():
        if not redis_manager.is_connected():
            return None
        return redis_manager.cache_get("system:stats")

    @staticmethod
    def cache_top_researchers(limit=10, ttl=600):
        if not redis_manager.is_connected():
            return False

        try:
            from app.services.researcher_service import ResearcherService
            researchers = ResearcherService.get_top_researchers(limit)
            redis_manager.cache_set(f"top_researchers:{limit}", researchers, ttl)
            print(f"{Fore.GREEN}Cached top {limit} researchers")
            return True
        except Exception as e:
            print(f"{Fore.RED}Error caching researchers: {e}")
            return False

    @staticmethod
    def cache_collaboration_pairs(limit=10, ttl=600):
        if not redis_manager.is_connected():
            return False

        try:
            from app.services.collaboration_service import CollaborationService
            pairs = CollaborationService.get_most_collaborative_pairs(limit)
            redis_manager.cache_set(f"collab_pairs:{limit}", pairs, ttl)
            print(f"{Fore.GREEN}Cached top {limit} collaboration pairs")
            return True
        except Exception as e:
            print(f"{Fore.RED}Error caching pairs: {e}")
            return False

    @staticmethod
    def get_cache_info():
        if not redis_manager.is_connected():
            return {'status': 'disconnected'}

        try:
            keys = redis_manager.client.keys("*")
            key_types = {}
            for key in keys:
                key_type = redis_manager.client.type(key)
                key_types[key_type] = key_types.get(key_type, 0) + 1

            return {
                'status': 'connected',
                'total_keys': len(keys),
                'key_types': key_types,
                'memory': redis_manager.client.info().get('used_memory_human', 'N/A')
            }
        except:
            return {'status': 'error'}

    @staticmethod
    def show_all_cache():
        if not redis_manager.is_connected():
            print(f"{Fore.RED}Redis not connected")
            return

        keys = redis_manager.client.keys("*")
        print(f"{Fore.CYAN}Redis Cache Contents ({len(keys)} keys):")
        print(f"{Fore.CYAN}{'='*60}")

        for key in sorted(keys):
            key_type = redis_manager.client.type(key)
            ttl = redis_manager.client.ttl(key)
            value = None

            if key_type == 'string':
                value = redis_manager.client.get(key)
                if value and len(value) > 100:
                    value = value[:100] + "..."
            elif key_type == 'hash':
                value = redis_manager.client.hgetall(key)

            print(f"{Fore.YELLOW}{key:30} {Fore.WHITE}({key_type}) TTL:{ttl:4}s")
            if value:
                print(f"  {Fore.GREEN}{str(value)[:80]}")

        print(f"{Fore.CYAN}{'='*60}")