#!/usr/bin/env python3
"""
Setup script for GitHub Actions secrets and configuration.
This script helps configure the required secrets for the automated pipeline.
"""

import os
import sys
from pathlib import Path

def check_secrets():
    """Check which secrets are configured in GitHub."""
    print("🔍 Checking GitHub Actions secrets configuration...")
    print()
    
    required_secrets = [
        "FRED_API_KEY",
        "ALPHA_VANTAGE_API_KEY", 
        "COINGECKO_API_KEY",
        "GITHUB_TOKEN",
        "OPENWEATHER_API_KEY",
        "SECRET_KEY"
    ]
    
    print("Required secrets for GitHub Actions:")
    for secret in required_secrets:
        print(f"  - {secret}")
    
    print()
    print("To add these secrets to your GitHub repository:")
    print("1. Go to your repository on GitHub")
    print("2. Click 'Settings' tab")
    print("3. Click 'Secrets and variables' → 'Actions'")
    print("4. Click 'New repository secret' for each required secret")
    print("5. Add the secret name and value")
    print()
    
    # Check if we have local .env file
    env_file = Path(".env")
    if env_file.exists():
        print("✅ Found local .env file")
        print("You can copy values from your .env file to GitHub secrets")
    else:
        print("⚠️  No local .env file found")
        print("Make sure to create one with your API keys")

def test_pipeline_locally():
    """Test the pipeline locally before setting up automation."""
    print("🧪 Testing pipeline locally...")
    print()
    
    # Check if virtual environment exists
    venv_path = Path("venv")
    if not venv_path.exists():
        print("❌ Virtual environment not found")
        print("Run: python -m venv venv")
        return False
    
    print("✅ Virtual environment found")
    
    # Check if requirements are installed
    try:
        import pandas
        import requests
        import yaml
        print("✅ Required packages installed")
    except ImportError as e:
        print(f"❌ Missing package: {e}")
        print("Run: pip install -r requirements.txt")
        return False
    
    print()
    print("To test the pipeline locally:")
    print("1. Activate virtual environment: .\\venv\\Scripts\\Activate.ps1")
    print("2. Run pipeline: python scripts/run_weekly.py")
    print("3. Check output in data/output/ directory")
    
    return True

def main():
    """Main setup function."""
    print("🚀 WeQuo GitHub Actions Setup")
    print("=" * 40)
    print()
    
    # Check current directory
    if not Path("scripts/run_weekly.py").exists():
        print("❌ Please run this script from the WeQuo project root directory")
        sys.exit(1)
    
    print("✅ Running from correct directory")
    print()
    
    # Check secrets configuration
    check_secrets()
    
    # Test pipeline locally
    test_pipeline_locally()
    
    print()
    print("🎯 Next Steps:")
    print("1. Add all required secrets to GitHub repository")
    print("2. Test pipeline locally to ensure it works")
    print("3. Push this workflow file to trigger the first run")
    print("4. Monitor the Actions tab for pipeline execution")
    print()
    print("📊 The pipeline will run every Monday at 9 AM UTC")
    print("You can also trigger it manually from the Actions tab")

if __name__ == "__main__":
    main()
