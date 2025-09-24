"""Analytics modules for WeQuo Phase 1.

This package provides lightweight analytics including:
- Deltas and percentiles
- Z-scores and anomaly detection
- Simple trend analysis
"""

from .core import AnalyticsEngine, AnalyticsResult
from .anomaly import AnomalyDetector
from .trends import TrendAnalyzer
from .deltas import DeltaCalculator

__all__ = [
    "AnalyticsEngine",
    "AnalyticsResult", 
    "AnomalyDetector",
    "TrendAnalyzer",
    "DeltaCalculator",
]
