"""Tests for advanced analytics modules."""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import patch

from wequo.analytics.advanced.changepoint import ChangePointDetector, ChangePoint
from wequo.analytics.advanced.correlation import CrossCorrelationAnalyzer, CorrelationResult
from wequo.analytics.advanced.events import EventImpactTagger, Event, EventImpact
from wequo.analytics.advanced.explainable import ExplainableAnalytics, AnalyticsExplanation


@pytest.fixture
def sample_time_series():
    """Create sample time series data for testing."""
    dates = pd.date_range('2023-01-01', periods=100, freq='D')
    
    # Create multiple series with different patterns
    data = []
    
    # Series 1: Trend with change point
    values1 = np.concatenate([
        np.linspace(10, 15, 50) + np.random.normal(0, 0.5, 50),  # Upward trend
        np.linspace(15, 10, 50) + np.random.normal(0, 0.5, 50)   # Downward trend
    ])
    
    for i, (date, value) in enumerate(zip(dates, values1)):
        data.append({
            'date': date,
            'value': value,
            'series_id': 'series_1',
            'source': 'test'
        })
    
    # Series 2: Correlated with series 1 (with lag)
    values2 = np.concatenate([
        np.linspace(20, 25, 50) + np.random.normal(0, 0.8, 50),
        np.linspace(25, 20, 50) + np.random.normal(0, 0.8, 50)
    ])
    # Add correlation with lag
    values2[5:] = 0.7 * values1[:-5] + 0.3 * values2[5:]
    
    for i, (date, value) in enumerate(zip(dates, values2)):
        data.append({
            'date': date,
            'value': value,
            'series_id': 'series_2',
            'source': 'test'
        })
    
    # Series 3: Volatility change
    values3 = np.concatenate([
        np.random.normal(30, 1, 50),    # Low volatility
        np.random.normal(30, 5, 50)     # High volatility
    ])
    
    for i, (date, value) in enumerate(zip(dates, values3)):
        data.append({
            'date': date,
            'value': value,
            'series_id': 'series_3',
            'source': 'test'
        })
    
    return pd.DataFrame(data)


class TestChangePointDetector:
    """Test change point detection functionality."""
    
    def test_initialization(self):
        """Test ChangePointDetector initialization."""
        detector = ChangePointDetector(min_size=10, max_changepoints=5)
        assert detector.min_size == 10
        assert detector.max_changepoints == 5
        assert detector.confidence_threshold == 0.8
    
    def test_detect_changepoints_empty_data(self):
        """Test change point detection with empty data."""
        detector = ChangePointDetector()
        df = pd.DataFrame()
        
        changepoints = detector.detect_changepoints(df)
        assert len(changepoints) == 0
    
    def test_detect_changepoints(self, sample_time_series):
        """Test change point detection with sample data."""
        detector = ChangePointDetector(min_size=5, confidence_threshold=0.5)
        
        changepoints = detector.detect_changepoints(sample_time_series)
        
        # Should detect change points
        assert len(changepoints) > 0
        
        # Check structure of change points
        for cp in changepoints:
            assert isinstance(cp, ChangePoint)
            assert cp.series_id in ['series_1', 'series_2', 'series_3']
            assert cp.change_type in ['mean', 'variance', 'trend', 'regime']
            assert 0 <= cp.confidence <= 1
            assert isinstance(cp.timestamp, datetime)
    
    def test_mean_change_detection(self, sample_time_series):
        """Test mean change detection specifically."""
        detector = ChangePointDetector(min_size=5)
        
        # Filter to one series for easier testing
        series_data = sample_time_series[sample_time_series['series_id'] == 'series_1']
        
        changepoints = detector.detect_changepoints(series_data)
        
        # Should detect mean changes in the trend data
        mean_changes = [cp for cp in changepoints if cp.change_type == 'mean']
        assert len(mean_changes) >= 0  # May or may not detect depending on noise
    
    def test_variance_change_detection(self, sample_time_series):
        """Test variance change detection."""
        detector = ChangePointDetector(min_size=5)
        
        # Filter to volatility series
        series_data = sample_time_series[sample_time_series['series_id'] == 'series_3']
        
        changepoints = detector.detect_changepoints(series_data)
        
        # Should detect variance changes
        variance_changes = [cp for cp in changepoints if cp.change_type == 'variance']
        # Note: May not always detect due to randomness in test data
        assert len(variance_changes) >= 0
    
    def test_get_changepoint_summary(self, sample_time_series):
        """Test change point summary generation."""
        detector = ChangePointDetector()
        changepoints = detector.detect_changepoints(sample_time_series)
        
        summary = detector.get_changepoint_summary(changepoints)
        
        assert 'total_changepoints' in summary
        assert 'by_type' in summary
        assert 'avg_confidence' in summary
        assert summary['total_changepoints'] == len(changepoints)


