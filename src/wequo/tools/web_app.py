from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
import pandas as pd


def create_app() -> Flask:
    """Create the WeQuo author web application."""
    # Set template folder to project root templates directory
    template_dir = Path(__file__).parent.parent.parent.parent / "templates"
    app = Flask(__name__, template_folder=str(template_dir))
    app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")
    
    # Configuration - use absolute paths from project root
    project_root = Path(__file__).parent.parent.parent.parent
    app.config["OUTPUT_ROOT"] = project_root / "data" / "output"
    app.config["TEMPLATE_PATH"] = project_root / "docs" / "template.md"
    
    @app.route("/")
    def index():
        """Main dashboard page."""
        # Get available packages
        packages = get_available_packages()
        return render_template("index.html", packages=packages)
    
    @app.route("/dashboard")
    def dashboard():
        """Enhanced data exploration dashboard."""
        # Get available packages
        packages = get_available_packages()
        
        # Get latest package for overview
        latest_package = packages[0] if packages else None
        latest_data = None
        
        if latest_package:
            package_dir = app.config["OUTPUT_ROOT"] / latest_package["date"]
            latest_data = load_package_data(package_dir)
        
        return render_template("index.html", 
                             packages=packages, 
                             latest_package=latest_package,
                             latest_data=latest_data,
                             dashboard_mode=True)
    
    @app.route("/package/<date>")
    def view_package(date: str):
        """View a specific data package."""
        package_dir = app.config["OUTPUT_ROOT"] / date
        
        if not package_dir.exists():
            return f"Package for {date} not found", 404
        
        # Load package data
        package_data = load_package_data(package_dir)
        return render_template("package.html", date=date, data=package_data)
    
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
        
        # Save to temporary file
        temp_path = package_dir / "template_prefilled.md"
        temp_path.write_text(template_content, encoding='utf-8')
        
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
        """Search across all data packages."""
        query = request.args.get("q", "").strip()
        source_filter = request.args.get("source", "").strip()
        date_from = request.args.get("date_from", "").strip()
        date_to = request.args.get("date_to", "").strip()
        limit = int(request.args.get("limit", 50))
        
        if not query:
            return jsonify({"error": "Query parameter 'q' is required"}), 400
        
        results = search_data(query, source_filter, date_from, date_to, limit)
        return jsonify({
            "query": query,
            "filters": {
                "source": source_filter,
                "date_from": date_from,
                "date_to": date_to
            },
            "results": results,
            "total": len(results)
        })
    
    @app.route("/api/search/suggestions")
    def api_search_suggestions():
        """Get search suggestions based on available data."""
        query = request.args.get("q", "").strip()
        if len(query) < 2:
            return jsonify({"suggestions": []})
        
        suggestions = get_search_suggestions(query)
        return jsonify({"suggestions": suggestions})
    
    @app.route("/export/<date>")
    def export_package(date: str):
        """Export a data package to PDF or HTML."""
        format_type = request.args.get("format", "pdf").lower()
        include_charts = request.args.get("charts", "true").lower() == "true"
        include_data = request.args.get("data", "true").lower() == "true"
        
        try:
            from .export import WeQuoExporter
            exporter = WeQuoExporter(app.config["OUTPUT_ROOT"])
            output_file = exporter.export_package(date, format_type, include_charts, include_data)
            
            return send_file(output_file, as_attachment=True, 
                           download_name=f"wequo_brief_{date}.{format_type}")
        except FileNotFoundError:
            return f"Package for {date} not found", 404
        except Exception as e:
            return f"Export failed: {str(e)}", 500
    
    @app.route("/export/<date>/html")
    def export_package_html(date: str):
        """Export a data package to HTML format."""
        try:
            from .export import WeQuoExporter
            exporter = WeQuoExporter(app.config["OUTPUT_ROOT"])
            output_file = exporter.export_package(date, "html", True, True)
            
            return send_file(output_file, as_attachment=True, 
                           download_name=f"wequo_brief_{date}.html")
        except FileNotFoundError:
            return f"Package for {date} not found", 404
        except Exception as e:
            return f"Export failed: {str(e)}", 500
    
    @app.route("/export/<date>/pdf")
    def export_package_pdf(date: str):
        """Export a data package to PDF format."""
        try:
            from .export import WeQuoExporter
            exporter = WeQuoExporter(app.config["OUTPUT_ROOT"])
            output_file = exporter.export_package(date, "pdf", True, True)
            
            return send_file(output_file, as_attachment=True, 
                           download_name=f"wequo_brief_{date}.pdf")
        except FileNotFoundError:
            return f"Package for {date} not found", 404
        except Exception as e:
            return f"Export failed: {str(e)}", 500
    
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
        "analytics": {},
        "csv_files": {},
        "reports": {}
    }
    
    # Load summary
    summary_path = package_dir / "package_summary.json"
    if summary_path.exists():
        data["summary"] = json.loads(summary_path.read_text())
    
    # Load analytics data
    analytics_path = package_dir / "analytics_summary.json"
    if analytics_path.exists():
        data["analytics"] = json.loads(analytics_path.read_text())
    
    # Load CSV files
    for csv_file in package_dir.glob("*.csv"):
        try:
            df = pd.read_csv(csv_file)
            data["csv_files"][csv_file.stem] = df.to_dict(orient="records")
        except Exception as e:
            print(f"Error loading {csv_file}: {e}")
    
    # Load reports
    for md_file in package_dir.glob("*.md"):
        try:
            data["reports"][md_file.stem] = md_file.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            # Fallback to latin-1 if utf-8 fails
            data["reports"][md_file.stem] = md_file.read_text(encoding='latin-1')
    
    return data


