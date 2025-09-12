from __future__ import annotations
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

import click
import pandas as pd


@click.group()
def cli():
    """WeQuo Author CLI - Tools for fetching and working with weekly data packages."""
    pass


@cli.command()
@click.option("--output-dir", default="data/output", help="Output directory for data packages")
def list_packages(output_dir: str):
    """List available data packages."""
    output_path = Path(output_dir)
    
    if not output_path.exists():
        click.echo("No data packages found.")
        return
    
    packages = []
    for package_dir in sorted(output_path.iterdir(), reverse=True):
        if package_dir.is_dir():
            summary_path = package_dir / "package_summary.json"
            if summary_path.exists():
                try:
                    summary = json.loads(summary_path.read_text())
                    packages.append({
                        "date": package_dir.name,
                        "timestamp": summary.get("timestamp", ""),
                        "sources": summary.get("sources", []),
                        "has_analytics": bool(summary.get("analytics"))
                    })
                except Exception:
                    packages.append({
                        "date": package_dir.name,
                        "timestamp": "",
                        "sources": [],
                        "has_analytics": False
                    })
    
    if not packages:
        click.echo("No data packages found.")
        return
    
    click.echo("Available data packages:")
    click.echo("=" * 50)
    
    for pkg in packages:
        click.echo(f"📅 {pkg['date']}")
        click.echo(f"   Sources: {', '.join(pkg['sources'])}")
        click.echo(f"   Analytics: {'✅' if pkg['has_analytics'] else '❌'}")
        if pkg['timestamp']:
            click.echo(f"   Generated: {pkg['timestamp']}")
        click.echo()


@cli.command()
@click.argument("date")
@click.option("--output-dir", default="data/output", help="Output directory for data packages")
@click.option("--format", "output_format", type=click.Choice(["json", "table", "summary"]), default="summary")
def view_package(date: str, output_dir: str, output_format: str):
    """View a specific data package."""
    package_dir = Path(output_dir) / date
    
    if not package_dir.exists():
        click.echo(f"Package for {date} not found.", err=True)
        sys.exit(1)
    
    # Load package data
    package_data = load_package_data(package_dir)
    
    if output_format == "json":
        click.echo(json.dumps(package_data, indent=2, default=str))
    elif output_format == "table":
        display_package_tables(package_data)
    else:  # summary
        display_package_summary(package_data, date)


@cli.command()
@click.argument("date")
@click.option("--output-dir", default="data/output", help="Output directory for data packages")
@click.option("--template-path", default="docs/template.md", help="Path to template file")
@click.option("--output-file", help="Output file path (default: auto-generated)")
def generate_template(date: str, output_dir: str, template_path: str, output_file: Optional[str]):
    """Generate a pre-filled template for a specific date."""
    package_dir = Path(output_dir) / date
    
    if not package_dir.exists():
        click.echo(f"Package for {date} not found.", err=True)
        sys.exit(1)
    
    template_path_obj = Path(template_path)
    if not template_path_obj.exists():
        click.echo(f"Template file {template_path} not found.", err=True)
        sys.exit(1)
    
    # Load package data
    package_data = load_package_data(package_dir)
    
    # Generate pre-filled template
    template_content = generate_prefilled_template(package_data, date, template_path_obj)
    
    # Determine output file
    if not output_file:
        output_file = f"wequo_brief_{date}.md"
    
    # Write template
    output_path = Path(output_file)
    output_path.write_text(template_content)
    
    click.echo(f"✅ Generated pre-filled template: {output_path}")
    click.echo(f"📝 Edit the template and customize as needed.")


@cli.command()
@click.argument("date")
@click.option("--output-dir", default="data/output", help="Output directory for data packages")
@click.option("--open-editor", is_flag=True, help="Open template in default editor")
def quick_start(date: str, output_dir: str, open_editor: bool):
    """Quick start workflow: fetch package and generate template."""
    package_dir = Path(output_dir) / date
    
    if not package_dir.exists():
        click.echo(f"Package for {date} not found.", err=True)
        click.echo("Run the pipeline first: python scripts/run_weekly.py")
        sys.exit(1)
    
    # Generate template
    package_data = load_package_data(package_dir)
    template_path = Path("docs/template.md")
    
    if not template_path.exists():
        click.echo("Template file not found.", err=True)
        sys.exit(1)
    
    template_content = generate_prefilled_template(package_data, date, template_path)
    output_file = f"wequo_brief_{date}.md"
    output_path = Path(output_file)
    output_path.write_text(template_content)
    
    click.echo(f"✅ Generated pre-filled template: {output_path}")
    
    # Show summary
    summary = package_data.get("summary", {})
    analytics = summary.get("analytics", {})
    
    click.echo("\n📊 Package Summary:")
    click.echo(f"   Sources: {', '.join(summary.get('sources', []))}")
    
    if analytics:
        top_deltas = analytics.get("top_deltas", [])
        anomalies = analytics.get("anomalies", [])
        trends = analytics.get("trends", [])
        
        if top_deltas:
            click.echo(f"   Key Changes: {len(top_deltas)} significant deltas")
        if anomalies:
            click.echo(f"   Anomalies: {len(anomalies)} detected")
        if trends:
            strong_trends = [t for t in trends if t['trend_strength'] in ['strong', 'moderate']]
            click.echo(f"   Trends: {len(strong_trends)} significant trends")
    
    click.echo(f"\n⏱️  Target: Complete brief within 2 hours")
    click.echo(f"📝 Next: Edit {output_path} and customize content")
    
    if open_editor:
        import subprocess
        try:
            subprocess.run([os.environ.get("EDITOR", "code"), str(output_path)])
        except Exception as e:
            click.echo(f"Could not open editor: {e}")


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
            click.echo(f"Warning: Error loading {csv_file}: {e}", err=True)
    
    # Load reports
    for md_file in package_dir.glob("*.md"):
        data["reports"][md_file.stem] = md_file.read_text()
    
    return data


