from __future__ import annotations
import numpy as np
import pandas as pd
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from scipy import stats
import warnings

try:
    import ruptures as rpt
    RUPTURES_AVAILABLE = True
except ImportError:
    RUPTURES_AVAILABLE = False
    warnings.warn("ruptures library not available. Change point detection will use basic methods.")


@dataclass
class ChangePoint:
    """Represents a detected change point in a time series."""
    
    series_id: str
    timestamp: datetime
    index: int
    change_type: str  # mean, variance, trend, regime
    confidence: float  # 0.0 to 1.0
    magnitude: float  # Size of the change
    description: str
    statistical_significance: float  # p-value
    context: Dict[str, Any]  # Additional context about the change


class ChangePointDetector:
    """Advanced change point detection for time series data."""
    
    def __init__(self, 
                 min_size: int = 5,
                 max_changepoints: int = 10,
                 confidence_threshold: float = 0.8):
        """
        Initialize change point detector.
        
        Args:
            min_size: Minimum segment size between change points
            max_changepoints: Maximum number of change points to detect
            confidence_threshold: Minimum confidence for reporting change points
        """
        self.min_size = min_size
        self.max_changepoints = max_changepoints
        self.confidence_threshold = confidence_threshold
    
    def detect_changepoints(self, df: pd.DataFrame) -> List[ChangePoint]:
        """
        Detect change points across all series in the DataFrame.
        
        Args:
            df: DataFrame with columns ['date', 'value', 'series_id', 'source']
            
        Returns:
            List of detected change points
        """
        changepoints = []
        
        if df.empty or 'series_id' not in df.columns:
            return changepoints
        
        # Detect change points for each series
        for series_id in df['series_id'].unique():
            series_data = df[df['series_id'] == series_id].copy()
            series_data = series_data.sort_values('date').reset_index(drop=True)
            
            if len(series_data) < self.min_size * 2:
                continue
            
            # Detect different types of change points
            series_changepoints = []
            
            # Mean change detection
            if RUPTURES_AVAILABLE:
                series_changepoints.extend(self._detect_mean_changes_ruptures(series_data, series_id))
            else:
                series_changepoints.extend(self._detect_mean_changes_basic(series_data, series_id))
            
            # Variance change detection
            series_changepoints.extend(self._detect_variance_changes(series_data, series_id))
            
            # Trend change detection
            series_changepoints.extend(self._detect_trend_changes(series_data, series_id))
            
            # Regime change detection (volatility shifts)
            series_changepoints.extend(self._detect_regime_changes(series_data, series_id))
            
            # Filter by confidence and merge nearby changepoints
            filtered_changepoints = self._filter_and_merge_changepoints(series_changepoints)
            changepoints.extend(filtered_changepoints)
        
        # Sort by confidence (highest first)
        changepoints.sort(key=lambda x: x.confidence, reverse=True)
        
        return changepoints[:self.max_changepoints]
    
    def _detect_mean_changes_ruptures(self, series_data: pd.DataFrame, series_id: str) -> List[ChangePoint]:
        """Detect mean change points using ruptures library."""
        changepoints = []
        
        try:
            values = series_data['value'].values
            
            # Use PELT (Pruned Exact Linear Time) algorithm
            algo = rpt.Pelt(model="rbf").fit(values)
            change_indices = algo.predict(pen=10)
            
            # Remove the last index (end of series)
            change_indices = change_indices[:-1]
            
            for idx in change_indices:
                if idx < len(series_data):
                    # Calculate change magnitude
                    before_mean = values[max(0, idx-self.min_size):idx].mean()
                    after_mean = values[idx:min(len(values), idx+self.min_size)].mean()
                    magnitude = abs(after_mean - before_mean)
                    
                    # Estimate confidence using statistical test
                    before_values = values[max(0, idx-self.min_size):idx]
                    after_values = values[idx:min(len(values), idx+self.min_size)]
                    
                    if len(before_values) > 1 and len(after_values) > 1:
                        t_stat, p_value = stats.ttest_ind(before_values, after_values)
                        confidence = 1 - p_value  # Convert p-value to confidence
                        
                        changepoints.append(ChangePoint(
                            series_id=series_id,
                            timestamp=pd.to_datetime(series_data.iloc[idx]['date']),
                            index=idx,
                            change_type="mean",
                            confidence=confidence,
                            magnitude=magnitude,
                            description=f"Mean shift from {before_mean:.3f} to {after_mean:.3f}",
                            statistical_significance=p_value,
                            context={
                                "before_mean": before_mean,
                                "after_mean": after_mean,
                                "before_std": before_values.std(),
                                "after_std": after_values.std(),
                                "method": "ruptures_pelt"
                            }
                        ))
        
        except Exception as e:
            # Fall back to basic method
            return self._detect_mean_changes_basic(series_data, series_id)
        
        return changepoints
    
    def _detect_mean_changes_basic(self, series_data: pd.DataFrame, series_id: str) -> List[ChangePoint]:
        """Detect mean change points using basic sliding window approach."""
        changepoints = []
        values = series_data['value'].values
        
        if len(values) < self.min_size * 2:
            return changepoints
        
        # Sliding window approach
        for i in range(self.min_size, len(values) - self.min_size):
            # Compare segments before and after potential change point
            before = values[max(0, i-self.min_size):i]
            after = values[i:min(len(values), i+self.min_size)]
            
            if len(before) > 1 and len(after) > 1:
                # Statistical test for mean difference
                t_stat, p_value = stats.ttest_ind(before, after)
                
                if p_value < 0.05:  # Significant change
                    confidence = 1 - p_value
                    magnitude = abs(after.mean() - before.mean())
                    
                    changepoints.append(ChangePoint(
                        series_id=series_id,
                        timestamp=pd.to_datetime(series_data.iloc[i]['date']),
                        index=i,
                        change_type="mean",
                        confidence=confidence,
                        magnitude=magnitude,
                        description=f"Mean shift from {before.mean():.3f} to {after.mean():.3f}",
                        statistical_significance=p_value,
                        context={
                            "before_mean": before.mean(),
                            "after_mean": after.mean(),
                            "before_std": before.std(),
                            "after_std": after.std(),
                            "method": "sliding_window"
                        }
                    ))
        
        return changepoints
    
    def _detect_variance_changes(self, series_data: pd.DataFrame, series_id: str) -> List[ChangePoint]:
        """Detect variance change points using F-test."""
        changepoints = []
        values = series_data['value'].values
        
        if len(values) < self.min_size * 2:
            return changepoints
        
        for i in range(self.min_size, len(values) - self.min_size):
            before = values[max(0, i-self.min_size):i]
            after = values[i:min(len(values), i+self.min_size)]
            
            if len(before) > 2 and len(after) > 2:
                # F-test for variance equality
                f_stat = before.var() / after.var() if after.var() > 0 else float('inf')
                
                # Calculate p-value for F-test
                df1, df2 = len(before) - 1, len(after) - 1
                if f_stat != float('inf'):
                    p_value = 2 * min(stats.f.cdf(f_stat, df1, df2), 1 - stats.f.cdf(f_stat, df1, df2))
                else:
                    p_value = 0.0
                
                if p_value < 0.05:  # Significant variance change
                    confidence = 1 - p_value
                    magnitude = abs(after.std() - before.std())
                    
                    changepoints.append(ChangePoint(
                        series_id=series_id,
                        timestamp=pd.to_datetime(series_data.iloc[i]['date']),
                        index=i,
                        change_type="variance",
                        confidence=confidence,
                        magnitude=magnitude,
                        description=f"Variance shift from {before.std():.3f} to {after.std():.3f}",
                        statistical_significance=p_value,
                        context={
                            "before_variance": before.var(),
                            "after_variance": after.var(),
                            "f_statistic": f_stat,
                            "method": "f_test"
                        }
                    ))
        
        return changepoints
    
    def _detect_trend_changes(self, series_data: pd.DataFrame, series_id: str) -> List[ChangePoint]:
        """Detect trend change points using linear regression slope comparison."""
        changepoints = []
        values = series_data['value'].values
        
        if len(values) < self.min_size * 2:
            return changepoints
        
        for i in range(self.min_size, len(values) - self.min_size):
            # Fit linear regression to segments before and after
            before_x = np.arange(max(0, i-self.min_size), i)
            before_y = values[max(0, i-self.min_size):i]
            
            after_x = np.arange(i, min(len(values), i+self.min_size))
            after_y = values[i:min(len(values), i+self.min_size)]
            
            if len(before_x) > 2 and len(after_x) > 2:
                # Calculate slopes
                before_slope, _, before_r, before_p, _ = stats.linregress(before_x, before_y)
                after_slope, _, after_r, after_p, _ = stats.linregress(after_x, after_y)
                
                # Test for significant slope difference
                slope_diff = abs(after_slope - before_slope)
                
                # Use combined significance from both regressions
                combined_p = (before_p + after_p) / 2
                slope_significance = 1 - combined_p if combined_p < 0.05 and slope_diff > 0.01 else 0
                
                if slope_significance > 0.8:
                    changepoints.append(ChangePoint(
                        series_id=series_id,
                        timestamp=pd.to_datetime(series_data.iloc[i]['date']),
                        index=i,
                        change_type="trend",
                        confidence=slope_significance,
                        magnitude=slope_diff,
                        description=f"Trend change from {before_slope:.4f} to {after_slope:.4f}",
                        statistical_significance=combined_p,
                        context={
                            "before_slope": before_slope,
                            "after_slope": after_slope,
                            "before_r_squared": before_r**2,
                            "after_r_squared": after_r**2,
                            "method": "linear_regression"
                        }
                    ))
        
        return changepoints
    
    def _detect_regime_changes(self, series_data: pd.DataFrame, series_id: str) -> List[ChangePoint]:
        """Detect regime changes using rolling statistics."""
        changepoints = []
        
        if len(series_data) < 20:  # Need sufficient data for regime detection
            return changepoints
        
        values = series_data['value'].values
        
        # Calculate rolling statistics
        window = max(5, len(values) // 10)
        rolling_mean = pd.Series(values).rolling(window=window, center=True).mean()
        rolling_std = pd.Series(values).rolling(window=window, center=True).std()
        
        # Detect sudden changes in rolling statistics
        mean_changes = np.diff(rolling_mean.dropna())
        std_changes = np.diff(rolling_std.dropna())
        
        # Find significant jumps
        mean_threshold = np.std(mean_changes) * 2
        std_threshold = np.std(std_changes) * 2
        
        for i, (mean_change, std_change) in enumerate(zip(mean_changes, std_changes)):
            if abs(mean_change) > mean_threshold or abs(std_change) > std_threshold:
                actual_index = i + window // 2  # Adjust for rolling window offset
                
                if actual_index < len(series_data):
                    magnitude = max(abs(mean_change), abs(std_change))
                    confidence = min(1.0, magnitude / (mean_threshold + std_threshold))
                    
                    if confidence > self.confidence_threshold:
                        changepoints.append(ChangePoint(
                            series_id=series_id,
                            timestamp=pd.to_datetime(series_data.iloc[actual_index]['date']),
                            index=actual_index,
                            change_type="regime",
                            confidence=confidence,
                            magnitude=magnitude,
                            description=f"Regime change detected (volatility shift)",
                            statistical_significance=1 - confidence,  # Approximate
                            context={
                                "mean_change": mean_change,
                                "std_change": std_change,
                                "rolling_window": window,
                                "method": "rolling_statistics"
                            }
                        ))
        
        return changepoints
    
    def _filter_and_merge_changepoints(self, changepoints: List[ChangePoint]) -> List[ChangePoint]:
        """Filter changepoints by confidence and merge nearby ones."""
        # Filter by confidence threshold
        filtered = [cp for cp in changepoints if cp.confidence >= self.confidence_threshold]
        
        if not filtered:
            return []
        
        # Sort by index
        filtered.sort(key=lambda x: x.index)
        
        # Merge nearby changepoints (within min_size distance)
        merged = []
        i = 0
        
        while i < len(filtered):
            current = filtered[i]
            
            # Look for nearby changepoints to merge
            nearby = [current]
            j = i + 1
            
            while j < len(filtered) and filtered[j].index - current.index < self.min_size:
                nearby.append(filtered[j])
                j += 1
            
            # Keep the one with highest confidence
            best = max(nearby, key=lambda x: x.confidence)
            merged.append(best)
            
            i = j
        
        return merged
    
    def get_changepoint_summary(self, changepoints: List[ChangePoint]) -> Dict[str, Any]:
        """Generate summary statistics for detected changepoints."""
        if not changepoints:
            return {
                "total_changepoints": 0,
                "by_type": {},
                "avg_confidence": 0.0,
                "most_significant": None
            }
        
        # Count by type
        by_type = {}
        for cp in changepoints:
            by_type[cp.change_type] = by_type.get(cp.change_type, 0) + 1
        
        # Find most significant
        most_significant = max(changepoints, key=lambda x: x.confidence)
        
        return {
            "total_changepoints": len(changepoints),
            "by_type": by_type,
            "avg_confidence": sum(cp.confidence for cp in changepoints) / len(changepoints),
            "most_significant": {
                "series_id": most_significant.series_id,
                "timestamp": most_significant.timestamp.isoformat(),
                "type": most_significant.change_type,
                "confidence": most_significant.confidence,
                "description": most_significant.description
            },
            "series_with_changes": len(set(cp.series_id for cp in changepoints))
        }
