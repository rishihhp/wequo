"""
Workflow manager for WeQuo author review workflows.

Integrates version control, approval workflows, and editorial notes
into a unified system for managing content creation and review.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from .version_control import VersionManager, VersionStatus
from .approval import ApprovalWorkflow, ApprovalLevel, ApprovalStatus
from .editorial import EditorialNotes, NoteType, NoteStatus


class WorkflowManager:
    """
    Unified workflow manager for WeQuo content creation and review.
    
    Features:
    - Version control integration
    - Approval workflow management
    - Editorial notes and feedback
    - Workflow automation
    - Status tracking and reporting
    """
    
    def __init__(self, base_path: Path):
        self.base_path = Path(base_path)
        
        # Initialize workflow components
        self.version_manager = VersionManager(base_path)
        self.approval_workflow = ApprovalWorkflow(base_path)
        self.editorial_notes = EditorialNotes(base_path)
    
    def create_content_workflow(
        self,
        date: str,
        author: str,
        message: str,
        source_files: List[Path],
        required_approval_level: ApprovalLevel = ApprovalLevel.EDITOR,
        deadline_days: int = 7
    ) -> Dict[str, str]:
        """
        Create a complete content workflow.
        
        Args:
            date: Date of the content (YYYY-MM-DD)
            author: Author name
            message: Initial commit message
            source_files: Files to version
            required_approval_level: Required approval level
            deadline_days: Days until approval deadline
            
        Returns:
            Dictionary with workflow IDs
        """
        # 1. Create initial version
        version_id = self.version_manager.create_version(
            date=date,
            author=author,
            message=message,
            source_files=source_files,
            status=VersionStatus.DRAFT
        )
        
        # 2. Create approval request
        approval_request_id = self.approval_workflow.create_approval_request(
            version_id=version_id,
            author=author,
            title=f"Weekly Brief {date}",
            description=message,
            required_level=required_approval_level,
            deadline_days=deadline_days
        )
        
        return {
            "version_id": version_id,
            "approval_request_id": approval_request_id,
            "workflow_status": "created"
        }
    
    def submit_for_review(
        self,
        version_id: str,
        author: str,
        message: str,
        required_approval_level: ApprovalLevel = ApprovalLevel.EDITOR
    ) -> str:
        """
        Submit a version for review.
        
        Args:
            version_id: Version to submit
            author: Author submitting
            message: Submission message
            required_approval_level: Required approval level
            
        Returns:
            Approval request ID
        """
        # Update version status
        self.version_manager.update_version_status(version_id, VersionStatus.REVIEW)
        
        # Create approval request
        approval_request_id = self.approval_workflow.create_approval_request(
            version_id=version_id,
            author=author,
            title=f"Review Request for {version_id}",
            description=message,
            required_level=required_approval_level
        )
        
        return approval_request_id
    
    def approve_content(self, approval_request_id: str, reviewer_id: str, comment: str = "") -> bool:
        """Approve content through the workflow."""
        success = self.approval_workflow.approve_request(approval_request_id, reviewer_id, comment)
        
        if success:
            # Check if fully approved
            request = self.approval_workflow.get_request(approval_request_id)
            if request and request.status == ApprovalStatus.APPROVED:
                # Update version status
                self.version_manager.update_version_status(
                    request.version_id, 
                    VersionStatus.APPROVED
                )
        
        return success
    
    def reject_content(self, approval_request_id: str, reviewer_id: str, reason: str) -> bool:
        """Reject content through the workflow."""
        success = self.approval_workflow.reject_request(approval_request_id, reviewer_id, reason)
        
        if success:
            # Update version status
            request = self.approval_workflow.get_request(approval_request_id)
            if request:
                self.version_manager.update_version_status(
                    request.version_id, 
                    VersionStatus.DRAFT
                )
        
        return success
    
    def publish_content(self, version_id: str, publisher: str) -> bool:
        """Publish approved content."""
        version_info = self.version_manager.get_version_by_id(version_id)
        if not version_info or version_info.status != VersionStatus.APPROVED:
            return False
        
        # Update version status
        success = self.version_manager.update_version_status(version_id, VersionStatus.PUBLISHED)
        
        if success:
            # Add editorial note about publication
            self.editorial_notes.create_note(
                version_id=version_id,
                author=publisher,
                note_type=NoteType.COMMENT,
                title="Content Published",
                content=f"Content published by {publisher}",
                priority=1
            )
        
        return success
    
    def add_editorial_feedback(
        self,
        version_id: str,
        reviewer: str,
        note_type: NoteType,
        title: str,
        content: str,
        target_section: Optional[str] = None,
        target_line: Optional[int] = None,
        priority: int = 1
    ) -> str:
        """Add editorial feedback to a version."""
        return self.editorial_notes.create_note(
            version_id=version_id,
            author=reviewer,
            note_type=note_type,
            title=title,
            content=content,
            target_section=target_section,
            target_line=target_line,
            priority=priority
        )
    
    def resolve_feedback(self, note_id: str, resolver: str, resolution: str = "") -> bool:
        """Resolve editorial feedback."""
        return self.editorial_notes.resolve_note(note_id, resolver, resolution)
    
    def create_revision(
        self,
        base_version_id: str,
        author: str,
        message: str,
        source_files: List[Path]
    ) -> str:
        """Create a revision based on feedback."""
        # Create new version with parent
        version_info = self.version_manager.get_version_by_id(base_version_id)
        if not version_info:
            raise ValueError(f"Base version {base_version_id} not found")
        
        new_version_id = self.version_manager.create_version(
            date=version_info.date,
            author=author,
            message=message,
            source_files=source_files,
            status=VersionStatus.DRAFT,
            parent_version=base_version_id
        )
        
        return new_version_id
    
    def get_workflow_status(self, version_id: str) -> Dict[str, Any]:
        """Get comprehensive workflow status for a version."""
        version_info = self.version_manager.get_version_by_id(version_id)
        if not version_info:
            return {"error": "Version not found"}
        
        # Get approval requests for this version
        approval_requests = [
            request for request in self.approval_workflow.requests.values()
            if request.version_id == version_id
        ]
        
        # Get editorial notes for this version
        editorial_notes = self.editorial_notes.get_notes_by_version(version_id)
        
        # Get latest approval request
        latest_request = None
        if approval_requests:
            latest_request = max(approval_requests, key=lambda r: r.created_at)
        
        return {
            "version": {
                "id": version_info.version_id,
                "date": version_info.date,
                "author": version_info.author,
                "status": version_info.status.value,
                "message": version_info.message,
                "created_at": version_info.created_at
            },
            "approval": {
                "has_request": latest_request is not None,
                "status": latest_request.status.value if latest_request else None,
                "assigned_reviewers": latest_request.assigned_reviewers if latest_request else [],
                "approved_by": latest_request.approved_by if latest_request else [],
                "deadline": latest_request.deadline if latest_request else None
            },
            "editorial": {
                "total_notes": len(editorial_notes),
                "open_notes": len([n for n in editorial_notes if n.status == NoteStatus.OPEN]),
                "resolved_notes": len([n for n in editorial_notes if n.status == NoteStatus.RESOLVED]),
                "critical_notes": len([n for n in editorial_notes if n.priority >= 4])
            },
            "workflow_status": self._determine_workflow_status(version_info, latest_request, editorial_notes)
        }
    
    def _determine_workflow_status(
        self, 
        version_info, 
        latest_request, 
        editorial_notes
    ) -> str:
        """Determine overall workflow status."""
        if version_info.status == VersionStatus.PUBLISHED:
            return "published"
        elif version_info.status == VersionStatus.APPROVED:
            return "approved_ready_for_publication"
        elif latest_request and latest_request.status == ApprovalStatus.APPROVED:
            return "approved"
        elif latest_request and latest_request.status == ApprovalStatus.REJECTED:
            return "rejected_needs_revision"
        elif latest_request and latest_request.status == ApprovalStatus.PENDING:
            return "under_review"
        elif version_info.status == VersionStatus.REVIEW:
            return "submitted_for_review"
        elif version_info.status == VersionStatus.DRAFT:
            if editorial_notes and any(n.status == NoteStatus.OPEN for n in editorial_notes):
                return "draft_with_feedback"
            else:
                return "draft"
        else:
            return "unknown"
    
    def get_author_dashboard(self, author: str) -> Dict[str, Any]:
        """Get dashboard data for an author."""
        # Get versions by author
        author_versions = []
        for date_versions in self.version_manager.versions.values():
            for version in date_versions:
                if version.author == author:
                    author_versions.append(version)
        
        # Get approval requests by author
        author_requests = self.approval_workflow.get_requests_by_author(author)
        
        # Get editorial notes by author
        author_notes = self.editorial_notes.get_notes_by_author(author)
        
        # Get activity summary
        activity_summary = self.editorial_notes.get_author_activity(author)
        
        return {
            "author": author,
            "versions": {
                "total": len(author_versions),
                "draft": len([v for v in author_versions if v.status == VersionStatus.DRAFT]),
                "review": len([v for v in author_versions if v.status == VersionStatus.REVIEW]),
                "approved": len([v for v in author_versions if v.status == VersionStatus.APPROVED]),
                "published": len([v for v in author_versions if v.status == VersionStatus.PUBLISHED])
            },
            "approvals": {
                "total_requests": len(author_requests),
                "pending": len([r for r in author_requests if r.status == ApprovalStatus.PENDING]),
                "approved": len([r for r in author_requests if r.status == ApprovalStatus.APPROVED]),
                "rejected": len([r for r in author_requests if r.status == ApprovalStatus.REJECTED])
            },
            "editorial": activity_summary,
            "recent_activity": self._get_recent_activity(author_versions, author_requests, author_notes)
        }
    
    def _get_recent_activity(self, versions, requests, notes) -> List[Dict[str, Any]]:
        """Get recent activity for an author."""
        activity = []
        
        # Add version activities
        for version in versions:
            activity.append({
                "type": "version_created",
                "timestamp": version.created_at,
                "description": f"Created version {version.version_id}",
                "status": version.status.value
            })
        
        # Add request activities
        for request in requests:
            activity.append({
                "type": "approval_request",
                "timestamp": request.created_at,
                "description": f"Submitted for approval: {request.title}",
                "status": request.status.value
            })
        
        # Add note activities
        for note in notes:
            activity.append({
                "type": "editorial_note",
                "timestamp": note.created_at,
                "description": f"Added note: {note.title}",
                "status": note.status.value
            })
        
        # Sort by timestamp and return recent 10
        activity.sort(key=lambda x: x["timestamp"], reverse=True)
        return activity[:10]
    
    def get_reviewer_dashboard(self, reviewer_id: str) -> Dict[str, Any]:
        """Get dashboard data for a reviewer."""
        # Get requests assigned to reviewer
        reviewer_requests = self.approval_workflow.get_requests_by_reviewer(reviewer_id)
        
        # Get pending requests
        pending_requests = [r for r in reviewer_requests if r.status == ApprovalStatus.PENDING]
        
        # Get approval summary
        approval_summary = self.approval_workflow.get_approval_summary()
        
        return {
            "reviewer_id": reviewer_id,
            "assigned_requests": {
                "total": len(reviewer_requests),
                "pending": len(pending_requests),
                "approved": len([r for r in reviewer_requests if r.status == ApprovalStatus.APPROVED]),
                "rejected": len([r for r in reviewer_requests if r.status == ApprovalStatus.REJECTED])
            },
            "pending_requests": [
                {
                    "request_id": r.request_id,
                    "version_id": r.version_id,
                    "author": r.author,
                    "title": r.title,
                    "deadline": r.deadline,
                    "required_level": r.required_level.value
                }
                for r in pending_requests
            ],
            "system_summary": approval_summary
        }
    
    def export_workflow_report(self, version_id: str) -> Dict[str, Any]:
        """Export comprehensive workflow report for a version."""
        version_info = self.version_manager.get_version_by_id(version_id)
        if not version_info:
            return {"error": "Version not found"}
        
        # Get approval requests
        approval_requests = [
            request for request in self.approval_workflow.requests.values()
            if request.version_id == version_id
        ]
        
        # Get editorial notes
        editorial_notes = self.editorial_notes.get_notes_by_version(version_id)
        
        # Get version history
        version_history = self.version_manager.get_version_history(version_info.date)
        
        return {
            "version_info": {
                "id": version_info.version_id,
                "date": version_info.date,
                "author": version_info.author,
                "status": version_info.status.value,
                "message": version_info.message,
                "created_at": version_info.created_at,
                "file_size": version_info.file_size
            },
            "version_history": version_history,
            "approval_requests": [
                {
                    "request_id": r.request_id,
                    "status": r.status.value,
                    "assigned_reviewers": r.assigned_reviewers,
                    "approved_by": r.approved_by,
                    "created_at": r.created_at,
                    "deadline": r.deadline,
                    "comments": r.comments
                }
                for r in approval_requests
            ],
            "editorial_notes": [
                {
                    "note_id": n.note_id,
                    "author": n.author,
                    "type": n.note_type.value,
                    "status": n.status.value,
                    "title": n.title,
                    "content": n.content,
                    "priority": n.priority,
                    "created_at": n.created_at,
                    "replies": n.replies
                }
                for n in editorial_notes
            ],
            "workflow_summary": self.get_workflow_status(version_id)
        }
