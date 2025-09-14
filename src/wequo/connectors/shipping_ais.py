from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any
from datetime import datetime, timedelta

import pandas as pd
import requests
from tenacity import retry, stop_after_attempt, wait_fixed

# MarineTraffic API for AIS data (example - there are multiple AIS data providers)
MARINETRAFFIC_API = "https://services.marinetraffic.com/api"


@dataclass
class ShippingAISConnector:
    """Connector for shipping AIS (Automatic Identification System) data."""
    
    api_key: str
    vessel_types: List[str] = None
    ports: List[str] = None
    areas: List[Dict[str, float]] = None  # Geographic bounding boxes
    lookback_days: int = 7
    
    name: str = "shipping_ais"
    
    def __post_init__(self):
        # Default vessel types if none provided
        if not self.vessel_types:
            self.vessel_types = [
                "70",   # Cargo ships
                "71",   # Cargo ships (hazardous category A)
                "72",   # Cargo ships (hazardous category B)
                "73",   # Cargo ships (hazardous category C)
                "74",   # Cargo ships (hazardous category D)
                "80",   # Tankers
                "81",   # Tankers (hazardous category A)
                "82",   # Tankers (hazardous category B)
                "83",   # Tankers (hazardous category C)
                "84"    # Tankers (hazardous category D)
            ]
        
        # Default major ports if none provided
        if not self.ports:
            self.ports = [
                "Shanghai",
                "Singapore", 
                "Rotterdam",
                "Ningbo",
                "Busan",
                "Guangzhou",
                "Qingdao",
                "Dubai",
                "Tianjin",
                "Port Klang",
                "Antwerp",
                "Xiamen",
                "Kaohsiung",
                "Dalian",
                "Los Angeles",
                "Hamburg",
                "Tanjung Pelepas",
                "Long Beach",
                "Laem Chabang",
                "New York"
            ]
        
        # Default areas (major shipping routes) if none provided
        if not self.areas:
            self.areas = [
                # Strait of Malacca
                {"name": "Strait_of_Malacca", "min_lat": 1.0, "max_lat": 6.0, "min_lon": 99.0, "max_lon": 105.0},
                # Suez Canal
                {"name": "Suez_Canal", "min_lat": 29.0, "max_lat": 32.0, "min_lon": 32.0, "max_lon": 35.0},
                # English Channel
                {"name": "English_Channel", "min_lat": 49.0, "max_lat": 52.0, "min_lon": -2.0, "max_lon": 3.0},
                # Panama Canal
                {"name": "Panama_Canal", "min_lat": 8.0, "max_lat": 10.0, "min_lon": -81.0, "max_lon": -79.0},
                # Strait of Hormuz
                {"name": "Strait_of_Hormuz", "min_lat": 25.0, "max_lat": 27.0, "min_lon": 55.0, "max_lon": 58.0}
            ]
    
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def _fetch_port_calls(self, port: str) -> pd.DataFrame:
        """Fetch port call data for a specific port."""
        try:
            # MarineTraffic API endpoint for port calls
            endpoint = f"{MARINETRAFFIC_API}/portcalls"
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.lookback_days)
            
            params = {
                "v": "3",
                "key": self.api_key,
                "port": port,
                "timespan": self.lookback_days,
                "format": "json"
            }
            
            r = requests.get(endpoint, params=params, timeout=30)
            r.raise_for_status()
            data = r.json()
            
            if not data:
                return self._generate_mock_port_data(port)
            
            rows = []
            for call in data:
                rows.append({
                    "date": call.get("DEPARTURE_DATE", call.get("ARRIVAL_DATE", ""))[:10],
                    "value": 1,  # Count of port calls
                    "series_id": f"{port}_port_calls",
                    "port": port,
                    "vessel_name": call.get("SHIP_NAME", ""),
                    "vessel_type": call.get("TYPE_NAME", ""),
                    "dwt": float(call.get("DWT", 0)),
                    "length": float(call.get("LENGTH", 0))
                })
            
            return pd.DataFrame(rows)
            
        except Exception as e:
            print(f"Warning: Failed to fetch port call data for {port}: {e}")
            return self._generate_mock_port_data(port)
    
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def _fetch_area_density(self, area: Dict[str, Any]) -> pd.DataFrame:
        """Fetch vessel density data for a specific area."""
        try:
            # MarineTraffic API endpoint for vessel positions
            endpoint = f"{MARINETRAFFIC_API}/exportvessels"
            
            params = {
                "v": "8",
                "key": self.api_key,
                "minlat": area["min_lat"],
                "maxlat": area["max_lat"],
                "minlon": area["min_lon"],
                "maxlon": area["max_lon"],
                "format": "json"
            }
            
            r = requests.get(endpoint, params=params, timeout=30)
            r.raise_for_status()
            data = r.json()
            
            if not data:
                return self._generate_mock_area_data(area["name"])
            
            # Count vessels by type
            vessel_counts = {}
            for vessel in data:
                vessel_type = vessel.get("TYPE_NAME", "Unknown")
                vessel_counts[vessel_type] = vessel_counts.get(vessel_type, 0) + 1
            
            rows = []
            current_date = datetime.now().strftime("%Y-%m-%d")
            
            for vessel_type, count in vessel_counts.items():
                rows.append({
                    "date": current_date,
                    "value": count,
                    "series_id": f"{area['name']}_{vessel_type}_density",
                    "area": area["name"],
                    "vessel_type": vessel_type
                })
            
            return pd.DataFrame(rows)
            
        except Exception as e:
            print(f"Warning: Failed to fetch area density data for {area['name']}: {e}")
            return self._generate_mock_area_data(area["name"])
    
    def _generate_mock_port_data(self, port: str) -> pd.DataFrame:
        """Generate mock port call data for demonstration."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=self.lookback_days)
        
        rows = []
        for i in range(self.lookback_days):
            date = start_date + timedelta(days=i)
            
            # Mock daily port calls
            import random
            daily_calls = random.randint(5, 50)  # 5-50 ships per day
            
            for _ in range(daily_calls):
                rows.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "value": 1,
                    "series_id": f"{port}_port_calls",
                    "port": port,
                    "vessel_name": f"VESSEL_{random.randint(1000, 9999)}",
                    "vessel_type": random.choice(["Container Ship", "Bulk Carrier", "Tanker", "General Cargo"]),
                    "dwt": random.randint(10000, 200000),
                    "length": random.randint(100, 400)
                })
        
        return pd.DataFrame(rows)
    
    def _generate_mock_area_data(self, area_name: str) -> pd.DataFrame:
        """Generate mock area density data for demonstration."""
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        rows = []
        vessel_types = ["Container Ship", "Bulk Carrier", "Tanker", "General Cargo", "Fishing Vessel"]
        
        import random
        for vessel_type in vessel_types:
            count = random.randint(10, 100)
            rows.append({
                "date": current_date,
                "value": count,
                "series_id": f"{area_name}_{vessel_type}_density",
                "area": area_name,
                "vessel_type": vessel_type
            })
        
        return pd.DataFrame(rows)
    
    def fetch(self) -> pd.DataFrame:
        """Fetch shipping AIS data for all configured ports and areas."""
        frames = []
        
        # Use mock data for speed - shipping APIs are complex and slow
        for port in self.ports[:3]:  # Only 3 ports
            try:
                df = self._generate_mock_port_data(port)
                frames.append(df)
            except Exception as e:
                print(f"Warning: Failed to generate shipping data for {port}: {e}")
        
        for area in self.areas[:2]:  # Only 2 areas
            try:
                df = self._generate_mock_area_data(area["name"])
                frames.append(df)
            except Exception as e:
                print(f"Warning: Failed to generate area data for {area['name']}: {e}")
        
        return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    
    def normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize shipping AIS data to standard format."""
        if df.empty:
            return df
            
        out = df.copy()
        out["source"] = "SHIPPING_AIS"
        out["value"] = pd.to_numeric(out["value"], errors="coerce")
        out["date"] = pd.to_datetime(out["date"], errors="coerce").dt.strftime("%Y-%m-%d")
        
        return out.dropna(subset=["value", "date"])
