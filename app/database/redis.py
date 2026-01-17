import redis
import ssl
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Union
from .connection import DatabaseConfig
from colorama import Fore, Style


class RedisManager:
    """Redis Operations Manager - Caching and Sessions (updated version)"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_redis()
        return cls._instance

    def _init_redis(self):
        """Create Redis connection with simplified SSL support"""
        config = DatabaseConfig.get_redis_config()

        print(f"CONNECT: Attempting Redis connection to {config['host']}:{config['port']}")

        try:
            connection_kwargs = {
                'host': config['host'],
                'port': config['port'],
                'decode_responses': config['decode_responses'],
                'socket_timeout': 10,
                'socket_connect_timeout': 10,
            }

            if config.get('username'):
                connection_kwargs['username'] = config['username']
            if config.get('password'):
                connection_kwargs['password'] = config['password']

            ssl_value = str(config.get('ssl', False)).lower()
            if ssl_value in ['true', '1', 'yes']:
                connection_kwargs['ssl'] = True

            print(f"   SSL setting: {connection_kwargs.get('ssl', False)}")

            self.client = redis.Redis(**connection_kwargs)

            if self.client.ping():
                print(f"{Fore.GREEN}PASS: Redis connected successfully!")

                try:
                    self.client.set("connection_test", "ok", ex=5)
                    test_result = self.client.get("connection_test")
                    if test_result == "ok":
                        print("   Connection test: PASSED")
                    else:
                        print("   Connection test: FAILED")
                except:
                    print("   Basic operations: OK")

            else:
                raise ConnectionError("Redis ping failed")

        except redis.AuthenticationError as e:
            print(f"{Fore.RED}FAIL: Redis authentication failed: {e}")
            print("TIP: Please check username and password in .env")
            self._disable_redis()
        except redis.ConnectionError as e:
            print(f"{Fore.RED}FAIL: Redis connection error: {e}")
            print("TIP: Common solutions:")
            print("   1. Set REDIS_SSL=False in .env")
            print("   2. Check network connectivity")
            print("   3. Verify Redis Cloud is running")
            self._disable_redis()
        except Exception as e:
            print(f"{Fore.YELLOW}WARN: Redis connection failed: {e}")
            self._disable_redis()

    def _disable_redis(self):
        """Temporarily disable Redis to continue without cache"""
        print(f"{Fore.YELLOW}WARN: Redis cache is DISABLED for this session")
        print("TIP: System will work but without caching features")
        print("TIP: Basic functionality will still work")
        self.client = None

    def is_connected(self):
        """Check connection"""
        return self.client is not None and self.client.ping()

    def create_session(self, user_id: str, user_data: Dict, ttl_hours: int = 24) -> Optional[str]:
        """Create new session"""
        if not self.is_connected():
            print(f"{Fore.YELLOW}WARN: Redis not connected - session not created")
            return None

        import secrets
        session_id = secrets.token_urlsafe(32)
        session_key = f"session:{session_id}"

        session_data = {
            **user_data,
            'session_id': session_id,
            'user_id': user_id,
            'created_at': datetime.utcnow().isoformat(),
            'expires_at': (datetime.utcnow() + timedelta(hours=ttl_hours)).isoformat(),
            'last_activity': datetime.utcnow().isoformat()
        }

        try:
            self.client.hset(session_key, mapping=session_data)
            self.client.expire(session_key, ttl_hours * 3600)

            user_sessions_key = f"user_sessions:{user_id}"
            self.client.sadd(user_sessions_key, session_id)
            self.client.expire(user_sessions_key, ttl_hours * 3600)

            return session_id
        except Exception as e:
            print(f"{Fore.RED}FAIL: Error creating session: {e}")
            return None

    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session data"""
        if not self.is_connected():
            return None

        session_key = f"session:{session_id}"

        try:
            session_data = self.client.hgetall(session_key)
            if not session_data:
                return None

            expires_at = datetime.fromisoformat(session_data.get('expires_at', ''))
            if datetime.utcnow() > expires_at:
                self.delete_session(session_id)
                return None

            session_data['last_activity'] = datetime.utcnow().isoformat()
            self.client.hset(session_key, 'last_activity', session_data['last_activity'])

            ttl = self.client.ttl(session_key)
            if ttl < 3600:
                self.client.expire(session_key, 24 * 3600)

            return session_data
        except Exception as e:
            print(f"{Fore.RED}FAIL: Error getting session: {e}")
            return None

    def delete_session(self, session_id: str) -> bool:
        """Delete session"""
        if not self.is_connected():
            return False

        try:
            session_key = f"session:{session_id}"
            return bool(self.client.delete(session_key))
        except Exception as e:
            print(f"{Fore.RED}FAIL: Error deleting session: {e}")
            return False

    def cache_get(self, key: str) -> Optional[Any]:
        """Get data from cache"""
        if not self.is_connected():
            return None

        try:
            value = self.client.get(key)
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return None
        except Exception as e:
            print(f"{Fore.RED}FAIL: Cache get error: {e}")
            return None

    def cache_set(self, key: str, value: Any, ttl_seconds: int = 300) -> bool:
        """Save data to cache"""
        if not self.is_connected():
            return False

        try:
            import json
            from datetime import datetime, date

            def json_serializer(obj):
                if isinstance(obj, (datetime, date)):
                    return obj.isoformat()
                try:
                    if hasattr(obj, 'iso_format'):
                        return obj.iso_format()
                    if hasattr(obj, 'to_native'):
                        return obj.to_native().isoformat()
                    if hasattr(obj, 'isoformat'):
                        return obj.isoformat()
                except:
                    pass
                raise TypeError(f"Type {type(obj)} not serializable")

            if isinstance(value, (dict, list, tuple)):
                try:
                    value = json.dumps(value, default=json_serializer, ensure_ascii=False)
                except TypeError:
                    try:
                        if hasattr(value, 'items'):
                            value = dict(value.items())
                            value = json.dumps(value, default=json_serializer, ensure_ascii=False)
                        else:
                            value = str(value)
                    except:
                        value = str(value)

            self.client.set(key, value, ex=ttl_seconds)
            return True
        except Exception as e:
            print(f"{Fore.RED}FAIL: Cache set error: {e}")
            return False

    def cache_delete(self, key: str) -> bool:
        """Delete from cache"""
        if not self.is_connected():
            return False

        return bool(self.client.delete(key))

    def track_activity(self, user_id: str, action: str, metadata: Dict = None) -> bool:
        """Track user activity (without Redis if disabled)"""
        if not self.is_connected():
            print(f"ACTIVITY (no Redis): {user_id} - {action}")
            return False

        try:
            activity = {
                'user_id': user_id,
                'action': action,
                'metadata': metadata or {},
                'timestamp': datetime.utcnow().isoformat()
            }

            self.client.lpush("recent_activities", json.dumps(activity))
            self.client.ltrim("recent_activities", 0, 99)

            return True
        except Exception as e:
            print(f"{Fore.RED}FAIL: Error tracking activity: {e}")
            return False

    def get_recent_activities(self, limit: int = 20) -> List[Dict]:
        """Get recent activities"""
        if not self.is_connected():
            return []

        try:
            activities = self.client.lrange("recent_activities", 0, limit - 1)
            result = []
            for activity_json in activities:
                try:
                    result.append(json.loads(activity_json))
                except json.JSONDecodeError:
                    continue
            return result
        except Exception as e:
            print(f"{Fore.RED}FAIL: Error getting recent activities: {e}")
            return []

    def get_system_stats(self) -> Dict:
        """Get system statistics"""
        if not self.is_connected():
            return {
                'status': 'disabled',
                'message': 'Redis cache is disabled'
            }

        try:
            info = self.client.info()

            stats = {
                'status': 'connected',
                'version': info.get('redis_version', 'unknown'),
                'memory_used': info.get('used_memory_human', 'unknown'),
                'connected_clients': info.get('connected_clients', 0),
                'total_keys': self.client.dbsize()
            }

            return stats
        except Exception as e:
            print(f"{Fore.RED}FAIL: Error getting system stats: {e}")
            return {'status': 'error', 'message': str(e)}

    def close(self):
        """Close connection"""
        if self.client:
            try:
                self.client.close()
                print("Redis connection closed")
            except:
                pass


redis_manager = RedisManager()