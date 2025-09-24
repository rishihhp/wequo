#!/usr/bin/env python3
"""
Workflow management CLI for WeQuo.

Provides command-line interface for managing content workflows,
version control, approvals, and editorial notes.
"""

import argparse
import json
from pathlib import Path
from datetime import datetime
import sys
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from wequo.workflows.manager import WorkflowManager
from wequo.workflows.version_control import VersionStatus
from wequo.workflows.approval import ApprovalLevel, ApprovalStatus
from wequo.workflows.editorial import NoteType, NoteStatus


def main():
    parser = argparse.ArgumentParser(description="WeQuo Workflow Manager")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Version control commands
    version_parser = subparsers.add_parser("version", help="Version control operations")
    version_subparsers = version_parser.add_subparsers(dest="version_action")
    
    # Create version
    create_version_parser = version_subparsers.add_parser("create", help="Create a new version")
    create_version_parser.add_argument("--date", required=True, help="Date (YYYY-MM-DD)")
    create_version_parser.add_argument("--author", required=True, help="Author name")
    create_version_parser.add_argument("--message", required=True, help="Commit message")
    create_version_parser.add_argument("--files", nargs="+", required=True, help="Files to version")
    
    # List versions
    version_subparsers.add_parser("list", help="List versions")
    
    # Get version info
    version_info_parser = version_subparsers.add_parser("info", help="Get version information")
    version_info_parser.add_argument("--version-id", required=True, help="Version ID")
    
    # Restore version
    restore_parser = version_subparsers.add_parser("restore", help="Restore a version")
    restore_parser.add_argument("--version-id", required=True, help="Version ID")
    restore_parser.add_argument("--target", required=True, help="Target directory")
    
    # Approval workflow commands
    approval_parser = subparsers.add_parser("approval", help="Approval workflow operations")
    approval_subparsers = approval_parser.add_subparsers(dest="approval_action")
    
    # Create approval request
    create_approval_parser = approval_subparsers.add_parser("create", help="Create approval request")
    create_approval_parser.add_argument("--version-id", required=True, help="Version ID")
    create_approval_parser.add_argument("--author", required=True, help="Author name")
    create_approval_parser.add_argument("--title", required=True, help="Request title")
    create_approval_parser.add_argument("--description", required=True, help="Request description")
    create_approval_parser.add_argument("--level", choices=["editor", "senior_editor", "managing_editor", "executive"], 
                                       default="editor", help="Required approval level")
    
    # List approval requests
    approval_subparsers.add_parser("list", help="List approval requests")
    
    # Approve request
    approve_parser = approval_subparsers.add_parser("approve", help="Approve a request")
    approve_parser.add_argument("--request-id", required=True, help="Request ID")
    approve_parser.add_argument("--reviewer", required=True, help="Reviewer ID")
    approve_parser.add_argument("--comment", help="Approval comment")
    
    # Reject request
    reject_parser = approval_subparsers.add_parser("reject", help="Reject a request")
    reject_parser.add_argument("--request-id", required=True, help="Request ID")
    reject_parser.add_argument("--reviewer", required=True, help="Reviewer ID")
    reject_parser.add_argument("--reason", required=True, help="Rejection reason")
    
    # Editorial notes commands
    notes_parser = subparsers.add_parser("notes", help="Editorial notes operations")
    notes_subparsers = notes_parser.add_subparsers(dest="notes_action")
    
    # Create note
    create_note_parser = notes_subparsers.add_parser("create", help="Create editorial note")
    create_note_parser.add_argument("--version-id", required=True, help="Version ID")
    create_note_parser.add_argument("--author", required=True, help="Author name")
    create_note_parser.add_argument("--type", choices=["comment", "suggestion", "question", "critical", "praise", "technical", "style", "fact_check"],
                                   default="comment", help="Note type")
    create_note_parser.add_argument("--title", required=True, help="Note title")
    create_note_parser.add_argument("--content", required=True, help="Note content")
    create_note_parser.add_argument("--section", help="Target section")
    create_note_parser.add_argument("--line", type=int, help="Target line number")
    create_note_parser.add_argument("--priority", type=int, choices=[1, 2, 3, 4], default=1, help="Priority level")
    
    # List notes
    list_notes_parser = notes_subparsers.add_parser("list", help="List editorial notes")
    list_notes_parser.add_argument("--version-id", help="Filter by version ID")
    list_notes_parser.add_argument("--author", help="Filter by author")
    list_notes_parser.add_argument("--status", choices=["open", "resolved", "dismissed"], help="Filter by status")
    
    # Resolve note
    resolve_parser = notes_subparsers.add_parser("resolve", help="Resolve a note")
    resolve_parser.add_argument("--note-id", required=True, help="Note ID")
    resolve_parser.add_argument("--resolver", required=True, help="Resolver name")
    resolve_parser.add_argument("--comment", help="Resolution comment")
    
    # Workflow commands
    workflow_parser = subparsers.add_parser("workflow", help="Workflow management")
    workflow_subparsers = workflow_parser.add_subparsers(dest="workflow_action")
    
    # Create workflow
    create_workflow_parser = workflow_subparsers.add_parser("create", help="Create complete workflow")
    create_workflow_parser.add_argument("--date", required=True, help="Date (YYYY-MM-DD)")
    create_workflow_parser.add_argument("--author", required=True, help="Author name")
    create_workflow_parser.add_argument("--message", required=True, help="Initial message")
    create_workflow_parser.add_argument("--files", nargs="+", required=True, help="Files to version")
    create_workflow_parser.add_argument("--level", choices=["editor", "senior_editor", "managing_editor", "executive"],
                                       default="editor", help="Required approval level")
    
    # Get workflow status
    status_parser = workflow_subparsers.add_parser("status", help="Get workflow status")
    status_parser.add_argument("--version-id", required=True, help="Version ID")
    
    # Get dashboard
    dashboard_parser = workflow_subparsers.add_parser("dashboard", help="Get dashboard data")
    dashboard_parser.add_argument("--user", required=True, help="User name")
    dashboard_parser.add_argument("--type", choices=["author", "reviewer"], required=True, help="Dashboard type")
    
    # Export report
    export_parser = workflow_subparsers.add_parser("export", help="Export workflow report")
    export_parser.add_argument("--version-id", required=True, help="Version ID")
    export_parser.add_argument("--output", help="Output file (default: stdout)")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize workflow manager
    base_path = Path("data/output")
    workflow_manager = WorkflowManager(base_path)
    
    try:
        if args.command == "version":
            handle_version_commands(workflow_manager, args)
        elif args.command == "approval":
            handle_approval_commands(workflow_manager, args)
        elif args.command == "notes":
            handle_notes_commands(workflow_manager, args)
        elif args.command == "workflow":
            handle_workflow_commands(workflow_manager, args)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def handle_version_commands(workflow_manager, args):
    """Handle version control commands."""
    if args.version_action == "create":
        # Convert file paths
        files = [Path(f) for f in args.files]
        
        version_id = workflow_manager.version_manager.create_version(
            date=args.date,
            author=args.author,
            message=args.message,
            source_files=files
        )
        
        print(f"Created version: {version_id}")
    
    elif args.version_action == "list":
        versions = workflow_manager.version_manager.versions
        if not versions:
            print("No versions found.")
            return
        
        for date, version_list in versions.items():
            print(f"\nDate: {date}")
            for version in sorted(version_list, key=lambda v: v.created_at, reverse=True):
                print(f"  {version.version_id} - {version.author} - {version.status.value} - {version.message}")
    
    elif args.version_action == "info":
        version_info = workflow_manager.version_manager.get_version_by_id(args.version_id)
        if not version_info:
            print(f"Version {args.version_id} not found.")
            return
        
        print(f"Version ID: {version_info.version_id}")
        print(f"Date: {version_info.date}")
        print(f"Author: {version_info.author}")
        print(f"Status: {version_info.status.value}")
        print(f"Message: {version_info.message}")
        print(f"Created: {version_info.created_at}")
        print(f"File Size: {version_info.file_size} bytes")
    
    elif args.version_action == "restore":
        target_path = Path(args.target)
        success = workflow_manager.version_manager.restore_version(args.version_id, target_path)
        if success:
            print(f"Version {args.version_id} restored to {target_path}")
        else:
            print(f"Failed to restore version {args.version_id}")


