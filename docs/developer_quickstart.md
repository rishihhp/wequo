# WeQuo Developer Quickstart Guide

This guide will help you get up and running with WeQuo development quickly.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Setup](#quick-setup)
- [Development Environment](#development-environment)
- [Running the Pipeline](#running-the-pipeline)
- [Web Dashboard](#web-dashboard)
- [Monitoring & Alerts](#monitoring--alerts)
- [Testing](#testing)
- [Contributing](#contributing)
- [Troubleshooting](#troubleshooting)

## Prerequisites

- Python 3.11+
- Git
- API Keys (see [API Setup](#api-setup))

## Quick Setup

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/your-org/wequo.git
cd wequo

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

```bash
# Copy environment template
cp env.example .env

# Edit .env file with your API keys
# See API Setup section below
```

### 3. API Setup

#### Required APIs

**FRED API (Required)**
1. Go to [FRED API Registration](https://fred.stlouisfed.org/docs/api/api_key.html)
2. Create an account and request an API key
3. Add to `.env`: `FRED_API_KEY=your_fred_api_key_here`

**Alpha Vantage API (Optional)**
1. Go to [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
2. Get a free API key
3. Add to `.env`: `ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here`

**CoinGecko API (Optional)**
1. Go to [CoinGecko API](https://www.coingecko.com/en/api)
2. Get a demo API key
3. Add to `.env`: `COINGECKO_API_KEY=your_coingecko_demo_key_here`

#### Optional APIs for Extended Features

**GitHub API (Optional)**
1. Go to [GitHub Personal Access Tokens](https://github.com/settings/tokens)
2. Generate a token with `public_repo` scope
3. Add to `.env`: `GITHUB_TOKEN=your_github_token_here`

**OpenWeather API (Optional)**
1. Go to [OpenWeather API](https://openweathermap.org/api)
2. Sign up for a free account
3. Add to `.env`: `OPENWEATHER_API_KEY=your_openweather_key_here`

### 4. Test the Setup

```bash
# Run a quick test
python scripts/run_weekly.py

# Check if data was generated
ls data/output/
```

## Development Environment

### Project Structure

```
wequo/
├── src/wequo/                 # Main source code
│   ├── connectors/           # Data source connectors
│   ├── analytics/            # Analytics and processing
│   ├── monitoring/           # Monitoring and alerting
│   ├── tools/               # CLI and web tools
│   └── utils/               # Utilities and helpers
├── scripts/                 # Executable scripts
├── templates/               # Web templates
├── docs/                    # Documentation
├── data/output/             # Generated data
└── tests/                   # Test files
```

### Key Components

- **Connectors**: Fetch data from external APIs (FRED, Alpha Vantage, etc.)
- **Analytics**: Process and analyze data for insights
- **Monitoring**: Track system health and performance
- **Web Dashboard**: Interactive interface for data exploration
- **Export System**: Generate PDF and HTML reports

### Configuration

Main configuration is in `src/wequo/config.yml`:

```yaml
run:
  output_root: "data/output"
  lookback_days: 7

connectors:
  fred:
    enabled: true
    series_ids:
      - CPIAUCSL   # US CPI
      - DFF        # Federal Funds Rate
      - DGS10      # 10-Year Treasury Rate

monitoring:
  enabled: true
  check_interval_minutes: 15

optimization:
  enabled: true
  max_workers: null  # Auto-detect
  chunk_size: 10000
```

## Running the Pipeline

### Basic Pipeline

```bash
# Run the standard pipeline
python scripts/run_weekly.py

# Run with verbose logging
python scripts/run_weekly.py --verbose
```

### Optimized Pipeline

```bash
# Run the optimized pipeline (recommended for production)
python scripts/run_weekly_optimized.py

# Check performance metrics
cat data/output/2025-09-12/performance_report.md
```

### Pipeline Output

After running, you'll find:

```
data/output/2025-09-12/
├── fred.csv                 # FRED economic data
├── commodities.csv          # Commodity prices
├── crypto.csv              # Cryptocurrency data
├── economic.csv            # World Bank economic data
├── package_summary.json    # Summary of all data
├── analytics_summary.json  # Analytics results
├── performance_report.md   # Performance metrics
└── qa_report.md           # Quality assurance report
```

## Web Dashboard

### Start the Dashboard

```bash
# Start the web application
python scripts/run_web_app.py

# Access at http://localhost:5000
```

### Dashboard Features

- **Data Overview**: View all available data packages
- **Search & Filter**: Find specific data series
- **Analytics Visualization**: Interactive charts and graphs
- **Export Reports**: Generate PDF and HTML reports
- **Monitoring Status**: Real-time system health

### API Endpoints

```bash
# Get package summary
curl http://localhost:5000/api/package/2025-09-12/summary

# Search data
curl "http://localhost:5000/api/search?q=bitcoin"

# Export HTML report
curl http://localhost:5000/export/2025-09-12/html

# Export PDF report
curl http://localhost:5000/export/2025-09-12/pdf
```

## Monitoring & Alerts

### Health Monitoring

```bash
# Run comprehensive health checks
python scripts/monitor_pipeline.py

# Health checks only
python scripts/monitor_pipeline.py --health-only

# Metrics collection only
python scripts/monitor_pipeline.py --metrics-only
```

### Alert Configuration

Set up alerts in your `.env` file:

```bash
# Slack alerts
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Email alerts
SMTP_SERVER=smtp.gmail.com
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
EMAIL_FROM=your_email@gmail.com
EMAIL_TO=admin@company.com

# Webhook alerts
WEBHOOK_URL=https://your-webhook-endpoint.com/alerts
```

### Monitoring Dashboard

Access monitoring at `http://localhost:5000/dashboard`:

- System status overview
- Data freshness indicators
- Connector health status
- Performance metrics
- Recent alerts and errors

## Testing

### Run Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test categories
python -m pytest tests/test_connectors.py
python -m pytest tests/test_analytics.py
python -m pytest tests/test_monitoring.py

# Run with coverage
python -m pytest --cov=src/wequo tests/
```

### Test Data

```bash
# Generate test data
python scripts/generate_test_data.py

# Validate test data
python scripts/validate_data.py
```

### Integration Tests

```bash
# Test full pipeline
python scripts/test_pipeline.py

# Test monitoring system
python scripts/test_monitoring.py
```

## Contributing

### Development Workflow

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/wequo.git
   cd wequo
   ```

2. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make Changes**
   - Follow the existing code style
   - Add tests for new functionality
   - Update documentation as needed

4. **Test Your Changes**
   ```bash
   python -m pytest tests/
   python scripts/run_weekly.py  # Test pipeline
   ```

5. **Commit and Push**
   ```bash
   git add .
   git commit -m "Add your feature"
   git push origin feature/your-feature-name
   ```

6. **Create Pull Request**
   - Provide clear description of changes
   - Include test results
   - Update documentation if needed

### Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Add docstrings for functions and classes
- Keep functions small and focused
- Use meaningful variable names

### Adding New Connectors

1. Create connector in `src/wequo/connectors/`
2. Implement `fetch()` and `normalize()` methods
3. Add configuration in `config.yml`
4. Add tests in `tests/test_connectors.py`
5. Update documentation

### Adding New Analytics

1. Create analytics module in `src/wequo/analytics/`
2. Implement analysis methods
3. Integrate with `AnalyticsEngine`
4. Add performance monitoring
5. Update tests and documentation

## Troubleshooting

### Common Issues

#### 1. API Key Errors

**Problem**: `401 Unauthorized` or `403 Forbidden` errors
**Solution**:
```bash
# Check your .env file
cat .env | grep API_KEY

# Test API keys individually
python -c "import os; print(os.environ.get('FRED_API_KEY'))"
```

#### 2. Connection Timeouts

**Problem**: `TimeoutError` or `ConnectionError`
**Solution**:
```bash
# Check network connectivity
ping api.stlouisfed.org

# Increase timeout in config
# Edit src/wequo/config.yml
```

#### 3. Memory Issues

**Problem**: `MemoryError` with large datasets
**Solution**:
```bash
# Use optimized pipeline
python scripts/run_weekly_optimized.py

# Reduce chunk size in config
# Edit src/wequo/config.yml
optimization:
  chunk_size: 5000  # Reduce from 10000
```

#### 4. Permission Errors

**Problem**: `PermissionError` when writing files
**Solution**:
```bash
# Check directory permissions
ls -la data/output/

# Create output directory
mkdir -p data/output
chmod 755 data/output
```

### Debug Mode

Enable debug logging:

```bash
# Set debug environment variable
export DEBUG=true

# Or run with debug flag
python scripts/run_weekly.py --debug
```

### Log Files

Check log files for detailed error information:

```bash
# Main pipeline logs
tail -f pipeline.log

# Monitoring logs
tail -f monitoring.log

# Error logs
cat logs/error_log.json | jq .
```

### Performance Issues

If the pipeline is running slowly:

1. **Check System Resources**
   ```bash
   # Monitor CPU and memory
   htop  # or top on Linux/macOS
   ```

2. **Optimize Configuration**
   ```yaml
   optimization:
     max_workers: 4  # Reduce if CPU limited
     chunk_size: 5000  # Reduce if memory limited
   ```

3. **Use Optimized Pipeline**
   ```bash
   python scripts/run_weekly_optimized.py
   ```

### Getting Help

1. **Check Documentation**
   - [Monitoring Guide](monitoring.md)
   - [API Documentation](api.md)

2. **Search Issues**
   - Check existing GitHub issues
   - Search for similar problems

3. **Create Issue**
   - Provide error logs
   - Include system information
   - Describe steps to reproduce

4. **Community Support**
   - Join our Discord/Slack
   - Ask questions in discussions

## Advanced Configuration

### Custom Connectors

Create custom connectors for new data sources:

```python
# src/wequo/connectors/custom.py
from ..connectors.base import BaseConnector

class CustomConnector(BaseConnector):
    def fetch(self):
        # Implement data fetching
        pass
    
    def normalize(self, df):
        # Implement data normalization
        pass
```

### Custom Analytics

Add custom analytics modules:

```python
# src/wequo/analytics/custom.py
class CustomAnalyzer:
    def analyze(self, data):
        # Implement custom analysis
        pass
```

### Scaling for Production

For production deployments:

1. **Use Optimized Pipeline**
   ```bash
   python scripts/run_weekly_optimized.py
   ```

2. **Configure Monitoring**
   ```yaml
   monitoring:
     enabled: true
     check_interval_minutes: 5
   ```

3. **Set Up Alerts**
   ```bash
   # Configure all alert channels
   SLACK_WEBHOOK_URL=...
   EMAIL_FROM=...
   WEBHOOK_URL=...
   ```

4. **Use Process Manager**
   ```bash
   # Use systemd, PM2, or similar
   pm2 start scripts/run_web_app.py --name wequo-dashboard
   ```

This quickstart guide should get you up and running with WeQuo development quickly. For more detailed information, see the full documentation in the `docs/` directory.
