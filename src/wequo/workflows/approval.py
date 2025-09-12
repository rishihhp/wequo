"""
Approval workflow system for WeQuo briefs.

Manages the review and approval process for weekly briefs with
multi-stage approval, reviewer assignments, and approval tracking.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum


class ApprovalStatus(Enum):
    """Status of an approval request."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class ApprovalLevel(Enum):
    """Level of approval required."""
    EDITOR = "editor"
    SENIOR_EDITOR = "senior_editor"
    MANAGING_EDITOR = "managing_editor"
    EXECUTIVE = "executive"


@dataclass
class Reviewer:
    """Information about a reviewer."""
    name: str
    email: str
    level: ApprovalLevel
    active: bool = True


@dataclass
class ApprovalRequest:
    """An approval request."""
    request_id: str
    version_id: str
    author: str
    title: str
    description: str
    required_level: ApprovalLevel
    assigned_reviewers: List[str]
    created_at: str
    deadline: str
    status: ApprovalStatus = ApprovalStatus.PENDING
    comments: List[Dict[str, str]] = None
    approved_by: List[str] = None
    rejected_by: Optional[str] = None
    rejection_reason: Optional[str] = None


class ApprovalWorkflow:
    """
    Manages approval workflows for WeQuo briefs.
    
    Features:
    - Multi-level approval (Editor, Senior Editor, Managing Editor, Executive)
    - Reviewer assignment and management
    - Approval tracking and notifications
    - Deadline management
    - Comment system
    - Approval history
    """
    
    def __init__(self, base_path: Path):
        self.base_path = Path(base_path)
        self.workflows_path = self.base_path / ".workflows"
        self.workflows_path.mkdir(exist_ok=True)
        
        # Initialize data files
        self.reviewers_file = self.workflows_path / "reviewers.json"
        self.requests_file = self.workflows_path / "approval_requests.json"
        
        # Load data
        self.reviewers = self._load_reviewers()
        self.requests = self._load_requests()
    
    def _load_reviewers(self) -> Dict[str, Reviewer]:
        """Load reviewers from disk."""
        if not self.reviewers_file.exists():
            # Create default reviewers
            default_reviewers = {
                "editor1": Reviewer("Editor One", "editor1@wequo.com", ApprovalLevel.EDITOR),
                "senior1": Reviewer("Senior Editor", "senior1@wequo.com", ApprovalLevel.SENIOR_EDITOR),
                "managing1": Reviewer("Managing Editor", "managing1@wequo.com", ApprovalLevel.MANAGING_EDITOR),
                "exec1": Reviewer("Executive Editor", "exec1@wequo.com", ApprovalLevel.EXECUTIVE)
            }
            self._save_reviewers(default_reviewers)
            return default_reviewers
        
        try:
            with open(self.reviewers_file, 'r') as f:
                data = json.load(f)
            
            reviewers = {}
            for reviewer_id, reviewer_data in data.items():
                reviewers[reviewer_id] = Reviewer(
                    name=reviewer_data['name'],
                    email=reviewer_data['email'],
                    level=ApprovalLevel(reviewer_data['level']),
                    active=reviewer_data.get('active', True)
                )
            
            return reviewers
        except Exception as e:
            print(f"Error loading reviewers: {e}")
            return {}
    
    def _save_reviewers(self, reviewers: Optional[Dict[str, Reviewer]] = None):
        """Save reviewers to disk."""
        if reviewers is None:
            reviewers = self.reviewers
        
        try:
            data = {}
            for reviewer_id, reviewer in reviewers.items():
                data[reviewer_id] = {
                    'name': reviewer.name,
                    'email': reviewer.email,
                    'level': reviewer.level.value,
                    'active': reviewer.active
                }
            
            with open(self.reviewers_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving reviewers: {e}")
    
    def _load_requests(self) -> Dict[str, ApprovalRequest]:
        """Load approval requests from disk."""
        if not self.requests_file.exists():
            return {}
        
        try:
            with open(self.requests_file, 'r') as f:
                data = json.load(f)
            
            requests = {}
            for request_id, request_data in data.items():
                requests[request_id] = ApprovalRequest(
                    request_id=request_data['request_id'],
                    version_id=request_data['version_id'],
                    author=request_data['author'],
                    title=request_data['title'],
                    description=request_data['description'],
                    required_level=ApprovalLevel(request_data['required_level']),
                    assigned_reviewers=request_data['assigned_reviewers'],
                    created_at=request_data['created_at'],
                    deadline=request_data['deadline'],
                    status=ApprovalStatus(request_data['status']),
                    comments=request_data.get('comments', []),
                    approved_by=request_data.get('approved_by', []),
                    rejected_by=request_data.get('rejected_by'),
                    rejection_reason=request_data.get('rejection_reason')
                )
            
            return requests
        except Exception as e:
            print(f"Error loading requests: {e}")
            return {}
    
    def _save_requests(self):
        """Save approval requests to disk."""
        try:
            data = {}
            for request_id, request in self.requests.items():
                data[request_id] = asdict(request)
                # Convert enum values to strings
                data[request_id]['required_level'] = request.required_level.value
                data[request_id]['status'] = request.status.value
            
            with open(self.requests_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving requests: {e}")
    
    def add_reviewer(self, reviewer_id: str, name: str, email: str, level: ApprovalLevel) -> bool:
        """Add a new reviewer."""
        if reviewer_id in self.reviewers:
            return False
        
        self.reviewers[reviewer_id] = Reviewer(name, email, level)
        self._save_reviewers()
        return True
    
    def remove_reviewer(self, reviewer_id: str) -> bool:
        """Remove a reviewer."""
        if reviewer_id not in self.reviewers:
            return False
        
        # Deactivate instead of removing to preserve history
        self.reviewers[reviewer_id].active = False
        self._save_reviewers()
        return True
    
    def get_reviewers_by_level(self, level: ApprovalLevel) -> List[Reviewer]:
        """Get active reviewers by approval level."""
        return [
            reviewer for reviewer in self.reviewers.values()
            if reviewer.level == level and reviewer.active
        ]
    
    def create_approval_request(
        self,
        version_id: str,
        author: str,
        title: str,
        description: str,
        required_level: ApprovalLevel,
        deadline_days: int = 7
    ) -> str:
        """
        Create a new approval request.
        
        Args:
            version_id: Version to approve
            author: Author of the content
            title: Title of the content
            description: Description of changes
            required_level: Required approval level
            deadline_days: Days until deadline
            
        Returns:
            Request ID
        """
        # Generate request ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        request_id = f"req_{timestamp}_{author.replace(' ', '_')}"
        
        # Calculate deadline
        deadline = datetime.now() + timedelta(days=deadline_days)
        
        # Assign reviewers based on required level
        assigned_reviewers = self._assign_reviewers(required_level)
        
        # Create approval request
        request = ApprovalRequest(
            request_id=request_id,
            version_id=version_id,
            author=author,
            title=title,
            description=description,
            required_level=required_level,
            assigned_reviewers=assigned_reviewers,
            created_at=datetime.now().isoformat(),
            deadline=deadline.isoformat(),
            comments=[],
            approved_by=[]
        )
        
        self.requests[request_id] = request
        self._save_requests()
        
        return request_id
    
    def _assign_reviewers(self, required_level: ApprovalLevel) -> List[str]:
        """Assign reviewers based on required level."""
        assigned = []
        
        # Get reviewers at or above the required level
        for reviewer_id, reviewer in self.reviewers.items():
            if reviewer.active and self._is_level_sufficient(reviewer.level, required_level):
                assigned.append(reviewer_id)
        
        # Limit to reasonable number of reviewers
        return assigned[:3]
    
    def _is_level_sufficient(self, reviewer_level: ApprovalLevel, required_level: ApprovalLevel) -> bool:
        """Check if reviewer level is sufficient for required level."""
        level_hierarchy = {
            ApprovalLevel.EDITOR: 1,
            ApprovalLevel.SENIOR_EDITOR: 2,
            ApprovalLevel.MANAGING_EDITOR: 3,
            ApprovalLevel.EXECUTIVE: 4
        }
        
        return level_hierarchy[reviewer_level] >= level_hierarchy[required_level]
    
    def approve_request(self, request_id: str, reviewer_id: str, comment: str = "") -> bool:
        """Approve a request."""
        if request_id not in self.requests:
            return False
        
        request = self.requests[request_id]
        
        # Check if reviewer is assigned
        if reviewer_id not in request.assigned_reviewers:
            return False
        
        # Check if already approved by this reviewer
        if reviewer_id in request.approved_by:
            return False
        
        # Check if already rejected
        if request.status == ApprovalStatus.REJECTED:
            return False
        
        # Add approval
        request.approved_by.append(reviewer_id)
        
        # Add comment if provided
        if comment:
            request.comments.append({
                "reviewer": reviewer_id,
                "comment": comment,
                "timestamp": datetime.now().isoformat(),
                "type": "approval"
            })
        
        # Check if enough approvals received
        required_approvals = self._get_required_approval_count(request.required_level)
        if len(request.approved_by) >= required_approvals:
            request.status = ApprovalStatus.APPROVED
        
        self._save_requests()
        return True
    
    def reject_request(self, request_id: str, reviewer_id: str, reason: str) -> bool:
        """Reject a request."""
        if request_id not in self.requests:
            return False
        
        request = self.requests[request_id]
        
        # Check if reviewer is assigned
        if reviewer_id not in request.assigned_reviewers:
            return False
        
        # Check if already approved or rejected
        if request.status in [ApprovalStatus.APPROVED, ApprovalStatus.REJECTED]:
            return False
        
        # Reject the request
        request.status = ApprovalStatus.REJECTED
        request.rejected_by = reviewer_id
        request.rejection_reason = reason
        
        # Add comment
        request.comments.append({
            "reviewer": reviewer_id,
            "comment": reason,
            "timestamp": datetime.now().isoformat(),
            "type": "rejection"
        })
        
        self._save_requests()
        return True
    
    def add_comment(self, request_id: str, reviewer_id: str, comment: str) -> bool:
        """Add a comment to a request."""
        if request_id not in self.requests:
            return False
        
        request = self.requests[request_id]
        
        # Check if reviewer is assigned
        if reviewer_id not in request.assigned_reviewers:
            return False
        
        # Add comment
        request.comments.append({
            "reviewer": reviewer_id,
            "comment": comment,
            "timestamp": datetime.now().isoformat(),
            "type": "comment"
        })
        
        self._save_requests()
        return True
    
    def _get_required_approval_count(self, level: ApprovalLevel) -> int:
        """Get required number of approvals for a level."""
        approval_requirements = {
            ApprovalLevel.EDITOR: 1,
            ApprovalLevel.SENIOR_EDITOR: 1,
            ApprovalLevel.MANAGING_EDITOR: 2,
            ApprovalLevel.EXECUTIVE: 2
        }
        
        return approval_requirements.get(level, 1)
    
    def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """Get an approval request by ID."""
        return self.requests.get(request_id)
    
    def get_requests_by_author(self, author: str) -> List[ApprovalRequest]:
        """Get all requests by an author."""
        return [
            request for request in self.requests.values()
            if request.author == author
        ]
    
    def get_requests_by_reviewer(self, reviewer_id: str) -> List[ApprovalRequest]:
        """Get all requests assigned to a reviewer."""
        return [
            request for request in self.requests.values()
            if reviewer_id in request.assigned_reviewers
        ]
    
    def get_pending_requests(self) -> List[ApprovalRequest]:
        """Get all pending requests."""
        return [
            request for request in self.requests.values()
            if request.status == ApprovalStatus.PENDING
        ]
    
    def check_expired_requests(self) -> List[str]:
        """Check for expired requests and mark them as expired."""
        expired_requests = []
        current_time = datetime.now()
        
        for request_id, request in self.requests.items():
            if request.status == ApprovalStatus.PENDING:
                deadline = datetime.fromisoformat(request.deadline)
                if current_time > deadline:
                    request.status = ApprovalStatus.EXPIRED
                    expired_requests.append(request_id)
        
        if expired_requests:
            self._save_requests()
        
        return expired_requests
    
    def get_approval_summary(self) -> Dict[str, Any]:
        """Get summary of approval workflow status."""
        total_requests = len(self.requests)
        pending_requests = len([r for r in self.requests.values() if r.status == ApprovalStatus.PENDING])
        approved_requests = len([r for r in self.requests.values() if r.status == ApprovalStatus.APPROVED])
        rejected_requests = len([r for r in self.requests.values() if r.status == ApprovalStatus.REJECTED])
        expired_requests = len([r for r in self.requests.values() if r.status == ApprovalStatus.EXPIRED])
        
        # Average approval time
        approved_times = []
        for request in self.requests.values():
            if request.status == ApprovalStatus.APPROVED and request.approved_by:
                # Calculate time from creation to last approval
                created_time = datetime.fromisoformat(request.created_at)
                # Use current time as proxy for approval time (in real implementation, track actual approval times)
                approval_time = datetime.now()
                approval_duration = (approval_time - created_time).total_seconds() / 3600  # hours
                approved_times.append(approval_duration)
        
        avg_approval_time = sum(approved_times) / len(approved_times) if approved_times else 0
        
        return {
            "total_requests": total_requests,
            "pending_requests": pending_requests,
            "approved_requests": approved_requests,
            "rejected_requests": rejected_requests,
            "expired_requests": expired_requests,
            "approval_rate": approved_requests / total_requests if total_requests > 0 else 0,
            "average_approval_time_hours": avg_approval_time,
            "active_reviewers": len([r for r in self.reviewers.values() if r.active])
        }
    
    def get_request_timeline(self, request_id: str) -> List[Dict[str, Any]]:
        """Get timeline of events for a request."""
        request = self.get_request(request_id)
        if not request:
            return []
        
        timeline = []
        
        # Creation event
        timeline.append({
            "timestamp": request.created_at,
            "event": "created",
            "actor": request.author,
            "description": f"Approval request created: {request.title}"
        })
        
        # Comments and approvals
        for comment in request.comments:
            timeline.append({
                "timestamp": comment["timestamp"],
                "event": comment["type"],
                "actor": comment["reviewer"],
                "description": comment["comment"]
            })
        
        # Final status
        if request.status == ApprovalStatus.APPROVED:
            timeline.append({
                "timestamp": datetime.now().isoformat(),
                "event": "approved",
                "actor": "system",
                "description": f"Request approved by {len(request.approved_by)} reviewer(s)"
            })
        elif request.status == ApprovalStatus.REJECTED:
            timeline.append({
                "timestamp": datetime.now().isoformat(),
                "event": "rejected",
                "actor": request.rejected_by,
                "description": f"Request rejected: {request.rejection_reason}"
            })
        
        # Sort by timestamp
        timeline.sort(key=lambda x: x["timestamp"])
        
        return timeline
