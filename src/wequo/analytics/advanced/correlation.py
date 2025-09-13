from __future__ import annotations
import numpy as np
import pandas as pd
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from scipy import stats
from scipy.signal import find_peaks
import warnings

try:
    import statsmodels.api as sm
    from statsmodels.tsa.stattools import ccf, grangercausalitytests
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False
    warnings.warn("statsmodels library not available. Advanced correlation analysis will use basic methods.")


@dataclass
class CorrelationResult:
    """Represents a cross-correlation analysis result."""
    
    series1_id: str
    series2_id: str
    correlation_type: str  # pearson, spearman, cross_correlation, granger
    correlation_coefficient: float
    statistical_significance: float  # p-value
    lag: int  # Time lag (0 for contemporaneous)
    confidence_interval: Tuple[float, float]
    description: str
    context: Dict[str, Any]


@dataclass
class LeadLagRelationship:
    """Represents a lead-lag relationship between two series."""
    
    leading_series: str
    lagging_series: str
    optimal_lag: int  # In time periods
    correlation_at_lag: float
    confidence: float
    economic_interpretation: str


class CrossCorrelationAnalyzer:
    """Advanced cross-correlation analysis between time series."""
    
    def __init__(self, 
                 max_lags: int = 10,
                 significance_level: float = 0.05,
                 min_overlap_periods: int = 10):
        """
        Initialize cross-correlation analyzer.
        
        Args:
            max_lags: Maximum number of lags to consider
            significance_level: Significance level for statistical tests
            min_overlap_periods: Minimum overlapping periods required
        """
        self.max_lags = max_lags
        self.significance_level = significance_level
        self.min_overlap_periods = min_overlap_periods
    
    def analyze_all_correlations(self, df: pd.DataFrame) -> List[CorrelationResult]:
        """
        Analyze correlations between all pairs of series.
        
        Args:
            df: DataFrame with columns ['date', 'value', 'series_id', 'source']
            
        Returns:
            List of correlation results
        """
        results = []
        
        if df.empty or 'series_id' not in df.columns:
            return results
        
        # Get unique series
        series_ids = df['series_id'].unique()
        
        # Analyze all pairs
        for i, series1 in enumerate(series_ids):
            for series2 in series_ids[i+1:]:  # Avoid duplicates and self-correlation
                
                # Get aligned data for both series
                aligned_data = self._align_series_data(df, series1, series2)
                
                if len(aligned_data) < self.min_overlap_periods:
                    continue
                
                # Perform different types of correlation analysis
                pair_results = []
                
                # 1. Pearson correlation
                pair_results.extend(self._pearson_correlation(aligned_data, series1, series2))
                
                # 2. Spearman correlation (rank-based)
                pair_results.extend(self._spearman_correlation(aligned_data, series1, series2))
                
                # 3. Cross-correlation with lags
                if STATSMODELS_AVAILABLE:
                    pair_results.extend(self._cross_correlation_analysis(aligned_data, series1, series2))
                
                # 4. Granger causality (if sufficient data)
                if STATSMODELS_AVAILABLE and len(aligned_data) > 20:
                    pair_results.extend(self._granger_causality_analysis(aligned_data, series1, series2))
                
                results.extend(pair_results)
        
        # Sort by absolute correlation strength
        results.sort(key=lambda x: abs(x.correlation_coefficient), reverse=True)
        
        return results
    
    def find_lead_lag_relationships(self, df: pd.DataFrame) -> List[LeadLagRelationship]:
        """
        Identify lead-lag relationships between series.
        
        Args:
            df: DataFrame with time series data
            
        Returns:
            List of lead-lag relationships
        """
        relationships = []
        correlation_results = self.analyze_all_correlations(df)
        
        # Group by series pairs
        pair_correlations = {}
        for result in correlation_results:
            if result.correlation_type == "cross_correlation":
                pair_key = (result.series1_id, result.series2_id)
                if pair_key not in pair_correlations:
                    pair_correlations[pair_key] = []
                pair_correlations[pair_key].append(result)
        
        # Find optimal lags for each pair
        for (series1, series2), lag_results in pair_correlations.items():
            if not lag_results:
                continue
            
            # Find the lag with maximum absolute correlation
            best_result = max(lag_results, key=lambda x: abs(x.correlation_coefficient))
            
            if abs(best_result.correlation_coefficient) > 0.3:  # Threshold for meaningful correlation
                # Determine lead-lag relationship
                if best_result.lag > 0:
                    leading_series = series1
                    lagging_series = series2
                    optimal_lag = best_result.lag
                elif best_result.lag < 0:
                    leading_series = series2
                    lagging_series = series1
                    optimal_lag = abs(best_result.lag)
                else:
                    # Contemporaneous correlation
                    leading_series = series1
                    lagging_series = series2
                    optimal_lag = 0
                
                # Generate economic interpretation
                interpretation = self._generate_economic_interpretation(
                    leading_series, lagging_series, optimal_lag, best_result.correlation_coefficient
                )
                
                relationships.append(LeadLagRelationship(
                    leading_series=leading_series,
                    lagging_series=lagging_series,
                    optimal_lag=optimal_lag,
                    correlation_at_lag=best_result.correlation_coefficient,
                    confidence=1 - best_result.statistical_significance,
                    economic_interpretation=interpretation
                ))
        
        # Sort by correlation strength
        relationships.sort(key=lambda x: abs(x.correlation_at_lag), reverse=True)
        
        return relationships
    
    def _align_series_data(self, df: pd.DataFrame, series1_id: str, series2_id: str) -> pd.DataFrame:
        """Align two time series on common dates."""
        
        # Get data for both series
        s1_data = df[df['series_id'] == series1_id][['date', 'value']].copy()
        s2_data = df[df['series_id'] == series2_id][['date', 'value']].copy()
        
        # Convert dates to datetime
        s1_data['date'] = pd.to_datetime(s1_data['date'])
        s2_data['date'] = pd.to_datetime(s2_data['date'])
        
        # Merge on date (inner join to get common dates)
        aligned = pd.merge(s1_data, s2_data, on='date', suffixes=('_1', '_2'))
        aligned = aligned.sort_values('date').reset_index(drop=True)
        
        return aligned
    
    def _pearson_correlation(self, aligned_data: pd.DataFrame, series1: str, series2: str) -> List[CorrelationResult]:
        """Calculate Pearson correlation coefficient."""
        if len(aligned_data) < 3:
            return []
        
        x = aligned_data['value_1'].values
        y = aligned_data['value_2'].values
        
        # Remove any NaN values
        mask = ~(np.isnan(x) | np.isnan(y))
        x, y = x[mask], y[mask]
        
        if len(x) < 3:
            return []
        
        # Calculate Pearson correlation
        correlation, p_value = stats.pearsonr(x, y)
        
        # Calculate confidence interval
        n = len(x)
        if n > 3:
            # Fisher transformation for confidence interval
            z = 0.5 * np.log((1 + correlation) / (1 - correlation))
            z_se = 1 / np.sqrt(n - 3)
            z_critical = stats.norm.ppf(1 - self.significance_level / 2)
            
            z_lower = z - z_critical * z_se
            z_upper = z + z_critical * z_se
            
            # Transform back
            ci_lower = (np.exp(2 * z_lower) - 1) / (np.exp(2 * z_lower) + 1)
            ci_upper = (np.exp(2 * z_upper) - 1) / (np.exp(2 * z_upper) + 1)
        else:
            ci_lower, ci_upper = -1, 1
        
        return [CorrelationResult(
            series1_id=series1,
            series2_id=series2,
            correlation_type="pearson",
            correlation_coefficient=correlation,
            statistical_significance=p_value,
            lag=0,
            confidence_interval=(ci_lower, ci_upper),
            description=f"Pearson correlation: {correlation:.3f} (p={p_value:.3f})",
            context={
                "n_observations": len(x),
                "method": "pearson",
                "contemporaneous": True
            }
        )]
    
    def _spearman_correlation(self, aligned_data: pd.DataFrame, series1: str, series2: str) -> List[CorrelationResult]:
        """Calculate Spearman rank correlation coefficient."""
        if len(aligned_data) < 3:
            return []
        
        x = aligned_data['value_1'].values
        y = aligned_data['value_2'].values
        
        # Remove any NaN values
        mask = ~(np.isnan(x) | np.isnan(y))
        x, y = x[mask], y[mask]
        
        if len(x) < 3:
            return []
        
        # Calculate Spearman correlation
        correlation, p_value = stats.spearmanr(x, y)
        
        # Approximate confidence interval (less precise than Pearson)
        n = len(x)
        se = 1 / np.sqrt(n - 3)
        z_critical = stats.norm.ppf(1 - self.significance_level / 2)
        ci_lower = max(-1, correlation - z_critical * se)
        ci_upper = min(1, correlation + z_critical * se)
        
        return [CorrelationResult(
            series1_id=series1,
            series2_id=series2,
            correlation_type="spearman",
            correlation_coefficient=correlation,
            statistical_significance=p_value,
            lag=0,
            confidence_interval=(ci_lower, ci_upper),
            description=f"Spearman correlation: {correlation:.3f} (p={p_value:.3f})",
            context={
                "n_observations": len(x),
                "method": "spearman_rank",
                "contemporaneous": True
            }
        )]
    
    def _cross_correlation_analysis(self, aligned_data: pd.DataFrame, series1: str, series2: str) -> List[CorrelationResult]:
        """Perform cross-correlation analysis with lags."""
        if not STATSMODELS_AVAILABLE or len(aligned_data) < 10:
            return []
        
        results = []
        x = aligned_data['value_1'].values
        y = aligned_data['value_2'].values
        
        # Remove any NaN values
        mask = ~(np.isnan(x) | np.isnan(y))
        x, y = x[mask], y[mask]
        
        if len(x) < 10:
            return []
        
        try:
            # Calculate cross-correlation function
            max_lags = min(self.max_lags, len(x) // 4)  # Don't use too many lags
            
            # Cross-correlation using statsmodels
            ccf_result = ccf(x, y, nlags=max_lags, fft=True)
            
            # Find significant correlations
            for lag in range(-max_lags, max_lags + 1):
                lag_idx = lag + max_lags
                if lag_idx < len(ccf_result):
                    correlation = ccf_result[lag_idx]
                    
                    # Approximate significance test (assumes white noise)
                    # Critical value for cross-correlation under null hypothesis
                    critical_value = 1.96 / np.sqrt(len(x))
                    
                    if abs(correlation) > critical_value:
                        # Approximate p-value
                        z_score = correlation * np.sqrt(len(x))
                        p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))
                        
                        description = f"Cross-correlation at lag {lag}: {correlation:.3f}"
                        if lag > 0:
                            description += f" ({series1} leads {series2} by {lag} periods)"
                        elif lag < 0:
                            description += f" ({series2} leads {series1} by {abs(lag)} periods)"
                        else:
                            description += " (contemporaneous)"
                        
                        results.append(CorrelationResult(
                            series1_id=series1,
                            series2_id=series2,
                            correlation_type="cross_correlation",
                            correlation_coefficient=correlation,
                            statistical_significance=p_value,
                            lag=lag,
                            confidence_interval=(-1, 1),  # Simplified
                            description=description,
                            context={
                                "method": "cross_correlation_function",
                                "max_lags": max_lags,
                                "critical_value": critical_value
                            }
                        ))
        
        except Exception as e:
            # If CCF fails, fall back to manual lag correlation
            results = self._manual_lag_correlation(x, y, series1, series2)
        
        return results
    
    def _manual_lag_correlation(self, x: np.ndarray, y: np.ndarray, series1: str, series2: str) -> List[CorrelationResult]:
        """Manual lag correlation calculation as fallback."""
        results = []
        max_lags = min(self.max_lags, len(x) // 4)
        
        for lag in range(-max_lags, max_lags + 1):
            if lag == 0:
                x_lag, y_lag = x, y
            elif lag > 0:
                # x leads y by lag periods
                x_lag = x[:-lag]
                y_lag = y[lag:]
            else:
                # y leads x by |lag| periods
                x_lag = x[-lag:]
                y_lag = y[:lag]
            
            if len(x_lag) >= 5:  # Minimum data points
                correlation, p_value = stats.pearsonr(x_lag, y_lag)
                
                if abs(correlation) > 0.2:  # Threshold for reporting
                    results.append(CorrelationResult(
                        series1_id=series1,
                        series2_id=series2,
                        correlation_type="cross_correlation",
                        correlation_coefficient=correlation,
                        statistical_significance=p_value,
                        lag=lag,
                        confidence_interval=(-1, 1),
                        description=f"Lag correlation at {lag}: {correlation:.3f}",
                        context={
                            "method": "manual_lag_correlation",
                            "n_observations": len(x_lag)
                        }
                    ))
        
        return results
    
    def _granger_causality_analysis(self, aligned_data: pd.DataFrame, series1: str, series2: str) -> List[CorrelationResult]:
        """Perform Granger causality analysis."""
        if not STATSMODELS_AVAILABLE or len(aligned_data) < 20:
            return []
        
        results = []
        x = aligned_data['value_1'].values
        y = aligned_data['value_2'].values
        
        # Remove any NaN values
        mask = ~(np.isnan(x) | np.isnan(y))
        x, y = x[mask], y[mask]
        
        if len(x) < 20:
            return []
        
        try:
            # Prepare data for Granger causality test
            data = np.column_stack([y, x])  # [dependent, independent]
            
            # Test if x Granger-causes y
            max_lag = min(5, len(x) // 8)  # Conservative lag selection
            
            # Perform Granger causality test
            gc_result = grangercausalitytests(data, maxlag=max_lag, verbose=False)
            
            # Extract results for each lag
            for lag in range(1, max_lag + 1):
                if lag in gc_result:
                    test_stats = gc_result[lag][0]
                    
                    # Use F-test result
                    f_stat = test_stats['ssr_ftest'][0]
                    p_value = test_stats['ssr_ftest'][1]
                    
                    if p_value < 0.1:  # More lenient threshold for Granger causality
                        # Convert F-statistic to a pseudo-correlation measure
                        # Higher F-stat indicates stronger causality
                        causality_strength = min(1.0, f_stat / 10)  # Normalize to [0,1]
                        
                        results.append(CorrelationResult(
                            series1_id=series1,
                            series2_id=series2,
                            correlation_type="granger",
                            correlation_coefficient=causality_strength,
                            statistical_significance=p_value,
                            lag=lag,
                            confidence_interval=(0, 1),
                            description=f"Granger causality: {series1} → {series2} at lag {lag}",
                            context={
                                "method": "granger_causality",
                                "f_statistic": f_stat,
                                "test_type": "ssr_ftest",
                                "interpretation": "causal_relationship"
                            }
                        ))
        
        except Exception as e:
            # Granger causality test failed
            pass
        
        return results
    
    def _generate_economic_interpretation(self, leading_series: str, lagging_series: str, 
                                        lag: int, correlation: float) -> str:
        """Generate economic interpretation of lead-lag relationships."""
        
        strength = "strong" if abs(correlation) > 0.7 else "moderate" if abs(correlation) > 0.4 else "weak"
        direction = "positive" if correlation > 0 else "negative"
        
        if lag == 0:
            return f"{strength.title()} {direction} contemporaneous relationship between {leading_series} and {lagging_series}"
        
        lag_description = f"{lag} period{'s' if lag != 1 else ''}"
        
        # Try to provide domain-specific interpretations
        interpretations = {
            "fred": "economic indicator",
            "commodities": "commodity price",
            "crypto": "cryptocurrency",
            "economic": "economic metric"
        }
        
        leading_type = interpretations.get(leading_series.split('_')[0], leading_series)
        lagging_type = interpretations.get(lagging_series.split('_')[0], lagging_series)
        
        return (f"{strength.title()} {direction} relationship: {leading_type} leads "
                f"{lagging_type} by {lag_description} (correlation: {correlation:.3f})")
    
    def get_correlation_summary(self, correlations: List[CorrelationResult]) -> Dict[str, Any]:
        """Generate summary statistics for correlation analysis."""
        if not correlations:
            return {
                "total_correlations": 0,
                "by_type": {},
                "strongest_correlation": None,
                "significant_correlations": 0
            }
        
        # Count by type
        by_type = {}
        for corr in correlations:
            by_type[corr.correlation_type] = by_type.get(corr.correlation_type, 0) + 1
        
        # Find strongest correlation
        strongest = max(correlations, key=lambda x: abs(x.correlation_coefficient))
        
        # Count significant correlations
        significant = sum(1 for c in correlations if c.statistical_significance < 0.05)
        
        return {
            "total_correlations": len(correlations),
            "by_type": by_type,
            "strongest_correlation": {
                "series1": strongest.series1_id,
                "series2": strongest.series2_id,
                "type": strongest.correlation_type,
                "coefficient": strongest.correlation_coefficient,
                "description": strongest.description
            },
            "significant_correlations": significant,
            "significance_rate": significant / len(correlations) if correlations else 0,
            "average_correlation": sum(abs(c.correlation_coefficient) for c in correlations) / len(correlations)
        }
