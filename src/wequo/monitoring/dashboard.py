from __future__ import annotations
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

from flask import Flask, render_template_string, jsonify, request, send_file

from .core import MonitoringEngine, MonitoringResult
from .alerts import AlertManager
from .sla import SLATracker
from ..search import SearchEngine, SearchQuery, DocumentType
from ..export import BriefExporter, ExportFormat


class MonitoringDashboard:
    """Web dashboard for monitoring WeQuo pipeline health and data search."""
    
    def __init__(self, 
                 monitoring_engine: MonitoringEngine,
                 alert_manager: AlertManager,
                 sla_tracker: SLATracker,
                 output_root: Path = None):
        self.monitoring_engine = monitoring_engine
        self.alert_manager = alert_manager
        self.sla_tracker = sla_tracker
        self.output_root = output_root or Path("data/output")
        
        # Initialize search engine and exporter
        self.search_engine = SearchEngine()
        self.brief_exporter = BriefExporter(output_root=self.output_root)
        
        self.app = Flask(__name__)
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup Flask routes for the dashboard."""
        
        @self.app.route('/')
        def dashboard():
            """Main dashboard page."""
            return render_template_string(DASHBOARD_TEMPLATE)
        
        @self.app.route('/api/monitoring-status')
        def monitoring_status():
            """Get current monitoring status."""
            try:
                # Generate monitoring report
                monitoring_result = self.monitoring_engine.generate_monitoring_report()
                
                # Get recent alerts
                recent_alerts = self.alert_manager.get_recent_alerts(24)
                
                # Get SLA status
                sla_report = self.sla_tracker.generate_sla_report(7)  # Weekly SLA
                
                return jsonify({
                    "status": "success",
                    "data": {
                        "monitoring": self._serialize_monitoring_result(monitoring_result),
                        "recent_alerts": recent_alerts,
                        "sla_report": self._serialize_sla_report(sla_report),
                        "last_updated": datetime.now().isoformat()
                    }
                })
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "message": str(e)
                }), 500
        
        @self.app.route('/api/pipeline-history')
        def pipeline_history():
            """Get pipeline run history."""
            days = int(request.args.get('days', 7))
            
            try:
                history = self._get_pipeline_history(days)
                return jsonify({
                    "status": "success",
                    "data": history
                })
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "message": str(e)
                }), 500
        
        @self.app.route('/api/sla-trend')
        def sla_trend():
            """Get SLA compliance trend."""
            days = int(request.args.get('days', 30))
            
            try:
                trend = self.sla_tracker.get_compliance_trend(days)
                return jsonify({
                    "status": "success",
                    "data": trend
                })
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "message": str(e)
                }), 500
        
        @self.app.route('/api/alerts')
        def alerts():
            """Get alerts with filtering."""
            hours = int(request.args.get('hours', 24))
            severity = request.args.get('severity', None)
            
            try:
                alerts_data = self.alert_manager.get_recent_alerts(hours)
                
                # Filter by severity if specified
                if severity:
                    alerts_data = [a for a in alerts_data if a['severity'] == severity]
                
                return jsonify({
                    "status": "success",
                    "data": alerts_data
                })
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "message": str(e)
                }), 500
        
        @self.app.route('/api/data-freshness')
        def data_freshness():
            """Get data freshness status."""
            date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
            
            try:
                freshness_checks = self.monitoring_engine.check_data_freshness(date)
                return jsonify({
                    "status": "success",
                    "data": [self._serialize_freshness_check(check) for check in freshness_checks]
                })
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "message": str(e)
                }), 500
        
        @self.app.route('/api/anomaly-rates')
        def anomaly_rates():
            """Get anomaly rates by connector."""
            days = int(request.args.get('days', 7))
            
            try:
                rates = self.monitoring_engine.calculate_anomaly_rates(days)
                return jsonify({
                    "status": "success",
                    "data": rates
                })
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "message": str(e)
                }), 500
        
        # Search routes
        @self.app.route('/search')
        def search_page():
            """Search interface page."""
            query = request.args.get('q', '')
            results = []
            facets = {}
            
            if query:
                search_results = self.search_engine.search_simple(query)
                results = [result.to_dict() for result in search_results]
            
            facets = self.search_engine.get_facets()
            stats = self.search_engine.get_stats()
            
            return render_template_string(SEARCH_TEMPLATE, 
                                        query=query, 
                                        results=results, 
                                        facets=facets,
                                        stats=stats.to_dict())
        
        @self.app.route('/api/search')
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
            results = self.search_engine.search(query)
            
            return jsonify({
                'query': query.to_dict(),
                'results': [result.to_dict() for result in results],
                'total': len(results)
            })
        
        @self.app.route('/api/search/rebuild', methods=['POST'])
        def api_rebuild_search():
            """API endpoint to rebuild search index."""
            try:
                count = self.search_engine.rebuild_index(self.output_root)
                return jsonify({
                    'success': True,
                    'message': f'Index rebuilt with {count} documents'
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/packages')
        def api_packages():
            """API endpoint to get available packages."""
            packages = self._get_available_packages()
            return jsonify(packages)
        
        @self.app.route('/export/<date>/<format>')
        def export_brief(date: str, format: str):
            """Export a brief in the specified format."""
            package_dir = self.output_root / date
            
            if not package_dir.exists():
                return jsonify({"error": "Package not found"}), 404
            
            # Load package data
            package_data = self._load_package_data(package_dir)
            
            try:
                # Determine export format
                if format.lower() == 'html':
                    export_format = ExportFormat.HTML
                elif format.lower() == 'pdf':
                    export_format = ExportFormat.PDF
                elif format.lower() in ['markdown', 'md']:
                    export_format = ExportFormat.MARKDOWN
                else:
                    return jsonify({"error": "Unsupported format"}), 400
                
                # Export the brief
                output_path = self.brief_exporter.export_brief(
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
    
    def _serialize_monitoring_result(self, result: MonitoringResult) -> Dict[str, Any]:
        """Serialize MonitoringResult for JSON response."""
        return {
            "timestamp": result.timestamp.isoformat(),
            "pipeline_run": self._serialize_pipeline_run(result.pipeline_run),
            "freshness_checks": [self._serialize_freshness_check(check) for check in result.freshness_checks],
            "sla_status": result.sla_status,
            "anomaly_rates": result.anomaly_rates,
            "system_health": result.system_health
        }
    
    def _serialize_pipeline_run(self, run) -> Optional[Dict[str, Any]]:
        """Serialize PipelineRun for JSON response."""
        if run is None:
            return None
        
        return {
            "timestamp": run.timestamp.isoformat(),
            "status": run.status,
            "duration_seconds": run.duration_seconds,
            "connectors_attempted": run.connectors_attempted,
            "connectors_succeeded": run.connectors_succeeded,
            "connectors_failed": run.connectors_failed,
            "data_points_collected": run.data_points_collected,
            "errors": run.errors,
            "output_dir": run.output_dir
        }
    
    def _serialize_freshness_check(self, check) -> Dict[str, Any]:
        """Serialize DataFreshnessCheck for JSON response."""
        return {
            "connector": check.connector,
            "latest_data_timestamp": check.latest_data_timestamp.isoformat(),
            "age_hours": check.age_hours,
            "is_fresh": check.is_fresh,
            "threshold_hours": check.threshold_hours
        }
    
    def _serialize_sla_report(self, report) -> Dict[str, Any]:
        """Serialize SLAReport for JSON response."""
        return {
            "report_date": report.report_date.isoformat(),
            "measurement_period_days": report.measurement_period_days,
            "overall_compliance": report.overall_compliance,
            "compliance_score": report.compliance_score,
            "metrics": [
                {
                    "name": m.name,
                    "current_value": m.current_value,
                    "target_threshold": m.target_threshold,
                    "is_compliant": m.is_compliant
                } for m in report.metrics
            ],
            "violations": report.violations,
            "recommendations": report.recommendations
        }
    
    def _get_pipeline_history(self, days: int) -> List[Dict[str, Any]]:
        """Get pipeline run history."""
        history_file = self.monitoring_engine.monitoring_dir / "pipeline_history.jsonl"
        
        if not history_file.exists():
            return []
        
        cutoff_date = datetime.now() - timedelta(days=days)
        history = []
        
        try:
            with open(history_file, 'r') as f:
                for line in f:
                    run_data = json.loads(line)
                    run_timestamp = datetime.fromisoformat(run_data["timestamp"])
                    
                    if run_timestamp >= cutoff_date:
                        history.append(run_data)
        except Exception:
            return []
        
        # Sort by timestamp (newest first)
        history.sort(key=lambda x: x["timestamp"], reverse=True)
        return history
    
    def _get_available_packages(self) -> List[Dict[str, Any]]:
        """Get list of available data packages."""
        packages = []
        
        if not self.output_root.exists():
            return packages
        
        for package_dir in sorted(self.output_root.iterdir(), reverse=True):
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
    
    def _load_package_data(self, package_dir: Path) -> Dict[str, Any]:
        """Load all data from a package directory."""
        import pandas as pd
        
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
    
    def run(self, host: str = "localhost", port: int = 5001, debug: bool = False):
        """Run the monitoring dashboard."""
        self.app.run(host=host, port=port, debug=debug)


# HTML template for the search interface
SEARCH_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WeQuo Data Search & Export</title>
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
            padding: 0;
            margin: 0;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 20px;
        }

        /* Navigation Bar */
        .navbar {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            padding: 15px 30px;
            margin: 20px;
            border-radius: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 20px;
            z-index: 100;
        }

        .nav-brand {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 1.5em;
            font-weight: 700;
            color: #2d3748;
        }

        .nav-links {
            display: flex;
            gap: 8px;
        }

        .nav-link {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 12px 20px;
            border-radius: 12px;
            text-decoration: none;
            color: #718096;
            font-weight: 500;
            transition: all 0.2s ease;
        }

        .nav-link:hover,
        .nav-link.active {
            background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%);
            color: white;
            transform: translateY(-2px);
            box-shadow: 0 4px 16px rgba(45, 55, 72, 0.4);
        }
        
        .header {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 24px;
            padding: 40px 50px;
            margin: 30px 20px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
            border: 1px solid rgba(255, 255, 255, 0.2);
            text-align: center;
        }
        
        .header h1 {
            color: #2d3748;
            font-size: 2.8em;
            font-weight: 800;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 15px;
            background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .header-subtitle {
            color: #718096;
            font-size: 1.2em;
            margin-bottom: 30px;
            font-weight: 500;
        }
        
        .nav-tabs {
            display: flex;
            gap: 16px;
            justify-content: center;
            margin-bottom: 30px;
        }
        
        .nav-tab {
            padding: 12px 24px;
            background: rgba(255, 255, 255, 0.8);
            border: none;
            border-radius: 25px;
            text-decoration: none;
            color: #4a5568;
            font-weight: 600;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 8px;
            border: 2px solid transparent;
        }
        
        .nav-tab:hover, 
        .nav-tab.active {
            background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%);
            color: white;
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(45, 55, 72, 0.4);
            border-color: rgba(255, 255, 255, 0.2);
        }
        
        .search-container {
            display: flex;
            gap: 10px;
            max-width: 600px;
            margin: 0 auto;
        }
        
        .search-input {
            flex: 1;
            padding: 15px 20px;
            border: 2px solid #e2e8f0;
            border-radius: 12px;
            font-size: 16px;
            transition: all 0.2s ease;
        }
        
        .search-input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .search-btn {
            padding: 15px 25px;
            background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%);
            color: white;
            border: none;
            border-radius: 12px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 8px;
            box-shadow: 0 4px 16px rgba(45, 55, 72, 0.3);
        }
        
        .search-btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 12px 32px rgba(45, 55, 72, 0.5);
            background: linear-gradient(135deg, #1a202c 0%, #2d3748 100%);
        }
        
        .main-content {
            display: grid;
            grid-template-columns: 300px 1fr;
            gap: 30px;
        }
        
        .sidebar {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }
        
        .card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 24px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.12);
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: all 0.3s ease;
        }

        .card:hover {
            transform: translateY(-4px);
            box-shadow: 0 25px 70px rgba(0, 0, 0, 0.15);
        }
        
        .card h3 {
            color: #2d3748;
            font-size: 1.2em;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .facet-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 12px;
            border-radius: 8px;
            cursor: pointer;
            transition: background-color 0.2s ease;
            margin-bottom: 4px;
        }
        
        .facet-item:hover {
            background: #f7fafc;
        }
        
        .facet-count {
            background: #e2e8f0;
            color: #4a5568;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: 600;
        }
        
        .results-section {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 30px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }
        
        .results-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 25px;
            padding-bottom: 15px;
            border-bottom: 2px solid #f7fafc;
        }
        
        .results-title {
            color: #2d3748;
            font-size: 1.5em;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .result-item {
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            transition: all 0.2s ease;
            position: relative;
        }
        
        .result-item:hover {
            border-color: #667eea;
            box-shadow: 0 4px 16px rgba(102, 126, 234, 0.1);
        }
        
        .result-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 12px;
        }
        
        .result-title {
            color: #2d3748;
            font-size: 1.2em;
            font-weight: 600;
            margin-bottom: 8px;
        }
        
        .export-dropdown {
            position: absolute;
            top: 10px;
            right: 10px;
            display: none;
        }
        
        .result-item:hover .export-dropdown {
            display: block;
        }
        
        .export-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 8px 15px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.8em;
            display: flex;
            align-items: center;
            gap: 5px;
        }
        
        .export-menu {
            position: absolute;
            top: 100%;
            right: 0;
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            z-index: 1000;
            min-width: 120px;
            display: none;
        }
        
        .export-menu.show {
            display: block;
        }
        
        .export-option {
            padding: 10px 15px;
            cursor: pointer;
            transition: background-color 0.2s;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .export-option:hover {
            background: #f7fafc;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .stat-card {
            text-align: center;
            padding: 15px;
            background: #f7fafc;
            border-radius: 10px;
        }
        
        .stat-number {
            font-size: 1.5em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }
        
        .type-badge {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: 600;
            text-transform: uppercase;
        }
        
        .type-package { background: #c6f6d5; color: #22543d; }
        .type-data_point { background: #bee3f8; color: #1a365d; }
        .type-analytics { background: #fed7aa; color: #c05621; }
        .type-report { background: #e9d8fd; color: #553c9a; }
        .type-anomaly { background: #fbb6ce; color: #97266d; }
        .type-trend { background: #c6f6d5; color: #22543d; }
        
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #718096;
        }
        
        mark {
            background: #fed7aa;
            padding: 2px 4px;
            border-radius: 4px;
        }
        
        @media (max-width: 1024px) {
            .main-content {
                grid-template-columns: 1fr;
            }

            .header {
                margin: 20px 10px;
                padding: 30px 25px;
            }

            .nav-links {
                flex-wrap: wrap;
                gap: 4px;
            }

            .nav-link {
                padding: 10px 16px;
                font-size: 0.9em;
            }
        }

        @media (max-width: 768px) {
            .navbar {
                margin: 10px;
                padding: 12px 20px;
            }

            .nav-brand {
                font-size: 1.3em;
            }

            .nav-links {
                display: none;
            }

            .header h1 {
                font-size: 2.2em;
            }

            .header-subtitle {
                font-size: 1em;
            }

            .main-content {
                grid-template-columns: 1fr;
            }
            
            .nav-tabs {
                flex-wrap: wrap;
                gap: 8px;
            }

            .card {
                padding: 20px;
            }
        }

        @media (max-width: 640px) {
            .container {
                padding: 0 10px;
            }

            .header {
                margin: 10px 5px;
                padding: 20px 15px;
            }

            .header h1 {
                font-size: 1.8em;
            }

            .search-container {
                flex-direction: column;
                gap: 12px;
            }

            .nav-tabs {
                flex-direction: column;
                gap: 8px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Navigation Bar -->
        <nav class="navbar">
            <div class="nav-brand">
                <i data-lucide="database" style="width: 32px; height: 32px; color: #2d3748;"></i>
                <span>WeQuo Monitoring</span>
            </div>
            <div class="nav-links">
                <a href="/" class="nav-link">
                    <i data-lucide="activity"></i>
                    Dashboard
                </a>
                <a href="/search" class="nav-link active">
                    <i data-lucide="search"></i>
                    Search & Export
                </a>
            </div>
        </nav>

        <div class="header">
            <h1>
                <i data-lucide="search"></i>
                Data Search & Export
            </h1>
            <div class="header-subtitle">
                Search through data packages, analytics, reports, and specific data points
            </div>
            
            <div class="nav-tabs">
                <a href="/" class="nav-tab">
                    <i data-lucide="activity"></i>
                    Monitoring
                </a>
                <a href="/search" class="nav-tab active">
                    <i data-lucide="search"></i>
                    Search
                </a>
            </div>
            
            <form class="search-container" method="GET">
                <input
                    type="text"
                    name="q"
                    class="search-input"
                    placeholder="Search data packages, analytics, and reports..."
                    value="{{ query }}"
                    autofocus
                />
                <button type="submit" class="search-btn">
                    <i data-lucide="search"></i>
                    Search
                </button>
            </form>
        </div>
        
        <div class="main-content">
            <div class="sidebar">
                <!-- Search Statistics -->
                <div class="card">
                    <h3>
                        <i data-lucide="bar-chart-3"></i>
                        Index Statistics
                    </h3>
                    
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-number">{{ stats.total_documents }}</div>
                            <div class="stat-label">Documents</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">{{ stats.total_sources }}</div>
                            <div class="stat-label">Sources</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">
                                {{ "%.1f"|format(stats.index_size_mb) }}
                            </div>
                            <div class="stat-label">MB</div>
                        </div>
                    </div>
                    
                    <button
                        onclick="rebuildIndex()"
                        class="search-btn"
                        style="width: 100%; justify-content: center; margin-top: 10px"
                    >
                        <i data-lucide="refresh-cw"></i>
                        Rebuild Index
                    </button>
                </div>
                
                <!-- Document Types Filter -->
                {% if facets.types %}
                <div class="card">
                    <h3>
                        <i data-lucide="file-type"></i>
                        Document Types
                    </h3>
                    
                    <div class="facet-group">
                        {% for type, count in facets.types.items() %}
                        <div class="facet-item" onclick="filterByType('{{ type }}')">
                            <span>{{ type.replace('_', ' ').title() }}</span>
                            <span class="facet-count">{{ count }}</span>
                        </div>
                        {% endfor %}
                    </div>
                </div>
                {% endif %}
                
                <!-- Sources Filter -->
                {% if facets.sources %}
                <div class="card">
                    <h3>
                        <i data-lucide="database"></i>
                        Data Sources
                    </h3>
                    
                    <div class="facet-group">
                        {% for source, count in facets.sources.items() %}
                        <div class="facet-item" onclick="filterBySource('{{ source }}')">
                            <span>{{ source.upper() }}</span>
                            <span class="facet-count">{{ count }}</span>
                        </div>
                        {% endfor %}
                    </div>
                </div>
                {% endif %}
            </div>
            
            <div class="results-section">
                <div class="results-header">
                    <h2 class="results-title">
                        <i data-lucide="list"></i>
                        Search Results
                    </h2>
                    {% if results %}
                    <div class="results-count">
                        {{ results|length }} results{% if query %} for "{{ query }}"{% endif %}
                    </div>
                    {% endif %}
                </div>
                
                {% if results %}
                {% for result in results %}
                <div class="result-item" data-type="{{ result.type }}" data-date="{{ result.metadata.get('package_date', '') }}">
                    <div class="result-header">
                        <div>
                            <div class="result-title">{{ result.title }}</div>
                            <div class="result-meta">
                                <span>{{ result.timestamp[:10] }}</span>
                                {% if result.source %}
                                <span>{{ result.source.upper() }}</span>
                                {% endif %}
                                <span>Score: {{ "%.2f"|format(result.score) }}</span>
                            </div>
                        </div>
                        <span class="type-badge type-{{ result.type }}">
                            {{ result.type.replace('_', ' ') }}
                        </span>
                    </div>
                    
                    {% if result.type == 'package' %}
                    <div class="export-dropdown">
                        <button class="export-btn" onclick="toggleExportMenu(this)">
                            <i data-lucide="download"></i>
                            Export
                        </button>
                        <div class="export-menu">
                            <div class="export-option" onclick="exportPackage('{{ result.metadata.get('package_date', '') }}', 'html')">
                                <i data-lucide="globe"></i>
                                HTML
                            </div>
                            <div class="export-option" onclick="exportPackage('{{ result.metadata.get('package_date', '') }}', 'pdf')">
                                <i data-lucide="file-text"></i>
                                PDF
                            </div>
                            <div class="export-option" onclick="exportPackage('{{ result.metadata.get('package_date', '') }}', 'markdown')">
                                <i data-lucide="file-edit"></i>
                                Markdown
                            </div>
                        </div>
                    </div>
                    {% endif %}
                    
                    {% if result.highlights %}
                    <div class="result-highlights">
                        {% for highlight in result.highlights %}
                        <div class="highlight">{{ highlight | safe }}</div>
                        {% endfor %}
                    </div>
                    {% endif %}
                    
                    <div class="result-content">{{ result.content[:300] }}{% if result.content|length > 300 %}...{% endif %}</div>
                </div>
                {% endfor %}
                {% elif query %}
                <div class="empty-state">
                    <i data-lucide="search-x" style="width: 48px; height: 48px; margin-bottom: 16px"></i>
                    <h3>No results found</h3>
                    <p>Try different keywords or check the filters.</p>
                </div>
                {% else %}
                <div class="empty-state">
                    <i data-lucide="search" style="width: 48px; height: 48px; margin-bottom: 16px"></i>
                    <h3>Search WeQuo Data</h3>
                    <p>Search through data packages, analytics, reports, and specific data points.</p>
                    <div style="margin-top: 20px; text-align: left; max-width: 400px; margin-left: auto; margin-right: auto;">
                        <strong>Examples:</strong>
                        <ul style="margin-top: 8px">
                            <li>"inflation" - Find inflation-related data</li>
                            <li>"anomaly" - Find detected anomalies</li>
                            <li>"2025-09-12" - Find data from specific date</li>
                            <li>"FRED" - Find Federal Reserve data</li>
                        </ul>
                    </div>
                </div>
                {% endif %}
            </div>
        </div>
    </div>
    
    <script>
        // Initialize Lucide icons
        lucide.createIcons();
        
        function filterByType(type) {
            const currentUrl = new URL(window.location);
            currentUrl.searchParams.set("types", type);
            window.location = currentUrl;
        }
        
        function filterBySource(source) {
            const currentUrl = new URL(window.location);
            currentUrl.searchParams.set("sources", source);
            window.location = currentUrl;
        }
        
        async function rebuildIndex() {
            const button = event.target;
            const originalText = button.innerHTML;
            button.disabled = true;
            button.innerHTML = '<i data-lucide="loader-2"></i> Rebuilding...';
            lucide.createIcons();
            
            try {
                const response = await fetch("/api/search/rebuild", {
                    method: "POST",
                });
                const result = await response.json();
                
                if (result.success) {
                    alert("Search index rebuilt successfully!");
                    location.reload();
                } else {
                    alert("Error rebuilding index: " + result.error);
                }
            } catch (error) {
                alert("Error rebuilding index: " + error.message);
            } finally {
                button.disabled = false;
                button.innerHTML = originalText;
                lucide.createIcons();
            }
        }
        
        function toggleExportMenu(btn) {
            const menu = btn.nextElementSibling;
            const isVisible = menu.classList.contains('show');
            
            // Hide all other export menus
            document.querySelectorAll('.export-menu').forEach(m => m.classList.remove('show'));
            
            // Toggle current menu
            if (!isVisible) {
                menu.classList.add('show');
            }
        }
        
        function exportPackage(date, format) {
            window.open(`/export/${date}/${format}`, '_blank');
            // Hide menu
            document.querySelectorAll('.export-menu').forEach(m => m.classList.remove('show'));
        }
        
        // Close export menus when clicking outside
        document.addEventListener('click', function(e) {
            if (!e.target.closest('.export-dropdown')) {
                document.querySelectorAll('.export-menu').forEach(m => m.classList.remove('show'));
            }
        });
    </script>
</body>
</html>
"""

