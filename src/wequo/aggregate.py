from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict
from datetime import datetime

import pandas as pd

from .utils.io import write_json, write_md
from .analytics import AnalyticsEngine


@dataclass
class Aggregator:
    outdir: Path
    analytics_enabled: bool = True

    def summarize(self, data_frames: Dict[str, pd.DataFrame]) -> dict:
        """Summarize all data frames with latest values and analytics."""
        summary: dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "sources": list(data_frames.keys()),
            "latest_values": {},
            "analytics": {}
        }
        
        # Get latest values for each source
        for source, df in data_frames.items():
            if df is not None and not df.empty:
                latest = (
                    df.dropna(subset=["value"])
                    .sort_values(["series_id", "date"])
                    .groupby("series_id")
                    .tail(1)
                )
                summary["latest_values"][source] = latest.to_dict(orient="records")
        
        # Run analytics if enabled
        if self.analytics_enabled and data_frames:
            analytics_engine = AnalyticsEngine()
            analytics_result = analytics_engine.analyze(data_frames)
            
            summary["analytics"] = {
                "top_deltas": analytics_result.top_deltas,
                "anomalies": analytics_result.anomalies,
                "trends": analytics_result.trends,
                "summary_stats": analytics_result.summary_stats
            }
            
            # Write analytics results
            analytics_engine.write_results(analytics_result, self.outdir)
        
        return summary

    def write_prefill(self, summary: dict) -> None:
        """Write prefill notes with analytics insights."""
        bullets = []
        
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
