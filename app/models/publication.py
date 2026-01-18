from datetime import datetime
from typing import List, Dict, Any, Optional
from bson import ObjectId

class Author:

    def __init__(self, **kwargs):
        self.researcher_id = kwargs.get('researcher_id', '')
        self.name = kwargs.get('name', '')
        self.order = kwargs.get('order', 1)
        self.affiliation = kwargs.get('affiliation', '')
        self.contribution = kwargs.get('contribution', '')

    def to_dict(self) -> Dict[str, Any]:
        return {
            'researcher_id': self.researcher_id,
            'name': self.name,
            'order': self.order,
            'affiliation': self.affiliation,
            'contribution': self.contribution
        }

class Publication:

    def __init__(self, **kwargs):
        self._id = kwargs.get('_id', ObjectId())
        self.title = kwargs.get('title', '')
        self.authors = kwargs.get('authors', [])
        self.year = kwargs.get('year', datetime.now().year)
        self.doi = kwargs.get('doi', '')
        self.journal = kwargs.get('journal', '')
        self.conference = kwargs.get('conference', '')
        self.abstract = kwargs.get('abstract', '')
        self.keywords = kwargs.get('keywords', [])
        self.citation_count = kwargs.get('citation_count', 0)
        self.related_projects = kwargs.get('related_projects', [])
        self.pdf_url = kwargs.get('pdf_url', '')
        self.status = kwargs.get('status', 'published')
        self.created_at = kwargs.get('created_at', datetime.utcnow())
        self.updated_at = kwargs.get('updated_at', datetime.utcnow())
        self.views = kwargs.get('views', 0)
        self.downloads = kwargs.get('downloads', 0)

    def to_dict(self) -> Dict[str, Any]:
        authors_list = []
        for author in self.authors:
            if isinstance(author, Author):
                authors_list.append(author.to_dict())
            else:
                authors_list.append(author)

        return {
            'title': self.title,
            'authors': authors_list,
            'year': self.year,
            'doi': self.doi,
            'journal': self.journal,
            'conference': self.conference,
            'abstract': self.abstract,
            'keywords': self.keywords,
            'citation_count': self.citation_count,
            'related_projects': self.related_projects,
            'pdf_url': self.pdf_url,
            'status': self.status,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'views': self.views,
            'downloads': self.downloads
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Publication':
        return cls(**data)

    def validate(self) -> List[str]:
        errors = []

        if not self.title or len(self.title.strip()) < 5:
            errors.append("Publication title must be at least 5 characters")

        if not self.authors or len(self.authors) == 0:
            errors.append("At least one author is required")

        if not self.year or self.year < 1900 or self.year > datetime.now().year + 1:
            errors.append("Valid publication year is required")

        if self.doi and not self.doi.startswith('10.'):
            errors.append("DOI should start with '10.'")

        if self.status not in ['published', 'submitted', 'accepted', 'rejected']:
            errors.append("Invalid publication status")

        return errors

    def add_author(self, researcher_id: str, name: str, order: Optional[int] = None) -> bool:
        if order is None:
            order = len(self.authors) + 1

        author = Author(
            researcher_id=researcher_id,
            name=name,
            order=order
        )

        self.authors.append(author)
        self.updated_at = datetime.utcnow()
        return True

    def get_citation(self, style: str = 'apa') -> str:
        if not self.authors:
            return self.title

        authors = []
        for author in self.authors[:3]:
            if isinstance(author, dict):
                authors.append(author.get('name', ''))
            else:
                authors.append(author.name)

        if len(self.authors) > 3:
            authors_str = f"{authors[0]} et al."
        else:
            authors_str = ', '.join(authors)

        if style == 'apa':
            return f"{authors_str} ({self.year}). {self.title}. {self.journal}."
        elif style == 'mla':
            return f"{authors_str}. \"{self.title}.\" {self.journal}, {self.year}."
        else:
            return f"{authors_str} - {self.title} ({self.year})"