"""Advanced analytics modules for WeQuo Phase 3.

This package provides sophisticated analytics including:
- Change-point detection in time series
- Cross-correlation analysis between series  
- Event impact tagging and attribution
- Advanced anomaly detection with explainability
"""

from .changepoint import ChangePointDetector, ChangePoint
from .correlation import CrossCorrelationAnalyzer, CorrelationResult
from .events import EventImpactTagger, Event, EventImpact
from .explainable import ExplainableAnalytics, AnalyticsExplanation

__all__ = [
    "ChangePointDetector",
    "ChangePoint",
    "CrossCorrelationAnalyzer", 
    "CorrelationResult",
    "EventImpactTagger",
    "Event",
    "EventImpact",
    "ExplainableAnalytics",
    "AnalyticsExplanation",
]
