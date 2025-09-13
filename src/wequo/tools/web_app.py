from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
import pandas as pd
from wequo.search import SearchEngine, SearchQuery, DocumentType
from wequo.export import BriefExporter, ExportFormat


def create_app() -> Flask:
    """Create the WeQuo author web application."""
    # Set template directory to the correct path
    template_dir = Path(__file__).parent.parent.parent.parent / "templates"
    app = Flask(__name__, template_folder=str(template_dir))
    app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")
    
    # Configuration
    app.config["OUTPUT_ROOT"] = Path(__file__).parent.parent.parent.parent / "data" / "output"
    app.config["TEMPLATE_PATH"] = Path(__file__).parent.parent.parent.parent / "docs" / "template.md"
    
    # Initialize search engine and exporter
    search_engine = SearchEngine()
    brief_exporter = BriefExporter(output_root=app.config["OUTPUT_ROOT"])
    
    @app.route("/")
    def index():
        """Main dashboard page."""
        # Get available packages
        packages = get_available_packages()
        return render_template("index.html", packages=packages)
    
    @app.route("/package/<date>")
    def view_package(date: str):
        """View a specific data package."""
        package_dir = app.config["OUTPUT_ROOT"] / date
        
        if not package_dir.exists():
            return f"Package for {date} not found", 404
        
        # Load package data
        package_data = load_package_data(package_dir)
        return render_template("package.html", date=date, data=package_data)
    
    @app.route("/package/<date>/provenance")
    def view_provenance(date: str):
        """View provenance information for a data package."""
        package_dir = app.config["OUTPUT_ROOT"] / date
        
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
        package_dir = app.config["OUTPUT_ROOT"] / date
        summary_file = package_dir / "package_summary.json"
        
        if not summary_file.exists():
            return jsonify({"error": "Package not found"}), 404
        
        with open(summary_file) as f:
            package_data = json.load(f)
        
        return jsonify(package_data.get("provenance", {}))
    
    @app.route("/template/<date>")
    def generate_template(date: str):
        """Generate a pre-filled template for a specific date."""
        package_dir = app.config["OUTPUT_ROOT"] / date
        
        if not package_dir.exists():
            return f"Package for {date} not found", 404
        
        # Load package data
        package_data = load_package_data(package_dir)
        
        # Generate pre-filled template
        template_content = generate_prefilled_template(package_data, date)
        
        # Save to temporary file for download option
        temp_path = package_dir / "template_prefilled.md"
        temp_path.write_text(template_content, encoding='utf-8')
        
        # Render template content in web interface
        return render_template('template.html', 
                             date=date, 
                             template_content=template_content,
                             package_data=package_data)
    
    @app.route("/template/<date>/download")
    def download_template(date: str):
        """Download the pre-filled template for a specific date."""
        package_dir = app.config["OUTPUT_ROOT"] / date
        
        if not package_dir.exists():
            return f"Package for {date} not found", 404
        
        temp_path = package_dir / "template_prefilled.md"
        if not temp_path.exists():
            return f"Template not generated for {date}", 404
            
        return send_file(temp_path, as_attachment=True, 
                        download_name=f"wequo_brief_{date}.md")
    
    @app.route("/api/packages")
    def api_packages():
        """API endpoint to get available packages."""
        packages = get_available_packages()
        return jsonify(packages)
    
    @app.route("/api/package/<date>/summary")
    def api_package_summary(date: str):
        """API endpoint to get package summary."""
        package_dir = app.config["OUTPUT_ROOT"] / date
        
        if not package_dir.exists():
            return jsonify({"error": "Package not found"}), 404
        
        summary_path = package_dir / "package_summary.json"
        if summary_path.exists():
            return jsonify(json.loads(summary_path.read_text()))
        else:
            return jsonify({"error": "Summary not found"}), 404
    
    @app.route("/api/search")
    def api_search():
        """API endpoint for search."""
        query_text = request.args.get('q', '')
        doc_types = request.args.getlist('types')
        sources = request.args.getlist('sources')
        tags = request.args.getlist('tags')
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        
        # Convert document types
        document_types = []
        for dt in doc_types:
            try:
                document_types.append(DocumentType(dt))
            except ValueError:
                pass
        
        # Create search query
        query = SearchQuery(
            query=query_text,
            document_types=document_types,
            sources=sources,
            tags=tags,
            limit=limit,
            offset=offset
        )
        
        # Perform search
        results = search_engine.search(query)
        
        return jsonify({
            'query': query.to_dict(),
            'results': [result.to_dict() for result in results],
            'total': len(results)
        })
    
    @app.route("/api/search/suggestions")
    def api_search_suggestions():
        """API endpoint for search suggestions."""
        query_text = request.args.get('q', '')
        limit = int(request.args.get('limit', 5))
        
        suggestions = search_engine.get_suggestions(query_text, limit)
        return jsonify({'suggestions': suggestions})
    
    @app.route("/api/search/facets")
    def api_search_facets():
        """API endpoint for search facets."""
        facets = search_engine.get_facets()
        return jsonify({'facets': facets})
    
    @app.route("/api/search/stats")
    def api_search_stats():
        """API endpoint for search statistics."""
        stats = search_engine.get_stats()
        return jsonify(stats.to_dict())
    
    @app.route("/api/search/rebuild", methods=['POST'])
    def api_rebuild_search():
        """API endpoint to rebuild search index."""
        try:
            output_root = app.config["OUTPUT_ROOT"]
            count = search_engine.rebuild_index(output_root)
            return jsonify({
                'success': True,
                'message': f'Index rebuilt with {count} documents'
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route("/search")
    def search_page():
        """Search interface page."""
        query = request.args.get('q', '')
        results = []
        facets = {}
        
        if query:
            search_results = search_engine.search_simple(query)
            results = [result.to_dict() for result in search_results]
        
        facets = search_engine.get_facets()
        stats = search_engine.get_stats()
        
        return render_template("search.html", 
                             query=query, 
                             results=results, 
                             facets=facets,
                             stats=stats.to_dict())
    
    @app.route("/export/<date>/<format>")
    def export_brief(date: str, format: str):
        """Export a brief in the specified format."""
        package_dir = app.config["OUTPUT_ROOT"] / date
        
        if not package_dir.exists():
            return jsonify({"error": "Package not found"}), 404
        
        # Load package data
        package_data = load_package_data(package_dir)
        
        try:
            # Determine export format
            if format.lower() == 'html':
                export_format = ExportFormat.HTML
            elif format.lower() == 'pdf':
                export_format = ExportFormat.PDF
            elif format.lower() == 'markdown' or format.lower() == 'md':
                export_format = ExportFormat.MARKDOWN
            else:
                return jsonify({"error": "Unsupported format"}), 400
            
            # Export the brief
            output_path = brief_exporter.export_brief(
                package_data=package_data,
                package_date=date,
                format=export_format
            )
            
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
            
            return send_file(
                output_path,
                mimetype=mimetype,
                as_attachment=True,
                download_name=filename
            )
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/export/<date>", methods=['POST'])
    def api_export_brief(date: str):
        """API endpoint to export brief."""
        package_dir = app.config["OUTPUT_ROOT"] / date
        
        if not package_dir.exists():
            return jsonify({"error": "Package not found"}), 404
        
        # Get export parameters
        data = request.get_json() or {}
        format_str = data.get('format', 'html').lower()
        template_name = data.get('template', 'default')
        
        try:
            # Determine export format
            if format_str == 'html':
                export_format = ExportFormat.HTML
            elif format_str == 'pdf':
                export_format = ExportFormat.PDF
            elif format_str in ['markdown', 'md']:
                export_format = ExportFormat.MARKDOWN
            else:
                return jsonify({"error": "Unsupported format"}), 400
            
            # Load package data
            package_data = load_package_data(package_dir)
            
            # Export the brief
            output_path = brief_exporter.export_brief(
                package_data=package_data,
                package_date=date,
                format=export_format,
                template_name=template_name
            )
            
            return jsonify({
                "success": True,
                "output_path": str(output_path),
                "format": format_str,
                "download_url": f"/export/{date}/{format_str}"
            })
            
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    return app


def get_available_packages() -> List[Dict[str, Any]]:
    """Get list of available data packages."""
    output_root = Path("data/output")
    packages = []
    
    if not output_root.exists():
        return packages
    
    for package_dir in sorted(output_root.iterdir(), reverse=True):
        if package_dir.is_dir():
            # Get package info
            summary_path = package_dir / "package_summary.json"
            if summary_path.exists():
                try:
                    summary = json.loads(summary_path.read_text())
                    packages.append({
                        "date": package_dir.name,
                        "timestamp": summary.get("timestamp", ""),
                        "sources": summary.get("sources", []),
                        "has_analytics": bool(summary.get("analytics")),
                        "path": str(package_dir)
                    })
                except Exception:
                    # Fallback for packages without summary
                    packages.append({
                        "date": package_dir.name,
                        "timestamp": "",
                        "sources": [],
                        "has_analytics": False,
                        "path": str(package_dir)
                    })
    
    return packages


def load_package_data(package_dir: Path) -> Dict[str, Any]:
    """Load all data from a package directory."""
    data = {
        "summary": {},
        "csv_files": {},
        "reports": {}
    }
    
    # Load summary
    summary_path = package_dir / "package_summary.json"
    if summary_path.exists():
        data["summary"] = json.loads(summary_path.read_text())
    
    # Load CSV files
    for csv_file in package_dir.glob("*.csv"):
        try:
            df = pd.read_csv(csv_file)
            data["csv_files"][csv_file.stem] = df.to_dict(orient="records")
        except Exception as e:
            print(f"Error loading {csv_file}: {e}")
    
    # Load reports
    for md_file in package_dir.glob("*.md"):
        data["reports"][md_file.stem] = md_file.read_text(encoding='utf-8')
    
    return data


def generate_prefilled_template(package_data: Dict[str, Any], date: str) -> str:
    """Generate a pre-filled template with package data."""
    template_path = Path("docs/template.md")
    
    if not template_path.exists():
        return "# Template not found"
    
    template_content = template_path.read_text()
    
    # Get summary data
    summary = package_data.get("summary", {})
    analytics = summary.get("analytics", {})
    
    # Replace placeholders
    template_content = template_content.replace("YYYY-W##", f"2025-W{get_week_number(date)}")
    template_content = template_content.replace("_(YYYY-MM-DD)_", date)
    
    # Add pre-filled content based on analytics
    prefill_section = generate_prefill_content(summary, analytics)
    
    # Insert prefill content after the description
    insert_point = template_content.find("Compact, investment-focused weekly brief")
    if insert_point != -1:
        end_point = template_content.find("\n", insert_point)
        template_content = (template_content[:end_point] + 
                          f"\n\n{prefill_section}" + 
                          template_content[end_point:])
    
    return template_content


def generate_prefill_content(summary: Dict[str, Any], analytics: Dict[str, Any]) -> str:
    """Generate pre-filled content based on analytics."""
    content = []
    
    # Executive Summary
    content.append("## Pre-filled Executive Summary")
    content.append("")
    
    # Key changes
    top_deltas = analytics.get("top_deltas", [])
    if top_deltas:
        content.append("**Key Market Changes:**")
        for delta in top_deltas[:3]:
            direction = "📈" if delta["delta_pct"] > 0 else "📉"
            content.append(f"- {direction} **{delta['series_id']}**: {delta['delta_pct']:.1%} change ({delta['old_value']:.2f} → {delta['new_value']:.2f})")
        content.append("")
    
    # Anomalies
    anomalies = analytics.get("anomalies", [])
    if anomalies:
        content.append("**Notable Anomalies:**")
        for anomaly in anomalies[:2]:
            content.append(f"- **{anomaly['series_id']}**: {anomaly['value']:.2f} (z-score: {anomaly['z_score']:.2f}) on {anomaly['date']}")
        content.append("")
    
    # Trends
    trends = analytics.get("trends", [])
    strong_trends = [t for t in trends if t['trend_strength'] in ['strong', 'moderate']]
    if strong_trends:
        content.append("**Significant Trends:**")
        for trend in strong_trends[:3]:
            direction = "📈" if trend['slope'] > 0 else "📉"
            content.append(f"- {direction} **{trend['series_id']}**: {trend['trend_strength']} {trend['direction']} trend")
        content.append("")
    
    # Data sources
    sources = summary.get("sources", [])
    if sources:
        content.append("**Available Data Sources:**")
        for source in sources:
            content.append(f"- {source.upper()}")
        content.append("")
    
    content.append("---")
    content.append("")
    content.append("*This section was auto-generated from WeQuo analytics. Review and customize as needed.*")
    
    return "\n".join(content)


def get_week_number(date_str: str) -> int:
    """Get week number from date string."""
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.isocalendar()[1]
    except:
        return 1


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000)
