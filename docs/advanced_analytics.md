# WeQuo Advanced Analytics Documentation

This document describes the advanced analytics capabilities implemented in Phase 3 of the WeQuo pipeline.

## Overview

The advanced analytics system provides sophisticated time series analysis capabilities including:

- **Change Point Detection**: Identifies structural breaks and regime changes
- **Cross-Correlation Analysis**: Discovers relationships between series with lag analysis
- **Event Impact Tagging**: Attributes time series changes to known events
- **Explainable Analytics**: Provides human-readable insights and explanations

## Architecture

### Core Components

```
wequo.analytics.advanced/
├── changepoint.py      # Change point detection algorithms
├── correlation.py      # Cross-correlation and lead-lag analysis
├── events.py          # Event impact attribution
└── explainable.py     # Human-readable explanations
```

### Integration

The advanced analytics are integrated into the main `AnalyticsEngine` and can be enabled/disabled via configuration:

```python
from wequo.analytics.core import AnalyticsEngine

engine = AnalyticsEngine(
    enable_advanced_analytics=True  # Enable Phase 3 features
)

results = engine.analyze(data_frames)
# Access via results.changepoints, results.correlations, etc.
```

## Change Point Detection

### Overview

Detects structural breaks in time series data using multiple algorithms:

1. **Mean Change Detection**: Identifies level shifts using statistical tests
2. **Variance Change Detection**: Finds volatility regime changes via F-tests
3. **Trend Change Detection**: Detects slope changes using linear regression
4. **Regime Change Detection**: Identifies broader structural changes

### Usage

```python
from wequo.analytics.advanced.changepoint import ChangePointDetector

detector = ChangePointDetector(
    min_size=10,              # Minimum segment size
    max_changepoints=15,      # Maximum change points to detect
    confidence_threshold=0.8  # Minimum confidence threshold
)

changepoints = detector.detect_changepoints(df)

for cp in changepoints:
    print(f"Series: {cp.series_id}")
    print(f"Date: {cp.timestamp}")
    print(f"Type: {cp.change_type}")
    print(f"Confidence: {cp.confidence}")
    print(f"Description: {cp.description}")
```

### Algorithms

#### 1. Ruptures-based Detection (Optional)

If the `ruptures` library is available, uses the PELT (Pruned Exact Linear Time) algorithm for optimal change point detection.

#### 2. Basic Statistical Tests (Fallback)

- **T-test**: For mean changes between segments
- **F-test**: For variance changes between segments
- **Linear Regression**: For trend changes

### Output Format

Each change point includes:

```python
@dataclass
class ChangePoint:
    series_id: str                    # Time series identifier
    timestamp: datetime               # When the change occurred
    index: int                        # Position in the series
    change_type: str                  # mean, variance, trend, regime
    confidence: float                 # 0.0 to 1.0
    magnitude: float                  # Size of the change
    description: str                  # Human-readable description
    statistical_significance: float   # P-value
    context: Dict[str, Any]          # Additional metadata
```

## Cross-Correlation Analysis

### Overview

Analyzes relationships between time series including:

1. **Pearson Correlation**: Linear relationships
2. **Spearman Correlation**: Rank-based relationships
3. **Cross-Correlation with Lags**: Time-delayed relationships
4. **Granger Causality**: Predictive relationships (if statsmodels available)

### Usage

```python
from wequo.analytics.advanced.correlation import CrossCorrelationAnalyzer

analyzer = CrossCorrelationAnalyzer(
    max_lags=10,                    # Maximum lag periods to test
    significance_level=0.05,        # Statistical significance threshold
    min_overlap_periods=20          # Minimum overlapping data points
)

correlations = analyzer.analyze_all_correlations(df)
relationships = analyzer.find_lead_lag_relationships(df)

for corr in correlations:
    print(f"{corr.series1_id} ↔ {corr.series2_id}")
    print(f"Coefficient: {corr.correlation_coefficient:.3f}")
    print(f"Lag: {corr.lag} periods")
```

### Lead-Lag Analysis

The system automatically identifies leading and lagging indicators:

```python
for rel in relationships:
    print(f"Leading: {rel.leading_series}")
    print(f"Lagging: {rel.lagging_series}")
    print(f"Optimal lag: {rel.optimal_lag} periods")
    print(f"Interpretation: {rel.economic_interpretation}")
```

### Output Format

