#!/usr/bin/env python3
"""Run the WeQuo author web application."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from wequo.tools.web_app import create_app

if __name__ == "__main__":
    app = create_app()
    
    # Get configuration from environment
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("DEBUG", "false").lower() == "true"
    
    print(f"🚀 Starting WeQuo Author Dashboard")
    print(f"📊 Dashboard: http://{host}:{port}")
    print(f"🔧 Debug mode: {debug}")
    print(f"📁 Data directory: {app.config['OUTPUT_ROOT']}")
    
    app.run(host=host, port=port, debug=debug)
