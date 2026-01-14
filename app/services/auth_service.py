import bcrypt
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from app.database.mongodb import mongodb
from app.database.redis import redis_manager
from app.models.researcher import Researcher

# Replace the import with this code
import secrets

def generate_session_token(length=32):
    """Generate secure session token"""
    return secrets.token_urlsafe(length)

class AuthService:
    """Authentication and session management service"""

    @staticmethod
    def register_researcher(data: Dict[str, Any]) -> Tuple[bool, str, Optional[str]]:
        """Register a new researcher"""
        # Validate required fields
        required_fields = ['name', 'email', 'password', 'department']
        for field in required_fields:
            if field not in data or not data[field]:
                return False, None, f"Missing required field: {field}"

        # Check if email already exists
        existing = mongodb.get_researcher_by_email(data['email'])
        if existing:
            return False, None, "Email already registered"

        # Hash password
        hashed_password = Researcher.hash_password(data['password'])
        data['password'] = hashed_password

        # Set default values
        data.setdefault('profile_status', 'pending')
        data.setdefault('role', 'researcher')
        data.setdefault('research_interests', [])
        data.setdefault('contact', {'phone': '', 'city': 'Hebron', 'street': ''})

        # Create researcher
        researcher = Researcher(**data)
        errors = researcher.validate()

        if errors:
            return False, None, "; ".join(errors)

        # Save to MongoDB
        researcher_data = researcher.to_dict()
        researcher_id = mongodb.create_researcher(researcher_data)

        if not researcher_id:
            return False, None, "Failed to create researcher"

        # Create node in Neo4j
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
        """Login user"""
        # Find researcher
        researcher_data = mongodb.get_researcher_by_email(email)

        if not researcher_data:
            return False, None, None, "Invalid email or password"

        # Check account status
        if researcher_data['profile_status'] != 'approved':
            status = researcher_data['profile_status']
            if status == 'pending':
                return False, None, None, "Account pending approval"
            elif status == 'rejected':
                return False, None, None, "Account rejected"
            elif status == 'deleted':
                return False, None, None, "Account deleted"

        # Verify password
        if not Researcher.verify_password(password, researcher_data['password']):
            return False, None, None, "Invalid email or password"

        # Update login data
        mongodb.update_researcher(
            str(researcher_data['_id']),
            {
                'last_login': datetime.utcnow(),
                'login_count': researcher_data.get('login_count', 0) + 1
            }
        )

        # Create session
        session_data = {
            'user_id': str(researcher_data['_id']),
            'email': researcher_data['email'],
            'name': researcher_data['name'],
            'role': researcher_data['role'],
            'department': researcher_data['department'],
            'profile_status': researcher_data['profile_status']
        }

        session_id = redis_manager.create_session(
            str(researcher_data['_id']),
            session_data
        )

        if not session_id:
            return False, None, None, "Failed to create session"

        # Log activity
        redis_manager.track_activity(
            str(researcher_data['_id']),
            'login',
            {'ip': '127.0.0.1', 'timestamp': datetime.utcnow().isoformat()}
        )

        return True, session_id, session_data, "Login successful"

    @staticmethod
    def logout(session_id: str) -> bool:
        """Logout user"""
        # Get session data first
        session_data = redis_manager.get_session(session_id)

        if session_data:
            # Log activity
            redis_manager.track_activity(
                session_data.get('user_id'),
                'logout',
                {'timestamp': datetime.utcnow().isoformat()}
            )

        # Delete session
        return redis_manager.delete_session(session_id)

    @staticmethod
    def validate_session(session_id: str) -> Optional[Dict]:
        """Validate session"""
        session_data = redis_manager.get_session(session_id)

        if not session_data:
            return None

        # Update activity time
        redis_manager.update_session(session_id, {
            'last_activity': datetime.utcnow().isoformat()
        })

        return session_data

    @staticmethod
    def change_password(user_id: str, old_password: str, new_password: str) -> Tuple[bool, str]:
        """Change password"""
        # Get researcher data
        researcher_data = mongodb.get_researcher(user_id)

        if not researcher_data:
            return False, "User not found"

        # Verify old password
        if not Researcher.verify_password(old_password, researcher_data['password']):
            return False, "Current password is incorrect"

        # Hash new password
        hashed_password = Researcher.hash_password(new_password)

        # Update in MongoDB
        success = mongodb.update_researcher(user_id, {'password': hashed_password})

        if success:
            # Log activity
            redis_manager.track_activity(user_id, 'password_change', {
                'timestamp': datetime.utcnow().isoformat()
            })
            return True, "Password changed successfully"
        else:
            return False, "Failed to update password"

    @staticmethod
    def reset_password_request(email: str) -> Tuple[bool, str]:
        """Request password reset"""
        # Find researcher
        researcher_data = mongodb.get_researcher_by_email(email)

        if not researcher_data:
            return False, "If email exists, reset instructions will be sent"

        # Create reset token
        reset_token = secrets.token_urlsafe(32)
        reset_key = f"password_reset:{reset_token}"

        # Store in Redis for 1 hour
        redis_manager.cache_set(reset_key, {
            'user_id': str(researcher_data['_id']),
            'email': email,
            'created_at': datetime.utcnow().isoformat(),
            'expires_at': (datetime.utcnow() + timedelta(hours=1)).isoformat()
        }, ttl_seconds=3600)

        # In reality, send email here
        # For testing, print the token
        print(f"Reset token for {email}: {reset_token}")

        return True, "Reset instructions sent to email"

    @staticmethod
    def reset_password_confirm(reset_token: str, new_password: str) -> Tuple[bool, str]:
        """Confirm password reset"""
        # Get reset data
        reset_key = f"password_reset:{reset_token}"
        reset_data = redis_manager.cache_get(reset_key)

        if not reset_data:
            return False, "Invalid or expired reset token"

        # Hash new password
        hashed_password = Researcher.hash_password(new_password)

        # Update password
        success = mongodb.update_researcher(reset_data['user_id'], {
            'password': hashed_password
        })

        if success:
            # Delete reset token
            redis_manager.cache_delete(reset_key)

            # Log activity
            redis_manager.track_activity(reset_data['user_id'], 'password_reset', {
                'timestamp': datetime.utcnow().isoformat()
            })

            return True, "Password reset successful"
        else:
            return False, "Failed to reset password"