```python
@dataclass
class CorrelationResult:
    series1_id: str
    series2_id: str
    correlation_type: str              # pearson, spearman, cross_correlation, granger
    correlation_coefficient: float     # -1.0 to 1.0
    statistical_significance: float    # P-value
    lag: int                          # Time lag (0 for contemporaneous)
    confidence_interval: Tuple[float, float]
    description: str
    context: Dict[str, Any]
```

## Event Impact Analysis

### Overview

Attributes time series changes to known events by:

1. **Event Catalog Management**: Maintains a catalog of significant events
2. **Impact Detection**: Identifies statistical changes around event dates
3. **Attribution**: Links changes to specific events with confidence scores
4. **Timeline Creation**: Builds event impact timelines

### Usage

```python
from wequo.analytics.advanced.events import EventImpactTagger, Event

tagger = EventImpactTagger(
    impact_window_days=7,      # Days after event to look for impacts
    baseline_window_days=14,   # Days before event for baseline
    significance_threshold=0.05
)

# Add custom events
custom_event = Event(
    event_id="fed_rate_hike_2023",
    timestamp=datetime(2023, 3, 22),
    event_type="monetary_policy",
    description="Federal Reserve raises rates by 0.25%",
    severity="high",
    affected_domains=["financial", "crypto"],
    metadata={"rate_change": 0.25}
)

impacts = tagger.detect_event_impacts(df, custom_events=[custom_event])
```

### Built-in Event Catalog

The system includes a catalog of major events:

- COVID-19 pandemic declaration (2020-03-11)
- Russia-Ukraine conflict (2022-02-24)
- Federal Reserve rate changes
- Banking crises (Silicon Valley Bank)
- OPEC production changes

### Impact Types

- **spike**: Sudden increase in values
- **drop**: Sudden decrease in values
- **volatility_increase**: Increased variance
- **extreme_spike/drop**: Extreme outliers

### Output Format

```python
@dataclass
class EventImpact:
    event_id: str
    series_id: str
    impact_type: str
    impact_magnitude: float
    impact_duration_days: int
    confidence: float
    pre_event_baseline: float
    post_event_value: float
    statistical_significance: float
    description: str
    context: Dict[str, Any]
```

## Explainable Analytics

### Overview

Provides human-readable explanations for all analytics results by:

1. **Contextual Analysis**: Considers relationships between findings
2. **Causal Attribution**: Links effects to potential causes
3. **Recommendation Generation**: Suggests follow-up actions
4. **Evidence Compilation**: Provides supporting statistical evidence

### Usage

```python
from wequo.analytics.advanced.explainable import ExplainableAnalytics

explainer = ExplainableAnalytics()

# Explain specific findings
anomaly_explanation = explainer.explain_anomaly(anomaly_data, df)
trend_explanation = explainer.explain_trend(trend_data, df)
correlation_explanation = explainer.explain_correlation(correlation_result, df)

# Generate comprehensive explanations
explanations = explainer.generate_comprehensive_explanation(analytics_results, df)

for explanation in explanations:
    print(f"Analysis: {explanation.analysis_type}")
    print(f"Primary: {explanation.primary_explanation}")
    print(f"Factors: {explanation.contributing_factors}")
    print(f"Recommendations: {explanation.recommendations}")
```

### Explanation Types

1. **Anomaly Explanations**: Why unusual values occurred
2. **Trend Explanations**: What drives directional changes
3. **Correlation Explanations**: Why series move together
4. **Change Point Explanations**: What caused structural breaks
5. **Event Impact Explanations**: How events affected series

### Output Format

```python
@dataclass
class AnalyticsExplanation:
    analysis_type: str                # anomaly, trend, correlation, etc.
    series_id: str
    timestamp: datetime
    confidence: float
    primary_explanation: str          # Main insight
    contributing_factors: List[str]   # What influenced the result
    evidence: Dict[str, Any]         # Supporting statistical evidence
    recommendations: List[str]        # Suggested actions
    related_findings: List[str]       # Connected insights
```

## Configuration

### Analytics Engine Configuration

```python
# Enable/disable advanced analytics
analytics_engine = AnalyticsEngine(
    enable_advanced_analytics=True,
    anomaly_threshold=2.0,
    min_data_points=5
)
```

### Module-specific Configuration

```python
# Change point detection
cp_detector = ChangePointDetector(
    min_size=10,                    # Minimum segment size
    max_changepoints=15,            # Maximum change points
    confidence_threshold=0.8        # Minimum confidence
)

# Correlation analysis
corr_analyzer = CrossCorrelationAnalyzer(
    max_lags=10,                    # Maximum lag periods
    significance_level=0.05,        # P-value threshold
    min_overlap_periods=20          # Minimum data overlap
)

# Event impact analysis
event_tagger = EventImpactTagger(
    impact_window_days=7,           # Post-event window
    baseline_window_days=14,        # Pre-event baseline
    significance_threshold=0.05     # Statistical significance
)
```

