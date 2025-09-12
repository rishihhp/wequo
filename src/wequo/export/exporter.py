"""
Export functionality for WeQuo briefs.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum
import tempfile

try:
    import weasyprint
    HAS_WEASYPRINT = True
except (ImportError, OSError):
    HAS_WEASYPRINT = False

from .templates import TemplateRenderer


class ExportFormat(Enum):
    """Supported export formats."""
    HTML = "html"
    PDF = "pdf"
    MARKDOWN = "markdown"


class BriefExporter:
    """Exports WeQuo briefs to various formats."""
    
    def __init__(self, template_dir: str = "templates/export"):
        """Initialize exporter with template directory."""
        self.template_dir = Path(template_dir)
        self.template_dir.mkdir(parents=True, exist_ok=True)
        self.renderer = TemplateRenderer(str(self.template_dir))
        
        # Ensure default templates exist
        self._create_default_templates()
    
    def export_brief(self, 
                     package_data: Dict[str, Any], 
                     package_date: str,
                     format: ExportFormat,
                     output_path: Optional[Path] = None,
                     template_name: str = "default") -> Path:
        """Export a brief to the specified format."""
        
        if format == ExportFormat.HTML:
            return self._export_html(package_data, package_date, output_path, template_name)
        elif format == ExportFormat.PDF:
            return self._export_pdf(package_data, package_date, output_path, template_name)
        elif format == ExportFormat.MARKDOWN:
            return self._export_markdown(package_data, package_date, output_path, template_name)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _export_html(self, 
                     package_data: Dict[str, Any], 
                     package_date: str,
                     output_path: Optional[Path],
                     template_name: str) -> Path:
        """Export to HTML format."""
        
        # Prepare context data
        context = self._prepare_context(package_data, package_date)
        
        # Render HTML
        html_content = self.renderer.render_template(f"{template_name}_brief.html", context)
        
        # Determine output path
        if output_path is None:
            output_path = Path(f"data/output/{package_date}/wequo_brief_{package_date}.html")
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write HTML file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return output_path
    
    def _export_pdf(self, 
                    package_data: Dict[str, Any], 
                    package_date: str,
                    output_path: Optional[Path],
                    template_name: str) -> Path:
        """Export to PDF format."""
        
        if not HAS_WEASYPRINT:
            # Fallback: Export as HTML with print-friendly styling
            print("Warning: WeasyPrint not available. Exporting as print-friendly HTML instead of PDF.")
            return self._export_html(package_data, package_date, output_path, template_name)
        
        # First generate HTML
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as temp_html:
            html_path = Path(temp_html.name)
        
        try:
            self._export_html(package_data, package_date, html_path, template_name)
            
            # Determine output path
            if output_path is None:
                output_path = Path(f"data/output/{package_date}/wequo_brief_{package_date}.pdf")
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert HTML to PDF
            weasyprint.HTML(filename=str(html_path)).write_pdf(str(output_path))
            
            return output_path
            
        finally:
            # Clean up temporary HTML file
            html_path.unlink(missing_ok=True)
    
    def _export_markdown(self, 
                         package_data: Dict[str, Any], 
                         package_date: str,
                         output_path: Optional[Path],
                         template_name: str) -> Path:
        """Export to Markdown format."""
        
        # Prepare context data
        context = self._prepare_context(package_data, package_date)
        
        # Render Markdown
        md_content = self.renderer.render_template(f"{template_name}_brief.md", context)
        
        # Determine output path
        if output_path is None:
            output_path = Path(f"data/output/{package_date}/wequo_brief_{package_date}.md")
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write Markdown file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        return output_path
    
    def _prepare_context(self, package_data: Dict[str, Any], package_date: str) -> Dict[str, Any]:
        """Prepare template context from package data."""
        
        summary = package_data.get('summary', {})
        analytics = summary.get('analytics', {})
        
        # Get week number
        try:
            week_num = datetime.strptime(package_date, '%Y-%m-%d').isocalendar()[1]
        except:
            week_num = 1
        
        context = {
            'date': package_date,
            'week_number': week_num,
            'year': package_date[:4],
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'sources': summary.get('sources', []),
            'analytics': analytics,
            'package_data': package_data,
            
            # Executive Summary Data
            'top_deltas': analytics.get('top_deltas', [])[:5],
            'anomalies': analytics.get('anomalies', [])[:3],
            'trends': analytics.get('trends', [])[:5],
            
            # Formatted summaries
            'executive_summary': self._generate_executive_summary(analytics),
            'key_insights': self._generate_key_insights(analytics),
            'market_overview': self._generate_market_overview(analytics),
            'risk_assessment': self._generate_risk_assessment(analytics),
            'data_summary': self._generate_data_summary(summary),
        }
        
        return context
    
    def _generate_executive_summary(self, analytics: Dict[str, Any]) -> str:
        """Generate executive summary from analytics."""
        summary_parts = []
        
        # Top changes
        top_deltas = analytics.get('top_deltas', [])[:3]
        if top_deltas:
            changes = []
            for delta in top_deltas:
                direction = "increased" if delta.get('delta_pct', 0) > 0 else "decreased"
                pct = abs(delta.get('delta_pct', 0) * 100)
                changes.append(f"{delta.get('series_id', 'Unknown')} {direction} by {pct:.1f}%")
            
            if changes:
                summary_parts.append(f"Key market movements this week include {', '.join(changes[:-1])}{' and ' + changes[-1] if len(changes) > 1 else changes[0]}.")
        
        # Anomalies
        anomalies = analytics.get('anomalies', [])
        if anomalies:
            summary_parts.append(f"We detected {len(anomalies)} significant anomalies requiring attention.")
        
        # Trends
        trends = analytics.get('trends', [])
        strong_trends = [t for t in trends if t.get('trend_strength') in ['strong', 'moderate']]
        if strong_trends:
            upward = len([t for t in strong_trends if t.get('direction') == 'upward'])
            downward = len([t for t in strong_trends if t.get('direction') == 'downward'])
            summary_parts.append(f"Market trends show {upward} series trending upward and {downward} trending downward.")
        
        return ' '.join(summary_parts) if summary_parts else "Market conditions remain stable with normal variation patterns."
    
    def _generate_key_insights(self, analytics: Dict[str, Any]) -> list:
        """Generate key insights list."""
        insights = []
        
        # High-impact deltas
        top_deltas = analytics.get('top_deltas', [])[:5]
        for delta in top_deltas:
            pct = delta.get('delta_pct', 0) * 100
            if abs(pct) >= 5:  # Significant change
                direction = "surge" if pct > 0 else "decline"
                insights.append({
                    'title': f"{delta.get('series_id', 'Unknown')} shows significant {direction}",
                    'description': f"Changed by {abs(pct):.1f}% from {delta.get('old_value', 'N/A')} to {delta.get('new_value', 'N/A')}",
                    'impact': 'high' if abs(pct) >= 10 else 'medium'
                })
        
        # Critical anomalies
        anomalies = analytics.get('anomalies', [])
        for anomaly in anomalies[:3]:
            z_score = abs(anomaly.get('z_score', 0))
            if z_score >= 2.5:  # Very unusual
                insights.append({
                    'title': f"Unusual activity in {anomaly.get('series_id', 'Unknown')}",
                    'description': f"Value of {anomaly.get('value', 'N/A')} is {z_score:.1f} standard deviations from normal",
                    'impact': 'high' if z_score >= 3 else 'medium'
                })
        
        return insights
    
    def _generate_market_overview(self, analytics: Dict[str, Any]) -> Dict[str, Any]:
        """Generate market overview section."""
        overview = {
            'volatility': 'normal',
            'sentiment': 'neutral',
            'major_movers': [],
            'stability_indicators': []
        }
        
        # Analyze volatility from deltas
        deltas = analytics.get('top_deltas', [])
        if deltas:
            avg_change = sum(abs(d.get('delta_pct', 0)) for d in deltas) / len(deltas) * 100
            if avg_change > 10:
                overview['volatility'] = 'high'
            elif avg_change > 5:
                overview['volatility'] = 'elevated'
        
        # Major movers
        for delta in deltas[:3]:
            pct = delta.get('delta_pct', 0) * 100
            if abs(pct) >= 5:
                overview['major_movers'].append({
                    'series': delta.get('series_id', 'Unknown'),
                    'change': pct,
                    'direction': 'up' if pct > 0 else 'down'
                })
        
        return overview
    
    def _generate_risk_assessment(self, analytics: Dict[str, Any]) -> Dict[str, Any]:
        """Generate risk assessment."""
        risk = {
            'level': 'low',
            'factors': [],
            'monitoring': []
        }
        
        # Count high-impact events
        anomalies = analytics.get('anomalies', [])
        high_z_scores = [a for a in anomalies if abs(a.get('z_score', 0)) >= 2.5]
        
        large_deltas = analytics.get('top_deltas', [])
        significant_changes = [d for d in large_deltas if abs(d.get('delta_pct', 0)) >= 0.1]
        
        # Assess risk level
        if len(high_z_scores) >= 3 or len(significant_changes) >= 5:
            risk['level'] = 'high'
        elif len(high_z_scores) >= 1 or len(significant_changes) >= 3:
            risk['level'] = 'medium'
        
        # Risk factors
        if high_z_scores:
            risk['factors'].append(f"{len(high_z_scores)} statistical anomalies detected")
        if significant_changes:
            risk['factors'].append(f"{len(significant_changes)} significant market movements")
        
        # Monitoring recommendations
        for anomaly in high_z_scores[:2]:
            risk['monitoring'].append(f"Monitor {anomaly.get('series_id', 'Unknown')} for continued deviation")
        
        return risk
    
    def _generate_data_summary(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        """Generate data summary section."""
        data_summary = {
            'sources': summary.get('sources', []),
            'total_points': 0,
            'coverage': {},
            'quality': 'good'
        }
        
        # Count data points by source
        latest_values = summary.get('latest_values', {})
        for source, values in latest_values.items():
            count = len(values) if isinstance(values, list) else 1
            data_summary['coverage'][source] = count
            data_summary['total_points'] += count
        
        return data_summary
    
    def _create_default_templates(self):
        """Create default export templates."""
        
        # Default HTML template
        html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WeQuo Weekly Brief - {{ date }}</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 20px;
            background: #fff;
        }
        .header {
            text-align: center;
            border-bottom: 3px solid #667eea;
            padding-bottom: 30px;
            margin-bottom: 40px;
        }
        .header h1 {
            color: #667eea;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .header .subtitle {
            color: #666;
            font-size: 1.2em;
        }
        .section {
            margin-bottom: 40px;
        }
        .section h2 {
            color: #4a5568;
            border-left: 4px solid #667eea;
            padding-left: 15px;
            margin-bottom: 20px;
        }
        .insight-item {
            background: #f7fafc;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 0 8px 8px 0;
        }
        .insight-title {
            font-weight: bold;
            color: #2d3748;
            margin-bottom: 5px;
        }
        .delta-positive { border-left-color: #38a169; }
        .delta-negative { border-left-color: #e53e3e; }
        .anomaly { border-left-color: #ed8936; }
        .metadata {
            background: #edf2f7;
            padding: 20px;
            border-radius: 8px;
            font-size: 0.9em;
            color: #4a5568;
            margin-top: 40px;
        }
        .data-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .data-card {
            background: #f7fafc;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }
        .data-number {
            font-size: 1.5em;
            font-weight: bold;
            color: #667eea;
        }
        .risk-level-low { color: #38a169; }
        .risk-level-medium { color: #ed8936; }
        .risk-level-high { color: #e53e3e; }
        @media print {
            body { padding: 20px; }
            .header { page-break-after: avoid; }
            .section { page-break-inside: avoid; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Weekly Global Risk & Opportunity Brief</h1>
        <div class="subtitle">Week {{ week_number }}, {{ year }} | {{ date }}</div>
    </div>

    <div class="section">
        <h2>Executive Summary</h2>
        <p>{{ executive_summary }}</p>
    </div>

    <div class="section">
        <h2>Key Market Insights</h2>
        {% for insight in key_insights %}
        <div class="insight-item">
            <div class="insight-title">{{ insight.title }}</div>
            <div>{{ insight.description }}</div>
        </div>
        {% endfor %}
    </div>

    <div class="section">
        <h2>Significant Changes</h2>
        {% for delta in top_deltas %}
        <div class="insight-item {% if delta.delta_pct > 0 %}delta-positive{% else %}delta-negative{% endif %}">
            <div class="insight-title">{{ delta.series_id }}</div>
            <div>{{ "%.1f"|format(delta.delta_pct * 100) }}% change: {{ "%.2f"|format(delta.old_value) }} → {{ "%.2f"|format(delta.new_value) }}</div>
        </div>
        {% endfor %}
    </div>

    {% if anomalies %}
    <div class="section">
        <h2>Market Anomalies</h2>
        {% for anomaly in anomalies %}
        <div class="insight-item anomaly">
            <div class="insight-title">{{ anomaly.series_id }}</div>
            <div>Unusual value: {{ "%.2f"|format(anomaly.value) }} ({{ "%.1f"|format(anomaly.z_score) }}σ from normal)</div>
        </div>
        {% endfor %}
    </div>
    {% endif %}

    <div class="section">
        <h2>Risk Assessment</h2>
        <p>Current risk level: <strong class="risk-level-{{ risk_assessment.level }}">{{ risk_assessment.level.upper() }}</strong></p>
        {% if risk_assessment.factors %}
        <ul>
        {% for factor in risk_assessment.factors %}
            <li>{{ factor }}</li>
        {% endfor %}
        </ul>
        {% endif %}
    </div>

    <div class="section">
        <h2>Data Coverage</h2>
        <div class="data-grid">
            <div class="data-card">
                <div class="data-number">{{ data_summary.total_points }}</div>
                <div>Total Data Points</div>
            </div>
            <div class="data-card">
                <div class="data-number">{{ data_summary.sources|length }}</div>
                <div>Data Sources</div>
            </div>
            {% for source, count in data_summary.coverage.items() %}
            <div class="data-card">
                <div class="data-number">{{ count }}</div>
                <div>{{ source.upper() }}</div>
            </div>
            {% endfor %}
        </div>
    </div>

    <div class="metadata">
        <strong>Generated by WeQuo</strong><br>
        Report Date: {{ timestamp }}<br>
        Data Sources: {{ sources|join(', ')|upper }}<br>
        Coverage Period: {{ date }}
    </div>
</body>
</html>'''
        
        # Default Markdown template
        md_template = '''# Weekly Global Risk & Opportunity Brief

**Week {{ week_number }}, {{ year }} | {{ date }}**

## Executive Summary

{{ executive_summary }}

## Key Market Insights

{% for insight in key_insights %}
### {{ insight.title }}

{{ insight.description }}

{% endfor %}

## Significant Changes

{% for delta in top_deltas %}
- **{{ delta.series_id }}**: {{ "%.1f"|format(delta.delta_pct * 100) }}% change ({{ "%.2f"|format(delta.old_value) }} → {{ "%.2f"|format(delta.new_value) }})
{% endfor %}

{% if anomalies %}
## Market Anomalies

{% for anomaly in anomalies %}
- **{{ anomaly.series_id }}**: Unusual value {{ "%.2f"|format(anomaly.value) }} ({{ "%.1f"|format(anomaly.z_score) }}σ from normal)
{% endfor %}

{% endif %}
## Risk Assessment

**Current Risk Level:** {{ risk_assessment.level.upper() }}

{% if risk_assessment.factors %}
**Risk Factors:**
{% for factor in risk_assessment.factors %}
- {{ factor }}
{% endfor %}

{% endif %}
{% if risk_assessment.monitoring %}
**Monitoring Recommendations:**
{% for item in risk_assessment.monitoring %}
- {{ item }}
{% endfor %}

{% endif %}
## Data Coverage

- **Total Data Points:** {{ data_summary.total_points }}
- **Data Sources:** {{ data_summary.sources|length }}

{% for source, count in data_summary.coverage.items() %}
- **{{ source.upper() }}:** {{ count }} data points
{% endfor %}

---

*Generated by WeQuo | {{ timestamp }} | Sources: {{ sources|join(', ')|upper }}*
'''
        
        # Write templates
        html_path = self.template_dir / "default_brief.html"
        md_path = self.template_dir / "default_brief.md"
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_template)
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_template)
