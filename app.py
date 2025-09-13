#!/usr/bin/env python3
"""
WeQuo Main Application Entry Point for Render Deployment
Combines both authoring and monitoring dashboards into a single Flask app
"""

import os
import sys
from pathlib import Path
from flask import Flask, render_template_string, redirect, url_for

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from wequo.tools.web_app import create_app as create_authoring_app
from wequo.monitoring.core import MonitoringEngine
from wequo.monitoring.alerts import AlertManager
from wequo.monitoring.sla import SLATracker
from wequo.monitoring.dashboard import MonitoringDashboard
import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_main_app():
    """Create the main Flask application combining all services."""
    app = Flask(__name__)
    
    # Load configuration
    config_path = Path(__file__).parent / "src" / "wequo" / "config.yml"
    with open(config_path, "r") as fh:
        cfg = yaml.safe_load(fh)
    
    # Set up data directories
    output_root = Path(cfg["run"]["output_root"]).resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    
    # Initialize monitoring components
    monitoring_config = cfg.get("monitoring", {})
    monitoring_engine = MonitoringEngine(monitoring_config, output_root)
    alert_manager = AlertManager(monitoring_config, monitoring_engine.monitoring_dir)
    sla_tracker = SLATracker(monitoring_engine, monitoring_config)
    
    # Create authoring app
    authoring_app = create_authoring_app()
    
    # Create monitoring dashboard
    monitoring_dashboard = MonitoringDashboard(
        monitoring_engine, 
        alert_manager, 
        sla_tracker, 
        output_root
    )
    
    # Register blueprints
    app.register_blueprint(authoring_app, url_prefix='/authoring')
    app.register_blueprint(monitoring_dashboard.app, url_prefix='/monitoring')
    
    # Main landing page
    @app.route('/')
    def index():
        return render_template_string(MAIN_TEMPLATE)
    
    # Health check endpoint
    @app.route('/health')
    def health():
        return {"status": "healthy", "service": "wequo"}
    
    return app

# Main landing page template
MAIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WeQuo - Global Risk & Opportunity Platform</title>
    <script src="https://unpkg.com/lucide@latest/dist/umd/lucide.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
            background: linear-gradient(135deg, #1a365d 0%, #2d3748 50%, #4a5568 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
        }
        
        .header {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 24px;
            padding: 60px 50px;
            margin: 40px 20px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
            border: 1px solid rgba(255, 255, 255, 0.2);
            text-align: center;
        }
        
        .header h1 {
            color: #2d3748;
            font-size: 3.5em;
            font-weight: 800;
            margin-bottom: 20px;
            background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .header-subtitle {
            color: #718096;
            font-size: 1.3em;
            margin-bottom: 40px;
            font-weight: 500;
        }
        
        .services-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 30px;
            margin: 40px 20px;
        }
        
        .service-card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: all 0.3s ease;
            text-align: center;
        }
        
        .service-card:hover {
            transform: translateY(-8px);
            box-shadow: 0 25px 70px rgba(0, 0, 0, 0.12);
        }
        
        .service-icon {
            width: 80px;
            height: 80px;
            margin: 0 auto 20px;
            background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%);
            border-radius: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
        }
        
        .service-title {
            color: #2d3748;
            font-size: 1.8em;
            font-weight: 700;
            margin-bottom: 15px;
        }
        
        .service-description {
            color: #718096;
            font-size: 1.1em;
            margin-bottom: 25px;
            line-height: 1.6;
        }
        
        .service-btn {
            display: inline-block;
            background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%);
            color: white;
            padding: 15px 30px;
            border-radius: 12px;
            text-decoration: none;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 4px 16px rgba(45, 55, 72, 0.3);
        }
        
        .service-btn:hover {
            background: linear-gradient(135deg, #1a202c 0%, #2d3748 100%);
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(45, 55, 72, 0.4);
            color: white;
            text-decoration: none;
        }
        
        .features {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 40px;
            margin: 40px 20px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.08);
        }
        
        .features h2 {
            color: #2d3748;
            font-size: 2.2em;
            font-weight: 700;
            margin-bottom: 30px;
            text-align: center;
        }
        
        .features-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
        }
        
        .feature-item {
            display: flex;
            align-items: center;
            gap: 15px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 12px;
        }
        
        .feature-icon {
            width: 24px;
            height: 24px;
            color: #2d3748;
        }
        
        .footer {
            text-align: center;
            padding: 40px 20px;
            color: rgba(255, 255, 255, 0.8);
        }
        
        @media (max-width: 768px) {
            .header h1 {
                font-size: 2.5em;
            }
            
            .services-grid {
                grid-template-columns: 1fr;
                margin: 20px 10px;
            }
            
            .service-card {
                padding: 30px 20px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>
                <i data-lucide="globe"></i>
                WeQuo
            </h1>
            <div class="header-subtitle">
                Global Risk & Opportunity Intelligence Platform
            </div>
        </div>
        
        <div class="services-grid">
            <div class="service-card">
                <div class="service-icon">
                    <i data-lucide="edit-3"></i>
                </div>
                <h3 class="service-title">Authoring Dashboard</h3>
                <p class="service-description">
                    Create and manage weekly briefs with version control, 
                    collaboration tools, and automated data integration.
                </p>
                <a href="/authoring" class="service-btn">
                    <i data-lucide="arrow-right"></i>
                    Open Authoring
                </a>
            </div>
            
            <div class="service-card">
                <div class="service-icon">
                    <i data-lucide="activity"></i>
                </div>
                <h3 class="service-title">Monitoring Dashboard</h3>
                <p class="service-description">
                    Monitor pipeline health, SLA compliance, system alerts, 
                    and search through data packages and analytics.
                </p>
                <a href="/monitoring" class="service-btn">
                    <i data-lucide="arrow-right"></i>
                    Open Monitoring
                </a>
            </div>
        </div>
        
        <div class="features">
            <h2>Platform Features</h2>
            <div class="features-grid">
                <div class="feature-item">
                    <i data-lucide="database" class="feature-icon"></i>
                    <span>Multi-source Data Collection</span>
                </div>
                <div class="feature-item">
                    <i data-lucide="trending-up" class="feature-icon"></i>
                    <span>Advanced Analytics & Anomaly Detection</span>
                </div>
                <div class="feature-item">
                    <i data-lucide="git-branch" class="feature-icon"></i>
                    <span>Version Control & Collaboration</span>
                </div>
                <div class="feature-item">
                    <i data-lucide="shield-check" class="feature-icon"></i>
                    <span>Real-time Monitoring & Alerts</span>
                </div>
                <div class="feature-item">
                    <i data-lucide="search" class="feature-icon"></i>
                    <span>Data Search & Export</span>
                </div>
                <div class="feature-item">
                    <i data-lucide="file-text" class="feature-icon"></i>
                    <span>Automated Report Generation</span>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>WeQuo - Comprehensive data pipeline and authoring system</p>
        </div>
    </div>
    
    <script>
        lucide.createIcons();
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    app = create_main_app()
    
    # Get configuration from environment
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("DEBUG", "false").lower() == "true"
    
    print(f"🚀 Starting WeQuo Platform")
    print(f"📊 Authoring Dashboard: http://{host}:{port}/authoring")
    print(f"📈 Monitoring Dashboard: http://{host}:{port}/monitoring")
    print(f"🔧 Debug mode: {debug}")
    
    app.run(host=host, port=port, debug=debug)
