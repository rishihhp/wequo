from __future__ import annotations
import re
import numpy as np
import pandas as pd
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set, Tuple
from collections import defaultdict


@dataclass
class Event:
    """Represents a significant event that may impact time series."""
    
    event_id: str
    timestamp: datetime
    event_type: str  # economic, political, market, natural_disaster, etc.
    description: str
    severity: str  # low, medium, high, critical
    affected_domains: List[str]  # commodities, financial, crypto, etc.
    metadata: Dict[str, Any]


@dataclass
class EventImpact:
    """Represents the detected impact of an event on a time series."""
    
    event_id: str
    series_id: str
    impact_type: str  # spike, drop, volatility_increase, regime_change
    impact_magnitude: float
    impact_duration_days: int
    confidence: float  # 0.0 to 1.0
    pre_event_baseline: float
    post_event_value: float
    statistical_significance: float
    description: str
    context: Dict[str, Any]


class EventImpactTagger:
    """Tags time series with event impacts and attribution."""
    
    def __init__(self, 
                 impact_window_days: int = 7,
                 baseline_window_days: int = 14,
                 significance_threshold: float = 0.05):
        """
        Initialize event impact tagger.
        
        Args:
            impact_window_days: Days after event to look for impacts
            baseline_window_days: Days before event to establish baseline
            significance_threshold: Statistical significance threshold
        """
        self.impact_window_days = impact_window_days
        self.baseline_window_days = baseline_window_days
        self.significance_threshold = significance_threshold
        
        # Pre-defined event catalog (in real system, this would be loaded from external sources)
        self.event_catalog = self._initialize_event_catalog()
    
    def _initialize_event_catalog(self) -> List[Event]:
        """Initialize a catalog of known significant events."""
        # This is a sample catalog - in production, this would be loaded from
        # external sources like news APIs, economic calendars, etc.
        
        events = [
            Event(
                event_id="covid_19_declaration",
                timestamp=datetime(2020, 3, 11),
                event_type="pandemic",
                description="WHO declares COVID-19 a pandemic",
                severity="critical",
                affected_domains=["commodities", "financial", "crypto", "economic"],
                metadata={"source": "WHO", "global_impact": True}
            ),
            Event(
                event_id="russia_ukraine_conflict",
                timestamp=datetime(2022, 2, 24),
                event_type="geopolitical",
                description="Russia invades Ukraine",
                severity="critical",
                affected_domains=["commodities", "financial", "energy"],
                metadata={"source": "news", "regional_impact": ["Europe", "Global"]}
            ),
            Event(
                event_id="fed_rate_hike_2022_03",
                timestamp=datetime(2022, 3, 16),
                event_type="monetary_policy",
                description="Federal Reserve raises interest rates by 0.25%",
                severity="high",
                affected_domains=["financial", "crypto", "economic"],
                metadata={"source": "Federal Reserve", "rate_change": 0.25}
            ),
            Event(
                event_id="silicon_valley_bank_collapse",
                timestamp=datetime(2023, 3, 10),
                event_type="financial_crisis",
                description="Silicon Valley Bank collapses",
                severity="high",
                affected_domains=["financial", "crypto"],
                metadata={"source": "news", "sector": "banking"}
            ),
            Event(
                event_id="opec_production_cut_2023",
                timestamp=datetime(2023, 4, 2),
                event_type="supply_shock",
                description="OPEC+ announces oil production cuts",
                severity="medium",
                affected_domains=["commodities", "energy"],
                metadata={"source": "OPEC", "commodity": "oil"}
            )
        ]
        
        return events
    
    def detect_event_impacts(self, df: pd.DataFrame, 
                           custom_events: Optional[List[Event]] = None) -> List[EventImpact]:
        """
        Detect impacts of events on time series data.
        
        Args:
            df: DataFrame with time series data
            custom_events: Additional events to analyze
            
        Returns:
            List of detected event impacts
        """
        if df.empty:
            return []
        
        # Combine catalog events with custom events
        all_events = self.event_catalog.copy()
        if custom_events:
            all_events.extend(custom_events)
        
        impacts = []
        
        # Analyze each event
        for event in all_events:
            event_impacts = self._analyze_single_event_impact(df, event)
            impacts.extend(event_impacts)
        
        # Sort by confidence and magnitude
        impacts.sort(key=lambda x: (x.confidence, abs(x.impact_magnitude)), reverse=True)
        
        return impacts
    
    def _analyze_single_event_impact(self, df: pd.DataFrame, event: Event) -> List[EventImpact]:
        """Analyze the impact of a single event on all relevant series."""
        impacts = []
        
        # Get relevant series based on event domains
        relevant_series = self._get_relevant_series(df, event.affected_domains)
        
        for series_id in relevant_series:
            series_data = df[df['series_id'] == series_id].copy()
            series_data = series_data.sort_values('date')
            
            if len(series_data) < 10:  # Need sufficient data
                continue
            
            # Convert dates to datetime
            series_data['date'] = pd.to_datetime(series_data['date'])
            
            # Find impact
            impact = self._detect_series_event_impact(series_data, event, series_id)
            if impact:
                impacts.append(impact)
        
        return impacts
    
    def _get_relevant_series(self, df: pd.DataFrame, affected_domains: List[str]) -> List[str]:
        """Get series IDs that might be affected by the event."""
        relevant_series = set()
        
        # Map domains to series patterns
        domain_patterns = {
            "commodities": ["commodities", "oil", "gold", "silver", "copper", "gas"],
            "financial": ["fred", "dff", "dgs", "treasury", "bond", "stock"],
            "crypto": ["bitcoin", "ethereum", "crypto", "btc", "eth"],
            "economic": ["economic", "gdp", "inflation", "unemployment", "cpi"],
            "energy": ["oil", "gas", "energy", "wti", "brent"]
        }
        
        for domain in affected_domains:
            patterns = domain_patterns.get(domain, [domain])
            
            for series_id in df['series_id'].unique():
                series_lower = series_id.lower()
                if any(pattern.lower() in series_lower for pattern in patterns):
                    relevant_series.add(series_id)
        
        return list(relevant_series)
    
    def _detect_series_event_impact(self, series_data: pd.DataFrame, 
                                  event: Event, series_id: str) -> Optional[EventImpact]:
        """Detect impact of an event on a specific time series."""
        
        # Find data points around the event
        event_date = pd.to_datetime(event.timestamp)
        
        # Define time windows
        baseline_start = event_date - timedelta(days=self.baseline_window_days)
        baseline_end = event_date - timedelta(days=1)
        impact_start = event_date
        impact_end = event_date + timedelta(days=self.impact_window_days)
        
        # Get baseline data (before event)
        baseline_data = series_data[
            (series_data['date'] >= baseline_start) & 
            (series_data['date'] <= baseline_end)
        ]
        
        # Get impact window data (after event)
        impact_data = series_data[
            (series_data['date'] >= impact_start) & 
            (series_data['date'] <= impact_end)
        ]
        
        if len(baseline_data) < 3 or len(impact_data) < 2:
            return None
        
        # Calculate baseline statistics
        baseline_values = baseline_data['value'].values
        baseline_mean = np.mean(baseline_values)
        baseline_std = np.std(baseline_values)
        
        # Calculate impact statistics
        impact_values = impact_data['value'].values
        impact_mean = np.mean(impact_values)
        
        # Detect different types of impacts
        impact_results = []
        
        # 1. Mean shift detection
        mean_impact = self._detect_mean_shift(baseline_values, impact_values, event, series_id)
        if mean_impact:
            impact_results.append(mean_impact)
        
        # 2. Volatility change detection
        volatility_impact = self._detect_volatility_change(baseline_values, impact_values, event, series_id)
        if volatility_impact:
            impact_results.append(volatility_impact)
        
        # 3. Extreme value detection
        extreme_impact = self._detect_extreme_values(baseline_values, impact_values, event, series_id)
        if extreme_impact:
            impact_results.append(extreme_impact)
        
        # Return the most significant impact
        if impact_results:
            return max(impact_results, key=lambda x: x.confidence)
        
        return None
    
    def _detect_mean_shift(self, baseline: np.ndarray, impact: np.ndarray, 
                          event: Event, series_id: str) -> Optional[EventImpact]:
        """Detect significant mean shifts after an event."""
        from scipy import stats
        
        # Perform t-test
        t_stat, p_value = stats.ttest_ind(baseline, impact)
        
        if p_value < self.significance_threshold:
            baseline_mean = np.mean(baseline)
            impact_mean = np.mean(impact)
            
            # Calculate effect size (Cohen's d)
            pooled_std = np.sqrt(((len(baseline) - 1) * np.var(baseline) + 
                                 (len(impact) - 1) * np.var(impact)) / 
                                (len(baseline) + len(impact) - 2))
            
            effect_size = abs(impact_mean - baseline_mean) / pooled_std if pooled_std > 0 else 0
            
            # Determine impact type
            if impact_mean > baseline_mean:
                impact_type = "spike"
                magnitude = (impact_mean - baseline_mean) / baseline_mean if baseline_mean != 0 else 0
            else:
                impact_type = "drop"
                magnitude = (baseline_mean - impact_mean) / baseline_mean if baseline_mean != 0 else 0
            
            # Confidence based on p-value and effect size
            confidence = (1 - p_value) * min(1.0, effect_size / 2)
            
            return EventImpact(
                event_id=event.event_id,
                series_id=series_id,
                impact_type=impact_type,
                impact_magnitude=magnitude,
                impact_duration_days=self.impact_window_days,
                confidence=confidence,
                pre_event_baseline=baseline_mean,
                post_event_value=impact_mean,
                statistical_significance=p_value,
                description=f"{impact_type.title()} in {series_id} following {event.description}",
                context={
                    "test_type": "t_test",
                    "effect_size": effect_size,
                    "t_statistic": t_stat,
                    "baseline_periods": len(baseline),
                    "impact_periods": len(impact)
                }
            )
        
        return None
    
    def _detect_volatility_change(self, baseline: np.ndarray, impact: np.ndarray,
                                event: Event, series_id: str) -> Optional[EventImpact]:
        """Detect significant volatility changes after an event."""
        from scipy import stats
        
        # Calculate variances
        baseline_var = np.var(baseline)
        impact_var = np.var(impact)
        
        if baseline_var == 0 or impact_var == 0:
            return None
        
        # F-test for variance equality
        f_stat = max(impact_var, baseline_var) / min(impact_var, baseline_var)
        df1 = len(impact) - 1 if impact_var > baseline_var else len(baseline) - 1
        df2 = len(baseline) - 1 if impact_var > baseline_var else len(impact) - 1
        
        p_value = 2 * (1 - stats.f.cdf(f_stat, df1, df2))
        
        if p_value < self.significance_threshold:
            volatility_ratio = np.sqrt(impact_var) / np.sqrt(baseline_var)
            
            if volatility_ratio > 1.5:  # Significant increase in volatility
                magnitude = volatility_ratio - 1
                confidence = (1 - p_value) * min(1.0, magnitude)
                
                return EventImpact(
                    event_id=event.event_id,
                    series_id=series_id,
                    impact_type="volatility_increase",
                    impact_magnitude=magnitude,
                    impact_duration_days=self.impact_window_days,
                    confidence=confidence,
                    pre_event_baseline=np.sqrt(baseline_var),
                    post_event_value=np.sqrt(impact_var),
                    statistical_significance=p_value,
                    description=f"Volatility increase in {series_id} following {event.description}",
                    context={
                        "test_type": "f_test",
                        "f_statistic": f_stat,
                        "volatility_ratio": volatility_ratio
                    }
                )
        
        return None
    
    def _detect_extreme_values(self, baseline: np.ndarray, impact: np.ndarray,
                             event: Event, series_id: str) -> Optional[EventImpact]:
        """Detect extreme values in the impact period."""
        
        # Calculate baseline statistics
        baseline_mean = np.mean(baseline)
        baseline_std = np.std(baseline)
        
        if baseline_std == 0:
            return None
        
        # Find extreme values in impact period (>2 standard deviations)
        extreme_threshold = 2.0
        extreme_values = []
        
        for value in impact:
            z_score = abs(value - baseline_mean) / baseline_std
            if z_score > extreme_threshold:
                extreme_values.append((value, z_score))
        
        if extreme_values:
            # Find most extreme value
            max_extreme = max(extreme_values, key=lambda x: x[1])
            extreme_value, z_score = max_extreme
            
            # Calculate confidence based on z-score
            from scipy import stats
            p_value = 2 * (1 - stats.norm.cdf(z_score))  # Two-tailed test
            confidence = 1 - p_value
            
            # Determine impact type
            if extreme_value > baseline_mean:
                impact_type = "extreme_spike"
            else:
                impact_type = "extreme_drop"
            
            magnitude = abs(extreme_value - baseline_mean) / baseline_mean if baseline_mean != 0 else 0
            
            return EventImpact(
                event_id=event.event_id,
                series_id=series_id,
                impact_type=impact_type,
                impact_magnitude=magnitude,
                impact_duration_days=1,  # Extreme values are typically short-term
                confidence=confidence,
                pre_event_baseline=baseline_mean,
                post_event_value=extreme_value,
                statistical_significance=p_value,
                description=f"{impact_type.replace('_', ' ').title()} in {series_id} following {event.description}",
                context={
                    "test_type": "z_score",
                    "z_score": z_score,
                    "extreme_threshold": extreme_threshold,
                    "total_extreme_values": len(extreme_values)
                }
            )
        
        return None
    
    def add_custom_event(self, event: Event):
        """Add a custom event to the catalog."""
        self.event_catalog.append(event)
    
    def get_events_in_period(self, start_date: datetime, end_date: datetime) -> List[Event]:
        """Get all events within a specific time period."""
        return [
            event for event in self.event_catalog
            if start_date <= event.timestamp <= end_date
        ]
    
    def get_impact_summary(self, impacts: List[EventImpact]) -> Dict[str, Any]:
        """Generate summary statistics for event impacts."""
        if not impacts:
            return {
                "total_impacts": 0,
                "by_type": {},
                "by_event": {},
                "most_significant": None
            }
        
        # Count by impact type
        by_type = defaultdict(int)
        for impact in impacts:
            by_type[impact.impact_type] += 1
        
        # Count by event
        by_event = defaultdict(int)
        for impact in impacts:
            by_event[impact.event_id] += 1
        
        # Find most significant impact
        most_significant = max(impacts, key=lambda x: x.confidence)
        
        return {
            "total_impacts": len(impacts),
            "by_type": dict(by_type),
            "by_event": dict(by_event),
            "most_significant": {
                "event_id": most_significant.event_id,
                "series_id": most_significant.series_id,
                "impact_type": most_significant.impact_type,
                "confidence": most_significant.confidence,
                "magnitude": most_significant.impact_magnitude,
                "description": most_significant.description
            },
            "average_confidence": sum(i.confidence for i in impacts) / len(impacts),
            "significant_impacts": sum(1 for i in impacts if i.statistical_significance < 0.05)
        }
    
    def create_event_timeline(self, impacts: List[EventImpact]) -> List[Dict[str, Any]]:
        """Create a timeline of events and their impacts."""
        # Group impacts by event
        event_impacts = defaultdict(list)
        for impact in impacts:
            event_impacts[impact.event_id].append(impact)
        
        timeline = []
        
        # Get events and their impacts
        for event in self.event_catalog:
            if event.event_id in event_impacts:
                event_entry = {
                    "event_id": event.event_id,
                    "timestamp": event.timestamp.isoformat(),
                    "description": event.description,
                    "severity": event.severity,
                    "event_type": event.event_type,
                    "impacts": []
                }
                
                for impact in event_impacts[event.event_id]:
                    event_entry["impacts"].append({
                        "series_id": impact.series_id,
                        "impact_type": impact.impact_type,
                        "magnitude": impact.impact_magnitude,
                        "confidence": impact.confidence,
                        "description": impact.description
                    })
                
                timeline.append(event_entry)
        
        # Sort by timestamp
        timeline.sort(key=lambda x: x["timestamp"])
        
        return timeline
