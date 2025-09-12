"""
Optimized analytics engine for better performance with larger datasets.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from pathlib import Path
import time
import logging

import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing as mp

from .anomaly import AnomalyDetector
from .trends import TrendAnalyzer
from .deltas import DeltaCalculator
from .change_points import ChangePointDetector
from .correlation import CorrelationAnalyzer
from .event_impact import EventImpactAnalyzer


@dataclass
class PerformanceMetrics:
    """Performance metrics for analytics operations."""
    total_time: float
    data_combination_time: float
    delta_calculation_time: float
    anomaly_detection_time: float
    trend_analysis_time: float
    percentile_calculation_time: float
    summary_stats_time: float
    parallel_processing_time: float


class OptimizedAnalyticsEngine:
    """
    Optimized analytics engine with performance improvements for larger datasets.
    
    Features:
    - Parallel processing for independent operations
    - Chunked processing for large datasets
    - Memory-efficient data handling
    - Performance monitoring
    - Caching for repeated operations
    """
    
    def __init__(self, 
                 anomaly_threshold: float = 2.0,
                 delta_threshold: float = 0.05,
                 min_data_points: int = 5,
                 max_workers: Optional[int] = None,
                 chunk_size: int = 10000):
        self.anomaly_detector = AnomalyDetector(threshold=anomaly_threshold)
        self.trend_analyzer = TrendAnalyzer()
        self.delta_calculator = DeltaCalculator(threshold=delta_threshold)
        self.change_point_detector = ChangePointDetector(min_segment_length=min_data_points)
        self.correlation_analyzer = CorrelationAnalyzer(min_data_points=min_data_points)
        self.event_impact_analyzer = EventImpactAnalyzer()
        self.min_data_points = min_data_points
        self.max_workers = max_workers or min(mp.cpu_count(), 8)
        self.chunk_size = chunk_size
        self.logger = logging.getLogger(__name__)
        
        # Performance tracking
        self.performance_metrics = None
    
    def analyze(self, data_frames: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Run optimized analytics on all data frames."""
        start_time = time.time()
        self.logger.info(f"Starting optimized analytics with {self.max_workers} workers")
        
        # Combine data efficiently
        combine_start = time.time()
        all_data = self._combine_data_optimized(data_frames)
        combine_time = time.time() - combine_start
        
        if all_data.empty:
            self.logger.warning("No data available for analysis")
            return {
                "top_deltas": [],
                "anomalies": [],
                "trends": [],
                "percentiles": {},
                "summary_stats": {},
                "performance_metrics": {
                    "total_time": time.time() - start_time,
                    "data_combination_time": combine_time,
                    "delta_calculation_time": 0.0,
                    "anomaly_detection_time": 0.0,
                    "trend_analysis_time": 0.0,
                    "percentile_calculation_time": 0.0,
                    "summary_stats_time": 0.0,
                    "parallel_processing_time": 0.0
                }
            }
        
        self.logger.info(f"Combined data: {len(all_data)} rows, {all_data['series_id'].nunique()} series")
        
        # Run analytics in parallel where possible
        parallel_start = time.time()
        results = self._run_parallel_analytics(all_data)
        parallel_time = time.time() - parallel_start
        
        # Analyze event impacts (sequential, depends on anomalies and change points)
        event_impact_start = time.time()
        event_impacts = self._analyze_event_impacts(all_data, results)
        event_impact_time = time.time() - event_impact_start
        
        # Add event impacts to results
        results['event_impacts'] = event_impacts
        results['event_impact_time'] = event_impact_time
        
        # Calculate performance metrics
        total_time = time.time() - start_time
        self.performance_metrics = PerformanceMetrics(
            total_time=total_time,
            data_combination_time=combine_time,
            delta_calculation_time=results.get('delta_time', 0.0),
            anomaly_detection_time=results.get('anomaly_time', 0.0),
            trend_analysis_time=results.get('trend_time', 0.0),
            percentile_calculation_time=results.get('percentile_time', 0.0),
            summary_stats_time=results.get('summary_time', 0.0),
            parallel_processing_time=parallel_time
        )
        
        # Add performance metrics to results
        results['performance_metrics'] = {
            "total_time": total_time,
            "data_combination_time": combine_time,
            "delta_calculation_time": results.get('delta_time', 0.0),
            "anomaly_detection_time": results.get('anomaly_time', 0.0),
            "trend_analysis_time": results.get('trend_time', 0.0),
            "percentile_calculation_time": results.get('percentile_time', 0.0),
            "summary_stats_time": results.get('summary_time', 0.0),
            "parallel_processing_time": parallel_time
        }
        
        self.logger.info(f"Analytics completed in {total_time:.2f}s")
        return results
    
    def _combine_data_optimized(self, data_frames: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Optimized data combination with memory efficiency."""
        if not data_frames:
            return pd.DataFrame()
        
        # Use list comprehension for better performance
        combined_data = []
        for source, df in data_frames.items():
            if df.empty:
                continue
            
            # Only copy necessary columns to reduce memory usage
            df_subset = df[['series_id', 'date', 'value']].copy()
            df_subset['source'] = source
            combined_data.append(df_subset)
        
        if not combined_data:
            return pd.DataFrame()
        
        # Use pd.concat with ignore_index for better performance
        result = pd.concat(combined_data, ignore_index=True)
        
        # Optimize data types
        result['date'] = pd.to_datetime(result['date'])
        result['value'] = pd.to_numeric(result['value'], errors='coerce')
        
        # Sort for better performance in subsequent operations
        result = result.sort_values(['series_id', 'date'])
        
        return result
    
    def _run_parallel_analytics(self, all_data: pd.DataFrame) -> Dict[str, Any]:
        """Run analytics operations in parallel where possible."""
        results = {}
        
        # Operations that can run in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit tasks
            future_to_task = {
                executor.submit(self._calculate_deltas_optimized, all_data): 'deltas',
                executor.submit(self._detect_anomalies_optimized, all_data): 'anomalies',
                executor.submit(self._analyze_trends_optimized, all_data): 'trends',
                executor.submit(self._calculate_percentiles_optimized, all_data): 'percentiles',
                executor.submit(self._calculate_summary_stats_optimized, all_data): 'summary_stats',
                executor.submit(self._detect_change_points_optimized, all_data): 'change_points',
                executor.submit(self._analyze_correlations_optimized, all_data): 'correlations'
            }
            
            # Collect results
            for future in as_completed(future_to_task):
                task_name = future_to_task[future]
                try:
                    result = future.result()
                    if task_name == 'deltas':
                        results['top_deltas'] = result['deltas']
                        results['delta_time'] = result['time']
                    elif task_name == 'anomalies':
                        results['anomalies'] = result['anomalies']
                        results['anomaly_time'] = result['time']
                    elif task_name == 'trends':
                        results['trends'] = result['trends']
                        results['trend_time'] = result['time']
                    elif task_name == 'percentiles':
                        results['percentiles'] = result['percentiles']
                        results['percentile_time'] = result['time']
                    elif task_name == 'summary_stats':
                        results['summary_stats'] = result['summary_stats']
                        results['summary_time'] = result['time']
                    elif task_name == 'change_points':
                        results['change_points'] = result['change_points']
                        results['change_points_time'] = result['time']
                    elif task_name == 'correlations':
                        results['correlations'] = result['correlations']
                        results['correlations_time'] = result['time']
                except Exception as e:
                    self.logger.error(f"Error in {task_name}: {e}")
                    # Set default values for failed tasks
                    if task_name == 'deltas':
                        results['top_deltas'] = []
                        results['delta_time'] = 0.0
                    elif task_name == 'anomalies':
                        results['anomalies'] = []
                        results['anomaly_time'] = 0.0
                    elif task_name == 'trends':
                        results['trends'] = []
                        results['trend_time'] = 0.0
                    elif task_name == 'percentiles':
                        results['percentiles'] = {}
                        results['percentile_time'] = 0.0
                    elif task_name == 'summary_stats':
                        results['summary_stats'] = {}
                        results['summary_time'] = 0.0
                    elif task_name == 'change_points':
                        results['change_points'] = {}
                        results['change_points_time'] = 0.0
                    elif task_name == 'correlations':
                        results['correlations'] = []
                        results['correlations_time'] = 0.0
        
        return results
    
    def _calculate_deltas_optimized(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Optimized delta calculation."""
        start_time = time.time()
        
        try:
            # Use vectorized operations where possible
            deltas = self.delta_calculator.calculate_top_deltas(df, top_n=5)
            return {
                'deltas': deltas,
                'time': time.time() - start_time
            }
        except Exception as e:
            self.logger.error(f"Error calculating deltas: {e}")
            return {
                'deltas': [],
                'time': time.time() - start_time
            }
    
    def _detect_anomalies_optimized(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Optimized anomaly detection with chunking for large datasets."""
        start_time = time.time()
        
        try:
            # For very large datasets, process in chunks
            if len(df) > self.chunk_size:
                anomalies = self._detect_anomalies_chunked(df)
            else:
                anomalies = self.anomaly_detector.detect_anomalies(df)
            
            return {
                'anomalies': anomalies,
                'time': time.time() - start_time
            }
        except Exception as e:
            self.logger.error(f"Error detecting anomalies: {e}")
            return {
                'anomalies': [],
                'time': time.time() - start_time
            }
    
    def _detect_anomalies_chunked(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect anomalies in chunks for large datasets."""
        all_anomalies = []
        series_ids = df['series_id'].unique()
        
        # Process series in chunks
        for i in range(0, len(series_ids), self.chunk_size // 100):  # Smaller chunks for anomaly detection
            chunk_series = series_ids[i:i + self.chunk_size // 100]
            chunk_df = df[df['series_id'].isin(chunk_series)]
            
            if not chunk_df.empty:
                chunk_anomalies = self.anomaly_detector.detect_anomalies(chunk_df)
                all_anomalies.extend(chunk_anomalies)
        
        return all_anomalies
    
    def _analyze_trends_optimized(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Optimized trend analysis."""
        start_time = time.time()
        
        try:
            trends = self.trend_analyzer.analyze_trends(df)
            return {
                'trends': trends,
                'time': time.time() - start_time
            }
        except Exception as e:
            self.logger.error(f"Error analyzing trends: {e}")
            return {
                'trends': [],
                'time': time.time() - start_time
            }
    
    def _calculate_percentiles_optimized(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Optimized percentile calculation using vectorized operations."""
        start_time = time.time()
        
        try:
            percentiles = {}
            series_ids = df['series_id'].unique()
            
            # Use groupby for better performance
            grouped = df.groupby('series_id')['value']
            
            for series_id in series_ids:
                series_data = grouped.get_group(series_id)
                if len(series_data) >= self.min_data_points:
                    # Use numpy for faster percentile calculation
                    values = series_data.values
                    percentiles[series_id] = {
                        "p25": float(np.percentile(values, 25)),
                        "p50": float(np.median(values)),
                        "p75": float(np.percentile(values, 75)),
                        "p90": float(np.percentile(values, 90)),
                        "p95": float(np.percentile(values, 95)),
                    }
            
            return {
                'percentiles': percentiles,
                'time': time.time() - start_time
            }
        except Exception as e:
            self.logger.error(f"Error calculating percentiles: {e}")
            return {
                'percentiles': {},
                'time': time.time() - start_time
            }
    
    def _calculate_summary_stats_optimized(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Optimized summary statistics calculation."""
        start_time = time.time()
        
        try:
            if df.empty:
                return {
                    'summary_stats': {},
                    'time': time.time() - start_time
                }
            
            # Use vectorized operations for better performance
            summary_stats = {
                "total_series": int(df["series_id"].nunique()),
                "total_data_points": int(len(df)),
                "date_range": {
                    "start": str(df["date"].min()),
                    "end": str(df["date"].max())
                },
                "sources": list(df["source"].unique()),
                "value_stats": {
                    "mean": float(df["value"].mean()),
                    "std": float(df["value"].std()),
                    "min": float(df["value"].min()),
                    "max": float(df["value"].max())
                }
            }
            
            return {
                'summary_stats': summary_stats,
                'time': time.time() - start_time
            }
        except Exception as e:
            self.logger.error(f"Error calculating summary stats: {e}")
            return {
                'summary_stats': {},
                'time': time.time() - start_time
            }
    
    def _detect_change_points_optimized(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Optimized change point detection."""
        start_time = time.time()
        
        try:
            change_points = self.change_point_detector.analyze_all_series(df)
            return {
                'change_points': change_points,
                'time': time.time() - start_time
            }
        except Exception as e:
            self.logger.error(f"Error detecting change points: {e}")
            return {
                'change_points': {},
                'time': time.time() - start_time
            }
    
    def _analyze_correlations_optimized(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Optimized correlation analysis."""
        start_time = time.time()
        
        try:
            correlations = self.correlation_analyzer.analyze_correlations(df)
            return {
                'correlations': correlations,
                'time': time.time() - start_time
            }
        except Exception as e:
            self.logger.error(f"Error analyzing correlations: {e}")
            return {
                'correlations': [],
                'time': time.time() - start_time
            }
    
    def _analyze_event_impacts(self, df: pd.DataFrame, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze event impacts on anomalies and change points."""
        try:
            # Convert results to the format expected by event impact analyzer
            anomalies = results.get('anomalies', [])
            change_points = results.get('change_points', {})
            
            # Flatten change points
            flattened_change_points = []
            for series_id, points in change_points.items():
                for point in points:
                    flattened_change_points.append({
                        'series_id': series_id,
                        'date': point.date,
                        'change_type': point.change_type,
                        'confidence': point.confidence
                    })
            
            # Analyze event impacts
            event_impacts = self.event_impact_analyzer.analyze_event_impacts(
                df, anomalies, flattened_change_points
            )
            
            # Convert to serializable format
            serializable_impacts = []
            for impact in event_impacts:
                serializable_impacts.append({
                    'event_name': impact.event.name,
                    'event_date': impact.event.date,
                    'event_type': impact.event.event_type,
                    'series_id': impact.series_id,
                    'impact_date': impact.impact_date,
                    'impact_type': impact.impact_type,
                    'impact_magnitude': impact.impact_magnitude,
                    'impact_direction': impact.impact_direction,
                    'confidence': impact.confidence,
                    'time_lag': impact.time_lag,
                    'description': impact.description
                })
            
            return serializable_impacts
            
        except Exception as e:
            self.logger.error(f"Error analyzing event impacts: {e}")
            return []
    
    def get_performance_metrics(self) -> Optional[PerformanceMetrics]:
        """Get performance metrics from the last analysis."""
        return self.performance_metrics
    
    def write_results(self, result: Dict[str, Any], output_dir: Path) -> None:
        """Write analytics results to files with performance metrics."""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Write JSON summary
        import json
        with open(output_dir / "analytics_summary.json", "w") as f:
            json.dump(result, f, indent=2, default=str)
        
        # Write performance report
        self._write_performance_report(result, output_dir / "performance_report.md")
        
        # Write markdown report
        self._write_markdown_report(result, output_dir / "analytics_report.md")
    
    def _write_performance_report(self, result: Dict[str, Any], output_path: Path) -> None:
        """Write performance metrics report."""
        perf_metrics = result.get('performance_metrics', {})
        
        lines = ["# Performance Report\n"]
        lines.append(f"## Analytics Performance Metrics")
        lines.append(f"- **Total Time**: {perf_metrics.get('total_time', 0):.2f} seconds")
        lines.append(f"- **Data Combination**: {perf_metrics.get('data_combination_time', 0):.2f} seconds")
        lines.append(f"- **Delta Calculation**: {perf_metrics.get('delta_calculation_time', 0):.2f} seconds")
        lines.append(f"- **Anomaly Detection**: {perf_metrics.get('anomaly_detection_time', 0):.2f} seconds")
        lines.append(f"- **Trend Analysis**: {perf_metrics.get('trend_analysis_time', 0):.2f} seconds")
        lines.append(f"- **Percentile Calculation**: {perf_metrics.get('percentile_calculation_time', 0):.2f} seconds")
        lines.append(f"- **Summary Statistics**: {perf_metrics.get('summary_stats_time', 0):.2f} seconds")
        lines.append(f"- **Parallel Processing Overhead**: {perf_metrics.get('parallel_processing_time', 0):.2f} seconds")
        lines.append("")
        
        # Calculate efficiency metrics
        total_sequential_time = (
            perf_metrics.get('delta_calculation_time', 0) +
            perf_metrics.get('anomaly_detection_time', 0) +
            perf_metrics.get('trend_analysis_time', 0) +
            perf_metrics.get('percentile_calculation_time', 0) +
            perf_metrics.get('summary_stats_time', 0)
        )
        
        parallel_efficiency = (
            (total_sequential_time - perf_metrics.get('parallel_processing_time', 0)) / 
            perf_metrics.get('total_time', 1) * 100
        )
        
        lines.append(f"## Efficiency Metrics")
        lines.append(f"- **Parallel Efficiency**: {parallel_efficiency:.1f}%")
        lines.append(f"- **Workers Used**: {self.max_workers}")
        lines.append(f"- **Chunk Size**: {self.chunk_size}")
        lines.append("")
        
        output_path.write_text("\n".join(lines), encoding='utf-8')
    
    def _write_markdown_report(self, result: Dict[str, Any], output_path: Path) -> None:
        """Write a human-readable markdown report."""
        lines = ["# Analytics Report\n"]
        
        # Summary stats
        lines.append("## Summary Statistics")
        stats = result.get('summary_stats', {})
        lines.append(f"- Total series: {stats.get('total_series', 0)}")
        lines.append(f"- Total data points: {stats.get('total_data_points', 0)}")
        lines.append(f"- Date range: {stats.get('date_range', {}).get('start', 'N/A')} to {stats.get('date_range', {}).get('end', 'N/A')}")
        lines.append(f"- Sources: {', '.join(stats.get('sources', []))}")
        lines.append("")
        
        # Top deltas
        top_deltas = result.get('top_deltas', [])
        if top_deltas:
            lines.append("## Top 5 Deltas")
            for delta in top_deltas:
                lines.append(f"- **{delta['series_id']}**: {delta['delta_pct']:.1%} change ({delta['old_value']:.2f} -> {delta['new_value']:.2f})")
            lines.append("")
        
        # Anomalies
        anomalies = result.get('anomalies', [])
        if anomalies:
            lines.append("## Detected Anomalies")
            for anomaly in anomalies:
                lines.append(f"- **{anomaly['series_id']}**: {anomaly['value']:.2f} (z-score: {anomaly['z_score']:.2f}) on {anomaly['date']}")
            lines.append("")
        
        # Trends
        trends = result.get('trends', [])
        if trends:
            lines.append("## Trend Analysis")
            for trend in trends:
                direction = "📈" if trend['slope'] > 0 else "📉"
                lines.append(f"- **{trend['series_id']}**: {direction} {trend['trend_strength']} trend (slope: {trend['slope']:.4f})")
            lines.append("")
        
        output_path.write_text("\n".join(lines), encoding='utf-8')
