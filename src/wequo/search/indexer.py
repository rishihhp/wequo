"""
Data indexer for WeQuo search functionality.
"""

import json
import os
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd

from .models import IndexDocument, DocumentType, SearchStats


class DataIndexer:
    """Indexes WeQuo data packages for search."""
    
    def __init__(self, index_dir: str = "data/search"):
        """Initialize indexer with storage directory."""
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.documents_file = self.index_dir / "documents.jsonl"
        self.stats_file = self.index_dir / "stats.json"
    
    def index_package(self, package_dir: Path) -> List[IndexDocument]:
        """Index a complete data package."""
        documents = []
        package_date = package_dir.name
        
        # Index package summary
        summary_file = package_dir / "package_summary.json"
        if summary_file.exists():
            summary_doc = self._index_package_summary(summary_file, package_date)
            if summary_doc:
                documents.append(summary_doc)
        
        # Index CSV data files
        for csv_file in package_dir.glob("*.csv"):
            csv_docs = self._index_csv_file(csv_file, package_date)
            documents.extend(csv_docs)
        
        # Index reports
        for md_file in package_dir.glob("*.md"):
            report_doc = self._index_report(md_file, package_date)
            if report_doc:
                documents.append(report_doc)
        
        # Index analytics if available
        analytics_file = package_dir / "analytics_summary.json"
        if analytics_file.exists():
            analytics_docs = self._index_analytics(analytics_file, package_date)
            documents.extend(analytics_docs)
        
        # Store documents
        for doc in documents:
            self._store_document(doc)
        
        return documents
    
    def _index_package_summary(self, summary_file: Path, package_date: str) -> Optional[IndexDocument]:
        """Index package summary."""
        try:
            with open(summary_file, 'r') as f:
                summary = json.load(f)
            
            content = f"""Package for {package_date}
Sources: {', '.join(summary.get('sources', []))}
Generated: {summary.get('timestamp', 'Unknown')}
Total data points: {len(summary.get('latest_values', {}))}
"""
            
            # Add latest values summary
            for source, values in summary.get('latest_values', {}).items():
                content += f"\n{source.upper()}: {len(values)} data points"
                for value in values[:3]:  # Include first 3 values
                    content += f"\n  - {value.get('series_id', 'N/A')}: {value.get('value', 'N/A')}"
            
            doc_id = f"package_{package_date}"
            return IndexDocument(
                id=doc_id,
                type=DocumentType.PACKAGE,
                title=f"Data Package - {package_date}",
                content=content,
                metadata={
                    'package_date': package_date,
                    'sources': summary.get('sources', []),
                    'data_points': len(summary.get('latest_values', {}))
                },
                tags=['package', 'summary'] + summary.get('sources', []),
                source='package'
            )
        except Exception as e:
            print(f"Error indexing package summary {summary_file}: {e}")
            return None
    
    def _index_csv_file(self, csv_file: Path, package_date: str) -> List[IndexDocument]:
        """Index CSV data file."""
        documents = []
        source = csv_file.stem
        
        try:
            df = pd.read_csv(csv_file)
            
            # Create document for the dataset
            content = f"""Dataset: {source.upper()}
Date: {package_date}
Rows: {len(df)}
Columns: {', '.join(df.columns)}

Sample data:
"""
            # Add sample rows
            for idx, row in df.head(5).iterrows():
                content += f"Row {idx + 1}: " + ", ".join([f"{col}={val}" for col, val in row.items()]) + "\n"
            
            doc_id = f"dataset_{source}_{package_date}"
            dataset_doc = IndexDocument(
                id=doc_id,
                type=DocumentType.DATA_POINT,
                title=f"{source.upper()} Dataset - {package_date}",
                content=content,
                metadata={
                    'package_date': package_date,
                    'source': source,
                    'rows': len(df),
                    'columns': list(df.columns)
                },
                tags=['dataset', source],
                source=source
            )
            documents.append(dataset_doc)
            
            # Index individual data points for time series data
            if 'date' in df.columns and 'value' in df.columns:
                for idx, row in df.iterrows():
                    if idx >= 100:  # Limit to avoid too many documents
                        break
                    
                    series_id = row.get('series_id', f"{source}_{idx}")
                    content = f"Data point: {series_id}\nDate: {row['date']}\nValue: {row['value']}"
                    if 'source' in row:
                        content += f"\nSource: {row['source']}"
                    
                    doc_id = f"datapoint_{source}_{package_date}_{idx}"
                    point_doc = IndexDocument(
                        id=doc_id,
                        type=DocumentType.DATA_POINT,
                        title=f"{series_id} - {row['date']}",
                        content=content,
                        metadata={
                            'package_date': package_date,
                            'source': source,
                            'series_id': series_id,
                            'date': str(row['date']),
                            'value': float(row['value']) if pd.notna(row['value']) else None
                        },
                        tags=['data_point', source, series_id],
                        source=source
                    )
                    documents.append(point_doc)
            
        except Exception as e:
            print(f"Error indexing CSV file {csv_file}: {e}")
        
        return documents
    
    def _index_report(self, report_file: Path, package_date: str) -> Optional[IndexDocument]:
        """Index markdown report."""
        try:
            content = report_file.read_text()
            report_type = report_file.stem
            
            doc_id = f"report_{report_type}_{package_date}"
            return IndexDocument(
                id=doc_id,
                type=DocumentType.REPORT,
                title=f"{report_type.replace('_', ' ').title()} - {package_date}",
                content=content,
                metadata={
                    'package_date': package_date,
                    'report_type': report_type,
                    'length': len(content)
                },
                tags=['report', report_type, package_date],
                source='report'
            )
        except Exception as e:
            print(f"Error indexing report {report_file}: {e}")
            return None
    
    def _index_analytics(self, analytics_file: Path, package_date: str) -> List[IndexDocument]:
        """Index analytics data."""
        documents = []
        
        try:
            with open(analytics_file, 'r') as f:
                analytics = json.load(f)
            
            # Index top deltas
            for i, delta in enumerate(analytics.get('top_deltas', [])):
                content = f"""Delta Analysis
Series: {delta.get('series_id', 'Unknown')}
Change: {delta.get('delta_pct', 0) * 100:.1f}%
Old Value: {delta.get('old_value', 'N/A')}
New Value: {delta.get('new_value', 'N/A')}
Date: {package_date}
"""
                
                doc_id = f"delta_{package_date}_{i}"
                delta_doc = IndexDocument(
                    id=doc_id,
                    type=DocumentType.ANALYTICS,
                    title=f"Delta: {delta.get('series_id', 'Unknown')} ({delta.get('delta_pct', 0) * 100:.1f}%)",
                    content=content,
                    metadata={
                        'package_date': package_date,
                        'analysis_type': 'delta',
                        'series_id': delta.get('series_id'),
                        'delta_pct': delta.get('delta_pct'),
                        'old_value': delta.get('old_value'),
                        'new_value': delta.get('new_value')
                    },
                    tags=['analytics', 'delta', delta.get('series_id', 'unknown')],
                    source='analytics'
                )
                documents.append(delta_doc)
            
            # Index anomalies
            for i, anomaly in enumerate(analytics.get('anomalies', [])):
                content = f"""Anomaly Detection
Series: {anomaly.get('series_id', 'Unknown')}
Value: {anomaly.get('value', 'N/A')}
Z-Score: {anomaly.get('z_score', 'N/A')}
Date: {anomaly.get('date', package_date)}
Type: {anomaly.get('anomaly_type', 'statistical')}
"""
                
                doc_id = f"anomaly_{package_date}_{i}"
                anomaly_doc = IndexDocument(
                    id=doc_id,
                    type=DocumentType.ANOMALY,
                    title=f"Anomaly: {anomaly.get('series_id', 'Unknown')} (z={anomaly.get('z_score', 'N/A')})",
                    content=content,
                    metadata={
                        'package_date': package_date,
                        'analysis_type': 'anomaly',
                        'series_id': anomaly.get('series_id'),
                        'value': anomaly.get('value'),
                        'z_score': anomaly.get('z_score'),
                        'anomaly_type': anomaly.get('anomaly_type')
                    },
                    tags=['analytics', 'anomaly', anomaly.get('series_id', 'unknown')],
                    source='analytics'
                )
                documents.append(anomaly_doc)
            
            # Index trends
            for i, trend in enumerate(analytics.get('trends', [])):
                content = f"""Trend Analysis
Series: {trend.get('series_id', 'Unknown')}
Direction: {trend.get('direction', 'Unknown')}
Strength: {trend.get('trend_strength', 'Unknown')}
Slope: {trend.get('slope', 'N/A')}
R-squared: {trend.get('r_squared', 'N/A')}
Date: {package_date}
"""
                
                doc_id = f"trend_{package_date}_{i}"
                trend_doc = IndexDocument(
                    id=doc_id,
                    type=DocumentType.TREND,
                    title=f"Trend: {trend.get('series_id', 'Unknown')} ({trend.get('trend_strength', 'unknown')} {trend.get('direction', '')})",
                    content=content,
                    metadata={
                        'package_date': package_date,
                        'analysis_type': 'trend',
                        'series_id': trend.get('series_id'),
                        'direction': trend.get('direction'),
                        'trend_strength': trend.get('trend_strength'),
                        'slope': trend.get('slope'),
                        'r_squared': trend.get('r_squared')
                    },
                    tags=['analytics', 'trend', trend.get('series_id', 'unknown'), trend.get('direction', 'unknown')],
                    source='analytics'
                )
                documents.append(trend_doc)
                
        except Exception as e:
            print(f"Error indexing analytics {analytics_file}: {e}")
        
        return documents
    
    def _store_document(self, document: IndexDocument):
        """Store document in the index."""
        with open(self.documents_file, 'a') as f:
            f.write(json.dumps(document.to_dict()) + '\n')
    
    def rebuild_index(self, output_root: Path):
        """Rebuild the entire search index."""
        print("🔄 Rebuilding search index...")
        
        # Clear existing index
        if self.documents_file.exists():
            self.documents_file.unlink()
        
        total_docs = 0
        
        # Index all packages
        for package_dir in sorted(output_root.iterdir()):
            if package_dir.is_dir():
                print(f"   Indexing package: {package_dir.name}")
                docs = self.index_package(package_dir)
                total_docs += len(docs)
        
        # Update statistics
        self._update_stats()
        
        print(f"✅ Index rebuilt with {total_docs} documents")
        return total_docs
    
    def _update_stats(self):
        """Update index statistics."""
        stats = SearchStats()
        
        if self.documents_file.exists():
            docs_by_type = {}
            sources = set()
            dates = []
            
            with open(self.documents_file, 'r') as f:
                for line in f:
                    doc_data = json.loads(line)
                    doc_type = doc_data['type']
                    docs_by_type[doc_type] = docs_by_type.get(doc_type, 0) + 1
                    stats.total_documents += 1
                    
                    if doc_data.get('source'):
                        sources.add(doc_data['source'])
                    
                    if 'package_date' in doc_data.get('metadata', {}):
                        dates.append(doc_data['metadata']['package_date'])
            
            stats.documents_by_type = docs_by_type
            stats.total_sources = len(sources)
            if dates:
                stats.date_range = (min(dates), max(dates))
            stats.last_updated = datetime.now()
            
            # Calculate file size
            if self.documents_file.exists():
                stats.index_size_mb = self.documents_file.stat().st_size / (1024 * 1024)
        
        # Save stats
        with open(self.stats_file, 'w') as f:
            json.dump(stats.to_dict(), f, indent=2)
    
    def get_stats(self) -> SearchStats:
        """Get current index statistics."""
        if self.stats_file.exists():
            with open(self.stats_file, 'r') as f:
                data = json.load(f)
                stats = SearchStats(**data)
                if data.get('last_updated'):
                    stats.last_updated = datetime.fromisoformat(data['last_updated'])
                return stats
        else:
            return SearchStats()
