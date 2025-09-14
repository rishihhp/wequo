from __future__ import annotations
import json
import smtplib
from dataclasses import dataclass
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart   
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable

from .core import MonitoringResult, PipelineRun


class AlertType(Enum):
    """Types of alerts that can be triggered."""
    
    PIPELINE_FAILURE = "pipeline_failure"
    SLA_BREACH = "sla_breach"
    DATA_FRESHNESS = "data_freshness"
    HIGH_ANOMALY_RATE = "high_anomaly_rate"
    SYSTEM_HEALTH = "system_health"
    CONNECTOR_FAILURE = "connector_failure"


@dataclass
class Alert:
    """Represents an alert condition."""
    
    alert_type: AlertType
    severity: str  # critical, warning, info
    title: str
    message: str
    timestamp: datetime
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary."""
        return {
            "alert_type": self.alert_type.value,
            "severity": self.severity,
            "title": self.title,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


class AlertManager:
    """Manages alerts and notifications for the WeQuo pipeline."""
    
    def __init__(self, config: Dict[str, Any], monitoring_dir: Path):
        self.config = config
        self.monitoring_dir = monitoring_dir
        self.alerts_dir = monitoring_dir / "alerts"
        self.alerts_dir.mkdir(exist_ok=True)
        
        # Alert handlers
        self.handlers: Dict[str, Callable] = {
            "email": self._send_email,
            "file": self._write_to_file,
            "webhook": self._send_webhook,
            "console": self._print_console
        }
        
        # Alert thresholds
        self.thresholds = config.get("alert_thresholds", {
            "pipeline_failure_immediate": True,
            "sla_breach_threshold": 0.95,
            "freshness_hours": 25,
            "anomaly_rate_threshold": 0.15,
            "disk_usage_threshold": 85
        })
    
    def check_and_alert(self, monitoring_result: MonitoringResult) -> List[Alert]:
        """Check monitoring results and generate alerts as needed."""
        alerts = []
        
        # Check pipeline run status
        if monitoring_result.pipeline_run:
            pipeline_alerts = self._check_pipeline_alerts(monitoring_result.pipeline_run)
            alerts.extend(pipeline_alerts)
        
        # Check SLA breaches
        sla_alerts = self._check_sla_alerts(monitoring_result.sla_status)
        alerts.extend(sla_alerts)
        
        # Check data freshness
        freshness_alerts = self._check_freshness_alerts(monitoring_result.freshness_checks)
        alerts.extend(freshness_alerts)
        
        # Check anomaly rates
        anomaly_alerts = self._check_anomaly_alerts(monitoring_result.anomaly_rates)
        alerts.extend(anomaly_alerts)
        
        # Check system health
        system_alerts = self._check_system_alerts(monitoring_result.system_health)
        alerts.extend(system_alerts)
        
        # Send alerts
        for alert in alerts:
            self._send_alert(alert)
        
        return alerts
    
    def _check_pipeline_alerts(self, pipeline_run: PipelineRun) -> List[Alert]:
        """Check for pipeline-related alerts."""
        alerts = []
        
        if pipeline_run.status == "failure":
            alerts.append(Alert(
                alert_type=AlertType.PIPELINE_FAILURE,
                severity="critical",
                title="WeQuo Pipeline Failed",
                message=f"Pipeline run failed with {len(pipeline_run.errors)} errors. "
                       f"Failed connectors: {', '.join(pipeline_run.connectors_failed)}",
                timestamp=pipeline_run.timestamp,
                metadata={
                    "duration_seconds": pipeline_run.duration_seconds,
                    "connectors_failed": pipeline_run.connectors_failed,
                    "errors": pipeline_run.errors[:5],  # Limit error list
                    "data_points_collected": pipeline_run.data_points_collected
                }
            ))
        
        # Check for partial failures
        if pipeline_run.connectors_failed and pipeline_run.status != "failure":
            alerts.append(Alert(
                alert_type=AlertType.CONNECTOR_FAILURE,
                severity="warning",
                title="Some Connectors Failed",
                message=f"Pipeline completed but {len(pipeline_run.connectors_failed)} connectors failed: "
                       f"{', '.join(pipeline_run.connectors_failed)}",
                timestamp=pipeline_run.timestamp,
                metadata={
                    "connectors_failed": pipeline_run.connectors_failed,
                    "connectors_succeeded": pipeline_run.connectors_succeeded
                }
            ))
        
        # Check for long duration
        max_duration = self.config.get("sla", {}).get("max_pipeline_duration_minutes", 30) * 60
        if pipeline_run.duration_seconds > max_duration:
            alerts.append(Alert(
                alert_type=AlertType.SLA_BREACH,
                severity="warning",
                title="Pipeline Duration Exceeded",
                message=f"Pipeline took {pipeline_run.duration_seconds/60:.1f} minutes "
                       f"(limit: {max_duration/60} minutes)",
                timestamp=pipeline_run.timestamp,
                metadata={
                    "duration_seconds": pipeline_run.duration_seconds,
                    "threshold_seconds": max_duration
                }
            ))
        
        return alerts
    
    def _check_sla_alerts(self, sla_status: Dict[str, Any]) -> List[Alert]:
        """Check for SLA breach alerts."""
        alerts = []
        
        for metric, status in sla_status.items():
            if not status.get("compliant", True):
                severity = "critical" if status["value"] < 0.9 else "warning"
                
                alerts.append(Alert(
                    alert_type=AlertType.SLA_BREACH,
                    severity=severity,
                    title=f"SLA Breach: {metric.replace('_', ' ').title()}",
                    message=f"{metric} is {status['value']:.3f}, below threshold of {status['threshold']}",
                    timestamp=datetime.now(),
                    metadata={
                        "metric": metric,
                        "current_value": status["value"],
                        "threshold": status["threshold"],
                        "compliance_gap": status["threshold"] - status["value"]
                    }
                ))
        
        return alerts
    
    def _check_freshness_alerts(self, freshness_checks: List) -> List[Alert]:
        """Check for data freshness alerts."""
        alerts = []
        
        stale_connectors = []
        for check in freshness_checks:
            if not check.is_fresh:
                stale_connectors.append({
                    "connector": check.connector,
                    "age_hours": check.age_hours,
                    "latest_timestamp": check.latest_data_timestamp.isoformat()
                })
        
        if stale_connectors:
            severity = "critical" if len(stale_connectors) > 2 else "warning"
            
            alerts.append(Alert(
                alert_type=AlertType.DATA_FRESHNESS,
                severity=severity,
                title="Stale Data Detected",
                message=f"{len(stale_connectors)} connectors have stale data: "
                       f"{', '.join([c['connector'] for c in stale_connectors])}",
                timestamp=datetime.now(),
                metadata={
                    "stale_connectors": stale_connectors,
                    "freshness_threshold_hours": self.thresholds["freshness_hours"]
                }
            ))
        
        return alerts
    
    def _check_anomaly_alerts(self, anomaly_rates: Dict[str, float]) -> List[Alert]:
        """Check for high anomaly rate alerts."""
        alerts = []
        
        threshold = self.thresholds["anomaly_rate_threshold"]
        high_anomaly_sources = []
        
        for source, rate in anomaly_rates.items():
            if rate > threshold:
                high_anomaly_sources.append({
                    "source": source,
                    "rate": rate
                })
        
        if high_anomaly_sources:
            alerts.append(Alert(
                alert_type=AlertType.HIGH_ANOMALY_RATE,
                severity="warning",
                title="High Anomaly Rates Detected",
                message=f"{len(high_anomaly_sources)} sources have high anomaly rates (>{threshold:.1%})",
                timestamp=datetime.now(),
                metadata={
                    "high_anomaly_sources": high_anomaly_sources,
                    "threshold": threshold
                }
            ))
        
        return alerts
    
    def _check_system_alerts(self, system_health: Dict[str, Any]) -> List[Alert]:
        """Check for system health alerts."""
        alerts = []
        
        # Check disk usage
        disk_usage = system_health.get("disk_usage_percent", 0)
        if disk_usage > self.thresholds["disk_usage_threshold"]:
            alerts.append(Alert(
                alert_type=AlertType.SYSTEM_HEALTH,
                severity="warning",
                title="High Disk Usage",
                message=f"Disk usage is {disk_usage:.1f}% (threshold: {self.thresholds['disk_usage_threshold']}%)",
                timestamp=datetime.now(),
                metadata={
                    "disk_usage_percent": disk_usage,
                    "output_dir_size_mb": system_health.get("output_dir_size_mb", 0),
                    "monitoring_dir_size_mb": system_health.get("monitoring_dir_size_mb", 0)
                }
            ))
        
        return alerts
    
    def _send_alert(self, alert: Alert):
        """Send alert using configured handlers."""
        alert_config = self.config.get("alerts", {})
        enabled_handlers = alert_config.get("handlers", ["file", "console"])
        
        # Check if alert type is enabled
        if not alert_config.get("enabled", True):
            return
        
        # Check severity filter
        min_severity = alert_config.get("min_severity", "info")
        severity_levels = {"info": 0, "warning": 1, "critical": 2}
        
        if severity_levels.get(alert.severity, 0) < severity_levels.get(min_severity, 0):
            return
        
        # Send using enabled handlers
        for handler_name in enabled_handlers:
            if handler_name in self.handlers:
                try:
                    self.handlers[handler_name](alert)
                except Exception as e:
                    print(f"Alert handler '{handler_name}' failed: {e}")
    
    def _send_email(self, alert: Alert):
        """Send alert via email."""
        email_config = self.config.get("alerts", {}).get("email", {})
        
        if not email_config.get("enabled", False):
            return
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = email_config['smtp_user']
            msg['To'] = ', '.join(email_config['recipients'])
            msg['Subject'] = f"[WeQuo Alert] {alert.title}"
            
            # Create body
            body = f"""
