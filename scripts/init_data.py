#!/usr/bin/env python3
"""
Data initialization script for Render deployment.
Creates necessary directories and initial data structures.
"""

import os
import sys
from pathlib import Path
import json
from datetime import datetime

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def init_data_directories():
    """Initialize data directories and basic structure."""
    print("🔧 Initializing data directories...")
    
    # Create main data directory
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # Create subdirectories
    directories = [
        "data/output",
        "data/authoring/documents",
        "data/authoring/metadata", 
        "data/authoring/versions",
        "data/monitoring/alerts",
        "data/monitoring/sla",
        "data/search"
    ]
    
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"  ✅ Created: {dir_path}")
    
    # Create initial search index
    search_dir = Path("data/search")
    if not (search_dir / "documents.jsonl").exists():
        with open(search_dir / "documents.jsonl", "w") as f:
            f.write("")  # Empty file
        print("  ✅ Created: data/search/documents.jsonl")
    
    if not (search_dir / "stats.json").exists():
        initial_stats = {
            "total_documents": 0,
            "total_sources": 0,
            "index_size_mb": 0.0,
            "last_updated": datetime.now().isoformat()
        }
        with open(search_dir / "stats.json", "w") as f:
            json.dump(initial_stats, f, indent=2)
        print("  ✅ Created: data/search/stats.json")

def create_sample_data():
    """Create sample data for demonstration."""
    print("📊 Creating sample data...")
    
    # Create a sample output directory with today's date
    today = datetime.now().strftime("%Y-%m-%d")
    sample_dir = Path(f"data/output/{today}")
    sample_dir.mkdir(parents=True, exist_ok=True)
    
    # Create sample package summary
    sample_summary = {
        "timestamp": datetime.now().isoformat(),
        "sources": ["fred", "commodities", "crypto"],
        "total_data_points": 150,
        "analytics": {
            "anomalies_detected": 3,
            "trends_identified": 5,
            "correlations_found": 2
        }
    }
    
    with open(sample_dir / "package_summary.json", "w") as f:
        json.dump(sample_summary, f, indent=2)
    
    # Create sample QA report
    qa_report = """# QA Report

## Data Quality Summary
- FRED: 50 data points, latest: 2025-01-15
- Commodities: 50 data points, latest: 2025-01-15  
- Crypto: 50 data points, latest: 2025-01-15

## Validation Results
- All data sources: ✅ Valid
- Data freshness: ✅ Within 24 hours
- Format compliance: ✅ Passed

## Recommendations
- Continue monitoring data quality
- Consider adding additional data sources
"""
    
    with open(sample_dir / "qa_report.md", "w") as f:
        f.write(qa_report)
    
    # Create sample prefill notes
    prefill_notes = """# Prefill Notes

## Key Insights
- Economic indicators show stable growth
- Commodity prices trending upward
- Crypto market showing increased volatility

## Notable Changes
- Federal funds rate unchanged at 5.25%
- Oil prices up 2.3% this week
- Bitcoin trading above $45,000

## Risk Factors
- Geopolitical tensions in key regions
- Supply chain disruptions continuing
- Inflation concerns persist
"""
    
    with open(sample_dir / "prefill_notes.md", "w") as f:
        f.write(prefill_notes)
    
    print(f"  ✅ Created sample data in: {sample_dir}")

def create_env_template():
    """Create environment template if it doesn't exist."""
    print("🔑 Setting up environment configuration...")
    
    env_file = Path(".env")
    if not env_file.exists():
        env_example = Path("env.example")
        if env_example.exists():
            # Copy example to .env
            with open(env_example, "r") as f:
                content = f.read()
            with open(env_file, "w") as f:
                f.write(content)
            print("  ✅ Created .env from env.example")
        else:
            # Create basic .env
            basic_env = """# WeQuo Environment Configuration
# Copy this file and fill in your API keys

# Required API Keys
FRED_API_KEY=your_fred_api_key_here

# Optional API Keys (uncomment and fill as needed)
# ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here
# ACLED_API_KEY=your_acled_api_key
# ACLED_EMAIL=your_registered_email@example.com
# NOAA_API_KEY=your_noaa_api_key
# UNCOMTRADE_API_KEY=your_uncomtrade_subscription_key
# MARINETRAFFIC_API_KEY=your_marinetraffic_api_key

# Web App Configuration
SECRET_KEY=your_secret_key_here
HOST=0.0.0.0
PORT=5000
DEBUG=false
"""
            with open(env_file, "w") as f:
                f.write(basic_env)
            print("  ✅ Created basic .env file")

def main():
    """Main initialization function."""
    print("🚀 Initializing WeQuo for deployment...")
    
    try:
        init_data_directories()
        create_sample_data()
        create_env_template()
        
        print("\n✅ Initialization complete!")
        print("📁 Data directories created")
        print("📊 Sample data generated")
        print("🔑 Environment configuration ready")
        print("\n🌐 Ready to start the application!")
        
    except Exception as e:
        print(f"\n❌ Initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
