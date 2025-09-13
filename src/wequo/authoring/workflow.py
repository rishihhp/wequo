"""
Authoring workflow management for WeQuo briefs.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from .models import BriefDocument, BriefVersion, DocumentState, ApprovalStatus
from .version_control import VersionController


class NotificationService:
    """Service for sending notifications about document workflow events."""
    
    def __init__(self, smtp_host: str = "", smtp_port: int = 587, 
                 smtp_user: str = "", smtp_password: str = ""):
        """Initialize notification service."""
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.enabled = bool(smtp_host and smtp_user)
    
    def send_notification(self, 
                         recipients: List[str],
                         subject: str,
                         message: str,
                         html_message: Optional[str] = None) -> bool:
        """Send email notification."""
        if not self.enabled or not recipients:
            return False
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.smtp_user
            msg['To'] = ', '.join(recipients)
            
            # Text part
            text_part = MIMEText(message, 'plain')
            msg.attach(text_part)
            
            # HTML part if provided
            if html_message:
                html_part = MIMEText(html_message, 'html')
                msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            print(f"Failed to send notification: {e}")
            return False
    
    def notify_review_requested(self, 
                               document: BriefDocument,
                               version: BriefVersion,
                               reviewers: List[str]) -> bool:
        """Notify reviewers that a document is ready for review."""
        subject = f"Review Requested: {document.title} v{version.version_number}"
        
        message = f"""
A new document version is ready for your review:

Document: {document.title}
Version: {version.version_number}
Author: {version.author}
Package Date: {document.package_date}

Please review and approve/reject the document in the WeQuo authoring system.

--
WeQuo Authoring System
"""
        
        html_message = f"""
<h2>Review Requested</h2>
<p>A new document version is ready for your review:</p>

<ul>
<li><strong>Document:</strong> {document.title}</li>
<li><strong>Version:</strong> {version.version_number}</li>
<li><strong>Author:</strong> {version.author}</li>
<li><strong>Package Date:</strong> {document.package_date}</li>
</ul>

<p>Please review and approve/reject the document in the WeQuo authoring system.</p>

<hr>
<p><em>WeQuo Authoring System</em></p>
"""
        
        return self.send_notification(reviewers, subject, message, html_message)
    
    def notify_approval_status(self,
                              document: BriefDocument,
                              version: BriefVersion,
                              reviewer: str,
                              status: ApprovalStatus,
                              author_email: str) -> bool:
        """Notify author about approval status change."""
        status_text = {
            ApprovalStatus.APPROVED: "approved",
            ApprovalStatus.REJECTED: "rejected", 
            ApprovalStatus.CHANGES_REQUESTED: "requested changes for"
        }.get(status, "reviewed")
        
        subject = f"Document {status_text.title()}: {document.title} v{version.version_number}"
        
        message = f"""
Your document has been {status_text} by {reviewer}:

Document: {document.title}
Version: {version.version_number}
Reviewer: {reviewer}
Status: {status.value.replace('_', ' ').title()}

Check the WeQuo authoring system for detailed feedback and next steps.

--
WeQuo Authoring System
"""
        
        html_message = f"""
<h2>Document {status_text.title()}</h2>
<p>Your document has been <strong>{status_text}</strong> by {reviewer}:</p>

<ul>
<li><strong>Document:</strong> {document.title}</li>
<li><strong>Version:</strong> {version.version_number}</li>
<li><strong>Reviewer:</strong> {reviewer}</li>
<li><strong>Status:</strong> {status.value.replace('_', ' ').title()}</li>
</ul>

<p>Check the WeQuo authoring system for detailed feedback and next steps.</p>

<hr>
<p><em>WeQuo Authoring System</em></p>
"""
        
        return self.send_notification([author_email], subject, message, html_message)


class AuthoringWorkflow:
    """Manages the complete authoring workflow for weekly briefs."""
    
    def __init__(self, 
                 version_controller: VersionController,
                 notification_service: Optional[NotificationService] = None):
        """Initialize workflow manager."""
        self.vc = version_controller
        self.notifications = notification_service or NotificationService()
        
        # Default workflow settings
        self.settings = {
            'auto_submit_for_review': False,
            'required_approvals': 1,
            'approval_timeout_days': 3,
            'auto_publish_when_approved': False,
            'notify_reviewers': True,
            'notify_authors': True
        }
    
    def create_weekly_brief(self,
                           package_date: str,
                           author: str,
                           reviewers: List[str],
                           template_content: str = "",
                           auto_submit: bool = False) -> BriefDocument:
        """Create a new weekly brief with proper workflow setup."""
        
        title = f"Weekly Brief - {package_date}"
        
        # Load template if no content provided
        if not template_content:
            template_content = self._load_template_content(package_date)
        
        # Create document
        document = self.vc.create_document(
            title=title,
            package_date=package_date,
            author=author,
            initial_content=template_content,
            reviewers=reviewers
        )
        
        # Auto-submit if requested
        if auto_submit:
            current_version = document.get_current_version()
            if current_version:
                self.submit_for_review(document.id, current_version.id, author)
        
        return document
    
    def _load_template_content(self, package_date: str) -> str:
        """Load template content for the brief."""
        template_path = Path("docs/template.md")
        
        if template_path.exists():
            content = template_path.read_text(encoding='utf-8')
            
            # Replace placeholders
            from datetime import datetime
            date_obj = datetime.strptime(package_date, '%Y-%m-%d')
            week_num = date_obj.isocalendar()[1]
            
            content = content.replace("YYYY-W##", f"2025-W{week_num:02d}")
            content = content.replace("_(YYYY-MM-DD)_", package_date)
            
            return content
        
        return f"""# Weekly Global Risk & Opportunity Brief