## Dependencies

### Required

- `pandas>=1.5.0`: Data manipulation
- `numpy>=1.21.0`: Numerical computing
- `scipy>=1.9.0`: Statistical functions

### Optional (Enhanced Features)

- `ruptures>=1.1.0`: Advanced change point detection
- `statsmodels>=0.13.0`: Granger causality testing

### Installation

```bash
# Basic installation
pip install -r requirements.txt

# With optional dependencies for enhanced features
pip install ruptures>=1.1.0 statsmodels>=0.13.0
```

## Performance Considerations

### Computational Complexity

- **Change Point Detection**: O(n log n) with ruptures, O(n²) with basic methods
- **Cross-Correlation**: O(n × m × L) where L is max_lags
- **Event Impact Analysis**: O(E × S) where E is events, S is series
- **Explainable Analytics**: O(R) where R is number of results to explain

### Memory Usage

- **Large Time Series**: Consider chunking data for very long series (>10,000 points)
- **Many Series**: Correlation analysis scales quadratically with number of series
- **Event Catalog**: Grows linearly with number of tracked events

### Optimization Tips

1. **Reduce max_lags**: For correlation analysis with many series
2. **Increase min_size**: For change point detection to reduce false positives
3. **Filter by confidence**: Only process high-confidence results
4. **Batch processing**: Process series in groups for large datasets

## Examples

### Basic Usage

```python
# Load data
df = pd.read_csv('time_series_data.csv')

# Run full advanced analytics
engine = AnalyticsEngine(enable_advanced_analytics=True)
data_frames = {'source1': df}  # Group by source
results = engine.analyze(data_frames)

# Access results
print(f"Change points: {len(results.changepoints)}")
print(f"Correlations: {len(results.correlations)}")
print(f"Event impacts: {len(results.event_impacts)}")
print(f"Explanations: {len(results.explanations)}")
```

### Custom Event Analysis

```python
# Define custom events
events = [
    Event(
        event_id="company_earnings",
        timestamp=datetime(2023, 4, 15),
        event_type="earnings",
        description="Major tech company reports earnings",
        severity="medium",
        affected_domains=["financial", "tech"],
        metadata={"sector": "technology"}
    )
]

# Analyze impacts
tagger = EventImpactTagger()
impacts = tagger.detect_event_impacts(df, custom_events=events)
```

### Focused Analysis

```python
# Analyze specific series pair
analyzer = CrossCorrelationAnalyzer()
pair_data = df[df['series_id'].isin(['series_a', 'series_b'])]
correlations = analyzer.analyze_all_correlations(pair_data)

# Explain the strongest correlation
if correlations:
    strongest = max(correlations, key=lambda x: abs(x.correlation_coefficient))
    explanation = explainer.explain_correlation(strongest, df)
    print(explanation.primary_explanation)
```

## Troubleshooting

### Common Issues

1. **No change points detected**: Increase confidence threshold or reduce min_size
2. **Low correlation significance**: Increase min_overlap_periods or check data quality
3. **No event impacts found**: Verify event dates align with data range
4. **ImportError for optional dependencies**: Install ruptures/statsmodels for enhanced features

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check intermediate results
cp_detector = ChangePointDetector()
changepoints = cp_detector.detect_changepoints(df)
summary = cp_detector.get_changepoint_summary(changepoints)
print(f"Detection summary: {summary}")
```

### Performance Monitoring

```python
import time

start_time = time.time()
results = analytics_engine.analyze(data_frames)
duration = time.time() - start_time

print(f"Analytics completed in {duration:.2f} seconds")
print(f"Results: {len(results.changepoints)} CPs, {len(results.correlations)} correlations")
```

## API Reference

For detailed API documentation, see the docstrings in each module:

- `wequo.analytics.advanced.changepoint`
- `wequo.analytics.advanced.correlation`
- `wequo.analytics.advanced.events`
- `wequo.analytics.advanced.explainable`

## Contributing

When adding new advanced analytics features:

1. Follow the existing pattern of detector classes with `analyze()` methods
2. Include comprehensive unit tests in `tests/test_advanced_analytics.py`
3. Add notebook examples demonstrating new capabilities
4. Update this documentation with usage examples
5. Consider performance implications for large datasets
