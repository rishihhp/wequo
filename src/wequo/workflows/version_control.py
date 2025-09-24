"""
Version control system for WeQuo briefs.

Manages version history, branching, and rollback capabilities for weekly briefs.
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib


class VersionStatus(Enum):
    """Status of a version."""
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    PUBLISHED = "published"
    ARCHIVED = "archived"


@dataclass
class VersionInfo:
    """Information about a version."""
    version_id: str
    date: str
    author: str
    status: VersionStatus
    message: str
    parent_version: Optional[str] = None
    created_at: str = ""
    file_hash: str = ""
    file_size: int = 0


class VersionManager:
    """
    Manages version control for WeQuo briefs.
    
    Features:
    - Git-like versioning with commits
    - Branch support for different versions
    - Rollback capabilities
    - Version comparison
    - Metadata tracking
    """
    
    def __init__(self, base_path: Path):
        self.base_path = Path(base_path)
        self.versions_path = self.base_path / ".versions"
        self.versions_path.mkdir(exist_ok=True)
        
        # Initialize version tracking
        self.version_file = self.versions_path / "versions.json"
        self.versions = self._load_versions()
    
    def _load_versions(self) -> Dict[str, List[VersionInfo]]:
        """Load version history from disk."""
        if not self.version_file.exists():
            return {}
        
        try:
            with open(self.version_file, 'r') as f:
                data = json.load(f)
            
            # Convert back to VersionInfo objects
            versions = {}
            for date, version_list in data.items():
                versions[date] = [
                    VersionInfo(
                        version_id=v['version_id'],
                        date=v['date'],
                        author=v['author'],
                        status=VersionStatus(v['status']) if isinstance(v['status'], str) else v['status'],
                        message=v['message'],
                        parent_version=v.get('parent_version'),
                        created_at=v.get('created_at', ''),
                        file_hash=v.get('file_hash', ''),
                        file_size=v.get('file_size', 0)
                    )
                    for v in version_list
                ]
            
            return versions
        except Exception as e:
            print(f"Error loading versions: {e}")
            return {}
    
    def _save_versions(self):
        """Save version history to disk."""
        try:
            # Convert to serializable format
            data = {}
            for date, version_list in self.versions.items():
                data[date] = []
                for v in version_list:
                    version_dict = asdict(v)
                    version_dict['status'] = v.status.value  # Convert enum to string
                    data[date].append(version_dict)
            
            with open(self.version_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving versions: {e}")
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of a file."""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            return ""
    
    def create_version(
        self, 
        date: str, 
        author: str, 
        message: str, 
        source_files: List[Path],
        status: VersionStatus = VersionStatus.DRAFT,
        parent_version: Optional[str] = None
    ) -> str:
        """
        Create a new version of the brief.
        
        Args:
            date: Date of the brief (YYYY-MM-DD)
            author: Author name
            message: Commit message
            source_files: List of files to version
            status: Version status
            parent_version: Parent version ID (for branching)
            
        Returns:
            Version ID
        """
        # Generate version ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        version_id = f"{date}_{timestamp}_{author.replace(' ', '_')}"
        
        # Create version directory
        version_dir = self.versions_path / date / version_id
        version_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy files to version directory
        total_size = 0
        file_hashes = []
        
        for source_file in source_files:
            if source_file.exists():
                dest_file = version_dir / source_file.name
                shutil.copy2(source_file, dest_file)
                
                # Calculate file hash and size
                file_hash = self._calculate_file_hash(dest_file)
                file_size = dest_file.stat().st_size
                total_size += file_size
                file_hashes.append(file_hash)
        
        # Calculate combined hash
        combined_hash = hashlib.sha256(''.join(file_hashes).encode()).hexdigest()
        
        # Create version info
        version_info = VersionInfo(
            version_id=version_id,
            date=date,
            author=author,
            status=status,
            message=message,
            parent_version=parent_version,
            created_at=datetime.now().isoformat(),
            file_hash=combined_hash,
            file_size=total_size
        )
        
        # Add to versions
        if date not in self.versions:
            self.versions[date] = []
        
        self.versions[date].append(version_info)
        self._save_versions()
        
        return version_id
    
    def get_versions(self, date: str) -> List[VersionInfo]:
        """Get all versions for a specific date."""
        return self.versions.get(date, [])
    
    def get_latest_version(self, date: str) -> Optional[VersionInfo]:
        """Get the latest version for a specific date."""
        versions = self.get_versions(date)
        if not versions:
            return None
        
        # Sort by creation time (latest first)
        return sorted(versions, key=lambda v: v.created_at, reverse=True)[0]
    
    def get_version_by_id(self, version_id: str) -> Optional[VersionInfo]:
        """Get version info by version ID."""
        for date_versions in self.versions.values():
            for version in date_versions:
                if version.version_id == version_id:
                    return version
        return None
    
    def restore_version(self, version_id: str, target_path: Path) -> bool:
        """
        Restore files from a specific version.
        
        Args:
            version_id: Version to restore
            target_path: Where to restore files
            
        Returns:
            True if successful
        """
        version_info = self.get_version_by_id(version_id)
        if not version_info:
            return False
        
        version_dir = self.versions_path / version_info.date / version_id
        
        if not version_dir.exists():
            return False
        
        try:
            # Create target directory if it doesn't exist
            target_path.mkdir(parents=True, exist_ok=True)
            
            # Copy files from version directory
            for file_path in version_dir.iterdir():
                if file_path.is_file():
                    dest_file = target_path / file_path.name
                    shutil.copy2(file_path, dest_file)
            
            return True
        except Exception as e:
            print(f"Error restoring version: {e}")
            return False
    
    def compare_versions(self, version_id_1: str, version_id_2: str) -> Dict[str, Any]:
        """
        Compare two versions.
        
        Args:
            version_id_1: First version ID
            version_id_2: Second version ID
            
        Returns:
            Comparison results
        """
        version_1 = self.get_version_by_id(version_id_1)
        version_2 = self.get_version_by_id(version_id_2)
        
        if not version_1 or not version_2:
            return {"error": "One or both versions not found"}
        
        return {
            "version_1": {
                "id": version_1.version_id,
                "date": version_1.date,
                "author": version_1.author,
                "status": version_1.status.value,
                "message": version_1.message,
                "created_at": version_1.created_at,
                "file_size": version_1.file_size
            },
            "version_2": {
                "id": version_2.version_id,
                "date": version_2.date,
                "author": version_2.author,
                "status": version_2.status.value,
                "message": version_2.message,
                "created_at": version_2.created_at,
                "file_size": version_2.file_size
            },
            "differences": {
                "same_author": version_1.author == version_2.author,
                "same_status": version_1.status == version_2.status,
                "size_difference": version_2.file_size - version_1.file_size,
                "time_difference": self._calculate_time_difference(
                    version_1.created_at, version_2.created_at
                )
            }
        }
    
    def _calculate_time_difference(self, time1: str, time2: str) -> str:
        """Calculate time difference between two timestamps."""
        try:
            dt1 = datetime.fromisoformat(time1)
            dt2 = datetime.fromisoformat(time2)
            diff = dt2 - dt1
            
            if diff.days > 0:
                return f"{diff.days} days"
            elif diff.seconds > 3600:
                hours = diff.seconds // 3600
                return f"{hours} hours"
            elif diff.seconds > 60:
                minutes = diff.seconds // 60
                return f"{minutes} minutes"
            else:
                return f"{diff.seconds} seconds"
        except Exception:
            return "unknown"
    
    def update_version_status(self, version_id: str, new_status: VersionStatus) -> bool:
        """Update the status of a version."""
        version_info = self.get_version_by_id(version_id)
        if not version_info:
            return False
        
        version_info.status = new_status
        self._save_versions()
        return True
    
    def delete_version(self, version_id: str) -> bool:
        """Delete a version (and its files)."""
        version_info = self.get_version_by_id(version_id)
        if not version_info:
            return False
        
        try:
            # Remove files
            version_dir = self.versions_path / version_info.date / version_id
            if version_dir.exists():
                shutil.rmtree(version_dir)
            
            # Remove from versions list
            for date_versions in self.versions.values():
                if version_info in date_versions:
                    date_versions.remove(version_info)
                    break
            
            self._save_versions()
            return True
        except Exception as e:
            print(f"Error deleting version: {e}")
            return False
    
    def get_version_history(self, date: str) -> List[Dict[str, Any]]:
        """Get version history for a date."""
        versions = self.get_versions(date)
        
        history = []
        for version in sorted(versions, key=lambda v: v.created_at, reverse=True):
            history.append({
                "version_id": version.version_id,
                "author": version.author,
                "status": version.status.value,
                "message": version.message,
                "created_at": version.created_at,
                "file_size": version.file_size,
                "parent_version": version.parent_version
            })
        
        return history
    
    def create_branch(self, base_version_id: str, new_author: str, branch_message: str) -> str:
        """Create a new branch from an existing version."""
        base_version = self.get_version_by_id(base_version_id)
        if not base_version:
            raise ValueError(f"Base version {base_version_id} not found")
        
        # Create new version with parent
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_version_id = f"{base_version.date}_{timestamp}_{new_author.replace(' ', '_')}_branch"
        
        # Copy files from base version
        base_version_dir = self.versions_path / base_version.date / base_version_id
        if not base_version_dir.exists():
            raise ValueError(f"Base version files not found")
        
        # Create new version directory
        new_version_dir = self.versions_path / base_version.date / new_version_id
        new_version_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy files
        for file_path in base_version_dir.iterdir():
            if file_path.is_file():
                shutil.copy2(file_path, new_version_dir / file_path.name)
        
        # Create version info
        version_info = VersionInfo(
            version_id=new_version_id,
            date=base_version.date,
            author=new_author,
            status=VersionStatus.DRAFT,
            message=branch_message,
            parent_version=base_version_id,
            created_at=datetime.now().isoformat(),
            file_hash=base_version.file_hash,
            file_size=base_version.file_size
        )
        
        # Add to versions
        if base_version.date not in self.versions:
            self.versions[base_version.date] = []
        
        self.versions[base_version.date].append(version_info)
        self._save_versions()
        
        return new_version_id
    
    def get_branch_info(self, version_id: str) -> Dict[str, Any]:
        """Get information about a branch."""
        version_info = self.get_version_by_id(version_id)
        if not version_info:
            return {"error": "Version not found"}
        
        # Find all versions in the same branch
        branch_versions = []
        current_version = version_info
        
        # Go up the parent chain
        while current_version:
            branch_versions.append(current_version)
            if current_version.parent_version:
                current_version = self.get_version_by_id(current_version.parent_version)
            else:
                break
        
        # Find child versions
        for date_versions in self.versions.values():
            for version in date_versions:
                if version.parent_version == version_id:
                    branch_versions.extend(self._get_all_children(version))
        
        return {
            "version_id": version_info.version_id,
            "branch_length": len(branch_versions),
            "branch_versions": [
                {
                    "version_id": v.version_id,
                    "author": v.author,
                    "status": v.status.value,
                    "created_at": v.created_at
                }
                for v in sorted(branch_versions, key=lambda x: x.created_at)
            ]
        }
    
    def _get_all_children(self, version: VersionInfo) -> List[VersionInfo]:
        """Get all child versions recursively."""
        children = []
        for date_versions in self.versions.values():
            for child_version in date_versions:
                if child_version.parent_version == version.version_id:
                    children.append(child_version)
                    children.extend(self._get_all_children(child_version))
        return children
