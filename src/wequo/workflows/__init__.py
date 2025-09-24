"""
Author review workflows for WeQuo.

Provides version control, approval systems, and editorial workflows
for managing weekly briefs and content.
"""

from .version_control import VersionManager
from .approval import ApprovalWorkflow
from .editorial import EditorialNotes

__all__ = ['VersionManager', 'ApprovalWorkflow', 'EditorialNotes']
