#!/usr/bin/env python3
"""
WeQuo Pipeline Monitoring Script

Runs comprehensive monitoring checks and sends alerts if needed.
Can be run as a standalone script or integrated into CI/CD pipelines.
"""

import argparse
import json
import logging
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from wequo.monitoring import WeQuoMonitor, HealthChecker, AlertManager, MetricsCollector


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('monitoring.log')
        ]
    )


def main() -> int:
    """Main monitoring function."""
    parser = argparse.ArgumentParser(description="WeQuo Pipeline Monitoring")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Enable verbose logging")
    parser.add_argument("--config", "-c", default="src/wequo/config.yml",
                       help="Path to configuration file")
    parser.add_argument("--output", "-o", default="data/output",
                       help="Output directory for monitoring data")
    parser.add_argument("--no-alerts", action="store_true",
                       help="Disable alert sending")
    parser.add_argument("--health-only", action="store_true",
                       help="Run only health checks")
    parser.add_argument("--metrics-only", action="store_true",
                       help="Run only metrics collection")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Starting WeQuo pipeline monitoring...")
        
        # Initialize monitoring components
        monitor = WeQuoMonitor(args.config, args.output)
        health_checker = HealthChecker(args.config, args.output)
        alert_manager = AlertManager(args.config, args.output)
        metrics_collector = MetricsCollector(args.output)
        
        results = {}
        
        # Run monitoring cycle
        if not args.metrics_only:
            logger.info("Running monitoring cycle...")
            metrics = monitor.run_monitoring_cycle()
            results["monitoring_metrics"] = {
                "uptime_status": metrics.uptime_status,
                "data_freshness_hours": metrics.data_freshness_hours,
                "anomaly_rate": metrics.anomaly_rate,
                "total_data_points": metrics.total_data_points,
                "connector_status": metrics.connector_status,
                "error_count": metrics.error_count,
                "warning_count": metrics.warning_count
            }
        
        # Run health checks
        if not args.metrics_only:
            logger.info("Running health checks...")
            health_results = health_checker.run_health_checks()
            results["health_checks"] = health_results
        
        # Collect and analyze metrics
        if not args.health_only:
            logger.info("Collecting and analyzing metrics...")
            metrics_report = metrics_collector.generate_metrics_report()
            results["metrics_analysis"] = metrics_report
        
        # Send alerts if enabled
        if not args.no_alerts and not args.metrics_only:
            logger.info("Checking alert conditions...")
            if "monitoring_metrics" in results:
                triggered_alerts = alert_manager.check_and_alert(results["monitoring_metrics"])
                results["triggered_alerts"] = [
                    {
                        "rule_name": alert.rule_name,
                        "severity": alert.severity,
                        "message": alert.message,
                        "timestamp": alert.timestamp
                    }
                    for alert in triggered_alerts
                ]
                logger.info(f"Triggered {len(triggered_alerts)} alerts")
        
        # Save results
        output_file = Path(args.output) / "monitoring_results.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Print summary
        logger.info("Monitoring cycle completed successfully")
        
        if "monitoring_metrics" in results:
            metrics = results["monitoring_metrics"]
            logger.info(f"Status: {metrics['uptime_status']}")
            logger.info(f"Data freshness: {metrics['data_freshness_hours']:.1f} hours")
            logger.info(f"Anomaly rate: {metrics['anomaly_rate']:.2%}")
            logger.info(f"Data points: {metrics['total_data_points']}")
        
        if "health_checks" in results:
            health = results["health_checks"]
            logger.info(f"Overall health: {health['overall_status']}")
            logger.info(f"Healthy connectors: {health['connectors']['healthy']}/{health['connectors']['total']}")
        
        if "triggered_alerts" in results:
            alerts = results["triggered_alerts"]
            if alerts:
                logger.warning(f"Triggered {len(alerts)} alerts")
                for alert in alerts:
                    logger.warning(f"  - {alert['severity'].upper()}: {alert['rule_name']}")
        
        # Return appropriate exit code
        if "monitoring_metrics" in results:
            if results["monitoring_metrics"]["uptime_status"] == "down":
                return 2  # Critical
            elif results["monitoring_metrics"]["uptime_status"] == "degraded":
                return 1  # Warning
            else:
                return 0  # Success
        else:
            return 0
            
    except Exception as e:
        logger.error(f"Monitoring failed: {e}")
        return 3  # Error


if __name__ == "__main__":
    sys.exit(main())
