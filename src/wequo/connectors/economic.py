from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any
from datetime import datetime, timedelta

import pandas as pd
import requests
from tenacity import retry, stop_after_attempt, wait_fixed

# Using World Bank API for economic indicators
WORLDBANK_API = "https://api.worldbank.org/v2"


@dataclass
class EconomicConnector:
    """Connector for economic indicators from World Bank and other sources."""
    
    indicators: List[str] = None
    countries: List[str] = None
    lookback_days: int = 30
    
    name: str = "economic"
    
    def __post_init__(self):
        # Default economic indicators if none provided
        if not self.indicators:
            self.indicators = [
                "NY.GDP.MKTP.CD",      # GDP (current US$)
                "FP.CPI.TOTL.ZG",      # Inflation, consumer prices (annual %)
                "SL.UEM.TOTL.ZS",      # Unemployment, total (% of total labor force)
                "NE.TRD.GNFS.ZS",      # Trade (% of GDP)
            ]
        
        if not self.countries:
            self.countries = [
                "US",   # United States
                "CN",   # China
                "DE",   # Germany
                "JP",   # Japan
                "GB",   # United Kingdom
                "IN",   # India
            ]
    
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def _fetch_economic_data(self, indicator: str, country: str) -> pd.DataFrame:
        """Fetch economic data for a single indicator and country."""
        try:
            # World Bank API call
            url = f"{WORLDBANK_API}/country/{country}/indicator/{indicator}"
            params = {
                "format": "json",
                "per_page": 10,  # Last 10 years
                "date": "2014:2024"
            }
            
            r = requests.get(url, params=params, timeout=30)
            r.raise_for_status()
            data = r.json()
            
            if len(data) < 2 or not data[1]:
                return self._generate_mock_data(indicator, country)
            
            rows = []
            for item in data[1]:
                if item.get("value") is not None:
                    rows.append({
                        "date": f"{item['date']}-12-31",  # Year-end date
                        "value": float(item["value"]),
                        "series_id": f"{country}_{indicator}",
                        "country": country,
                        "indicator": indicator
                    })
            
            return pd.DataFrame(rows)
            
        except Exception as e:
            print(f"Warning: Failed to fetch economic data for {indicator} in {country}: {e}")
            return self._generate_mock_data(indicator, country)
    
    def _generate_mock_data(self, indicator: str, country: str) -> pd.DataFrame:
        """Generate mock economic data for demonstration."""
        # Mock base values for different indicators
        base_values = {
            "NY.GDP.MKTP.CD": 2000000000000,  # GDP in USD
            "FP.CPI.TOTL.ZG": 2.5,            # Inflation %
            "SL.UEM.TOTL.ZS": 5.0,            # Unemployment %
            "NE.TRD.GNFS.ZS": 50.0,           # Trade % of GDP
        }
        
        base_value = base_values.get(indicator, 100.0)
        rows = []
        
        # Generate data for last 5 years
        for year in range(2020, 2025):
            import random
            variation = random.uniform(-0.1, 0.1)  # ±10% variation
            value = base_value * (1 + variation)
            
            rows.append({
                "date": f"{year}-12-31",
                "value": round(value, 2),
                "series_id": f"{country}_{indicator}",
                "country": country,
                "indicator": indicator
            })
        
        return pd.DataFrame(rows)
    
    def fetch(self) -> pd.DataFrame:
        """Fetch economic data for all configured indicators and countries."""
        frames = []
        for indicator in self.indicators:
            for country in self.countries:
                df = self._fetch_economic_data(indicator, country)
                frames.append(df)
        
        return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    
    def normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize economic data to standard format."""
        if df.empty:
            return df
            
        out = df.copy()
        out["source"] = "ECONOMIC"
        out["value"] = pd.to_numeric(out["value"], errors="coerce")
        out["date"] = pd.to_datetime(out["date"], errors="coerce").dt.strftime("%Y-%m-%d")
        
        return out.dropna(subset=["value", "date"])
