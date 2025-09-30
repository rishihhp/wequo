# WeQuo Database Schema

WeQuo uses SQLite for persistent data storage. All time-series data, analytics results, and pipeline metadata are stored in a single SQLite database.

## Database Location

Default: `data/wequo.db`

Can be configured in `config.yml`:
```yaml
run:
  database_path: "data/wequo.db"
```

## Schema Overview

### Core Data Tables

#### `series`
Stores metadata about each time series.

| Column | Type | Description |
|--------|------|-------------|
| series_id | TEXT PRIMARY KEY | Unique identifier for the series |
| source | TEXT | Data source (e.g., FRED, COMMODITIES) |
| connector | TEXT | Connector that fetched the data |
| description | TEXT | Series description |
| unit | TEXT | Unit of measurement |
| frequency | TEXT | Data frequency (daily, weekly, etc.) |
| first_date | TEXT | Earliest data point date |
| last_date | TEXT | Latest data point date |
| data_points_count | INTEGER | Total number of data points |
| created_at | TEXT | Record creation timestamp |
| updated_at | TEXT | Last update timestamp |
| metadata_json | TEXT | Additional metadata as JSON |

#### `data_points`
Main table storing all time-series data points.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-incrementing ID |
| series_id | TEXT | Reference to series |
| date | TEXT | Date of the data point (ISO format) |
| value | REAL | Numeric value |
| source | TEXT | Data source |
| connector | TEXT | Connector name |
| pipeline_run_id | TEXT | Reference to pipeline run |
| metadata_id | TEXT | Reference to metadata record |
| created_at | TEXT | Record creation timestamp |
| extra_data_json | TEXT | Connector-specific data as JSON |

**Indexes:**
- `idx_data_points_series_date` on (series_id, date)
- `idx_data_points_source` on (source)
- `idx_data_points_date` on (date)
- `idx_data_points_pipeline_run` on (pipeline_run_id)

**Unique Constraint:** (series_id, date)

### Pipeline Tracking Tables

#### `pipeline_runs`
Tracks execution of data pipeline runs.

| Column | Type | Description |
|--------|------|-------------|
| run_id | TEXT PRIMARY KEY | Unique run identifier |
| start_time | TEXT | Pipeline start timestamp |
| end_time | TEXT | Pipeline end timestamp |
| status | TEXT | success, partial_failure, or failure |
| duration_seconds | REAL | Execution duration |
| connectors_attempted | TEXT | List of attempted connectors (JSON) |
| connectors_succeeded | TEXT | List of successful connectors (JSON) |
| connectors_failed | TEXT | List of failed connectors (JSON) |
| data_points_collected | INTEGER | Total data points fetched |
| errors_json | TEXT | Error messages as JSON |
| output_dir | TEXT | Output directory path |
| created_at | TEXT | Record creation timestamp |

#### `connectors`
Tracks connector status and performance.

| Column | Type | Description |
|--------|------|-------------|
| connector_name | TEXT PRIMARY KEY | Connector identifier |
| enabled | BOOLEAN | Whether connector is enabled |
| last_successful_run | TEXT | Last successful run timestamp |
| last_failed_run | TEXT | Last failed run timestamp |
| total_runs | INTEGER | Total number of runs |
| successful_runs | INTEGER | Number of successful runs |
| failed_runs | INTEGER | Number of failed runs |
| avg_duration_seconds | REAL | Average execution duration |
| config_json | TEXT | Connector configuration as JSON |
| updated_at | TEXT | Last update timestamp |

### Analytics Tables

#### `analytics_anomalies`
Stores detected anomalies in time-series data.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-incrementing ID |
| series_id | TEXT | Reference to series |
| date | TEXT | Date of anomaly |
| value | REAL | Anomalous value |
| z_score | REAL | Statistical z-score |
| source | TEXT | Data source |
| pipeline_run_id | TEXT | Reference to pipeline run |
| created_at | TEXT | Record creation timestamp |

#### `analytics_trends`
Stores trend analysis results.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-incrementing ID |
| series_id | TEXT | Reference to series |
| slope | REAL | Trend slope |
| trend_strength | TEXT | weak, moderate, strong |
| direction | TEXT | up or down |
| r_squared | REAL | Coefficient of determination |
| start_date | TEXT | Trend start date |
| end_date | TEXT | Trend end date |
| pipeline_run_id | TEXT | Reference to pipeline run |
| created_at | TEXT | Record creation timestamp |

#### `analytics_correlations`
Stores correlation analysis between series.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-incrementing ID |
| series1_id | TEXT | First series ID |
| series2_id | TEXT | Second series ID |
| correlation_coefficient | REAL | Correlation coefficient (-1 to 1) |
| correlation_type | TEXT | positive or negative |
| p_value | REAL | Statistical significance |
| lag | INTEGER | Time lag applied |
| pipeline_run_id | TEXT | Reference to pipeline run |
| created_at | TEXT | Record creation timestamp |

#### `analytics_changepoints`
Stores detected structural changes in series.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-incrementing ID |
| series_id | TEXT | Reference to series |
| timestamp | TEXT | Changepoint timestamp |
| change_type | TEXT | Type of change detected |
| magnitude | REAL | Change magnitude |
| confidence | REAL | Detection confidence (0-1) |
| pipeline_run_id | TEXT | Reference to pipeline run |
| created_at | TEXT | Record creation timestamp |

