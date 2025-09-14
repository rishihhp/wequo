from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from pathlib import Path

import pandas as pd
import numpy as np

from .anomaly import AnomalyDetector
from .trends import TrendAnalyzer
from .deltas import DeltaCalculator
from .advanced.changepoint import ChangePointDetector
from .advanced.correlation import CrossCorrelationAnalyzer
from .advanced.events import EventImpactTagger
from .advanced.explainable import ExplainableAnalytics


@dataclass
class AnalyticsResult:
    """Container for analytics results."""
    
    top_deltas: List[Dict[str, Any]]
    anomalies: List[Dict[str, Any]]
    trends: List[Dict[str, Any]]
    percentiles: Dict[str, Dict[str, float]]
    summary_stats: Dict[str, Any]
    
    # Advanced analytics (Phase 3)
    changepoints: List[Dict[str, Any]]
    correlations: List[Dict[str, Any]]
    event_impacts: List[Dict[str, Any]]
    explanations: List[Dict[str, Any]]


class AnalyticsEngine:
    """Main analytics engine that orchestrates all analytics modules."""
    
    def __init__(self, 
                 anomaly_threshold: float = 2.0,
                 delta_threshold: float = 0.05,
                 min_data_points: int = 5,
                 enable_advanced_analytics: bool = True):
        self.anomaly_detector = AnomalyDetector(threshold=anomaly_threshold)
        self.trend_analyzer = TrendAnalyzer()
        self.delta_calculator = DeltaCalculator(threshold=delta_threshold)
        self.min_data_points = min_data_points
        
        # Advanced analytics (Phase 3)
        self.enable_advanced_analytics = enable_advanced_analytics
        if enable_advanced_analytics:
            self.changepoint_detector = ChangePointDetector(min_size=min_data_points)
            self.correlation_analyzer = CrossCorrelationAnalyzer()
            self.event_tagger = EventImpactTagger()
            self.explainable_analytics = ExplainableAnalytics()
    
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
                summary_stats={},
                changepoints=[],
                correlations=[],
                event_impacts=[],
                explanations=[]
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
        
        # Advanced analytics (Phase 3)
        changepoints = []
        correlations = []
        event_impacts = []
        explanations = []
        
        if self.enable_advanced_analytics:
            # Change point detection
            print("Detecting change points...")
            changepoint_results = self.changepoint_detector.detect_changepoints(all_data)
            changepoints = [self._serialize_changepoint(cp) for cp in changepoint_results]
            print(f"Found {len(changepoints)} change points")
            
            # Cross-correlation analysis
            print("Analyzing cross-correlations...")
            correlation_results = self.correlation_analyzer.analyze_all_correlations(all_data)
            correlations = [self._serialize_correlation(corr) for corr in correlation_results]
            print(f"Found {len(correlations)} correlations")
            
            # Event impact analysis
            print("Analyzing event impacts...")
            event_impact_results = self.event_tagger.detect_event_impacts(all_data)
            event_impacts = [self._serialize_event_impact(ei) for ei in event_impact_results]
            print(f"Found {len(event_impacts)} event impacts")
            
            # Generate explanations
            analytics_data = {
                'anomalies': anomalies,
                'trends': trends,
                'changepoints': changepoints,
                'correlations': correlations,
                'event_impacts': event_impacts
            }
            explanation_results = self.explainable_analytics.generate_comprehensive_explanation(analytics_data, all_data)
            explanations = [self._serialize_explanation(exp) for exp in explanation_results]
        
        return AnalyticsResult(
            top_deltas=top_deltas,
            anomalies=anomalies,
            trends=trends,
            percentiles=percentiles,
            summary_stats=summary_stats,
            changepoints=changepoints,
            correlations=correlations,
            event_impacts=event_impacts,
            explanations=explanations
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
    
    def _serialize_changepoint(self, changepoint) -> Dict[str, Any]:
        """Serialize ChangePoint object to dictionary."""
        return {
            "series_id": changepoint.series_id,
            "timestamp": changepoint.timestamp.isoformat(),
            "index": changepoint.index,
            "change_type": changepoint.change_type,
            "confidence": changepoint.confidence,
            "magnitude": changepoint.magnitude,
            "description": changepoint.description,
            "statistical_significance": changepoint.statistical_significance,
            "context": changepoint.context
        }
    
    def _serialize_correlation(self, correlation) -> Dict[str, Any]:
        """Serialize CorrelationResult object to dictionary."""
        return {
            "series1_id": correlation.series1_id,
            "series2_id": correlation.series2_id,
            "correlation_type": correlation.correlation_type,
            "correlation_coefficient": correlation.correlation_coefficient,
            "statistical_significance": correlation.statistical_significance,
            "lag": correlation.lag,
            "confidence_interval": correlation.confidence_interval,
            "description": correlation.description,
            "context": correlation.context
        }
    
    def _serialize_event_impact(self, event_impact) -> Dict[str, Any]:
        """Serialize EventImpact object to dictionary."""
        return {
            "event_id": event_impact.event_id,
            "series_id": event_impact.series_id,
            "impact_type": event_impact.impact_type,
            "impact_magnitude": event_impact.impact_magnitude,
            "impact_duration_days": event_impact.impact_duration_days,
            "confidence": event_impact.confidence,
            "pre_event_baseline": event_impact.pre_event_baseline,
            "post_event_value": event_impact.post_event_value,
            "statistical_significance": event_impact.statistical_significance,
            "description": event_impact.description,
            "context": event_impact.context
        }
    
    def _serialize_explanation(self, explanation) -> Dict[str, Any]:
        """Serialize AnalyticsExplanation object to dictionary."""
        return {
            "analysis_type": explanation.analysis_type,
            "series_id": explanation.series_id,
            "timestamp": explanation.timestamp.isoformat(),
            "confidence": explanation.confidence,
            "primary_explanation": explanation.primary_explanation,
            "contributing_factors": explanation.contributing_factors,
            "evidence": explanation.evidence,
            "recommendations": explanation.recommendations,
            "related_findings": explanation.related_findings
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
            "summary_stats": result.summary_stats,
            "changepoints": result.changepoints,
            "correlations": result.correlations,
            "event_impacts": result.event_impacts,
            "explanations": result.explanations
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
        
        # Advanced Analytics Sections
        if self.enable_advanced_analytics:
            # Change Points
            if result.changepoints:
                lines.append("## Change Point Detection")
                for cp in result.changepoints:
                    lines.append(f"- **{cp['series_id']}**: {cp['change_type']} detected on {cp['timestamp'][:10]} (confidence: {cp['confidence']:.2f})")
                    if 'description' in cp:
                        lines.append(f"  - {cp['description']}")
                lines.append("")
            
            # Correlations
            if result.correlations:
                lines.append("## Cross-Correlation Analysis")
                significant_corr = [c for c in result.correlations if abs(c['correlation_coefficient']) > 0.3]
                for corr in significant_corr[:10]:  # Top 10 significant correlations
                    strength = "Strong" if abs(corr['correlation_coefficient']) > 0.7 else "Moderate" if abs(corr['correlation_coefficient']) > 0.5 else "Weak"
                    lines.append(f"- **{corr['series1_id']} ↔ {corr['series2_id']}**: {strength} {corr['correlation_type']} correlation ({corr['correlation_coefficient']:.3f})")
                    if corr.get('lag', 0) != 0:
                        lines.append(f"  - Time lag: {corr['lag']} periods")
                    if corr.get('statistical_significance', 1) < 0.05:
                        lines.append(f"  - Statistically significant (p-value: {corr['statistical_significance']:.3f})")
                lines.append("")
            
            # Event Impacts
            if result.event_impacts:
                lines.append("## Event Impact Analysis")
                for event in result.event_impacts:
                    lines.append(f"- **{event['event_id']}** → {event['series_id']}: {event['impact_type']} impact")
                    lines.append(f"  - Impact magnitude: {event['impact_magnitude']:.2f}")
                    lines.append(f"  - Confidence: {event['confidence']:.2f}")
                    if 'description' in event:
                        lines.append(f"  - {event['description']}")
                lines.append("")
            
            # Explanations
            if result.explanations:
                lines.append("## Analytical Insights")
                high_confidence = [e for e in result.explanations if e['confidence'] > 0.6]
                for explanation in high_confidence[:5]:  # Top 5 high-confidence explanations
                    lines.append(f"- **{explanation['series_id']}** ({explanation['analysis_type']}): {explanation['primary_explanation']}")
                    if explanation.get('contributing_factors'):
                        for factor in explanation['contributing_factors'][:2]:  # Top 2 factors
                            lines.append(f"  - {factor}")
                    if explanation.get('recommendations'):
                        for rec in explanation['recommendations'][:1]:  # Top recommendation
                            lines.append(f"  - 💡 {rec}")
                lines.append("")
        
        output_path.write_text("\n".join(lines), encoding='utf-8')
