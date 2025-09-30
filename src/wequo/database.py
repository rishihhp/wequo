"""SQLite database module for WeQuo data storage and management."""
from __future__ import annotations
import sqlite3
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from contextlib import contextmanager
import pandas as pd


class WeQuoDB:
    """SQLite database manager for WeQuo application."""
    
    def __init__(self, db_path: str | Path = "data/wequo.db"):
        """Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = None
        self._initialize_db()
    
    def _initialize_db(self):
        """Initialize database with schema if it doesn't exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create tables
            self._create_series_table(cursor)
            self._create_data_points_table(cursor)
            self._create_pipeline_runs_table(cursor)
            self._create_analytics_anomalies_table(cursor)
            self._create_analytics_trends_table(cursor)
            self._create_analytics_correlations_table(cursor)
            self._create_analytics_changepoints_table(cursor)
            self._create_metadata_table(cursor)
            self._create_connectors_table(cursor)
            
            # Create indexes
            self._create_indexes(cursor)
            
            conn.commit()
    
    def _create_series_table(self, cursor):
        """Create series metadata table."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS series (
                series_id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                connector TEXT NOT NULL,
                description TEXT,
                unit TEXT,
                frequency TEXT,
                first_date TEXT,
                last_date TEXT,
                data_points_count INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                metadata_json TEXT
            )
        """)
    
    def _create_data_points_table(self, cursor):
        """Create main data points table."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_points (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                series_id TEXT NOT NULL,
                date TEXT NOT NULL,
                value REAL NOT NULL,
                source TEXT NOT NULL,
                connector TEXT NOT NULL,
                pipeline_run_id TEXT,
                metadata_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                extra_data_json TEXT,
                FOREIGN KEY (series_id) REFERENCES series(series_id),
                FOREIGN KEY (pipeline_run_id) REFERENCES pipeline_runs(run_id),
                UNIQUE(series_id, date)
            )
        """)
    
    def _create_pipeline_runs_table(self, cursor):
        """Create pipeline runs tracking table."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pipeline_runs (
                run_id TEXT PRIMARY KEY,
                start_time TEXT NOT NULL,
                end_time TEXT,
                status TEXT,
                duration_seconds REAL,
                connectors_attempted TEXT,
                connectors_succeeded TEXT,
                connectors_failed TEXT,
                data_points_collected INTEGER DEFAULT 0,
                errors_json TEXT,
                output_dir TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
    
    def _create_analytics_anomalies_table(self, cursor):
        """Create analytics anomalies table."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analytics_anomalies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                series_id TEXT NOT NULL,
                date TEXT NOT NULL,
                value REAL NOT NULL,
                z_score REAL,
                source TEXT,
                pipeline_run_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (series_id) REFERENCES series(series_id),
                FOREIGN KEY (pipeline_run_id) REFERENCES pipeline_runs(run_id)
            )
        """)
    
    def _create_analytics_trends_table(self, cursor):
        """Create analytics trends table."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analytics_trends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                series_id TEXT NOT NULL,
                slope REAL,
                trend_strength TEXT,
                direction TEXT,
                r_squared REAL,
                start_date TEXT,
                end_date TEXT,
                pipeline_run_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (series_id) REFERENCES series(series_id),
                FOREIGN KEY (pipeline_run_id) REFERENCES pipeline_runs(run_id)
            )
        """)
    
    def _create_analytics_correlations_table(self, cursor):
        """Create analytics correlations table."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analytics_correlations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                series1_id TEXT NOT NULL,
                series2_id TEXT NOT NULL,
                correlation_coefficient REAL,
                correlation_type TEXT,
                p_value REAL,
                lag INTEGER DEFAULT 0,
                pipeline_run_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (pipeline_run_id) REFERENCES pipeline_runs(run_id)
            )
        """)
    
    def _create_analytics_changepoints_table(self, cursor):
        """Create analytics changepoints table."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analytics_changepoints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                series_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                change_type TEXT,
                magnitude REAL,
                confidence REAL,
                pipeline_run_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (series_id) REFERENCES series(series_id),
                FOREIGN KEY (pipeline_run_id) REFERENCES pipeline_runs(run_id)
            )
        """)
    
    def _create_metadata_table(self, cursor):
        """Create metadata/provenance table."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metadata (
                metadata_id TEXT PRIMARY KEY,
                timestamp TEXT,
                api_endpoint TEXT,
                source_url TEXT,
                fetch_duration_ms REAL,
                confidence_score REAL,
                validation_status TEXT,
                data_license TEXT,
                terms_of_service_url TEXT,
                api_version TEXT,
                transformation_log_json TEXT,
                pipeline_run_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
    
    def _create_connectors_table(self, cursor):
        """Create connectors status table."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS connectors (
                connector_name TEXT PRIMARY KEY,
                enabled BOOLEAN DEFAULT 1,
                last_successful_run TEXT,
                last_failed_run TEXT,
                total_runs INTEGER DEFAULT 0,
                successful_runs INTEGER DEFAULT 0,
                failed_runs INTEGER DEFAULT 0,
                avg_duration_seconds REAL,
                config_json TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
    
    def _create_indexes(self, cursor):
        """Create database indexes for performance."""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_data_points_series_date ON data_points(series_id, date)",
            "CREATE INDEX IF NOT EXISTS idx_data_points_source ON data_points(source)",
            "CREATE INDEX IF NOT EXISTS idx_data_points_date ON data_points(date)",
            "CREATE INDEX IF NOT EXISTS idx_data_points_pipeline_run ON data_points(pipeline_run_id)",
            "CREATE INDEX IF NOT EXISTS idx_anomalies_series ON analytics_anomalies(series_id)",
            "CREATE INDEX IF NOT EXISTS idx_trends_series ON analytics_trends(series_id)",
            "CREATE INDEX IF NOT EXISTS idx_pipeline_runs_status ON pipeline_runs(status)",
            "CREATE INDEX IF NOT EXISTS idx_pipeline_runs_start_time ON pipeline_runs(start_time)",
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
    
    @contextmanager
    def get_connection(self):
        """Get database connection context manager."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    # ==================== Data Operations ====================
    
    def insert_data_points(self, df: pd.DataFrame, pipeline_run_id: Optional[str] = None) -> int:
        """Insert data points from DataFrame into database.
        
        Args:
            df: DataFrame with columns: series_id, date, value, source, connector
            pipeline_run_id: Optional pipeline run identifier
            
        Returns:
            Number of rows inserted
        """
        if df.empty:
            return 0
        
        # Ensure required columns exist
        required_cols = ['series_id', 'date', 'value', 'source']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"DataFrame must contain columns: {required_cols}")
        
        # Add connector if not present
        if 'connector' not in df.columns:
            df['connector'] = df['source'].str.lower()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Prepare extra data columns
            standard_cols = {'series_id', 'date', 'value', 'source', 'connector', 'metadata_id'}
            extra_cols = set(df.columns) - standard_cols
            
            inserted = 0
            for _, row in df.iterrows():
                # Collect extra data
                extra_data = {col: row[col] for col in extra_cols if col in row.index and pd.notna(row[col])}
                extra_json = json.dumps(extra_data) if extra_data else None
                
                metadata_id = row.get('metadata_id', None) if 'metadata_id' in row.index else None
                
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO data_points 
                        (series_id, date, value, source, connector, pipeline_run_id, metadata_id, extra_data_json)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        row['series_id'],
                        row['date'],
                        float(row['value']),
                        row['source'],
                        row['connector'],
                        pipeline_run_id,
                        metadata_id,
                        extra_json
                    ))
                    inserted += 1
                    
                    # Update or create series metadata
                    self._upsert_series(cursor, row['series_id'], row['source'], row['connector'])
                    
                except sqlite3.Error as e:
                    print(f"Error inserting data point: {e}")
                    continue
            
            conn.commit()
            return inserted
    
    def _upsert_series(self, cursor, series_id: str, source: str, connector: str):
        """Update or insert series metadata."""
        cursor.execute("""
            INSERT INTO series (series_id, source, connector)
            VALUES (?, ?, ?)
            ON CONFLICT(series_id) DO UPDATE SET
                updated_at = CURRENT_TIMESTAMP
        """, (series_id, source, connector))
        
        # Update series statistics
        cursor.execute("""
            UPDATE series SET
                first_date = (SELECT MIN(date) FROM data_points WHERE series_id = ?),
                last_date = (SELECT MAX(date) FROM data_points WHERE series_id = ?),
                data_points_count = (SELECT COUNT(*) FROM data_points WHERE series_id = ?)
            WHERE series_id = ?
        """, (series_id, series_id, series_id, series_id))
    
    def get_data_points(self, 
                       series_id: Optional[str] = None,
                       source: Optional[str] = None,
                       start_date: Optional[str] = None,
                       end_date: Optional[str] = None,
                       limit: Optional[int] = None) -> pd.DataFrame:
        """Retrieve data points from database.
        
        Args:
            series_id: Filter by series ID
            source: Filter by source
            start_date: Filter by start date (inclusive)
            end_date: Filter by end date (inclusive)
            limit: Maximum number of rows to return
            
        Returns:
            DataFrame with data points
        """
        query = "SELECT * FROM data_points WHERE 1=1"
        params = []
        
        if series_id:
            query += " AND series_id = ?"
            params.append(series_id)
        
        if source:
            query += " AND source = ?"
            params.append(source)
        
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        
        query += " ORDER BY date DESC"
        
        if limit:
            query += f" LIMIT {limit}"
        
        with self.get_connection() as conn:
            df = pd.read_sql_query(query, conn, params=params)
            
            # Parse extra_data_json if present
            if 'extra_data_json' in df.columns and not df.empty:
                for idx, row in df.iterrows():
                    if row['extra_data_json']:
                        try:
                            extra_data = json.loads(row['extra_data_json'])
                            for key, value in extra_data.items():
                                df.at[idx, key] = value
                        except:
                            pass
            
            return df
    
    # ==================== Pipeline Operations ====================
    
    def start_pipeline_run(self, connectors: List[str]) -> str:
        """Start a new pipeline run and return run_id."""
        run_id = f"run_{int(datetime.now().timestamp())}"
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO pipeline_runs (run_id, start_time, status, connectors_attempted)
                VALUES (?, ?, ?, ?)
            """, (run_id, datetime.now().isoformat(), 'running', json.dumps(connectors)))
            conn.commit()
        
        return run_id
    
    def finish_pipeline_run(self,
                           run_id: str,
                           status: str,
                           connectors_succeeded: List[str],
                           connectors_failed: List[str],
                           data_points: int,
                           errors: List[str],
                           output_dir: str):
        """Mark pipeline run as complete."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get start time
            cursor.execute("SELECT start_time FROM pipeline_runs WHERE run_id = ?", (run_id,))
            row = cursor.fetchone()
            if row:
                start_time = datetime.fromisoformat(row['start_time'])
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                cursor.execute("""
                    UPDATE pipeline_runs SET
                        end_time = ?,
                        status = ?,
                        duration_seconds = ?,
                        connectors_succeeded = ?,
                        connectors_failed = ?,
                        data_points_collected = ?,
                        errors_json = ?,
                        output_dir = ?
                    WHERE run_id = ?
                """, (
                    end_time.isoformat(),
                    status,
                    duration,
                    json.dumps(connectors_succeeded),
                    json.dumps(connectors_failed),
                    data_points,
                    json.dumps(errors),
                    output_dir,
                    run_id
                ))
                conn.commit()
    
    # ==================== Analytics Operations ====================
    
    def insert_anomalies(self, anomalies: List[Dict[str, Any]], pipeline_run_id: Optional[str] = None):
        """Insert detected anomalies."""
        if not anomalies:
            return
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            for anomaly in anomalies:
                cursor.execute("""
                    INSERT INTO analytics_anomalies 
                    (series_id, date, value, z_score, source, pipeline_run_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    anomaly.get('series_id'),
                    anomaly.get('date'),
                    anomaly.get('value'),
                    anomaly.get('z_score'),
                    anomaly.get('source'),
                    pipeline_run_id
                ))
            
            conn.commit()
    
    def insert_trends(self, trends: List[Dict[str, Any]], pipeline_run_id: Optional[str] = None):
        """Insert trend analysis results."""
        if not trends:
            return
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            for trend in trends:
                cursor.execute("""
                    INSERT INTO analytics_trends
                    (series_id, slope, trend_strength, direction, r_squared, pipeline_run_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    trend.get('series_id'),
                    trend.get('slope'),
                    trend.get('trend_strength'),
                    'up' if trend.get('slope', 0) > 0 else 'down',
                    trend.get('r_squared'),
                    pipeline_run_id
                ))
            
            conn.commit()
    
    def insert_correlations(self, correlations: List[Dict[str, Any]], pipeline_run_id: Optional[str] = None):
        """Insert correlation analysis results."""
        if not correlations:
            return
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            for corr in correlations:
                cursor.execute("""
                    INSERT INTO analytics_correlations
                    (series1_id, series2_id, correlation_coefficient, correlation_type, p_value, pipeline_run_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    corr.get('series1_id'),
                    corr.get('series2_id'),
                    corr.get('correlation_coefficient'),
                    corr.get('correlation_type'),
                    corr.get('p_value'),
                    pipeline_run_id
                ))
            
            conn.commit()
    
    def insert_changepoints(self, changepoints: List[Dict[str, Any]], pipeline_run_id: Optional[str] = None):
        """Insert changepoint detection results."""
        if not changepoints:
            return
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            for cp in changepoints:
                cursor.execute("""
                    INSERT INTO analytics_changepoints
                    (series_id, timestamp, change_type, magnitude, confidence, pipeline_run_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    cp.get('series_id'),
                    cp.get('timestamp'),
                    cp.get('change_type'),
                    cp.get('magnitude'),
                    cp.get('confidence'),
                    pipeline_run_id
                ))
            
            conn.commit()
    
    # ==================== Query Operations ====================
    
    def get_all_sources(self) -> List[str]:
        """Get list of all data sources."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT source FROM series ORDER BY source")
            return [row['source'] for row in cursor.fetchall()]
    
    def get_series_by_source(self, source: str) -> List[str]:
        """Get all series IDs for a given source."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT series_id FROM series WHERE source = ? ORDER BY series_id", (source,))
            return [row['series_id'] for row in cursor.fetchall()]
    
    def get_latest_values(self, source: Optional[str] = None) -> pd.DataFrame:
        """Get latest value for each series."""
        query = """
            SELECT dp.*
            FROM data_points dp
            INNER JOIN (
                SELECT series_id, MAX(date) as max_date
                FROM data_points
                GROUP BY series_id
            ) latest ON dp.series_id = latest.series_id AND dp.date = latest.max_date
        """
        
        params = []
        if source:
            query += " WHERE dp.source = ?"
            params.append(source)
        
        query += " ORDER BY dp.series_id"
        
        with self.get_connection() as conn:
            return pd.read_sql_query(query, conn, params=params)
    
    def export_to_csv(self, output_dir: Path, date_str: str):
        """Export database contents to CSV files for compatibility.
        
        Args:
            output_dir: Directory to write CSV files
            date_str: Date string for organizing output
        """
        date_dir = output_dir / date_str
        date_dir.mkdir(parents=True, exist_ok=True)
        
        # Export data by source
        sources = self.get_all_sources()
        for source in sources:
            df = self.get_data_points(source=source)
            if not df.empty:
                csv_path = date_dir / f"{source.lower()}.csv"
                df.to_csv(csv_path, index=False)
                print(f"Exported {len(df)} rows to {csv_path}")
    
    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
