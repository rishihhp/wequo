from __future__ import annotations
import json
from pathlib import Path
from typing import Any
import pandas as pd


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding='utf-8')


def write_md(path: Path, content: str) -> None:
    path.write_text(content, encoding='utf-8')


def write_df_csv(path: Path, df: pd.DataFrame) -> None:
    df.to_csv(path, index=False)