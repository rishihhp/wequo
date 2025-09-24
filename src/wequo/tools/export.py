"""
Export functionality for WeQuo data packages.

This module provides PDF and HTML export capabilities for weekly briefs
and data packages, including charts, tables, and formatted reports.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder
from jinja2 import Environment, FileSystemLoader, Template
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
# WeasyPrint has Windows compatibility issues, using ReportLab only for now
# import weasyprint
# from weasyprint import HTML, CSS


class WeQuoExporter:
    """Main export class for generating PDF and HTML reports."""
    
    def __init__(self, output_root: Path):
        self.output_root = output_root
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.templates_dir = self.project_root / "templates"
        self.static_dir = self.project_root / "static"
        
        # Ensure static directory exists
        self.static_dir.mkdir(exist_ok=True)
        
        # Setup Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=True
        )
    
    def export_package(self, date: str, format: str = "pdf", 
                      include_charts: bool = True, 
                      include_data: bool = True) -> Path:
        """
        Export a data package to the specified format.
        
        Args:
            date: Package date (YYYY-MM-DD)
            format: Export format ('pdf' or 'html')
            include_charts: Whether to include charts
            include_data: Whether to include raw data tables
            
        Returns:
            Path to the exported file
        """
        package_dir = self.output_root / date
        
        if not package_dir.exists():
            raise FileNotFoundError(f"Package for {date} not found")
        
        # Load package data
        package_data = self._load_package_data(package_dir)
        
        if format.lower() == "pdf":
            return self._export_pdf(package_dir, package_data, include_charts, include_data)
        elif format.lower() == "html":
            return self._export_html(package_dir, package_data, include_charts, include_data)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _load_package_data(self, package_dir: Path) -> Dict[str, Any]:
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
                data["reports"][md_file.stem] = md_file.read_text(encoding='latin-1')
        
        return data
    
    def _export_pdf(self, package_dir: Path, package_data: Dict[str, Any], 
                   include_charts: bool, include_data: bool) -> Path:
        """Export package to PDF format."""
        date = package_dir.name
        output_file = package_dir / f"wequo_brief_{date}.pdf"
        
        # Create PDF document
        doc = SimpleDocTemplate(
            str(output_file),
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.darkblue
        )
        
        # Build story (content)
        story = []
        
        # Title
        story.append(Paragraph("WeQuo Weekly Brief", title_style))
        story.append(Paragraph(f"Week of {date}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Executive Summary
        summary = package_data.get("summary", {})
        if summary:
            story.append(Paragraph("Executive Summary", heading_style))
            story.append(Paragraph(
                f"Data collected from {len(summary.get('sources', []))} sources: "
                f"{', '.join(summary.get('sources', []))}", 
                styles['Normal']
            ))
            story.append(Spacer(1, 12))
        
        # Key Analytics
        analytics = package_data.get("analytics", {})
        if analytics and include_charts:
            story.append(Paragraph("Key Market Insights", heading_style))
            
            # Top deltas
            top_deltas = analytics.get("top_deltas", [])
            if top_deltas:
                story.append(Paragraph("Significant Changes:", styles['Heading3']))
                for delta in top_deltas[:5]:
                    direction = "UP" if delta["delta_pct"] > 0 else "DOWN"
                    story.append(Paragraph(
                        f"• {delta['series_id']}: {direction} {delta['delta_pct']:.1%} "
                        f"({delta['old_value']:.2f} → {delta['new_value']:.2f})",
                        styles['Normal']
                    ))
                story.append(Spacer(1, 12))
            
            # Anomalies
            anomalies = analytics.get("anomalies", [])
            if anomalies:
                story.append(Paragraph("Notable Anomalies:", styles['Heading3']))
                for anomaly in anomalies[:3]:
                    story.append(Paragraph(
                        f"• {anomaly['series_id']}: {anomaly['value']:.2f} "
                        f"(z-score: {anomaly['z_score']:.2f}) on {anomaly['date']}",
                        styles['Normal']
                    ))
                story.append(Spacer(1, 12))
        
        # Data Tables
        if include_data:
            csv_files = package_data.get("csv_files", {})
            for source, data_records in csv_files.items():
                if data_records:
                    story.append(Paragraph(f"{source.title()} Data", heading_style))
                    
                    # Create table from data
                    df = pd.DataFrame(data_records)
                    if len(df) > 0:
                        # Limit to first 10 rows for PDF
                        df_display = df.head(10)
                        
                        # Convert to table format
                        table_data = [df_display.columns.tolist()]
                        for _, row in df_display.iterrows():
                            table_data.append([str(val) for val in row.values])
                        
                        table = Table(table_data)
                        table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, 0), 10),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black)
                        ]))
                        
                        story.append(table)
                        story.append(Spacer(1, 12))
        
        # Footer
        story.append(Spacer(1, 20))
        story.append(Paragraph(
            f"Generated by WeQuo on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            styles['Normal']
        ))
        
        # Build PDF
        doc.build(story)
        
        return output_file
    
    def _export_html(self, package_dir: Path, package_data: Dict[str, Any], 
                    include_charts: bool, include_data: bool) -> Path:
        """Export package to HTML format."""
        date = package_dir.name
        output_file = package_dir / f"wequo_brief_{date}.html"
        
        # Create HTML template
        template = self.jinja_env.get_template("export_template.html")
        
        # Prepare template data
        template_data = {
            "date": date,
            "package_data": package_data,
            "include_charts": include_charts,
            "include_data": include_data,
            "generated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Render HTML
        html_content = template.render(**template_data)
        
        # Write to file
        output_file.write_text(html_content, encoding='utf-8')
        
        return output_file
    
    def export_to_pdf_via_html(self, date: str) -> Path:
        """Export package to PDF using HTML-to-PDF conversion (disabled on Windows)."""
        # WeasyPrint not available on Windows, fallback to direct PDF generation
        package_dir = self.output_root / date
        
        if not package_dir.exists():
            raise FileNotFoundError(f"Package for {date} not found")
        
        return self._export_pdf(package_dir, self._load_package_data(package_dir), True, True)


def export_package_cli(date: str, format: str = "pdf", 
                      output_dir: Optional[Path] = None,
                      include_charts: bool = True,
                      include_data: bool = True) -> Path:
    """
    CLI function to export a package.
    
    Args:
        date: Package date (YYYY-MM-DD)
        format: Export format ('pdf' or 'html')
        output_dir: Custom output directory
        include_charts: Whether to include charts
        include_data: Whether to include raw data tables
        
    Returns:
        Path to the exported file
    """
    if output_dir is None:
        output_dir = Path("data/output")
    
    exporter = WeQuoExporter(output_dir)
    return exporter.export_package(date, format, include_charts, include_data)


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python export.py <date> [format]")
        print("Example: python export.py 2025-09-12 pdf")
        sys.exit(1)
    
    date = sys.argv[1]
    format = sys.argv[2] if len(sys.argv) > 2 else "pdf"
    
    try:
        output_file = export_package_cli(date, format)
        print(f"Export successful: {output_file}")
    except Exception as e:
        print(f"Export failed: {e}")
        sys.exit(1)
