# WeQuo Onboarding Guide

Welcome to WeQuo - a comprehensive data pipeline and authoring system for global risk and opportunity briefs. This guide will help you get started with setup, configuration, and daily operations.

## Table of Contents

1. [System Overview](#system-overview)
2. [Initial Setup](#initial-setup)
3. [Running the Application](#running-the-application)
4. [For Authors](#for-authors)
5. [For Administrators](#for-administrators)
6. [Troubleshooting](#troubleshooting)

## System Overview

WeQuo is a multi-component system that:

- **Data Pipeline**: Collects data from multiple sources (FRED, commodities, crypto, economic indicators, etc.)
- **Analytics Engine**: Performs anomaly detection, trend analysis, and advanced statistical analysis
- **Authoring System**: Provides version control and workflow management for content creation
- **Monitoring Dashboard**: Tracks system health, SLA compliance, and generates alerts
- **Web Applications**: User interfaces for authors and administrators

### Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Sources  │───▶│  WeQuo Pipeline │───▶│  Authoring      │
│   (FRED, etc.)  │    │  (Connectors)   │    │  System         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Monitoring    │
                       │   Dashboard     │
                       └─────────────────┘
```

## Initial Setup

### Prerequisites

- Python 3.10 or higher
- Git
- API keys for data sources (see [API Keys](#api-keys) section)

### 1. Clone and Install

```bash
# Clone the repository
git clone <repository-url>
cd wequo-1


# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

```bash
# Copy environment template
cp env.example .env

```

### 3. API Keys

Configure the following API keys in your `.env` file:

#### Required

- `FRED_API_KEY`: Get from [FRED API](https://fred.stlouisfed.org/docs/api/api_key.html)

#### Optional (for additional data sources)

- `ALPHA_VANTAGE_API_KEY`: For commodities data
- `ACLED_API_KEY` & `ACLED_EMAIL`: For conflict data
- `NOAA_API_KEY`: For weather data
- `UNCOMTRADE_API_KEY`: For trade data
- `MARINETRAFFIC_API_KEY`: For shipping data

### 4. Configuration

The system uses `src/wequo/config.yml` for configuration. Key settings:

- **Data Sources**: Enable/disable connectors
- **Analytics**: Configure anomaly detection thresholds
- **Monitoring**: Set SLA targets and alert thresholds
- **Output**: Specify data storage location

## Running the Application

### 1. Data Pipeline (Weekly Run)

```bash
# Run the complete data collection pipeline
python scripts/run_weekly.py
```

This will:

- Collect data from enabled sources
- Perform analytics and anomaly detection
- Generate QA reports
- Create prefill notes for authors
- Update monitoring metrics

### 2. Author Dashboard

```bash
# Start the authoring web application
python scripts/run_web_app.py
```

Access at: `http://localhost:5000`

Features:

- Create and edit weekly briefs
- Version control and collaboration
- Review and approval workflow
- Template management

### 3. Monitoring Dashboard

```bash
# Start the monitoring dashboard
python scripts/run_monitoring_dashboard.py
```

Access at: `http://localhost:5001`

Features:

- Pipeline health monitoring
- SLA compliance tracking
- Alert management
- Data search and export

## For Authors

### Getting Started

1. **Access the Author Dashboard**

   - Navigate to `http://localhost:5000`
   - Use your configured credentials

2. **Create a New Brief**

   - Click "New Brief"
   - Select package date
   - Choose template
   - Add reviewers

3. **Edit Content**
   - Use the built-in editor
   - Reference prefill notes from data pipeline
   - Save versions as you work

### Key Features

#### Version Control

- Track all changes
- Compare versions side-by-side
- Rollback to previous versions

#### Templates

- Pre-built brief templates
- Customizable sections
- Auto-population from data pipeline
- Export to multiple formats

## For Administrators

### System Monitoring

#### 1. Dashboard Overview

Access the monitoring dashboard at `http://localhost:5001` to view:

- **Pipeline Status**: Success/failure rates
- **Data Freshness**: Last update timestamps
- **SLA Compliance**: Performance metrics
- **System Health**: Resource usage and alerts

#### 2. Key Metrics

**Pipeline Health:**

- Success rate (target: 99%)
- Data freshness (target: <25 hours)
- Processing time (target: <30 minutes)
- Anomaly rate (target: <10%)

**System Resources:**

- Disk usage (alert at 85%)
- Memory consumption
- CPU utilization
- Network connectivity

**Performance Optimization:**

- SLA reports are cached for 6 hours to reduce computational load
- Use the "Refresh" button in the SLA Status card to force immediate updates
- Monitoring dashboard auto-refreshes every 5 minutes for real-time data

#### 3. Alert Management

**Alert Types:**

- **Critical**: Pipeline failures, system outages
- **Warning**: SLA breaches, high anomaly rates
- **Info**: Successful runs, status updates

**Alert Channels:**

- File logs
- Console output
- Email notifications (configurable)
- Webhook integrations (configurable)

### Configuration Management

#### 1. Data Source Configuration

Edit `src/wequo/config.yml` to:

- Enable/disable data connectors
- Adjust collection parameters
- Set data quality thresholds
- Configure API endpoints

### Maintenance Tasks

### Troubleshooting Common Issues

#### Pipeline Failures

1. Check API key validity
2. Verify network connectivity
3. Review error logs in monitoring dashboard
4. Check data source availability

#### Performance Issues

1. Monitor disk usage
2. Check memory consumption
3. Review processing times
4. Optimize data collection schedules
5. SLA reports are cached for 6 hours - use "Refresh" button for immediate updates

#### Alert Fatigue

1. Adjust alert thresholds
2. Configure severity levels
3. Set up alert filtering
4. Review notification channels

## Troubleshooting

### Common Issues

#### 1. Import Errors

```bash
# Ensure you're in the correct directory
cd wequo-1

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

#### 2. API Key Issues

- Verify keys are correctly set in `.env`
- Check API key validity with source providers
- Ensure no extra spaces or quotes in configuration

#### 3. Port Conflicts

- Change ports in script files if 5000/5001 are in use
- Update environment variables accordingly

#### 4. Permission Errors

- Ensure write permissions for data directories
- Check file ownership and access rights

### Getting Help

1. **Check Logs**: Review console output and log files
2. **Monitor Dashboard**: Use the monitoring interface for diagnostics
3. **Configuration**: Verify all settings in `config.yml` and `.env`
4. **Documentation**: Refer to additional docs in the `docs/` directory

### Support Contacts

- **Technical Issues**: Check monitoring dashboard alerts
- **Data Questions**: Review analytics reports and QA summaries
- **Workflow Issues**: Consult authoring system documentation

---

## Quick Reference

### Essential Commands

```bash
# Run data pipeline
python scripts/run_weekly.py

# Start author dashboard
python scripts/run_web_app.py

# Start monitoring dashboard
python scripts/run_monitoring_dashboard.py
```

### Key URLs

- Author Dashboard: `http://localhost:5000`
- Monitoring Dashboard: `http://localhost:5001`

### Important Files

- Configuration: `src/wequo/config.yml`
- Environment: `.env`
- Dependencies: `requirements.txt`
- Data Output: `data/output/`

---

_Last updated: September 2025_
