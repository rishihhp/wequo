from __future__ import annotations
from dataclasses import dataclass
from typing import Dict
import pandas as pd


@dataclass
class ValidationResult:
    name: str
    rows: int
    has_data: bool
    latest_date: str | None


def basic_freshness_check(df: pd.DataFrame, date_col: str) -> str | None:
    if date_col not in df.columns or df.empty:
        return None
    try:
        latest = pd.to_datetime(df[date_col], errors="coerce").dropna().max()
        return None if pd.isna(latest) else latest.date().isoformat()
    except Exception:
        return None


def validate_frames(frames: Dict[str, pd.DataFrame]) -> list[ValidationResult]:
    results: list[ValidationResult] = []
    for name, df in frames.items():
        latest = None
        if "date" in df.columns:
            latest = basic_freshness_check(df, "date")
        results.append(ValidationResult(name=name, rows=len(df), has_data=not df.empty, latest_date=latest))
    return results
