#!/usr/bin/env python3
"""
WeQuo Alerting System Setup Script

This script helps configure and test the alerting system for WeQuo.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from wequo.monitoring.alerts import AlertManager, Alert
from wequo.monitoring.core import WeQuoMonitor
from wequo.utils.logging import get_logger


def test_slack_webhook(webhook_url: str) -> bool:
    """Test Slack webhook connectivity."""
    import requests
    
    try:
        payload = {
            "text": "🧪 WeQuo Alerting System Test",
            "attachments": [
                {
                    "color": "good",
                    "title": "Test Alert",
                    "text": "This is a test message from WeQuo monitoring system.",
                    "footer": "WeQuo Monitoring",
                    "ts": 1234567890
                }
            ]
        }
        
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        return True
        
    except Exception as e:
        print(f"❌ Slack webhook test failed: {e}")
        return False


def test_email_config(smtp_config: Dict[str, Any]) -> bool:
    """Test email configuration."""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    try:
        # Create test email
        msg = MIMEMultipart()
        msg['From'] = smtp_config['from_address']
        msg['To'] = smtp_config['to_addresses'][0]  # Test with first address
        msg['Subject'] = "WeQuo Alerting System Test"
        
        body = """
WeQuo Alerting System Test

This is a test message to verify email alerting configuration.

If you receive this message, your email alerts are working correctly.

---
WeQuo Monitoring System
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        server = smtplib.SMTP(smtp_config['smtp_server'], smtp_config['smtp_port'])
        server.starttls()
        server.login(smtp_config['username'], smtp_config['password'])
        server.send_message(msg)
        server.quit()
        
        return True
        
    except Exception as e:
        print(f"❌ Email test failed: {e}")
        return False


