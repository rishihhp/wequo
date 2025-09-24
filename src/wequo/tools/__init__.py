"""Author tools for WeQuo Phase 1.

This package provides tools for authors to:
- Fetch weekly data packages
- Pre-fill templates with data
- Generate author-ready briefs
"""

from .web_app import create_app
from .cli import cli

__all__ = ["create_app", "cli"]
