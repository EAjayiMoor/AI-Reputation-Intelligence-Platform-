from __future__ import annotations

from pathlib import Path
from typing import BinaryIO

import pandas as pd

from src.ingestion.normalise import base_visibility_frame


def load_xlsx_visibility(source: str | Path | BinaryIO, source_name: str | None = None) -> pd.DataFrame:
    workbook = pd.read_excel(source, sheet_name=None, dtype=str, keep_default_na=False)
    name = source_name or _resolve_source_name(source, fallback='uploaded.xlsx')

    frames: list[pd.DataFrame] = []
    for sheet_name, frame in workbook.items():
        filtered = _drop_empty_rows(frame)
        if filtered.empty:
            continue
        normalised = base_visibility_frame(
            filtered,
            source_type='xlsx',
            source_file=name,
            source_sheet=sheet_name,
        )
        frames.append(normalised)

    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def _drop_empty_rows(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame
    trimmed = frame.copy()
    for column in trimmed.columns:
        trimmed[column] = trimmed[column].astype(str).str.strip()
    mask = trimmed.apply(lambda row: any(cell not in {'' , 'nan', 'None'} for cell in row), axis=1)
    return frame.loc[mask].reset_index(drop=True)


def _resolve_source_name(source: object, fallback: str) -> str:
    if hasattr(source, 'name') and getattr(source, 'name'):
        return Path(str(getattr(source, 'name'))).name
    if isinstance(source, (str, Path)):
        return Path(str(source)).name
    return fallback
