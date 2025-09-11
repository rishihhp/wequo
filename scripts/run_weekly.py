from __future__ import annotations
import os
import sys
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
from wequo.aggregate import Aggregator
from wequo import validate as v


def main() -> int:
    load_dotenv()
    with open("src/wequo/config.yml", "r") as fh:
        cfg = yaml.safe_load(fh)

    output_root = Path(cfg["run"]["output_root"]).resolve()
    lookback_days = int(cfg["run"].get("lookback_days", 7))
    start, end = daterange_lookback(lookback_days)

    outdir = output_root / end
    ensure_dir(outdir)

    frames: dict[str, pd.DataFrame] = {}

    # FRED
    if cfg["connectors"]["fred"]["enabled"]:
        print("Fetching FRED data...")
        fred = FredConnector(
            series_ids=cfg["connectors"]["fred"]["series_ids"],
            api_key=os.environ.get("FRED_API_KEY", ""),
            lookback_start=start,
            lookback_end=end,
        )
        fdf = fred.normalize(fred.fetch())
        frames["fred"] = fdf
        write_df_csv(outdir / "fred.csv", fdf)

    # Commodities
    if cfg["connectors"]["commodities"]["enabled"]:
        print("Fetching commodities data...")
        commodities = CommoditiesConnector(
            api_key=os.environ.get("ALPHA_VANTAGE_API_KEY", ""),
            symbols=cfg["connectors"]["commodities"]["symbols"],
            lookback_days=lookback_days,
        )
        cdf = commodities.normalize(commodities.fetch())
        frames["commodities"] = cdf
        write_df_csv(outdir / "commodities.csv", cdf)

    # Crypto
    if cfg["connectors"]["crypto"]["enabled"]:
        print("Fetching crypto data...")
        crypto = CryptoConnector(
            symbols=cfg["connectors"]["crypto"]["symbols"],
            lookback_days=lookback_days,
        )
        crdf = crypto.normalize(crypto.fetch())
        frames["crypto"] = crdf
        write_df_csv(outdir / "crypto.csv", crdf)

    # GitHub (disabled by default - requires API setup)
    if cfg["connectors"]["github"]["enabled"]:
        print("Fetching GitHub data...")
        github = GitHubConnector(
            api_key=os.environ.get("GITHUB_TOKEN", ""),
            repos=cfg["connectors"]["github"]["repos"],
            lookback_days=lookback_days,
        )
        gdf = github.normalize(github.fetch())
        frames["github"] = gdf
        write_df_csv(outdir / "github.csv", gdf)

    # Weather (disabled by default - requires API setup)
    if cfg["connectors"]["weather"]["enabled"]:
        print("Fetching weather data...")
        weather = WeatherConnector(
            api_key=os.environ.get("OPENWEATHER_API_KEY", ""),
            cities=cfg["connectors"]["weather"]["cities"],
            lookback_days=lookback_days,
        )
        wdf = weather.normalize(weather.fetch())
        frames["weather"] = wdf
        write_df_csv(outdir / "weather.csv", wdf)

    # Economic
    if cfg["connectors"]["economic"]["enabled"]:
        print("Fetching economic data...")
        economic = EconomicConnector(
            indicators=cfg["connectors"]["economic"]["indicators"],
            countries=cfg["connectors"]["economic"]["countries"],
            lookback_days=lookback_days,
        )
        edf = economic.normalize(economic.fetch())
        frames["economic"] = edf
        write_df_csv(outdir / "economic.csv", edf)

    # Validation
    print("Running validation...")
    results = v.validate_frames(frames)
    report_lines = ["# QA Report\n"]
    for r in results:
        report_lines.append(f"- {r.name}: rows={r.rows}, latest_date={r.latest_date}")
    write_md(outdir / "qa_report.md", "\n".join(report_lines))

    # Aggregation with analytics
    print("Running analytics and aggregation...")
    analytics_enabled = cfg.get("analytics", {}).get("enabled", True)
    agg = Aggregator(outdir, analytics_enabled=analytics_enabled)
    summary = agg.summarize(frames)
    agg.write_prefill(summary)

    print(f"Wrote weekly package to {outdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())