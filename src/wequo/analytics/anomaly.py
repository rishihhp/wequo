from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any
import pandas as pd
import numpy as np
from scipy import stats


@dataclass
class AnomalyResult:
    """Result of anomaly detection."""
    
    series_id: str
    date: str
    value: float
    z_score: float
    is_anomaly: bool
    source: str


class AnomalyDetector:
    """Detect anomalies in time series data using statistical methods."""
    
    def __init__(self, threshold: float = 2.0, min_data_points: int = 10):
        self.threshold = threshold  # Z-score threshold for anomaly detection
        self.min_data_points = min_data_points
    
    def detect_anomalies(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect anomalies across all series in the DataFrame."""
        if df.empty:
            return []
        
        anomalies = []
        
        for series_id in df["series_id"].unique():
            series_data = df[df["series_id"] == series_id].copy()
            series_data = series_data.sort_values("date")
            
            if len(series_data) < self.min_data_points:
                continue
            
            # Detect anomalies for this series
            series_anomalies = self._detect_series_anomalies(series_data, series_id)
            anomalies.extend(series_anomalies)
        
        # Sort by z-score (most anomalous first)
        anomalies.sort(key=lambda x: abs(x["z_score"]), reverse=True)
        return anomalies
    
    def _detect_series_anomalies(self, series_data: pd.DataFrame, series_id: str) -> List[Dict[str, Any]]:
        """Detect anomalies in a single time series."""
        values = series_data["value"].values
        
        # Calculate z-scores
        z_scores = np.abs(stats.zscore(values))
        
        anomalies = []
        for i, (_, row) in enumerate(series_data.iterrows()):
            z_score = z_scores[i]
            
            if z_score > self.threshold:
                anomalies.append({
                    "series_id": series_id,
                    "date": row["date"],
                    "value": row["value"],
                    "z_score": z_score,
                    "is_anomaly": True,
                    "source": row.get("source", "unknown")
                })
        
        return anomalies
    
    def detect_trend_anomalies(self, df: pd.DataFrame, window: int = 7) -> List[Dict[str, Any]]:
        """Detect anomalies based on trend deviations."""
        if df.empty:
            return []
        
        trend_anomalies = []
        
        for series_id in df["series_id"].unique():
            series_data = df[df["series_id"] == series_id].copy()
            series_data = series_data.sort_values("date")
            
            if len(series_data) < window * 2:
                continue
            
            # Calculate rolling mean and std
            series_data["rolling_mean"] = series_data["value"].rolling(window=window).mean()
            series_data["rolling_std"] = series_data["value"].rolling(window=window).std()
            
            # Detect points that deviate significantly from rolling mean
            for _, row in series_data.iterrows():
                if pd.isna(row["rolling_mean"]) or pd.isna(row["rolling_std"]):
                    continue
                
                if row["rolling_std"] == 0:
                    continue
                
                z_score = abs(row["value"] - row["rolling_mean"]) / row["rolling_std"]
                
                if z_score > self.threshold:
                    trend_anomalies.append({
                        "series_id": series_id,
                        "date": row["date"],
                        "value": row["value"],
                        "z_score": z_score,
                        "is_anomaly": True,
                        "source": row.get("source", "unknown"),
                        "anomaly_type": "trend_deviation"
                    })
        
        return trend_anomalies
    
    def detect_volatility_anomalies(self, df: pd.DataFrame, window: int = 7) -> List[Dict[str, Any]]:
        """Detect anomalies in volatility patterns."""
        if df.empty:
            return []
        
        volatility_anomalies = []
        
        for series_id in df["series_id"].unique():
            series_data = df[df["series_id"] == series_id].copy()
            series_data = series_data.sort_values("date")
            
            if len(series_data) < window * 2:
                continue
            
            # Calculate rolling volatility (standard deviation of returns)
            series_data["returns"] = series_data["value"].pct_change()
            series_data["rolling_volatility"] = series_data["returns"].rolling(window=window).std()
            
            # Detect unusually high volatility
            vol_mean = series_data["rolling_volatility"].mean()
            vol_std = series_data["rolling_volatility"].std()
            
            if vol_std == 0:
                continue
            
            for _, row in series_data.iterrows():
                if pd.isna(row["rolling_volatility"]):
                    continue
                
                vol_z_score = (row["rolling_volatility"] - vol_mean) / vol_std
                
                if vol_z_score > self.threshold:
                    volatility_anomalies.append({
                        "series_id": series_id,
                        "date": row["date"],
                        "value": row["rolling_volatility"],
                        "z_score": vol_z_score,
                        "is_anomaly": True,
                        "source": row.get("source", "unknown"),
                        "anomaly_type": "high_volatility"
                    })
        
        return volatility_anomalies
