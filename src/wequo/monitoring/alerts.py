"""
Alerting system for WeQuo monitoring.
Supports Slack, email, and webhook notifications.
"""

import json
import logging
import smtplib
import time
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

import requests


@dataclass
class AlertRule:
    """Configuration for an alert rule."""
    name: str
    condition: str  # "uptime_down", "data_stale", "anomaly_high", "connector_down"
    threshold: float
    severity: str  # "low", "medium", "high", "critical"
    enabled: bool = True
    cooldown_minutes: int = 60  # Minimum time between alerts


@dataclass
class Alert:
    """An alert instance."""
    rule_name: str
    severity: str
    message: str
    timestamp: str
    details: Dict[str, Any]
    resolved: bool = False


class AlertManager:
    """
    Manages alerting for WeQuo monitoring.
    
    Features:
    - Configurable alert rules
    - Multiple notification channels (Slack, email, webhook)
    - Alert cooldown and deduplication
    - Alert history and resolution tracking
    """
    
    def __init__(self, config_path: str = "src/wequo/config.yml",
                 output_root: str = "data/output"):
        self.config_path = Path(config_path)
        self.output_root = Path(output_root)
        self.alerts_file = self.output_root / "alerts_history.json"
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Load configuration
        import yaml
        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Default alert rules
        self.alert_rules = [
            AlertRule(
                name="pipeline_down",
                condition="uptime_down",
                threshold=0.0,
                severity="critical",
                cooldown_minutes=30
            ),
            AlertRule(
                name="data_stale",
                condition="data_stale",
                threshold=24.0,  # 24 hours
                severity="high",
                cooldown_minutes=120
            ),
            AlertRule(
                name="high_anomaly_rate",
                condition="anomaly_high",
                threshold=0.1,  # 10%
                severity="medium",
                cooldown_minutes=60
            ),
            AlertRule(
                name="connector_down",
                condition="connector_down",
                threshold=0.0,
                severity="medium",
                cooldown_minutes=60
            )
        ]
        
        # Load alert history
        self.alert_history = self._load_alert_history()
    
    def _load_alert_history(self) -> List[Dict[str, Any]]:
        """Load alert history from file."""
        try:
            if self.alerts_file.exists():
                with open(self.alerts_file, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            self.logger.error(f"Error loading alert history: {e}")
            return []
    
    def _save_alert_history(self) -> None:
        """Save alert history to file."""
        try:
            # Ensure output directory exists
            self.output_root.mkdir(parents=True, exist_ok=True)
            
            # Keep only last 1000 alerts
            if len(self.alert_history) > 1000:
                self.alert_history = self.alert_history[-1000:]
            
            with open(self.alerts_file, 'w') as f:
                json.dump(self.alert_history, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving alert history: {e}")
    
    def _should_send_alert(self, rule: AlertRule) -> bool:
        """Check if alert should be sent based on cooldown."""
        if not rule.enabled:
            return False
        
        # Find the last alert for this rule
        cutoff_time = datetime.now() - timedelta(minutes=rule.cooldown_minutes)
        
        for alert in reversed(self.alert_history):
            if (alert.get('rule_name') == rule.name and 
                not alert.get('resolved', False) and
                datetime.fromisoformat(alert['timestamp']) > cutoff_time):
                return False
        
        return True
    
    def _create_alert(self, rule: AlertRule, message: str, details: Dict[str, Any]) -> Alert:
        """Create a new alert."""
        return Alert(
            rule_name=rule.name,
            severity=rule.severity,
            message=message,
            timestamp=datetime.now().isoformat(),
            details=details
        )
    
    def _send_slack_alert(self, alert: Alert) -> bool:
        """Send alert to Slack."""
        try:
            webhook_url = self.config.get('alerts', {}).get('slack', {}).get('webhook_url')
            if not webhook_url:
                self.logger.warning("Slack webhook URL not configured")
                return False
            
            # Create Slack message
            color = {
                "low": "#36a64f",      # Green
                "medium": "#ff9500",   # Orange
                "high": "#ff0000",     # Red
                "critical": "#8b0000"  # Dark red
            }.get(alert.severity, "#ff0000")
            
            payload = {
                "attachments": [
                    {
                        "color": color,
                        "title": f"WeQuo Alert: {alert.rule_name}",
                        "text": alert.message,
                        "fields": [
                            {
                                "title": "Severity",
                                "value": alert.severity.upper(),
                                "short": True
                            },
                            {
                                "title": "Timestamp",
                                "value": alert.timestamp,
                                "short": True
                            }
                        ],
                        "footer": "WeQuo Monitoring",
                        "ts": int(time.time())
                    }
                ]
            }
            
            # Add details if available
            if alert.details:
                details_text = "\n".join([f"• {k}: {v}" for k, v in alert.details.items()])
                payload["attachments"][0]["fields"].append({
                    "title": "Details",
                    "value": details_text,
                    "short": False
                })
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            self.logger.info(f"Slack alert sent successfully: {alert.rule_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending Slack alert: {e}")
            return False
    
    def _send_email_alert(self, alert: Alert) -> bool:
        """Send alert via email."""
        try:
            email_config = self.config.get('alerts', {}).get('email', {})
            if not email_config.get('enabled', False):
                return False
            
            smtp_server = email_config.get('smtp_server')
            smtp_port = email_config.get('smtp_port', 587)
            username = email_config.get('username')
            password = email_config.get('password')
            from_addr = email_config.get('from_address')
            to_addrs = email_config.get('to_addresses', [])
            
            if not all([smtp_server, username, password, from_addr, to_addrs]):
                self.logger.warning("Email configuration incomplete")
                return False
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = from_addr
            msg['To'] = ', '.join(to_addrs)
            msg['Subject'] = f"WeQuo Alert [{alert.severity.upper()}]: {alert.rule_name}"
            
            # Create email body
            body = f"""
WeQuo Monitoring Alert

Rule: {alert.rule_name}
Severity: {alert.severity.upper()}
Timestamp: {alert.timestamp}

Message:
{alert.message}

Details:
{json.dumps(alert.details, indent=2) if alert.details else 'None'}

---
WeQuo Monitoring System
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(username, password)
            server.send_message(msg)
            server.quit()
            
            self.logger.info(f"Email alert sent successfully: {alert.rule_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending email alert: {e}")
            return False
    
    def _send_webhook_alert(self, alert: Alert) -> bool:
        """Send alert to webhook."""
        try:
            webhook_config = self.config.get('alerts', {}).get('webhook', {})
            if not webhook_config.get('enabled', False):
                return False
            
            webhook_url = webhook_config.get('url')
            if not webhook_url:
                self.logger.warning("Webhook URL not configured")
                return False
            
            # Create webhook payload
            payload = {
                "alert": asdict(alert),
                "source": "wequo_monitoring",
                "timestamp": datetime.now().isoformat()
            }
            
            headers = webhook_config.get('headers', {})
            response = requests.post(webhook_url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            
            self.logger.info(f"Webhook alert sent successfully: {alert.rule_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending webhook alert: {e}")
            return False
    
    def send_alert(self, alert: Alert) -> bool:
        """Send alert through all configured channels."""
        success = False
        
        # Send to Slack
        if self._send_slack_alert(alert):
            success = True
        
        # Send email
        if self._send_email_alert(alert):
            success = True
        
        # Send webhook
        if self._send_webhook_alert(alert):
            success = True
        
        return success
    
    def check_and_alert(self, metrics: Dict[str, Any]) -> List[Alert]:
        """Check metrics against alert rules and send alerts."""
        triggered_alerts = []
        
        for rule in self.alert_rules:
            if not rule.enabled:
                continue
            
            # Check if alert should be sent (cooldown)
            if not self._should_send_alert(rule):
                continue
            
            alert = None
            
            # Check rule conditions
            if rule.condition == "uptime_down":
                if metrics.get('uptime_status') == 'down':
                    alert = self._create_alert(
                        rule,
                        f"WeQuo pipeline is DOWN. Data freshness: {metrics.get('data_freshness_hours', 'unknown')} hours",
                        {
                            "uptime_status": metrics.get('uptime_status'),
                            "data_freshness_hours": metrics.get('data_freshness_hours'),
                            "last_successful_run": metrics.get('last_successful_run')
                        }
                    )
            
            elif rule.condition == "data_stale":
                freshness_hours = metrics.get('data_freshness_hours', 0)
                if freshness_hours > rule.threshold:
                    alert = self._create_alert(
                        rule,
                        f"Data is stale: {freshness_hours:.1f} hours old (threshold: {rule.threshold} hours)",
                        {
                            "data_freshness_hours": freshness_hours,
                            "threshold_hours": rule.threshold,
                            "last_successful_run": metrics.get('last_successful_run')
                        }
                    )
            
            elif rule.condition == "anomaly_high":
                anomaly_rate = metrics.get('anomaly_rate', 0)
                if anomaly_rate > rule.threshold:
                    alert = self._create_alert(
                        rule,
                        f"High anomaly rate detected: {anomaly_rate:.1%} (threshold: {rule.threshold:.1%})",
                        {
                            "anomaly_rate": anomaly_rate,
                            "threshold": rule.threshold,
                            "total_data_points": metrics.get('total_data_points')
                        }
                    )
            
            elif rule.condition == "connector_down":
                connector_status = metrics.get('connector_status', {})
                unhealthy_connectors = [name for name, status in connector_status.items() 
                                      if status in ['down', 'error', 'no_data']]
                if unhealthy_connectors:
                    alert = self._create_alert(
                        rule,
                        f"Unhealthy connectors detected: {', '.join(unhealthy_connectors)}",
                        {
                            "unhealthy_connectors": unhealthy_connectors,
                            "connector_status": connector_status
                        }
                    )
            
            # Send alert if created
            if alert:
                if self.send_alert(alert):
                    # Add to history
                    self.alert_history.append(asdict(alert))
                    self._save_alert_history()
                    triggered_alerts.append(alert)
                    self.logger.info(f"Alert triggered and sent: {alert.rule_name}")
                else:
                    self.logger.error(f"Failed to send alert: {alert.rule_name}")
        
        return triggered_alerts
    
    def get_alert_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get alert history for the last N hours."""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_alerts = []
            
            for alert in self.alert_history:
                try:
                    alert_time = datetime.fromisoformat(alert['timestamp'])
                    if alert_time >= cutoff_time:
                        recent_alerts.append(alert)
                except (ValueError, KeyError):
                    continue
            
            return recent_alerts
            
        except Exception as e:
            self.logger.error(f"Error getting alert history: {e}")
            return []
    
    def resolve_alert(self, rule_name: str) -> bool:
        """Mark an alert as resolved."""
        try:
            # Find the most recent unresolved alert for this rule
            for alert in reversed(self.alert_history):
                if (alert.get('rule_name') == rule_name and 
                    not alert.get('resolved', False)):
                    alert['resolved'] = True
                    alert['resolved_at'] = datetime.now().isoformat()
                    self._save_alert_history()
                    self.logger.info(f"Alert resolved: {rule_name}")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error resolving alert: {e}")
            return False
