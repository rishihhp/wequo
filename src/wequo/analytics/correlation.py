"""
Cross-correlation analysis for time series data.

Analyzes relationships between different economic and financial indicators
to identify leading/lagging relationships and causal patterns.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from scipy import stats
from scipy.signal import correlate
import warnings


@dataclass
class CorrelationResult:
    """Represents a correlation analysis result."""
    series_1: str
    series_2: str
    correlation_type: str  # "pearson", "spearman", "cross_correlation"
    correlation_value: float
    p_value: float
    lag: int  # For cross-correlation
    significance: str  # "high", "medium", "low"
    relationship_type: str  # "positive", "negative", "none"
    strength: str  # "strong", "moderate", "weak"
    description: str


class CorrelationAnalyzer:
    """
    Advanced correlation analysis for time series data.
    
    Features:
    - Pearson and Spearman correlations
    - Cross-correlation with lag analysis
    - Rolling correlation analysis
    - Significance testing
    - Relationship strength assessment
    """
    
    def __init__(self, min_data_points: int = 10, significance_level: float = 0.05):
        self.min_data_points = min_data_points
        self.significance_level = significance_level
    
    def analyze_correlations(self, df: pd.DataFrame) -> List[CorrelationResult]:
        """
        Analyze correlations between all pairs of series.
        
        Args:
            df: DataFrame with 'date', 'value', 'series_id' columns
            
        Returns:
            List of correlation results
        """
        results = []
        series_ids = df['series_id'].unique()
        
        # Get all unique pairs
        for i, series_1 in enumerate(series_ids):
            for series_2 in series_ids[i+1:]:  # Avoid duplicates and self-correlation
                try:
                    correlation_results = self._analyze_pair(df, series_1, series_2)
                    results.extend(correlation_results)
                except Exception as e:
                    print(f"Error analyzing correlation between {series_1} and {series_2}: {e}")
                    continue
        
        return results
    
    def _analyze_pair(self, df: pd.DataFrame, series_1: str, series_2: str) -> List[CorrelationResult]:
        """Analyze correlation between a pair of series."""
        results = []
        
        # Get data for both series
        data_1 = df[df['series_id'] == series_1].sort_values('date')
        data_2 = df[df['series_id'] == series_2].sort_values('date')
        
        if len(data_1) < self.min_data_points or len(data_2) < self.min_data_points:
            return results
        
        # Align data by date
        aligned_data = self._align_series(data_1, data_2)
        if aligned_data is None or len(aligned_data) < self.min_data_points:
            return results
        
        values_1 = aligned_data['value_1'].values
        values_2 = aligned_data['value_2'].values
        
        # 1. Pearson correlation
        pearson_result = self._calculate_pearson_correlation(
            series_1, series_2, values_1, values_2
        )
        if pearson_result:
            results.append(pearson_result)
        
        # 2. Spearman correlation
        spearman_result = self._calculate_spearman_correlation(
            series_1, series_2, values_1, values_2
        )
        if spearman_result:
            results.append(spearman_result)
        
        # 3. Cross-correlation with lag analysis
        cross_corr_results = self._calculate_cross_correlation(
            series_1, series_2, values_1, values_2
        )
        results.extend(cross_corr_results)
        
        return results
    
    def _align_series(self, data_1: pd.DataFrame, data_2: pd.DataFrame) -> Optional[pd.DataFrame]:
        """Align two time series by date."""
        try:
            # Convert dates to datetime if needed
            data_1 = data_1.copy()
            data_2 = data_2.copy()
            data_1['date'] = pd.to_datetime(data_1['date'])
            data_2['date'] = pd.to_datetime(data_2['date'])
            
            # Merge on date
            merged = pd.merge(
                data_1[['date', 'value']].rename(columns={'value': 'value_1'}),
                data_2[['date', 'value']].rename(columns={'value': 'value_2'}),
                on='date',
                how='inner'
            )
            
            # Remove rows with NaN values
            merged = merged.dropna()
            
            return merged if len(merged) > 0 else None
            
        except Exception as e:
            print(f"Error aligning series: {e}")
            return None
    
    def _calculate_pearson_correlation(
        self, 
        series_1: str, 
        series_2: str, 
        values_1: np.ndarray, 
        values_2: np.ndarray
    ) -> Optional[CorrelationResult]:
        """Calculate Pearson correlation."""
        try:
            correlation, p_value = stats.pearsonr(values_1, values_2)
            
            if np.isnan(correlation) or np.isnan(p_value):
                return None
            
            significance = self._assess_significance(p_value)
            relationship_type = self._assess_relationship_type(correlation)
            strength = self._assess_strength(abs(correlation))
            
            return CorrelationResult(
                series_1=series_1,
                series_2=series_2,
                correlation_type="pearson",
                correlation_value=correlation,
                p_value=p_value,
                lag=0,
                significance=significance,
                relationship_type=relationship_type,
                strength=strength,
                description=f"Pearson correlation: {correlation:.3f} (p={p_value:.3f})"
            )
            
        except Exception as e:
            print(f"Error calculating Pearson correlation: {e}")
            return None
    
    def _calculate_spearman_correlation(
        self, 
        series_1: str, 
        series_2: str, 
        values_1: np.ndarray, 
        values_2: np.ndarray
    ) -> Optional[CorrelationResult]:
        """Calculate Spearman correlation."""
        try:
            correlation, p_value = stats.spearmanr(values_1, values_2)
            
            if np.isnan(correlation) or np.isnan(p_value):
                return None
            
            significance = self._assess_significance(p_value)
            relationship_type = self._assess_relationship_type(correlation)
            strength = self._assess_strength(abs(correlation))
            
            return CorrelationResult(
                series_1=series_1,
                series_2=series_2,
                correlation_type="spearman",
                correlation_value=correlation,
                p_value=p_value,
                lag=0,
                significance=significance,
                relationship_type=relationship_type,
                strength=strength,
                description=f"Spearman correlation: {correlation:.3f} (p={p_value:.3f})"
            )
            
        except Exception as e:
            print(f"Error calculating Spearman correlation: {e}")
            return None
    
    def _calculate_cross_correlation(
        self, 
        series_1: str, 
        series_2: str, 
        values_1: np.ndarray, 
        values_2: np.ndarray
    ) -> List[CorrelationResult]:
        """Calculate cross-correlation with lag analysis."""
        results = []
        
        try:
            # Calculate cross-correlation
            max_lag = min(len(values_1) // 4, 20)  # Limit lag to reasonable range
            
            if max_lag < 1:
                return results
            
            # Normalize the signals
            values_1_norm = (values_1 - np.mean(values_1)) / (np.std(values_1) + 1e-8)
            values_2_norm = (values_2 - np.mean(values_2)) / (np.std(values_2) + 1e-8)
            
            # Calculate cross-correlation
            correlation = correlate(values_1_norm, values_2_norm, mode='full')
            lags = np.arange(-len(values_2_norm) + 1, len(values_1_norm))
            
            # Limit to reasonable lag range
            valid_indices = np.where((lags >= -max_lag) & (lags <= max_lag))[0]
            if len(valid_indices) == 0:
                return results
            
            correlation_limited = correlation[valid_indices]
            lags_limited = lags[valid_indices]
            
            # Find the lag with maximum correlation
            max_corr_idx = np.argmax(np.abs(correlation_limited))
            max_corr_value = correlation_limited[max_corr_idx]
            optimal_lag = lags_limited[max_corr_idx]
            
            # Calculate significance (simplified)
            # In practice, you might want to use more sophisticated significance testing
            p_value = self._estimate_cross_corr_p_value(max_corr_value, len(values_1))
            
            significance = self._assess_significance(p_value)
            relationship_type = self._assess_relationship_type(max_corr_value)
            strength = self._assess_strength(abs(max_corr_value))
            
            # Determine leading/lagging relationship
            if optimal_lag > 0:
                lead_lag_desc = f"{series_1} leads {series_2} by {optimal_lag} periods"
            elif optimal_lag < 0:
                lead_lag_desc = f"{series_2} leads {series_1} by {abs(optimal_lag)} periods"
            else:
                lead_lag_desc = "No significant lead-lag relationship"
            
            result = CorrelationResult(
                series_1=series_1,
                series_2=series_2,
                correlation_type="cross_correlation",
                correlation_value=max_corr_value,
                p_value=p_value,
                lag=optimal_lag,
                significance=significance,
                relationship_type=relationship_type,
                strength=strength,
                description=f"Cross-correlation: {max_corr_value:.3f} at lag {optimal_lag} - {lead_lag_desc}"
            )
            results.append(result)
            
        except Exception as e:
            print(f"Error calculating cross-correlation: {e}")
        
        return results
    
    def _estimate_cross_corr_p_value(self, correlation: float, n: int) -> float:
        """Estimate p-value for cross-correlation (simplified approach)."""
        # This is a simplified approach - in practice, you might want to use
        # more sophisticated significance testing for cross-correlation
        if n < 3:
            return 1.0
        
        # Handle edge cases
        if abs(correlation) >= 1.0:
            return 0.0
        
        try:
            # Use t-test approximation
            t_stat = correlation * np.sqrt((n - 2) / (1 - correlation**2 + 1e-8))
            p_value = 2 * (1 - stats.t.cdf(abs(t_stat), n - 2))
            
            return min(max(p_value, 0.0), 1.0)
        except (ValueError, OverflowError):
            return 1.0
    
    def _assess_significance(self, p_value: float) -> str:
        """Assess statistical significance."""
        if p_value < 0.01:
            return "high"
        elif p_value < 0.05:
            return "medium"
        else:
            return "low"
    
    def _assess_relationship_type(self, correlation: float) -> str:
        """Assess the type of relationship."""
        if correlation > 0.1:
            return "positive"
        elif correlation < -0.1:
            return "negative"
        else:
            return "none"
    
    def _assess_strength(self, abs_correlation: float) -> str:
        """Assess the strength of correlation."""
        if abs_correlation >= 0.7:
            return "strong"
        elif abs_correlation >= 0.3:
            return "moderate"
        else:
            return "weak"
    
    def get_correlation_summary(self, results: List[CorrelationResult]) -> Dict[str, Any]:
        """Generate summary statistics for correlation results."""
        if not results:
            return {
                "total_correlations": 0,
                "by_type": {},
                "by_significance": {},
                "by_strength": {},
                "strong_correlations": [],
                "leading_indicators": []
            }
        
        by_type = {}
        by_significance = {}
        by_strength = {}
        strong_correlations = []
        leading_indicators = []
        
        for result in results:
            # Count by type
            by_type[result.correlation_type] = by_type.get(result.correlation_type, 0) + 1
            
            # Count by significance
            by_significance[result.significance] = by_significance.get(result.significance, 0) + 1
            
            # Count by strength
            by_strength[result.strength] = by_strength.get(result.strength, 0) + 1
            
            # Collect strong correlations
            if result.strength == "strong" and result.significance in ["high", "medium"]:
                strong_correlations.append({
                    "series_1": result.series_1,
                    "series_2": result.series_2,
                    "correlation": result.correlation_value,
                    "type": result.correlation_type,
                    "description": result.description
                })
            
            # Collect leading indicators (cross-correlation with significant lag)
            if (result.correlation_type == "cross_correlation" and 
                abs(result.lag) > 0 and 
                result.significance in ["high", "medium"]):
                leading_indicators.append({
                    "leading_series": result.series_1 if result.lag > 0 else result.series_2,
                    "lagging_series": result.series_2 if result.lag > 0 else result.series_1,
                    "lag": abs(result.lag),
                    "correlation": result.correlation_value,
                    "description": result.description
                })
        
        return {
            "total_correlations": len(results),
            "by_type": by_type,
            "by_significance": by_significance,
            "by_strength": by_strength,
            "strong_correlations": strong_correlations,
            "leading_indicators": leading_indicators
        }
    
    def analyze_rolling_correlations(
        self, 
        df: pd.DataFrame, 
        series_1: str, 
        series_2: str, 
        window_size: int = 30
    ) -> pd.DataFrame:
        """Calculate rolling correlations between two series."""
        try:
            # Get aligned data
            data_1 = df[df['series_id'] == series_1].sort_values('date')
            data_2 = df[df['series_id'] == series_2].sort_values('date')
            
            aligned_data = self._align_series(data_1, data_2)
            if aligned_data is None:
                return pd.DataFrame()
            
            # Calculate rolling correlation
            rolling_corr = aligned_data['value_1'].rolling(
                window=window_size, 
                min_periods=max(5, window_size // 2)
            ).corr(aligned_data['value_2'])
            
            result_df = aligned_data[['date']].copy()
            result_df['rolling_correlation'] = rolling_corr
            result_df['series_1'] = series_1
            result_df['series_2'] = series_2
            result_df['window_size'] = window_size
            
            return result_df.dropna()
            
        except Exception as e:
            print(f"Error calculating rolling correlations: {e}")
            return pd.DataFrame()