WeQuo Alert: {alert.title}

Severity: {alert.severity.upper()}
Time: {alert.timestamp}
Type: {alert.alert_type.value}

Message:
{alert.message}

Metadata:
{json.dumps(alert.metadata, indent=2, default=str)}
"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(email_config['smtp_host'], email_config.get('smtp_port', 587))
            server.starttls()
            server.login(email_config['smtp_user'], email_config['smtp_password'])
            server.send_message(msg)
            server.quit()
            
        except Exception as e:
            print(f"Failed to send email alert: {e}")
    
    def _write_to_file(self, alert: Alert):
        """Write alert to file."""
        alert_file = self.alerts_dir / f"alerts_{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        
        with open(alert_file, 'a') as f:
            f.write(json.dumps(alert.to_dict()) + '\n')
    
    def _send_webhook(self, alert: Alert):
        """Send alert via webhook."""
        webhook_config = self.config.get("alerts", {}).get("webhook", {})
        
        if not webhook_config.get("enabled", False):
            return
        
        try:
            import requests
            
            payload = {
                "alert": alert.to_dict(),
                "webhook_type": "wequo_alert"
            }
            
            response = requests.post(
                webhook_config['url'],
                json=payload,
                headers=webhook_config.get('headers', {}),
                timeout=10
            )
            response.raise_for_status()
            
        except Exception as e:
            print(f"Failed to send webhook alert: {e}")
    
    def _print_console(self, alert: Alert):
        """Print alert to console."""
        print(f"\n🚨 ALERT [{alert.severity.upper()}]: {alert.title}")
        print(f"   Time: {alert.timestamp}")
        print(f"   Type: {alert.alert_type.value}")
        print(f"   Message: {alert.message}")
        if alert.metadata:
            print(f"   Details: {json.dumps(alert.metadata, indent=6, default=str)}")
        print()
    
    def get_recent_alerts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get alerts from the last N hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        alerts = []
        
        # Read recent alert files
        for alert_file in self.alerts_dir.glob("alerts_*.jsonl"):
            try:
                with open(alert_file, 'r') as f:
                    for line in f:
                        alert_data = json.loads(line)
                        alert_time = datetime.fromisoformat(alert_data['timestamp'])
                        
                        if alert_time >= cutoff_time:
                            alerts.append(alert_data)
            except Exception:
                continue
        
        # Sort by timestamp
        alerts.sort(key=lambda x: x['timestamp'], reverse=True)
        return alerts
