from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime
import uuid
import pandas as pd


@dataclass
class DataPointMetadata:
    """Metadata for a single data point with comprehensive provenance tracking."""
    
    # Core identification
    id: str
    series_id: str
    source: str
    
    # Temporal information
    date: str
    timestamp: str  # When the data was fetched
    
    # Data provenance (Phase 1 requirement)
    api_endpoint: Optional[str] = None
    source_url: Optional[str] = None  # Direct link to source data
    raw_response_hash: Optional[str] = None
    fetch_duration_ms: Optional[int] = None
    
    # Enhanced provenance tracking
    api_version: Optional[str] = None
    request_parameters: Optional[Dict[str, Any]] = None
    response_headers: Optional[Dict[str, str]] = None
    data_transformation_log: Optional[List[str]] = None
    
    # Data quality and validation
    confidence_score: Optional[float] = None
    validation_status: str = "unknown"
    quality_checks_passed: Optional[List[str]] = None
    quality_checks_failed: Optional[List[str]] = None
    
    # Processing information
    processing_version: str = "1.0"
    connector_version: str = "1.0"
    pipeline_run_id: Optional[str] = None
    
    # Licensing and terms
    data_license: Optional[str] = None
    terms_of_service_url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "series_id": self.series_id,
            "source": self.source,
            "date": self.date,
            "timestamp": self.timestamp,
            # Provenance information
            "api_endpoint": self.api_endpoint,
            "source_url": self.source_url,
            "raw_response_hash": self.raw_response_hash,
            "fetch_duration_ms": self.fetch_duration_ms,
            "api_version": self.api_version,
            "request_parameters": self.request_parameters,
            "response_headers": self.response_headers,
            "data_transformation_log": self.data_transformation_log,
            # Quality information
            "confidence_score": self.confidence_score,
            "validation_status": self.validation_status,
            "quality_checks_passed": self.quality_checks_passed,
            "quality_checks_failed": self.quality_checks_failed,
            # Processing information
            "processing_version": self.processing_version,
            "connector_version": self.connector_version,
            "pipeline_run_id": self.pipeline_run_id,
            # Licensing
            "data_license": self.data_license,
            "terms_of_service_url": self.terms_of_service_url,
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
                       source_url: Optional[str] = None,
                       fetch_duration_ms: Optional[int] = None,
                       confidence_score: Optional[float] = None,
                       api_version: Optional[str] = None,
                       request_parameters: Optional[Dict[str, Any]] = None,
                       response_headers: Optional[Dict[str, str]] = None,
                       data_transformation_log: Optional[List[str]] = None,
                       pipeline_run_id: Optional[str] = None,
                       data_license: Optional[str] = None,
                       terms_of_service_url: Optional[str] = None) -> DataPointMetadata:
        """Create metadata for a data point."""
        
        metadata = DataPointMetadata(
            id=str(uuid.uuid4()),
            series_id=series_id,
            source=source,
            date=date,
            timestamp=datetime.now().isoformat(),
            api_endpoint=api_endpoint,
            source_url=source_url,
            fetch_duration_ms=fetch_duration_ms,
            confidence_score=confidence_score,
            api_version=api_version,
            request_parameters=request_parameters,
            response_headers=response_headers,
            data_transformation_log=data_transformation_log or [],
            pipeline_run_id=pipeline_run_id,
            data_license=data_license,
            terms_of_service_url=terms_of_service_url,
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
    
    def create_metadata_from_api_response(self,
                                        series_id: str,
                                        source: str,
                                        date: str,
                                        api_response,
                                        request_url: str,
                                        request_params: Dict[str, Any],
                                        fetch_start_time: datetime,
                                        pipeline_run_id: Optional[str] = None) -> DataPointMetadata:
        """Create metadata from API response with full provenance tracking."""
        import hashlib
        
        fetch_duration = int((datetime.now() - fetch_start_time).total_seconds() * 1000)
        
        # Generate response hash for integrity checking
        response_text = str(api_response) if hasattr(api_response, '__str__') else ""
        response_hash = hashlib.md5(response_text.encode()).hexdigest()
        
        # Extract response headers if available
        response_headers = None
        if hasattr(api_response, 'headers'):
            response_headers = dict(api_response.headers)
        
        # Create transformation log
        transformation_log = [
            f"Raw API response received at {datetime.now().isoformat()}",
            f"Response size: {len(response_text)} characters",
            "Data normalization applied"
        ]
        
        return self.create_metadata(
            series_id=series_id,
            source=source,
            date=date,
            api_endpoint=request_url,
            source_url=request_url,
            fetch_duration_ms=fetch_duration,
            confidence_score=1.0,  # Default high confidence for successful API calls
            request_parameters=request_params,
            response_headers=response_headers,
            data_transformation_log=transformation_log,
            pipeline_run_id=pipeline_run_id,
            raw_response_hash=response_hash
        )


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
