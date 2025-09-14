#!/usr/bin/env python3
"""
WeQuo Main Application Entry Point for Render Deployment
Combines both authoring and monitoring dashboards into a single Flask app
"""

import os
import sys
from pathlib import Path
from flask import Flask, render_template_string, redirect, url_for, jsonify, render_template, request, send_file

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from wequo.monitoring.core import MonitoringEngine
from wequo.monitoring.alerts import AlertManager
from wequo.monitoring.sla import SLATracker
from wequo.monitoring.dashboard import MonitoringDashboard
from wequo.authoring.api import add_authoring_routes
from wequo.export import BriefExporter, ExportFormat
import yaml
from dotenv import load_dotenv
import json
from datetime import datetime

# Load environment variables
load_dotenv()

def create_main_app():
    """Create the main Flask application combining all services."""
    # Set template directory to the correct path
    template_dir = Path(__file__).parent / "templates"
    app = Flask(__name__, template_folder=str(template_dir))
    app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")
    
    # Load configuration
    config_path = Path(__file__).parent / "src" / "wequo" / "config.yml"
    with open(config_path, "r") as fh:
        cfg = yaml.safe_load(fh)
    
    # Set up data directories
    output_root = Path(cfg["run"]["output_root"]).resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    data_root = Path(__file__).parent / "data"
    
    # Configuration
    app.config["OUTPUT_ROOT"] = output_root
    app.config["TEMPLATE_PATH"] = Path(__file__).parent / "docs" / "template.md"
    
    # Initialize exporter
    brief_exporter = BriefExporter(output_root=output_root)
    
    # Initialize monitoring components
    monitoring_config = cfg.get("monitoring", {})
    monitoring_engine = MonitoringEngine(monitoring_config, output_root)
    alert_manager = AlertManager(monitoring_config, monitoring_engine.monitoring_dir)
    sla_tracker = SLATracker(monitoring_engine, monitoring_config)
    
    # Create monitoring dashboard and register its routes
    monitoring_dashboard = MonitoringDashboard(
        monitoring_engine, 
        alert_manager, 
        sla_tracker, 
        output_root
    )
    
    # Register all monitoring routes directly with main app
    # Copy all routes from monitoring dashboard
    for rule in monitoring_dashboard.app.url_map.iter_rules():
        endpoint = rule.endpoint
        view_func = monitoring_dashboard.app.view_functions[endpoint]
        methods = rule.methods or ['GET']
        
        # Add monitoring prefix to routes
        if rule.rule == '/':
            monitoring_route = '/monitoring/'
        else:
            monitoring_route = f'/monitoring{rule.rule}'
            
        app.add_url_rule(monitoring_route, f'monitoring_{endpoint}', view_func, methods=methods)
    
    # Initialize authoring system and register routes  
    from wequo.authoring.version_control import VersionController
    vc = VersionController(str(data_root))
    add_authoring_routes(app, str(data_root))
    
    # Add authoring dashboard route (override the one from add_authoring_routes)
    @app.route('/authoring')
    @app.route('/authoring/')
    def authoring_dashboard():
        """Authoring dashboard page."""
        # Get available packages for Document Authoring Center
        packages = []
        try:
            for date_dir in sorted(output_root.glob("????-??-??"), reverse=True):
                date_str = date_dir.name
                template_file = date_dir / "template_prefilled.md"
                package_summary = date_dir / "package_summary.json"
                
                if template_file.exists():
                    try:
                        package_info = {}
                        if package_summary.exists():
                            with open(package_summary, 'r', encoding='utf-8') as f:
                                package_info = json.load(f)
                        
                        packages.append({
                            'date': date_str,
                            'title': f"Weekly Brief - {date_str}",
                            'sources': package_info.get('sources', []),
                            'edit_url': f'/template/{date_str}'
                        })
                    except Exception:
                        continue
        except Exception as e:
            print(f"Error loading packages: {e}")
        
        # Get user-edited documents from version control
        my_documents = []
        try:
            docs = vc.list_documents()
            for doc in docs:
                current_version = doc.get_current_version()
                my_documents.append({
                    'id': doc.id,
                    'title': doc.title,
                    'date': doc.package_date,
                    'status': current_version.state.value if current_version else 'draft',
                    'last_modified': current_version.timestamp.isoformat() if current_version else None,
                    'edit_url': f'/authoring/document/{doc.id}'
                })
        except Exception as e:
            print(f"Error loading documents: {e}")
        
        return render_template("authoring_dashboard.html", 
                             packages=packages, 
                             my_documents=my_documents)
    
    # Add main authoring web app routes (index is handled by main_index route below)
    
    @app.route("/package/<date>")
    def view_package(date: str):
        """View a specific data package."""
        package_dir = output_root / date
        
        if not package_dir.exists():
            return f"Package for {date} not found", 404
        
        # Load package data
        package_data = load_package_data(package_dir)
        return render_template("package.html", date=date, data=package_data)
    
    @app.route("/package/<date>/provenance")
    def view_provenance(date: str):
        """View provenance information for a data package."""
        package_dir = output_root / date
        
        if not package_dir.exists():
            return f"Package for {date} not found", 404
        
        # Load package summary with provenance
        summary_file = package_dir / "package_summary.json"
        if not summary_file.exists():
            return f"Package summary not found for {date}", 404
        
        with open(summary_file) as f:
            package_data = json.load(f)
        
        provenance_data = package_data.get("provenance", {})
        return render_template("provenance.html", date=date, provenance=provenance_data)
    
    @app.route("/api/package/<date>/provenance")
    def api_provenance(date: str):
        """API endpoint for provenance data."""
        package_dir = output_root / date
        summary_file = package_dir / "package_summary.json"
        
        if not summary_file.exists():
            return jsonify({"error": "Package not found"}), 404
        
        with open(summary_file) as f:
            package_data = json.load(f)
        
        return jsonify(package_data.get("provenance", {}))
    
    @app.route("/template/<date>")
    def generate_template(date: str):
        """Generate a pre-filled template for a specific date."""
        package_dir = output_root / date
        
        if not package_dir.exists():
            return f"Package for {date} not found", 404
        
        # Load package data
        package_data = load_package_data(package_dir)
        
        # Load prefill notes
        prefill_notes = ""
        prefill_notes_path = package_dir / "prefill_notes.md"
        if prefill_notes_path.exists():
            prefill_notes = prefill_notes_path.read_text(encoding='utf-8')
        
        # Generate pre-filled template
        template_content = generate_prefilled_template(package_data, date)
        
        # Save to temporary file for download option
        temp_path = package_dir / "template_prefilled.md"
        temp_path.write_text(template_content, encoding='utf-8')
        
        # Check if document exists in authoring system
        try:
            document = vc.get_document_by_date(date)
            if document:
                current_version = document.get_current_version()
                if current_version:
                    template_content = current_version.content
        except Exception as e:
            print(f"Error getting document: {e}")
            document = None
        
        # Render template content in web interface
        return render_template('template.html', 
                             date=date, 
                             template_content=template_content,
                             package_data=package_data,
                             prefill_notes=prefill_notes,
                             document_id=document.id if document else None)
    
    @app.route("/api/packages")
    def api_packages():
        """API endpoint to get available packages."""
        packages = get_available_packages(output_root)
        return jsonify(packages)
    
    @app.route("/api/package/<date>/summary")
    def api_package_summary(date: str):
        """API endpoint to get package summary."""
        package_dir = output_root / date
        
        if not package_dir.exists():
            return jsonify({"error": "Package not found"}), 404
        
        summary_path = package_dir / "package_summary.json"
        if summary_path.exists():
            return jsonify(json.loads(summary_path.read_text()))
        else:
            return jsonify({"error": "Summary not found"}), 404
    
    @app.route("/api/template/<date>/save", methods=['POST'])
    def save_template_edit(date: str):
        """Save template edit as a new version."""
        try:
            data = request.get_json()
            content = data.get('content', '')
            author = data.get('author', 'unknown')
            commit_message = data.get('commit_message', 'Updated via template editor')
            
            if not content:
                return jsonify({"error": "No content provided"}), 400
            
            # Check if document exists
            document = vc.get_document_by_date(date)
            
            if not document:
                # Create new document
                title = f"Weekly Brief - {date}"
                document = vc.create_document(
                    title=title,
                    package_date=date,
                    author=author,
                    initial_content=content,
                    reviewers=[]
                )
            else:
                # Update existing document
                vc.update_document(
                    document=document,
                    content=content,
                    author=author,
                    commit_message=commit_message
                )
            
            return jsonify({
                "success": True,
                "document_id": document.id,
                "version_id": document.current_version,
                "message": "Template saved successfully"
            })
            
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    # Add pipeline execution API endpoints
    pipeline_status = {
        "running": False,
        "start_time": None,
        "end_time": None,
        "success": None,
        "message": "",
        "output": "",
        "error": ""
    }
    
    @app.route("/api/run-pipeline", methods=['POST'])
    def run_pipeline():
        """Execute the run_weekly.py script to fetch new data."""
        import subprocess
        import threading
        import time
        
        nonlocal pipeline_status
        
        # Check if pipeline is already running
        if pipeline_status["running"]:
            return jsonify({
                "success": False,
                "error": "Pipeline is already running"
            }), 409
        
        try:
            # Get the project root directory (wequo folder)
            project_root = Path(__file__).parent
            script_path = project_root / "scripts" / "run_weekly.py"
            
            if not script_path.exists():
                return jsonify({
                    "success": False,
                    "error": f"Script not found at {script_path}"
                }), 404
            
            # Update status to running
            pipeline_status.update({
                "running": True,
                "start_time": time.time(),
                "end_time": None,
                "success": None,
                "message": "Pipeline execution started",
                "output": "",
                "error": ""
            })
            
            # Run the script in a separate thread to avoid blocking the web app
            def run_script():
                nonlocal pipeline_status
                try:
                    # Change to the project root directory and run the script
                    result = subprocess.run(
                        ["python", str(script_path)],
                        cwd=str(project_root),
                        capture_output=True,
                        text=True,
                        timeout=300  # 5 minute timeout
                    )
                    
                    # Update status with results
                    pipeline_status.update({
                        "running": False,
                        "end_time": time.time(),
                        "success": result.returncode == 0,
                        "message": "Pipeline execution completed" if result.returncode == 0 else "Pipeline execution failed",
                        "output": result.stdout,
                        "error": result.stderr if result.returncode != 0 else ""
                    })
                    
                except subprocess.TimeoutExpired:
                    pipeline_status.update({
                        "running": False,
                        "end_time": time.time(),
                        "success": False,
                        "message": "Pipeline execution timed out",
                        "error": "Script execution exceeded 5 minute timeout"
                    })
                except Exception as e:
                    pipeline_status.update({
                        "running": False,
                        "end_time": time.time(),
                        "success": False,
                        "message": "Pipeline execution failed",
                        "error": str(e)
                    })
            
            # Start the thread
            thread = threading.Thread(target=run_script)
            thread.start()
            
            return jsonify({
                "success": True,
                "message": "Pipeline execution started",
                "status": pipeline_status
            })
            
        except Exception as e:
            pipeline_status.update({
                "running": False,
                "end_time": time.time(),
                "success": False,
                "message": "Failed to start pipeline",
                "error": str(e)
            })
            
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    @app.route("/api/pipeline-status")
    def api_pipeline_status():
        """API endpoint for pipeline status (used by authoring dashboard)."""
        import time
        
        nonlocal pipeline_status
        
        # Calculate duration if running
        duration = None
        if pipeline_status["running"] and pipeline_status["start_time"]:
            duration = time.time() - pipeline_status["start_time"]
        elif pipeline_status["end_time"] and pipeline_status["start_time"]:
            duration = pipeline_status["end_time"] - pipeline_status["start_time"]
        
        return jsonify({
            "running": pipeline_status["running"],
            "success": pipeline_status["success"],
            "message": pipeline_status["message"],
            "duration": duration,
            "start_time": pipeline_status["start_time"],
            "end_time": pipeline_status["end_time"],
            "output": pipeline_status["output"][-500:] if pipeline_status["output"] else "",  # Last 500 chars
            "error": pipeline_status["error"]
        })
    
    @app.route("/api/pipeline-status-legacy")
    def api_pipeline_status_legacy():
        """Legacy API endpoint for pipeline status (used by authoring dashboard)."""
        # Get the latest pipeline run status
        try:
            monitoring_dir = output_root.parent / "monitoring"
            history_file = monitoring_dir / "pipeline_history.jsonl"
            
            if history_file.exists():
                # Read last line of JSONL file
                with open(history_file, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        last_run = json.loads(lines[-1].strip())
                        return jsonify({
                            "status": "success",
                            "data": last_run
                        })
            
            return jsonify({
                "status": "success", 
                "data": {
                    "running": False,
                    "last_run": None,
                    "message": "No pipeline runs found"
                }
            })
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500
    
    # Main landing page
    @app.route('/')
    def main_index():
        packages = get_available_packages(output_root)
        return render_template("index.html", packages=packages)
    
    # Export endpoint (global, not prefixed)
    @app.route('/export/<date>/<format>')
    def export_brief(date: str, format: str):
        """Export a brief in the specified format."""
        print(f"Export route called: date={date}, format={format}")
        
        package_dir = output_root / date
        print(f"Package directory: {package_dir}")
        
        if not package_dir.exists():
            print(f"Package directory not found: {package_dir}")
            return jsonify({"error": "Package not found"}), 404
        
        try:
            # Load package data
            print("Loading package data...")
            package_data = load_package_data(package_dir)
            print(f"Package data loaded: {len(package_data)} top-level keys")
            
            # Determine export format
            if format.lower() == 'html':
                export_format = ExportFormat.HTML
            elif format.lower() == 'pdf':
                export_format = ExportFormat.PDF
            elif format.lower() in ['markdown', 'md']:
                export_format = ExportFormat.MARKDOWN
            else:
                print(f"Unsupported format: {format}")
                return jsonify({"error": "Unsupported format"}), 400
            
            print(f"Export format: {export_format}")
            
            # Export the brief
            print("Starting export...")
            output_path = brief_exporter.export_brief(
                package_data=package_data,
                package_date=date,
                format=export_format
            )
            print(f"Export completed: {output_path}")
            
            # Determine MIME type and filename
            if export_format == ExportFormat.HTML:
                mimetype = 'text/html'
                filename = f"wequo_brief_{date}.html"
            elif export_format == ExportFormat.PDF:
                mimetype = 'application/pdf'
                filename = f"wequo_brief_{date}.pdf"
            else:  # Markdown
                mimetype = 'text/markdown'
                filename = f"wequo_brief_{date}.md"
            
            print(f"Sending file: {output_path} as {filename}")
            return send_file(
                output_path,
                mimetype=mimetype,
                as_attachment=True,
                download_name=filename
            )
            
        except Exception as e:
            print(f"Export error: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500
    
    # Health check endpoint
    @app.route('/health')
    def health():
        return {"status": "healthy", "service": "wequo"}
    
    return app


def get_available_packages(output_root: Path):
    """Get list of available data packages."""
    packages = []
    try:
        for date_dir in sorted(output_root.glob("????-??-??"), reverse=True):
            date_str = date_dir.name
            summary_file = date_dir / "package_summary.json"
            
            if summary_file.exists():
                try:
                    with open(summary_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Get file count and size
                    files = list(date_dir.glob("*.csv")) + list(date_dir.glob("*.json"))
                    total_size = sum(f.stat().st_size for f in files if f.is_file())
                    
                    packages.append({
                        'date': date_str,
                        'timestamp': date_str,
                        'sources': data.get('sources', []),
                        'file_count': len(files),
                        'size_mb': round(total_size / (1024 * 1024), 2),
                        'title': f"Data Package {date_str}",
                        'description': f"Data collected on {date_str}"
                    })
                except Exception as e:
                    print(f"Error loading package {date_str}: {e}")
                    continue
    except Exception as e:
        print(f"Error scanning packages: {e}")
    
    return packages


def load_package_data(package_dir: Path):
    """Load all data files from a package directory."""
    data = {}
    
    # Load JSON files
    for json_file in package_dir.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data[json_file.stem] = json.load(f)
        except Exception as e:
            print(f"Error loading {json_file}: {e}")
    
    # Ensure summary data is available for template
    if 'package_summary' in data:
        data['summary'] = data['package_summary']
    else:
        data['summary'] = {
            'timestamp': 'Unknown',
            'sources': [],
            'file_count': 0,
            'total_size_mb': 0
        }
    
    # Load CSV file info
    csv_files = {}
    for csv_file in package_dir.glob("*.csv"):
        try:
            import pandas as pd
            df = pd.read_csv(csv_file)
            csv_files[csv_file.stem] = {
                'name': csv_file.name,
                'path': str(csv_file),
                'rows': len(df),
                'columns': list(df.columns),
                'size_mb': round(csv_file.stat().st_size / (1024 * 1024), 2),
                'data': df.to_dict(orient='records')
            }
        except Exception as e:
            print(f"Error reading CSV {csv_file}: {e}")
    
    data['csv_files'] = csv_files
    
    # Load reports (markdown files)
    reports = {}
    for md_file in package_dir.glob("*.md"):
        try:
            reports[md_file.stem] = md_file.read_text(encoding='utf-8')
        except Exception as e:
            print(f"Error reading report {md_file}: {e}")
    
    data['reports'] = reports
    
    # Ensure analytics data is available
    if 'analytics_summary' in data:
        data['analytics'] = data['analytics_summary']
    else:
        data['analytics'] = {
            'anomalies': [],
            'top_deltas': [],
            'trends': []
        }
    
    return data


def generate_prefilled_template(package_data, date):
    """Generate a pre-filled template with package data."""
    # This is a simplified version - in practice you'd load from template.md
    template = f"""# Weekly Brief - {date}

## Data Sources

"""
    
    # Add data source information
    if 'package_summary' in package_data:
        sources = package_data['package_summary'].get('sources', [])
        for source in sources:
            template += f"- **{source}**: Data collected successfully\\n"
    
    template += """

## Key Metrics

[Add your analysis here]

## Notable Events

[Add significant events and observations]

## Outlook

[Add forward-looking analysis]
"""
    
    return template

# Main landing page template
MAIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WeQuo - Global Risk & Opportunity Platform</title>
    <script src="https://unpkg.com/lucide@latest/dist/umd/lucide.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
            background: linear-gradient(135deg, #1a365d 0%, #2d3748 50%, #4a5568 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
        }
        
        .header {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 24px;
            padding: 60px 50px;
            margin: 40px 20px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
            border: 1px solid rgba(255, 255, 255, 0.2);
            text-align: center;
        }
        
        .header h1 {
            color: #2d3748;
            font-size: 3.5em;
            font-weight: 800;
            margin-bottom: 20px;
            background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .header-subtitle {
            color: #718096;
            font-size: 1.3em;
            margin-bottom: 40px;
            font-weight: 500;
        }
        
        .services-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 30px;
            margin: 40px 20px;
        }
        
        .service-card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: all 0.3s ease;
            text-align: center;
        }
        
        .service-card:hover {
            transform: translateY(-8px);
            box-shadow: 0 25px 70px rgba(0, 0, 0, 0.12);
        }
        
        .service-icon {
            width: 80px;
            height: 80px;
            margin: 0 auto 20px;
            background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%);
            border-radius: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
        }
        
        .service-title {
            color: #2d3748;
            font-size: 1.8em;
            font-weight: 700;
            margin-bottom: 15px;
        }
        
        .service-description {
            color: #718096;
            font-size: 1.1em;
            margin-bottom: 25px;
            line-height: 1.6;
        }
        
        .service-btn {
            display: inline-block;
            background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%);
            color: white;
            padding: 15px 30px;
            border-radius: 12px;
            text-decoration: none;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 4px 16px rgba(45, 55, 72, 0.3);
        }
        
        .service-btn:hover {
            background: linear-gradient(135deg, #1a202c 0%, #2d3748 100%);
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(45, 55, 72, 0.4);
            color: white;
            text-decoration: none;
        }
        
        .features {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 40px;
            margin: 40px 20px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.08);
        }
        
        .features h2 {
            color: #2d3748;
            font-size: 2.2em;
            font-weight: 700;
            margin-bottom: 30px;
            text-align: center;
        }
        
        .features-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
        }
        
        .feature-item {
            display: flex;
            align-items: center;
            gap: 15px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 12px;
        }
        
        .feature-icon {
            width: 24px;
            height: 24px;
            color: #2d3748;
        }
        
        .footer {
            text-align: center;
            padding: 40px 20px;
            color: rgba(255, 255, 255, 0.8);
        }
        
        @media (max-width: 768px) {
            .header h1 {
                font-size: 2.5em;
            }
            
            .services-grid {
                grid-template-columns: 1fr;
                margin: 20px 10px;
            }
            
            .service-card {
                padding: 30px 20px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>
                <i data-lucide="globe"></i>
                WeQuo
            </h1>
            <div class="header-subtitle">
                Global Risk & Opportunity Intelligence Platform
            </div>
        </div>
        
        <div class="services-grid">
            <div class="service-card">
                <div class="service-icon">
                    <i data-lucide="edit-3"></i>
                </div>
                <h3 class="service-title">Authoring Dashboard</h3>
                <p class="service-description">
                    Create and manage weekly briefs with version control, 
                    collaboration tools, and automated data integration.
                </p>
                <a href="/authoring" class="service-btn">
                    <i data-lucide="arrow-right"></i>
                    Open Authoring
                </a>
            </div>
            
            <div class="service-card">
                <div class="service-icon">
                    <i data-lucide="activity"></i>
                </div>
                <h3 class="service-title">Monitoring Dashboard</h3>
                <p class="service-description">
                    Monitor pipeline health, SLA compliance, system alerts, 
                    and search through data packages and analytics.
                </p>
                <a href="/monitoring" class="service-btn">
                    <i data-lucide="arrow-right"></i>
                    Open Monitoring
                </a>
            </div>
        </div>
        
        <div class="features">
            <h2>Platform Features</h2>
            <div class="features-grid">
                <div class="feature-item">
                    <i data-lucide="database" class="feature-icon"></i>
                    <span>Multi-source Data Collection</span>
                </div>
                <div class="feature-item">
                    <i data-lucide="trending-up" class="feature-icon"></i>
                    <span>Advanced Analytics & Anomaly Detection</span>
                </div>
                <div class="feature-item">
                    <i data-lucide="git-branch" class="feature-icon"></i>
                    <span>Version Control & Collaboration</span>
                </div>
                <div class="feature-item">
                    <i data-lucide="shield-check" class="feature-icon"></i>
                    <span>Real-time Monitoring & Alerts</span>
                </div>
                <div class="feature-item">
                    <i data-lucide="search" class="feature-icon"></i>
                    <span>Data Search & Export</span>
                </div>
                <div class="feature-item">
                    <i data-lucide="file-text" class="feature-icon"></i>
                    <span>Automated Report Generation</span>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>WeQuo - Comprehensive data pipeline and authoring system</p>
        </div>
    </div>
    
    <script>
        lucide.createIcons();
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    app = create_main_app()
    
    # Get configuration from environment
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("DEBUG", "false").lower() == "true"
    
    print(f"🚀 Starting WeQuo Platform")
    print(f"📊 Authoring Dashboard: http://{host}:{port}/authoring")
    print(f"📈 Monitoring Dashboard: http://{host}:{port}/monitoring")
    print(f"🔧 Debug mode: {debug}")
    
    app.run(host=host, port=port, debug=debug)
