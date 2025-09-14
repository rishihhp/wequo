"""
Search data models and structures.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from enum import Enum


class DocumentType(Enum):
    """Types of documents that can be indexed."""
    PACKAGE = "package"
    DATA_POINT = "data_point"
    ANALYTICS = "analytics"
    REPORT = "report"
    ANOMALY = "anomaly"
    TREND = "trend"


@dataclass
class IndexDocument:
    """Represents a document in the search index."""
    id: str
    type: DocumentType
    title: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    source: Optional[str] = None
    date_range: Optional[tuple] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'id': self.id,
            'type': self.type.value,
            'title': self.title,
            'content': self.content,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat(),
            'tags': self.tags,
            'source': self.source,
            'date_range': self.date_range
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IndexDocument':
        """Create from dictionary."""
        return cls(
            id=data['id'],
            type=DocumentType(data['type']),
            title=data['title'],
            content=data['content'],
            metadata=data.get('metadata', {}),
            timestamp=datetime.fromisoformat(data['timestamp']),
            tags=data.get('tags', []),
            source=data.get('source'),
            date_range=data.get('date_range')
        )


@dataclass
class SearchResult:
    """Represents a search result."""
    document: IndexDocument
    score: float
    highlights: List[str] = field(default_factory=list)
    explanation: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            'id': self.document.id,
            'type': self.document.type.value,
            'title': self.document.title,
            'content': self.document.content[:500] + "..." if len(self.document.content) > 500 else self.document.content,
            'metadata': self.document.metadata,
            'timestamp': self.document.timestamp.isoformat(),
            'tags': self.document.tags,
            'source': self.document.source,
            'score': self.score,
            'highlights': self.highlights,
            'explanation': self.explanation
        }


@dataclass
class SearchQuery:
    """Represents a search query with filters and options."""
    query: str
    filters: Dict[str, Any] = field(default_factory=dict)
    document_types: List[DocumentType] = field(default_factory=list)
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    sources: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    limit: int = 50
    offset: int = 0
    sort_by: str = 'relevance'  # relevance, date, score
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'query': self.query,
            'filters': self.filters,
            'document_types': [dt.value for dt in self.document_types],
            'date_from': self.date_from.isoformat() if self.date_from else None,
            'date_to': self.date_to.isoformat() if self.date_to else None,
            'sources': self.sources,
            'tags': self.tags,
            'limit': self.limit,
            'offset': self.offset,
            'sort_by': self.sort_by
        }


@dataclass
class SearchStats:
    """Search index statistics."""
    total_documents: int = 0
    documents_by_type: Dict[str, int] = field(default_factory=dict)
    total_sources: int = 0
    date_range: Optional[tuple] = None
    last_updated: Optional[datetime] = None
    index_size_mb: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'total_documents': self.total_documents,
            'documents_by_type': self.documents_by_type,
            'total_sources': self.total_sources,
            'date_range': self.date_range,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'index_size_mb': self.index_size_mb
        }
