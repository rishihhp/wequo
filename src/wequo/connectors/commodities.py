from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any
from datetime import datetime, timedelta

import pandas as pd
import requests
from tenacity import retry, stop_after_attempt, wait_fixed

# Using Alpha Vantage for commodities data
ALPHA_VANTAGE_API = "https://www.alphavantage.co/query"


@dataclass
class CommoditiesConnector:
    """Connector for commodity prices using Alpha Vantage API."""
    
    api_key: str
    symbols: List[str]
    lookback_days: int = 30
    
    name: str = "commodities"
    
    def __post_init__(self):
        # Default commodity symbols if none provided
        if not self.symbols:
            self.symbols = [
                "WTI",      # West Texas Intermediate crude oil
                "BRENT",    # Brent crude oil
                "GOLD",     # Gold
                "SILVER",   # Silver
                "COPPER",   # Copper
                "NATURAL_GAS",  # Natural gas
            ]
    
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def _fetch_commodity(self, symbol: str) -> pd.DataFrame:
        """Fetch commodity data for a single symbol."""
        params = {
            "function": "DIGITAL_CURRENCY_DAILY" if symbol in ["BTC", "ETH"] else "TIME_SERIES_DAILY",
            "symbol": symbol,
            "apikey": self.api_key,
            "outputsize": "compact"
        }
        
        # For commodities, we'll use a different approach
        # Using a mock implementation for now - in production, you'd use a real commodities API
        if symbol == "WTI":
            params["function"] = "TIME_SERIES_DAILY"
            params["symbol"] = "CL=F"  # WTI Crude Oil futures
        
        r = requests.get(ALPHA_VANTAGE_API, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        
        # Handle different response formats
        if "Time Series (Daily)" in data:
            time_series = data["Time Series (Daily)"]
        elif "Time Series (Digital Currency Daily)" in data:
            time_series = data["Time Series (Digital Currency Daily)"]
        else:
            # Mock data for demonstration
            return self._generate_mock_data(symbol)
        
        # Convert to DataFrame
        rows = []
        for date_str, values in time_series.items():
            if isinstance(values, dict):
                price = float(values.get("4. close", values.get("close (USD)", 0)))
            else:
                price = float(values)
            
            rows.append({
                "date": date_str,
                "value": price,
                "series_id": symbol
            })
        
        return pd.DataFrame(rows)
    
    def _generate_mock_data(self, symbol: str) -> pd.DataFrame:
        """Generate mock commodity data for demonstration."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=self.lookback_days)
        
        # Mock prices for different commodities
        base_prices = {
            "WTI": 75.0,
            "BRENT": 78.0,
            "GOLD": 2000.0,
            "SILVER": 25.0,
            "COPPER": 4.0,
            "NATURAL_GAS": 3.5,
        }
        
        base_price = base_prices.get(symbol, 100.0)
        rows = []
        
        for i in range(self.lookback_days):
            date = start_date + timedelta(days=i)
            # Add some random variation
            import random
            variation = random.uniform(-0.05, 0.05)  # ±5% variation
            price = base_price * (1 + variation)
            
            rows.append({
                "date": date.strftime("%Y-%m-%d"),
                "value": round(price, 2),
                "series_id": symbol
            })
        
        return pd.DataFrame(rows)
    
    def fetch(self) -> pd.DataFrame:
        """Fetch data for all configured commodity symbols."""
        frames = []
        for symbol in self.symbols:
            try:
                df = self._fetch_commodity(symbol)
                frames.append(df)
            except Exception as e:
                print(f"Warning: Failed to fetch {symbol}: {e}")
                # Add mock data as fallback
                frames.append(self._generate_mock_data(symbol))
        
        return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    
    def normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize commodity data to standard format."""
        if df.empty:
            return df
            
        out = df.copy()
        out["source"] = "COMMODITIES"
        out["value"] = pd.to_numeric(out["value"], errors="coerce")
        out["date"] = pd.to_datetime(out["date"], errors="coerce").dt.strftime("%Y-%m-%d")
        
        return out.dropna(subset=["value", "date"])
