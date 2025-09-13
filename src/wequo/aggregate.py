from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict
from datetime import datetime

import pandas as pd

from .utils.io import write_json, write_md
from .analytics import AnalyticsEngine
from .metadata import MetadataTracker


@dataclass
class Aggregator:
    outdir: Path
    analytics_enabled: bool = True
    metadata_tracker: MetadataTracker = None

    def __post_init__(self):
        if self.metadata_tracker is None:
            self.metadata_tracker = MetadataTracker()

    def summarize(self, data_frames: Dict[str, pd.DataFrame], metadata_tracker: MetadataTracker = None) -> dict:
        """Summarize all data frames with latest values, analytics, and provenance."""
        # Use provided metadata tracker or fallback to instance tracker
        if metadata_tracker is None:
            metadata_tracker = self.metadata_tracker
            
        summary: dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "sources": list(data_frames.keys()),
            "latest_values": {},
            "analytics": {},
            "provenance": metadata_tracker.export_metadata() if metadata_tracker else {}
        }
        
        # Get latest values for each source with provenance
        for source, df in data_frames.items():
            if df is not None and not df.empty:
                latest = (
                    df.dropna(subset=["value"])
                    .sort_values(["series_id", "date"])
                    .groupby("series_id")
                    .tail(1)
                )
                
                # Add provenance metadata to latest values
                latest_with_provenance = []
                for _, row in latest.iterrows():
                    row_dict = row.to_dict()
                    
                    # Add metadata if available
                    if "metadata_id" in row_dict and metadata_tracker:
                        metadata = metadata_tracker.get_metadata(row_dict["metadata_id"])
                        if metadata:
                            row_dict["provenance"] = {
                                "timestamp": metadata.timestamp,
                                "api_endpoint": metadata.api_endpoint,
                                "source_url": metadata.source_url,
                                "fetch_duration_ms": metadata.fetch_duration_ms,
                                "confidence_score": metadata.confidence_score,
                                "validation_status": metadata.validation_status,
                                "data_license": metadata.data_license,
                                "terms_of_service_url": metadata.terms_of_service_url
                            }
                    
                    latest_with_provenance.append(row_dict)
                
                summary["latest_values"][source] = latest_with_provenance
        
        # Run analytics if enabled
        if self.analytics_enabled and data_frames:
            # Load analytics configuration from config.yml if available
            import yaml
            from pathlib import Path
            
            try:
                config_path = Path(__file__).parent / "config.yml"
                if config_path.exists():
                    with open(config_path, "r") as fh:
                        cfg = yaml.safe_load(fh)
                    analytics_config = cfg.get("analytics", {})
                else:
                    analytics_config = {}
                
                analytics_engine = AnalyticsEngine(
                    anomaly_threshold=analytics_config.get("anomaly_threshold", 2.0),
                    delta_threshold=analytics_config.get("delta_threshold", 0.05),
                    min_data_points=analytics_config.get("min_data_points", 5),
                    enable_advanced_analytics=analytics_config.get("enable_advanced_analytics", True)
                )
            except Exception:
                # Fallback to defaults if config loading fails
                analytics_engine = AnalyticsEngine(enable_advanced_analytics=True)
            
            analytics_result = analytics_engine.analyze(data_frames)
            
            summary["analytics"] = {
                "top_deltas": analytics_result.top_deltas,
                "anomalies": analytics_result.anomalies,
                "trends": analytics_result.trends,
                "summary_stats": analytics_result.summary_stats,
                "percentiles": analytics_result.percentiles,
                # Advanced analytics
                "changepoints": analytics_result.changepoints,
                "correlations": analytics_result.correlations,
                "event_impacts": analytics_result.event_impacts,
                "explanations": analytics_result.explanations
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
            
            # Advanced analytics insights
            changepoints = analytics.get("changepoints", [])
            if changepoints:
                bullets.append(f"**Change Points**: {len(changepoints)} structural changes detected")
                for cp in changepoints[:2]:  # Top 2
                    bullets.append(f"  - {cp['series_id']}: {cp['change_type']} on {cp['timestamp'][:10]}")
            
            correlations = analytics.get("correlations", [])
            if correlations:
                significant_corr = [c for c in correlations if abs(c['correlation_coefficient']) > 0.5]
                if significant_corr:
                    bullets.append(f"**Correlations**: {len(significant_corr)} strong correlations found")
                    for corr in significant_corr[:2]:  # Top 2
                        bullets.append(f"  - {corr['series1_id']} ↔ {corr['series2_id']}: {corr['correlation_coefficient']:.2f} ({corr['correlation_type']})")
            
            event_impacts = analytics.get("event_impacts", [])
            if event_impacts:
                bullets.append(f"**Event Impacts**: {len(event_impacts)} events with measurable impact")
                for event in event_impacts[:2]:  # Top 2
                    bullets.append(f"  - {event['event_id']}: {event['impact_type']} impact on {event['series_id']}")
            
            explanations = analytics.get("explanations", [])
            if explanations:
                bullets.append(f"**Insights**: {len(explanations)} analytical explanations generated")
                high_confidence = [e for e in explanations if e['confidence'] > 0.7]
                if high_confidence:
                    bullets.append(f"  - {len(high_confidence)} high-confidence insights available")
        
        # Add metadata
        bullets.append(f"**Data Package**: Generated at {summary.get('timestamp', 'unknown')}")
        bullets.append(f"**Sources**: {', '.join(summary.get('sources', []))}")
        
        # Join bullets into a Markdown list
        content = "\n".join([f"- {b}" for b in bullets])
        write_md(self.outdir / "prefill_notes.md", content)
        write_json(self.outdir / "package_summary.json", summary)
