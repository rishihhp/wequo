from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any
import pandas as pd
import numpy as np


@dataclass
class DeltaResult:
    """Result of delta calculation."""
    
    series_id: str
    old_value: float
    new_value: float
    delta_abs: float
    delta_pct: float
    date_old: str
    date_new: str
    source: str


class DeltaCalculator:
    """Calculate deltas and changes in time series data."""
    
    def __init__(self, threshold: float = 0.05):
        self.threshold = threshold  # Minimum percentage change to report
    
    def calculate_top_deltas(self, df: pd.DataFrame, top_n: int = 5) -> List[Dict[str, Any]]:
        """Calculate top N deltas across all series."""
        if df.empty:
            return []
        
        deltas = []
        
        for series_id in df["series_id"].unique():
            series_data = df[df["series_id"] == series_id].copy()
            series_data = series_data.sort_values("date")
            
            if len(series_data) < 2:
                continue
            
            # Calculate delta between first and last values
            first_row = series_data.iloc[0]
            last_row = series_data.iloc[-1]
            
            old_value = first_row["value"]
            new_value = last_row["value"]
            
            if old_value == 0:
                continue
            
            delta_abs = new_value - old_value
            delta_pct = delta_abs / abs(old_value)
            
            # Only include significant changes
            if abs(delta_pct) >= self.threshold:
                deltas.append({
                    "series_id": series_id,
                    "old_value": old_value,
                    "new_value": new_value,
                    "delta_abs": delta_abs,
                    "delta_pct": delta_pct,
                    "date_old": first_row["date"],
                    "date_new": last_row["date"],
                    "source": first_row.get("source", "unknown")
                })
        
        # Sort by absolute percentage change and return top N
        deltas.sort(key=lambda x: abs(x["delta_pct"]), reverse=True)
        return deltas[:top_n]
    
    def calculate_rolling_deltas(self, df: pd.DataFrame, window: int = 7) -> pd.DataFrame:
        """Calculate rolling deltas for each series."""
        if df.empty:
            return df
        
        result_dfs = []
        
        for series_id in df["series_id"].unique():
            series_data = df[df["series_id"] == series_id].copy()
            series_data = series_data.sort_values("date")
            
            if len(series_data) < window:
                continue
            
            # Calculate rolling percentage change
            series_data["rolling_delta_pct"] = series_data["value"].pct_change(window)
            series_data["rolling_delta_abs"] = series_data["value"].diff(window)
            
            result_dfs.append(series_data)
        
        return pd.concat(result_dfs, ignore_index=True) if result_dfs else pd.DataFrame()
    
    def calculate_daily_deltas(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate daily deltas for each series."""
        if df.empty:
            return df
        
        result_dfs = []
        
        for series_id in df["series_id"].unique():
            series_data = df[df["series_id"] == series_id].copy()
            series_data = series_data.sort_values("date")
            
            if len(series_data) < 2:
                continue
            
            # Calculate daily percentage change
            series_data["daily_delta_pct"] = series_data["value"].pct_change()
            series_data["daily_delta_abs"] = series_data["value"].diff()
            
            result_dfs.append(series_data)
        
        return pd.concat(result_dfs, ignore_index=True) if result_dfs else pd.DataFrame()
