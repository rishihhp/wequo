"""
Editorial notes and feedback system for WeQuo briefs.

Manages editorial comments, feedback, and collaboration features
for content review and improvement.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class NoteType(Enum):
    """Type of editorial note."""
    COMMENT = "comment"
    SUGGESTION = "suggestion"
    QUESTION = "question"
    CRITICAL = "critical"
    PRAISE = "praise"
    TECHNICAL = "technical"
    STYLE = "style"
    FACT_CHECK = "fact_check"


class NoteStatus(Enum):
    """Status of a note."""
    OPEN = "open"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


@dataclass
class EditorialNote:
    """An editorial note or comment."""
    note_id: str
    version_id: str
    author: str
    note_type: NoteType
    status: NoteStatus
    title: str
    content: str
    target_section: Optional[str] = None
    target_line: Optional[int] = None
    created_at: str = ""
    updated_at: str = ""
    resolved_by: Optional[str] = None
    resolved_at: Optional[str] = None
    priority: int = 1  # 1=low, 2=medium, 3=high, 4=critical
    tags: List[str] = None
    replies: List[Dict[str, str]] = None


class EditorialNotes:
    """
    Manages editorial notes and feedback for WeQuo briefs.
    
    Features:
    - Section-specific comments
    - Line-by-line feedback
    - Note categorization and prioritization
    - Resolution tracking
    - Reply system
    - Search and filtering
    """
    
    def __init__(self, base_path: Path):
        self.base_path = Path(base_path)
        self.workflows_path = self.base_path / ".workflows"
        self.workflows_path.mkdir(exist_ok=True)
        
        # Initialize notes file
        self.notes_file = self.workflows_path / "editorial_notes.json"
        self.notes = self._load_notes()
    
    def _load_notes(self) -> Dict[str, EditorialNote]:
        """Load editorial notes from disk."""
        if not self.notes_file.exists():
            return {}
        
        try:
            with open(self.notes_file, 'r') as f:
                data = json.load(f)
            
            notes = {}
            for note_id, note_data in data.items():
                notes[note_id] = EditorialNote(
                    note_id=note_data['note_id'],
                    version_id=note_data['version_id'],
                    author=note_data['author'],
                    note_type=NoteType(note_data['note_type']),
                    status=NoteStatus(note_data['status']),
                    title=note_data['title'],
                    content=note_data['content'],
                    target_section=note_data.get('target_section'),
                    target_line=note_data.get('target_line'),
                    created_at=note_data.get('created_at', ''),
                    updated_at=note_data.get('updated_at', ''),
                    resolved_by=note_data.get('resolved_by'),
                    resolved_at=note_data.get('resolved_at'),
                    priority=note_data.get('priority', 1),
                    tags=note_data.get('tags', []),
                    replies=note_data.get('replies', [])
                )
            
            return notes
        except Exception as e:
            print(f"Error loading notes: {e}")
            return {}
    
    def _save_notes(self):
        """Save editorial notes to disk."""
        try:
            data = {}
            for note_id, note in self.notes.items():
                data[note_id] = asdict(note)
                # Convert enum values to strings
                data[note_id]['note_type'] = note.note_type.value
                data[note_id]['status'] = note.status.value
            
            with open(self.notes_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving notes: {e}")
    
    def create_note(
        self,
        version_id: str,
        author: str,
        note_type: NoteType,
        title: str,
        content: str,
        target_section: Optional[str] = None,
        target_line: Optional[int] = None,
        priority: int = 1,
        tags: List[str] = None
    ) -> str:
        """
        Create a new editorial note.
        
        Args:
            version_id: Version this note applies to
            author: Author of the note
            note_type: Type of note
            title: Note title
            content: Note content
            target_section: Specific section (optional)
            target_line: Specific line number (optional)
            priority: Priority level (1-4)
            tags: List of tags
            
        Returns:
            Note ID
        """
        # Generate note ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        note_id = f"note_{timestamp}_{author.replace(' ', '_')}"
        
        # Create note
        note = EditorialNote(
            note_id=note_id,
            version_id=version_id,
            author=author,
            note_type=note_type,
            status=NoteStatus.OPEN,
            title=title,
            content=content,
            target_section=target_section,
            target_line=target_line,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            priority=priority,
            tags=tags or [],
            replies=[]
        )
        
        self.notes[note_id] = note
        self._save_notes()
        
        return note_id
    
    def get_note(self, note_id: str) -> Optional[EditorialNote]:
        """Get a note by ID."""
        return self.notes.get(note_id)
    
    def get_notes_by_version(self, version_id: str) -> List[EditorialNote]:
        """Get all notes for a specific version."""
        return [
            note for note in self.notes.values()
            if note.version_id == version_id
        ]
    
    def get_notes_by_author(self, author: str) -> List[EditorialNote]:
        """Get all notes by a specific author."""
        return [
            note for note in self.notes.values()
            if note.author == author
        ]
    
    def get_notes_by_type(self, note_type: NoteType) -> List[EditorialNote]:
        """Get all notes of a specific type."""
        return [
            note for note in self.notes.values()
            if note.note_type == note_type
        ]
    
    def get_notes_by_status(self, status: NoteStatus) -> List[EditorialNote]:
        """Get all notes with a specific status."""
        return [
            note for note in self.notes.values()
            if note.status == status
        ]
    
    def get_notes_by_priority(self, min_priority: int = 1) -> List[EditorialNote]:
        """Get notes with priority >= min_priority."""
        return [
            note for note in self.notes.values()
            if note.priority >= min_priority
        ]
    
    def get_notes_by_section(self, version_id: str, section: str) -> List[EditorialNote]:
        """Get notes for a specific section of a version."""
        return [
            note for note in self.notes.values()
            if note.version_id == version_id and note.target_section == section
        ]
    
    def search_notes(self, query: str) -> List[EditorialNote]:
        """Search notes by title or content."""
        query_lower = query.lower()
        matching_notes = []
        
        for note in self.notes.values():
            if (query_lower in note.title.lower() or 
                query_lower in note.content.lower() or
                any(query_lower in tag.lower() for tag in note.tags)):
                matching_notes.append(note)
        
        return matching_notes
    
    def update_note(
        self,
        note_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        priority: Optional[int] = None,
        tags: Optional[List[str]] = None
    ) -> bool:
        """Update a note."""
        if note_id not in self.notes:
            return False
        
        note = self.notes[note_id]
        
        if title is not None:
            note.title = title
        if content is not None:
            note.content = content
        if priority is not None:
            note.priority = priority
        if tags is not None:
            note.tags = tags
        
        note.updated_at = datetime.now().isoformat()
        self._save_notes()
        
        return True
    
    def resolve_note(self, note_id: str, resolved_by: str, resolution_comment: str = "") -> bool:
        """Resolve a note."""
        if note_id not in self.notes:
            return False
        
        note = self.notes[note_id]
        note.status = NoteStatus.RESOLVED
        note.resolved_by = resolved_by
        note.resolved_at = datetime.now().isoformat()
        note.updated_at = datetime.now().isoformat()
        
        # Add resolution comment as a reply
        if resolution_comment:
            note.replies.append({
                "author": resolved_by,
                "content": resolution_comment,
                "timestamp": datetime.now().isoformat(),
                "type": "resolution"
            })
        
        self._save_notes()
        return True
    
    def dismiss_note(self, note_id: str, dismissed_by: str, dismissal_reason: str = "") -> bool:
        """Dismiss a note."""
        if note_id not in self.notes:
            return False
        
        note = self.notes[note_id]
        note.status = NoteStatus.DISMISSED
        note.resolved_by = dismissed_by
        note.resolved_at = datetime.now().isoformat()
        note.updated_at = datetime.now().isoformat()
        
        # Add dismissal reason as a reply
        if dismissal_reason:
            note.replies.append({
                "author": dismissed_by,
                "content": dismissal_reason,
                "timestamp": datetime.now().isoformat(),
                "type": "dismissal"
            })
        
        self._save_notes()
        return True
    
    def reopen_note(self, note_id: str, reopened_by: str, reason: str = "") -> bool:
        """Reopen a resolved or dismissed note."""
        if note_id not in self.notes:
            return False
        
        note = self.notes[note_id]
        note.status = NoteStatus.OPEN
        note.resolved_by = None
        note.resolved_at = None
        note.updated_at = datetime.now().isoformat()
        
        # Add reopen reason as a reply
        if reason:
            note.replies.append({
                "author": reopened_by,
                "content": reason,
                "timestamp": datetime.now().isoformat(),
                "type": "reopen"
            })
        
        self._save_notes()
        return True
    
    def add_reply(self, note_id: str, author: str, content: str) -> bool:
        """Add a reply to a note."""
        if note_id not in self.notes:
            return False
        
        note = self.notes[note_id]
        note.replies.append({
            "author": author,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "type": "reply"
        })
        
        note.updated_at = datetime.now().isoformat()
        self._save_notes()
        
        return True
    
    def get_note_summary(self, version_id: str) -> Dict[str, Any]:
        """Get summary of notes for a version."""
        version_notes = self.get_notes_by_version(version_id)
        
        if not version_notes:
            return {
                "total_notes": 0,
                "by_type": {},
                "by_status": {},
                "by_priority": {},
                "open_notes": 0,
                "resolved_notes": 0,
                "critical_notes": 0
            }
        
        # Count by type
        by_type = {}
        for note in version_notes:
            note_type = note.note_type.value
            by_type[note_type] = by_type.get(note_type, 0) + 1
        
        # Count by status
        by_status = {}
        for note in version_notes:
            status = note.status.value
            by_status[status] = by_status.get(status, 0) + 1
        
        # Count by priority
        by_priority = {}
        for note in version_notes:
            priority = note.priority
            by_priority[priority] = by_priority.get(priority, 0) + 1
        
        return {
            "total_notes": len(version_notes),
            "by_type": by_type,
            "by_status": by_status,
            "by_priority": by_priority,
            "open_notes": len([n for n in version_notes if n.status == NoteStatus.OPEN]),
            "resolved_notes": len([n for n in version_notes if n.status == NoteStatus.RESOLVED]),
            "critical_notes": len([n for n in version_notes if n.priority >= 4])
        }
    
    def get_author_activity(self, author: str) -> Dict[str, Any]:
        """Get activity summary for an author."""
        author_notes = self.get_notes_by_author(author)
        
        if not author_notes:
            return {
                "total_notes": 0,
                "notes_created": 0,
                "notes_resolved": 0,
                "replies_made": 0,
                "by_type": {}
            }
        
        # Count notes created
        notes_created = len(author_notes)
        
        # Count notes resolved by this author
        notes_resolved = len([
            note for note in self.notes.values()
            if note.resolved_by == author
        ])
        
        # Count replies made
        replies_made = sum(
            len([reply for reply in note.replies if reply["author"] == author])
            for note in self.notes.values()
        )
        
        # Count by type
        by_type = {}
        for note in author_notes:
            note_type = note.note_type.value
            by_type[note_type] = by_type.get(note_type, 0) + 1
        
        return {
            "total_notes": notes_created,
            "notes_created": notes_created,
            "notes_resolved": notes_resolved,
            "replies_made": replies_made,
            "by_type": by_type
        }
    
    def export_notes(self, version_id: str, format: str = "json") -> str:
        """Export notes for a version."""
        version_notes = self.get_notes_by_version(version_id)
        
        if format == "json":
            return json.dumps([asdict(note) for note in version_notes], indent=2, default=str)
        elif format == "markdown":
            return self._export_notes_markdown(version_notes)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _export_notes_markdown(self, notes: List[EditorialNote]) -> str:
        """Export notes as markdown."""
        if not notes:
            return "# Editorial Notes\n\nNo notes found.\n"
        
        markdown = "# Editorial Notes\n\n"
        
        # Group by section
        sections = {}
        for note in notes:
            section = note.target_section or "General"
            if section not in sections:
                sections[section] = []
            sections[section].append(note)
        
        for section, section_notes in sections.items():
            markdown += f"## {section}\n\n"
            
            for note in sorted(section_notes, key=lambda n: n.priority, reverse=True):
                priority_emoji = {1: "🟢", 2: "🟡", 3: "🟠", 4: "🔴"}.get(note.priority, "⚪")
                status_emoji = {
                    NoteStatus.OPEN: "🔓",
                    NoteStatus.RESOLVED: "✅",
                    NoteStatus.DISMISSED: "❌"
                }.get(note.status, "❓")
                
                markdown += f"### {priority_emoji} {status_emoji} {note.title}\n\n"
                markdown += f"**Type:** {note.note_type.value}  \n"
                markdown += f"**Author:** {note.author}  \n"
                markdown += f"**Created:** {note.created_at}  \n"
                
                if note.target_line:
                    markdown += f"**Line:** {note.target_line}  \n"
                
                if note.tags:
                    markdown += f"**Tags:** {', '.join(note.tags)}  \n"
                
                markdown += f"\n{note.content}\n\n"
                
                # Add replies
                if note.replies:
                    markdown += "**Replies:**\n\n"
                    for reply in note.replies:
                        markdown += f"- **{reply['author']}** ({reply['timestamp']}): {reply['content']}\n"
                    markdown += "\n"
                
                markdown += "---\n\n"
        
        return markdown
