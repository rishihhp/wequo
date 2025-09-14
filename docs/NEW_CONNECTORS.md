# New Data Connectors

This document describes the new data connectors added to the WeQuo project, extending coverage to conflict data, food security, climate data, international trade, and maritime traffic.

## Added Connectors

### 1. ACLED Connector (`acled.py`)

**Source**: Armed Conflict Location & Event Data Project  
**Purpose**: Conflict and crisis event data  
**API**: https://api.acleddata.com/acled/read

**Environment Variables Required**:

- `ACLED_API_KEY`: Your ACLED API key
- `ACLED_EMAIL`: Your registered email address

**Data Collected**:

- Conflict events (battles, violence against civilians, riots, protests)
- Event locations (latitude/longitude)
- Fatality counts
- Event types and dates

**Configuration**: Set `enabled: true` in `config.yml` under `connectors.acled`

### 2. FAO Connector (`fao.py`)

**Source**: Food and Agriculture Organization  
**Purpose**: Food security and agricultural data  
**API**: https://fenixservices.fao.org/faostat/api/v1/en

**Environment Variables Required**: None (public API)

**Data Collected**:

- Crop production data
- Agricultural trade statistics
- Food balance sheets
- Producer prices
- Population data
- Land use statistics

**Configuration**: Set `enabled: true` in `config.yml` under `connectors.fao`

### 3. NOAA Connector (`noaa.py`)

**Source**: National Oceanic and Atmospheric Administration  
**Purpose**: Climate and weather data  
**API**: https://www.ncdc.noaa.gov/cdo-web/api/v2

**Environment Variables Required**:

- `NOAA_API_KEY`: Your NOAA API token

**Data Collected**:

- Temperature data (max/min)
- Precipitation data
- Snow data
- Wind speed
- Weather station observations

**Configuration**: Set `enabled: true` in `config.yml` under `connectors.noaa`

### 4. UN Comtrade Connector (`uncomtrade.py`)

**Source**: United Nations Comtrade  
**Purpose**: International trade statistics  
**API**: https://comtradeapi.un.org/data/v1/get

**Environment Variables Required**:

- `UNCOMTRADE_API_KEY`: Your UN Comtrade subscription key (optional, for higher rate limits)

**Data Collected**:

- Import/export trade values
- Commodity trade flows
- Trade quantities and weights
- Country-to-country trade data

**Configuration**: Set `enabled: true` in `config.yml` under `connectors.uncomtrade`

### 5. Shipping AIS Connector (`shipping_ais.py`)

**Source**: MarineTraffic API (example - multiple providers available)  
**Purpose**: Maritime traffic and shipping data  
**API**: https://services.marinetraffic.com/api

**Environment Variables Required**:

- `MARINETRAFFIC_API_KEY`: Your MarineTraffic API key

**Data Collected**:

- Port call statistics
- Vessel positions and density
- Ship types and characteristics
- Major shipping route traffic

**Configuration**: Set `enabled: true` in `config.yml` under `connectors.shipping_ais`

## Configuration

All new connectors are added to `config.yml` with `enabled: false` by default. To enable a connector:

1. Set `enabled: true` for the desired connector
2. Configure the required API keys in your environment variables
3. Adjust the configuration parameters as needed (countries, indicators, etc.)

## Integration

The new connectors are fully integrated into:

- `run_weekly.py` - Main pipeline execution
- Configuration system - YAML-based settings
- Error handling and monitoring - Same patterns as existing connectors
- Data validation - Standard validation pipeline
- Output generation - CSV exports and analytics

## API Rate Limits

Each connector implements:

- Retry logic with exponential backoff
- Rate limiting considerations
- Mock data fallbacks for development/testing
- Error handling and graceful degradation

## Mock Data

All connectors include mock data generation for:

- Development and testing
- API failures or rate limit scenarios
- Demonstration purposes when API keys are not available

## Usage

To run the pipeline with new connectors:

```bash
# Set required environment variables
export ACLED_API_KEY="your_key"
export ACLED_EMAIL="your_email"
export NOAA_API_KEY="your_key"
export UNCOMTRADE_API_KEY="your_key"
export MARINETRAFFIC_API_KEY="your_key"

# Enable desired connectors in config.yml
# Run the pipeline
python scripts/run_weekly.py
```

## Data Output

Each connector generates:

- CSV files in `data/output/{date}/` directory
- Normalized data with standard columns:
  - `date`: ISO date string
  - `value`: Numeric measurement
  - `series_id`: Unique identifier
  - `source`: Data source identifier
- Additional connector-specific metadata columns

## Architecture Compliance

All new connectors follow the established architecture:

- Implement the `Connector` protocol
- Include `fetch()` and `normalize()` methods
- Use dataclass structure
- Follow naming conventions
- Include comprehensive error handling
- Support configuration via YAML
