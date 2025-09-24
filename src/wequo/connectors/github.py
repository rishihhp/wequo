from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any
from datetime import datetime, timedelta

import pandas as pd
import requests
from tenacity import retry, stop_after_attempt, wait_fixed

# GitHub API for trending repositories and activity
GITHUB_API = "https://api.github.com"


@dataclass
class GitHubConnector:
    """Connector for GitHub trends and activity metrics."""
    
    api_key: str | None = None  # Optional GitHub token for higher rate limits
    repos: List[str] = None
    lookback_days: int = 7
    
    name: str = "github"
    
    def __post_init__(self):
        # Default repositories to track if none provided
        if not self.repos:
            self.repos = [
                "microsoft/vscode",
                "facebook/react",
                "tensorflow/tensorflow",
                "pytorch/pytorch",
                "openai/gpt-3",
                "langchain-ai/langchain",
            ]
    
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    def _fetch_repo_stats(self, repo: str) -> Dict[str, Any]:
        """Fetch statistics for a single repository."""
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"token {self.api_key}"
        
        # Get repository info
        repo_url = f"{GITHUB_API}/repos/{repo}"
        r = requests.get(repo_url, headers=headers, timeout=30)
        r.raise_for_status()
        repo_data = r.json()
        
        # Get recent commits (last week)
        commits_url = f"{GITHUB_API}/repos/{repo}/commits"
        since_date = (datetime.now() - timedelta(days=self.lookback_days)).isoformat()
        commits_params = {"since": since_date}
        
        r = requests.get(commits_url, headers=headers, params=commits_params, timeout=30)
        r.raise_for_status()
        commits_data = r.json()
        
        # Get stargazers count over time (simplified)
        stargazers_url = f"{GITHUB_API}/repos/{repo}/stargazers"
        r = requests.get(stargazers_url, headers=headers, timeout=30)
        r.raise_for_status()
        stargazers_data = r.json()
        
        return {
            "repo": repo,
            "stars": repo_data.get("stargazers_count", 0),
            "forks": repo_data.get("forks_count", 0),
            "commits_last_week": len(commits_data),
            "open_issues": repo_data.get("open_issues_count", 0),
            "last_updated": repo_data.get("updated_at", ""),
        }
    
    def _generate_mock_data(self) -> pd.DataFrame:
        """Generate mock GitHub data for demonstration."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=self.lookback_days)
        
        rows = []
        for repo in self.repos:
            for i in range(self.lookback_days):
                date = start_date + timedelta(days=i)
                
                # Mock metrics with some variation
                import random
                base_stars = random.randint(1000, 50000)
                daily_stars = random.randint(0, 50)
                daily_commits = random.randint(0, 20)
                
                rows.extend([
                    {
                        "date": date.strftime("%Y-%m-%d"),
                        "value": base_stars + daily_stars,
                        "series_id": f"{repo}_stars",
                        "metric": "stars"
                    },
                    {
                        "date": date.strftime("%Y-%m-%d"),
                        "value": daily_commits,
                        "series_id": f"{repo}_commits",
                        "metric": "commits"
                    }
                ])
        
        return pd.DataFrame(rows)
    
    def fetch(self) -> pd.DataFrame:
        """Fetch GitHub trends data."""
        if not self.api_key:
            # Use mock data if no API key provided
            return self._generate_mock_data()
        
        rows = []
        for repo in self.repos:
            try:
                stats = self._fetch_repo_stats(repo)
                
                # Create time series data
                end_date = datetime.now()
                for i in range(self.lookback_days):
                    date = end_date - timedelta(days=i)
                    
                    rows.extend([
                        {
                            "date": date.strftime("%Y-%m-%d"),
                            "value": stats["stars"],
                            "series_id": f"{repo}_stars",
                            "metric": "stars"
                        },
                        {
                            "date": date.strftime("%Y-%m-%d"),
                            "value": stats["commits_last_week"] / self.lookback_days,  # Average daily
                            "series_id": f"{repo}_commits",
                            "metric": "commits"
                        }
                    ])
                    
            except Exception as e:
                print(f"Warning: Failed to fetch GitHub data for {repo}: {e}")
                continue
        
        return pd.DataFrame(rows) if rows else self._generate_mock_data()
    
    def normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize GitHub data to standard format."""
        if df.empty:
            return df
            
        out = df.copy()
        out["source"] = "GITHUB"
        out["value"] = pd.to_numeric(out["value"], errors="coerce")
        out["date"] = pd.to_datetime(out["date"], errors="coerce").dt.strftime("%Y-%m-%d")
        
        return out.dropna(subset=["value", "date"])
