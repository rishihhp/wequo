from __future__ import annotations
from datetime import date, datetime, timedelta


def today_utc_date() -> date:
    return datetime.utcnow().date()


def iso_date(d: date) -> str:
    return d.isoformat()


def daterange_lookback(days: int) -> tuple[str, str]:
    end = today_utc_date()
    start = end - timedelta(days=days)
    return iso_date(start), iso_date(end)