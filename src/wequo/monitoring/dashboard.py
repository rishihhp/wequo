from __future__ import annotations
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

from flask import Flask, render_template_string, jsonify, request

from .core import MonitoringEngine, MonitoringResult
from .alerts import AlertManager
from .sla import SLATracker


class MonitoringDashboard:
    """Web dashboard for monitoring WeQuo pipeline health."""
    
    def __init__(self, 
                 monitoring_engine: MonitoringEngine,
                 alert_manager: AlertManager,
                 sla_tracker: SLATracker):
        self.monitoring_engine = monitoring_engine
        self.alert_manager = alert_manager
        self.sla_tracker = sla_tracker
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
    
    def run(self, host: str = "localhost", port: int = 5001, debug: bool = False):
        """Run the monitoring dashboard."""
        self.app.run(host=host, port=port, debug=debug)


# HTML template for the monitoring dashboard
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WeQuo Pipeline Monitoring</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f5f5f5;
            color: #333;
        }
        
        .header {
            background-color: #2c3e50;
            color: white;
            padding: 1rem 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            margin: 0;
            font-size: 1.8rem;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        
        .card {
            background: white;
            border-radius: 8px;
            padding: 1.5rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .card h3 {
            margin-bottom: 1rem;
            color: #2c3e50;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 0.5rem;
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
            background-color: #3498db;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            cursor: pointer;
            margin-bottom: 1rem;
        }
        
        .refresh-btn:hover {
            background-color: #2980b9;
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
    </style>
</head>
<body>
    <header class="header">
        <h1>WeQuo Pipeline Monitoring Dashboard</h1>
    </header>
    
    <div class="container">
        <button class="refresh-btn" onclick="refreshDashboard()">🔄 Refresh Data</button>
        
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
                updateSLAStatus(),
                updateRecentAlerts(),
                updateDataFreshness(),
                updateSystemHealth(),
                updateSLATrend(),
                updatePipelineHistory()
            ]);
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
