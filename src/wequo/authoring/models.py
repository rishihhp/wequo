"""
Data models for the authoring version control system.
"""

from __future__ import annotations
import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
import json


class DocumentState(Enum):
    """Document workflow states."""
    DRAFT = "draft"
    REVIEW = "review" 
    APPROVED = "approved"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ApprovalStatus(Enum):
    """Approval status for documents."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CHANGES_REQUESTED = "changes_requested"


@dataclass
class ReviewComment:
    """Editorial comment for collaborative authoring."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    author: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    content: str = ""
    line_number: Optional[int] = None
    resolved: bool = False
    thread_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'author': self.author,
            'timestamp': self.timestamp.isoformat(),
            'content': self.content,
            'line_number': self.line_number,
            'resolved': self.resolved,
            'thread_id': self.thread_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ReviewComment:
        """Create from dictionary."""
        return cls(
            id=data['id'],
            author=data['author'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            content=data['content'],
            line_number=data.get('line_number'),
            resolved=data.get('resolved', False),
            thread_id=data.get('thread_id')
        )


@dataclass  
class Approval:
    """Approval record for document review."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    reviewer: str = ""
    status: ApprovalStatus = ApprovalStatus.PENDING
    timestamp: datetime = field(default_factory=datetime.now)
    comments: str = ""
    version_id: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'reviewer': self.reviewer,
            'status': self.status.value,
            'timestamp': self.timestamp.isoformat(),
            'comments': self.comments,
            'version_id': self.version_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Approval:
        """Create from dictionary."""
        return cls(
            id=data['id'],
            reviewer=data['reviewer'], 
            status=ApprovalStatus(data['status']),
            timestamp=datetime.fromisoformat(data['timestamp']),
            comments=data.get('comments', ''),
            version_id=data['version_id']
        )


@dataclass
class BriefVersion:
    """Version of a weekly brief document."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    version_number: str = ""
    author: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    state: DocumentState = DocumentState.DRAFT
    comments: List[ReviewComment] = field(default_factory=list)
    approvals: List[Approval] = field(default_factory=list)
    parent_version: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'version_number': self.version_number,
            'author': self.author,
            'timestamp': self.timestamp.isoformat(),
            'content': self.content,
            'metadata': self.metadata,
            'state': self.state.value,
            'comments': [c.to_dict() for c in self.comments],
            'approvals': [a.to_dict() for a in self.approvals],
            'parent_version': self.parent_version,
            'tags': self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BriefVersion:
        """Create from dictionary."""
        return cls(
            id=data['id'],
            version_number=data['version_number'],
            author=data['author'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            content=data['content'],
            metadata=data.get('metadata', {}),
            state=DocumentState(data['state']),
            comments=[ReviewComment.from_dict(c) for c in data.get('comments', [])],
            approvals=[Approval.from_dict(a) for a in data.get('approvals', [])],
            parent_version=data.get('parent_version'),
            tags=data.get('tags', [])
        )


@dataclass
class BriefDocument:
    """Weekly brief document with version control."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    package_date: str = ""
    current_version: str = ""
    versions: Dict[str, BriefVersion] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    author: str = ""
    reviewers: List[str] = field(default_factory=list)
    file_path: str = ""
    
    def get_current_version(self) -> Optional[BriefVersion]:
        """Get the current version of the document."""
        if self.current_version and self.current_version in self.versions:
            return self.versions[self.current_version]
        return None
    
    def get_version_history(self) -> List[BriefVersion]:
        """Get version history sorted by timestamp."""
        return sorted(self.versions.values(), key=lambda v: v.timestamp, reverse=True)
    
    def add_version(self, version: BriefVersion) -> None:
        """Add a new version."""
        self.versions[version.id] = version
        self.current_version = version.id
        self.updated_at = datetime.now()
    
    def get_approvals_status(self) -> Dict[str, Any]:
        """Get current approval status."""
        current = self.get_current_version()
        if not current:
            return {'required': len(self.reviewers), 'approved': 0, 'status': 'no_version'}
        
        approved_count = sum(1 for a in current.approvals if a.status == ApprovalStatus.APPROVED)
        has_rejections = any(a.status == ApprovalStatus.REJECTED for a in current.approvals)
        has_change_requests = any(a.status == ApprovalStatus.CHANGES_REQUESTED for a in current.approvals)
        
        if has_rejections:
            status = 'rejected'
        elif has_change_requests:
            status = 'changes_requested'
        elif approved_count >= len(self.reviewers):
            status = 'fully_approved'
        elif approved_count > 0:
            status = 'partially_approved'
        else:
            status = 'pending'
        
        return {
            'required': len(self.reviewers),
            'approved': approved_count,
            'status': status,
            'remaining': max(0, len(self.reviewers) - approved_count)
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'package_date': self.package_date,
            'current_version': self.current_version,
            'versions': {k: v.to_dict() for k, v in self.versions.items()},
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'author': self.author,
            'reviewers': self.reviewers,
            'file_path': self.file_path
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BriefDocument:
        """Create from dictionary."""
        return cls(
            id=data['id'],
            title=data['title'],
            package_date=data['package_date'],
            current_version=data['current_version'],
            versions={k: BriefVersion.from_dict(v) for k, v in data.get('versions', {}).items()},
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            author=data['author'],
            reviewers=data.get('reviewers', []),
            file_path=data.get('file_path', '')
        )
    
    def save_to_file(self, file_path: Path) -> None:
        """Save document to JSON file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load_from_file(cls, file_path: Path) -> BriefDocument:
        """Load document from JSON file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)
