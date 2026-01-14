from datetime import datetime
from typing import List, Dict, Any, Optional
from bson import ObjectId


class Project:
    """Research Project Model"""

    def __init__(self, **kwargs):
        self._id = kwargs.get('_id', ObjectId())
        self.title = kwargs.get('title', '')
        self.description = kwargs.get('description', '')
        self.creator_id = kwargs.get('creator_id', '')
        self.creator_name = kwargs.get('creator_name', '')
        self.participants = kwargs.get('participants', [])  # List of researcher IDs
        self.start_date = kwargs.get('start_date', datetime.utcnow().date().isoformat())
        self.end_date = kwargs.get('end_date')
        self.status = kwargs.get('status', 'active')  # active, completed, pending, cancelled
        self.research_area = kwargs.get('research_area', '')
        self.tags = kwargs.get('tags', [])
        self.budget = kwargs.get('budget', 0.0)
        self.funding_source = kwargs.get('funding_source', '')
        self.related_publications = kwargs.get('related_publications', [])  # List of publication IDs
        self.created_at = kwargs.get('created_at', datetime.utcnow())
        self.updated_at = kwargs.get('updated_at', datetime.utcnow())
        self.milestones = kwargs.get('milestones', [])
        self.documents = kwargs.get('documents', [])  # List of document references

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'title': self.title,
            'description': self.description,
            'creator_id': self.creator_id,
            'creator_name': self.creator_name,
            'participants': self.participants,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'status': self.status,
            'research_area': self.research_area,
            'tags': self.tags,
            'budget': self.budget,
            'funding_source': self.funding_source,
            'related_publications': self.related_publications,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'milestones': self.milestones,
            'documents': self.documents
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Project':
        """Create object from dictionary"""
        return cls(**data)

    def validate(self) -> List[str]:
        """Validate data"""
        errors = []

        if not self.title or len(self.title.strip()) < 3:
            errors.append("Project title must be at least 3 characters")

        if not self.creator_id:
            errors.append("Creator ID is required")

        if not self.start_date:
            errors.append("Start date is required")

        if self.status not in ['active', 'completed', 'pending', 'cancelled']:
            errors.append("Invalid project status")

        if self.end_date and self.end_date < self.start_date:
            errors.append("End date cannot be before start date")

        return errors

    def add_participant(self, researcher_id: str) -> bool:
        """Add researcher to project"""
        if researcher_id not in self.participants:
            self.participants.append(researcher_id)
            self.updated_at = datetime.utcnow()
            return True
        return False

    def remove_participant(self, researcher_id: str) -> bool:
        """Remove researcher from project"""
        if researcher_id in self.participants:
            self.participants.remove(researcher_id)
            self.updated_at = datetime.utcnow()
            return True
        return False

    def get_summary(self) -> Dict[str, Any]:
        """Get project summary"""
        return {
            'title': self.title,
            'creator': self.creator_name,
            'participants_count': len(self.participants),
            'status': self.status,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'research_area': self.research_area,
            'publications_count': len(self.related_publications)
        }