from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any
from datetime import datetime, timedelta

import pandas as pd
import requests
from tenacity import retry, stop_after_attempt, wait_fixed

# Using OpenWeatherMap API for weather data
OPENWEATHER_API = "https://api.openweathermap.org/data/2.5"


@dataclass
class WeatherConnector:
    """Connector for weather and climate data."""
    
    api_key: str
    cities: List[str] = None
    lookback_days: int = 7
    
    name: str = "weather"
    
    def __post_init__(self):
        # Default cities to track if none provided
        if not self.cities:
            self.cities = [
                "New York",
                "London", 
                "Tokyo",
                "Sydney",
                "Dubai",
                "Singapore",
            ]
    
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def _fetch_weather_data(self, city: str) -> pd.DataFrame:
        """Fetch weather data for a single city."""
        # Get current weather
        params = {
            "q": city,
            "appid": self.api_key,
            "units": "metric"
        }
        
        try:
            r = requests.get(f"{OPENWEATHER_API}/weather", params=params, timeout=30)
            r.raise_for_status()
            data = r.json()
            
            # Extract key metrics
            main = data.get("main", {})
            weather = data.get("weather", [{}])[0]
            
            return pd.DataFrame([{
                "date": datetime.now().strftime("%Y-%m-%d"),
                "value": main.get("temp", 0),
                "series_id": f"{city}_temperature",
                "metric": "temperature"
            }])
            
        except Exception as e:
            print(f"Warning: Failed to fetch weather data for {city}: {e}")
            return self._generate_mock_data(city)
    
    def _generate_mock_data(self, city: str) -> pd.DataFrame:
        """Generate mock weather data for demonstration."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=self.lookback_days)
        
        # Mock base temperatures for different cities
        base_temps = {
            "New York": 15.0,
            "London": 12.0,
            "Tokyo": 18.0,
            "Sydney": 22.0,
            "Dubai": 28.0,
            "Singapore": 26.0,
        }
        
        base_temp = base_temps.get(city, 20.0)
        rows = []
        
        for i in range(self.lookback_days):
            date = start_date + timedelta(days=i)
            # Add some random variation
            import random
            variation = random.uniform(-5, 5)  # ±5°C variation
            temp = base_temp + variation
            
            rows.append({
                "date": date.strftime("%Y-%m-%d"),
                "value": round(temp, 1),
                "series_id": f"{city}_temperature",
                "metric": "temperature"
            })
        
        return pd.DataFrame(rows)
    
    def fetch(self) -> pd.DataFrame:
        """Fetch weather data for all configured cities."""
        frames = []
        for city in self.cities:
            df = self._fetch_weather_data(city)
            frames.append(df)
        
        return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    
    def normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize weather data to standard format."""
        if df.empty:
            return df
            
        out = df.copy()
        out["source"] = "WEATHER"
        out["value"] = pd.to_numeric(out["value"], errors="coerce")
        out["date"] = pd.to_datetime(out["date"], errors="coerce").dt.strftime("%Y-%m-%d")
        
        return out.dropna(subset=["value", "date"])