# HTML template for the monitoring dashboard
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WeQuo Pipeline Monitoring</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
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
            padding: 0;
            margin: 0;
            color: #333;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 20px;
        }

        /* Navigation Bar */
        .navbar {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            padding: 15px 30px;
            margin: 20px;
            border-radius: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 20px;
            z-index: 100;
        }

        .nav-brand {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 1.5em;
            font-weight: 700;
            color: #2d3748;
        }

        .nav-links {
            display: flex;
            gap: 8px;
        }

        .nav-link {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 12px 20px;
            border-radius: 12px;
            text-decoration: none;
            color: #718096;
            font-weight: 500;
            transition: all 0.2s ease;
        }

        .nav-link:hover,
        .nav-link.active {
            background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%);
            color: white;
            transform: translateY(-2px);
            box-shadow: 0 4px 16px rgba(45, 55, 72, 0.4);
        }

        .header {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 24px;
            padding: 40px 50px;
            margin: 30px 20px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
            border: 1px solid rgba(255, 255, 255, 0.2);
            text-align: center;
        }
        
        .header h1 {
            color: #2d3748;
            font-size: 2.8em;
            font-weight: 800;
            margin-bottom: 16px;
            background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .header-subtitle {
            color: #718096;
            font-size: 1.2em;
            margin-bottom: 30px;
            font-weight: 500;
        }

        .header-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }

        .header-stat {
            background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%);
            padding: 24px;
            border-radius: 16px;
            text-align: center;
            border-left: 4px solid #2d3748;
            transition: all 0.3s ease;
        }

        .header-stat:hover {
            transform: translateY(-4px);
            box-shadow: 0 8px 25px rgba(45, 55, 72, 0.15);
        }

        .header-stat-number {
            font-size: 2.2em;
            font-weight: 800;
            color: #2d3748;
            margin-bottom: 8px;
        }

        .header-stat-label {
            color: #718096;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-size: 0.85em;
        }
        
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 30px;
            margin: 20px;
        }
        
        .card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: all 0.3s ease;
        }

        .card:hover {
            transform: translateY(-4px);
            box-shadow: 0 25px 70px rgba(0, 0, 0, 0.12);
        }
        
        .card h3 {
            margin-bottom: 20px;
            color: #2d3748;
            font-size: 1.4em;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 10px;
            border-bottom: 2px solid #f7fafc;
            padding-bottom: 12px;
        }
        
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        
        .status-success { background-color: #27ae60; }
        .status-warning { background-color: #f39c12; }
        .status-error { background-color: #e74c3c; }
        
        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.5rem;
            padding: 0.5rem;
            background-color: #f8f9fa;
            border-radius: 4px;
        }
        
        .metric-value {
            font-weight: bold;
            font-size: 1.1rem;
        }
        
        .alert {
            padding: 0.75rem;
            margin-bottom: 0.5rem;
            border-radius: 4px;
            border-left: 4px solid;
        }
        
        .alert-critical {
            background-color: #fdf2f2;
            border-color: #e74c3c;
            color: #c0392b;
        }
        
        .alert-warning {
            background-color: #fef5e7;
            border-color: #f39c12;
            color: #d68910;
        }
        
        .alert-info {
            background-color: #e8f4f8;
            border-color: #3498db;
            color: #2980b9;
        }
        
        .chart-container {
            position: relative;
            height: 300px;
            margin-top: 1rem;
        }
        
        .refresh-btn {
            background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 12px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 8px;
            box-shadow: 0 4px 16px rgba(45, 55, 72, 0.3);
        }
        
        .refresh-btn:hover {
            background: linear-gradient(135deg, #1a202c 0%, #2d3748 100%);
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(45, 55, 72, 0.4);
        }
        
        .loading {
            color: #7f8c8d;
            font-style: italic;
        }
        
        .timestamp {
            color: #7f8c8d;
            font-size: 0.9rem;
            margin-top: 1rem;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
        }
        
        th, td {
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid #ecf0f1;
        }
        
        th {
            background-color: #f8f9fa;
            font-weight: 600;
        }
        
        .progress-bar {
            width: 100%;
            height: 20px;
            background-color: #ecf0f1;
            border-radius: 10px;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            transition: width 0.3s ease;
        }
        
        .progress-success { background-color: #27ae60; }
        .progress-warning { background-color: #f39c12; }
        .progress-error { background-color: #e74c3c; }

        @media (max-width: 1024px) {
            .dashboard-grid {
                grid-template-columns: 1fr;
            }

            .header {
                margin: 20px 10px;
                padding: 30px 25px;
            }

            .header-stats {
                grid-template-columns: repeat(2, 1fr);
            }

            .nav-links {
                flex-wrap: wrap;
                gap: 4px;
            }

            .nav-link {
                padding: 10px 16px;
                font-size: 0.9em;
            }
        }

        @media (max-width: 768px) {
            .navbar {
                margin: 10px;
                padding: 12px 20px;
            }

            .nav-brand {
                font-size: 1.3em;
            }

            .nav-links {
                display: none;
            }

            .header h1 {
                font-size: 2.2em;
            }

            .header-subtitle {
                font-size: 1em;
            }

            .header-stats {
                grid-template-columns: 1fr;
                gap: 15px;
            }

            .dashboard-grid {
                margin: 10px;
            }

            .card {
                padding: 20px;
            }
        }

        @media (max-width: 640px) {
            .container {
                padding: 0 10px;
            }

            .header {
                margin: 10px 5px;
                padding: 20px 15px;
            }

            .header h1 {
                font-size: 1.8em;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Navigation Bar -->
        <nav class="navbar">
            <div class="nav-brand">
                <i data-lucide="activity" style="width: 32px; height: 32px; color: #2d3748;"></i>
                <span>WeQuo Monitoring</span>
            </div>
            <div class="nav-links">
                <a href="/" class="nav-link active">
                    <i data-lucide="activity"></i>
                    Dashboard
                </a>
                <a href="/search" class="nav-link">
                    <i data-lucide="search"></i>
                    Search & Export
                </a>
            </div>
        </nav>

        <!-- Header with System Overview -->
        <div class="header">
            <h1>
                <i data-lucide="shield-check"></i>
                Pipeline Monitoring Dashboard
            </h1>
            <div class="header-subtitle">
                Real-time monitoring and analytics for WeQuo data pipeline
            </div>
            
            <div class="header-stats">
                <div class="header-stat">
                    <div class="header-stat-number" id="total-runs">--</div>
                    <div class="header-stat-label">Pipeline Runs</div>
                </div>
                <div class="header-stat">
                    <div class="header-stat-number" id="success-rate">--</div>
                    <div class="header-stat-label">Success Rate</div>
                </div>
                <div class="header-stat">
                    <div class="header-stat-number" id="avg-duration">--</div>
                    <div class="header-stat-label">Avg Duration</div>
                </div>
                <div class="header-stat">
                    <div class="header-stat-number" id="active-alerts">--</div>
                    <div class="header-stat-label">Active Alerts</div>
                </div>
            </div>
        </div>

        <!-- Action Bar -->
        <div style="display: flex; justify-content: space-between; align-items: center; margin: 20px; padding: 20px; background: rgba(255, 255, 255, 0.1); border-radius: 16px; backdrop-filter: blur(10px);">
            <div style="display: flex; gap: 20px; align-items: center;">
                <span style="color: white; font-weight: 600;">System Status:</span>
                <div id="system-status" style="display: flex; align-items: center; gap: 8px; color: white;">
                    <i data-lucide="loader" style="width: 16px; height: 16px;"></i>
                    <span>Loading...</span>
                </div>
            </div>
            <button class="refresh-btn" onclick="refreshDashboard()">
                <i data-lucide="refresh-cw"></i>
                Refresh Data
            </button>
        </div>
        
        <div class="dashboard-grid">
            <!-- SLA Status -->
            <div class="card">
                <h3>SLA Status</h3>
                <div id="sla-status" class="loading">Loading...</div>
            </div>
            
            <!-- Recent Alerts -->
            <div class="card">
                <h3>Recent Alerts (24h)</h3>
                <div id="recent-alerts" class="loading">Loading...</div>
            </div>
            
            <!-- Data Freshness -->
            <div class="card">
                <h3>Data Freshness</h3>
                <div id="data-freshness" class="loading">Loading...</div>
            </div>
            
            <!-- System Health -->
            <div class="card">
                <h3>System Health</h3>
                <div id="system-health" class="loading">Loading...</div>
            </div>
        </div>
        
        <!-- Charts -->
        <div class="dashboard-grid">
            <div class="card">
                <h3>SLA Compliance Trend</h3>
                <div class="chart-container">
                    <canvas id="sla-trend-chart"></canvas>
                </div>
            </div>
            
            <div class="card">
                <h3>Pipeline Run History</h3>
                <div class="chart-container">
                    <canvas id="pipeline-history-chart"></canvas>
                </div>
            </div>
        </div>
        
        <!-- Pipeline History Table -->
        <div class="card">
            <h3>Recent Pipeline Runs</h3>
            <div id="pipeline-history" class="loading">Loading...</div>
        </div>
    </div>
    
    <script>
        // Initialize Lucide icons
        lucide.createIcons();
        
        let slaChart = null;
        let historyChart = null;
        
        async function fetchData(endpoint) {
            try {
                const response = await fetch(endpoint);
                const data = await response.json();
                return data;
            } catch (error) {
                console.error('Error fetching data:', error);
                return { status: 'error', message: error.message };
            }
        }
        
        async function refreshDashboard() {
            // Update all dashboard sections
            await Promise.all([
                updateHeaderStats(),
                updateSLAStatus(),
                updateRecentAlerts(),
                updateDataFreshness(),
                updateSystemHealth(),
                updateSLATrend(),
                updatePipelineHistory()
            ]);
        }

        async function updateHeaderStats() {
            try {
                const [statusData, historyData] = await Promise.all([
                    fetchData('/api/monitoring-status'),
                    fetchData('/api/pipeline-history?days=7')
                ]);

                if (statusData.status === 'success' && historyData.status === 'success') {
                    const slaReport = statusData.data.sla_report;
                    const history = historyData.data;
                    
                    // Update header stats
                    document.getElementById('total-runs').textContent = history.length;
                    document.getElementById('success-rate').textContent = 
                        `${(slaReport.metrics.find(m => m.name === 'pipeline_success_rate')?.current_value * 100 || 0).toFixed(1)}%`;
                    
                    const avgDuration = slaReport.metrics.find(m => m.name === 'average_runtime_minutes')?.current_value || 0;
                    document.getElementById('avg-duration').textContent = `${avgDuration.toFixed(1)}m`;
                    
                    const alertsData = await fetchData('/api/alerts?hours=24');
                    const activeAlerts = alertsData.status === 'success' ? alertsData.data.length : 0;
                    document.getElementById('active-alerts').textContent = activeAlerts;

                    // Update system status
                    const systemStatus = document.getElementById('system-status');
                    const isHealthy = slaReport.overall_compliance && activeAlerts === 0;
                    
                    systemStatus.innerHTML = isHealthy ? 
                        '<i data-lucide="check-circle" style="width: 16px; height: 16px; color: #10b981;"></i><span style="color: #10b981;">Operational</span>' :
                        '<i data-lucide="alert-triangle" style="width: 16px; height: 16px; color: #f59e0b;"></i><span style="color: #f59e0b;">Attention Required</span>';
                    
                    lucide.createIcons();
                }
            } catch (error) {
                console.error('Failed to update header stats:', error);
            }
        }
        
        async function updateSLAStatus() {
            const data = await fetchData('/api/monitoring-status');
            const container = document.getElementById('sla-status');
            
            if (data.status === 'error') {
                container.innerHTML = `<div class="alert alert-critical">Error: ${data.message}</div>`;
                return;
            }
            
            const slaReport = data.data.sla_report;
            const complianceScore = (slaReport.compliance_score * 100).toFixed(1);
            
            let html = `
                <div class="metric">
                    <span>Overall Compliance</span>
                    <span class="metric-value ${slaReport.overall_compliance ? 'status-success' : 'status-error'}">
                        ${slaReport.overall_compliance ? '✅' : '❌'} ${complianceScore}%
                    </span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill ${slaReport.compliance_score > 0.9 ? 'progress-success' : slaReport.compliance_score > 0.7 ? 'progress-warning' : 'progress-error'}" 
                         style="width: ${complianceScore}%"></div>
                </div>
            `;
            
            // Add top violations
            if (slaReport.violations.length > 0) {
                html += '<h4 style="margin-top: 1rem;">Top Violations:</h4>';
                slaReport.violations.slice(0, 3).forEach(violation => {
                    html += `<div class="alert alert-${violation.severity}">${violation.description}</div>`;
                });
            }
            
            container.innerHTML = html;
        }
        
        async function updateRecentAlerts() {
            const data = await fetchData('/api/alerts?hours=24');
            const container = document.getElementById('recent-alerts');
            
            if (data.status === 'error') {
                container.innerHTML = `<div class="alert alert-critical">Error: ${data.message}</div>`;
                return;
            }
            
            const alerts = data.data;
            
            if (alerts.length === 0) {
                container.innerHTML = '<div class="alert alert-info">No alerts in the last 24 hours</div>';
                return;
            }
            
            let html = '';
            alerts.slice(0, 5).forEach(alert => {
                const time = new Date(alert.timestamp).toLocaleTimeString();
                html += `
                    <div class="alert alert-${alert.severity}">
                        <strong>${alert.title}</strong> (${time})<br>
                        <small>${alert.message}</small>
                    </div>
                `;
            });
            
            if (alerts.length > 5) {
                html += `<div class="timestamp">... and ${alerts.length - 5} more alerts</div>`;
            }
            
            container.innerHTML = html;
        }
        
        async function updateDataFreshness() {
            const data = await fetchData('/api/data-freshness');
            const container = document.getElementById('data-freshness');
            
            if (data.status === 'error') {
                container.innerHTML = `<div class="alert alert-critical">Error: ${data.message}</div>`;
                return;
            }
            
            const checks = data.data;
            
            if (checks.length === 0) {
                container.innerHTML = '<div class="alert alert-warning">No data freshness checks available</div>';
                return;
            }
            
            let html = '';
            checks.forEach(check => {
                const indicator = check.is_fresh ? 'status-success' : 'status-error';
                const age = check.age_hours < 24 ? `${check.age_hours.toFixed(1)}h` : `${(check.age_hours/24).toFixed(1)}d`;
                
                html += `
                    <div class="metric">
                        <span><span class="status-indicator ${indicator}"></span>${check.connector}</span>
                        <span class="metric-value">${age}</span>
                    </div>
                `;
            });
            
            container.innerHTML = html;
        }
        
        async function updateSystemHealth() {
            const data = await fetchData('/api/monitoring-status');
            const container = document.getElementById('system-health');
            
            if (data.status === 'error') {
                container.innerHTML = `<div class="alert alert-critical">Error: ${data.message}</div>`;
                return;
            }
            
            const health = data.data.monitoring.system_health;
            
            let html = `
                <div class="metric">
                    <span>Disk Usage</span>
                    <span class="metric-value">${health.disk_usage_percent.toFixed(1)}%</span>
                </div>
                <div class="metric">
                    <span>Output Directory</span>
                    <span class="metric-value">${health.output_dir_size_mb.toFixed(1)} MB</span>
                </div>
                <div class="metric">
                    <span>Monitoring Data</span>
                    <span class="metric-value">${health.monitoring_dir_size_mb.toFixed(1)} MB</span>
                </div>
                <div class="timestamp">Last checked: ${new Date(health.last_monitoring_check).toLocaleString()}</div>
            `;
            
            container.innerHTML = html;
        }
        
        async function updateSLATrend() {
            const data = await fetchData('/api/sla-trend?days=30');
            
            if (data.status === 'error' || !data.data.dates.length) {
                return;
            }
            
            const ctx = document.getElementById('sla-trend-chart').getContext('2d');
            
            if (slaChart) {
                slaChart.destroy();
            }
            
            slaChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.data.dates.map(d => new Date(d).toLocaleDateString()),
                    datasets: [{
                        label: 'Overall Compliance',
                        data: data.data.compliance_scores.map(s => s * 100),
                        borderColor: '#3498db',
                        backgroundColor: 'rgba(52, 152, 219, 0.1)',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100,
                            ticks: {
                                callback: function(value) {
                                    return value + '%';
                                }
                            }
                        }
                    }
                }
            });
        }
        
        async function updatePipelineHistory() {
            const data = await fetchData('/api/pipeline-history?days=7');
            const container = document.getElementById('pipeline-history');
            
            if (data.status === 'error') {
                container.innerHTML = `<div class="alert alert-critical">Error: ${data.message}</div>`;
                return;
            }
            
            const history = data.data;
            
            if (history.length === 0) {
                container.innerHTML = '<div class="alert alert-info">No pipeline runs in the last 7 days</div>';
                return;
            }
            
            let html = `
                <table>
                    <thead>
                        <tr>
                            <th>Time</th>
                            <th>Status</th>
                            <th>Duration</th>
                            <th>Connectors</th>
                            <th>Data Points</th>
                        </tr>
                    </thead>
                    <tbody>
            `;
            
            history.slice(0, 10).forEach(run => {
                const time = new Date(run.timestamp).toLocaleString();
                const duration = `${(run.duration_seconds / 60).toFixed(1)}m`;
                const statusIndicator = run.status === 'success' ? 'status-success' : 'status-error';
                
                html += `
                    <tr>
                        <td>${time}</td>
                        <td><span class="status-indicator ${statusIndicator}"></span>${run.status}</td>
                        <td>${duration}</td>
                        <td>${run.connectors_succeeded.length}/${run.connectors_attempted.length}</td>
                        <td>${run.data_points_collected}</td>
                    </tr>
                `;
            });
            
            html += '</tbody></table>';
            container.innerHTML = html;
        }
        
        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', function() {
            refreshDashboard();
            
            // Auto-refresh every 5 minutes
            setInterval(refreshDashboard, 5 * 60 * 1000);
        });
    </script>
</body>
</html>
"""
