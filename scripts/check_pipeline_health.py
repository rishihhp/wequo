#!/usr/bin/env python3
"""
Pipeline health check script.
Monitors the health of data connectors and pipeline components.
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # If python-dotenv is not installed, try to load .env manually
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

def check_api_connectivity():
    """Check if API endpoints are accessible."""
    print("🔍 Checking API connectivity...")
    
    apis = {
        "FRED": "https://api.stlouisfed.org/fred/series/observations",
        "CoinGecko": "https://api.coingecko.com/api/v3/ping",
        "Alpha Vantage": "https://www.alphavantage.co/query",
        "World Bank": "https://api.worldbank.org/v2/country"
    }
    
    results = {}
    
    for name, url in apis.items():
        try:
            # Simple ping test
            if name == "CoinGecko":
                response = requests.get(url, timeout=10)
                results[name] = "✅ OK" if response.status_code == 200 else f"❌ HTTP {response.status_code}"
            else:
                # For other APIs, just check if we can reach them
                response = requests.get(url, timeout=10)
                results[name] = "✅ OK" if response.status_code in [200, 400] else f"❌ HTTP {response.status_code}"
        except requests.exceptions.RequestException as e:
            results[name] = f"❌ Error: {str(e)[:50]}"
    
    for name, status in results.items():
        print(f"  {name}: {status}")
    
    return results

def check_data_freshness():
    """Check freshness of recent data outputs."""
    print("\n📅 Checking data freshness...")
    
    output_dir = Path("data/output")
    if not output_dir.exists():
        print("  ❌ No output directory found")
        return False
    
    # Find most recent output
    recent_dirs = [d for d in output_dir.iterdir() if d.is_dir()]
    if not recent_dirs:
        print("  ❌ No output directories found")
        return False
    
    latest_dir = max(recent_dirs, key=lambda x: x.name)
    print(f"  📁 Latest output: {latest_dir.name}")
    
    # Check file ages
    files_to_check = ["fred.csv", "crypto.csv", "commodities.csv", "economic.csv"]
    all_fresh = True
    
    for file_name in files_to_check:
        file_path = latest_dir / file_name
        if file_path.exists():
            # Check if file was created in last 7 days
            file_age = datetime.now() - datetime.fromtimestamp(file_path.stat().st_mtime)
            if file_age.days <= 7:
                print(f"  ✅ {file_name}: {file_age.days} days old")
            else:
                print(f"  ⚠️  {file_name}: {file_age.days} days old (stale)")
                all_fresh = False
        else:
            print(f"  ❌ {file_name}: Missing")
            all_fresh = False
    
    return all_fresh

def check_environment():
    """Check environment configuration."""
    print("\n🔧 Checking environment configuration...")
    
    required_vars = [
        "FRED_API_KEY",
        "ALPHA_VANTAGE_API_KEY", 
        "COINGECKO_API_KEY",
        "SECRET_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        if os.getenv(var):
            print(f"  ✅ {var}: Configured")
        else:
            print(f"  ❌ {var}: Missing")
            missing_vars.append(var)
    
    return len(missing_vars) == 0

def check_dependencies():
    """Check if required Python packages are installed."""
    print("\n📦 Checking dependencies...")
    
    # Map package names to import names (some packages have different import names)
    required_packages = {
        "pandas": "pandas",
        "requests": "requests", 
        "pyyaml": "yaml",
        "tenacity": "tenacity",
        "flask": "flask",
        "plotly": "plotly",
        "scipy": "scipy",
        "numpy": "numpy"
    }
    
    missing_packages = []
    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name)
            print(f"  ✅ {package_name}: Installed")
        except ImportError:
            print(f"  ❌ {package_name}: Missing")
            missing_packages.append(package_name)
    
    return len(missing_packages) == 0

def generate_health_report():
    """Generate a comprehensive health report."""
    print("🏥 WeQuo Pipeline Health Check")
    print("=" * 40)
    
    # Run all checks
    api_status = check_api_connectivity()
    data_fresh = check_data_freshness()
    env_ok = check_environment()
    deps_ok = check_dependencies()
    
    # Summary
    print("\n📊 Health Summary:")
    print("=" * 20)
    
    checks = [
        ("API Connectivity", api_status),
        ("Data Freshness", data_fresh),
        ("Environment", env_ok),
        ("Dependencies", deps_ok)
    ]
    
    all_healthy = True
    for check_name, status in checks:
        if isinstance(status, dict):
            # For API connectivity, check if any failed
            failed_apis = [name for name, result in status.items() if "❌" in result]
            if failed_apis:
                print(f"  ⚠️  {check_name}: {len(failed_apis)} APIs failed")
                all_healthy = False
            else:
                print(f"  ✅ {check_name}: All APIs healthy")
        elif status:
            print(f"  ✅ {check_name}: OK")
        else:
            print(f"  ❌ {check_name}: Issues found")
            all_healthy = False
    
    print()
    if all_healthy:
        print("🎉 Pipeline is healthy and ready!")
    else:
        print("⚠️  Pipeline has issues that need attention")
    
    return all_healthy

def main():
    """Main health check function."""
    # Check if we're in the right directory
    if not Path("scripts/run_weekly.py").exists():
        print("❌ Please run this script from the WeQuo project root directory")
        sys.exit(1)
    
    healthy = generate_health_report()
    
    # Exit with appropriate code
    sys.exit(0 if healthy else 1)

if __name__ == "__main__":
    main()
