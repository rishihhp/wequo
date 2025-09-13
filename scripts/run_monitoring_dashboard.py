#!/usr/bin/env python3
"""Run the WeQuo monitoring dashboard."""

import sys
import yaml
from pathlib import Path
from dotenv import load_dotenv

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from wequo.monitoring.core import MonitoringEngine
from wequo.monitoring.alerts import AlertManager
from wequo.monitoring.sla import SLATracker
from wequo.monitoring.dashboard import MonitoringDashboard


def main():
    """Run the monitoring dashboard."""
    load_dotenv()
    
    # Load configuration
    config_path = Path(__file__).parent.parent / "src" / "wequo" / "config.yml"
    with open(config_path, "r") as fh:
        cfg = yaml.safe_load(fh)
    
    # Initialize monitoring components
    output_root = Path(cfg["run"]["output_root"]).resolve()
    monitoring_config = cfg.get("monitoring", {})
    
    monitoring_engine = MonitoringEngine(monitoring_config, output_root)
    alert_manager = AlertManager(monitoring_config, monitoring_engine.monitoring_dir)
    sla_tracker = SLATracker(monitoring_engine, monitoring_config)
    
    # Create and run dashboard
    dashboard = MonitoringDashboard(monitoring_engine, alert_manager, sla_tracker)
    
    print("Starting WeQuo Monitoring Dashboard...")
    print("Dashboard will be available at: http://localhost:5001")
    print("Press Ctrl+C to stop")
    
    try:
        dashboard.run(host="0.0.0.0", port=5001, debug=False)
    except KeyboardInterrupt:
        print("\nShutting down monitoring dashboard...")


if __name__ == "__main__":
    main()