def display_package_summary(package_data: Dict[str, Any], date: str):
    """Display a human-readable package summary."""
    summary = package_data.get("summary", {})
    analytics = summary.get("analytics", {})
    
    click.echo(f"📅 WeQuo Data Package: {date}")
    click.echo("=" * 40)
    
    # Basic info
    click.echo(f"Generated: {summary.get('timestamp', 'Unknown')}")
    click.echo(f"Sources: {', '.join(summary.get('sources', []))}")
    click.echo()
    
    # Analytics summary
    if analytics:
        click.echo("📊 Analytics Summary:")
        
        top_deltas = analytics.get("top_deltas", [])
        if top_deltas:
            click.echo(f"  Key Changes: {len(top_deltas)} significant deltas")
            for delta in top_deltas[:3]:
                direction = "📈" if delta["delta_pct"] > 0 else "📉"
                click.echo(f"    {direction} {delta['series_id']}: {delta['delta_pct']:.1%}")
        
        anomalies = analytics.get("anomalies", [])
        if anomalies:
            click.echo(f"  Anomalies: {len(anomalies)} detected")
            for anomaly in anomalies[:2]:
                click.echo(f"    ⚠️  {anomaly['series_id']}: {anomaly['value']:.2f} (z-score: {anomaly['z_score']:.2f})")
        
        trends = analytics.get("trends", [])
        strong_trends = [t for t in trends if t['trend_strength'] in ['strong', 'moderate']]
        if strong_trends:
            click.echo(f"  Trends: {len(strong_trends)} significant trends")
            for trend in strong_trends[:3]:
                direction = "📈" if trend['slope'] > 0 else "📉"
                click.echo(f"    {direction} {trend['series_id']}: {trend['trend_strength']} {trend['direction']}")
        
        click.echo()
    
    # Available files
    click.echo("📁 Available Files:")
    csv_files = package_data.get("csv_files", {})
    reports = package_data.get("reports", {})
    
    for name in csv_files.keys():
        click.echo(f"  📊 {name}.csv")
    for name in reports.keys():
        click.echo(f"  📝 {name}.md")


def display_package_tables(package_data: Dict[str, Any]):
    """Display package data as tables."""
    csv_files = package_data.get("csv_files", {})
    
    for name, data in csv_files.items():
        if not data:
            continue
        
        click.echo(f"\n📊 {name.upper()} Data:")
        click.echo("-" * 30)
        
        df = pd.DataFrame(data)
        if len(df) > 10:
            click.echo(df.head(10).to_string(index=False))
            click.echo(f"... and {len(df) - 10} more rows")
        else:
            click.echo(df.to_string(index=False))


def generate_prefilled_template(package_data: Dict[str, Any], date: str, template_path: Path) -> str:
    """Generate a pre-filled template with package data."""
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


@cli.command()
@click.argument("date")
@click.option("--format", "export_format", type=click.Choice(["pdf", "html"]), default="pdf", help="Export format")
@click.option("--output-dir", default="data/output", help="Output directory for data packages")
@click.option("--include-charts/--no-charts", default=True, help="Include charts in export")
@click.option("--include-data/--no-data", default=True, help="Include data tables in export")
def export_package(date: str, export_format: str, output_dir: str, include_charts: bool, include_data: bool):
    """Export a data package to PDF or HTML format."""
    try:
        from .export import WeQuoExporter
        
        output_path = Path(output_dir)
        exporter = WeQuoExporter(output_path)
        
        click.echo(f"Exporting package {date} to {export_format.upper()}...")
        output_file = exporter.export_package(date, export_format, include_charts, include_data)
        
        click.echo(f"✅ Export successful: {output_file}")
        click.echo(f"📁 File size: {output_file.stat().st_size / 1024:.1f} KB")
        
    except FileNotFoundError:
        click.echo(f"❌ Error: Package for {date} not found in {output_dir}")
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Export failed: {e}")
        sys.exit(1)


@cli.command()
@click.argument("date")
@click.option("--output-dir", default="data/output", help="Output directory for data packages")
def export_all(date: str, output_dir: str):
    """Export a data package to both PDF and HTML formats."""
    try:
        from .export import WeQuoExporter
        
        output_path = Path(output_dir)
        exporter = WeQuoExporter(output_path)
        
        click.echo(f"Exporting package {date} to all formats...")
        
        # Export PDF
        click.echo("📄 Generating PDF...")
        pdf_file = exporter.export_package(date, "pdf", True, True)
        click.echo(f"✅ PDF: {pdf_file}")
        
        # Export HTML
        click.echo("🌐 Generating HTML...")
        html_file = exporter.export_package(date, "html", True, True)
        click.echo(f"✅ HTML: {html_file}")
        
        click.echo(f"🎉 All exports completed successfully!")
        
    except FileNotFoundError:
        click.echo(f"❌ Error: Package for {date} not found in {output_dir}")
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Export failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    cli()