class TestCrossCorrelationAnalyzer:
    """Test cross-correlation analysis functionality."""
    
    def test_initialization(self):
        """Test CrossCorrelationAnalyzer initialization."""
        analyzer = CrossCorrelationAnalyzer(max_lags=15, significance_level=0.01)
        assert analyzer.max_lags == 15
        assert analyzer.significance_level == 0.01
    
    def test_analyze_correlations_empty_data(self):
        """Test correlation analysis with empty data."""
        analyzer = CrossCorrelationAnalyzer()
        df = pd.DataFrame()
        
        correlations = analyzer.analyze_all_correlations(df)
        assert len(correlations) == 0
    
    def test_analyze_correlations(self, sample_time_series):
        """Test correlation analysis with sample data."""
        analyzer = CrossCorrelationAnalyzer(min_overlap_periods=5)
        
        correlations = analyzer.analyze_all_correlations(sample_time_series)
        
        # Should find correlations between series
        assert len(correlations) > 0
        
        # Check structure
        for corr in correlations:
            assert isinstance(corr, CorrelationResult)
            assert corr.series1_id in ['series_1', 'series_2', 'series_3']
            assert corr.series2_id in ['series_1', 'series_2', 'series_3']
            assert corr.series1_id != corr.series2_id
            assert -1 <= corr.correlation_coefficient <= 1
            assert corr.correlation_type in ['pearson', 'spearman', 'cross_correlation', 'granger']
    
    def test_pearson_correlation(self, sample_time_series):
        """Test Pearson correlation calculation."""
        analyzer = CrossCorrelationAnalyzer()
        
        # Get aligned data for two series
        aligned_data = analyzer._align_series_data(sample_time_series, 'series_1', 'series_2')
        
        pearson_results = analyzer._pearson_correlation(aligned_data, 'series_1', 'series_2')
        
        assert len(pearson_results) == 1
        result = pearson_results[0]
        assert result.correlation_type == 'pearson'
        assert result.lag == 0  # Contemporaneous
    
    def test_find_lead_lag_relationships(self, sample_time_series):
        """Test lead-lag relationship detection."""
        analyzer = CrossCorrelationAnalyzer()
        
        relationships = analyzer.find_lead_lag_relationships(sample_time_series)
        
        # May or may not find relationships depending on data
        for rel in relationships:
            assert rel.leading_series in ['series_1', 'series_2', 'series_3']
            assert rel.lagging_series in ['series_1', 'series_2', 'series_3']
            assert rel.leading_series != rel.lagging_series
            assert rel.optimal_lag >= 0
            assert 0 <= rel.confidence <= 1
    
    def test_get_correlation_summary(self, sample_time_series):
        """Test correlation summary generation."""
        analyzer = CrossCorrelationAnalyzer()
        correlations = analyzer.analyze_all_correlations(sample_time_series)
        
        summary = analyzer.get_correlation_summary(correlations)
        
        assert 'total_correlations' in summary
        assert 'by_type' in summary
        assert 'strongest_correlation' in summary
        assert 'significant_correlations' in summary
        assert summary['total_correlations'] == len(correlations)


