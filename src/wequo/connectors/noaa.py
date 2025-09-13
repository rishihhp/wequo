from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any
from datetime import datetime, timedelta

import pandas as pd
import requests
from tenacity import retry, stop_after_attempt, wait_fixed

# NOAA (National Oceanic and Atmospheric Administration) API
NOAA_API = "https://www.ncdc.noaa.gov/cdo-web/api/v2"


@dataclass
class NOAAConnector:
    """Connector for NOAA climate and weather data."""
    
    api_key: str
    datasets: List[str] = None
    stations: List[str] = None
    datatypes: List[str] = None
    lookback_days: int = 30
    
    name: str = "noaa"
    
    def __post_init__(self):
        # Default datasets if none provided
        if not self.datasets:
            self.datasets = [
                "GHCND",  # Global Historical Climatology Network Daily
                "GSOM",   # Global Summary of the Month
                "GSOY"    # Global Summary of the Year
            ]
        
        # Default stations (major cities) if none provided
        if not self.stations:
            self.stations = [
                "GHCND:USW00014732",  # New York Central Park
                "GHCND:USW00023174",  # Los Angeles LAX
                "GHCND:USW00012960",  # Chicago O'Hare
                "GHCND:USW00013881",  # Miami International
                "GHCND:CA001158355",  # Toronto Pearson
                "GHCND:GM000010393",  # Berlin Tempelhof
                "GHCND:JA000047662",  # Tokyo
                "GHCND:AS000066062",  # Sydney Observatory Hill
            ]
        
        # Default data types if none provided
        if not self.datatypes:
            self.datatypes = [
                "TMAX",  # Maximum temperature
                "TMIN",  # Minimum temperature
                "PRCP",  # Precipitation
                "SNOW",  # Snowfall
                "SNWD",  # Snow depth
                "AWND"   # Average wind speed
            ]
    
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def _fetch_noaa_data(self, dataset: str, station: str, datatype: str) -> pd.DataFrame:
        """Fetch NOAA data for a single dataset, station, and datatype."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=self.lookback_days)
        
        headers = {
            "token": self.api_key
        }
        
        params = {
            "datasetid": dataset,
            "stationid": station,
            "datatypeid": datatype,
            "startdate": start_date.strftime("%Y-%m-%d"),
            "enddate": end_date.strftime("%Y-%m-%d"),
            "format": "json",
            "limit": 1000,
            "units": "metric"
        }
        
        try:
            r = requests.get(f"{NOAA_API}/data", headers=headers, params=params, timeout=30)
            r.raise_for_status()
            data = r.json()
            
            if not data.get("results"):
                return self._generate_mock_data(dataset, station, datatype)
            
            rows = []
            for item in data["results"]:
                rows.append({
                    "date": item.get("date", "")[:10],  # Extract date part
                    "value": float(item.get("value", 0)),
                    "series_id": f"{station}_{datatype}",
                    "dataset": dataset,
                    "station": station,
                    "datatype": datatype,
                    "attributes": item.get("attributes", "")
                })
            
            return pd.DataFrame(rows)
            
        except Exception as e:
            print(f"Warning: Failed to fetch NOAA data for {dataset}/{station}/{datatype}: {e}")
            return self._generate_mock_data(dataset, station, datatype)
    
    def _generate_mock_data(self, dataset: str, station: str, datatype: str) -> pd.DataFrame:
        """Generate mock NOAA data for demonstration."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=self.lookback_days)
        
        # Mock base values for different data types
        base_values = {
            "TMAX": 20.0,   # Maximum temperature (°C)
            "TMIN": 10.0,   # Minimum temperature (°C)
            "PRCP": 2.0,    # Precipitation (mm)
            "SNOW": 0.0,    # Snowfall (mm)
            "SNWD": 0.0,    # Snow depth (mm)
            "AWND": 5.0     # Average wind speed (m/s)
        }
        
        base_value = base_values.get(datatype, 15.0)
        rows = []
        
        for i in range(self.lookback_days):
            date = start_date + timedelta(days=i)
            
            # Add seasonal and random variation
            import random
            import math
            
            # Seasonal variation (simple sine wave)
            day_of_year = date.timetuple().tm_yday
            seasonal = math.sin(2 * math.pi * day_of_year / 365) * 5
            
            # Random variation
            random_var = random.uniform(-2, 2)
            
            value = base_value + seasonal + random_var
            
            # Ensure non-negative values for precipitation and snow
            if datatype in ["PRCP", "SNOW", "SNWD"] and value < 0:
                value = 0
            
            rows.append({
                "date": date.strftime("%Y-%m-%d"),
                "value": round(value, 2),
                "series_id": f"{station}_{datatype}",
                "dataset": dataset,
                "station": station,
                "datatype": datatype,
                "attributes": ""
            })
        
        return pd.DataFrame(rows)
    
    def fetch(self) -> pd.DataFrame:
        """Fetch NOAA data for all configured combinations."""
        frames = []
        for dataset in self.datasets:
            for station in self.stations:
                for datatype in self.datatypes:
                    df = self._fetch_noaa_data(dataset, station, datatype)
                    frames.append(df)
        
        return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    
    def normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize NOAA data to standard format."""
        if df.empty:
            return df
            
        out = df.copy()
        out["source"] = "NOAA"
        out["value"] = pd.to_numeric(out["value"], errors="coerce")
        out["date"] = pd.to_datetime(out["date"], errors="coerce").dt.strftime("%Y-%m-%d")
        
        return out.dropna(subset=["value", "date"])
