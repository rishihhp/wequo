# Database Integration Migration Guide

## Overview

The WeQuo application has been updated to use **SQLite database** for persistent storage instead of solely relying on CSV files. This provides:

✅ **Centralized data storage** - All time-series data in one place  
✅ **Efficient querying** - Fast indexed lookups  
✅ **Analytics persistence** - Store anomalies, trends, correlations  
✅ **Pipeline tracking** - Complete audit trail of all runs  
✅ **Backward compatibility** - CSV files still generated for compatibility

## What Changed

### Before (CSV-only)

```
data/output/
  └── 2025-09-13/
      ├── fred.csv
      ├── commodities.csv
      ├── crypto.csv
      └── ...
```

### After (Database + CSV)

```
data/
  ├── wequo.db              # SQLite database (primary storage)
  └── output/
      └── 2025-09-13/       # CSV files (for compatibility)
          ├── fred.csv
          ├── commodities.csv
          └── ...
```

## Quick Start

### 1. Run the Pipeline

The pipeline now automatically uses the database:

```bash
python scripts/run_weekly.py
```

This will:

- Create `data/wequo.db` if it doesn't exist
- Fetch data from connectors
- Store data in database
- Also write CSV files for backward compatibility
- Store analytics results in database

### 2. Query the Database

Use the command-line tool:

```bash
# Show database statistics
python scripts/db_query.py stats

# List all data sources
python scripts/db_query.py sources

# View latest values
python scripts/db_query.py latest

# Query specific data
python scripts/db_query.py query --source FRED --limit 10

# View analytics
python scripts/db_query.py analytics anomalies
```

### 3. Export to CSV

Export database contents to CSV files:

```bash
python scripts/db_query.py export 2025-09-13 --output-dir data/output
```

## Configuration

Update `src/wequo/config.yml`:

```yaml
run:
  output_root: "data/output"
  lookback_days: 7
  database_path: "data/wequo.db" # ← Database location
```

## Database Schema

The database includes these main tables:

### Core Data

- **`series`** - Metadata for each time series
- **`data_points`** - All time-series data points
- **`metadata`** - Data provenance and lineage

### Pipeline Tracking

- **`pipeline_runs`** - Execution history
- **`connectors`** - Connector status

### Analytics

- **`analytics_anomalies`** - Detected anomalies
- **`analytics_trends`** - Trend analysis
- **`analytics_correlations`** - Series correlations
- **`analytics_changepoints`** - Structural changes

See [DATABASE.md](DATABASE.md) for complete schema documentation.

## Python API

### Basic Usage

```python
from wequo.database import WeQuoDB

# Initialize
db = WeQuoDB("data/wequo.db")

# Query data
df = db.get_data_points(
    source="FRED",
    start_date="2025-09-01",
    limit=100
)

# Get latest values
latest = db.get_latest_values(source="CRYPTO")

# Close connection
db.close()
```

### In Your Code

```python
from wequo.database import WeQuoDB
import pandas as pd

db = WeQuoDB()

# Insert data
data = pd.DataFrame({
    'series_id': ['SERIES1', 'SERIES2'],
    'date': ['2025-09-13', '2025-09-13'],
    'value': [100.0, 200.0],
    'source': ['CUSTOM', 'CUSTOM'],
    'connector': ['custom', 'custom']
})

inserted = db.insert_data_points(data)
print(f"Inserted {inserted} rows")

# Track pipeline runs
run_id = db.start_pipeline_run(['connector1', 'connector2'])

# ... run your pipeline ...

db.finish_pipeline_run(
    run_id=run_id,
    status='success',
    connectors_succeeded=['connector1'],
    connectors_failed=['connector2'],
    data_points=1000,
    errors=['connector2 timeout'],
    output_dir='data/output/2025-09-13'
)

db.close()
```

## Migrating Existing Data

If you have existing CSV data, migrate it to the database:

```python
from wequo.database import WeQuoDB
import pandas as pd
from pathlib import Path

db = WeQuoDB()

# Migrate data from a specific date
csv_dir = Path("data/output/2025-09-13")
for csv_file in csv_dir.glob("*.csv"):
    df = pd.read_csv(csv_file)
    source = csv_file.stem.upper()

    # Ensure required columns
    if 'source' not in df.columns:
        df['source'] = source
    if 'connector' not in df.columns:
        df['connector'] = source.lower()

    # Insert
    inserted = db.insert_data_points(df)
    print(f"Migrated {inserted} rows from {csv_file.name}")

db.close()
```

## Benefits of Database Approach

### 1. **Data Deduplication**

- Unique constraint on (series_id, date)
- Automatically handles duplicate data

### 2. **Fast Queries**

- Indexed columns for quick lookups
- Query by source, date range, series

### 3. **Analytics Storage**

- Persist anomalies, trends, correlations
- Historical analytics tracking

### 4. **Audit Trail**

- Complete pipeline run history
- Track connector success/failure rates

### 5. **Data Integrity**

- Foreign key constraints
- Transaction support

## Performance Tips

1. **Batch Inserts**: Insert DataFrames instead of row-by-row

   ```python
   db.insert_data_points(large_df)  # ✅ Fast
   ```

2. **Use Indexes**: Queries on indexed columns are optimized

   - series_id, date, source, pipeline_run_id

3. **Connection Pooling**: Reuse connections

   ```python
   with db.get_connection() as conn:
       # Multiple queries with same connection
   ```

4. **Archive Old Data**: Keep database size manageable
   ```sql
   DELETE FROM data_points WHERE date < date('now', '-1 year');
   VACUUM;
   ```

## Backup and Restore

### Backup

```bash
# Simple copy
cp data/wequo.db data/backups/wequo_$(date +%Y%m%d).db

# SQLite backup command
sqlite3 data/wequo.db ".backup data/backups/wequo.db"
```

### Restore

```bash
cp data/backups/wequo_20250913.db data/wequo.db
```

## Troubleshooting

### "Database is locked"

- Only one process can write at a time
- Close connections properly: `db.close()`
- Increase timeout in connection

### Schema Changes

- Database auto-creates missing tables
- Existing data is preserved
- Safe to re-run initialization

### Reset Database

```bash
rm data/wequo.db
python scripts/run_weekly.py  # Creates fresh database
```

## Backward Compatibility

✅ CSV files are **still generated** in `data/output/`  
✅ Existing scripts reading CSVs continue to work  
✅ Database is **additive** - doesn't break existing workflows

## Next Steps

1. ✅ Run pipeline: `python scripts/run_weekly.py`
2. ✅ Explore data: `python scripts/db_query.py stats`
3. ✅ Query analytics: `python scripts/db_query.py analytics anomalies`
4. ✅ Read full docs: [DATABASE.md](DATABASE.md)

## Support

For detailed schema and API documentation, see:

- [DATABASE.md](DATABASE.md) - Complete schema reference
- [API Documentation](../src/wequo/database.py) - Python API

---

**Database Location**: `data/wequo.db`  
**Query Tool**: `scripts/db_query.py`  
**Schema Docs**: [DATABASE.md](DATABASE.md)