def test_webhook_config(webhook_config: Dict[str, Any]) -> bool:
    """Test webhook configuration."""
    import requests
    
    try:
        payload = {
            "test": True,
            "message": "WeQuo Alerting System Test",
            "timestamp": "2025-09-12T16:00:00Z",
            "source": "wequo_monitoring"
        }
        
        headers = webhook_config.get('headers', {})
        response = requests.post(webhook_config['url'], json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        return True
        
    except Exception as e:
        print(f"❌ Webhook test failed: {e}")
        return False


def load_environment_config() -> Dict[str, Any]:
    """Load alerting configuration from environment variables."""
    config = {
        'slack': {
            'enabled': bool(os.environ.get('SLACK_WEBHOOK_URL')),
            'webhook_url': os.environ.get('SLACK_WEBHOOK_URL', '')
        },
        'email': {
            'enabled': bool(os.environ.get('SMTP_USERNAME') and os.environ.get('SMTP_PASSWORD')),
            'smtp_server': os.environ.get('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.environ.get('SMTP_PORT', '587')),
            'username': os.environ.get('SMTP_USERNAME', ''),
            'password': os.environ.get('SMTP_PASSWORD', ''),
            'from_address': os.environ.get('EMAIL_FROM', ''),
            'to_addresses': [addr.strip() for addr in os.environ.get('EMAIL_TO', '').split(',') if addr.strip()]
        },
        'webhook': {
            'enabled': bool(os.environ.get('WEBHOOK_URL')),
            'url': os.environ.get('WEBHOOK_URL', ''),
            'headers': json.loads(os.environ.get('WEBHOOK_HEADERS', '{}'))
        }
    }
    
    return config


def update_config_file(config: Dict[str, Any]) -> None:
    """Update the config.yml file with alerting configuration."""
    import yaml
    
    config_path = Path("src/wequo/config.yml")
    
    # Load existing config
    with open(config_path, 'r') as f:
        existing_config = yaml.safe_load(f)
    
    # Update monitoring section
    if 'monitoring' not in existing_config:
        existing_config['monitoring'] = {}
    
    existing_config['monitoring']['alerts'] = config
    
    # Write updated config
    with open(config_path, 'w') as f:
        yaml.dump(existing_config, f, default_flow_style=False, indent=2)
    
    print("✅ Updated config.yml with alerting configuration")


def test_alert_system() -> None:
    """Test the complete alerting system."""
    print("🧪 Testing WeQuo Alerting System...")
    
    # Create test alert
    test_alert = Alert(
        rule_name="test_alert",
        severity="medium",
        message="This is a test alert from WeQuo monitoring system",
        timestamp="2025-09-12T16:00:00Z",
        details={
            "test": True,
            "component": "alerting_system",
            "purpose": "configuration_test"
        }
    )
    
    # Initialize alert manager
    alert_manager = AlertManager()
    
    # Send test alert
    success = alert_manager.send_alert(test_alert)
    
    if success:
        print("✅ Alert system test completed successfully")
    else:
        print("❌ Alert system test failed - check configuration")


def main():
    """Main setup function."""
    parser = argparse.ArgumentParser(description="Setup WeQuo Alerting System")
    parser.add_argument("--test", action="store_true", help="Test alerting configuration")
    parser.add_argument("--setup", action="store_true", help="Setup alerting from environment variables")
    parser.add_argument("--slack", help="Test Slack webhook URL")
    parser.add_argument("--email", action="store_true", help="Test email configuration")
    parser.add_argument("--webhook", help="Test webhook URL")
    
    args = parser.parse_args()
    
    if args.setup:
        print("🔧 Setting up WeQuo Alerting System...")
        
        # Load configuration from environment
        config = load_environment_config()
        
        # Update config file
        update_config_file(config)
        
        # Test each configured channel
        if config['slack']['enabled']:
            print("📱 Testing Slack webhook...")
            if test_slack_webhook(config['slack']['webhook_url']):
                print("✅ Slack webhook test passed")
            else:
                print("❌ Slack webhook test failed")
        
        if config['email']['enabled']:
            print("📧 Testing email configuration...")
            if test_email_config(config['email']):
                print("✅ Email test passed")
            else:
                print("❌ Email test failed")
        
        if config['webhook']['enabled']:
            print("🔗 Testing webhook configuration...")
            if test_webhook_config(config['webhook']):
                print("✅ Webhook test passed")
            else:
                print("❌ Webhook test failed")
        
        print("\n🎉 Alerting system setup completed!")
        print("\nNext steps:")
        print("1. Run 'python scripts/monitor_pipeline.py' to test monitoring")
        print("2. Check your alert channels for test messages")
        print("3. Configure alert rules in src/wequo/config.yml if needed")
    
    elif args.test:
        test_alert_system()
    
    elif args.slack:
        print(f"📱 Testing Slack webhook: {args.slack}")
        if test_slack_webhook(args.slack):
            print("✅ Slack webhook test passed")
        else:
            print("❌ Slack webhook test failed")
    
    elif args.email:
        print("📧 Testing email configuration...")
        config = load_environment_config()
        if config['email']['enabled']:
            if test_email_config(config['email']):
                print("✅ Email test passed")
            else:
                print("❌ Email test failed")
        else:
            print("❌ Email configuration not found in environment variables")
    
    elif args.webhook:
        print(f"🔗 Testing webhook: {args.webhook}")
        webhook_config = {'url': args.webhook, 'headers': {}}
        if test_webhook_config(webhook_config):
            print("✅ Webhook test passed")
        else:
            print("❌ Webhook test failed")
    
    else:
        parser.print_help()
        print("\n📋 Quick Setup Guide:")
        print("1. Set environment variables in .env file:")
        print("   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL")
        print("   SMTP_USERNAME=your_email@gmail.com")
        print("   SMTP_PASSWORD=your_app_password")
        print("   EMAIL_FROM=your_email@gmail.com")
        print("   EMAIL_TO=admin@company.com")
        print("2. Run: python scripts/setup_alerts.py --setup")
        print("3. Test: python scripts/setup_alerts.py --test")


if __name__ == "__main__":
    main()
