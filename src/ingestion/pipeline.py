from __future__ import annotations

from pathlib import Path
from typing import BinaryIO

import pandas as pd

from src.ingestion.csv_loader import load_csv_visibility
from src.ingestion.xlsx_loader import load_xlsx_visibility
from src.prompts.registry import PromptMappingSummary, build_prompt_registry, map_visibility_to_registry


def merge_visibility_frames(csv_df: pd.DataFrame | None, xlsx_df: pd.DataFrame | None) -> pd.DataFrame:
    frames = [frame for frame in (csv_df, xlsx_df) if frame is not None and not frame.empty]
    if not frames:
        return pd.DataFrame()

    merged = pd.concat(frames, ignore_index=True)
    dedupe_columns = ['source_type', 'source_file', 'source_sheet', 'source_row_ref']
    merged = merged.drop_duplicates(subset=dedupe_columns, keep='first')
    return merged.reset_index(drop=True)


def run_ingestion_pipeline(
    csv_source: str | Path | BinaryIO | None = None,
    xlsx_source: str | Path | BinaryIO | None = None,
    csv_source_name: str | None = None,
    xlsx_source_name: str | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, PromptMappingSummary]:
    csv_df = load_csv_visibility(csv_source, source_name=csv_source_name) if csv_source is not None else pd.DataFrame()
    xlsx_df = load_xlsx_visibility(xlsx_source, source_name=xlsx_source_name) if xlsx_source is not None else pd.DataFrame()

    merged = merge_visibility_frames(csv_df=csv_df, xlsx_df=xlsx_df)
    if merged.empty:
        summary = PromptMappingSummary(total_records=0, matched_records=0, unmatched_records=0)
        return pd.DataFrame(), pd.DataFrame(), summary

    registry = build_prompt_registry(merged)
    mapped, summary = map_visibility_to_registry(merged, registry)
    return mapped, registry, summary
