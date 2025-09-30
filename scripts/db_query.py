"""Utility script for querying the WeQuo database."""
from __future__ import annotations
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import argparse
import pandas as pd
from wequo.database import WeQuoDB


def main():
    parser = argparse.ArgumentParser(description="Query WeQuo SQLite database")
    parser.add_argument(
        "--db",
        type=str,
        default="data/wequo.db",
        help="Path to SQLite database file (default: data/wequo.db)"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # List sources command
    subparsers.add_parser("sources", help="List all data sources")
    
    # List series command
    series_parser = subparsers.add_parser("series", help="List series for a source")
    series_parser.add_argument("source", type=str, help="Source name (e.g., FRED)")
    
    # Query data command
    query_parser = subparsers.add_parser("query", help="Query data points")
    query_parser.add_argument("--series", type=str, help="Series ID")
    query_parser.add_argument("--source", type=str, help="Source name")
    query_parser.add_argument("--start-date", type=str, help="Start date (YYYY-MM-DD)")
    query_parser.add_argument("--end-date", type=str, help="End date (YYYY-MM-DD)")
    query_parser.add_argument("--limit", type=int, default=100, help="Max rows to return")
    query_parser.add_argument("--output", type=str, help="Output CSV file path")
    
    # Latest values command
    latest_parser = subparsers.add_parser("latest", help="Get latest values for all series")
    latest_parser.add_argument("--source", type=str, help="Filter by source")
    latest_parser.add_argument("--output", type=str, help="Output CSV file path")
    
    # Pipeline runs command
    runs_parser = subparsers.add_parser("runs", help="List recent pipeline runs")
    runs_parser.add_argument("--limit", type=int, default=10, help="Number of runs to show")
    
    # Analytics command
    analytics_parser = subparsers.add_parser("analytics", help="Query analytics results")
    analytics_parser.add_argument(
        "type",
        choices=["anomalies", "trends", "correlations", "changepoints"],
        help="Type of analytics to query"
    )
    analytics_parser.add_argument("--limit", type=int, default=20, help="Max rows to return")
    analytics_parser.add_argument("--output", type=str, help="Output CSV file path")
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export data to CSV files")
    export_parser.add_argument("date", type=str, help="Date for output directory (YYYY-MM-DD)")
    export_parser.add_argument("--output-dir", type=str, default="data/output", help="Output directory")
    
    # Stats command
    subparsers.add_parser("stats", help="Show database statistics")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Initialize database
    db = WeQuoDB(args.db)
    print(f"Connected to database: {args.db}\n")
    
    try:
        if args.command == "sources":
            sources = db.get_all_sources()
            print("Available sources:")
            for source in sources:
                print(f"  - {source}")
        
        elif args.command == "series":
            series_list = db.get_series_by_source(args.source)
            print(f"Series for {args.source}:")
            for series in series_list:
                print(f"  - {series}")
        
        elif args.command == "query":
            df = db.get_data_points(
                series_id=args.series,
                source=args.source,
                start_date=args.start_date,
                end_date=args.end_date,
                limit=args.limit
            )
            
            if df.empty:
                print("No data found")
            else:
                print(f"Found {len(df)} data points:")
                print(df[['date', 'series_id', 'value', 'source']].to_string())
                
                if args.output:
                    df.to_csv(args.output, index=False)
                    print(f"\nSaved to: {args.output}")
        
        elif args.command == "latest":
            df = db.get_latest_values(source=args.source)
            
            if df.empty:
                print("No data found")
            else:
                print(f"Latest values for {len(df)} series:")
                print(df[['series_id', 'date', 'value', 'source']].to_string())
                
                if args.output:
                    df.to_csv(args.output, index=False)
                    print(f"\nSaved to: {args.output}")
        
        elif args.command == "runs":
            query = f"""
                SELECT run_id, start_time, status, duration_seconds, 
                       data_points_collected, connectors_succeeded
                FROM pipeline_runs
                ORDER BY start_time DESC
                LIMIT {args.limit}
            """
            
            with db.get_connection() as conn:
                df = pd.read_sql_query(query, conn)
            
            if df.empty:
                print("No pipeline runs found")
            else:
                print(f"Recent pipeline runs:")
                print(df.to_string())
        
        elif args.command == "analytics":
            table_map = {
                "anomalies": "analytics_anomalies",
                "trends": "analytics_trends",
                "correlations": "analytics_correlations",
                "changepoints": "analytics_changepoints"
            }
            
            table = table_map[args.type]
            query = f"SELECT * FROM {table} ORDER BY created_at DESC LIMIT {args.limit}"
            
            with db.get_connection() as conn:
                df = pd.read_sql_query(query, conn)
            
            if df.empty:
                print(f"No {args.type} found")
            else:
                print(f"Latest {args.type}:")
                print(df.to_string())
                
                if args.output:
                    df.to_csv(args.output, index=False)
                    print(f"\nSaved to: {args.output}")
        
        elif args.command == "export":
            output_dir = Path(args.output_dir)
            db.export_to_csv(output_dir, args.date)
            print(f"Exported data to {output_dir / args.date}")
        
        elif args.command == "stats":
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Count data points
                cursor.execute("SELECT COUNT(*) FROM data_points")
                data_points = cursor.fetchone()[0]
                
                # Count series
                cursor.execute("SELECT COUNT(*) FROM series")
                series_count = cursor.fetchone()[0]
                
                # Count sources
                cursor.execute("SELECT COUNT(DISTINCT source) FROM series")
                sources_count = cursor.fetchone()[0]
                
                # Count pipeline runs
                cursor.execute("SELECT COUNT(*) FROM pipeline_runs")
                runs_count = cursor.fetchone()[0]
                
                # Count analytics
                cursor.execute("SELECT COUNT(*) FROM analytics_anomalies")
                anomalies = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM analytics_trends")
                trends = cursor.fetchone()[0]
                
                # Latest run
                cursor.execute("""
                    SELECT run_id, start_time, status 
                    FROM pipeline_runs 
                    ORDER BY start_time DESC 
                    LIMIT 1
                """)
                latest_run = cursor.fetchone()
                
                print("Database Statistics:")
                print(f"  Total data points: {data_points:,}")
                print(f"  Total series: {series_count:,}")
                print(f"  Total sources: {sources_count}")
                print(f"  Pipeline runs: {runs_count}")
                print(f"  Anomalies detected: {anomalies:,}")
                print(f"  Trends identified: {trends:,}")
                
                if latest_run:
                    print(f"\nLatest pipeline run:")
                    print(f"  Run ID: {latest_run['run_id']}")
                    print(f"  Time: {latest_run['start_time']}")
                    print(f"  Status: {latest_run['status']}")
    
    finally:
        db.close()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
