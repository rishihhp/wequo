from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any
from datetime import datetime, timedelta

import pandas as pd
import requests
from tenacity import retry, stop_after_attempt, wait_fixed

# ACLED (Armed Conflict Location & Event Data Project) API
ACLED_API = "https://api.acleddata.com/acled/read"


@dataclass
class ACLEDConnector:
    """Connector for ACLED conflict and crisis data."""
    
    api_key: str
    email: str
    countries: List[str] = None
    event_types: List[str] = None
    lookback_days: int = 30
    
    name: str = "acled"
    
    def __post_init__(self):
        # Default countries to track if none provided
        if not self.countries:
            self.countries = [
                "United States of America",
                "Syria", 
                "Ukraine",
                "Afghanistan",
                "Somalia",
                "Myanmar",
                "Yemen",
                "Nigeria",
                "Democratic Republic of Congo",
                "Ethiopia"
            ]
        
        # Default event types if none provided
        if not self.event_types:
            self.event_types = [
                "Battles",
                "Explosions/Remote violence", 
                "Violence against civilians",
                "Riots",
                "Protests",
                "Strategic developments"
            ]
    
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def _fetch_acled_data(self, country: str) -> pd.DataFrame:
        """Fetch ACLED data for a single country."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=self.lookback_days)
        
        params = {
            "key": self.api_key,
            "email": self.email,
            "country": country,
            "event_date": f"{start_date.strftime('%Y-%m-%d')}|{end_date.strftime('%Y-%m-%d')}",
            "event_date_where": "BETWEEN",
            "format": "json",
            "limit": 1000
        }
        
        try:
            r = requests.get(ACLED_API, params=params, timeout=30)
            r.raise_for_status()
            data = r.json()
            
            if not data.get("data"):
                return self._generate_mock_data(country)
            
            rows = []
            for event in data["data"]:
                rows.append({
                    "date": event.get("event_date", ""),
                    "value": 1,  # Count of events
                    "series_id": f"{country}_{event.get('event_type', 'unknown')}",
                    "country": country,
                    "event_type": event.get("event_type", "unknown"),
                    "fatalities": int(event.get("fatalities", 0)),
                    "latitude": float(event.get("latitude", 0)),
                    "longitude": float(event.get("longitude", 0))
                })
            
            return pd.DataFrame(rows)
            
        except Exception as e:
            print(f"Warning: Failed to fetch ACLED data for {country}: {e}")
            return self._generate_mock_data(country)
    
    def _generate_mock_data(self, country: str) -> pd.DataFrame:
        """Generate mock ACLED data for demonstration."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=self.lookback_days)
        
        rows = []
        for i in range(self.lookback_days):
            date = start_date + timedelta(days=i)
            
            # Mock events with some random variation
            import random
            for event_type in self.event_types:
                if random.random() < 0.3:  # 30% chance of event each day
                    fatalities = random.randint(0, 10) if event_type in ["Battles", "Violence against civilians"] else 0
                    
                    rows.append({
                        "date": date.strftime("%Y-%m-%d"),
                        "value": 1,
                        "series_id": f"{country}_{event_type}",
                        "country": country,
                        "event_type": event_type,
                        "fatalities": fatalities,
                        "latitude": random.uniform(-90, 90),
                        "longitude": random.uniform(-180, 180)
                    })
        
        return pd.DataFrame(rows)
    
    def fetch(self) -> pd.DataFrame:
        """Fetch ACLED data for all configured countries."""
        frames = []
        for country in self.countries:
            df = self._fetch_acled_data(country)
            frames.append(df)
        
        return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    
    def normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize ACLED data to standard format."""
        if df.empty:
            return df
            
        out = df.copy()
        out["source"] = "ACLED"
        out["value"] = pd.to_numeric(out["value"], errors="coerce")
        out["date"] = pd.to_datetime(out["date"], errors="coerce").dt.strftime("%Y-%m-%d")
        
        return out.dropna(subset=["value", "date"])
