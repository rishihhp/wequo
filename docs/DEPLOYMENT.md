# WeQuo Deployment Guide

This guide covers deploying the WeQuo platform to Render.com for production use.

## Prerequisites

- GitHub repository with WeQuo code
- Render.com account
- API keys for data sources (see [API Keys](#api-keys) section)

## Quick Deployment

### 1. Prepare Your Repository

Ensure your repository contains all the necessary files:

```
wequo/
├── app.py                    # Main application entry point
├── render.yaml              # Render deployment configuration
├── requirements.txt         # Python dependencies
├── scripts/
│   └── init_data.py        # Data initialization script
├── src/wequo/              # Application source code
├── templates/              # HTML templates
└── docs/                   # Documentation
```

### 2. Deploy to Render

1. **Connect Repository**

   - Log in to [Render.com](https://render.com)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository

2. **Configure Service**

   - **Name**: `wequo-platform`
   - **Environment**: `Python 3`
   - **Region**: `Oregon (US West)`
   - **Branch**: `main`
   - **Root Directory**: `wequo` (if your code is in a subdirectory)

3. **Build & Deploy Settings**

   - **Build Command**:
     ```bash
     pip install --upgrade pip && pip install -r requirements.txt && python scripts/init_data.py
     ```
   - **Start Command**:
     ```bash
     python app.py
     ```

4. **Environment Variables**
   Add the following environment variables in Render dashboard:

   **Required:**

   - `FRED_API_KEY`: Your FRED API key
   - `SECRET_KEY`: Random secret key (Render can generate this)

   **Optional (for additional data sources):**

   - `ALPHA_VANTAGE_API_KEY`: For commodities data
   - `ACLED_API_KEY`: For conflict data
   - `ACLED_EMAIL`: Your registered email for ACLED
   - `NOAA_API_KEY`: For weather data
   - `UNCOMTRADE_API_KEY`: For trade data
   - `MARINETRAFFIC_API_KEY`: For shipping data

5. **Deploy**
   - Click "Create Web Service"
   - Wait for build and deployment to complete
   - Your app will be available at `https://your-app-name.onrender.com`

## API Keys

### Required API Keys

#### FRED API Key

1. Visit [FRED API Documentation](https://fred.stlouisfed.org/docs/api/api_key.html)
2. Sign up for a free account
3. Generate an API key
4. Add to Render environment variables as `FRED_API_KEY`

### Optional API Keys

#### Alpha Vantage (Commodities)

- Get free API key at [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
- Add as `ALPHA_VANTAGE_API_KEY`

#### ACLED (Conflict Data)

- Register at [ACLED](https://acleddata.com/request-access/)
- Add both `ACLED_API_KEY` and `ACLED_EMAIL`

#### NOAA (Weather Data)

- Get API key at [NOAA API](https://www.ncdc.noaa.gov/cdo-web/token)
- Add as `NOAA_API_KEY`

#### UN Comtrade (Trade Data)

- Subscribe at [UN Comtrade](https://comtrade.un.org/data/doc/api/)
- Add as `UNCOMTRADE_API_KEY`

#### MarineTraffic (Shipping Data)

- Get API key at [MarineTraffic API](https://www.marinetraffic.com/en/ais-api-services)
- Add as `MARINETRAFFIC_API_KEY`

## Application Structure

Once deployed, your WeQuo platform will have:

### Main Landing Page

- **URL**: `https://your-app.onrender.com/`
- **Features**: Service overview and navigation

### Authoring Dashboard

- **URL**: `https://your-app.onrender.com/authoring`
- **Features**:
  - Create and edit weekly briefs
  - Version control and collaboration
  - Review and approval workflow
  - Template management

### Monitoring Dashboard

- **URL**: `https://your-app.onrender.com/monitoring`
- **Features**:
  - Pipeline health monitoring
  - SLA compliance tracking
  - Alert management
  - Data search and export

### Health Check

- **URL**: `https://your-app.onrender.com/health`
- **Response**: `{"status": "healthy", "service": "wequo"}`

## Configuration

### Production Settings

The application uses the following production-optimized settings:

- **SLA Reports**: Cached for 6 hours to reduce computational load
- **Data Storage**: Persistent storage in `/data` directory
- **Logging**: INFO level with log rotation
- **Timeout**: 300 seconds for data operations
- **Workers**: 4 concurrent workers for data processing

### Customization

You can modify settings in `src/wequo/config.yml`:

```yaml
run:
  output_root: "data/output"
  lookback_days: 7
  max_workers: 4
  timeout_seconds: 300

monitoring:
  sla:
    cache_duration_hours: 6 # Adjust cache duration
  log_level: "INFO"
  max_log_files: 10
```

## Data Management

### Initial Data

- Sample data is created during deployment
- Data directories are automatically initialized
- Search index is built on first run

### Data Persistence

- Data is stored in the `/data` directory
- Render provides persistent storage for this directory
- Data survives application restarts

### Backup Recommendations

- Consider setting up automated backups of the `/data` directory
- Export important briefs and reports regularly
- Monitor disk usage in the monitoring dashboard

## Monitoring and Maintenance

### Health Monitoring

- Use the built-in health check endpoint
- Monitor application logs in Render dashboard
- Check SLA compliance in the monitoring dashboard

### Performance Optimization

- SLA reports are cached for 6 hours
- Use the "Refresh" button for immediate updates
- Monitor resource usage in Render dashboard

### Troubleshooting

#### Common Issues

1. **Build Failures**

   - Check Python version compatibility
   - Verify all dependencies in requirements.txt
   - Check build logs in Render dashboard

2. **Runtime Errors**

   - Verify all environment variables are set
   - Check application logs
   - Ensure API keys are valid

3. **Data Issues**
   - Check data directory permissions
   - Verify data initialization completed
   - Review monitoring dashboard for errors

#### Getting Help

1. **Application Logs**: Check Render dashboard logs
2. **Monitoring Dashboard**: Use built-in monitoring tools
3. **Health Check**: Verify service status
4. **Documentation**: Refer to additional docs in `/docs`

## Scaling Considerations

### Render Plans

- **Starter**: Good for development and testing
- **Standard**: Recommended for production use
- **Pro**: For high-traffic applications

### Resource Limits

- **Memory**: Monitor usage in Render dashboard
- **Storage**: Data directory grows over time
- **CPU**: Analytics operations can be CPU-intensive

### Optimization Tips

1. **Data Cleanup**: Regularly clean old data
2. **Cache Usage**: Leverage SLA report caching
3. **API Limits**: Monitor external API usage
4. **Resource Monitoring**: Use built-in monitoring tools

## Security Considerations

### Environment Variables

- Never commit API keys to version control
- Use Render's environment variable system
- Rotate API keys regularly

### Data Protection

- Data is stored securely in Render's infrastructure
- Access is controlled through the web interface
- Consider additional security measures for sensitive data

### API Security

- API keys are stored securely
- External API calls use HTTPS
- Monitor for unusual API usage patterns

## Support and Maintenance

### Regular Tasks

- Monitor application health
- Review SLA compliance
- Update API keys as needed
- Clean up old data files

### Updates

- Deploy updates through Render dashboard
- Test changes in staging environment
- Monitor performance after updates

### Documentation

- Keep deployment documentation updated
- Document any custom configurations
- Maintain API key inventory

---

## Quick Reference

### Essential URLs

- **Main App**: `https://your-app.onrender.com/`
- **Authoring**: `https://your-app.onrender.com/authoring`
- **Monitoring**: `https://your-app.onrender.com/monitoring`
- **Health Check**: `https://your-app.onrender.com/health`

### Key Files

- **Main App**: `app.py`
- **Config**: `src/wequo/config.yml`
- **Dependencies**: `requirements.txt`
- **Deployment**: `render.yaml`

### Environment Variables

- **Required**: `FRED_API_KEY`, `SECRET_KEY`
- **Optional**: Various data source API keys
- **System**: `HOST`, `PORT`, `DEBUG`

---

_Last updated: January 2025_
