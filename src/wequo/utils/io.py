from __future__ import annotations
import json
from pathlib import Path
from typing import Any
import pandas as pd


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, obj: Any) -> None:
    """Write JSON with support for pandas objects."""
    def json_serializer(obj):
        """Custom JSON serializer for pandas objects."""
        if isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        elif isinstance(obj, pd.DataFrame):
            return obj.to_dict(orient='records')
        elif isinstance(obj, pd.Series):
            return obj.to_dict()
        elif hasattr(obj, 'isoformat'):  # datetime objects
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):  # custom objects
            return obj.__dict__
        else:
            return str(obj)
    
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, default=json_serializer), encoding='utf-8')


def write_md(path: Path, content: str) -> None:
    path.write_text(content, encoding='utf-8')


def write_df_csv(path: Path, df: pd.DataFrame) -> None:
    df.to_csv(path, index=False)