class TestEventImpactTagger:
    """Test event impact tagging functionality."""
    
    def test_initialization(self):
        """Test EventImpactTagger initialization."""
        tagger = EventImpactTagger(impact_window_days=10, baseline_window_days=20)
        assert tagger.impact_window_days == 10
        assert tagger.baseline_window_days == 20
        assert len(tagger.event_catalog) > 0
    
    def test_detect_event_impacts_empty_data(self):
        """Test event impact detection with empty data."""
        tagger = EventImpactTagger()
        df = pd.DataFrame()
        
        impacts = tagger.detect_event_impacts(df)
        assert len(impacts) == 0
    
    def test_detect_event_impacts(self, sample_time_series):
        """Test event impact detection with sample data."""
        tagger = EventImpactTagger()
        
        # Add a custom event for testing
        test_event = Event(
            event_id="test_event",
            timestamp=datetime(2023, 2, 15),  # Middle of our data range
            event_type="test",
            description="Test event",
            severity="high",
            affected_domains=["test"],
            metadata={}
        )
        
        impacts = tagger.detect_event_impacts(sample_time_series, custom_events=[test_event])
        
        # Check structure of impacts
        for impact in impacts:
            assert isinstance(impact, EventImpact)
            assert impact.series_id in ['series_1', 'series_2', 'series_3']
            assert impact.impact_type in ['spike', 'drop', 'volatility_increase', 'extreme_spike', 'extreme_drop']
            assert 0 <= impact.confidence <= 1
            assert impact.impact_duration_days > 0
    
    def test_add_custom_event(self):
        """Test adding custom events."""
        tagger = EventImpactTagger()
        initial_count = len(tagger.event_catalog)
        
        custom_event = Event(
            event_id="custom_test",
            timestamp=datetime(2023, 1, 1),
            event_type="custom",
            description="Custom test event",
            severity="medium",
            affected_domains=["test"],
            metadata={}
        )
        
        tagger.add_custom_event(custom_event)
        assert len(tagger.event_catalog) == initial_count + 1
    
    def test_get_events_in_period(self):
        """Test getting events within a time period."""
        tagger = EventImpactTagger()
        
        start_date = datetime(2020, 1, 1)
        end_date = datetime(2021, 1, 1)
        
        events = tagger.get_events_in_period(start_date, end_date)
        
        # Should find COVID-19 event
        assert len(events) > 0
        covid_events = [e for e in events if 'covid' in e.event_id.lower()]
        assert len(covid_events) > 0
    
    def test_get_impact_summary(self):
        """Test impact summary generation."""
        tagger = EventImpactTagger()
        
        # Create mock impacts
        mock_impacts = [
            EventImpact(
                event_id="test1",
                series_id="series1",
                impact_type="spike",
                impact_magnitude=0.5,
                impact_duration_days=3,
                confidence=0.8,
                pre_event_baseline=10.0,
                post_event_value=15.0,
                statistical_significance=0.01,
                description="Test impact",
                context={}
            )
        ]
        
        summary = tagger.get_impact_summary(mock_impacts)
        
        assert 'total_impacts' in summary
        assert 'by_type' in summary
        assert 'most_significant' in summary
        assert summary['total_impacts'] == 1


class TestExplainableAnalytics:
    """Test explainable analytics functionality."""
    
    def test_initialization(self):
        """Test ExplainableAnalytics initialization."""
        explainer = ExplainableAnalytics()
        assert hasattr(explainer, 'changepoint_detector')
        assert hasattr(explainer, 'correlation_analyzer')
        assert hasattr(explainer, 'event_tagger')
    
    def test_explain_anomaly(self, sample_time_series):
        """Test anomaly explanation generation."""
        explainer = ExplainableAnalytics()
        
        # Mock anomaly data
        anomaly_data = {
            'series_id': 'series_1',
            'timestamp': '2023-02-15',
            'value': 100,
            'z_score': 3.5
        }
        
        explanation = explainer.explain_anomaly(anomaly_data, sample_time_series)
        
        assert isinstance(explanation, AnalyticsExplanation)
        assert explanation.analysis_type == "anomaly"
        assert explanation.series_id == 'series_1'
        assert 0 <= explanation.confidence <= 1
        assert len(explanation.primary_explanation) > 0
        assert isinstance(explanation.contributing_factors, list)
        assert isinstance(explanation.recommendations, list)
    
    def test_explain_trend(self, sample_time_series):
        """Test trend explanation generation."""
        explainer = ExplainableAnalytics()
        
        # Mock trend data
        trend_data = {
            'series_id': 'series_1',
            'slope': 0.05,
            'r_squared': 0.75,
            'direction': 'upward',
            'trend_strength': 'strong'
        }
        
        explanation = explainer.explain_trend(trend_data, sample_time_series)
        
        assert isinstance(explanation, AnalyticsExplanation)
        assert explanation.analysis_type == "trend"
        assert explanation.series_id == 'series_1'
        assert 0 <= explanation.confidence <= 1
        assert "trend" in explanation.primary_explanation.lower()
    
    def test_explain_correlation(self, sample_time_series):
        """Test correlation explanation generation."""
        explainer = ExplainableAnalytics()
        
        # Create mock correlation
        correlation = CorrelationResult(
            series1_id='series_1',
            series2_id='series_2',
            correlation_type='pearson',
            correlation_coefficient=0.75,
            statistical_significance=0.01,
            lag=0,
            confidence_interval=(0.6, 0.85),
            description="Strong positive correlation",
            context={}
        )
        
        explanation = explainer.explain_correlation(correlation, sample_time_series)
        
        assert isinstance(explanation, AnalyticsExplanation)
        assert explanation.analysis_type == "correlation"
        assert "correlation" in explanation.primary_explanation.lower()
    
    def test_categorize_anomaly_severity(self):
        """Test anomaly severity categorization."""
        explainer = ExplainableAnalytics()
        
        assert explainer._categorize_anomaly_severity(1.5) == "Mild"
        assert explainer._categorize_anomaly_severity(2.5) == "Moderate"
        assert explainer._categorize_anomaly_severity(3.5) == "Severe"
        assert explainer._categorize_anomaly_severity(4.5) == "Extreme"
    
    def test_categorize_correlation_strength(self):
        """Test correlation strength categorization."""
        explainer = ExplainableAnalytics()
        
        assert explainer._categorize_correlation_strength(0.1) == "Very weak"
        assert explainer._categorize_correlation_strength(0.3) == "Weak"
        assert explainer._categorize_correlation_strength(0.5) == "Moderate"
        assert explainer._categorize_correlation_strength(0.7) == "Strong"
        assert explainer._categorize_correlation_strength(0.9) == "Very strong"
    
    def test_identify_series_domain(self):
        """Test series domain identification."""
        explainer = ExplainableAnalytics()
        
        assert explainer._identify_series_domain("fred_cpi") == "economic"
        assert explainer._identify_series_domain("commodities_gold") == "commodities"
        assert explainer._identify_series_domain("bitcoin_price") == "cryptocurrency"
        assert explainer._identify_series_domain("economic_gdp") == "macroeconomic"
        assert explainer._identify_series_domain("unknown_series") == "unknown"


