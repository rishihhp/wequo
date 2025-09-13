# WeQuo Search & Export Functionality

## Overview

The WeQuo search and export functionality has been moved from the main web application to the monitoring dashboard, providing a centralized location for data search, exploration, and export capabilities.

## Features

### 🔍 Advanced Search

- **Full-text search** across all data packages, analytics, reports, and data points
- **Faceted filtering** by document type, data source, and tags
- **Real-time suggestions** and autocomplete
- **Relevance scoring** with highlighted search results

### 📊 Data Types Searchable

- **Packages**: Complete data packages with metadata
- **Data Points**: Individual time series data points
- **Analytics**: Generated insights, deltas, anomalies, and trends
- **Reports**: Markdown reports and documentation
- **Anomalies**: Detected statistical anomalies
- **Trends**: Identified market trends

### 📁 Export Capabilities

- **HTML Format**: Web-ready reports with styling
- **PDF Format**: Print-ready documents (requires WeasyPrint)
- **Markdown Format**: Raw markdown for further processing
- **Package Export**: Export complete weekly data packages

## Usage

### Starting the Monitoring Dashboard

```bash
cd wequo
python scripts/run_monitoring_dashboard.py
```

The dashboard will be available at: http://localhost:5001

### Accessing Search

1. Navigate to http://localhost:5001/search
2. Or click "Search & Export" from the monitoring dashboard

### Search Examples

- `"inflation"` - Find inflation-related data
- `"DFF"` - Find Federal Funds Rate data
- `"anomaly"` - Find detected anomalies
- `"2025-09-12"` - Find data from specific date
- `"FRED"` - Find Federal Reserve Economic Data

### Exporting Data

1. Search for packages (document type: "package")
2. Hover over package results to see export options
3. Choose format: HTML, PDF, or Markdown
4. Downloads will start automatically

## API Endpoints

The monitoring dashboard provides REST API endpoints:

- `GET /api/search?q={query}` - Perform search
- `POST /api/search/rebuild` - Rebuild search index
- `GET /api/packages` - List available packages
- `GET /export/{date}/{format}` - Export package in specified format

## Configuration

Search functionality uses the following configuration:

- **Index Location**: `data/search/`
- **Document Storage**: `documents.jsonl`
- **Statistics**: `stats.json`
- **Export Templates**: `templates/export/`

## Rebuilding Search Index

The search index is automatically built when data packages are created. To manually rebuild:

1. Click "Rebuild Index" in the search interface
2. Or call `POST /api/search/rebuild`

## Architecture

```
┌─────────────────────────────────────┐
│         Monitoring Dashboard        │
│  (http://localhost:5001)           │
├─────────────────────────────────────┤
│  ┌─────────────┐  ┌───────────────┐ │
│  │  Monitoring │  │ Search & Export│ │
│  │  /          │  │ /search        │ │
│  └─────────────┘  └───────────────┘ │
├─────────────────────────────────────┤
│  ┌─────────────────────────────────┐ │
│  │       Search Engine             │ │
│  │  - Full-text search             │ │
│  │  - Faceted filtering            │ │
│  │  - Relevance scoring            │ │
│  └─────────────────────────────────┘ │
├─────────────────────────────────────┤
│  ┌─────────────────────────────────┐ │
│  │       Export Engine             │ │
│  │  - HTML/PDF/Markdown           │ │
│  │  - Template rendering          │ │
│  │  - Package exports             │ │
│  └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

## Benefits

1. **Centralized Access**: Single location for monitoring, search, and export
2. **Real-time Search**: Instant search across all data types
3. **Multiple Export Formats**: Choose the right format for your needs
4. **Comprehensive Coverage**: Search everything from raw data to analytics
5. **User-friendly Interface**: Modern, responsive design
6. **API Access**: Programmatic access for automation

## Future Enhancements

- Saved search queries
- Scheduled exports
- Advanced filtering options
- Data visualization in search results
- Bulk export capabilities