### Metadata Table

#### `metadata`
Stores data provenance and metadata information.

| Column | Type | Description |
|--------|------|-------------|
| metadata_id | TEXT PRIMARY KEY | Unique metadata identifier |
| timestamp | TEXT | Metadata creation timestamp |
| api_endpoint | TEXT | API endpoint used |
| source_url | TEXT | Original data source URL |
| fetch_duration_ms | REAL | Data fetch duration |
| confidence_score | REAL | Data quality confidence |
| validation_status | TEXT | Validation result |
| data_license | TEXT | Data license information |
| terms_of_service_url | TEXT | Terms of service URL |
| api_version | TEXT | API version used |
| transformation_log_json | TEXT | Data transformations as JSON |
| pipeline_run_id | TEXT | Reference to pipeline run |
| created_at | TEXT | Record creation timestamp |

## Usage Examples

### Command Line Query Tool

Use the `db_query.py` script to interact with the database:

```bash
# Show database statistics
python scripts/db_query.py stats

# List all data sources
python scripts/db_query.py sources

# List series for a specific source
python scripts/db_query.py series FRED

# Query data points
python scripts/db_query.py query --source FRED --limit 10

# Get latest values
python scripts/db_query.py latest --source CRYPTO

# View recent pipeline runs
python scripts/db_query.py runs --limit 5

# View detected anomalies
python scripts/db_query.py analytics anomalies --limit 20

# Export data to CSV
python scripts/db_query.py export 2025-09-13 --output-dir data/output
```

### Python API

```python
from wequo.database import WeQuoDB

# Initialize database
db = WeQuoDB("data/wequo.db")

# Get all sources
sources = db.get_all_sources()

# Query data points
df = db.get_data_points(
    source="FRED",
    start_date="2025-09-01",
    end_date="2025-09-30",
    limit=100
)

# Get latest values
latest = db.get_latest_values(source="CRYPTO")

# Insert data points
db.insert_data_points(dataframe, pipeline_run_id="run_123")

# Start pipeline run
run_id = db.start_pipeline_run(["fred", "crypto", "commodities"])

# Finish pipeline run
db.finish_pipeline_run(
    run_id=run_id,
    status="success",
    connectors_succeeded=["fred", "crypto"],
    connectors_failed=[],
    data_points=1000,
    errors=[],
    output_dir="data/output/2025-09-13"
)

# Export to CSV files
db.export_to_csv(Path("data/output"), "2025-09-13")

# Close connection
db.close()
```

## Data Migration

### From CSV to Database

The pipeline automatically writes data to both the database and CSV files for backward compatibility. To migrate existing CSV data to the database:

```python
from wequo.database import WeQuoDB
import pandas as pd
from pathlib import Path

db = WeQuoDB("data/wequo.db")

# For each CSV file
csv_dir = Path("data/output/2025-09-13")
for csv_file in csv_dir.glob("*.csv"):
    df = pd.read_csv(csv_file)
    source = csv_file.stem.upper()
    
    # Add required columns if missing
    if 'source' not in df.columns:
        df['source'] = source
    if 'connector' not in df.columns:
        df['connector'] = source.lower()
    
    # Insert into database
    inserted = db.insert_data_points(df)
    print(f"Migrated {inserted} rows from {csv_file.name}")

db.close()
```

### Database Backup

```bash
# Create backup
cp data/wequo.db data/backups/wequo_$(date +%Y%m%d_%H%M%S).db

# Or use SQLite backup
sqlite3 data/wequo.db ".backup data/backups/wequo_backup.db"
```

## Performance Considerations

1. **Indexes**: The database includes indexes on commonly queried columns for fast lookups.

2. **Batch Inserts**: Use `insert_data_points()` with DataFrames for efficient bulk inserts.

3. **Connection Management**: Use context managers for proper connection handling:
   ```python
   with db.get_connection() as conn:
       # Execute queries
       cursor = conn.cursor()
       cursor.execute("SELECT ...")
   ```

4. **Database Size**: Monitor database size and consider archiving old data:
   ```sql
   -- Archive data older than 1 year
   DELETE FROM data_points WHERE date < date('now', '-1 year');
   VACUUM;  -- Reclaim space
   ```

## Troubleshooting

### Database Locked Error

If you encounter "database is locked" errors:
1. Ensure only one process accesses the database at a time
2. Close database connections properly
3. Increase timeout: `sqlite3.connect(db_path, timeout=30)`

### Schema Updates

To add new columns or tables, modify `database.py` and run:
```python
db = WeQuoDB("data/wequo.db")  # Will auto-create new schema
```

The initialization is idempotent - existing tables won't be affected.

### Reset Database

To start fresh:
```bash
rm data/wequo.db
python scripts/run_weekly.py  # Will create new database
```

## Schema Diagram

```
┌─────────────┐         ┌──────────────────┐
│   series    │◄────────│   data_points    │
└─────────────┘         └──────────────────┘
      │                          │
      │                          ▼
      │                  ┌───────────────┐
      │                  │ pipeline_runs │
      │                  └───────────────┘
      │                          │
      ▼                          ▼
┌──────────────────┐    ┌───────────────────┐
│ analytics_*      │    │    metadata       │
│ - anomalies      │    └───────────────────┘
│ - trends         │
│ - correlations   │
│ - changepoints   │
└──────────────────┘
```