def handle_approval_commands(workflow_manager, args):
    """Handle approval workflow commands."""
    if args.approval_action == "create":
        level_map = {
            "editor": ApprovalLevel.EDITOR,
            "senior_editor": ApprovalLevel.SENIOR_EDITOR,
            "managing_editor": ApprovalLevel.MANAGING_EDITOR,
            "executive": ApprovalLevel.EXECUTIVE
        }
        
        request_id = workflow_manager.approval_workflow.create_approval_request(
            version_id=args.version_id,
            author=args.author,
            title=args.title,
            description=args.description,
            required_level=level_map[args.level]
        )
        
        print(f"Created approval request: {request_id}")
    
    elif args.approval_action == "list":
        requests = workflow_manager.approval_workflow.requests
        if not requests:
            print("No approval requests found.")
            return
        
        for request_id, request in requests.items():
            print(f"{request_id} - {request.author} - {request.status.value} - {request.title}")
    
    elif args.approval_action == "approve":
        success = workflow_manager.approval_workflow.approve_request(
            args.request_id, args.reviewer, args.comment or ""
        )
        if success:
            print(f"Request {args.request_id} approved by {args.reviewer}")
        else:
            print(f"Failed to approve request {args.request_id}")
    
    elif args.approval_action == "reject":
        success = workflow_manager.approval_workflow.reject_request(
            args.request_id, args.reviewer, args.reason
        )
        if success:
            print(f"Request {args.request_id} rejected by {args.reviewer}")
        else:
            print(f"Failed to reject request {args.request_id}")


