"""
Metrics collection and analysis for WeQuo monitoring.
"""

import json
import logging
import statistics
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

import pandas as pd


@dataclass
class PerformanceMetrics:
    """Performance metrics for a time period."""
    period_start: str
    period_end: str
    avg_response_time_ms: float
    max_response_time_ms: float
    min_response_time_ms: float
    success_rate: float
    error_count: int
    total_requests: int
    uptime_percentage: float


@dataclass
class TrendAnalysis:
    """Trend analysis results."""
    metric_name: str
    trend_direction: str  # "increasing", "decreasing", "stable"
    change_percentage: float
    significance: str  # "high", "medium", "low"
    data_points: int


class MetricsCollector:
    """
    Collects and analyzes metrics for WeQuo monitoring.
    
    Features:
    - Performance trend analysis
    - Anomaly detection in metrics
    - Historical data analysis
    - Statistical summaries
    """
    
    def __init__(self, output_root: str = "data/output"):
        self.output_root = Path(output_root)
        self.metrics_file = self.output_root / "monitoring_metrics.json"
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
    
    def _load_metrics_history(self) -> List[Dict[str, Any]]:
        """Load metrics history from file."""
        try:
            if self.metrics_file.exists():
                with open(self.metrics_file, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            self.logger.error(f"Error loading metrics history: {e}")
            return []
    
    def get_performance_metrics(self, hours: int = 24) -> PerformanceMetrics:
        """Calculate performance metrics for the specified time period."""
        try:
            metrics_history = self._load_metrics_history()
            
            if not metrics_history:
                return PerformanceMetrics(
                    period_start=datetime.now().isoformat(),
                    period_end=datetime.now().isoformat(),
                    avg_response_time_ms=0.0,
                    max_response_time_ms=0.0,
                    min_response_time_ms=0.0,
                    success_rate=0.0,
                    error_count=0,
                    total_requests=0,
                    uptime_percentage=0.0
                )
            
            # Filter by time period
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_metrics = []
            
            for metric in metrics_history:
                try:
                    metric_time = datetime.fromisoformat(metric['timestamp'])
                    if metric_time >= cutoff_time:
                        recent_metrics.append(metric)
                except (ValueError, KeyError):
                    continue
            
            if not recent_metrics:
                return PerformanceMetrics(
                    period_start=cutoff_time.isoformat(),
                    period_end=datetime.now().isoformat(),
                    avg_response_time_ms=0.0,
                    max_response_time_ms=0.0,
                    min_response_time_ms=0.0,
                    success_rate=0.0,
                    error_count=0,
                    total_requests=0,
                    uptime_percentage=0.0
                )
            
            # Calculate performance metrics
            uptime_statuses = [m.get('uptime_status', 'down') for m in recent_metrics]
            error_counts = [m.get('error_count', 0) for m in recent_metrics]
            warning_counts = [m.get('warning_count', 0) for m in recent_metrics]
            
            # Calculate uptime percentage
            healthy_count = sum(1 for status in uptime_statuses if status == 'healthy')
            uptime_percentage = (healthy_count / len(uptime_statuses)) * 100 if uptime_statuses else 0
            
            # Calculate success rate (based on error count)
            total_errors = sum(error_counts)
            total_warnings = sum(warning_counts)
            total_issues = total_errors + total_warnings
            total_checks = len(recent_metrics)
            success_rate = ((total_checks - total_issues) / total_checks * 100) if total_checks > 0 else 0
            
            # For response time, we'll use data freshness as a proxy
            # (since we don't have actual response times in our current metrics)
            data_freshness_values = [m.get('data_freshness_hours', 0) for m in recent_metrics 
                                   if m.get('data_freshness_hours') is not None]
            
            if data_freshness_values:
                avg_response_time_ms = statistics.mean(data_freshness_values) * 1000  # Convert to ms
                max_response_time_ms = max(data_freshness_values) * 1000
                min_response_time_ms = min(data_freshness_values) * 1000
            else:
                avg_response_time_ms = 0.0
                max_response_time_ms = 0.0
                min_response_time_ms = 0.0
            
            return PerformanceMetrics(
                period_start=cutoff_time.isoformat(),
                period_end=datetime.now().isoformat(),
                avg_response_time_ms=avg_response_time_ms,
                max_response_time_ms=max_response_time_ms,
                min_response_time_ms=min_response_time_ms,
                success_rate=success_rate,
                error_count=total_errors,
                total_requests=total_checks,
                uptime_percentage=uptime_percentage
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating performance metrics: {e}")
            return PerformanceMetrics(
                period_start=datetime.now().isoformat(),
                period_end=datetime.now().isoformat(),
                avg_response_time_ms=0.0,
                max_response_time_ms=0.0,
                min_response_time_ms=0.0,
                success_rate=0.0,
                error_count=0,
                total_requests=0,
                uptime_percentage=0.0
            )
    
    def analyze_trends(self, hours: int = 24) -> List[TrendAnalysis]:
        """Analyze trends in key metrics."""
        try:
            metrics_history = self._load_metrics_history()
            
            if len(metrics_history) < 2:
                return []
            
            # Filter by time period
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_metrics = []
            
            for metric in metrics_history:
                try:
                    metric_time = datetime.fromisoformat(metric['timestamp'])
                    if metric_time >= cutoff_time:
                        recent_metrics.append(metric)
                except (ValueError, KeyError):
                    continue
            
            if len(recent_metrics) < 2:
                return []
            
            # Sort by timestamp
            recent_metrics.sort(key=lambda x: x['timestamp'])
            
            trends = []
            
            # Analyze data freshness trend
            freshness_values = [m.get('data_freshness_hours', 0) for m in recent_metrics 
                              if m.get('data_freshness_hours') is not None]
            if len(freshness_values) >= 2:
                trend = self._calculate_trend(freshness_values, "data_freshness_hours")
                if trend:
                    trends.append(trend)
            
            # Analyze anomaly rate trend
            anomaly_values = [m.get('anomaly_rate', 0) for m in recent_metrics 
                            if m.get('anomaly_rate') is not None]
            if len(anomaly_values) >= 2:
                trend = self._calculate_trend(anomaly_values, "anomaly_rate")
                if trend:
                    trends.append(trend)
            
            # Analyze data points trend
            data_points_values = [m.get('total_data_points', 0) for m in recent_metrics 
                                if m.get('total_data_points') is not None]
            if len(data_points_values) >= 2:
                trend = self._calculate_trend(data_points_values, "total_data_points")
                if trend:
                    trends.append(trend)
            
            return trends
            
        except Exception as e:
            self.logger.error(f"Error analyzing trends: {e}")
            return []
    
    def _calculate_trend(self, values: List[float], metric_name: str) -> Optional[TrendAnalysis]:
        """Calculate trend for a list of values."""
        try:
            if len(values) < 2:
                return None
            
            # Simple linear trend calculation
            n = len(values)
            x_values = list(range(n))
            
            # Calculate slope using least squares
            x_mean = statistics.mean(x_values)
            y_mean = statistics.mean(values)
            
            numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, values))
            denominator = sum((x - x_mean) ** 2 for x in x_values)
            
            if denominator == 0:
                return None
            
            slope = numerator / denominator
            
            # Calculate change percentage
            first_value = values[0]
            last_value = values[-1]
            
            if first_value == 0:
                change_percentage = 0.0
            else:
                change_percentage = ((last_value - first_value) / first_value) * 100
            
            # Determine trend direction
            if abs(slope) < 0.01:  # Very small slope
                trend_direction = "stable"
            elif slope > 0:
                trend_direction = "increasing"
            else:
                trend_direction = "decreasing"
            
            # Determine significance
            if abs(change_percentage) > 20:
                significance = "high"
            elif abs(change_percentage) > 10:
                significance = "medium"
            else:
                significance = "low"
            
            return TrendAnalysis(
                metric_name=metric_name,
                trend_direction=trend_direction,
                change_percentage=change_percentage,
                significance=significance,
                data_points=n
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating trend for {metric_name}: {e}")
            return None
    
    def detect_anomalies(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Detect anomalies in metrics data."""
        try:
            metrics_history = self._load_metrics_history()
            
            if len(metrics_history) < 10:  # Need enough data for anomaly detection
                return []
            
            # Filter by time period
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_metrics = []
            
            for metric in metrics_history:
                try:
                    metric_time = datetime.fromisoformat(metric['timestamp'])
                    if metric_time >= cutoff_time:
                        recent_metrics.append(metric)
                except (ValueError, KeyError):
                    continue
            
            if len(recent_metrics) < 5:
                return []
            
            anomalies = []
            
            # Check for anomalies in data freshness
            freshness_values = [m.get('data_freshness_hours', 0) for m in recent_metrics 
                              if m.get('data_freshness_hours') is not None]
            if len(freshness_values) >= 5:
                freshness_anomalies = self._detect_statistical_anomalies(
                    freshness_values, "data_freshness_hours", recent_metrics
                )
                anomalies.extend(freshness_anomalies)
            
            # Check for anomalies in anomaly rate
            anomaly_values = [m.get('anomaly_rate', 0) for m in recent_metrics 
                            if m.get('anomaly_rate') is not None]
            if len(anomaly_values) >= 5:
                rate_anomalies = self._detect_statistical_anomalies(
                    anomaly_values, "anomaly_rate", recent_metrics
                )
                anomalies.extend(rate_anomalies)
            
            # Check for anomalies in data points
            data_points_values = [m.get('total_data_points', 0) for m in recent_metrics 
                                if m.get('total_data_points') is not None]
            if len(data_points_values) >= 5:
                points_anomalies = self._detect_statistical_anomalies(
                    data_points_values, "total_data_points", recent_metrics
                )
                anomalies.extend(points_anomalies)
            
            return anomalies
            
        except Exception as e:
            self.logger.error(f"Error detecting anomalies: {e}")
            return []
    
    def _detect_statistical_anomalies(self, values: List[float], metric_name: str, 
                                    metrics_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect statistical anomalies using Z-score method."""
        try:
            if len(values) < 5:
                return []
            
            # Calculate mean and standard deviation
            mean_val = statistics.mean(values)
            std_val = statistics.stdev(values) if len(values) > 1 else 0
            
            if std_val == 0:
                return []
            
            anomalies = []
            
            # Check each value for anomalies (Z-score > 2)
            for i, value in enumerate(values):
                z_score = abs((value - mean_val) / std_val)
                
                if z_score > 2.0:  # Statistical anomaly threshold
                    anomaly = {
                        "metric_name": metric_name,
                        "timestamp": metrics_data[i]['timestamp'],
                        "value": value,
                        "mean": mean_val,
                        "std_dev": std_val,
                        "z_score": z_score,
                        "severity": "high" if z_score > 3.0 else "medium"
                    }
                    anomalies.append(anomaly)
            
            return anomalies
            
        except Exception as e:
            self.logger.error(f"Error detecting statistical anomalies for {metric_name}: {e}")
            return []
    
    def generate_metrics_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate a comprehensive metrics report."""
        try:
            performance_metrics = self.get_performance_metrics(hours)
            trends = self.analyze_trends(hours)
            anomalies = self.detect_anomalies(hours)
            
            return {
                "report_timestamp": datetime.now().isoformat(),
                "period_hours": hours,
                "performance": asdict(performance_metrics),
                "trends": [asdict(trend) for trend in trends],
                "anomalies": anomalies,
                "summary": {
                    "total_trends": len(trends),
                    "total_anomalies": len(anomalies),
                    "high_severity_anomalies": len([a for a in anomalies if a.get('severity') == 'high']),
                    "uptime_percentage": performance_metrics.uptime_percentage,
                    "success_rate": performance_metrics.success_rate
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error generating metrics report: {e}")
            return {
                "report_timestamp": datetime.now().isoformat(),
                "period_hours": hours,
                "error": str(e)
            }
