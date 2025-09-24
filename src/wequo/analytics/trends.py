from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any
import pandas as pd
import numpy as np
from scipy import stats


@dataclass
class TrendResult:
    """Result of trend analysis."""
    
    series_id: str
    slope: float
    r_squared: float
    trend_strength: str
    direction: str
    p_value: float
    source: str


class TrendAnalyzer:
    """Analyze trends in time series data."""
    
    def __init__(self, min_data_points: int = 5):
        self.min_data_points = min_data_points
    
    def analyze_trends(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Analyze trends across all series in the DataFrame."""
        if df.empty:
            return []
        
        trends = []
        
        for series_id in df["series_id"].unique():
            series_data = df[df["series_id"] == series_id].copy()
            series_data = series_data.sort_values("date")
            
            if len(series_data) < self.min_data_points:
                continue
            
            # Analyze trend for this series
            trend = self._analyze_series_trend(series_data, series_id)
            if trend:
                trends.append(trend)
        
        # Sort by absolute slope (strongest trends first)
        trends.sort(key=lambda x: abs(x["slope"]), reverse=True)
        return trends
    
    def _analyze_series_trend(self, series_data: pd.DataFrame, series_id: str) -> Dict[str, Any] | None:
        """Analyze trend in a single time series using linear regression."""
        if len(series_data) < self.min_data_points:
            return None
        
        # Convert dates to numeric values for regression
        series_data = series_data.copy()
        series_data["date_numeric"] = pd.to_datetime(series_data["date"]).astype(np.int64)
        
        x = series_data["date_numeric"].values
        y = series_data["value"].values
        
        # Perform linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        r_squared = r_value ** 2
        
        # Determine trend strength
        if r_squared > 0.8:
            trend_strength = "strong"
        elif r_squared > 0.5:
            trend_strength = "moderate"
        elif r_squared > 0.2:
            trend_strength = "weak"
        else:
            trend_strength = "none"
        
        # Determine direction
        if slope > 0:
            direction = "upward"
        elif slope < 0:
            direction = "downward"
        else:
            direction = "flat"
        
        return {
            "series_id": series_id,
            "slope": slope,
            "r_squared": r_squared,
            "trend_strength": trend_strength,
            "direction": direction,
            "p_value": p_value,
            "source": series_data.iloc[0].get("source", "unknown")
        }
    
    def analyze_moving_averages(self, df: pd.DataFrame, windows: List[int] = [5, 10, 20]) -> pd.DataFrame:
        """Calculate moving averages for trend analysis."""
        if df.empty:
            return df
        
        result_dfs = []
        
        for series_id in df["series_id"].unique():
            series_data = df[df["series_id"] == series_id].copy()
            series_data = series_data.sort_values("date")
            
            # Calculate moving averages
            for window in windows:
                if len(series_data) >= window:
                    series_data[f"ma_{window}"] = series_data["value"].rolling(window=window).mean()
            
            result_dfs.append(series_data)
        
        return pd.concat(result_dfs, ignore_index=True) if result_dfs else pd.DataFrame()
    
    def detect_trend_changes(self, df: pd.DataFrame, window: int = 10) -> List[Dict[str, Any]]:
        """Detect points where trends change direction."""
        if df.empty:
            return []
        
        trend_changes = []
        
        for series_id in df["series_id"].unique():
            series_data = df[df["series_id"] == series_id].copy()
            series_data = series_data.sort_values("date")
            
            if len(series_data) < window * 2:
                continue
            
            # Calculate rolling slopes
            series_data["rolling_slope"] = series_data["value"].rolling(window=window).apply(
                lambda x: stats.linregress(range(len(x)), x)[0] if len(x) == window else np.nan
            )
            
            # Detect slope sign changes
            series_data["slope_sign"] = np.sign(series_data["rolling_slope"])
            series_data["slope_change"] = series_data["slope_sign"].diff()
            
            for _, row in series_data.iterrows():
                if pd.isna(row["slope_change"]) or row["slope_change"] == 0:
                    continue
                
                trend_changes.append({
                    "series_id": series_id,
                    "date": row["date"],
                    "value": row["value"],
                    "slope_change": row["slope_change"],
                    "new_slope": row["rolling_slope"],
                    "source": row.get("source", "unknown")
                })
        
        return trend_changes
    
    def calculate_trend_momentum(self, df: pd.DataFrame, window: int = 5) -> pd.DataFrame:
        """Calculate trend momentum (acceleration of trend)."""
        if df.empty:
            return df
        
        result_dfs = []
        
        for series_id in df["series_id"].unique():
            series_data = df[df["series_id"] == series_id].copy()
            series_data = series_data.sort_values("date")
            
            if len(series_data) < window * 2:
                continue
            
            # Calculate first derivative (velocity)
            series_data["velocity"] = series_data["value"].diff()
            
            # Calculate second derivative (acceleration)
            series_data["acceleration"] = series_data["velocity"].diff()
            
            # Calculate momentum (rolling average of acceleration)
            series_data["momentum"] = series_data["acceleration"].rolling(window=window).mean()
            
            result_dfs.append(series_data)
        
        return pd.concat(result_dfs, ignore_index=True) if result_dfs else pd.DataFrame()
