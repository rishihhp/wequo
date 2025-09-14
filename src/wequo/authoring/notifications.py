"""
Notification service for the authoring system.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending notifications via email."""
    
    def __init__(self, 
                 smtp_host: str = "",
                 smtp_port: int = 587,
                 smtp_user: str = "",
                 smtp_password: str = ""):
        """Initialize notification service.
        
        Args:
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port
            smtp_user: SMTP username
            smtp_password: SMTP password
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.enabled = bool(smtp_host and smtp_user and smtp_password)
    
    def send_review_notification(self, 
                                reviewer_email: str,
                                document_title: str,
                                author: str,
                                document_url: str) -> bool:
        """Send notification to reviewer about pending review.
        
        Args:
            reviewer_email: Email address of reviewer
            document_title: Title of document to review
            author: Author of the document
            document_url: URL to access the document
            
        Returns:
            True if notification sent successfully, False otherwise
        """
        if not self.enabled:
            logger.info(f"Notifications disabled - would send review notification to {reviewer_email}")
            return True
        
        subject = f"Review Request: {document_title}"
        body = f"""
Hello,

You have been assigned to review the following document:

Title: {document_title}
Author: {author}

Please review the document at: {document_url}

Thank you for your time.

Best regards,
WeQuo Authoring System
"""
        
        return self._send_email(reviewer_email, subject, body)
    
    def send_approval_notification(self,
                                  author_email: str,
                                  document_title: str,
                                  reviewer: str,
                                  status: str,
                                  comments: str = "") -> bool:
        """Send notification to author about approval status.
        
        Args:
            author_email: Email address of author
            document_title: Title of document
            reviewer: Name of reviewer
            status: Approval status (approved, rejected, changes_requested)
            comments: Review comments
            
        Returns:
            True if notification sent successfully, False otherwise
        """
        if not self.enabled:
            logger.info(f"Notifications disabled - would send approval notification to {author_email}")
            return True
        
        status_text = {
            'approved': 'approved',
            'rejected': 'rejected',
            'changes_requested': 'requested changes for'
        }.get(status, status)
        
        subject = f"Document {status_text.title()}: {document_title}"
        body = f"""
Hello,

Your document has been {status_text}:

Title: {document_title}
Reviewer: {reviewer}
Status: {status_text.title()}
"""
        
        if comments:
            body += f"\nComments:\n{comments}\n"
        
        body += """
Thank you for using WeQuo Authoring System.

Best regards,
WeQuo Authoring System
"""
        
        return self._send_email(author_email, subject, body)
    
    def send_publish_notification(self,
                                 author_email: str,
                                 document_title: str,
                                 publish_url: str) -> bool:
        """Send notification about document publication.
        
        Args:
            author_email: Email address of author
            document_title: Title of document
            publish_url: URL to published document
            
        Returns:
            True if notification sent successfully, False otherwise
        """
        if not self.enabled:
            logger.info(f"Notifications disabled - would send publish notification to {author_email}")
            return True
        
        subject = f"Document Published: {document_title}"
        body = f"""
Hello,

Your document has been published:

Title: {document_title}
Published URL: {publish_url}

Congratulations on getting your document published!

Best regards,
WeQuo Authoring System
"""
        
        return self._send_email(author_email, subject, body)
    
    def _send_email(self, to_email: str, subject: str, body: str) -> bool:
        """Send email notification.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            msg = MIMEMultipart()
            msg['From'] = self.smtp_user
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            
            text = msg.as_string()
            server.sendmail(self.smtp_user, to_email, text)
            server.quit()
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
