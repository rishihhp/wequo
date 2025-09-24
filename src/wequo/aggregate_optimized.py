"""
Optimized aggregator with performance improvements for larger datasets.
"""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict
from datetime import datetime
import time
import logging

import pandas as pd

from .utils.io import write_json, write_md
from .analytics.optimized import OptimizedAnalyticsEngine


@dataclass
class OptimizedAggregator:
    """Optimized aggregator with performance improvements."""
    
    outdir: Path
    analytics_enabled: bool = True
    max_workers: int = None
    chunk_size: int = 10000
    
    def __post_init__(self):
        self.logger = logging.getLogger(__name__)
        self.analytics_engine = OptimizedAnalyticsEngine(
            max_workers=self.max_workers,
            chunk_size=self.chunk_size
        )
    
    def summarize(self, data_frames: Dict[str, pd.DataFrame]) -> dict:
        """Optimized summarization with performance tracking."""
        start_time = time.time()
        self.logger.info("Starting optimized data summarization")
        
        summary: dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "sources": list(data_frames.keys()),
            "latest_values": {},
            "analytics": {},
            "performance_metrics": {}
        }
        
        # Get latest values for each source (optimized)
        latest_start = time.time()
        for source, df in data_frames.items():
            if df is not None and not df.empty:
                latest = self._get_latest_values_optimized(df)
                summary["latest_values"][source] = latest.to_dict(orient="records")
        
        latest_time = time.time() - latest_start
        self.logger.info(f"Latest values calculated in {latest_time:.2f}s")
        
        # Run analytics if enabled
        if self.analytics_enabled and data_frames:
            analytics_start = time.time()
            analytics_result = self.analytics_engine.analyze(data_frames)
            analytics_time = time.time() - analytics_start
            
            summary["analytics"] = {
                "top_deltas": analytics_result.get("top_deltas", []),
                "anomalies": analytics_result.get("anomalies", []),
                "trends": analytics_result.get("trends", []),
                "percentiles": analytics_result.get("percentiles", {}),
                "summary_stats": analytics_result.get("summary_stats", {})
            }
            
            # Add performance metrics
            summary["performance_metrics"] = {
                "latest_values_time": latest_time,
                "analytics_time": analytics_time,
                "total_time": time.time() - start_time,
                "analytics_breakdown": analytics_result.get("performance_metrics", {})
            }
            
            # Write analytics results
            self.analytics_engine.write_results(analytics_result, self.outdir)
            
            self.logger.info(f"Analytics completed in {analytics_time:.2f}s")
        else:
            summary["performance_metrics"] = {
                "latest_values_time": latest_time,
                "analytics_time": 0.0,
                "total_time": time.time() - start_time
            }
        
        total_time = time.time() - start_time
        self.logger.info(f"Total summarization completed in {total_time:.2f}s")
        
        return summary
    
    def _get_latest_values_optimized(self, df: pd.DataFrame) -> pd.DataFrame:
        """Optimized latest values calculation."""
        if df.empty:
            return pd.DataFrame()
        
        # Use vectorized operations for better performance
        # Sort by series_id and date, then group by series_id and take the last value
        df_sorted = df.sort_values(["series_id", "date"])
        
        # Use groupby with tail(1) for better performance than drop_duplicates
        latest = (
            df_sorted
            .dropna(subset=["value"])
            .groupby("series_id")
            .tail(1)
        )
        
        return latest
    
    def write_prefill(self, summary: dict) -> None:
        """Write prefill notes with analytics insights and performance metrics."""
        bullets = []
        
        # Add performance metrics
        perf_metrics = summary.get("performance_metrics", {})
        if perf_metrics:
            total_time = perf_metrics.get("total_time", 0)
            analytics_time = perf_metrics.get("analytics_time", 0)
            bullets.append(f"**Performance**: Total processing time {total_time:.2f}s (analytics: {analytics_time:.2f}s)")
        
        # Add latest values summary
        latest_values = summary.get("latest_values", {})
        for source, values in latest_values.items():
            if values:
                bullets.append(f"**{source.upper()}**: Latest values available for {len(values)} series")
        
        # Add analytics insights
        analytics = summary.get("analytics", {})
        if analytics:
            top_deltas = analytics.get("top_deltas", [])
            if top_deltas:
                bullets.append(f"**Key Changes**: {len(top_deltas)} significant deltas detected")
                for delta in top_deltas[:3]:  # Top 3
                    bullets.append(f"  - {delta['series_id']}: {delta['delta_pct']:.1%} change ({delta['old_value']:.2f} -> {delta['new_value']:.2f})")
            
            anomalies = analytics.get("anomalies", [])
            if anomalies:
                bullets.append(f"**Anomalies**: {len(anomalies)} anomalies detected")
                for anomaly in anomalies[:2]:  # Top 2
                    bullets.append(f"  - {anomaly['series_id']}: {anomaly['value']:.2f} (z-score: {anomaly['z_score']:.2f})")
            
            trends = analytics.get("trends", [])
            if trends:
                strong_trends = [t for t in trends if t['trend_strength'] in ['strong', 'moderate']]
                if strong_trends:
                    bullets.append(f"**Trends**: {len(strong_trends)} significant trends")
                    for trend in strong_trends[:2]:  # Top 2
                        direction = "📈" if trend['slope'] > 0 else "📉"
                        bullets.append(f"  - {trend['series_id']}: {direction} {trend['trend_strength']} trend")
        
        # Add metadata
        bullets.append(f"**Data Package**: Generated at {summary.get('timestamp', 'unknown')}")
        bullets.append(f"**Sources**: {', '.join(summary.get('sources', []))}")
        
        # Join bullets into a Markdown list
        content = "\n".join([f"- {b}" for b in bullets])
        write_md(self.outdir / "prefill_notes.md", content)
        write_json(self.outdir / "package_summary.json", summary)
