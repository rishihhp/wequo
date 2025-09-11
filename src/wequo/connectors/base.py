from __future__ import annotations
"""Connector protocol and a thin helper mixin for WeQuo data sources.

Phase-0 keeps things intentionally simple: each connector implements
`fetch()` (pull raw data) and `normalize()` (produce a tidy DataFrame with
canonical columns). The `run()` helper wires them together and writes a
single normalized CSV per connector under the given `outdir`.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable, Any, Dict

import pandas as pd


@runtime_checkable
class Connector(Protocol):
    """Minimal interface every connector must implement."""

    # Short, filesystem-safe name used for filenames (e.g., "fred").
    name: str

    def fetch(self) -> pd.DataFrame:
        """Return a *raw* DataFrame fetched from the upstream service.

        Implementations may perform pagination, retries, etc. Keep any heavy
        transformation work out of this method: do it in `normalize()`.
        """
        #...
        pass

    def normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        """Return a tidy DataFrame ready for downstream use.

        Recommended columns (when applicable):
        - `date`: ISO8601 string or datetime-like
        - `value`: numeric measurement
        - `series_id` (if multiple series are returned)
        - `source`: constant string identifying the upstream source
        """
        #...
        pass

    def run(self, outdir: Path) -> Dict[str, Any]:
        """Fetch -> normalize -> save; return a compact summary dict.

        The normalized CSV is written as `<outdir>/<self.name>.csv`.
        """
        raw_df = self.fetch()
        ndf = self.normalize(raw_df)
        outdir.mkdir(parents=True, exist_ok=True)
        norm_path = outdir / f"{self.name}.csv"
        ndf.to_csv(norm_path, index=False)
        return {
            "connector": self.name,
            "rows": int(len(ndf)),
            "files": {
                "normalized": str(norm_path),
            },
        }