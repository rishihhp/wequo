from __future__ import annotations
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

from .core import MonitoringEngine


@dataclass
class SLAMetric:
    """Individual SLA metric tracking."""
    
    name: str
    current_value: float
    target_threshold: float
    is_compliant: bool
    measurement_period_days: int
    last_updated: datetime


@dataclass
class SLAReport:
    """Comprehensive SLA report."""
    
    report_date: datetime
    measurement_period_days: int
    overall_compliance: bool
    compliance_score: float  # 0.0 to 1.0
    metrics: List[SLAMetric]
    violations: List[Dict[str, Any]]
    recommendations: List[str]


class SLATracker:
    """Tracks and reports on Service Level Agreement metrics."""
    
    def __init__(self, monitoring_engine: MonitoringEngine, config: Dict[str, Any]):
        self.monitoring_engine = monitoring_engine
        self.config = config
        self.sla_dir = monitoring_engine.monitoring_dir / "sla"
        self.sla_dir.mkdir(exist_ok=True)
        
        # SLA targets from config
        self.sla_targets = config.get("sla_targets", {
            "pipeline_success_rate": 0.99,     # 99% uptime
            "data_freshness_compliance": 0.95, # 95% of data fresh
            "average_runtime_minutes": 15,     # Target runtime
            "max_runtime_minutes": 30,         # Hard limit
            "anomaly_rate_threshold": 0.10,    # 10% max anomaly rate
            "connector_availability": 0.98     # 98% connector availability
        })
        
        # Compliance scoring weights
        self.metric_weights = config.get("sla_weights", {
            "pipeline_success_rate": 0.3,
            "data_freshness_compliance": 0.25,
            "average_runtime_minutes": 0.15,
            "max_runtime_minutes": 0.15,
            "anomaly_rate_threshold": 0.10,
            "connector_availability": 0.05
        })
        
        # Cache settings - generate SLA reports only every 6 hours
        self.cache_duration_hours = config.get("sla_cache_duration_hours", 6)
        self._cached_report = None
        self._cache_timestamp = None
    
    def generate_sla_report(self, measurement_period_days: int = 30, force_refresh: bool = False) -> SLAReport:
        """Generate comprehensive SLA report with caching to reduce frequency."""
        
        # Check if we have a cached report that's still valid
        if not force_refresh and self._is_cache_valid():
            return self._cached_report
        
        report_date = datetime.now()
        
        # Calculate all SLA metrics
        metrics = self._calculate_all_metrics(measurement_period_days)
        
        # Determine overall compliance
        overall_compliance = all(metric.is_compliant for metric in metrics)
        
        # Calculate weighted compliance score
        compliance_score = self._calculate_compliance_score(metrics)
        
        # Identify violations
        violations = self._identify_violations(metrics)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(metrics, violations)
        
        report = SLAReport(
            report_date=report_date,
            measurement_period_days=measurement_period_days,
            overall_compliance=overall_compliance,
            compliance_score=compliance_score,
            metrics=metrics,
            violations=violations,
            recommendations=recommendations
        )
        
        # Cache the report
        self._cached_report = report
        self._cache_timestamp = report_date
        
        # Save report
        self._save_report(report)
        
        return report
    
    def _calculate_all_metrics(self, period_days: int) -> List[SLAMetric]:
        """Calculate all SLA metrics for the given period."""
        metrics = []
        
        # Get monitoring data
        sla_status = self.monitoring_engine.get_sla_status(period_days)
        
        # Pipeline Success Rate
        success_rate_data = sla_status.get("pipeline_success_rate", {})
        metrics.append(SLAMetric(
            name="pipeline_success_rate",
            current_value=success_rate_data.get("value", 0.0),
            target_threshold=self.sla_targets["pipeline_success_rate"],
            is_compliant=success_rate_data.get("compliant", False),
            measurement_period_days=period_days,
            last_updated=datetime.now()
        ))
        
        # Data Freshness Compliance
        freshness_data = sla_status.get("data_freshness_compliance", {})
        metrics.append(SLAMetric(
            name="data_freshness_compliance",
            current_value=freshness_data.get("value", 0.0),
            target_threshold=self.sla_targets["data_freshness_compliance"],
            is_compliant=freshness_data.get("compliant", False),
            measurement_period_days=period_days,
            last_updated=datetime.now()
        ))
        
        # Average Runtime
        runtime_data = sla_status.get("average_duration_minutes", {})
        metrics.append(SLAMetric(
            name="average_runtime_minutes",
            current_value=runtime_data.get("value", 0.0),
            target_threshold=self.sla_targets["average_runtime_minutes"],
            is_compliant=runtime_data.get("value", 0.0) <= self.sla_targets["average_runtime_minutes"],
            measurement_period_days=period_days,
            last_updated=datetime.now()
        ))
        
        # Max Runtime Compliance
        max_runtime_data = sla_status.get("average_duration_minutes", {})
        metrics.append(SLAMetric(
            name="max_runtime_minutes",
            current_value=max_runtime_data.get("value", 0.0),
            target_threshold=self.sla_targets["max_runtime_minutes"],
            is_compliant=max_runtime_data.get("compliant", False),
            measurement_period_days=period_days,
            last_updated=datetime.now()
        ))
        
        # Anomaly Rate
        anomaly_data = sla_status.get("max_anomaly_rate", {})
        metrics.append(SLAMetric(
            name="anomaly_rate_threshold",
            current_value=anomaly_data.get("value", 0.0),
            target_threshold=self.sla_targets["anomaly_rate_threshold"],
            is_compliant=anomaly_data.get("compliant", False),
            measurement_period_days=period_days,
            last_updated=datetime.now()
        ))
        
        # Connector Availability
        connector_availability = self._calculate_connector_availability(period_days)
        metrics.append(SLAMetric(
            name="connector_availability",
            current_value=connector_availability,
            target_threshold=self.sla_targets["connector_availability"],
            is_compliant=connector_availability >= self.sla_targets["connector_availability"],
            measurement_period_days=period_days,
            last_updated=datetime.now()
        ))
        
        return metrics
    
    def _calculate_connector_availability(self, period_days: int) -> float:
        """Calculate overall connector availability."""
        history_file = self.monitoring_engine.monitoring_dir / "pipeline_history.jsonl"
        
        if not history_file.exists():
            return 1.0
        
        cutoff_date = datetime.now() - timedelta(days=period_days)
        total_connector_attempts = 0
        successful_connector_runs = 0
        
        try:
            with open(history_file, 'r') as f:
                for line in f:
                    run_data = json.loads(line)
                    run_timestamp = datetime.fromisoformat(run_data["timestamp"])
                    
                    if run_timestamp >= cutoff_date:
                        attempted = len(run_data.get("connectors_attempted", []))
                        succeeded = len(run_data.get("connectors_succeeded", []))
                        
                        total_connector_attempts += attempted
                        successful_connector_runs += succeeded
        except Exception:
            return 1.0
        
        if total_connector_attempts == 0:
            return 1.0
        
        return successful_connector_runs / total_connector_attempts
    
    def _calculate_compliance_score(self, metrics: List[SLAMetric]) -> float:
        """Calculate weighted compliance score."""
        weighted_score = 0.0
        total_weight = 0.0
        
        for metric in metrics:
            weight = self.metric_weights.get(metric.name, 0.0)
            if weight > 0:
                # Calculate metric score (1.0 if compliant, partial if close)
                if metric.is_compliant:
                    metric_score = 1.0
                else:
                    # Calculate partial score based on how close to target
                    if metric.name in ["average_runtime_minutes", "anomaly_rate_threshold"]:
                        # For metrics where lower is better
                        if metric.current_value > metric.target_threshold:
                            ratio = metric.target_threshold / metric.current_value
                            metric_score = max(0.0, ratio)
                        else:
                            metric_score = 1.0
                    else:
                        # For metrics where higher is better
                        ratio = metric.current_value / metric.target_threshold
                        metric_score = min(1.0, ratio)
                
                weighted_score += metric_score * weight
                total_weight += weight
        
        if total_weight == 0:
            return 1.0
        
        return weighted_score / total_weight
    
    def _identify_violations(self, metrics: List[SLAMetric]) -> List[Dict[str, Any]]:
        """Identify SLA violations and their severity."""
        violations = []
        
        for metric in metrics:
            if not metric.is_compliant:
                # Calculate severity based on how far from target
                if metric.name in ["average_runtime_minutes", "anomaly_rate_threshold"]:
                    deviation_ratio = metric.current_value / metric.target_threshold
                else:
                    deviation_ratio = metric.target_threshold / metric.current_value if metric.current_value > 0 else float('inf')
                
                if deviation_ratio > 2.0:
                    severity = "critical"
                elif deviation_ratio > 1.5:
                    severity = "major"
                else:
                    severity = "minor"
                
                violations.append({
                    "metric": metric.name,
                    "severity": severity,
                    "current_value": metric.current_value,
                    "target_threshold": metric.target_threshold,
                    "deviation_ratio": deviation_ratio,
                    "description": self._get_violation_description(metric)
                })
        
        return violations
    
    def _get_violation_description(self, metric: SLAMetric) -> str:
        """Get human-readable description of violation."""
        descriptions = {
            "pipeline_success_rate": f"Pipeline success rate is {metric.current_value:.1%}, below target of {metric.target_threshold:.1%}",
            "data_freshness_compliance": f"Data freshness compliance is {metric.current_value:.1%}, below target of {metric.target_threshold:.1%}",
            "average_runtime_minutes": f"Average runtime is {metric.current_value:.1f} minutes, above target of {metric.target_threshold} minutes",
            "max_runtime_minutes": f"Runtime exceeded maximum of {metric.target_threshold} minutes",
            "anomaly_rate_threshold": f"Anomaly rate is {metric.current_value:.1%}, above threshold of {metric.target_threshold:.1%}",
            "connector_availability": f"Connector availability is {metric.current_value:.1%}, below target of {metric.target_threshold:.1%}"
        }
        
        return descriptions.get(metric.name, f"Metric {metric.name} is not compliant")
    
    def _generate_recommendations(self, metrics: List[SLAMetric], violations: List[Dict[str, Any]]) -> List[str]:
        """Generate actionable recommendations based on SLA status."""
        recommendations = []
        
        # Check for critical violations
        critical_violations = [v for v in violations if v["severity"] == "critical"]
        if critical_violations:
            recommendations.append("🚨 URGENT: Address critical SLA violations immediately")
        
        # Specific recommendations based on metrics
        for metric in metrics:
            if not metric.is_compliant:
                recs = self._get_metric_recommendations(metric)
                recommendations.extend(recs)
        
        # General recommendations
        if len(violations) > 2:
            recommendations.append("Consider reviewing overall system architecture and capacity")
        
        # Performance optimization
        runtime_metric = next((m for m in metrics if m.name == "average_runtime_minutes"), None)
        if runtime_metric and runtime_metric.current_value > runtime_metric.target_threshold * 0.8:
            recommendations.append("Consider optimizing pipeline performance to reduce runtime")
        
        return recommendations
    
    def _get_metric_recommendations(self, metric: SLAMetric) -> List[str]:
        """Get specific recommendations for a metric."""
        recs = {
            "pipeline_success_rate": [
                "Review connector error logs and implement retries",
                "Add circuit breakers for external API calls",
                "Implement backup data sources for critical connectors"
            ],
            "data_freshness_compliance": [
                "Increase monitoring frequency for data sources",
                "Implement data source health checks",
                "Add automatic data validation and refresh triggers"
            ],
            "average_runtime_minutes": [
                "Optimize connector fetch operations",
                "Implement parallel data processing",
                "Review and optimize analytics algorithms"
            ],
            "max_runtime_minutes": [
                "Add timeout handling for connector operations",
                "Implement graceful degradation for slow sources",
                "Consider reducing lookback period for large datasets"
            ],
            "anomaly_rate_threshold": [
                "Review anomaly detection thresholds",
                "Implement data quality checks before anomaly detection",
                "Add manual review process for high anomaly periods"
            ],
            "connector_availability": [
                "Implement robust error handling and retries",
                "Add health checks for external APIs",
                "Consider backup data sources for unreliable connectors"
            ]
        }
        
        return recs.get(metric.name, [])
    
    def _save_report(self, report: SLAReport):
        """Save SLA report to file."""
        timestamp = report.report_date.strftime("%Y%m%d_%H%M%S")
        report_file = self.sla_dir / f"sla_report_{timestamp}.json"
        
        # Convert report to dictionary
        report_dict = asdict(report)
        
        # Save to file
        with open(report_file, 'w') as f:
            json.dump(report_dict, f, indent=2, default=str)
        
        # Also save as latest
        latest_file = self.sla_dir / "sla_report_latest.json"
        with open(latest_file, 'w') as f:
            json.dump(report_dict, f, indent=2, default=str)
    
    def get_sla_history(self, days: int = 90) -> List[Dict[str, Any]]:
        """Get SLA report history for the specified period."""
        cutoff_date = datetime.now() - timedelta(days=days)
        reports = []
        
        for report_file in self.sla_dir.glob("sla_report_*.json"):
            if "latest" in report_file.name:
                continue
                
            try:
                with open(report_file, 'r') as f:
                    report_data = json.load(f)
                
                report_date = datetime.fromisoformat(report_data["report_date"])
                if report_date >= cutoff_date:
                    reports.append(report_data)
            except Exception:
                continue
        
        # Sort by date
        reports.sort(key=lambda x: x["report_date"], reverse=True)
        return reports
    
    def get_compliance_trend(self, days: int = 30) -> Dict[str, List[float]]:
        """Get compliance score trend over time."""
        history = self.get_sla_history(days)
        
        trend_data = {
            "dates": [],
            "compliance_scores": [],
            "pipeline_success_rates": [],
            "freshness_compliance": []
        }
        
        for report in reversed(history):  # Oldest first for trend
            trend_data["dates"].append(report["report_date"])
            trend_data["compliance_scores"].append(report["compliance_score"])
            
            # Extract specific metrics
            for metric in report["metrics"]:
                if metric["name"] == "pipeline_success_rate":
                    trend_data["pipeline_success_rates"].append(metric["current_value"])
                elif metric["name"] == "data_freshness_compliance":
                    trend_data["freshness_compliance"].append(metric["current_value"])
        
        return trend_data
    
    def _is_cache_valid(self) -> bool:
        """Check if the cached SLA report is still valid."""
        if self._cached_report is None or self._cache_timestamp is None:
            return False
        
        # Check if cache has expired (6 hours by default)
        cache_age = datetime.now() - self._cache_timestamp
        return cache_age.total_seconds() < (self.cache_duration_hours * 3600)
    
    def clear_cache(self):
        """Clear the cached SLA report to force regeneration on next request."""
        self._cached_report = None
        self._cache_timestamp = None
