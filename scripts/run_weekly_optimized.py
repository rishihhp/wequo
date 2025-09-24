#!/usr/bin/env python3
"""
Optimized WeQuo Weekly Pipeline Runner

Enhanced version with performance optimizations for larger datasets.
"""

from __future__ import annotations
import os
import sys
import time
import logging
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pandas as pd
import yaml
from dotenv import load_dotenv

from wequo.utils.dates import daterange_lookback
from wequo.utils.io import ensure_dir, write_df_csv, write_md
from wequo.connectors.fred import FredConnector
from wequo.connectors.commodities import CommoditiesConnector
from wequo.connectors.crypto import CryptoConnector
from wequo.connectors.github import GitHubConnector
from wequo.connectors.weather import WeatherConnector
from wequo.connectors.economic import EconomicConnector
from wequo.aggregate_optimized import OptimizedAggregator
from wequo import validate as v


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('pipeline_optimized.log')
        ]
    )


def main() -> int:
    """Main optimized pipeline function."""
    start_time = time.time()
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting optimized WeQuo weekly pipeline...")
    
    load_dotenv()
    with open("src/wequo/config.yml", "r") as fh:
        cfg = yaml.safe_load(fh)

    output_root = Path(cfg["run"]["output_root"]).resolve()
    lookback_days = int(cfg["run"].get("lookback_days", 7))
    start, end = daterange_lookback(lookback_days)

    outdir = output_root / end
    ensure_dir(outdir)

    frames: dict[str, pd.DataFrame] = {}
    connector_times = {}

    # FRED
    if cfg["connectors"]["fred"]["enabled"]:
        logger.info("Fetching FRED data...")
        connector_start = time.time()
        try:
            fred = FredConnector(
                series_ids=cfg["connectors"]["fred"]["series_ids"],
                api_key=os.environ.get("FRED_API_KEY", ""),
                lookback_start=start,
                lookback_end=end,
            )
            fdf = fred.normalize(fred.fetch())
            frames["fred"] = fdf
            write_df_csv(outdir / "fred.csv", fdf)
            connector_times["fred"] = time.time() - connector_start
            logger.info(f"FRED data fetched in {connector_times['fred']:.2f}s: {len(fdf)} rows")
        except Exception as e:
            logger.error(f"Error fetching FRED data: {e}")
            connector_times["fred"] = time.time() - connector_start

    # Commodities
    if cfg["connectors"]["commodities"]["enabled"]:
        logger.info("Fetching commodities data...")
        connector_start = time.time()
        try:
            commodities = CommoditiesConnector(
                api_key=os.environ.get("ALPHA_VANTAGE_API_KEY", ""),
                symbols=cfg["connectors"]["commodities"]["symbols"],
                lookback_days=lookback_days,
            )
            cdf = commodities.normalize(commodities.fetch())
            frames["commodities"] = cdf
            write_df_csv(outdir / "commodities.csv", cdf)
            connector_times["commodities"] = time.time() - connector_start
            logger.info(f"Commodities data fetched in {connector_times['commodities']:.2f}s: {len(cdf)} rows")
        except Exception as e:
            logger.error(f"Error fetching commodities data: {e}")
            connector_times["commodities"] = time.time() - connector_start

    # Crypto
    if cfg["connectors"]["crypto"]["enabled"]:
        logger.info("Fetching crypto data...")
        connector_start = time.time()
        try:
            crypto = CryptoConnector(
                symbols=cfg["connectors"]["crypto"]["symbols"],
                lookback_days=lookback_days,
                api_key=os.environ.get("COINGECKO_API_KEY", ""),
            )
            crdf = crypto.normalize(crypto.fetch())
            frames["crypto"] = crdf
            write_df_csv(outdir / "crypto.csv", crdf)
            connector_times["crypto"] = time.time() - connector_start
            logger.info(f"Crypto data fetched in {connector_times['crypto']:.2f}s: {len(crdf)} rows")
        except Exception as e:
            logger.error(f"Error fetching crypto data: {e}")
            connector_times["crypto"] = time.time() - connector_start

    # GitHub (disabled by default - requires API setup)
    if cfg["connectors"]["github"]["enabled"]:
        logger.info("Fetching GitHub data...")
        connector_start = time.time()
        try:
            github = GitHubConnector(
                api_key=os.environ.get("GITHUB_TOKEN", ""),
                repos=cfg["connectors"]["github"]["repos"],
                lookback_days=lookback_days,
            )
            gdf = github.normalize(github.fetch())
            frames["github"] = gdf
            write_df_csv(outdir / "github.csv", gdf)
            connector_times["github"] = time.time() - connector_start
            logger.info(f"GitHub data fetched in {connector_times['github']:.2f}s: {len(gdf)} rows")
        except Exception as e:
            logger.error(f"Error fetching GitHub data: {e}")
            connector_times["github"] = time.time() - connector_start

    # Weather (disabled by default - requires API setup)
    if cfg["connectors"]["weather"]["enabled"]:
        logger.info("Fetching weather data...")
        connector_start = time.time()
        try:
            weather = WeatherConnector(
                api_key=os.environ.get("OPENWEATHER_API_KEY", ""),
                cities=cfg["connectors"]["weather"]["cities"],
                lookback_days=lookback_days,
            )
            wdf = weather.normalize(weather.fetch())
            frames["weather"] = wdf
            write_df_csv(outdir / "weather.csv", wdf)
            connector_times["weather"] = time.time() - connector_start
            logger.info(f"Weather data fetched in {connector_times['weather']:.2f}s: {len(wdf)} rows")
        except Exception as e:
            logger.error(f"Error fetching weather data: {e}")
            connector_times["weather"] = time.time() - connector_start

    # Economic
    if cfg["connectors"]["economic"]["enabled"]:
        logger.info("Fetching economic data...")
        connector_start = time.time()
        try:
            economic = EconomicConnector(
                indicators=cfg["connectors"]["economic"]["indicators"],
                countries=cfg["connectors"]["economic"]["countries"],
                lookback_days=lookback_days,
            )
            edf = economic.normalize(economic.fetch())
            frames["economic"] = edf
            write_df_csv(outdir / "economic.csv", edf)
            connector_times["economic"] = time.time() - connector_start
            logger.info(f"Economic data fetched in {connector_times['economic']:.2f}s: {len(edf)} rows")
        except Exception as e:
            logger.error(f"Error fetching economic data: {e}")
            connector_times["economic"] = time.time() - connector_start

    # Validation
    logger.info("Running validation...")
    validation_start = time.time()
    results = v.validate_frames(frames)
    validation_time = time.time() - validation_start
    
    report_lines = ["# QA Report\n"]
    for r in results:
        report_lines.append(f"- {r.name}: rows={r.rows}, latest_date={r.latest_date}")
    
    # Add performance metrics to QA report
    report_lines.append(f"\n## Performance Metrics")
    report_lines.append(f"- Validation time: {validation_time:.2f}s")
    report_lines.append(f"- Total connector time: {sum(connector_times.values()):.2f}s")
    for connector, time_taken in connector_times.items():
        report_lines.append(f"  - {connector}: {time_taken:.2f}s")
    
    write_md(outdir / "qa_report.md", "\n".join(report_lines))

    # Aggregation with optimized analytics
    logger.info("Running optimized analytics and aggregation...")
    analytics_enabled = cfg.get("analytics", {}).get("enabled", True)
    
    # Get optimization settings from config
    max_workers = cfg.get("optimization", {}).get("max_workers", None)
    chunk_size = cfg.get("optimization", {}).get("chunk_size", 10000)
    
    agg = OptimizedAggregator(
        outdir, 
        analytics_enabled=analytics_enabled,
        max_workers=max_workers,
        chunk_size=chunk_size
    )
    
    summary = agg.summarize(frames)
    agg.write_prefill(summary)

    total_time = time.time() - start_time
    logger.info(f"Optimized pipeline completed in {total_time:.2f}s")
    logger.info(f"Wrote weekly package to {outdir}")
    
    # Log performance summary
    perf_metrics = summary.get("performance_metrics", {})
    if perf_metrics:
        logger.info("Performance Summary:")
        logger.info(f"  - Total time: {total_time:.2f}s")
        logger.info(f"  - Analytics time: {perf_metrics.get('analytics_time', 0):.2f}s")
        logger.info(f"  - Latest values time: {perf_metrics.get('latest_values_time', 0):.2f}s")
        
        analytics_breakdown = perf_metrics.get("analytics_breakdown", {})
        if analytics_breakdown:
            logger.info("  - Analytics breakdown:")
            logger.info(f"    - Delta calculation: {analytics_breakdown.get('delta_calculation_time', 0):.2f}s")
            logger.info(f"    - Anomaly detection: {analytics_breakdown.get('anomaly_detection_time', 0):.2f}s")
            logger.info(f"    - Trend analysis: {analytics_breakdown.get('trend_analysis_time', 0):.2f}s")
            logger.info(f"    - Percentile calculation: {analytics_breakdown.get('percentile_calculation_time', 0):.2f}s")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
