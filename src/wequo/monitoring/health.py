"""
Health checking functionality for WeQuo connectors and services.
"""

import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

import requests
import pandas as pd


@dataclass
class HealthCheckResult:
    """Result of a health check."""
    name: str
    status: str  # "healthy", "degraded", "unhealthy"
    response_time_ms: float
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class HealthChecker:
    """
    Health checker for WeQuo connectors and external services.
    
    Performs:
    - API connectivity tests
    - Data freshness checks
    - Service availability tests
    - Performance monitoring
    """
    
    def __init__(self, config_path: str = "src/wequo/config.yml",
                 output_root: str = "data/output"):
        self.config_path = Path(config_path)
        self.output_root = Path(output_root)
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Load configuration
        import yaml
        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)
    
    def check_all_connectors(self) -> List[HealthCheckResult]:
        """Check health of all enabled connectors."""
        results = []
        
        connectors = self.config.get('connectors', {})
        for connector_name, connector_config in connectors.items():
            if not connector_config.get('enabled', False):
                continue
            
            try:
                result = self._check_connector(connector_name, connector_config)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Error checking {connector_name}: {e}")
                results.append(HealthCheckResult(
                    name=connector_name,
                    status="unhealthy",
                    response_time_ms=0.0,
                    error_message=str(e)
                ))
        
        return results
    
    def _check_connector(self, name: str, config: Dict[str, Any]) -> HealthCheckResult:
        """Check health of a specific connector."""
        start_time = time.time()
        
        try:
            if name == "fred":
                return self._check_fred_connector(start_time)
            elif name == "commodities":
                return self._check_commodities_connector(start_time)
            elif name == "crypto":
                return self._check_crypto_connector(start_time)
            elif name == "economic":
                return self._check_economic_connector(start_time)
            elif name == "github":
                return self._check_github_connector(start_time)
            elif name == "weather":
                return self._check_weather_connector(start_time)
            else:
                return HealthCheckResult(
                    name=name,
                    status="unhealthy",
                    response_time_ms=(time.time() - start_time) * 1000,
                    error_message=f"Unknown connector: {name}"
                )
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                name=name,
                status="unhealthy",
                response_time_ms=response_time,
                error_message=str(e)
            )
    
    def _check_fred_connector(self, start_time: float) -> HealthCheckResult:
        """Check FRED API health."""
        try:
            # Test FRED API connectivity
            url = "https://api.stlouisfed.org/fred/series"
            params = {
                'series_id': 'GDP',
                'api_key': 'test',  # We'll get a real key from env
                'file_type': 'json'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                return HealthCheckResult(
                    name="fred",
                    status="healthy",
                    response_time_ms=response_time,
                    details={"api_status": "accessible"}
                )
            elif response.status_code == 400:  # Bad API key is expected
                return HealthCheckResult(
                    name="fred",
                    status="healthy",
                    response_time_ms=response_time,
                    details={"api_status": "accessible", "note": "API key needed"}
                )
            else:
                return HealthCheckResult(
                    name="fred",
                    status="degraded",
                    response_time_ms=response_time,
                    error_message=f"HTTP {response.status_code}"
                )
                
        except requests.exceptions.Timeout:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                name="fred",
                status="unhealthy",
                response_time_ms=response_time,
                error_message="Request timeout"
            )
        except requests.exceptions.ConnectionError:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                name="fred",
                status="unhealthy",
                response_time_ms=response_time,
                error_message="Connection error"
            )
    
    def _check_commodities_connector(self, start_time: float) -> HealthCheckResult:
        """Check Alpha Vantage API health."""
        try:
            # Test Alpha Vantage API connectivity
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'TIME_SERIES_DAILY',
                'symbol': 'AAPL',
                'apikey': 'test'  # We'll get a real key from env
            }
            
            response = requests.get(url, params=params, timeout=10)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                if 'Error Message' in data:
                    return HealthCheckResult(
                        name="commodities",
                        status="healthy",
                        response_time_ms=response_time,
                        details={"api_status": "accessible", "note": "API key needed"}
                    )
                else:
                    return HealthCheckResult(
                        name="commodities",
                        status="healthy",
                        response_time_ms=response_time,
                        details={"api_status": "accessible"}
                    )
            else:
                return HealthCheckResult(
                    name="commodities",
                    status="degraded",
                    response_time_ms=response_time,
                    error_message=f"HTTP {response.status_code}"
                )
                
        except requests.exceptions.Timeout:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                name="commodities",
                status="unhealthy",
                response_time_ms=response_time,
                error_message="Request timeout"
            )
        except requests.exceptions.ConnectionError:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                name="commodities",
                status="unhealthy",
                response_time_ms=response_time,
                error_message="Connection error"
            )
    
    def _check_crypto_connector(self, start_time: float) -> HealthCheckResult:
        """Check CoinGecko API health."""
        try:
            # Test CoinGecko API connectivity
            url = "https://api.coingecko.com/api/v3/ping"
            
            response = requests.get(url, timeout=10)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                return HealthCheckResult(
                    name="crypto",
                    status="healthy",
                    response_time_ms=response_time,
                    details={"api_status": "accessible"}
                )
            else:
                return HealthCheckResult(
                    name="crypto",
                    status="degraded",
                    response_time_ms=response_time,
                    error_message=f"HTTP {response.status_code}"
                )
                
        except requests.exceptions.Timeout:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                name="crypto",
                status="unhealthy",
                response_time_ms=response_time,
                error_message="Request timeout"
            )
        except requests.exceptions.ConnectionError:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                name="crypto",
                status="unhealthy",
                response_time_ms=response_time,
                error_message="Connection error"
            )
    
    def _check_economic_connector(self, start_time: float) -> HealthCheckResult:
        """Check World Bank API health."""
        try:
            # Test World Bank API connectivity
            url = "https://api.worldbank.org/v2/country/US/indicator/NY.GDP.MKTP.CD"
            params = {
                'format': 'json',
                'per_page': 1
            }
            
            response = requests.get(url, params=params, timeout=10)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                return HealthCheckResult(
                    name="economic",
                    status="healthy",
                    response_time_ms=response_time,
                    details={"api_status": "accessible"}
                )
            else:
                return HealthCheckResult(
                    name="economic",
                    status="degraded",
                    response_time_ms=response_time,
                    error_message=f"HTTP {response.status_code}"
                )
                
        except requests.exceptions.Timeout:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                name="economic",
                status="unhealthy",
                response_time_ms=response_time,
                error_message="Request timeout"
            )
        except requests.exceptions.ConnectionError:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                name="economic",
                status="unhealthy",
                response_time_ms=response_time,
                error_message="Connection error"
            )
    
    def _check_github_connector(self, start_time: float) -> HealthCheckResult:
        """Check GitHub API health."""
        try:
            # Test GitHub API connectivity
            url = "https://api.github.com/zen"
            
            response = requests.get(url, timeout=10)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                return HealthCheckResult(
                    name="github",
                    status="healthy",
                    response_time_ms=response_time,
                    details={"api_status": "accessible"}
                )
            else:
                return HealthCheckResult(
                    name="github",
                    status="degraded",
                    response_time_ms=response_time,
                    error_message=f"HTTP {response.status_code}"
                )
                
        except requests.exceptions.Timeout:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                name="github",
                status="unhealthy",
                response_time_ms=response_time,
                error_message="Request timeout"
            )
        except requests.exceptions.ConnectionError:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                name="github",
                status="unhealthy",
                response_time_ms=response_time,
                error_message="Connection error"
            )
    
    def _check_weather_connector(self, start_time: float) -> HealthCheckResult:
        """Check OpenWeather API health."""
        try:
            # Test OpenWeather API connectivity (without API key)
            url = "https://api.openweathermap.org/data/2.5/weather"
            params = {
                'q': 'London',
                'appid': 'test'  # Invalid key for testing
            }
            
            response = requests.get(url, params=params, timeout=10)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 401:  # Unauthorized is expected with test key
                return HealthCheckResult(
                    name="weather",
                    status="healthy",
                    response_time_ms=response_time,
                    details={"api_status": "accessible", "note": "API key needed"}
                )
            elif response.status_code == 200:
                return HealthCheckResult(
                    name="weather",
                    status="healthy",
                    response_time_ms=response_time,
                    details={"api_status": "accessible"}
                )
            else:
                return HealthCheckResult(
                    name="weather",
                    status="degraded",
                    response_time_ms=response_time,
                    error_message=f"HTTP {response.status_code}"
                )
                
        except requests.exceptions.Timeout:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                name="weather",
                status="unhealthy",
                response_time_ms=response_time,
                error_message="Request timeout"
            )
        except requests.exceptions.ConnectionError:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                name="weather",
                status="unhealthy",
                response_time_ms=response_time,
                error_message="Connection error"
            )
    
    def check_data_freshness(self) -> Dict[str, Any]:
        """Check freshness of data files."""
        try:
            recent_dirs = sorted([d for d in self.output_root.iterdir() 
                                if d.is_dir() and d.name.startswith('2025-')], 
                               reverse=True)
            
            if not recent_dirs:
                return {
                    "status": "no_data",
                    "latest_data_age_hours": float('inf'),
                    "data_sources": {}
                }
            
            latest_dir = recent_dirs[0]
            data_sources = {}
            max_age_hours = 0
            
            # Check each data source
            for csv_file in latest_dir.glob("*.csv"):
                source_name = csv_file.stem
                try:
                    df = pd.read_csv(csv_file)
                    if len(df) > 0 and 'date' in df.columns:
                        df['date'] = pd.to_datetime(df['date'])
                        latest_data_date = df['date'].max()
                        age_hours = (datetime.now() - latest_data_date).total_seconds() / 3600
                        data_sources[source_name] = {
                            "latest_data_age_hours": age_hours,
                            "data_points": len(df),
                            "status": "healthy" if age_hours < 48 else "stale"
                        }
                        max_age_hours = max(max_age_hours, age_hours)
                    else:
                        data_sources[source_name] = {
                            "latest_data_age_hours": float('inf'),
                            "data_points": 0,
                            "status": "no_data"
                        }
                except Exception as e:
                    data_sources[source_name] = {
                        "latest_data_age_hours": float('inf'),
                        "data_points": 0,
                        "status": "error",
                        "error": str(e)
                    }
            
            overall_status = "healthy"
            if max_age_hours > 48:
                overall_status = "stale"
            elif max_age_hours == float('inf'):
                overall_status = "no_data"
            
            return {
                "status": overall_status,
                "latest_data_age_hours": max_age_hours,
                "data_sources": data_sources
            }
            
        except Exception as e:
            self.logger.error(f"Error checking data freshness: {e}")
            return {
                "status": "error",
                "latest_data_age_hours": float('inf'),
                "data_sources": {},
                "error": str(e)
            }
    
    def run_health_checks(self) -> Dict[str, Any]:
        """Run all health checks and return comprehensive results."""
        self.logger.info("Running comprehensive health checks...")
        
        # Check connectors
        connector_results = self.check_all_connectors()
        
        # Check data freshness
        freshness_results = self.check_data_freshness()
        
        # Calculate overall health
        healthy_connectors = sum(1 for r in connector_results if r.status == "healthy")
        total_connectors = len(connector_results)
        
        overall_status = "healthy"
        if healthy_connectors == 0:
            overall_status = "unhealthy"
        elif healthy_connectors < total_connectors:
            overall_status = "degraded"
        
        if freshness_results["status"] != "healthy":
            if overall_status == "healthy":
                overall_status = "degraded"
            elif freshness_results["status"] == "no_data":
                overall_status = "unhealthy"
        
        return {
            "overall_status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "connectors": {
                "total": total_connectors,
                "healthy": healthy_connectors,
                "degraded": sum(1 for r in connector_results if r.status == "degraded"),
                "unhealthy": sum(1 for r in connector_results if r.status == "unhealthy"),
                "details": [
                    {
                        "name": r.name,
                        "status": r.status,
                        "response_time_ms": r.response_time_ms,
                        "error_message": r.error_message,
                        "details": r.details
                    }
                    for r in connector_results
                ]
            },
            "data_freshness": freshness_results
        }