def handle_notes_commands(workflow_manager, args):
    """Handle editorial notes commands."""
    if args.notes_action == "create":
        type_map = {
            "comment": NoteType.COMMENT,
            "suggestion": NoteType.SUGGESTION,
            "question": NoteType.QUESTION,
            "critical": NoteType.CRITICAL,
            "praise": NoteType.PRAISE,
            "technical": NoteType.TECHNICAL,
            "style": NoteType.STYLE,
            "fact_check": NoteType.FACT_CHECK
        }
        
        note_id = workflow_manager.editorial_notes.create_note(
            version_id=args.version_id,
            author=args.author,
            note_type=type_map[args.type],
            title=args.title,
            content=args.content,
            target_section=args.section,
            target_line=args.line,
            priority=args.priority
        )
        
        print(f"Created note: {note_id}")
    
    elif args.notes_action == "list":
        notes = workflow_manager.editorial_notes.notes
        
        # Apply filters
        if args.version_id:
            notes = {k: v for k, v in notes.items() if v.version_id == args.version_id}
        if args.author:
            notes = {k: v for k, v in notes.items() if v.author == args.author}
        if args.status:
            status_map = {"open": NoteStatus.OPEN, "resolved": NoteStatus.RESOLVED, "dismissed": NoteStatus.DISMISSED}
            notes = {k: v for k, v in notes.items() if v.status == status_map[args.status]}
        
        if not notes:
            print("No notes found.")
            return
        
        for note_id, note in notes.items():
            print(f"{note_id} - {note.author} - {note.note_type.value} - {note.status.value} - {note.title}")
    
    elif args.notes_action == "resolve":
        success = workflow_manager.editorial_notes.resolve_note(
            args.note_id, args.resolver, args.comment or ""
        )
        if success:
            print(f"Note {args.note_id} resolved by {args.resolver}")
        else:
            print(f"Failed to resolve note {args.note_id}")


def handle_workflow_commands(workflow_manager, args):
    """Handle workflow management commands."""
    if args.workflow_action == "create":
        # Convert file paths
        files = [Path(f) for f in args.files]
        
        level_map = {
            "editor": ApprovalLevel.EDITOR,
            "senior_editor": ApprovalLevel.SENIOR_EDITOR,
            "managing_editor": ApprovalLevel.MANAGING_EDITOR,
            "executive": ApprovalLevel.EXECUTIVE
        }
        
        result = workflow_manager.create_content_workflow(
            date=args.date,
            author=args.author,
            message=args.message,
            source_files=files,
            required_approval_level=level_map[args.level]
        )
        
        print(f"Created workflow:")
        print(f"  Version ID: {result['version_id']}")
        print(f"  Approval Request ID: {result['approval_request_id']}")
        print(f"  Status: {result['workflow_status']}")
    
    elif args.workflow_action == "status":
        status = workflow_manager.get_workflow_status(args.version_id)
        if "error" in status:
            print(f"Error: {status['error']}")
            return
        
        print(f"Workflow Status for {args.version_id}:")
        print(f"  Version Status: {status['version']['status']}")
        print(f"  Approval Status: {status['approval']['status']}")
        print(f"  Editorial Notes: {status['editorial']['total_notes']} total, {status['editorial']['open_notes']} open")
        print(f"  Overall Status: {status['workflow_status']}")
    
    elif args.workflow_action == "dashboard":
        if args.type == "author":
            dashboard = workflow_manager.get_author_dashboard(args.user)
        else:
            dashboard = workflow_manager.get_reviewer_dashboard(args.user)
        
        print(json.dumps(dashboard, indent=2, default=str))
    
    elif args.workflow_action == "export":
        report = workflow_manager.export_workflow_report(args.version_id)
        if "error" in report:
            print(f"Error: {report['error']}")
            return
        
        output = json.dumps(report, indent=2, default=str)
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(output)
            print(f"Report exported to {args.output}")
        else:
            print(output)


if __name__ == "__main__":
    main()