def generate_prefilled_template(package_data: Dict[str, Any], date: str) -> str:
    """Generate a pre-filled template with package data."""
    template_path = Path("docs/template.md")
    
    if not template_path.exists():
        return "# Template not found"
    
    template_content = template_path.read_text()
    
    # Get summary and analytics data
    summary = package_data.get("summary", {})
    analytics = package_data.get("analytics", {})
    
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
            direction = "UP" if delta["delta_pct"] > 0 else "DOWN"
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
            direction = "UP" if trend['slope'] > 0 else "DOWN"
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


def search_data(query: str, source_filter: str = "", date_from: str = "", date_to: str = "", limit: int = 50) -> List[Dict[str, Any]]:
    """Search across all data packages."""
    results = []
    output_root = Path("data/output")
    
    if not output_root.exists():
        return results
    
    query_lower = query.lower()
    
    # Get all package directories
    package_dirs = [d for d in output_root.iterdir() if d.is_dir()]
    
    # Apply date filtering
    if date_from or date_to:
        filtered_dirs = []
        for package_dir in package_dirs:
            package_date = package_dir.name
            if date_from and package_date < date_from:
                continue
            if date_to and package_date > date_to:
                continue
            filtered_dirs.append(package_dir)
        package_dirs = filtered_dirs
    
    # Search through each package
    for package_dir in sorted(package_dirs, reverse=True):
        if len(results) >= limit:
            break
            
        package_data = load_package_data(package_dir)
        package_date = package_dir.name
        
        # Search in summary data
        summary = package_data.get("summary", {})
        if _matches_query(query_lower, str(summary)):
            results.append({
                "type": "summary",
                "date": package_date,
                "source": "package_summary",
                "content": str(summary)[:200] + "..." if len(str(summary)) > 200 else str(summary),
                "relevance": _calculate_relevance(query_lower, str(summary))
            })
        
        # Search in analytics data
        analytics = package_data.get("analytics", {})
        if _matches_query(query_lower, str(analytics)):
            results.append({
                "type": "analytics",
                "date": package_date,
                "source": "analytics",
                "content": str(analytics)[:200] + "..." if len(str(analytics)) > 200 else str(analytics),
                "relevance": _calculate_relevance(query_lower, str(analytics))
            })
        
        # Search in CSV data
        csv_files = package_data.get("csv_files", {})
        for source, data in csv_files.items():
            if source_filter and source != source_filter:
                continue
                
            if _matches_query(query_lower, str(data)):
                results.append({
                    "type": "data",
                    "date": package_date,
                    "source": source,
                    "content": str(data)[:200] + "..." if len(str(data)) > 200 else str(data),
                    "relevance": _calculate_relevance(query_lower, str(data))
                })
        
        # Search in reports
        reports = package_data.get("reports", {})
        for report_name, content in reports.items():
            if _matches_query(query_lower, content):
                results.append({
                    "type": "report",
                    "date": package_date,
                    "source": report_name,
                    "content": content[:200] + "..." if len(content) > 200 else content,
                    "relevance": _calculate_relevance(query_lower, content)
                })
    
    # Sort by relevance and return top results
    results.sort(key=lambda x: x["relevance"], reverse=True)
    return results[:limit]


