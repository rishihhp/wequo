from __future__ import annotations
from dataclasses import dataclass
from typing import List

import pandas as pd
import requests
from tenacity import retry, stop_after_attempt, wait_fixed

FRED_API = "https://api.stlouisfed.org/fred/series/observations"


@dataclass
class FredConnector:
    series_ids: List[str]
    api_key: str
    lookback_start: str | None = None
    lookback_end: str | None = None

    name: str = "fred"

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    def _fetch_series(self, series_id: str) -> pd.DataFrame:
        params = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json",
        }
        if self.lookback_start:
            params["observation_start"] = self.lookback_start
        if self.lookback_end:
            params["observation_end"] = self.lookback_end

        r = requests.get(FRED_API, params=params, timeout=30)
        r.raise_for_status()
        js = r.json()
        rows = js.get("observations", [])
        df = pd.DataFrame(rows)
        df["series_id"] = series_id
        return df

    def fetch(self) -> pd.DataFrame:
        frames = [self._fetch_series(sid) for sid in self.series_ids]
        return pd.concat(frames, ignore_index=True)

    def normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        out = (
            df.rename(columns={"date": "date", "value": "value"})[
                ["series_id", "date", "value"]
            ]
            .assign(source="FRED")
        )
        out["value"] = pd.to_numeric(out["value"], errors="coerce")
        return out.dropna(subset=["value"])
