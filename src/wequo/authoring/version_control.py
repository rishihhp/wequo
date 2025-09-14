"""
JSON-based version control system for weekly briefs.
"""

import os
import json
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import uuid

from .models import BriefDocument, BriefVersion, DocumentState, ApprovalStatus, ReviewComment, Approval


class VersionController:
    """JSON-based version control for brief documents."""
    
    def __init__(self, data_root: str = "data"):
        """Initialize version controller.
        
        Args:
            data_root: Path to data directory
        """
        self.data_root = Path(data_root)
        self.documents_dir = self.data_root / "authoring" / "documents"
        self.versions_dir = self.data_root / "authoring" / "versions"
        self.metadata_dir = self.data_root / "authoring" / "metadata"
        
        # Ensure directories exist
        self.documents_dir.mkdir(parents=True, exist_ok=True)
        self.versions_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
    
    def _generate_version_id(self) -> str:
        """Generate a unique version ID."""
        return str(uuid.uuid4())
    
    def _save_document_metadata(self, document: BriefDocument) -> None:
        """Save document metadata to JSON file."""
        metadata_file = self.metadata_dir / f"{document.id}.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(document.to_dict(), f, indent=2, ensure_ascii=False)
    
    def _load_document_metadata(self, document_id: str) -> Optional[BriefDocument]:
        """Load document metadata from JSON file."""
        metadata_file = self.metadata_dir / f"{document_id}.json"
        if not metadata_file.exists():
            return None
        
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return BriefDocument.from_dict(data)
        except Exception as e:
            print(f"Error loading document metadata {metadata_file}: {e}")
            return None
    
    def create_document(self, 
                       title: str,
                       package_date: str, 
                       author: str,
                       initial_content: str = "",
                       reviewers: Optional[List[str]] = None) -> BriefDocument:
        """Create a new document with initial version."""
        
        document = BriefDocument(
            id=self._generate_version_id(),
            title=title,
            package_date=package_date,
            author=author,
            reviewers=reviewers or [],
            file_path=f"documents/{package_date}_brief.md"
        )
        
        # Create initial version
        initial_version = BriefVersion(
            id=self._generate_version_id(),
            version_number="1.0",
            author=author,
            content=initial_content,
            metadata={
                "created_from": "template",
                "package_date": package_date
            },
            state=DocumentState.DRAFT
        )
        
        document.add_version(initial_version)
        
        # Save document file
        doc_path = self.documents_dir / f"{package_date}_brief.md"
        doc_path.write_text(initial_content, encoding='utf-8')
        
        # Save version content
        version_path = self.versions_dir / f"{initial_version.id}.md"
        version_path.write_text(initial_content, encoding='utf-8')
        
        # Save metadata
        self._save_document_metadata(document)
        
        return document
    
    def update_document(self, 
                       document: BriefDocument,
                       content: str,
                       author: str,
                       commit_message: Optional[str] = None) -> BriefVersion:
        """Update document with new version."""
        
        current_version = document.get_current_version()
        if not current_version:
            raise ValueError("Document has no current version")
        
        # Generate new version number
        version_parts = current_version.version_number.split('.')
        if len(version_parts) >= 2:
            major, minor = int(version_parts[0]), int(version_parts[1])
            if current_version.state == DocumentState.PUBLISHED:
                # New major version for published documents
                new_version_number = f"{major + 1}.0"
            else:
                # Minor version increment
                new_version_number = f"{major}.{minor + 1}"
        else:
            new_version_number = "1.1"
        
        # Create new version
        new_version = BriefVersion(
            id=self._generate_version_id(),
            version_number=new_version_number,
            author=author,
            content=content,
            metadata={
                "updated_from": current_version.id,
                "package_date": document.package_date,
                "commit_message": commit_message
            },
            state=DocumentState.DRAFT,
            parent_version=current_version.id
        )
        
        document.add_version(new_version)
        
        # Update document file
        doc_path = self.documents_dir / f"{document.package_date}_brief.md"
        doc_path.write_text(content, encoding='utf-8')
        
        # Save version content
        version_path = self.versions_dir / f"{new_version.id}.md"
        version_path.write_text(content, encoding='utf-8')
        
        # Save metadata
        self._save_document_metadata(document)
        
        return new_version
    
    def revert_to_version(self, 
                         document: BriefDocument,
                         version_id: str,
                         author: str) -> BriefVersion:
        """Revert document to a specific version."""
        
        if version_id not in document.versions:
            raise ValueError(f"Version {version_id} not found")
        
        target_version = document.versions[version_id]
        
        # Create new version based on target
        reverted_version = BriefVersion(
            id=self._generate_version_id(),
            version_number=f"{target_version.version_number}-reverted",
            author=author,
            content=target_version.content,
            metadata={
                "reverted_from": version_id,
                "original_version": target_version.version_number,
                "package_date": document.package_date
            },
            state=DocumentState.DRAFT
        )
        
        document.add_version(reverted_version)
        
        # Update document file
        doc_path = self.documents_dir / f"{document.package_date}_brief.md"
        doc_path.write_text(target_version.content, encoding='utf-8')
        
        # Save version content
        version_path = self.versions_dir / f"{reverted_version.id}.md"
        version_path.write_text(target_version.content, encoding='utf-8')
        
        # Save metadata
        self._save_document_metadata(document)
        
        return reverted_version
    
    def get_version_diff(self, 
                        document: BriefDocument,
                        version_a: str,
                        version_b: str) -> Dict[str, Any]:
        """Get diff between two versions."""
        
        if version_a not in document.versions or version_b not in document.versions:
            raise ValueError("One or both versions not found")
        
        version_a_obj = document.versions[version_a]
        version_b_obj = document.versions[version_b]
        
        # Simple diff implementation
        lines_a = version_a_obj.content.split('\n')
        lines_b = version_b_obj.content.split('\n')
        
        diff_lines = []
        max_lines = max(len(lines_a), len(lines_b))
        
        for i in range(max_lines):
            line_a = lines_a[i] if i < len(lines_a) else ""
            line_b = lines_b[i] if i < len(lines_b) else ""
            
            if line_a != line_b:
                if i < len(lines_a) and i < len(lines_b):
                    diff_lines.append(f"- {line_a}")
                    diff_lines.append(f"+ {line_b}")
                elif i < len(lines_a):
                    diff_lines.append(f"- {line_a}")
                else:
                    diff_lines.append(f"+ {line_b}")
            else:
                diff_lines.append(f"  {line_a}")
        
        diff_output = '\n'.join(diff_lines)
        
        return {
            'version_a': {
                'id': version_a,
                'version_number': version_a_obj.version_number,
                'author': version_a_obj.author,
                'timestamp': version_a_obj.timestamp.isoformat()
            },
            'version_b': {
                'id': version_b,
                'version_number': version_b_obj.version_number,
                'author': version_b_obj.author,
                'timestamp': version_b_obj.timestamp.isoformat()
            },
            'diff': diff_output,
            'raw_diff': self._parse_diff(diff_output)
        }
    
    def _parse_diff(self, diff_output: str) -> List[Dict[str, Any]]:
        """Parse diff output into structured format."""
        lines = diff_output.split('\n')
        parsed_diff = []
        current_hunk = {
            'header': 'Changes',
            'changes': []
        }
        
        for line in lines:
            change_type = 'context'
            if line.startswith('+'):
                change_type = 'addition'
            elif line.startswith('-'):
                change_type = 'deletion'
            
            current_hunk['changes'].append({
                'type': change_type,
                'content': line[2:] if line.startswith(('+', '-', ' ')) else line
            })
        
        if current_hunk['changes']:
            parsed_diff.append(current_hunk)
        
        return parsed_diff
    
    def add_comment(self, 
                   document: BriefDocument,
                   version_id: str,
                   author: str,
                   content: str,
                   line_number: Optional[int] = None,
                   thread_id: Optional[str] = None) -> ReviewComment:
        """Add a review comment to a version."""
        
        if version_id not in document.versions:
            raise ValueError(f"Version {version_id} not found")
        
        comment = ReviewComment(
            author=author,
            content=content,
            line_number=line_number,
            thread_id=thread_id
        )
        
        document.versions[version_id].comments.append(comment)
        document.updated_at = datetime.now()
        
        # Save metadata
        self._save_document_metadata(document)
        
        return comment
    
    def add_approval(self,
                    document: BriefDocument,
                    version_id: str,
                    reviewer: str,
                    status: ApprovalStatus,
                    comments: str = "") -> Approval:
        """Add an approval/rejection to a version."""
        
        if version_id not in document.versions:
            raise ValueError(f"Version {version_id} not found")
        
        version = document.versions[version_id]
        
        # Remove any existing approval from this reviewer
        version.approvals = [a for a in version.approvals if a.reviewer != reviewer]
        
        approval = Approval(
            reviewer=reviewer,
            status=status,
            comments=comments,
            version_id=version_id
        )
        
        version.approvals.append(approval)
        document.updated_at = datetime.now()
        
        # Update version state if fully approved
        approval_status = document.get_approvals_status()
        if approval_status['status'] == 'fully_approved' and version.state == DocumentState.REVIEW:
            version.state = DocumentState.APPROVED
        elif approval_status['status'] in ['rejected', 'changes_requested']:
            version.state = DocumentState.DRAFT
        
        # Save metadata
        self._save_document_metadata(document)
        
        return approval
    
    def submit_for_review(self, document: BriefDocument, version_id: str) -> None:
        """Submit a version for review."""
        
        if version_id not in document.versions:
            raise ValueError(f"Version {version_id} not found")
        
        version = document.versions[version_id]
        version.state = DocumentState.REVIEW
        document.updated_at = datetime.now()
        
        # Save metadata
        self._save_document_metadata(document)
    
    def publish_version(self, document: BriefDocument, version_id: str) -> None:
        """Publish an approved version."""
        
        if version_id not in document.versions:
            raise ValueError(f"Version {version_id} not found")
        
        version = document.versions[version_id]
        
        if version.state != DocumentState.APPROVED:
            raise ValueError("Can only publish approved versions")
        
        version.state = DocumentState.PUBLISHED
        version.tags.append("published")
        document.updated_at = datetime.now()
        
        # Save metadata
        self._save_document_metadata(document)
    
    def list_documents(self) -> List[BriefDocument]:
        """List all documents in the repository."""
        documents = []
        
        for metadata_file in self.metadata_dir.glob("*.json"):
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                document = BriefDocument.from_dict(data)
                documents.append(document)
            except Exception as e:
                print(f"Error loading document metadata {metadata_file}: {e}")
        
        return sorted(documents, key=lambda d: d.updated_at, reverse=True)
    
    def get_document(self, document_id: str) -> Optional[BriefDocument]:
        """Get a document by ID."""
        return self._load_document_metadata(document_id)
    
    def get_document_by_date(self, package_date: str) -> Optional[BriefDocument]:
        """Get a document by package date."""
        for document in self.list_documents():
            if document.package_date == package_date:
                return document
        return None
    
    def get_version_log(self, document: BriefDocument, max_entries: int = 20) -> List[Dict[str, Any]]:
        """Get version log for document."""
        history = document.get_version_history()
        entries = []
        
        for version in history[:max_entries]:
            entries.append({
                'version_id': version.id,
                'version_number': version.version_number,
                'message': version.metadata.get('commit_message', f"Version {version.version_number}"),
                'author': version.author,
                'timestamp': version.timestamp.isoformat()
            })
        
        return entries
    
    def backup_data(self, backup_path: str) -> None:
        """Create a backup of the authoring data."""
        backup_dest = Path(backup_path)
        
        if backup_dest.exists():
            import shutil
            shutil.rmtree(backup_dest)
        
        import shutil
        shutil.copytree(self.data_root / "authoring", backup_dest)
        print(f"Authoring data backed up to: {backup_dest}")
