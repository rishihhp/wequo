"""
Core monitoring functionality for WeQuo pipeline.
"""

import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

import pandas as pd
import yaml


@dataclass
class MonitoringMetrics:
    """Container for monitoring metrics."""
    timestamp: str
    uptime_status: str  # "healthy", "degraded", "down"
    data_freshness_hours: float
    anomaly_rate: float
    total_data_points: int
    connector_status: Dict[str, str]
    last_successful_run: Optional[str]
    error_count: int
    warning_count: int


class WeQuoMonitor:
    """
    Main monitoring class for WeQuo pipeline.
    
    Tracks:
    - Pipeline uptime and health
    - Data freshness (last successful ingestion)
    - Anomaly detection rates
    - Connector status
    - Error and warning counts
    """
    
    def __init__(self, config_path: str = "src/wequo/config.yml", 
                 output_root: str = "data/output"):
        self.config_path = Path(config_path)
        self.output_root = Path(output_root)
        self.metrics_file = self.output_root / "monitoring_metrics.json"
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Load configuration
        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)
    
    def collect_metrics(self) -> MonitoringMetrics:
        """Collect all monitoring metrics."""
        timestamp = datetime.now().isoformat()
        
        # Check uptime status
        uptime_status = self._check_uptime_status()
        
        # Check data freshness
        data_freshness_hours = self._check_data_freshness()
        
        # Check anomaly rates
        anomaly_rate = self._check_anomaly_rate()
        
        # Count total data points
        total_data_points = self._count_data_points()
        
        # Check connector status
        connector_status = self._check_connector_status()
        
        # Get last successful run
        last_successful_run = self._get_last_successful_run()
        
        # Count errors and warnings
        error_count, warning_count = self._count_errors_warnings()
        
        return MonitoringMetrics(
            timestamp=timestamp,
            uptime_status=uptime_status,
            data_freshness_hours=data_freshness_hours,
            anomaly_rate=anomaly_rate,
            total_data_points=total_data_points,
            connector_status=connector_status,
            last_successful_run=last_successful_run,
            error_count=error_count,
            warning_count=warning_count
        )
    
    def _check_uptime_status(self) -> str:
        """Check overall pipeline uptime status."""
        try:
            # Check if we have recent data
            latest_date = self._get_latest_data_date()
            if not latest_date:
                return "down"
            
            # Check if data is fresh (within last 25 hours for daily pipeline)
            hours_old = (datetime.now() - latest_date).total_seconds() / 3600
            if hours_old > 25:
                return "down"
            elif hours_old > 12:
                return "degraded"
            else:
                return "healthy"
                
        except Exception as e:
            self.logger.error(f"Error checking uptime status: {e}")
            return "down"
    
    def _check_data_freshness(self) -> float:
        """Check how fresh the data is in hours."""
        try:
            latest_date = self._get_latest_data_date()
            if not latest_date:
                return float('inf')  # No data available
            
            return (datetime.now() - latest_date).total_seconds() / 3600
            
        except Exception as e:
            self.logger.error(f"Error checking data freshness: {e}")
            return float('inf')
    
    def _check_anomaly_rate(self) -> float:
        """Check the rate of anomalies in recent data."""
        try:
            # Look for recent analytics data
            recent_dirs = sorted([d for d in self.output_root.iterdir() 
                                if d.is_dir() and d.name.startswith('2025-')], 
                               reverse=True)
            
            if not recent_dirs:
                return 0.0
            
            latest_dir = recent_dirs[0]
            analytics_file = latest_dir / "analytics_summary.json"
            
            if not analytics_file.exists():
                return 0.0
            
            with open(analytics_file, 'r') as f:
                analytics = json.load(f)
            
            # Calculate anomaly rate from analytics
            total_series = analytics.get('summary_stats', {}).get('total_series', 0)
            anomalies_list = analytics.get('anomalies', [])
            anomaly_count = len(anomalies_list) if isinstance(anomalies_list, list) else 0
            
            if total_series == 0:
                return 0.0
            
            return anomaly_count / total_series
            
        except Exception as e:
            self.logger.error(f"Error checking anomaly rate: {e}")
            return 0.0
    
    def _count_data_points(self) -> int:
        """Count total data points across all sources."""
        try:
            recent_dirs = sorted([d for d in self.output_root.iterdir() 
                                if d.is_dir() and d.name.startswith('2025-')], 
                               reverse=True)
            
            if not recent_dirs:
                return 0
            
            latest_dir = recent_dirs[0]
            total_points = 0
            
            # Count data points from CSV files
            for csv_file in latest_dir.glob("*.csv"):
                try:
                    df = pd.read_csv(csv_file)
                    total_points += len(df)
                except Exception as e:
                    self.logger.warning(f"Error reading {csv_file}: {e}")
            
            return total_points
            
        except Exception as e:
            self.logger.error(f"Error counting data points: {e}")
            return 0
    
    def _check_connector_status(self) -> Dict[str, str]:
        """Check status of each connector."""
        status = {}
        
        try:
            recent_dirs = sorted([d for d in self.output_root.iterdir() 
                                if d.is_dir() and d.name.startswith('2025-')], 
                               reverse=True)
            
            if not recent_dirs:
                # No data available
                for connector in self.config.get('connectors', {}):
                    status[connector] = "no_data"
                return status
            
            latest_dir = recent_dirs[0]
            
            # Check each connector
            for connector_name, connector_config in self.config.get('connectors', {}).items():
                if not connector_config.get('enabled', False):
                    status[connector_name] = "disabled"
                    continue
                
                # Check if data file exists and has recent data
                data_file = latest_dir / f"{connector_name}.csv"
                if not data_file.exists():
                    status[connector_name] = "no_data"
                    continue
                
                try:
                    df = pd.read_csv(data_file)
                    if len(df) == 0:
                        status[connector_name] = "empty_data"
                    else:
                        # Check if data is recent (within last 2 days)
                        df['date'] = pd.to_datetime(df['date'])
                        latest_data_date = df['date'].max()
                        hours_old = (datetime.now() - latest_data_date).total_seconds() / 3600
                        
                        if hours_old > 48:
                            status[connector_name] = "stale_data"
                        else:
                            status[connector_name] = "healthy"
                            
                except Exception as e:
                    self.logger.warning(f"Error checking {connector_name}: {e}")
                    status[connector_name] = "error"
            
            return status
            
        except Exception as e:
            self.logger.error(f"Error checking connector status: {e}")
            return {connector: "error" for connector in self.config.get('connectors', {})}
    
    def _get_latest_data_date(self) -> Optional[datetime]:
        """Get the date of the most recent data."""
        try:
            recent_dirs = sorted([d for d in self.output_root.iterdir() 
                                if d.is_dir() and d.name.startswith('2025-')], 
                               reverse=True)
            
            if not recent_dirs:
                return None
            
            latest_dir = recent_dirs[0]
            
            # Try to parse the directory name as a date
            try:
                return datetime.strptime(latest_dir.name, '%Y-%m-%d')
            except ValueError:
                # If directory name is not a date, look for the most recent CSV
                latest_date = None
                for csv_file in latest_dir.glob("*.csv"):
                    try:
                        df = pd.read_csv(csv_file)
                        if 'date' in df.columns:
                            df['date'] = pd.to_datetime(df['date'])
                            file_latest = df['date'].max()
                            if latest_date is None or file_latest > latest_date:
                                latest_date = file_latest
                    except Exception:
                        continue
                
                return latest_date
                
        except Exception as e:
            self.logger.error(f"Error getting latest data date: {e}")
            return None
    
    def _get_last_successful_run(self) -> Optional[str]:
        """Get timestamp of last successful pipeline run."""
        try:
            recent_dirs = sorted([d for d in self.output_root.iterdir() 
                                if d.is_dir() and d.name.startswith('2025-')], 
                               reverse=True)
            
            if not recent_dirs:
                return None
            
            latest_dir = recent_dirs[0]
            
            # Check for package summary (indicates successful run)
            package_summary = latest_dir / "package_summary.json"
            if package_summary.exists():
                return latest_dir.name  # Use directory name as timestamp
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting last successful run: {e}")
            return None
    
    def _count_errors_warnings(self) -> tuple[int, int]:
        """Count errors and warnings from recent runs."""
        try:
            recent_dirs = sorted([d for d in self.output_root.iterdir() 
                                if d.is_dir() and d.name.startswith('2025-')], 
                               reverse=True)
            
            if not recent_dirs:
                return 0, 0
            
            latest_dir = recent_dirs[0]
            error_count = 0
            warning_count = 0
            
            # Check QA report for errors/warnings
            qa_report = latest_dir / "qa_report.md"
            if qa_report.exists():
                with open(qa_report, 'r') as f:
                    content = f.read().lower()
                    error_count += content.count('error')
                    warning_count += content.count('warning')
            
            return error_count, warning_count
            
        except Exception as e:
            self.logger.error(f"Error counting errors/warnings: {e}")
            return 0, 0
    
    def save_metrics(self, metrics: MonitoringMetrics) -> None:
        """Save metrics to file."""
        try:
            # Ensure output directory exists
            self.output_root.mkdir(parents=True, exist_ok=True)
            
            # Load existing metrics
            existing_metrics = []
            if self.metrics_file.exists():
                with open(self.metrics_file, 'r') as f:
                    existing_metrics = json.load(f)
            
            # Add new metrics
            existing_metrics.append(asdict(metrics))
            
            # Keep only last 100 entries
            if len(existing_metrics) > 100:
                existing_metrics = existing_metrics[-100:]
            
            # Save updated metrics
            with open(self.metrics_file, 'w') as f:
                json.dump(existing_metrics, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving metrics: {e}")
    
    def get_metrics_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get metrics history for the last N hours."""
        try:
            if not self.metrics_file.exists():
                return []
            
            with open(self.metrics_file, 'r') as f:
                all_metrics = json.load(f)
            
            # Filter by time
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_metrics = []
            
            for metric in all_metrics:
                try:
                    metric_time = datetime.fromisoformat(metric['timestamp'])
                    if metric_time >= cutoff_time:
                        recent_metrics.append(metric)
                except (ValueError, KeyError):
                    continue
            
            return recent_metrics
            
        except Exception as e:
            self.logger.error(f"Error getting metrics history: {e}")
            return []
    
    def run_monitoring_cycle(self) -> MonitoringMetrics:
        """Run a complete monitoring cycle."""
        self.logger.info("Starting monitoring cycle...")
        
        # Collect metrics
        metrics = self.collect_metrics()
        
        # Save metrics
        self.save_metrics(metrics)
        
        # Log summary
        self.logger.info(f"Monitoring cycle complete:")
        self.logger.info(f"  Status: {metrics.uptime_status}")
        self.logger.info(f"  Data freshness: {metrics.data_freshness_hours:.1f} hours")
        self.logger.info(f"  Anomaly rate: {metrics.anomaly_rate:.2%}")
        self.logger.info(f"  Data points: {metrics.total_data_points}")
        self.logger.info(f"  Errors: {metrics.error_count}, Warnings: {metrics.warning_count}")
        
        return metrics
