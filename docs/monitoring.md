# WeQuo Monitoring & Alerting Guide

This guide covers the comprehensive monitoring and alerting system implemented in WeQuo Phase 3.

## Table of Contents

- [Overview](#overview)
- [Monitoring Components](#monitoring-components)
- [Health Checks](#health-checks)
- [Alerting System](#alerting-system)
- [Performance Monitoring](#performance-monitoring)
- [Error Handling](#error-handling)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

## Overview

The WeQuo monitoring system provides:

- **Real-time Health Monitoring**: Track pipeline uptime, data freshness, and connector status
- **Performance Analytics**: Monitor processing times, throughput, and resource usage
- **Anomaly Detection**: Automatic detection of unusual patterns in data and system behavior
- **Comprehensive Alerting**: Multi-channel notifications (Slack, email, webhooks)
- **Error Tracking**: Structured error logging with recovery strategies
- **Circuit Breakers**: Automatic failure protection for external services

## Monitoring Components

### 1. Core Monitoring (`WeQuoMonitor`)

Tracks overall system health and data freshness.

```python
from wequo.monitoring import WeQuoMonitor

monitor = WeQuoMonitor()
metrics = monitor.collect_metrics()
```

**Key Metrics:**
- **Uptime Status**: `healthy`, `degraded`, or `down`
- **Data Freshness**: Hours since last successful data ingestion
- **Anomaly Rate**: Percentage of data points flagged as anomalies
- **Total Data Points**: Count of processed data points
- **Connector Status**: Health status of each data connector
- **Error/Warning Counts**: Tracked from recent runs

### 2. Health Checker (`HealthChecker`)

Performs connectivity and availability tests for all connectors.

```python
from wequo.monitoring import HealthChecker

health_checker = HealthChecker()
results = health_checker.run_health_checks()
```

**Health Check Types:**
- **API Connectivity**: Test external API endpoints
- **Data Freshness**: Verify recent data availability
- **Response Times**: Monitor API response performance
- **Error Rates**: Track failure patterns

### 3. Metrics Collector (`MetricsCollector`)

Analyzes performance trends and detects anomalies in system metrics.

```python
from wequo.monitoring import MetricsCollector

metrics_collector = MetricsCollector()
report = metrics_collector.generate_metrics_report()
```

**Analysis Features:**
- **Performance Trends**: Track processing time changes
- **Anomaly Detection**: Statistical analysis of metric patterns
- **Historical Analysis**: Compare current vs. historical performance
- **Efficiency Metrics**: Parallel processing effectiveness

## Health Checks

### Connector Health Status

Each connector reports one of these statuses:

- **`healthy`**: Normal operation, recent data available
- **`degraded`**: Some issues but still functional
- **`unhealthy`**: Major problems, not functioning
- **`disabled`**: Connector is turned off in configuration
- **`no_data`**: No recent data available
- **`stale_data`**: Data is older than expected
- **`error`**: Technical error occurred

### Health Check Configuration

```yaml
monitoring:
  health_checks:
    enabled: true
    timeout_seconds: 10
    retry_attempts: 3
    retry_delay_seconds: 5
```

### Running Health Checks

```bash
# Run comprehensive health checks
python scripts/monitor_pipeline.py --health-only

# Check specific components
python scripts/monitor_pipeline.py --metrics-only
```

## Alerting System

### Alert Rules

The system includes pre-configured alert rules:

1. **Pipeline Down** (`pipeline_down`)
   - **Condition**: `uptime_down`
   - **Severity**: `critical`
   - **Cooldown**: 30 minutes

2. **Data Stale** (`data_stale`)
   - **Condition**: Data older than 24 hours
   - **Severity**: `high`
   - **Cooldown**: 2 hours

3. **High Anomaly Rate** (`high_anomaly_rate`)
   - **Condition**: Anomaly rate > 10%
   - **Severity**: `medium`
   - **Cooldown**: 1 hour

4. **Connector Down** (`connector_down`)
   - **Condition**: One or more connectors unhealthy
   - **Severity**: `medium`
   - **Cooldown**: 1 hour

### Alert Channels

#### Slack Integration

```yaml
monitoring:
  alerts:
    slack:
      enabled: true
      webhook_url: "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

Environment variable:
```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

#### Email Alerts

```yaml
monitoring:
  alerts:
    email:
      enabled: true
      smtp_server: "smtp.gmail.com"
      smtp_port: 587
      username: "your_email@gmail.com"
      password: "your_app_password"
      from_address: "your_email@gmail.com"
      to_addresses: ["admin@company.com", "alerts@company.com"]
```

Environment variables:
```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
EMAIL_FROM=your_email@gmail.com
EMAIL_TO=admin@company.com,alerts@company.com
```

#### Webhook Integration

```yaml
monitoring:
  alerts:
    webhook:
      enabled: true
      url: "https://your-webhook-endpoint.com/alerts"
      headers:
        Authorization: "Bearer your_token_here"
```

Environment variables:
```bash
WEBHOOK_URL=https://your-webhook-endpoint.com/alerts
WEBHOOK_HEADERS={"Authorization": "Bearer your_token_here"}
```

### Custom Alert Rules

You can add custom alert rules by modifying the `AlertManager` configuration:

```python
from wequo.monitoring.alerts import AlertRule, AlertManager

# Create custom alert rule
custom_rule = AlertRule(
    name="custom_metric_high",
    condition="custom_metric_high",
    threshold=100.0,
    severity="medium",
    cooldown_minutes=30
)

# Add to alert manager
alert_manager = AlertManager()
alert_manager.alert_rules.append(custom_rule)
```

## Performance Monitoring

### Analytics Performance

The optimized analytics engine provides detailed performance metrics:

```python
from wequo.analytics.optimized import OptimizedAnalyticsEngine

engine = OptimizedAnalyticsEngine()
result = engine.analyze(data_frames)
metrics = result.get('performance_metrics', {})
```

**Performance Metrics:**
- **Total Time**: Complete analytics processing time
- **Data Combination**: Time to combine data from all sources
- **Delta Calculation**: Time to calculate value changes
- **Anomaly Detection**: Time to detect statistical anomalies
- **Trend Analysis**: Time to analyze data trends
- **Percentile Calculation**: Time to calculate statistical percentiles
- **Parallel Processing Overhead**: Time spent on parallel coordination

### Performance Reports

Performance reports are automatically generated in the output directory:

- `performance_report.md`: Human-readable performance summary
- `analytics_summary.json`: Detailed metrics in JSON format

### Optimization Settings

```yaml
optimization:
  enabled: true
  max_workers: null  # Auto-detect (min(cpu_count, 8))
  chunk_size: 10000  # For large dataset processing
  memory_efficient: true
  parallel_connectors: false  # Experimental
```

## Error Handling

### Structured Error Logging

All errors are logged with structured information:

```python
from wequo.utils.error_handling import error_handler, ErrorSeverity

try:
    # Some operation
    pass
except Exception as e:
    error_info = error_handler.handle_error(
        e, 
        component="connector", 
        operation="fetch_data",
        severity=ErrorSeverity.HIGH
    )
```

### Error Categories

- **Connection**: Network and connectivity issues
- **Authentication**: API key and permission problems
- **Data Validation**: Invalid or malformed data
- **Processing**: Data processing errors
- **Storage**: File and database issues
- **Configuration**: Setup and configuration problems

### Recovery Strategies

Automatic recovery strategies are implemented for common error types:

- **Retry with Backoff**: Exponential backoff for transient failures
- **Circuit Breaker**: Automatic failure protection
- **Data Validation**: Input sanitization and validation
- **Fallback Mechanisms**: Alternative data sources or processing methods

### Error Monitoring

```python
# Get error summary for last 24 hours
summary = error_handler.get_error_summary(hours=24)
print(f"Total errors: {summary['total_errors']}")
print(f"By severity: {summary['by_severity']}")
print(f"By category: {summary['by_category']}")
```

## Configuration

### Complete Monitoring Configuration

```yaml
monitoring:
  enabled: true
  check_interval_minutes: 15
  metrics_retention_days: 30
  alert_cooldown_minutes: 60
  
  alerts:
    slack:
      enabled: false
      webhook_url: ""
    email:
      enabled: false
      smtp_server: "smtp.gmail.com"
      smtp_port: 587
      username: ""
      password: ""
      from_address: ""
      to_addresses: []
    webhook:
      enabled: false
      url: ""
      headers: {}
  
  health_checks:
    enabled: true
    timeout_seconds: 10
    retry_attempts: 3
    retry_delay_seconds: 5

optimization:
  enabled: true
  max_workers: null
  chunk_size: 10000
  memory_efficient: true
  parallel_connectors: false
```

### Environment Variables

```bash
# Monitoring & Alerting
SLACK_WEBHOOK_URL=your_slack_webhook_url_here
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password_here
EMAIL_FROM=your_email@gmail.com
EMAIL_TO=admin@yourcompany.com,alerts@yourcompany.com
WEBHOOK_URL=your_webhook_url_here
WEBHOOK_HEADERS={"Authorization": "Bearer your_token_here"}
```

## Troubleshooting

### Common Issues

#### 1. High Anomaly Rate Alerts

**Problem**: Frequent alerts about high anomaly rates
**Solution**: 
- Review anomaly detection threshold in `config.yml`
- Check data quality and source reliability
- Adjust `anomaly_threshold` in analytics configuration

#### 2. Connector Health Issues

**Problem**: Connectors showing as unhealthy
**Solution**:
- Verify API keys and credentials
- Check network connectivity
- Review connector-specific error logs
- Test individual connectors manually

#### 3. Alert Delivery Failures

**Problem**: Alerts not being delivered
**Solution**:
- Verify webhook URLs and credentials
- Check email SMTP settings
- Test alert channels individually
- Review alert cooldown settings

#### 4. Performance Degradation

**Problem**: Slow processing times
**Solution**:
- Monitor system resources (CPU, memory)
- Adjust `max_workers` and `chunk_size` settings
- Review data volume and complexity
- Check for external API rate limits

### Monitoring Commands

```bash
# Run full monitoring cycle
python scripts/monitor_pipeline.py --verbose

# Health checks only
python scripts/monitor_pipeline.py --health-only

# Metrics collection only
python scripts/monitor_pipeline.py --metrics-only

# Disable alerts (for testing)
python scripts/monitor_pipeline.py --no-alerts

# Check monitoring logs
tail -f monitoring.log

# View error log
cat logs/error_log.json | jq .
```

### Log Files

- `monitoring.log`: Main monitoring system logs
- `pipeline_optimized.log`: Optimized pipeline execution logs
- `logs/error_log.json`: Structured error log
- `data/output/*/performance_report.md`: Performance reports

### Monitoring Dashboard

Access the monitoring dashboard at `http://localhost:5000/dashboard` to view:

- Real-time system status
- Data freshness indicators
- Connector health status
- Performance metrics
- Recent alerts and errors

## Best Practices

1. **Regular Monitoring**: Run health checks every 15 minutes
2. **Alert Tuning**: Adjust thresholds based on your data patterns
3. **Log Rotation**: Implement log rotation for long-running systems
4. **Backup Configuration**: Keep monitoring configuration in version control
5. **Test Alerts**: Regularly test alert delivery channels
6. **Performance Baselines**: Establish performance baselines for your environment
7. **Error Analysis**: Regularly review error patterns and trends
8. **Capacity Planning**: Monitor resource usage for scaling decisions

## Integration with CI/CD

The monitoring system can be integrated into CI/CD pipelines:

```yaml
# GitHub Actions example
- name: Run WeQuo Health Checks
  run: |
    python scripts/monitor_pipeline.py --health-only
    if [ $? -ne 0 ]; then
      echo "Health checks failed"
      exit 1
    fi
```

This ensures that any deployment issues are caught early and alerts are sent to the appropriate channels.
