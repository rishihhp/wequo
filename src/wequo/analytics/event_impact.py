"""
Event impact analysis for time series data.

Links anomalies and significant changes to real-world events to provide
context and explainability for detected patterns.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import json


@dataclass
class Event:
    """Represents a real-world event that may impact data."""
    event_id: str
    name: str
    date: str
    event_type: str  # "economic", "political", "natural", "market", "policy"
    description: str
    impact_scope: str  # "global", "regional", "national", "sector"
    confidence: float  # 0-1, how confident we are this event occurred
    source: str  # Where this event data came from


@dataclass
class EventImpact:
    """Represents the impact of an event on a data series."""
    event: Event
    series_id: str
    impact_date: str
    impact_type: str  # "anomaly", "change_point", "trend_change"
    impact_magnitude: float
    impact_direction: str  # "positive", "negative", "neutral"
    confidence: float
    time_lag: int  # Days between event and impact
    description: str


class EventImpactAnalyzer:
    """
    Analyzes the impact of real-world events on time series data.
    
    Features:
    - Event database management
    - Impact detection and linking
    - Temporal analysis (before/after event)
    - Impact magnitude assessment
    - Explainable anomaly attribution
    """
    
    def __init__(self):
        self.events = []
        self.event_impacts = []
        self._load_default_events()
    
    def _load_default_events(self):
        """Load a default set of known economic and financial events."""
        default_events = [
            # Economic events
            Event(
                event_id="covid_pandemic_start",
                name="COVID-19 Pandemic Declaration",
                date="2020-03-11",
                event_type="economic",
                description="WHO declares COVID-19 a global pandemic",
                impact_scope="global",
                confidence=1.0,
                source="WHO"
            ),
            Event(
                event_id="fed_rate_cut_2020",
                name="Federal Reserve Emergency Rate Cut",
                date="2020-03-15",
                event_type="policy",
                description="Fed cuts rates to near zero in emergency response to COVID-19",
                impact_scope="global",
                confidence=1.0,
                source="Federal Reserve"
            ),
            Event(
                event_id="ukraine_invasion",
                name="Russia Invades Ukraine",
                date="2022-02-24",
                event_type="political",
                description="Russian military invasion of Ukraine begins",
                impact_scope="global",
                confidence=1.0,
                source="News"
            ),
            Event(
                event_id="inflation_surge_2022",
                name="Global Inflation Surge",
                date="2022-01-01",
                event_type="economic",
                description="Global inflation reaches multi-decade highs",
                impact_scope="global",
                confidence=0.9,
                source="Economic Data"
            ),
            Event(
                event_id="crypto_crash_2022",
                name="Cryptocurrency Market Crash",
                date="2022-05-01",
                event_type="market",
                description="Major cryptocurrency market downturn",
                impact_scope="global",
                confidence=0.9,
                source="Market Data"
            ),
            Event(
                event_id="energy_crisis_2022",
                name="European Energy Crisis",
                date="2022-09-01",
                event_type="economic",
                description="European energy prices surge due to supply constraints",
                impact_scope="regional",
                confidence=0.9,
                source="Energy Markets"
            )
        ]
        
        self.events.extend(default_events)
    
    def add_event(self, event: Event):
        """Add a new event to the database."""
        self.events.append(event)
    
    def load_events_from_file(self, file_path: str):
        """Load events from a JSON file."""
        try:
            with open(file_path, 'r') as f:
                events_data = json.load(f)
            
            for event_data in events_data:
                event = Event(**event_data)
                self.events.append(event)
                
        except Exception as e:
            print(f"Error loading events from file: {e}")
    
    def save_events_to_file(self, file_path: str):
        """Save events to a JSON file."""
        try:
            events_data = [event.__dict__ for event in self.events]
            with open(file_path, 'w') as f:
                json.dump(events_data, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving events to file: {e}")
    
    def analyze_event_impacts(
        self, 
        df: pd.DataFrame, 
        anomalies: List[Dict[str, Any]], 
        change_points: List[Dict[str, Any]]
    ) -> List[EventImpact]:
        """
        Analyze the impact of events on detected anomalies and change points.
        
        Args:
            df: Time series data
            anomalies: List of detected anomalies
            change_points: List of detected change points
            
        Returns:
            List of event impacts
        """
        impacts = []
        
        # Analyze anomalies
        for anomaly in anomalies:
            anomaly_impacts = self._analyze_anomaly_impacts(df, anomaly)
            impacts.extend(anomaly_impacts)
        
        # Analyze change points
        for change_point in change_points:
            change_point_impacts = self._analyze_change_point_impacts(df, change_point)
            impacts.extend(change_point_impacts)
        
        self.event_impacts.extend(impacts)
        return impacts
    
    def _analyze_anomaly_impacts(
        self, 
        df: pd.DataFrame, 
        anomaly: Dict[str, Any]
    ) -> List[EventImpact]:
        """Analyze potential event impacts on anomalies."""
        impacts = []
        
        anomaly_date = pd.to_datetime(anomaly['date'])
        series_id = anomaly['series_id']
        
        # Look for events within a reasonable time window
        time_window = timedelta(days=30)  # 30 days before/after
        
        for event in self.events:
            event_date = pd.to_datetime(event.date)
            
            # Check if event is within time window
            time_diff = abs((anomaly_date - event_date).days)
            if time_diff <= time_window.days:
                # Calculate impact magnitude and direction
                impact_magnitude = self._calculate_impact_magnitude(
                    df, series_id, anomaly_date, event_date
                )
                
                impact_direction = self._determine_impact_direction(
                    df, series_id, anomaly_date, event_date
                )
                
                # Calculate confidence based on temporal proximity and magnitude
                confidence = self._calculate_impact_confidence(
                    time_diff, impact_magnitude, event.confidence
                )
                
                if confidence > 0.3:  # Only include impacts with reasonable confidence
                    impact = EventImpact(
                        event=event,
                        series_id=series_id,
                        impact_date=anomaly['date'],
                        impact_type="anomaly",
                        impact_magnitude=impact_magnitude,
                        impact_direction=impact_direction,
                        confidence=confidence,
                        time_lag=time_diff,
                        description=f"Event '{event.name}' may have caused anomaly in {series_id}"
                    )
                    impacts.append(impact)
        
        return impacts
    
    def _analyze_change_point_impacts(
        self, 
        df: pd.DataFrame, 
        change_point: Dict[str, Any]
    ) -> List[EventImpact]:
        """Analyze potential event impacts on change points."""
        impacts = []
        
        change_date = pd.to_datetime(change_point['date'])
        series_id = change_point['series_id']
        
        # Look for events within a reasonable time window
        time_window = timedelta(days=45)  # 45 days before/after for change points
        
        for event in self.events:
            event_date = pd.to_datetime(event.date)
            
            # Check if event is within time window
            time_diff = abs((change_date - event_date).days)
            if time_diff <= time_window.days:
                # Calculate impact magnitude and direction
                impact_magnitude = self._calculate_impact_magnitude(
                    df, series_id, change_date, event_date
                )
                
                impact_direction = self._determine_impact_direction(
                    df, series_id, change_date, event_date
                )
                
                # Calculate confidence based on temporal proximity and magnitude
                confidence = self._calculate_impact_confidence(
                    time_diff, impact_magnitude, event.confidence
                )
                
                if confidence > 0.3:  # Only include impacts with reasonable confidence
                    impact = EventImpact(
                        event=event,
                        series_id=series_id,
                        impact_date=change_point['date'],
                        impact_type="change_point",
                        impact_magnitude=impact_magnitude,
                        impact_direction=impact_direction,
                        confidence=confidence,
                        time_lag=time_diff,
                        description=f"Event '{event.name}' may have caused change point in {series_id}"
                    )
                    impacts.append(impact)
        
        return impacts
    
    def _calculate_impact_magnitude(
        self, 
        df: pd.DataFrame, 
        series_id: str, 
        impact_date: pd.Timestamp, 
        event_date: pd.Timestamp
    ) -> float:
        """Calculate the magnitude of impact."""
        try:
            series_data = df[df['series_id'] == series_id].sort_values('date')
            series_data['date'] = pd.to_datetime(series_data['date'])
            
            # Get data before and after the event
            before_data = series_data[series_data['date'] < event_date]
            after_data = series_data[series_data['date'] >= event_date]
            
            if len(before_data) < 5 or len(after_data) < 5:
                return 0.0
            
            # Calculate mean values before and after
            before_mean = before_data['value'].mean()
            after_mean = after_data['value'].mean()
            
            # Calculate relative change
            if before_mean != 0:
                relative_change = abs((after_mean - before_mean) / before_mean)
            else:
                relative_change = 0.0
            
            return min(relative_change, 1.0)  # Cap at 100%
            
        except Exception as e:
            print(f"Error calculating impact magnitude: {e}")
            return 0.0
    
    def _determine_impact_direction(
        self, 
        df: pd.DataFrame, 
        series_id: str, 
        impact_date: pd.Timestamp, 
        event_date: pd.Timestamp
    ) -> str:
        """Determine the direction of impact (positive/negative/neutral)."""
        try:
            series_data = df[df['series_id'] == series_id].sort_values('date')
            series_data['date'] = pd.to_datetime(series_data['date'])
            
            # Get data before and after the event
            before_data = series_data[series_data['date'] < event_date]
            after_data = series_data[series_data['date'] >= event_date]
            
            if len(before_data) < 5 or len(after_data) < 5:
                return "neutral"
            
            # Calculate mean values before and after
            before_mean = before_data['value'].mean()
            after_mean = after_data['value'].mean()
            
            # Determine direction
            change = after_mean - before_mean
            if change > 0.05 * abs(before_mean):  # 5% threshold
                return "positive"
            elif change < -0.05 * abs(before_mean):
                return "negative"
            else:
                return "neutral"
                
        except Exception as e:
            print(f"Error determining impact direction: {e}")
            return "neutral"
    
    def _calculate_impact_confidence(
        self, 
        time_diff: int, 
        impact_magnitude: float, 
        event_confidence: float
    ) -> float:
        """Calculate confidence in the event-impact relationship."""
        # Temporal proximity factor (closer events are more likely to be related)
        temporal_factor = max(0, 1 - (time_diff / 30))  # Decay over 30 days
        
        # Magnitude factor (larger impacts are more likely to be event-related)
        magnitude_factor = min(impact_magnitude * 2, 1.0)  # Scale magnitude
        
        # Combined confidence
        confidence = (temporal_factor * 0.4 + magnitude_factor * 0.3 + event_confidence * 0.3)
        
        return min(confidence, 1.0)
    
    def get_event_impact_summary(self) -> Dict[str, Any]:
        """Generate summary of event impacts."""
        if not self.event_impacts:
            return {
                "total_impacts": 0,
                "by_event_type": {},
                "by_impact_type": {},
                "by_confidence": {},
                "high_confidence_impacts": [],
                "most_impactful_events": []
            }
        
        by_event_type = {}
        by_impact_type = {}
        by_confidence = {}
        high_confidence_impacts = []
        event_impact_counts = {}
        
        for impact in self.event_impacts:
            # Count by event type
            event_type = impact.event.event_type
            by_event_type[event_type] = by_event_type.get(event_type, 0) + 1
            
            # Count by impact type
            impact_type = impact.impact_type
            by_impact_type[impact_type] = by_impact_type.get(impact_type, 0) + 1
            
            # Count by confidence level
            if impact.confidence >= 0.8:
                confidence_level = "high"
            elif impact.confidence >= 0.6:
                confidence_level = "medium"
            else:
                confidence_level = "low"
            by_confidence[confidence_level] = by_confidence.get(confidence_level, 0) + 1
            
            # Collect high confidence impacts
            if impact.confidence >= 0.7:
                high_confidence_impacts.append({
                    "event": impact.event.name,
                    "series": impact.series_id,
                    "impact_type": impact.impact_type,
                    "confidence": impact.confidence,
                    "time_lag": impact.time_lag,
                    "description": impact.description
                })
            
            # Count impacts per event
            event_name = impact.event.name
            event_impact_counts[event_name] = event_impact_counts.get(event_name, 0) + 1
        
        # Find most impactful events
        most_impactful_events = sorted(
            event_impact_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
        return {
            "total_impacts": len(self.event_impacts),
            "by_event_type": by_event_type,
            "by_impact_type": by_impact_type,
            "by_confidence": by_confidence,
            "high_confidence_impacts": high_confidence_impacts,
            "most_impactful_events": [
                {"event": event, "impact_count": count} 
                for event, count in most_impactful_events
            ]
        }
    
    def explain_anomaly(self, anomaly: Dict[str, Any]) -> Dict[str, Any]:
        """Provide explanation for an anomaly based on event impacts."""
        anomaly_date = anomaly['date']
        series_id = anomaly['series_id']
        
        # Find related event impacts
        related_impacts = [
            impact for impact in self.event_impacts
            if (impact.series_id == series_id and 
                impact.impact_date == anomaly_date and
                impact.impact_type == "anomaly")
        ]
        
        if not related_impacts:
            return {
                "anomaly": anomaly,
                "explanation": "No clear event-based explanation found",
                "related_events": [],
                "confidence": 0.0
            }
        
        # Sort by confidence
        related_impacts.sort(key=lambda x: x.confidence, reverse=True)
        
        # Generate explanation
        best_impact = related_impacts[0]
        explanation = f"The anomaly in {series_id} on {anomaly_date} may be explained by '{best_impact.event.name}' which occurred {best_impact.time_lag} days {'before' if best_impact.time_lag > 0 else 'after'} the anomaly."
        
        return {
            "anomaly": anomaly,
            "explanation": explanation,
            "related_events": [
                {
                    "event": impact.event.name,
                    "date": impact.event.date,
                    "confidence": impact.confidence,
                    "time_lag": impact.time_lag,
                    "impact_direction": impact.impact_direction
                }
                for impact in related_impacts[:3]  # Top 3 most likely explanations
            ],
            "confidence": best_impact.confidence
        }
