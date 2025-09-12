"""
Enhanced FRED connector with retry logic, structured logging, and error handling.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional
import time

import pandas as pd
import requests

from ..utils.retry import retry_manager
from ..utils.logging import get_logger, LogContext, log_operation


FRED_API = "https://api.stlouisfed.org/fred/series/observations"


@dataclass
class FredConnectorEnhanced:
    """Enhanced FRED connector with robust error handling and monitoring."""
    
    series_ids: List[str]
    api_key: str
    lookback_start: Optional[str] = None
    lookback_end: Optional[str] = None
    name: str = "fred"
    
    def __post_init__(self):
        self.logger = get_logger("wequo.connectors.fred")
        self.retry_manager = retry_manager
    
    @retry_manager.retry_api_call
    def _fetch_series(self, series_id: str, context: Optional[LogContext] = None) -> pd.DataFrame:
        """Fetch data for a single FRED series with retry logic."""
        if context is None:
            context = LogContext(
                operation="fetch_series",
                component="fred_connector",
                connector_name="fred",
                data_source=series_id
            )
        
        self.logger.info(f"Fetching FRED series: {series_id}", context=context)
        
        params = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json",
        }
        
        if self.lookback_start:
            params["observation_start"] = self.lookback_start
        if self.lookback_end:
            params["observation_end"] = self.lookback_end
        
        try:
            response = requests.get(FRED_API, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            observations = data.get("observations", [])
            
            if not observations:
                self.logger.warning(f"No observations found for series {series_id}", context=context)
                return pd.DataFrame()
            
            df = pd.DataFrame(observations)
            df["series_id"] = series_id
            
            # Log success metrics
            context.record_count = len(df)
            self.logger.info(f"Successfully fetched {len(df)} observations for {series_id}", context=context)
            
            return df
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400:
                self.logger.error(f"Invalid request for series {series_id}: {e}", context=context)
                raise ValueError(f"Invalid FRED series ID or parameters: {series_id}")
            elif e.response.status_code == 429:
                self.logger.warning(f"Rate limited for series {series_id}, will retry", context=context)
                raise
            else:
                self.logger.error(f"HTTP error fetching series {series_id}: {e}", context=context)
                raise
        except requests.exceptions.Timeout:
            self.logger.error(f"Timeout fetching series {series_id}", context=context)
            raise
        except requests.exceptions.ConnectionError:
            self.logger.error(f"Connection error fetching series {series_id}", context=context)
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error fetching series {series_id}: {e}", context=context)
            raise
    
    @log_operation("fetch_all_series", "fred_connector")
    def fetch(self, pipeline_run_id: Optional[str] = None) -> pd.DataFrame:
        """Fetch data for all configured FRED series."""
        context = LogContext(
            operation="fetch_all_series",
            component="fred_connector",
            connector_name="fred",
            pipeline_run_id=pipeline_run_id
        )
        
        self.logger.info(f"Starting FRED data fetch for {len(self.series_ids)} series", context=context)
        
        if not self.series_ids:
            self.logger.warning("No FRED series IDs configured", context=context)
            return pd.DataFrame()
        
        if not self.api_key:
            self.logger.error("FRED API key not provided", context=context)
            raise ValueError("FRED API key is required")
        
        frames = []
        successful_series = []
        failed_series = []
        
        for series_id in self.series_ids:
            try:
                series_context = LogContext(
                    operation="fetch_series",
                    component="fred_connector",
                    connector_name="fred",
                    data_source=series_id,
                    pipeline_run_id=pipeline_run_id
                )
                
                df = self._fetch_series(series_id, series_context)
                if not df.empty:
                    frames.append(df)
                    successful_series.append(series_id)
                else:
                    failed_series.append(series_id)
                    
            except Exception as e:
                self.logger.error(f"Failed to fetch series {series_id}: {e}", context=context)
                failed_series.append(series_id)
        
        # Combine all successful fetches
        if frames:
            combined_df = pd.concat(frames, ignore_index=True)
            context.record_count = len(combined_df)
            
            self.logger.info(
                f"FRED fetch completed: {len(successful_series)} successful, {len(failed_series)} failed",
                context=context,
                successful_series=successful_series,
                failed_series=failed_series
            )
            
            return combined_df
        else:
            self.logger.error("No FRED data was successfully fetched", context=context)
            return pd.DataFrame()
    
    def normalize(self, df: pd.DataFrame, pipeline_run_id: Optional[str] = None) -> pd.DataFrame:
        """Normalize FRED data to standard format."""
        context = LogContext(
            operation="normalize_data",
            component="fred_connector",
            connector_name="fred",
            pipeline_run_id=pipeline_run_id
        )
        
        if df.empty:
            self.logger.warning("No data to normalize", context=context)
            return pd.DataFrame()
        
        try:
            # Normalize the data
            normalized_df = (
                df.rename(columns={"date": "date", "value": "value"})
                [["series_id", "date", "value"]]
                .assign(source="FRED")
                .dropna(subset=["value"])
                .copy()
            )
            
            # Convert value to numeric, handling FRED's "." for missing values
            normalized_df["value"] = pd.to_numeric(normalized_df["value"], errors="coerce")
            normalized_df = normalized_df.dropna(subset=["value"])
            
            # Convert date to datetime
            normalized_df["date"] = pd.to_datetime(normalized_df["date"])
            
            context.record_count = len(normalized_df)
            self.logger.info(f"Normalized {len(normalized_df)} FRED records", context=context)
            
            return normalized_df
            
        except Exception as e:
            self.logger.error(f"Error normalizing FRED data: {e}", context=context)
            raise
    
    def get_health_status(self) -> dict:
        """Get health status of the FRED connector."""
        try:
            # Test API connectivity
            test_params = {
                "series_id": "GDP",  # Use a known series for testing
                "api_key": self.api_key,
                "file_type": "json",
                "limit": 1
            }
            
            response = requests.get(FRED_API, params=test_params, timeout=10)
            
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "api_accessible": True,
                    "series_count": len(self.series_ids),
                    "circuit_breaker_status": self.retry_manager.get_circuit_breaker_status().get("api_calls", {})
                }
            elif response.status_code == 400:
                return {
                    "status": "healthy",
                    "api_accessible": True,
                    "note": "API accessible but test series not available",
                    "series_count": len(self.series_ids)
                }
            else:
                return {
                    "status": "degraded",
                    "api_accessible": False,
                    "http_status": response.status_code,
                    "series_count": len(self.series_ids)
                }
                
        except Exception as e:
            return {
                "status": "unhealthy",
                "api_accessible": False,
                "error": str(e),
                "series_count": len(self.series_ids)
            }
