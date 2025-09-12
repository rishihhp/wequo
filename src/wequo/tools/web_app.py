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
    # Determine repo root and templates directory relative to this file
    # Path(__file__).resolve().parents[3] points to the repository root (wequo/)
    module_dir = Path(__file__).resolve().parents[3]
    templates_dir = module_dir / "templates"

    # Create Flask app and point Jinja to the repo templates directory
    app = Flask(__name__, template_folder=str(templates_dir))
    app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")
    
    # Configuration (store absolute paths)
    app.config["OUTPUT_ROOT"] = (module_dir / "data" / "output")
    app.config["TEMPLATE_PATH"] = module_dir / "docs" / "template.md"
    
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
        
        # Save to temporary file (ensure UTF-8 encoding to support emojis and other Unicode)
        temp_path = package_dir / "template_prefilled.md"
        temp_path.write_text(template_content, encoding="utf-8")

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
            return jsonify(json.loads(summary_path.read_text(encoding="utf-8")))
        else:
            return jsonify({"error": "Summary not found"}), 404
    
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
                    summary = json.loads(summary_path.read_text(encoding="utf-8"))
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
        # Read JSON summary with UTF-8 encoding
        data["summary"] = json.loads(summary_path.read_text(encoding="utf-8"))
    
    # Load CSV files
    for csv_file in package_dir.glob("*.csv"):
        try:
            df = pd.read_csv(csv_file)
            data["csv_files"][csv_file.stem] = df.to_dict(orient="records")
        except Exception as e:
            print(f"Error loading {csv_file}: {e}")
    
    # Load reports
    for md_file in package_dir.glob("*.md"):
        # Read markdown reports as UTF-8 (templates or reports may contain emojis)
        data["reports"][md_file.stem] = md_file.read_text(encoding="utf-8")
    
    return data


def generate_prefilled_template(package_data: Dict[str, Any], date: str) -> str:
    """Generate a pre-filled template with package data."""
    template_path = Path("docs/template.md")
    
    if not template_path.exists():
        return "# Template not found"
    
    # Read template using UTF-8 to preserve any Unicode characters
    template_content = template_path.read_text(encoding="utf-8")
    
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