**Week XX, 2025 | {package_date}**

## Executive Summary

[To be completed based on data analysis]

## Key Market Insights

[Key insights from analytics]

## Significant Changes

[Major market movements]

## Risk Assessment

[Current risk level and factors]

---

*Generated by WeQuo Authoring System*
"""
    
    def update_brief(self,
                    document_id: str,
                    content: str,
                    author: str,
                    commit_message: Optional[str] = None,
                    auto_submit: bool = False) -> BriefVersion:
        """Update a brief document."""
        
        document = self.vc.get_document(document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        # Update document
        new_version = self.vc.update_document(
            document=document,
            content=content,
            author=author,
            commit_message=commit_message
        )
        
        # Auto-submit if requested
        if auto_submit:
            self.submit_for_review(document_id, new_version.id, author)
        
        return new_version
    
    def submit_for_review(self,
                         document_id: str,
                         version_id: str,
                         author: str) -> None:
        """Submit a document version for review."""
        
        document = self.vc.get_document(document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        # Submit for review
        self.vc.submit_for_review(document, version_id)
        
        # Send notifications
        if self.settings['notify_reviewers'] and document.reviewers:
            version = document.versions[version_id]
            self.notifications.notify_review_requested(
                document=document,
                version=version,
                reviewers=document.reviewers
            )
    
    def review_document(self,
                       document_id: str,
                       version_id: str,
                       reviewer: str,
                       status: ApprovalStatus,
                       comments: str = "",
                       author_email: str = "") -> None:
        """Review and approve/reject a document."""
        
        document = self.vc.get_document(document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        if reviewer not in document.reviewers:
            raise ValueError(f"User {reviewer} is not a reviewer for this document")
        
        # Add approval
        approval = self.vc.add_approval(
            document=document,
            version_id=version_id,
            reviewer=reviewer,
            status=status,
            comments=comments
        )
        
        # Reload document to get updated state
        document = self.vc.get_document(document_id)
        version = document.versions[version_id]
        
        # Send notification to author
        if self.settings['notify_authors'] and author_email:
            self.notifications.notify_approval_status(
                document=document,
                version=version,
                reviewer=reviewer,
                status=status,
                author_email=author_email
            )
        
        # Auto-publish if fully approved and setting enabled
        if (self.settings['auto_publish_when_approved'] and 
            version.state == DocumentState.APPROVED):
            self.vc.publish_version(document, version_id)
    
    def get_documents_in_review(self) -> List[Dict[str, Any]]:
        """Get documents currently in review state."""
        in_review = []
        
        for document in self.vc.list_documents():
            current_version = document.get_current_version()
            if not current_version or current_version.state != DocumentState.REVIEW:
                continue
            
            in_review.append({
                'document_id': document.id,
                'title': document.title,
                'package_date': document.package_date,
                'author': current_version.author,
                'version_id': current_version.id,
                'version_number': current_version.version_number,
                'submitted_at': current_version.timestamp,
                'reviewers': document.reviewers
            })
        
        # Sort by submission time
        return sorted(in_review, key=lambda x: x['submitted_at'])
    
    def get_workflow_stats(self) -> Dict[str, Any]:
        """Get workflow statistics."""
        documents = self.vc.list_documents()
        
        stats = {
            'total_documents': len(documents),
            'by_state': {state.value: 0 for state in DocumentState},
            'in_review': 0,
            'recent_activity': [],
            'avg_review_time': 0
        }
        
        review_times = []
        
        for document in documents:
            current_version = document.get_current_version()
            if current_version:
                stats['by_state'][current_version.state.value] += 1
                
                if current_version.state == DocumentState.REVIEW:
                    stats['in_review'] += 1
                
                # Calculate review time for completed reviews
                if current_version.state in [DocumentState.APPROVED, DocumentState.PUBLISHED]:
                    for approval in current_version.approvals:
                        if approval.status == ApprovalStatus.APPROVED:
                            review_time = (approval.timestamp - current_version.timestamp).total_seconds() / 3600
                            review_times.append(review_time)
        
        # Calculate average review time in hours
        if review_times:
            stats['avg_review_time'] = sum(review_times) / len(review_times)
        
        # Count documents in review
        stats['in_review'] = len(self.get_documents_in_review())
        
        # Recent activity
        all_versions = []
        for document in documents:
            for version in document.versions.values():
                all_versions.append({
                    'document_title': document.title,
                    'version_number': version.version_number,
                    'author': version.author,
                    'timestamp': version.timestamp,
                    'state': version.state.value
                })
        
        stats['recent_activity'] = sorted(
            all_versions, 
            key=lambda x: x['timestamp'], 
            reverse=True
        )[:10]
        
        return stats
    
    def configure_workflow(self, settings: Dict[str, Any]) -> None:
        """Update workflow settings."""
        self.settings.update(settings)