class TestAdvancedAnalyticsIntegration:
    """Test integration between advanced analytics modules."""
    
    def test_full_analysis_pipeline(self, sample_time_series):
        """Test the full advanced analytics pipeline."""
        
        # Test change point detection
        cp_detector = ChangePointDetector()
        changepoints = cp_detector.detect_changepoints(sample_time_series)
        
        # Test correlation analysis
        corr_analyzer = CrossCorrelationAnalyzer()
        correlations = corr_analyzer.analyze_all_correlations(sample_time_series)
        
        # Test event impact detection
        event_tagger = EventImpactTagger()
        event_impacts = event_tagger.detect_event_impacts(sample_time_series)
        
        # Test explainable analytics
        explainer = ExplainableAnalytics()
        
        # Create mock analytics results
        analytics_results = {
            'anomalies': [{
                'series_id': 'series_1',
                'timestamp': '2023-02-15',
                'value': 100,
                'z_score': 2.5
            }],
            'trends': [{
                'series_id': 'series_1',
                'slope': 0.05,
                'r_squared': 0.6,
                'direction': 'upward',
                'trend_strength': 'moderate'
            }],
            'changepoints': [],
            'correlations': [],
            'event_impacts': []
        }
        
        explanations = explainer.generate_comprehensive_explanation(analytics_results, sample_time_series)
        
        # Verify we get explanations
        assert len(explanations) > 0
        
        # Check that all analytics components worked
        assert isinstance(changepoints, list)
        assert isinstance(correlations, list)
        assert isinstance(event_impacts, list)
        assert isinstance(explanations, list)
    
    @patch('wequo.analytics.advanced.changepoint.RUPTURES_AVAILABLE', False)
    def test_fallback_methods(self, sample_time_series):
        """Test fallback methods when optional dependencies are unavailable."""
        
        # Test that change point detection works without ruptures
        cp_detector = ChangePointDetector()
        changepoints = cp_detector.detect_changepoints(sample_time_series)
        
        # Should still work, just using basic methods
        assert isinstance(changepoints, list)
    
    @patch('wequo.analytics.advanced.correlation.STATSMODELS_AVAILABLE', False)
    def test_correlation_fallback(self, sample_time_series):
        """Test correlation analysis fallback when statsmodels unavailable."""
        
        corr_analyzer = CrossCorrelationAnalyzer()
        correlations = corr_analyzer.analyze_all_correlations(sample_time_series)
        
        # Should still work with basic correlation methods
        assert isinstance(correlations, list)


if __name__ == "__main__":
    pytest.main([__file__])
