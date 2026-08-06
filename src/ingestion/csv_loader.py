from __future__ import annotations

from pathlib import Path
from typing import BinaryIO

import pandas as pd

from src.ingestion.normalise import base_visibility_frame


def load_csv_visibility(source: str | Path | BinaryIO, source_name: str | None = None) -> pd.DataFrame:
    frame = pd.read_csv(source, sep='\t', dtype=str, keep_default_na=False)
    name = source_name or _resolve_source_name(source, fallback='uploaded.csv')
    return base_visibility_frame(frame, source_type='csv', source_file=name)


def _resolve_source_name(source: object, fallback: str) -> str:
    if hasattr(source, 'name') and getattr(source, 'name'):
        return Path(str(getattr(source, 'name'))).name
    if isinstance(source, (str, Path)):
        return Path(str(source)).name
    return fallback
