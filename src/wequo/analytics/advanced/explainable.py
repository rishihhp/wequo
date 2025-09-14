from __future__ import annotations
import numpy as np
import pandas as pd
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict

from .changepoint import ChangePointDetector, ChangePoint
from .correlation import CrossCorrelationAnalyzer, CorrelationResult
from .events import EventImpactTagger, EventImpact


@dataclass
class AnalyticsExplanation:
    """Provides human-readable explanations for analytics results."""
    
    analysis_type: str  # anomaly, trend, correlation, changepoint, event_impact
    series_id: str
    timestamp: datetime
    confidence: float
    primary_explanation: str
    contributing_factors: List[str]
    evidence: Dict[str, Any]
    recommendations: List[str]
    related_findings: List[str]


class ExplainableAnalytics:
    """Provides explainable analytics with human-readable insights."""
    
    def __init__(self):
        self.changepoint_detector = ChangePointDetector()
        self.correlation_analyzer = CrossCorrelationAnalyzer()
        self.event_tagger = EventImpactTagger()
    
    def explain_anomaly(self, anomaly_data: Dict[str, Any], 
                       df: pd.DataFrame) -> AnalyticsExplanation:
        """Generate explanation for an anomaly detection result."""
        
        series_id = anomaly_data.get('series_id', 'unknown')
        timestamp = pd.to_datetime(anomaly_data.get('timestamp', datetime.now()))
        value = anomaly_data.get('value', 0)
        z_score = anomaly_data.get('z_score', 0)
        
        # Analyze potential causes
        contributing_factors = []
        evidence = {}
        recommendations = []
        related_findings = []
        
        # 1. Check for nearby change points
        series_data = df[df['series_id'] == series_id]
        if not series_data.empty:
            changepoints = self.changepoint_detector.detect_changepoints(series_data)
            nearby_changepoints = [
                cp for cp in changepoints 
                if abs((cp.timestamp - timestamp).days) <= 7
            ]
            
            if nearby_changepoints:
                cp = nearby_changepoints[0]
                contributing_factors.append(f"Structural change detected ({cp.change_type})")
                evidence['nearby_changepoint'] = {
                    'type': cp.change_type,
                    'confidence': cp.confidence,
                    'description': cp.description
                }
                related_findings.append(f"Change point in {cp.change_type} detected near anomaly")
        
        # 2. Check for event impacts
        event_impacts = self.event_tagger.detect_event_impacts(df)
        relevant_impacts = [
            impact for impact in event_impacts
            if (impact.series_id == series_id and 
                abs((pd.to_datetime(impact.context.get('event_timestamp', timestamp)) - timestamp).days) <= 7)
        ]
        
        if relevant_impacts:
            impact = relevant_impacts[0]
            contributing_factors.append(f"Event impact detected: {impact.event_id}")
            evidence['event_impact'] = {
                'event_id': impact.event_id,
                'impact_type': impact.impact_type,
                'confidence': impact.confidence
            }
            related_findings.append(f"Event '{impact.event_id}' may have caused this anomaly")
        
        # 3. Check correlations with other series
        correlations = self.correlation_analyzer.analyze_all_correlations(df)
        strong_correlations = [
            corr for corr in correlations
            if ((corr.series1_id == series_id or corr.series2_id == series_id) and
                abs(corr.correlation_coefficient) > 0.6)
        ]
        
        if strong_correlations:
            corr = strong_correlations[0]
            other_series = corr.series2_id if corr.series1_id == series_id else corr.series1_id
            contributing_factors.append(f"Strong correlation with {other_series}")
            evidence['correlation'] = {
                'other_series': other_series,
                'coefficient': corr.correlation_coefficient,
                'type': corr.correlation_type
            }
            related_findings.append(f"Check {other_series} for similar anomalous behavior")
        
        # Generate primary explanation
        severity = self._categorize_anomaly_severity(z_score)
        direction = "spike" if value > 0 else "drop"
        
        primary_explanation = (
            f"{severity} {direction} detected in {series_id} "
            f"(z-score: {z_score:.2f}). "
        )
        
        if contributing_factors:
            primary_explanation += f"Likely causes: {', '.join(contributing_factors[:2])}."
        else:
            primary_explanation += "No obvious structural causes identified."
        
        # Generate recommendations
        if abs(z_score) > 3:
            recommendations.append("Investigate data quality and potential measurement errors")
        
        if contributing_factors:
            recommendations.append("Monitor related series and events for additional context")
        else:
            recommendations.append("Check for external factors or data collection issues")
        
        if strong_correlations:
            recommendations.append(f"Validate findings against correlated series: {strong_correlations[0].series2_id if strong_correlations[0].series1_id == series_id else strong_correlations[0].series1_id}")
        
        return AnalyticsExplanation(
            analysis_type="anomaly",
            series_id=series_id,
            timestamp=timestamp,
            confidence=min(1.0, abs(z_score) / 4),  # Convert z-score to confidence
            primary_explanation=primary_explanation,
            contributing_factors=contributing_factors,
            evidence=evidence,
            recommendations=recommendations,
            related_findings=related_findings
        )
    
    def explain_trend(self, trend_data: Dict[str, Any], 
                     df: pd.DataFrame) -> AnalyticsExplanation:
        """Generate explanation for a trend analysis result."""
        
        series_id = trend_data.get('series_id', 'unknown')
        slope = trend_data.get('slope', 0)
        r_squared = trend_data.get('r_squared', 0)
        direction = trend_data.get('direction', 'flat')
        trend_strength = trend_data.get('trend_strength', 'none')
        
        contributing_factors = []
        evidence = {}
        recommendations = []
        related_findings = []
        
        # Analyze trend context
        evidence['trend_metrics'] = {
            'slope': slope,
            'r_squared': r_squared,
            'direction': direction,
            'strength': trend_strength
        }
        
        # Check for correlations that might explain the trend
        correlations = self.correlation_analyzer.analyze_all_correlations(df)
        relevant_correlations = [
            corr for corr in correlations
            if ((corr.series1_id == series_id or corr.series2_id == series_id) and
                abs(corr.correlation_coefficient) > 0.5)
        ]
        
        if relevant_correlations:
            for corr in relevant_correlations[:2]:  # Top 2 correlations
                other_series = corr.series2_id if corr.series1_id == series_id else corr.series1_id
                contributing_factors.append(f"Correlated with {other_series} trend")
                related_findings.append(f"{other_series} shows similar trend pattern")
        
        # Check for structural breaks
        series_data = df[df['series_id'] == series_id]
        if not series_data.empty:
            changepoints = self.changepoint_detector.detect_changepoints(series_data)
            trend_changepoints = [cp for cp in changepoints if cp.change_type == 'trend']
            
            if trend_changepoints:
                contributing_factors.append("Multiple trend regimes detected")
                evidence['changepoints'] = len(trend_changepoints)
                related_findings.append("Trend direction has changed over time")
        
        # Generate primary explanation
        strength_desc = {
            'strong': 'Strong',
            'moderate': 'Moderate', 
            'weak': 'Weak',
            'none': 'No clear'
        }.get(trend_strength, 'Unknown')
        
        if direction != 'flat':
            primary_explanation = (
                f"{strength_desc} {direction} trend in {series_id} "
                f"(R² = {r_squared:.3f}). "
            )
        else:
            primary_explanation = f"No significant trend detected in {series_id}. "
        
        if contributing_factors:
            primary_explanation += f"Pattern may be influenced by: {', '.join(contributing_factors[:2])}."
        
        # Generate recommendations
        if trend_strength in ['strong', 'moderate']:
            recommendations.append("Monitor for trend continuation or reversal")
            recommendations.append("Consider implications for forecasting and planning")
        
        if r_squared < 0.5:
            recommendations.append("Trend is not well-established; monitor for confirmation")
        
        if relevant_correlations:
            recommendations.append("Analyze correlated series to understand underlying drivers")
        
        confidence = r_squared * (1 if trend_strength in ['strong', 'moderate'] else 0.5)
        
        return AnalyticsExplanation(
            analysis_type="trend",
            series_id=series_id,
            timestamp=datetime.now(),
            confidence=confidence,
            primary_explanation=primary_explanation,
            contributing_factors=contributing_factors,
            evidence=evidence,
            recommendations=recommendations,
            related_findings=related_findings
        )
    
    def explain_correlation(self, correlation: CorrelationResult,
                          df: pd.DataFrame) -> AnalyticsExplanation:
        """Generate explanation for a correlation analysis result."""
        
        contributing_factors = []
        evidence = {}
        recommendations = []
        related_findings = []
        
        # Analyze correlation context
        evidence['correlation_metrics'] = {
            'coefficient': correlation.correlation_coefficient,
            'p_value': correlation.statistical_significance,
            'type': correlation.correlation_type,
            'lag': correlation.lag
        }
        
        # Determine correlation strength and direction
        strength = self._categorize_correlation_strength(abs(correlation.correlation_coefficient))
        direction = "positive" if correlation.correlation_coefficient > 0 else "negative"
        
        # Check for common underlying factors
        series1_domain = self._identify_series_domain(correlation.series1_id)
        series2_domain = self._identify_series_domain(correlation.series2_id)
        
        if series1_domain == series2_domain:
            contributing_factors.append(f"Both series are in {series1_domain} domain")
        else:
            contributing_factors.append(f"Cross-domain relationship ({series1_domain} ↔ {series2_domain})")
        
        # Analyze lag relationship
        if correlation.lag != 0:
            if correlation.lag > 0:
                leading_series = correlation.series1_id
                lagging_series = correlation.series2_id
                lag_periods = correlation.lag
            else:
                leading_series = correlation.series2_id
                lagging_series = correlation.series1_id
                lag_periods = abs(correlation.lag)
            
            contributing_factors.append(f"{leading_series} leads {lagging_series} by {lag_periods} periods")
            evidence['lead_lag'] = {
                'leading': leading_series,
                'lagging': lagging_series,
                'lag_periods': lag_periods
            }
        
        # Check for event-driven correlations
        event_impacts = self.event_tagger.detect_event_impacts(df)
        series1_impacts = [i for i in event_impacts if i.series_id == correlation.series1_id]
        series2_impacts = [i for i in event_impacts if i.series_id == correlation.series2_id]
        
        common_events = set(i.event_id for i in series1_impacts) & set(i.event_id for i in series2_impacts)
        if common_events:
            contributing_factors.append(f"Both affected by common events: {', '.join(list(common_events)[:2])}")
            evidence['common_events'] = list(common_events)
        
        # Generate primary explanation
        lag_desc = ""
        if correlation.lag > 0:
            lag_desc = f" with {correlation.series1_id} leading by {correlation.lag} periods"
        elif correlation.lag < 0:
            lag_desc = f" with {correlation.series2_id} leading by {abs(correlation.lag)} periods"
        
        primary_explanation = (
            f"{strength} {direction} correlation between {correlation.series1_id} "
            f"and {correlation.series2_id} (r = {correlation.correlation_coefficient:.3f}){lag_desc}. "
        )
        
        if correlation.statistical_significance < 0.01:
            primary_explanation += "Highly statistically significant. "
        elif correlation.statistical_significance < 0.05:
            primary_explanation += "Statistically significant. "
        
        # Generate recommendations
        if abs(correlation.correlation_coefficient) > 0.7:
            recommendations.append("Strong relationship suggests potential predictive value")
        
        if correlation.lag != 0:
            recommendations.append("Lead-lag relationship may be useful for forecasting")
        
        if correlation.statistical_significance > 0.05:
            recommendations.append("Correlation is not statistically significant; interpret with caution")
        
        if common_events:
            recommendations.append("Monitor both series during similar events")
        
        return AnalyticsExplanation(
            analysis_type="correlation",
            series_id=f"{correlation.series1_id} × {correlation.series2_id}",
            timestamp=datetime.now(),
            confidence=1 - correlation.statistical_significance,
            primary_explanation=primary_explanation,
            contributing_factors=contributing_factors,
            evidence=evidence,
            recommendations=recommendations,
            related_findings=related_findings
        )
    
    def explain_changepoint(self, changepoint: ChangePoint,
                          df: pd.DataFrame) -> AnalyticsExplanation:
        """Generate explanation for a change point detection result."""
        
        contributing_factors = []
        evidence = {}
        recommendations = []
        related_findings = []
        
        # Analyze change point context
        evidence['changepoint_metrics'] = {
            'type': changepoint.change_type,
            'confidence': changepoint.confidence,
            'magnitude': changepoint.magnitude,
            'p_value': changepoint.statistical_significance
        }
        
        # Check for events around the change point
        event_impacts = self.event_tagger.detect_event_impacts(df)
        relevant_impacts = [
            impact for impact in event_impacts
            if (impact.series_id == changepoint.series_id and
                abs((pd.to_datetime(impact.context.get('event_timestamp', changepoint.timestamp)) - changepoint.timestamp).days) <= 14)
        ]
        
        if relevant_impacts:
            impact = relevant_impacts[0]
            contributing_factors.append(f"Coincides with {impact.event_id}")
            evidence['related_event'] = {
                'event_id': impact.event_id,
                'impact_type': impact.impact_type
            }
            related_findings.append(f"Event '{impact.event_id}' may have triggered this structural change")
        
        # Check for similar change points in correlated series
        correlations = self.correlation_analyzer.analyze_all_correlations(df)
        correlated_series = [
            corr.series2_id if corr.series1_id == changepoint.series_id else corr.series1_id
            for corr in correlations
            if ((corr.series1_id == changepoint.series_id or corr.series2_id == changepoint.series_id) and
                abs(corr.correlation_coefficient) > 0.5)
        ]
        
        concurrent_changes = []  # Initialize the variable
        if correlated_series:
            # Check if correlated series also have change points around the same time
            all_changepoints = self.changepoint_detector.detect_changepoints(df)
            concurrent_changes = [
                cp for cp in all_changepoints
                if (cp.series_id in correlated_series and
                    abs((cp.timestamp - changepoint.timestamp).days) <= 7)
            ]
            
            if concurrent_changes:
                contributing_factors.append("Concurrent changes in correlated series")
                evidence['concurrent_changes'] = [cp.series_id for cp in concurrent_changes]
                related_findings.extend([f"Similar change detected in {cp.series_id}" for cp in concurrent_changes])
        
        # Generate primary explanation
        change_desc = {
            'mean': 'level shift',
            'variance': 'volatility change', 
            'trend': 'trend break',
            'regime': 'regime change'
        }.get(changepoint.change_type, 'structural change')
        
        primary_explanation = (
            f"Significant {change_desc} detected in {changepoint.series_id} "
            f"on {changepoint.timestamp.strftime('%Y-%m-%d')} "
            f"(confidence: {changepoint.confidence:.2f}). "
        )
        
        if changepoint.change_type == 'mean':
            before_after = changepoint.context.get('before_mean', 0), changepoint.context.get('after_mean', 0)
            primary_explanation += f"Mean shifted from {before_after[0]:.3f} to {before_after[1]:.3f}. "
        
        if contributing_factors:
            primary_explanation += f"Potential causes: {', '.join(contributing_factors[:2])}."
        
        # Generate recommendations
        recommendations.append("Investigate underlying causes of structural change")
        
        if changepoint.confidence > 0.8:
            recommendations.append("High-confidence change point warrants detailed analysis")
        
        if relevant_impacts:
            recommendations.append("Consider event impact in ongoing analysis and forecasting")
        
        if concurrent_changes:
            recommendations.append("Analyze system-wide changes across related series")
        
        return AnalyticsExplanation(
            analysis_type="changepoint",
            series_id=changepoint.series_id,
            timestamp=changepoint.timestamp,
            confidence=changepoint.confidence,
            primary_explanation=primary_explanation,
            contributing_factors=contributing_factors,
            evidence=evidence,
            recommendations=recommendations,
            related_findings=related_findings
        )
    
    def explain_event_impact(self, event_impact: EventImpact,
                           df: pd.DataFrame) -> AnalyticsExplanation:
        """Generate explanation for an event impact detection result."""
        
        contributing_factors = []
        evidence = {}
        recommendations = []
        related_findings = []
        
        # Get event details
        event = None
        for catalog_event in self.event_tagger.event_catalog:
            if catalog_event.event_id == event_impact.event_id:
                event = catalog_event
                break
        
        if event:
            evidence['event_details'] = {
                'type': event.event_type,
                'severity': event.severity,
                'description': event.description,
                'affected_domains': event.affected_domains
            }
            
            contributing_factors.append(f"{event.event_type} event")
            if event.severity in ['high', 'critical']:
                contributing_factors.append(f"{event.severity} severity")
        
        # Analyze impact characteristics
        evidence['impact_metrics'] = {
            'type': event_impact.impact_type,
            'magnitude': event_impact.impact_magnitude,
            'duration_days': event_impact.impact_duration_days,
            'confidence': event_impact.confidence,
            'pre_event_baseline': event_impact.pre_event_baseline,
            'post_event_value': event_impact.post_event_value
        }
        
        # Check for similar impacts in related series
        all_impacts = self.event_tagger.detect_event_impacts(df)
        same_event_impacts = [
            impact for impact in all_impacts
            if (impact.event_id == event_impact.event_id and 
                impact.series_id != event_impact.series_id)
        ]
        
        if same_event_impacts:
            related_findings.extend([
                f"Similar {impact.impact_type} detected in {impact.series_id}"
                for impact in same_event_impacts[:3]
            ])
            evidence['cross_series_impacts'] = len(same_event_impacts)
        
        # Generate primary explanation
        impact_desc = {
            'spike': 'sudden increase',
            'drop': 'sudden decrease',
            'volatility_increase': 'increased volatility',
            'extreme_spike': 'extreme spike',
            'extreme_drop': 'extreme drop'
        }.get(event_impact.impact_type, 'significant change')
        
        magnitude_desc = ""
        if event_impact.impact_magnitude > 0.5:
            magnitude_desc = " (large magnitude)"
        elif event_impact.impact_magnitude > 0.2:
            magnitude_desc = " (moderate magnitude)"
        
        primary_explanation = (
            f"{impact_desc.title()}{magnitude_desc} in {event_impact.series_id} "
            f"following {event.description if event else event_impact.event_id} "
            f"(confidence: {event_impact.confidence:.2f}). "
        )
        
        if event_impact.impact_duration_days > 1:
            primary_explanation += f"Impact lasted {event_impact.impact_duration_days} days. "
        
        # Generate recommendations
        if event_impact.confidence > 0.8:
            recommendations.append("High-confidence event impact confirmed")
        
        if same_event_impacts:
            recommendations.append("Monitor other affected series for continued impacts")
        
        if event and event.severity in ['high', 'critical']:
            recommendations.append("Consider ongoing monitoring for delayed or secondary effects")
        
        recommendations.append("Use this impact pattern for similar future events")
        
        return AnalyticsExplanation(
            analysis_type="event_impact",
            series_id=event_impact.series_id,
            timestamp=datetime.now(),  # Event impacts don't have specific timestamps
            confidence=event_impact.confidence,
            primary_explanation=primary_explanation,
            contributing_factors=contributing_factors,
            evidence=evidence,
            recommendations=recommendations,
            related_findings=related_findings
        )
    
    def _categorize_anomaly_severity(self, z_score: float) -> str:
        """Categorize anomaly severity based on z-score."""
        abs_z = abs(z_score)
        if abs_z >= 4:
            return "Extreme"
        elif abs_z >= 3:
            return "Severe"
        elif abs_z >= 2:
            return "Moderate"
        else:
            return "Mild"
    
    def _categorize_correlation_strength(self, abs_correlation: float) -> str:
        """Categorize correlation strength."""
        if abs_correlation >= 0.8:
            return "Very strong"
        elif abs_correlation >= 0.6:
            return "Strong"
        elif abs_correlation >= 0.4:
            return "Moderate"
        elif abs_correlation >= 0.2:
            return "Weak"
        else:
            return "Very weak"
    
    def _identify_series_domain(self, series_id: str) -> str:
        """Identify the domain/category of a time series."""
        series_lower = series_id.lower()
        
        if any(term in series_lower for term in ['fred', 'dff', 'dgs', 'cpi']):
            return "economic"
        elif any(term in series_lower for term in ['commodities', 'oil', 'gold', 'silver', 'copper']):
            return "commodities"
        elif any(term in series_lower for term in ['bitcoin', 'ethereum', 'crypto', 'btc', 'eth']):
            return "cryptocurrency"
        elif any(term in series_lower for term in ['economic', 'gdp', 'unemployment']):
            return "macroeconomic"
        else:
            return "unknown"
    
    def generate_comprehensive_explanation(self, analytics_results: Dict[str, Any],
                                         df: pd.DataFrame) -> List[AnalyticsExplanation]:
        """Generate comprehensive explanations for all analytics results."""
        explanations = []
        
        # Explain anomalies
        if 'anomalies' in analytics_results:
            for anomaly in analytics_results['anomalies'][:5]:  # Top 5 anomalies
                explanation = self.explain_anomaly(anomaly, df)
                explanations.append(explanation)
        
        # Explain trends
        if 'trends' in analytics_results:
            for trend in analytics_results['trends'][:3]:  # Top 3 trends
                explanation = self.explain_trend(trend, df)
                explanations.append(explanation)
        
        # Explain correlations
        correlations = self.correlation_analyzer.analyze_all_correlations(df)
        for correlation in correlations[:3]:  # Top 3 correlations
            explanation = self.explain_correlation(correlation, df)
            explanations.append(explanation)
        
        # Explain change points
        changepoints = self.changepoint_detector.detect_changepoints(df)
        for changepoint in changepoints[:3]:  # Top 3 change points
            explanation = self.explain_changepoint(changepoint, df)
            explanations.append(explanation)
        
        # Explain event impacts
        event_impacts = self.event_tagger.detect_event_impacts(df)
        for impact in event_impacts[:3]:  # Top 3 event impacts
            explanation = self.explain_event_impact(impact, df)
            explanations.append(explanation)
        
        return explanations
