from datetime import datetime
from typing import Dict, Any, List
from enum import Enum


class CollaborationType(Enum):
    CO_AUTHORSHIP = "co_authorship"
    SUPERVISION = "supervision"
    TEAMWORK = "teamwork"
    PROJECT_PARTICIPATION = "project_participation"


class Collaboration:
    def __init__(self, **kwargs):
        self.relationship_type = kwargs.get('relationship_type', '')
        self.researcher1_id = kwargs.get('researcher1_id', '')
        self.researcher2_id = kwargs.get('researcher2_id', '')
        self.collaboration_count = kwargs.get('collaboration_count', 0)
        self.first_collaboration = kwargs.get('first_collaboration')
        self.last_collaboration = kwargs.get('last_collaboration')
        self.projects = kwargs.get('projects', [])
        self.publications = kwargs.get('publications', [])
        self.strength_score = kwargs.get('strength_score', 0.0)
        self.created_at = kwargs.get('created_at', datetime.utcnow())
        self.updated_at = kwargs.get('updated_at', datetime.utcnow())

    def to_dict(self) -> Dict[str, Any]:
        return {
            'relationship_type': self.relationship_type,
            'researcher1_id': self.researcher1_id,
            'researcher2_id': self.researcher2_id,
            'collaboration_count': self.collaboration_count,
            'first_collaboration': self.first_collaboration,
            'last_collaboration': self.last_collaboration,
            'projects': self.projects,
            'publications': self.publications,
            'strength_score': self.strength_score,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Collaboration':
        return cls(**data)

    def increment_collaboration(self, project_id: str = None, publication_id: str = None) -> None:
        self.collaboration_count += 1

        if project_id and project_id not in self.projects:
            self.projects.append(project_id)

        if publication_id and publication_id not in self.publications:
            self.publications.append(publication_id)

        if not self.first_collaboration:
            self.first_collaboration = datetime.utcnow().isoformat()

        self.last_collaboration = datetime.utcnow().isoformat()
        self.updated_at = datetime.utcnow()
        self._calculate_strength_score()

    def _calculate_strength_score(self) -> None:
        base_score = self.collaboration_count * 10

        type_multiplier = 1.0
        if self.relationship_type == CollaborationType.CO_AUTHORSHIP.value:
            type_multiplier += 0.3
        elif self.relationship_type == CollaborationType.TEAMWORK.value:
            type_multiplier += 0.2
        elif self.relationship_type == CollaborationType.SUPERVISION.value:
            type_multiplier += 0.5

        joint_work_score = (len(self.projects) * 15) + (len(self.publications) * 20)
        self.strength_score = (base_score * type_multiplier) + joint_work_score

    def get_strength_level(self) -> str:
        if self.strength_score >= 100:
            return "Very Strong"
        elif self.strength_score >= 50:
            return "Strong"
        elif self.strength_score >= 20:
            return "Moderate"
        elif self.strength_score >= 5:
            return "Weak"
        else:
            return "New"