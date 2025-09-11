from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime
import uuid
import pandas as pd


@dataclass
class DataPointMetadata:
    """Metadata for a single data point."""
    
    # Core identification
    id: str
    series_id: str
    source: str
    
    # Temporal information
    date: str
    timestamp: str  # When the data was fetched
    
    # Data provenance
    api_endpoint: Optional[str] = None
    raw_response_hash: Optional[str] = None
    fetch_duration_ms: Optional[int] = None
    
    # Data quality
    confidence_score: Optional[float] = None
    validation_status: str = "unknown"
    
    # Processing information
    processing_version: str = "1.0"
    connector_version: str = "1.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "series_id": self.series_id,
            "source": self.source,
            "date": self.date,
            "timestamp": self.timestamp,
            "api_endpoint": self.api_endpoint,
            "raw_response_hash": self.raw_response_hash,
            "fetch_duration_ms": self.fetch_duration_ms,
            "confidence_score": self.confidence_score,
            "validation_status": self.validation_status,
            "processing_version": self.processing_version,
            "connector_version": self.connector_version,
        }


class MetadataTracker:
    """Track metadata and provenance for all data points."""
    
    def __init__(self):
        self.metadata_store: Dict[str, DataPointMetadata] = {}
    
    def create_metadata(self, 
                       series_id: str,
                       source: str,
                       date: str,
                       api_endpoint: Optional[str] = None,
                       fetch_duration_ms: Optional[int] = None,
                       confidence_score: Optional[float] = None) -> DataPointMetadata:
        """Create metadata for a data point."""
        
        metadata = DataPointMetadata(
            id=str(uuid.uuid4()),
            series_id=series_id,
            source=source,
            date=date,
            timestamp=datetime.now().isoformat(),
            api_endpoint=api_endpoint,
            fetch_duration_ms=fetch_duration_ms,
            confidence_score=confidence_score,
            validation_status="pending"
        )
        
        # Store metadata
        self.metadata_store[metadata.id] = metadata
        
        return metadata
    
    def update_validation_status(self, metadata_id: str, status: str) -> None:
        """Update validation status for a data point."""
        if metadata_id in self.metadata_store:
            self.metadata_store[metadata_id].validation_status = status
    
    def get_metadata(self, metadata_id: str) -> Optional[DataPointMetadata]:
        """Get metadata by ID."""
        return self.metadata_store.get(metadata_id)
    
    def get_metadata_by_series(self, series_id: str) -> list[DataPointMetadata]:
        """Get all metadata for a specific series."""
        return [md for md in self.metadata_store.values() if md.series_id == series_id]
    
    def get_metadata_by_source(self, source: str) -> list[DataPointMetadata]:
        """Get all metadata for a specific source."""
        return [md for md in self.metadata_store.values() if md.source == source]
    
    def export_metadata(self) -> Dict[str, Any]:
        """Export all metadata for serialization."""
        return {
            "metadata": {k: v.to_dict() for k, v in self.metadata_store.items()},
            "summary": {
                "total_data_points": len(self.metadata_store),
                "sources": list(set(md.source for md in self.metadata_store.values())),
                "series_count": len(set(md.series_id for md in self.metadata_store.values())),
                "validation_status_counts": self._get_validation_status_counts()
            }
        }
    
    def _get_validation_status_counts(self) -> Dict[str, int]:
        """Get counts by validation status."""
        counts = {}
        for metadata in self.metadata_store.values():
            status = metadata.validation_status
            counts[status] = counts.get(status, 0) + 1
        return counts


def add_metadata_to_dataframe(df, metadata_tracker: MetadataTracker, source: str) -> pd.DataFrame:
    """Add metadata IDs to a DataFrame."""
    if df.empty:
        return df
    
    df_copy = df.copy()
    metadata_ids = []
    
    for _, row in df_copy.iterrows():
        # Create metadata for this row
        metadata = metadata_tracker.create_metadata(
            series_id=row.get("series_id", "unknown"),
            source=source,
            date=row.get("date", ""),
            confidence_score=1.0  # Default confidence
        )
        metadata_ids.append(metadata.id)
    
    df_copy["metadata_id"] = metadata_ids
    return df_copy


def calculate_data_quality_score(metadata: DataPointMetadata) -> float:
    """Calculate a data quality score for metadata."""
    score = 1.0
    
    # Reduce score for missing information
    if not metadata.api_endpoint:
        score -= 0.1
    
    if not metadata.raw_response_hash:
        score -= 0.1
    
    if metadata.fetch_duration_ms and metadata.fetch_duration_ms > 5000:  # > 5 seconds
        score -= 0.2
    
    if metadata.validation_status != "valid":
        score -= 0.3
    
    if metadata.confidence_score:
        score *= metadata.confidence_score
    
    return max(0.0, min(1.0, score))