def get_search_suggestions(query: str) -> List[str]:
    """Get search suggestions based on available data with fuzzy matching."""
    suggestions = set()
    output_root = Path("data/output")
    
    if not output_root.exists():
        return []
    
    query_lower = query.lower()
    
    # Common misspellings and alternatives
    fuzzy_alternatives = {
        'bitcoin': ['bitcoin', 'btc', 'bit coin'],
        'ethereum': ['ethereum', 'eth', 'ether'],
        'dollar': ['dollar', 'usd', 'doller', 'dolar'],
        'inr': ['inr', 'rupee', 'indian rupee'],
        'gold': ['gold', 'au', 'precious metal'],
        'oil': ['oil', 'crude', 'brent', 'wti'],
        'inflation': ['inflation', 'cpi', 'price index'],
        'unemployment': ['unemployment', 'jobless', 'unemployed'],
        'gdp': ['gdp', 'gross domestic product', 'economic growth'],
        'crypto': ['crypto', 'cryptocurrency', 'digital currency']
    }
    
    # Get suggestions from all packages
    for package_dir in output_root.iterdir():
        if not package_dir.is_dir():
            continue
            
        package_data = load_package_data(package_dir)
        
        # Extract series IDs from analytics
        analytics = package_data.get("analytics", {})
        for trend in analytics.get("trends", []):
            series_id = trend.get("series_id", "")
            if _fuzzy_match(query_lower, series_id.lower()):
                suggestions.add(series_id)
        
        for delta in analytics.get("top_deltas", []):
            series_id = delta.get("series_id", "")
            if _fuzzy_match(query_lower, series_id.lower()):
                suggestions.add(series_id)
        
        for anomaly in analytics.get("anomalies", []):
            series_id = anomaly.get("series_id", "")
            if _fuzzy_match(query_lower, series_id.lower()):
                suggestions.add(series_id)
        
        # Extract source names
        csv_files = package_data.get("csv_files", {})
        for source in csv_files.keys():
            if _fuzzy_match(query_lower, source.lower()):
                suggestions.add(source)
    
    # Add fuzzy alternatives
    for key, alternatives in fuzzy_alternatives.items():
        if _fuzzy_match(query_lower, key):
            suggestions.update(alternatives)
    
    # Sort by relevance (exact matches first, then fuzzy matches)
    suggestions_list = list(suggestions)
    suggestions_list.sort(key=lambda x: _calculate_suggestion_relevance(query_lower, x), reverse=True)
    
    return suggestions_list[:15]


def _matches_query(query: str, text: str) -> bool:
    """Check if query matches text (case-insensitive)."""
    return query in text.lower()


def _calculate_relevance(query: str, text: str) -> float:
    """Calculate relevance score for search results."""
    text_lower = text.lower()
    query_words = query.split()
    
    score = 0.0
    
    # Exact phrase match gets highest score
    if query in text_lower:
        score += 10.0
    
    # Word matches
    for word in query_words:
        if word in text_lower:
            score += 1.0
    
    # Bonus for matches at the beginning
    if text_lower.startswith(query):
        score += 5.0
    
    return score


def _fuzzy_match(query: str, text: str) -> bool:
    """Check if query fuzzy matches text (handles typos and partial matches)."""
    if not query or not text:
        return False
    
    # Exact match
    if query in text:
        return True
    
    # Check if query is a substring of text
    if len(query) >= 3 and query in text:
        return True
    
    # Check if text is a substring of query (for abbreviations)
    if len(text) >= 3 and text in query:
        return True
    
    # Fuzzy matching for common typos (Levenshtein distance approximation)
    if _levenshtein_similarity(query, text) > 0.7:
        return True
    
    # Check individual words
    query_words = query.split()
    text_words = text.split()
    
    for q_word in query_words:
        for t_word in text_words:
            if len(q_word) >= 3 and len(t_word) >= 3:
                if _levenshtein_similarity(q_word, t_word) > 0.8:
                    return True
    
    return False


def _levenshtein_similarity(s1: str, s2: str) -> float:
    """Calculate similarity between two strings using Levenshtein distance."""
    if len(s1) < len(s2):
        return _levenshtein_similarity(s2, s1)
    
    if len(s2) == 0:
        return 0.0
    
    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    max_len = max(len(s1), len(s2))
    if max_len == 0:
        return 1.0
    
    return 1.0 - (previous_row[-1] / max_len)


def _calculate_suggestion_relevance(query: str, suggestion: str) -> float:
    """Calculate relevance score for search suggestions."""
    suggestion_lower = suggestion.lower()
    query_lower = query.lower()
    
    score = 0.0
    
    # Exact match gets highest score
    if query_lower == suggestion_lower:
        score += 100.0
    
    # Starts with query
    elif suggestion_lower.startswith(query_lower):
        score += 50.0
    
    # Contains query
    elif query_lower in suggestion_lower:
        score += 25.0
    
    # Fuzzy match
    else:
        similarity = _levenshtein_similarity(query_lower, suggestion_lower)
        score += similarity * 20.0
    
    # Bonus for shorter suggestions (more specific)
    if len(suggestion) < 20:
        score += 5.0
    
    return score


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000)
