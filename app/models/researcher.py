from datetime import datetime
from typing import List, Optional, Dict, Any
from bson import ObjectId
import bcrypt

class Researcher:

    def __init__(self, **kwargs):
        self._id = kwargs.get('_id', ObjectId())
        self.name = kwargs.get('name', '')
        self.email = kwargs.get('email', '')
        self.password = kwargs.get('password', '')
        self.department = kwargs.get('department', '')
        self.contact = kwargs.get('contact', {
            'phone': '',
            'city': 'Hebron',
            'street': ''
        })
        self.profile_status = kwargs.get('profile_status', 'pending')
        self.role = kwargs.get('role', 'researcher')
        self.research_interests = kwargs.get('research_interests', [])
        self.projects = kwargs.get('projects', [])
        self.publications = kwargs.get('publications', [])
        self.created_at = kwargs.get('created_at', datetime.utcnow())
        self.updated_at = kwargs.get('updated_at', datetime.utcnow())
        self.last_login = kwargs.get('last_login')
        self.login_count = kwargs.get('login_count', 0)

    @staticmethod
    def hash_password(password: str) -> str:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'email': self.email,
            'password': self.password,
            'department': self.department,
            'contact': self.contact,
            'profile_status': self.profile_status,
            'role': self.role,
            'research_interests': self.research_interests,
            'projects': self.projects,
            'publications': self.publications,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'last_login': self.last_login,
            'login_count': self.login_count
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Researcher':
        return cls(**data)

    def validate(self) -> List[str]:
        errors = []

        if not self.name or len(self.name.strip()) < 2:
            errors.append("Name must be at least 2 characters")

        if not self.email or '@' not in self.email:
            errors.append("Valid email is required")

        if not self.department:
            errors.append("Department is required")

        if self.profile_status not in ['pending', 'approved', 'rejected', 'deleted']:
            errors.append("Invalid profile status")

        if self.role not in ['researcher', 'admin']:
            errors.append("Invalid role")

        return errors

    def get_public_profile(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'email': self.email,
            'department': self.department,
            'research_interests': self.research_interests,
            'projects_count': len(self.projects),
            'publications_count': len(self.publications),
            'profile_status': self.profile_status
        }

class Admin(Researcher):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.role = 'admin'
        self.permissions = kwargs.get('permissions', [
            'manage_users',
            'approve_profiles',
            'view_analytics',
            'manage_system'
        ])
        self.admin_level = kwargs.get('admin_level', 'super_admin')

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data['permissions'] = self.permissions
        data['admin_level'] = self.admin_level
        return data