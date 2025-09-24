from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from pathlib import Path

import pandas as pd
import numpy as np

from .anomaly import AnomalyDetector
from .trends import TrendAnalyzer
from .deltas import DeltaCalculator


@dataclass
class AnalyticsResult:
    """Container for analytics results."""
    
    top_deltas: List[Dict[str, Any]]
    anomalies: List[Dict[str, Any]]
    trends: List[Dict[str, Any]]
    percentiles: Dict[str, Dict[str, float]]
    summary_stats: Dict[str, Any]


class AnalyticsEngine:
    """Main analytics engine that orchestrates all analytics modules."""
    
    def __init__(self, 
                 anomaly_threshold: float = 2.0,
                 delta_threshold: float = 0.05,
                 min_data_points: int = 5):
        self.anomaly_detector = AnomalyDetector(threshold=anomaly_threshold)
        self.trend_analyzer = TrendAnalyzer()
        self.delta_calculator = DeltaCalculator(threshold=delta_threshold)
        self.min_data_points = min_data_points
    
    def analyze(self, data_frames: Dict[str, pd.DataFrame]) -> AnalyticsResult:
        """Run comprehensive analytics on all data frames."""
        
        # Combine all data for analysis
        all_data = self._combine_data(data_frames)
        
        if all_data.empty:
            return AnalyticsResult(
                top_deltas=[],
                anomalies=[],
                trends=[],
                percentiles={},
                summary_stats={}
            )
        
        # Calculate deltas
        top_deltas = self.delta_calculator.calculate_top_deltas(all_data, top_n=5)
        
        # Detect anomalies
        anomalies = self.anomaly_detector.detect_anomalies(all_data)
        
        # Analyze trends
        trends = self.trend_analyzer.analyze_trends(all_data)
        
        # Calculate percentiles
        percentiles = self._calculate_percentiles(all_data)
        
        # Summary statistics
        summary_stats = self._calculate_summary_stats(all_data)
        
        return AnalyticsResult(
            top_deltas=top_deltas,
            anomalies=anomalies,
            trends=trends,
            percentiles=percentiles,
            summary_stats=summary_stats
        )
    
    def _combine_data(self, data_frames: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Combine all data frames into a single DataFrame for analysis."""
        if not data_frames:
            return pd.DataFrame()
        
        combined = []
        for source, df in data_frames.items():
            if df.empty:
                continue
            
            df_copy = df.copy()
            df_copy["source"] = source
            combined.append(df_copy)
        
        if not combined:
            return pd.DataFrame()
        
        return pd.concat(combined, ignore_index=True)
    
    def _calculate_percentiles(self, df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """Calculate percentiles for each series."""
        percentiles = {}
        
        for series_id in df["series_id"].unique():
            series_data = df[df["series_id"] == series_id]["value"]
            if len(series_data) >= self.min_data_points:
                percentiles[series_id] = {
                    "p25": float(np.percentile(series_data, 25)),
                    "p50": float(np.median(series_data)),
                    "p75": float(np.percentile(series_data, 75)),
                    "p90": float(np.percentile(series_data, 90)),
                    "p95": float(np.percentile(series_data, 95)),
                }
        
        return percentiles
    
    def _calculate_summary_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate summary statistics."""
        if df.empty:
            return {}
        
        return {
            "total_series": int(df["series_id"].nunique()),
            "total_data_points": int(len(df)),
            "date_range": {
                "start": str(df["date"].min()),
                "end": str(df["date"].max())
            },
            "sources": list(df["source"].unique()),
            "value_stats": {
                "mean": float(df["value"].mean()),
                "std": float(df["value"].std()),
                "min": float(df["value"].min()),
                "max": float(df["value"].max())
            }
        }
    
    def write_results(self, result: AnalyticsResult, output_dir: Path) -> None:
        """Write analytics results to files."""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Write JSON summary
        import json
        summary = {
            "top_deltas": result.top_deltas,
            "anomalies": result.anomalies,
            "trends": result.trends,
            "percentiles": result.percentiles,
            "summary_stats": result.summary_stats
        }
        
        with open(output_dir / "analytics_summary.json", "w") as f:
            json.dump(summary, f, indent=2, default=str)
        
        # Write markdown report
        self._write_markdown_report(result, output_dir / "analytics_report.md")
    
    def _write_markdown_report(self, result: AnalyticsResult, output_path: Path) -> None:
        """Write a human-readable markdown report."""
        lines = ["# Analytics Report\n"]
        
        # Summary stats
        lines.append("## Summary Statistics")
        stats = result.summary_stats
        lines.append(f"- Total series: {stats.get('total_series', 0)}")
        lines.append(f"- Total data points: {stats.get('total_data_points', 0)}")
        lines.append(f"- Date range: {stats.get('date_range', {}).get('start', 'N/A')} to {stats.get('date_range', {}).get('end', 'N/A')}")
        lines.append(f"- Sources: {', '.join(stats.get('sources', []))}")
        lines.append("")
        
        # Top deltas
        if result.top_deltas:
            lines.append("## Top 5 Deltas")
            for delta in result.top_deltas:
                lines.append(f"- **{delta['series_id']}**: {delta['delta_pct']:.1%} change ({delta['old_value']:.2f} -> {delta['new_value']:.2f})")
            lines.append("")
        
        # Anomalies
        if result.anomalies:
            lines.append("## Detected Anomalies")
            for anomaly in result.anomalies:
                lines.append(f"- **{anomaly['series_id']}**: {anomaly['value']:.2f} (z-score: {anomaly['z_score']:.2f}) on {anomaly['date']}")
            lines.append("")
        
        # Trends
        if result.trends:
            lines.append("## Trend Analysis")
            for trend in result.trends:
                direction = "📈" if trend['slope'] > 0 else "📉"
                lines.append(f"- **{trend['series_id']}**: {direction} {trend['trend_strength']} trend (slope: {trend['slope']:.4f})")
            lines.append("")
        
        output_path.write_text("\n".join(lines), encoding='utf-8')
