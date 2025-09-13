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
from wequo.connectors.acled import ACLEDConnector
from wequo.connectors.fao import FAOConnector
from wequo.connectors.noaa import NOAAConnector
from wequo.connectors.uncomtrade import UNComtradeConnector
from wequo.connectors.shipping_ais import ShippingAISConnector
from wequo.aggregate import Aggregator
from wequo import validate as v
from wequo.monitoring.core import MonitoringEngine
from wequo.monitoring.alerts import AlertManager
from wequo.monitoring.sla import SLATracker
from wequo.metadata import MetadataTracker, add_metadata_to_dataframe


def main() -> int:
    load_dotenv()
    with open("src/wequo/config.yml", "r") as fh:
        cfg = yaml.safe_load(fh)

    output_root = Path(cfg["run"]["output_root"]).resolve()
    lookback_days = int(cfg["run"].get("lookback_days", 7))
    start, end = daterange_lookback(lookback_days)

    outdir = output_root / end
    ensure_dir(outdir)

    # Initialize monitoring
    monitoring_config = cfg.get("monitoring", {})
    monitoring_enabled = monitoring_config.get("enabled", True)
    
    if monitoring_enabled:
        print("Initializing monitoring system...")
        monitoring_engine = MonitoringEngine(monitoring_config, output_root)
        alert_manager = AlertManager(monitoring_config, monitoring_engine.monitoring_dir)
        sla_tracker = SLATracker(monitoring_engine, monitoring_config)
        
        # Start pipeline run monitoring
        connectors_to_run = [name for name, config in cfg["connectors"].items() if config.get("enabled", False)]
        run_id = monitoring_engine.start_pipeline_run(connectors_to_run)
        print(f"Monitoring directory created at: {monitoring_engine.monitoring_dir}")
    else:
        print("Monitoring is disabled in configuration")
        monitoring_engine = None
        alert_manager = None
        sla_tracker = None
        run_id = None
    
    frames: dict[str, pd.DataFrame] = {}
    connectors_succeeded = []
    connectors_failed = []
    errors = []
    total_data_points = 0
    
    # Initialize metadata tracker for provenance
    metadata_tracker = MetadataTracker()

    # FRED
    if cfg["connectors"]["fred"]["enabled"]:
        try:
            print("Fetching FRED data...")
            fred = FredConnector(
                series_ids=cfg["connectors"]["fred"]["series_ids"],
                api_key=os.environ.get("FRED_API_KEY", ""),
                lookback_start=start,
                lookback_end=end,
            )
            fdf = fred.normalize(fred.fetch())
            
            # Add metadata tracking for FRED data
            fdf_with_metadata = add_metadata_to_dataframe(fdf, metadata_tracker, "fred")
            
            # Add connector-specific provenance info
            for idx, row in fdf_with_metadata.iterrows():
                if "metadata_id" in row:
                    metadata = metadata_tracker.get_metadata(row["metadata_id"])
                    if metadata:
                        metadata.api_endpoint = "https://api.stlouisfed.org/fred/series/observations"
                        metadata.source_url = f"https://fred.stlouisfed.org/series/{row.get('series_id', '')}"
                        metadata.data_license = "Public Domain"
                        metadata.terms_of_service_url = "https://fred.stlouisfed.org/legal/"
                        metadata.api_version = "v1"
                        metadata.data_transformation_log.append("FRED API response normalized to standard format")
                        metadata.pipeline_run_id = run_id
            
            frames["fred"] = fdf_with_metadata
            write_df_csv(outdir / "fred.csv", fdf_with_metadata)
            connectors_succeeded.append("fred")
            total_data_points += len(fdf_with_metadata)
        except Exception as e:
            connectors_failed.append("fred")
            errors.append(f"FRED connector failed: {str(e)}")
            print(f"Error in FRED connector: {e}")

    # Commodities
    if cfg["connectors"]["commodities"]["enabled"]:
        try:
            print("Fetching commodities data...")
            commodities = CommoditiesConnector(
                api_key=os.environ.get("ALPHA_VANTAGE_API_KEY", ""),
                symbols=cfg["connectors"]["commodities"]["symbols"],
                lookback_days=lookback_days,
            )
            cdf = commodities.normalize(commodities.fetch())
            frames["commodities"] = cdf
            write_df_csv(outdir / "commodities.csv", cdf)
            connectors_succeeded.append("commodities")
            total_data_points += len(cdf)
        except Exception as e:
            connectors_failed.append("commodities")
            errors.append(f"Commodities connector failed: {str(e)}")
            print(f"Error in Commodities connector: {e}")

    # Crypto
    if cfg["connectors"]["crypto"]["enabled"]:
        try:
            print("Fetching crypto data...")
            crypto = CryptoConnector(
                symbols=cfg["connectors"]["crypto"]["symbols"],
                lookback_days=lookback_days,
            )
            crdf = crypto.normalize(crypto.fetch())
            frames["crypto"] = crdf
            write_df_csv(outdir / "crypto.csv", crdf)
            connectors_succeeded.append("crypto")
            total_data_points += len(crdf)
        except Exception as e:
            connectors_failed.append("crypto")
            errors.append(f"Crypto connector failed: {str(e)}")
            print(f"Error in Crypto connector: {e}")

    # GitHub (disabled by default - requires API setup)
    if cfg["connectors"]["github"]["enabled"]:
        try:
            print("Fetching GitHub data...")
            github = GitHubConnector(
                api_key=os.environ.get("GITHUB_TOKEN", ""),
                repos=cfg["connectors"]["github"]["repos"],
                lookback_days=lookback_days,
            )
            gdf = github.normalize(github.fetch())
            frames["github"] = gdf
            write_df_csv(outdir / "github.csv", gdf)
            connectors_succeeded.append("github")
            total_data_points += len(gdf)
        except Exception as e:
            connectors_failed.append("github")
            errors.append(f"GitHub connector failed: {str(e)}")
            print(f"Error in GitHub connector: {e}")

    # Weather (disabled by default - requires API setup)
    if cfg["connectors"]["weather"]["enabled"]:
        try:
            print("Fetching weather data...")
            weather = WeatherConnector(
                api_key=os.environ.get("OPENWEATHER_API_KEY", ""),
                cities=cfg["connectors"]["weather"]["cities"],
                lookback_days=lookback_days,
            )
            wdf = weather.normalize(weather.fetch())
            frames["weather"] = wdf
            write_df_csv(outdir / "weather.csv", wdf)
            connectors_succeeded.append("weather")
            total_data_points += len(wdf)
        except Exception as e:
            connectors_failed.append("weather")
            errors.append(f"Weather connector failed: {str(e)}")
            print(f"Error in Weather connector: {e}")

    # Economic
    if cfg["connectors"]["economic"]["enabled"]:
        try:
            print("Fetching economic data...")
            economic = EconomicConnector(
                indicators=cfg["connectors"]["economic"]["indicators"],
                countries=cfg["connectors"]["economic"]["countries"],
                lookback_days=lookback_days,
            )
            edf = economic.normalize(economic.fetch())
            frames["economic"] = edf
            write_df_csv(outdir / "economic.csv", edf)
            connectors_succeeded.append("economic")
            total_data_points += len(edf)
        except Exception as e:
            connectors_failed.append("economic")
            errors.append(f"Economic connector failed: {str(e)}")
            print(f"Error in Economic connector: {e}")

    # ACLED (conflict and crisis data)
    if cfg["connectors"]["acled"]["enabled"]:
        try:
            print("Fetching ACLED data...")
            acled = ACLEDConnector(
                api_key=os.environ.get("ACLED_API_KEY", ""),
                email=os.environ.get("ACLED_EMAIL", ""),
                countries=cfg["connectors"]["acled"]["countries"],
                event_types=cfg["connectors"]["acled"]["event_types"],
                lookback_days=lookback_days,
            )
            adf = acled.normalize(acled.fetch())
            frames["acled"] = adf
            write_df_csv(outdir / "acled.csv", adf)
            connectors_succeeded.append("acled")
            total_data_points += len(adf)
        except Exception as e:
            connectors_failed.append("acled")
            errors.append(f"ACLED connector failed: {str(e)}")
            print(f"Error in ACLED connector: {e}")

    # FAO (food and agriculture data)
    if cfg["connectors"]["fao"]["enabled"]:
        try:
            print("Fetching FAO data...")
            fao = FAOConnector(
                indicators=cfg["connectors"]["fao"]["indicators"],
                countries=cfg["connectors"]["fao"]["countries"],
                lookback_years=5,
            )
            fdf = fao.normalize(fao.fetch())
            frames["fao"] = fdf
            write_df_csv(outdir / "fao.csv", fdf)
            connectors_succeeded.append("fao")
            total_data_points += len(fdf)
        except Exception as e:
            connectors_failed.append("fao")
            errors.append(f"FAO connector failed: {str(e)}")
            print(f"Error in FAO connector: {e}")

    # NOAA (climate and weather data)
    if cfg["connectors"]["noaa"]["enabled"]:
        try:
            print("Fetching NOAA data...")
            noaa = NOAAConnector(
                api_key=os.environ.get("NOAA_API_KEY", ""),
                datasets=cfg["connectors"]["noaa"]["datasets"],
                stations=cfg["connectors"]["noaa"]["stations"],
                datatypes=cfg["connectors"]["noaa"]["datatypes"],
                lookback_days=lookback_days,
            )
            ndf = noaa.normalize(noaa.fetch())
            frames["noaa"] = ndf
            write_df_csv(outdir / "noaa.csv", ndf)
            connectors_succeeded.append("noaa")
            total_data_points += len(ndf)
        except Exception as e:
            connectors_failed.append("noaa")
            errors.append(f"NOAA connector failed: {str(e)}")
            print(f"Error in NOAA connector: {e}")

    # UN Comtrade (international trade data)
    if cfg["connectors"]["uncomtrade"]["enabled"]:
        try:
            print("Fetching UN Comtrade data...")
            uncomtrade = UNComtradeConnector(
                subscription_key=os.environ.get("UNCOMTRADE_API_KEY", ""),
                reporters=cfg["connectors"]["uncomtrade"]["reporters"],
                partners=cfg["connectors"]["uncomtrade"]["partners"],
                commodities=cfg["connectors"]["uncomtrade"]["commodities"],
                trade_flows=cfg["connectors"]["uncomtrade"]["trade_flows"],
                lookback_years=3,
            )
            udf = uncomtrade.normalize(uncomtrade.fetch())
            frames["uncomtrade"] = udf
            write_df_csv(outdir / "uncomtrade.csv", udf)
            connectors_succeeded.append("uncomtrade")
            total_data_points += len(udf)
        except Exception as e:
            connectors_failed.append("uncomtrade")
            errors.append(f"UN Comtrade connector failed: {str(e)}")
            print(f"Error in UN Comtrade connector: {e}")

    # Shipping AIS (maritime traffic data)
    if cfg["connectors"]["shipping_ais"]["enabled"]:
        try:
            print("Fetching Shipping AIS data...")
            shipping_ais = ShippingAISConnector(
                api_key=os.environ.get("MARINETRAFFIC_API_KEY", ""),
                vessel_types=cfg["connectors"]["shipping_ais"]["vessel_types"],
                ports=cfg["connectors"]["shipping_ais"]["ports"],
                areas=cfg["connectors"]["shipping_ais"]["areas"],
                lookback_days=lookback_days,
            )
            sdf = shipping_ais.normalize(shipping_ais.fetch())
            frames["shipping_ais"] = sdf
            write_df_csv(outdir / "shipping_ais.csv", sdf)
            connectors_succeeded.append("shipping_ais")
            total_data_points += len(sdf)
        except Exception as e:
            connectors_failed.append("shipping_ais")
            errors.append(f"Shipping AIS connector failed: {str(e)}")
            print(f"Error in Shipping AIS connector: {e}")

    # Validation
    print("Running validation...")
    results = v.validate_frames(frames)
    report_lines = ["# QA Report\n"]
    for r in results:
        report_lines.append(f"- {r.name}: rows={r.rows}, latest_date={r.latest_date}")
    write_md(outdir / "qa_report.md", "\n".join(report_lines))

    # Aggregation with analytics and provenance
    print("Running analytics and aggregation...")
    analytics_enabled = cfg.get("analytics", {}).get("enabled", True)
    agg = Aggregator(outdir, analytics_enabled=analytics_enabled, metadata_tracker=metadata_tracker)
    summary = agg.summarize(frames, metadata_tracker=metadata_tracker)
    agg.write_prefill(summary)

    print(f"Wrote weekly package to {outdir}")
    
    # Complete pipeline run monitoring
    if monitoring_enabled and monitoring_engine:
        try:
            status = "success" if not connectors_failed else "partial_failure" if connectors_succeeded else "failure"
            pipeline_run = monitoring_engine.finish_pipeline_run(
                run_id=run_id,
                status=status,
                connectors_succeeded=connectors_succeeded,
                connectors_failed=connectors_failed,
                data_points=total_data_points,
                errors=errors,
                output_dir=str(outdir)
            )
            
            # Generate monitoring report and check for alerts
            monitoring_result = monitoring_engine.generate_monitoring_report()
            monitoring_result.pipeline_run = pipeline_run
            
            # Check for alerts
            alerts = alert_manager.check_and_alert(monitoring_result)
            if alerts:
                print(f"Generated {len(alerts)} alerts")
            else:
                print("No alerts generated")
            
            print("Monitoring completed successfully")
            
        except Exception as e:
            print(f"Warning: Monitoring failed: {e}")
    else:
        print("Monitoring was disabled, skipping monitoring completion")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())