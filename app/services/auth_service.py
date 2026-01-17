import bcrypt
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from app.database.mongodb import mongodb
from app.database.redis import redis_manager
from app.models.researcher import Researcher


class AuthService:
    @staticmethod
    def register_researcher(data: Dict[str, Any]) -> Tuple[bool, str, Optional[str]]:
        required_fields = ['name', 'email', 'password', 'department']
        for field in required_fields:
            if field not in data or not data[field]:
                return False, None, f"Missing required field: {field}"

        existing = mongodb.get_researcher_by_email(data['email'])
        if existing:
            return False, None, "Email already registered"

        hashed_password = Researcher.hash_password(data['password'])
        data['password'] = hashed_password

        data.setdefault('profile_status', 'pending')
        data.setdefault('role', 'researcher')
        data.setdefault('research_interests', [])
        data.setdefault('contact', {'phone': '', 'city': 'Hebron', 'street': ''})

        researcher = Researcher(**data)
        errors = researcher.validate()

        if errors:
            return False, None, "; ".join(errors)

        researcher_data = researcher.to_dict()
        researcher_id = mongodb.create_researcher(researcher_data)

        if not researcher_id:
            return False, None, "Failed to create researcher"

        from app.database.neo4j import neo4j
        neo4j.create_researcher_node({
            'id': researcher_id,
            'name': data['name'],
            'email': data['email'],
            'department': data['department'],
            'profile_status': data['profile_status']
        })

        return True, researcher_id, "Registration successful. Waiting for admin approval."

    @staticmethod
    def login(email: str, password: str) -> Tuple[bool, Optional[str], Optional[Dict], str]:
        admin_data = mongodb.db.admins.find_one({'email': email})

        if admin_data:
            user_data = admin_data
            user_data['_id'] = str(user_data['_id'])
            user_data['role'] = 'admin'

            if not Researcher.verify_password(password, user_data['password']):
                return False, None, None, "Invalid email or password"

            if user_data.get('profile_status') != 'approved':
                return False, None, None, "Account not approved"

        else:
            researcher_data = mongodb.get_researcher_by_email(email)

            if not researcher_data:
                return False, None, None, "Invalid email or password"

            if researcher_data['profile_status'] != 'approved':
                status = researcher_data['profile_status']
                if status == 'pending':
                    return False, None, None, "Account pending approval"
                elif status == 'rejected':
                    return False, None, None, "Account rejected"
                elif status == 'deleted':
                    return False, None, None, "Account deleted"

            if not Researcher.verify_password(password, researcher_data['password']):
                return False, None, None, "Invalid email or password"

            user_data = researcher_data

        user_id = str(user_data['_id'])

        if user_data['role'] == 'researcher':
            mongodb.update_researcher(
                user_id,
                {
                    'last_login': datetime.utcnow(),
                    'login_count': user_data.get('login_count', 0) + 1
                }
            )

        session_data = {
            'user_id': user_id,
            'email': user_data['email'],
            'name': user_data['name'],
            'role': user_data['role'],
            'department': user_data['department'],
            'profile_status': user_data['profile_status']
        }

        session_id = redis_manager.create_session(
            user_id,
            session_data
        )

        if not session_id:
            return False, None, None, "Failed to create session"

        redis_manager.track_activity(
            user_id,
            'login',
            {'ip': '127.0.0.1', 'timestamp': datetime.utcnow().isoformat()}
        )

        return True, session_id, session_data, "Login successful"

    @staticmethod
    def logout(session_id: str) -> bool:
        session_data = redis_manager.get_session(session_id)

        if session_data:
            redis_manager.track_activity(
                session_data.get('user_id'),
                'logout',
                {'timestamp': datetime.utcnow().isoformat()}
            )

        return redis_manager.delete_session(session_id)

    @staticmethod
    def validate_session(session_id: str) -> Optional[Dict]:
        session_data = redis_manager.get_session(session_id)

        if not session_data:
            return None

        redis_manager.update_session(session_id, {
            'last_activity': datetime.utcnow().isoformat()
        })

        return session_data

    @staticmethod
    def change_password(user_id: str, old_password: str, new_password: str) -> Tuple[bool, str]:
        user_data = mongodb.get_researcher(user_id)

        if not user_data:
            user_data = mongodb.db.admins.find_one({'_id': ObjectId(user_id)})
            if user_data:
                user_data['_id'] = str(user_data['_id'])
                user_data['role'] = 'admin'

        if not user_data:
            return False, "User not found"

        if not Researcher.verify_password(old_password, user_data['password']):
            return False, "Current password is incorrect"

        hashed_password = Researcher.hash_password(new_password)

        if user_data['role'] == 'admin':
            success = mongodb.db.admins.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': {'password': hashed_password}}
            ).modified_count > 0
        else:
            success = mongodb.update_researcher(user_id, {'password': hashed_password})

        if success:
            redis_manager.track_activity(user_id, 'password_change', {
                'timestamp': datetime.utcnow().isoformat()
            })
            return True, "Password changed successfully"
        else:
            return False, "Failed to update password"

    @staticmethod
    def reset_password_request(email: str) -> Tuple[bool, str]:
        admin_data = mongodb.db.admins.find_one({'email': email})
        researcher_data = mongodb.get_researcher_by_email(email)

        if not admin_data and not researcher_data:
            return False, "If email exists, reset instructions will be sent"

        reset_token = secrets.token_urlsafe(32)
        reset_key = f"password_reset:{reset_token}"

        redis_manager.cache_set(reset_key, {
            'email': email,
            'created_at': datetime.utcnow().isoformat(),
            'expires_at': (datetime.utcnow() + timedelta(hours=1)).isoformat()
        }, ttl_seconds=3600)

        print(f"Reset token for {email}: {reset_token}")

        return True, "Reset instructions sent to email"

    @staticmethod
    def reset_password_confirm(reset_token: str, new_password: str) -> Tuple[bool, str]:
        reset_key = f"password_reset:{reset_token}"
        reset_data = redis_manager.cache_get(reset_key)

        if not reset_data:
            return False, "Invalid or expired reset token"

        hashed_password = Researcher.hash_password(new_password)
        email = reset_data['email']

        success = False

        admin_data = mongodb.db.admins.find_one({'email': email})
        if admin_data:
            success = mongodb.db.admins.update_one(
                {'email': email},
                {'$set': {'password': hashed_password}}
            ).modified_count > 0
        else:
            researcher_data = mongodb.get_researcher_by_email(email)
            if researcher_data:
                success = mongodb.update_researcher(
                    str(researcher_data['_id']),
                    {'password': hashed_password}
                )

        if success:
            redis_manager.cache_delete(reset_key)
            redis_manager.track_activity(email, 'password_reset', {
                'timestamp': datetime.utcnow().isoformat()
            })
            return True, "Password reset successful"
        else:
            return False, "Failed to reset password"