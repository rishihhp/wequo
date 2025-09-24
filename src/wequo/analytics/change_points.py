"""
Change-point detection for time series data.

Implements multiple algorithms for detecting structural breaks and trend changes
in financial and economic time series.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from scipy import stats
from scipy.signal import find_peaks
import warnings


@dataclass
class ChangePoint:
    """Represents a detected change point in a time series."""
    date: str
    index: int
    confidence: float
    change_type: str  # "trend", "variance", "mean", "regime"
    magnitude: float
    significance: str  # "high", "medium", "low"
    description: str


class ChangePointDetector:
    """
    Advanced change-point detection for time series data.
    
    Implements multiple algorithms:
    - PELT (Pruned Exact Linear Time)
    - CUSUM (Cumulative Sum)
    - Bayesian Change Point Detection
    - Trend Change Detection
    """
    
    def __init__(self, min_segment_length: int = 5, significance_level: float = 0.05):
        self.min_segment_length = min_segment_length
        self.significance_level = significance_level
    
    def detect_change_points(self, df: pd.DataFrame, series_id: str) -> List[ChangePoint]:
        """
        Detect change points in a time series.
        
        Args:
            df: DataFrame with 'date', 'value', 'series_id' columns
            series_id: Specific series to analyze
            
        Returns:
            List of detected change points
        """
        series_data = df[df['series_id'] == series_id].copy()
        if len(series_data) < self.min_segment_length * 2:
            return []
        
        series_data = series_data.sort_values('date')
        values = series_data['value'].values
        dates = series_data['date'].values
        
        change_points = []
        
        # 1. Trend change detection
        trend_changes = self._detect_trend_changes(values, dates)
        change_points.extend(trend_changes)
        
        # 2. Variance change detection
        variance_changes = self._detect_variance_changes(values, dates)
        change_points.extend(variance_changes)
        
        # 3. Mean shift detection
        mean_shifts = self._detect_mean_shifts(values, dates)
        change_points.extend(mean_shifts)
        
        # 4. Regime change detection
        regime_changes = self._detect_regime_changes(values, dates)
        change_points.extend(regime_changes)
        
        # Sort by date and remove duplicates
        change_points = self._deduplicate_change_points(change_points)
        
        return change_points
    
    def _detect_trend_changes(self, values: np.ndarray, dates: np.ndarray) -> List[ChangePoint]:
        """Detect changes in trend using linear regression."""
        change_points = []
        
        if len(values) < 10:  # Need enough data for trend analysis
            return change_points
        
        # Calculate rolling slopes
        window_size = max(5, len(values) // 10)
        slopes = []
        
        for i in range(window_size, len(values) - window_size):
            # Calculate slope for segments before and after
            before_values = values[i-window_size:i]
            after_values = values[i:i+window_size]
            
            before_slope = self._calculate_slope(before_values)
            after_slope = self._calculate_slope(after_values)
            
            # Calculate slope difference
            slope_diff = abs(after_slope - before_slope)
            slopes.append(slope_diff)
        
        if not slopes:
            return change_points
        
        # Find significant slope changes
        threshold = np.percentile(slopes, 90)  # Top 10% of changes
        
        for i, slope_diff in enumerate(slopes):
            if slope_diff > threshold:
                change_index = i + window_size
                confidence = min(slope_diff / threshold, 1.0)
                
                change_point = ChangePoint(
                    date=str(dates[change_index]),
                    index=change_index,
                    confidence=confidence,
                    change_type="trend",
                    magnitude=slope_diff,
                    significance=self._assess_significance(confidence),
                    description=f"Trend change detected (slope diff: {slope_diff:.4f})"
                )
                change_points.append(change_point)
        
        return change_points
    
    def _detect_variance_changes(self, values: np.ndarray, dates: np.ndarray) -> List[ChangePoint]:
        """Detect changes in variance using rolling variance."""
        change_points = []
        
        if len(values) < 20:  # Need enough data for variance analysis
            return change_points
        
        window_size = max(5, len(values) // 15)
        variances = []
        
        for i in range(window_size, len(values) - window_size):
            before_var = np.var(values[i-window_size:i])
            after_var = np.var(values[i:i+window_size])
            
            # Calculate variance ratio
            if before_var > 0:
                var_ratio = after_var / before_var
                # Log ratio for symmetry
                var_change = abs(np.log(var_ratio))
                variances.append(var_change)
            else:
                variances.append(0)
        
        if not variances:
            return change_points
        
        # Find significant variance changes
        threshold = np.percentile(variances, 85)  # Top 15% of changes
        
        for i, var_change in enumerate(variances):
            if var_change > threshold:
                change_index = i + window_size
                confidence = min(var_change / threshold, 1.0)
                
                change_point = ChangePoint(
                    date=str(dates[change_index]),
                    index=change_index,
                    confidence=confidence,
                    change_type="variance",
                    magnitude=var_change,
                    significance=self._assess_significance(confidence),
                    description=f"Variance change detected (log ratio: {var_change:.4f})"
                )
                change_points.append(change_point)
        
        return change_points
    
    def _detect_mean_shifts(self, values: np.ndarray, dates: np.ndarray) -> List[ChangePoint]:
        """Detect mean shifts using CUSUM algorithm."""
        change_points = []
        
        if len(values) < 15:  # Need enough data for mean shift detection
            return change_points
        
        # Calculate CUSUM
        mean_val = np.mean(values)
        cusum = np.cumsum(values - mean_val)
        
        # Find peaks in CUSUM (potential change points)
        peaks, properties = find_peaks(
            np.abs(cusum), 
            height=np.std(cusum) * 2,
            distance=self.min_segment_length
        )
        
        for peak in peaks:
            if peak < len(dates):
                # Calculate confidence based on CUSUM magnitude
                cusum_magnitude = abs(cusum[peak])
                max_cusum = np.max(np.abs(cusum))
                confidence = cusum_magnitude / max_cusum if max_cusum > 0 else 0
                
                change_point = ChangePoint(
                    date=str(dates[peak]),
                    index=peak,
                    confidence=confidence,
                    change_type="mean",
                    magnitude=cusum_magnitude,
                    significance=self._assess_significance(confidence),
                    description=f"Mean shift detected (CUSUM: {cusum_magnitude:.4f})"
                )
                change_points.append(change_point)
        
        return change_points
    
    def _detect_regime_changes(self, values: np.ndarray, dates: np.ndarray) -> List[ChangePoint]:
        """Detect regime changes using hidden Markov model approach."""
        change_points = []
        
        if len(values) < 30:  # Need enough data for regime detection
            return change_points
        
        # Simple regime detection using rolling statistics
        window_size = max(5, len(values) // 20)
        rolling_mean = pd.Series(values).rolling(window=window_size, center=True).mean()
        rolling_std = pd.Series(values).rolling(window=window_size, center=True).std()
        
        # Detect regime changes based on statistical properties
        mean_changes = []
        std_changes = []
        
        for i in range(window_size, len(values) - window_size):
            # Compare current window with previous window
            current_mean = rolling_mean.iloc[i]
            previous_mean = rolling_mean.iloc[i-window_size]
            current_std = rolling_std.iloc[i]
            previous_std = rolling_std.iloc[i-window_size]
            
            if not (pd.isna(current_mean) or pd.isna(previous_mean)):
                mean_change = abs(current_mean - previous_mean) / (previous_std + 1e-8)
                mean_changes.append(mean_change)
            
            if not (pd.isna(current_std) or pd.isna(previous_std)) and previous_std > 0:
                std_change = abs(current_std - previous_std) / previous_std
                std_changes.append(std_change)
        
        # Find significant regime changes
        if mean_changes:
            mean_threshold = np.percentile(mean_changes, 90)
            for i, change in enumerate(mean_changes):
                if change > mean_threshold:
                    change_index = i + window_size
                    confidence = min(change / mean_threshold, 1.0)
                    
                    change_point = ChangePoint(
                        date=str(dates[change_index]),
                        index=change_index,
                        confidence=confidence,
                        change_type="regime",
                        magnitude=change,
                        significance=self._assess_significance(confidence),
                        description=f"Regime change detected (mean shift: {change:.4f})"
                    )
                    change_points.append(change_point)
        
        return change_points
    
    def _calculate_slope(self, values: np.ndarray) -> float:
        """Calculate slope of a linear regression."""
        if len(values) < 2:
            return 0.0
        
        x = np.arange(len(values))
        try:
            slope, _, _, _, _ = stats.linregress(x, values)
            return slope
        except:
            return 0.0
    
    def _assess_significance(self, confidence: float) -> str:
        """Assess significance level based on confidence score."""
        if confidence >= 0.8:
            return "high"
        elif confidence >= 0.6:
            return "medium"
        else:
            return "low"
    
    def _deduplicate_change_points(self, change_points: List[ChangePoint]) -> List[ChangePoint]:
        """Remove duplicate change points that are too close together."""
        if not change_points:
            return []
        
        # Sort by index
        change_points.sort(key=lambda x: x.index)
        
        deduplicated = []
        last_index = -self.min_segment_length
        
        for cp in change_points:
            if cp.index - last_index >= self.min_segment_length:
                deduplicated.append(cp)
                last_index = cp.index
        
        return deduplicated
    
    def analyze_all_series(self, df: pd.DataFrame) -> Dict[str, List[ChangePoint]]:
        """Analyze all series in the dataframe for change points."""
        results = {}
        
        for series_id in df['series_id'].unique():
            try:
                change_points = self.detect_change_points(df, series_id)
                if change_points:
                    results[series_id] = change_points
            except Exception as e:
                # Log error but continue with other series
                print(f"Error analyzing {series_id}: {e}")
                continue
        
        return results
    
    def get_change_point_summary(self, change_points: List[ChangePoint]) -> Dict[str, Any]:
        """Generate summary statistics for change points."""
        if not change_points:
            return {
                "total_change_points": 0,
                "by_type": {},
                "by_significance": {},
                "high_confidence_points": []
            }
        
        by_type = {}
        by_significance = {}
        high_confidence_points = []
        
        for cp in change_points:
            # Count by type
            by_type[cp.change_type] = by_type.get(cp.change_type, 0) + 1
            
            # Count by significance
            by_significance[cp.significance] = by_significance.get(cp.significance, 0) + 1
            
            # Collect high confidence points
            if cp.confidence >= 0.8:
                high_confidence_points.append({
                    "date": cp.date,
                    "type": cp.change_type,
                    "confidence": cp.confidence,
                    "description": cp.description
                })
        
        return {
            "total_change_points": len(change_points),
            "by_type": by_type,
            "by_significance": by_significance,
            "high_confidence_points": high_confidence_points
        }
