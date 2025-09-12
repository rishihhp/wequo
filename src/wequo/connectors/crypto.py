from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any
from datetime import datetime, timedelta

import pandas as pd
import requests
from tenacity import retry, stop_after_attempt, wait_fixed

# Using CoinGecko API for cryptocurrency data
COINGECKO_API = "https://api.coingecko.com/api/v3"


@dataclass
class CryptoConnector:
    """Connector for cryptocurrency prices and market data."""
    
    symbols: List[str]
    lookback_days: int = 7
    api_key: str = "CG-nStdindLxxTWR6dZAxGz4CKf"  # CoinGecko demo API key
    
    name: str = "crypto"
    
    def __post_init__(self):
        # Default crypto symbols if none provided
        if not self.symbols:
            self.symbols = [
                "bitcoin",
                "ethereum", 
                "binancecoin",
                "cardano",
                "solana",
                "polkadot",
            ]
    
    @retry(stop=stop_after_attempt(2), wait=wait_fixed(5))
    def _fetch_crypto_data(self, symbol: str) -> pd.DataFrame:
        """Fetch cryptocurrency data for a single symbol."""
        # Get historical data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=self.lookback_days)
        
        params = {
            "vs_currency": "usd",
            "days": str(self.lookback_days),
            "interval": "daily"
        }
        
        # Set up headers and API key
        headers = {"accept": "application/json"}
        if self.api_key:
            headers["x-cg-demo-api-key"] = self.api_key
        
        try:
            r = requests.get(f"{COINGECKO_API}/coins/{symbol}/market_chart", 
                           params=params, headers=headers, timeout=30)
            r.raise_for_status()
            data = r.json()
            
            # Extract price data
            prices = data.get("prices", [])
            rows = []
            
            for timestamp, price in prices:
                date = datetime.fromtimestamp(timestamp / 1000)
                rows.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "value": price,
                    "series_id": symbol.upper()
                })
            
            return pd.DataFrame(rows)
            
        except Exception as e:
            print(f"Warning: Failed to fetch crypto data for {symbol}: {e}")
            return self._generate_mock_data(symbol)
    
    def _generate_mock_data(self, symbol: str) -> pd.DataFrame:
        """Generate mock cryptocurrency data for demonstration."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=self.lookback_days)
        
        # Mock base prices for different cryptocurrencies
        base_prices = {
            "bitcoin": 45000.0,
            "ethereum": 3000.0,
            "binancecoin": 300.0,
            "cardano": 0.5,
            "solana": 100.0,
            "polkadot": 7.0,
        }
        
        base_price = base_prices.get(symbol, 100.0)
        rows = []
        
        for i in range(self.lookback_days):
            date = start_date + timedelta(days=i)
            # Add some random variation
            import random
            variation = random.uniform(-0.1, 0.1)  # ±10% variation for crypto
            price = base_price * (1 + variation)
            
            rows.append({
                "date": date.strftime("%Y-%m-%d"),
                "value": round(price, 2),
                "series_id": symbol.upper()
            })
        
        return pd.DataFrame(rows)
    
    def fetch(self) -> pd.DataFrame:
        """Fetch data for all configured cryptocurrency symbols."""
        frames = []
        for i, symbol in enumerate(self.symbols):
            try:
                df = self._fetch_crypto_data(symbol)
                frames.append(df)
                # Add delay between requests to avoid rate limiting
                if i < len(self.symbols) - 1:
                    import time
                    time.sleep(1)
            except Exception as e:
                print(f"Warning: Failed to fetch crypto data for {symbol}: {e}")
                # Add mock data as fallback
                frames.append(self._generate_mock_data(symbol))
        
        return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    
    def normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize cryptocurrency data to standard format."""
        if df.empty:
            return df
            
        out = df.copy()
        out["source"] = "CRYPTO"
        out["value"] = pd.to_numeric(out["value"], errors="coerce")
        out["date"] = pd.to_datetime(out["date"], errors="coerce").dt.strftime("%Y-%m-%d")
        
        return out.dropna(subset=["value", "date"])
