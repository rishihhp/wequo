"""
API endpoints for the authoring version control system.
"""

from flask import Blueprint, request, jsonify, current_app
from typing import Dict, Any, List, Optional
from pathlib import Path
import os
import glob
import json
from datetime import datetime

from .version_control import VersionController
# Simplified authoring - no complex workflow needed
from .models import DocumentState, ApprovalStatus


def create_authoring_api(version_controller: VersionController) -> Blueprint:
    """Create Flask API blueprint for authoring system."""
    
    api = Blueprint('authoring_api', __name__, url_prefix='/api/authoring')
    
    @api.route('/templates', methods=['GET'])
    def list_package_templates():
        """List all package templates from output directories."""
        try:
            templates = []
            output_dir = Path("wequo/data/output")
            
            # Find all date directories
            for date_dir in sorted(output_dir.glob("????-??-??"), reverse=True):
                date_str = date_dir.name
                template_file = date_dir / "template_prefilled.md"
                package_summary = date_dir / "package_summary.json"
                
                # Check if template exists
                if template_file.exists():
                    try:
                        # Get package info
                        package_info = {}
                        if package_summary.exists():
                            with open(package_summary, 'r', encoding='utf-8') as f:
                                package_info = json.load(f)
                        
                        # Get file stats
                        stat = template_file.stat()
                        
                        templates.append({
                            'id': f"template_{date_str}",
                            'title': f"Weekly Brief - {date_str}",
                            'package_date': date_str,
                            'author': "system",
                            'created_at': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                            'updated_at': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            'type': 'template',
                            'current_version_info': {
                                'id': f"template_{date_str}_v1",
                                'version_number': "1.0",
                                'author': "system",
                                'timestamp': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                                'state': 'published'
                            },
                            'approval_status': {
                                'approved': 1,
                                'required': 1,
                                'status': 'approved'
                            },
                            'sources': package_info.get('sources', []),
                            'data_count': len(package_info.get('latest_values', {}).get('fred', [])) if package_info else 0
                        })
                    except Exception as e:
                        print(f"Error processing template {date_str}: {e}")
                        continue
            
            return jsonify(templates)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @api.route('/my-documents', methods=['GET'])
    def list_my_documents():
        """List user-edited documents from authoring workspace."""
        try:
            documents = version_controller.list_documents()
            
            result = []
            for doc in documents:
                current_version = doc.get_current_version()
                approval_status = doc.get_approvals_status()
                
                result.append({
                    'id': doc.id,
                    'title': doc.title,
                    'package_date': doc.package_date,
                    'author': doc.author,
                    'created_at': doc.created_at.isoformat(),
                    'updated_at': doc.updated_at.isoformat(),
                    'reviewers': doc.reviewers,
                    'type': 'document',
                    'current_version': doc.current_version,
                    'current_version_info': {
                        'id': current_version.id,
                        'version_number': current_version.version_number,
                        'author': current_version.author,
                        'timestamp': current_version.timestamp.isoformat(),
                        'state': current_version.state.value
                    } if current_version else None,
                    'approval_status': approval_status,
                    'version_count': len(doc.versions)
                })
            
            return jsonify(result)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @api.route('/documents', methods=['GET'])
    def list_documents():
        """List all documents with their current status (deprecated - use /templates and /my-documents)."""
        try:
            documents = version_controller.list_documents()
            
            result = []
            for doc in documents:
                current_version = doc.get_current_version()
                approval_status = doc.get_approvals_status()
                
                # Get version history for display
                version_history = doc.get_version_history()
                
                result.append({
                    'id': doc.id,
                    'title': doc.title,
                    'package_date': doc.package_date,
                    'author': doc.author,
                    'created_at': doc.created_at.isoformat(),
                    'updated_at': doc.updated_at.isoformat(),
                    'reviewers': doc.reviewers,
                    'current_version': doc.current_version,
                    'current_version_info': {
                        'id': current_version.id,
                        'version_number': current_version.version_number,
                        'author': current_version.author,
                        'timestamp': current_version.timestamp.isoformat(),
                        'state': current_version.state.value
                    } if current_version else None,
                    'approval_status': approval_status,
                    'version_count': len(doc.versions),
                    'versions': [
                        {
                            'id': v.id,
                            'version_number': v.version_number,
                            'author': v.author,
                            'timestamp': v.timestamp.isoformat(),
                            'state': v.state.value
                        } for v in version_history
                    ]
                })
            
            return jsonify(result)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # Simplified document creation - not needed for template editing workflow
    
    @api.route('/documents/<document_id>', methods=['GET'])
    def get_document(document_id: str):
        """Get a specific document with all versions."""
        try:
            document = version_controller.get_document(document_id)
            
            if not document:
                return jsonify({'error': 'Document not found'}), 404
            
            return jsonify({
                'id': document.id,
                'title': document.title,
                'package_date': document.package_date,
                'author': document.author,
                'reviewers': document.reviewers,
                'created_at': document.created_at.isoformat(),
                'updated_at': document.updated_at.isoformat(),
                'current_version': document.current_version,
                'file_path': document.file_path,
                'versions': {k: v.to_dict() for k, v in document.versions.items()},
                'approval_status': document.get_approvals_status()
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # Simplified version creation - handled by template save endpoint
    
    # Complex workflow removed - templates are saved directly
    
    # Review workflow removed - focus on template editing only
    
    # Publishing workflow removed
    
    @api.route('/documents/<document_id>/revert', methods=['POST'])
    def revert_document(document_id: str):
        """Revert document to a specific version."""
        try:
            data = request.get_json()
            
            version_id = data.get('version_id', '')
            author = data.get('author', '')
            
            if not all([version_id, author]):
                return jsonify({'error': 'Missing required fields'}), 400
            
            document = version_controller.get_document(document_id)
            if not document:
                return jsonify({'error': 'Document not found'}), 404
            
            reverted_version = version_controller.revert_to_version(
                document=document,
                version_id=version_id,
                author=author
            )
            
            return jsonify({
                'id': reverted_version.id,
                'version_number': reverted_version.version_number,
                'author': reverted_version.author,
                'timestamp': reverted_version.timestamp.isoformat()
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @api.route('/documents/<document_id>/history', methods=['GET'])
    def get_version_history(document_id: str):
        """Get version history for a document."""
        try:
            
            document = version_controller.get_document(document_id)
            if not document:
                return jsonify({'error': 'Document not found'}), 404
            
            history = document.get_version_history()
            
            result = []
            for version in history:
                result.append({
                    'id': version.id,
                    'version_number': version.version_number,
                    'author': version.author,
                    'timestamp': version.timestamp.isoformat(),
                    'state': version.state.value,
                    'parent_version': version.parent_version,
                    'tags': version.tags,
                    'comment_count': len(version.comments),
                    'approval_count': len(version.approvals)
                })
            
            return jsonify(result)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @api.route('/documents/<document_id>/versions/<version_id>', methods=['GET'])
    def get_version_content(document_id: str, version_id: str):
        """Get content of a specific version."""
        try:
            document = version_controller.get_document(document_id)
            if not document:
                return jsonify({'error': 'Document not found'}), 404
            
            if version_id not in document.versions:
                return jsonify({'error': 'Version not found'}), 404
            
            version = document.versions[version_id]
            return jsonify({
                'id': version.id,
                'version_number': version.version_number,
                'author': version.author,
                'timestamp': version.timestamp.isoformat(),
                'content': version.content,
                'state': version.state.value,
                'metadata': version.metadata,
                'parent_version': version.parent_version,
                'tags': version.tags
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @api.route('/documents/<document_id>/versions/<version_id>/download', methods=['GET'])
    def download_version(document_id: str, version_id: str):
        """Download a specific version as a markdown file."""
        try:
            document = version_controller.get_document(document_id)
            if not document:
                return jsonify({'error': 'Document not found'}), 404
            
            if version_id not in document.versions:
                return jsonify({'error': 'Version not found'}), 404
            
            version = document.versions[version_id]
            
            # Create a temporary file for download
            from flask import make_response
            
            response = make_response(version.content)
            response.headers['Content-Type'] = 'text/markdown'
            response.headers['Content-Disposition'] = f'attachment; filename="{document.title.replace(" ", "_")}_v{version.version_number}.md"'
            
            return response
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @api.route('/documents/<document_id>/diff', methods=['GET'])
    def get_version_diff(document_id: str):
        """Get diff between two versions."""
        try:
            version_a = request.args.get('version_a')
            version_b = request.args.get('version_b')
            
            if not all([version_a, version_b]):
                return jsonify({'error': 'Missing version parameters'}), 400
            
            document = version_controller.get_document(document_id)
            if not document:
                return jsonify({'error': 'Document not found'}), 404
            
            diff = version_controller.get_version_diff(
                document=document,
                version_a=version_a,
                version_b=version_b
            )
            
            return jsonify(diff)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # Comments functionality removed - simplified workflow
    
    # In-review endpoint removed
    
    # Stats simplified for template editing
    @api.route('/stats', methods=['GET'])
    def get_workflow_stats():
        """Get simplified authoring statistics."""
        try:
            docs = version_controller.list_documents()
            stats = {
                'total_documents': len(docs),
                'draft': len([d for d in docs if d.get_current_version() and d.get_current_version().state == DocumentState.DRAFT]),
                'in_review': 0,  # No review workflow
                'approved': 0,   # No approval workflow
                'published': len([d for d in docs if d.get_current_version() and d.get_current_version().state == DocumentState.PUBLISHED]),
                'avg_review_time': 0  # No review workflow
            }
            return jsonify(stats)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # Activity simplified
    @api.route('/activity', methods=['GET'])
    def get_recent_activity():
        """Get recent activity."""
        try:
            docs = version_controller.list_documents()
            activity = []
            for doc in docs[:5]:  # Last 5 documents
                current_version = doc.get_current_version()
                if current_version:
                    activity.append({
                        'document_title': doc.title,
                        'version_number': current_version.version_number,
                        'author': current_version.author,
                        'state': current_version.state.value,
                        'timestamp': current_version.timestamp.isoformat()
                    })
            return jsonify(activity)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # Settings simplified
    @api.route('/settings', methods=['GET'])
    def get_settings():
        """Get authoring settings."""
        try:
            return jsonify({'authoring_mode': 'simplified', 'version_control': True})
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return api


def add_authoring_routes(app, data_root: str = "data"):
    """Add authoring routes to Flask app."""
    
    # Initialize simplified version control
    vc = VersionController(data_root)
    
    # Register API blueprint
    api = create_authoring_api(vc)
    app.register_blueprint(api)
    
    # Dashboard route is now handled in main app.py
    
    return vc, None  # No workflow in simplified authoring
