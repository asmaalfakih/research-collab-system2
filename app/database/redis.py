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
            # Basic connection settings
            connection_kwargs = {
                'host': config['host'],
                'port': config['port'],
                'decode_responses': config['decode_responses'],
                'socket_timeout': 10,
                'socket_connect_timeout': 10,
            }

            # Add username and password if available
            if config.get('username'):
                connection_kwargs['username'] = config['username']
            if config.get('password'):
                connection_kwargs['password'] = config['password']

            # Simplified SSL handling
            # Most Redis Cloud issues are solved by setting REDIS_SSL=False
            if config.get('ssl'):
                # Convert value to boolean
                ssl_value = str(config['ssl']).lower()
                if ssl_value in ['true', '1', 'yes']:
                    connection_kwargs['ssl'] = True
                    # Remove ssl_cert_reqs to avoid WRONG_VERSION_NUMBER issue
                    # connection_kwargs['ssl_cert_reqs'] = ssl.CERT_NONE
                else:
                    connection_kwargs['ssl'] = False

            print(f"   SSL setting: {connection_kwargs.get('ssl', False)}")

            # Attempt connection
            self.client = redis.Redis(**connection_kwargs)

            # Test connection
            if self.client.ping():
                print(f"{Fore.GREEN}PASS: Redis connected successfully!")

                # Additional test
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

    # ============= Session Management =============

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
            # Save session
            self.client.hset(session_key, mapping=session_data)
            self.client.expire(session_key, ttl_hours * 3600)

            # Update user's active sessions list
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

            # Check expiration
            expires_at = datetime.fromisoformat(session_data.get('expires_at', ''))
            if datetime.utcnow() > expires_at:
                self.delete_session(session_id)
                return None

            # Update last activity
            session_data['last_activity'] = datetime.utcnow().isoformat()
            self.client.hset(session_key, 'last_activity', session_data['last_activity'])

            # Renew session if about to expire
            ttl = self.client.ttl(session_key)
            if ttl < 3600:  # If less than 1 hour remaining
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

    # ============= Caching System =============

    def cache_set(self, key: str, value: Any, ttl_seconds: int = 300) -> bool:
        """Save data to cache"""
        if not self.is_connected():
            return False

        try:
            import json
            from datetime import datetime, date

            # Helper function to serialize various date types
            def json_serializer(obj):
                """Custom JSON serializer for various types"""
                # Handle Python datetime and date
                if isinstance(obj, (datetime, date)):
                    return obj.isoformat()

                # Handle Neo4j Date type
                try:
                    # Check if it's a Neo4j Date object
                    if hasattr(obj, 'iso_format'):
                        return obj.iso_format()
                    if hasattr(obj, 'to_native'):
                        return obj.to_native().isoformat()
                    if hasattr(obj, 'isoformat'):
                        return obj.isoformat()
                except:
                    pass

                # Handle other unsupported types
                raise TypeError(f"Type {type(obj)} not serializable")

            # Convert to JSON with custom serializer
            if isinstance(value, (dict, list, tuple)):
                try:
                    value = json.dumps(value, default=json_serializer, ensure_ascii=False)
                except TypeError:
                    # Fallback: convert Neo4j objects to dict first
                    try:
                        # Try to convert Neo4j Record objects
                        if hasattr(value, 'items'):
                            value = dict(value.items())
                            value = json.dumps(value, default=json_serializer, ensure_ascii=False)
                        else:
                            # Last resort: convert to string
                            value = str(value)
                    except:
                        value = str(value)

            # Store in Redis
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

    # ============= Simplified Analytics =============

    def track_activity(self, user_id: str, action: str, metadata: Dict = None) -> bool:
        """Track user activity (without Redis if disabled)"""
        if not self.is_connected():
            # Log to memory or temporary file
            print(f"ACTIVITY (no Redis): {user_id} - {action}")
            return False

        try:
            activity = {
                'user_id': user_id,
                'action': action,
                'metadata': metadata or {},
                'timestamp': datetime.utcnow().isoformat()
            }

            # Store in activities list
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

    # ============= System Stats =============

    def get_system_stats(self) -> Dict:
        """Get system statistics"""
        if not self.is_connected():
            return {
                'status': 'disabled',
                'message': 'Redis cache is disabled'
            }

        try:
            info = self.client.info()

            # Extract important information
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

    # ============= Utility Methods =============

    def close(self):
        """Close connection"""
        if self.client:
            try:
                self.client.close()
                print("Redis connection closed")
            except:
                pass


# Create global instance
redis_manager = RedisManager()