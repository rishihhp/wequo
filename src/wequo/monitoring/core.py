from __future__ import annotations
import json
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd

from ..utils.dates import daterange_lookback


@dataclass
class PipelineRun:
    """Record of a single pipeline execution."""
    
    timestamp: datetime
    status: str  # success, failure, timeout
    duration_seconds: float
    connectors_attempted: List[str]
    connectors_succeeded: List[str]
    connectors_failed: List[str]
    data_points_collected: int
    errors: List[str]
    output_dir: str


@dataclass
class DataFreshnessCheck:
    """Result of data freshness validation."""
    
    connector: str
    latest_data_timestamp: datetime
    age_hours: float
    is_fresh: bool
    threshold_hours: float


@dataclass
class MonitoringResult:
    """Container for all monitoring results."""
    
    timestamp: datetime
    pipeline_run: Optional[PipelineRun]
    freshness_checks: List[DataFreshnessCheck]
    sla_status: Dict[str, Any]
    anomaly_rates: Dict[str, float]
    system_health: Dict[str, Any]


class MonitoringEngine:
    """Main monitoring engine for WeQuo pipeline."""
    
    def __init__(self, 
                 monitoring_config: Dict[str, Any],
                 output_root: Path):
        self.config = monitoring_config
        self.output_root = Path(output_root)
        self.monitoring_dir = self.output_root / "monitoring"
        self.monitoring_dir.mkdir(exist_ok=True)
        
        # SLA thresholds from config
        self.sla_thresholds = self.config.get("sla", {
            "pipeline_success_rate": 0.99,  # 99% of runs must succeed
            "data_freshness_hours": 25,     # Data must be < 25 hours old
            "max_pipeline_duration_minutes": 30,
            "max_anomaly_rate": 0.1         # < 10% anomaly rate
        })
    
    def start_pipeline_run(self, connectors: List[str]) -> str:
        """Start monitoring a new pipeline run."""
        run_id = f"run_{int(time.time())}"
        
        run_start = {
            "run_id": run_id,
            "start_time": datetime.now().isoformat(),
            "connectors": connectors,
            "status": "running"
        }
        
        # Save run start record
        run_file = self.monitoring_dir / f"{run_id}.json"
        with open(run_file, 'w') as f:
            json.dump(run_start, f, indent=2)
        
        return run_id
    
    def finish_pipeline_run(self,
                           run_id: str,
                           status: str,
                           connectors_succeeded: List[str],
                           connectors_failed: List[str],
                           data_points: int,
                           errors: List[str],
                           output_dir: str) -> PipelineRun:
        """Complete monitoring for a pipeline run."""
        
        run_file = self.monitoring_dir / f"{run_id}.json"
        
        # Load start record
        with open(run_file, 'r') as f:
            run_data = json.load(f)
        
        start_time = datetime.fromisoformat(run_data["start_time"])
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Create pipeline run record
        pipeline_run = PipelineRun(
            timestamp=end_time,
            status=status,
            duration_seconds=duration,
            connectors_attempted=run_data["connectors"],
            connectors_succeeded=connectors_succeeded,
            connectors_failed=connectors_failed,
            data_points_collected=data_points,
            errors=errors,
            output_dir=output_dir
        )
        
        # Update run record
        run_data.update({
            "end_time": end_time.isoformat(),
            "status": status,
            "duration_seconds": duration,
            "connectors_succeeded": connectors_succeeded,
            "connectors_failed": connectors_failed,
            "data_points_collected": data_points,
            "errors": errors,
            "output_dir": output_dir
        })
        
        with open(run_file, 'w') as f:
            json.dump(run_data, f, indent=2)
        
        # Append to run history
        self._append_to_history(pipeline_run)
        
        return pipeline_run
    
    def check_data_freshness(self, date_str: str) -> List[DataFreshnessCheck]:
        """Check freshness of data for a given date."""
        checks = []
        output_dir = self.output_root / "output" / date_str
        
        if not output_dir.exists():
            return checks
        
        threshold_hours = self.sla_thresholds["data_freshness_hours"]
        now = datetime.now()
        
        # Check each connector's data freshness
        for csv_file in output_dir.glob("*.csv"):
            if csv_file.name == "qa_report.md":
                continue
                
            connector = csv_file.stem
            
            try:
                df = pd.read_csv(csv_file)
                if df.empty or 'date' not in df.columns:
                    continue
                
                # Get latest data timestamp
                df['date'] = pd.to_datetime(df['date'])
                latest_timestamp = df['date'].max()
                
                age_hours = (now - latest_timestamp).total_seconds() / 3600
                is_fresh = age_hours <= threshold_hours
                
                checks.append(DataFreshnessCheck(
                    connector=connector,
                    latest_data_timestamp=latest_timestamp,
                    age_hours=age_hours,
                    is_fresh=is_fresh,
                    threshold_hours=threshold_hours
                ))
                
            except Exception as e:
                # Handle file read errors
                checks.append(DataFreshnessCheck(
                    connector=connector,
                    latest_data_timestamp=datetime.min,
                    age_hours=float('inf'),
                    is_fresh=False,
                    threshold_hours=threshold_hours
                ))
        
        return checks
    
    def calculate_anomaly_rates(self, lookback_days: int = 7) -> Dict[str, float]:
        """Calculate anomaly rates per connector over lookback period."""
        rates = {}
        
        start_date, end_date = daterange_lookback(lookback_days)
        current_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_datetime = datetime.strptime(end_date, "%Y-%m-%d")
        
        while current_date <= end_datetime:
            date_str = current_date.strftime("%Y-%m-%d")
            output_dir = self.output_root / "output" / date_str
            
            if output_dir.exists():
                # Check for analytics summary
                analytics_file = output_dir / "analytics_summary.json"
                if analytics_file.exists():
                    try:
                        with open(analytics_file, 'r') as f:
                            analytics_data = json.load(f)
                        
                        anomalies = analytics_data.get("anomalies", [])
                        for anomaly in anomalies:
                            source = anomaly.get("source", "unknown")
                            if source not in rates:
                                rates[source] = {"anomalies": 0, "total_points": 0}
                            rates[source]["anomalies"] += 1
                            
                        # Count total data points per source
                        for csv_file in output_dir.glob("*.csv"):
                            source = csv_file.stem
                            try:
                                df = pd.read_csv(csv_file)
                                if source not in rates:
                                    rates[source] = {"anomalies": 0, "total_points": 0}
                                rates[source]["total_points"] += len(df)
                            except:
                                pass
                                
                    except Exception:
                        pass
            
            current_date += timedelta(days=1)
        
        # Calculate rates
        anomaly_rates = {}
        for source, counts in rates.items():
            if counts["total_points"] > 0:
                anomaly_rates[source] = counts["anomalies"] / counts["total_points"]
            else:
                anomaly_rates[source] = 0.0
        
        return anomaly_rates
    
    def get_sla_status(self, lookback_days: int = 30) -> Dict[str, Any]:
        """Calculate current SLA status over lookback period."""
        
        # Get pipeline success rate
        success_rate = self._calculate_pipeline_success_rate(lookback_days)
        
        # Get freshness compliance
        freshness_compliance = self._calculate_freshness_compliance(lookback_days)
        
        # Get average pipeline duration
        avg_duration = self._calculate_average_duration(lookback_days)
        
        # Get anomaly rate status
        anomaly_rates = self.calculate_anomaly_rates(lookback_days)
        max_anomaly_rate = max(anomaly_rates.values()) if anomaly_rates else 0.0
        
        sla_status = {
            "pipeline_success_rate": {
                "value": success_rate,
                "threshold": self.sla_thresholds["pipeline_success_rate"],
                "compliant": success_rate >= self.sla_thresholds["pipeline_success_rate"]
            },
            "data_freshness_compliance": {
                "value": freshness_compliance,
                "threshold": 0.95,  # 95% of data should be fresh
                "compliant": freshness_compliance >= 0.95
            },
            "average_duration_minutes": {
                "value": avg_duration / 60,
                "threshold": self.sla_thresholds["max_pipeline_duration_minutes"],
                "compliant": avg_duration / 60 <= self.sla_thresholds["max_pipeline_duration_minutes"]
            },
            "max_anomaly_rate": {
                "value": max_anomaly_rate,
                "threshold": self.sla_thresholds["max_anomaly_rate"],
                "compliant": max_anomaly_rate <= self.sla_thresholds["max_anomaly_rate"]
            }
        }
        
        return sla_status
    
    def generate_monitoring_report(self, lookback_days: int = 7) -> MonitoringResult:
        """Generate comprehensive monitoring report."""
        
        timestamp = datetime.now()
        
        # Check current data freshness
        today = timestamp.strftime("%Y-%m-%d")
        freshness_checks = self.check_data_freshness(today)
        
        # Get SLA status
        sla_status = self.get_sla_status(lookback_days)
        
        # Calculate anomaly rates
        anomaly_rates = self.calculate_anomaly_rates(lookback_days)
        
        # System health metrics
        system_health = self._get_system_health()
        
        return MonitoringResult(
            timestamp=timestamp,
            pipeline_run=None,  # Will be populated during actual runs
            freshness_checks=freshness_checks,
            sla_status=sla_status,
            anomaly_rates=anomaly_rates,
            system_health=system_health
        )
    
    def _append_to_history(self, pipeline_run: PipelineRun):
        """Append pipeline run to history file."""
        history_file = self.monitoring_dir / "pipeline_history.jsonl"
        
        with open(history_file, 'a') as f:
            f.write(json.dumps(asdict(pipeline_run), default=str) + '\n')
    
    def _calculate_pipeline_success_rate(self, lookback_days: int) -> float:
        """Calculate pipeline success rate over lookback period."""
        history_file = self.monitoring_dir / "pipeline_history.jsonl"
        
        if not history_file.exists():
            return 1.0  # No runs yet, assume good
        
        cutoff_date = datetime.now() - timedelta(days=lookback_days)
        total_runs = 0
        successful_runs = 0
        
        try:
            with open(history_file, 'r') as f:
                for line in f:
                    run_data = json.loads(line)
                    run_timestamp = datetime.fromisoformat(run_data["timestamp"])
                    
                    if run_timestamp >= cutoff_date:
                        total_runs += 1
                        if run_data["status"] == "success":
                            successful_runs += 1
        except Exception:
            return 1.0
        
        if total_runs == 0:
            return 1.0
        
        return successful_runs / total_runs
    
    def _calculate_freshness_compliance(self, lookback_days: int) -> float:
        """Calculate data freshness compliance rate."""
        total_checks = 0
        fresh_checks = 0
        
        start_date, end_date = daterange_lookback(lookback_days)
        current_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_datetime = datetime.strptime(end_date, "%Y-%m-%d")
        
        while current_date <= end_datetime:
            date_str = current_date.strftime("%Y-%m-%d")
            freshness_checks = self.check_data_freshness(date_str)
            
            for check in freshness_checks:
                total_checks += 1
                if check.is_fresh:
                    fresh_checks += 1
            
            current_date += timedelta(days=1)
        
        if total_checks == 0:
            return 1.0
        
        return fresh_checks / total_checks
    
    def _calculate_average_duration(self, lookback_days: int) -> float:
        """Calculate average pipeline duration."""
        history_file = self.monitoring_dir / "pipeline_history.jsonl"
        
        if not history_file.exists():
            return 0.0
        
        cutoff_date = datetime.now() - timedelta(days=lookback_days)
        durations = []
        
        try:
            with open(history_file, 'r') as f:
                for line in f:
                    run_data = json.loads(line)
                    run_timestamp = datetime.fromisoformat(run_data["timestamp"])
                    
                    if run_timestamp >= cutoff_date:
                        durations.append(run_data["duration_seconds"])
        except Exception:
            return 0.0
        
        if not durations:
            return 0.0
        
        return sum(durations) / len(durations)
    
    def _get_system_health(self) -> Dict[str, Any]:
        """Get system health metrics."""
        return {
            "disk_usage_percent": self._get_disk_usage(),
            "monitoring_dir_size_mb": self._get_directory_size(self.monitoring_dir),
            "output_dir_size_mb": self._get_directory_size(self.output_root / "output"),
            "last_monitoring_check": datetime.now().isoformat()
        }
    
    def _get_disk_usage(self) -> float:
        """Get disk usage percentage for output directory."""
        try:
            import shutil
            total, used, free = shutil.disk_usage(self.output_root)
            return (used / total) * 100
        except:
            return 0.0
    
    def _get_directory_size(self, directory: Path) -> float:
        """Get directory size in MB."""
        if not directory.exists():
            return 0.0
        
        try:
            total_size = sum(f.stat().st_size for f in directory.rglob('*') if f.is_file())
            return total_size / (1024 * 1024)  # Convert to MB
        except:
            return 0.0
