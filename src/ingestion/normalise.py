from __future__ import annotations

import re
from typing import Any

import pandas as pd

from src.ingestion.contracts import DEFAULT_ORGANISATION, ensure_visibility_columns, utc_now_iso


def normalise_prompt_text(value: Any) -> str:
    text = str(value or '').strip().lower()
    text = re.sub(r'\s+', ' ', text)
    return text


def base_visibility_frame(df: pd.DataFrame, source_type: str, source_file: str, source_sheet: str | None = None, default_organisation: str = DEFAULT_ORGANISATION) -> pd.DataFrame:
    working = pd.DataFrame()
    working['organisation'] = default_organisation

    keyword_col = _find_column(df.columns, ['Keyword', 'Prompt', 'query'])
    model_col = _find_column(df.columns, ['Model', 'Platform'])
    response_col = _find_column(df.columns, ['Response', 'Answer'])
    mentions_col = _find_column(df.columns, ['Mentions', 'MentionCount'])
    cited_col = _find_column(df.columns, ['Cited pages', 'CitationSources', 'Citations'])
    found_col = _find_column(df.columns, ['Found but not cited', 'FoundNotCited'])
    country_col = _find_column(df.columns, ['Country', 'Market'])
    updated_col = _find_column(df.columns, ['Updated', 'Date', 'Timestamp'])
    platform_col = _find_column(df.columns, ['Platform', 'Model'])

    working['prompt_text_snapshot'] = df[keyword_col] if keyword_col else None
    working['model'] = df[model_col] if model_col else None
    working['platform'] = df[platform_col] if platform_col else source_type.upper()
    working['response_text'] = df[response_col] if response_col else None
    working['mentions_raw'] = df[mentions_col] if mentions_col else None
    working['citation_sources'] = df[cited_col] if cited_col else None
    working['found_not_cited'] = df[found_col] if found_col else None
    working['market'] = df[country_col] if country_col else None
    working['updated_at'] = df[updated_col] if updated_col else None

    row_start = 2
    working['source_row_ref'] = [f'{row_start + i}' for i in range(len(df))]
    working['source_type'] = source_type
    working['source_file'] = source_file
    working['source_sheet'] = source_sheet
    working['ingested_at'] = utc_now_iso()
    working['prompt_match_status'] = 'pending'
    working['prompt_match_confidence'] = 0.0
    working['canonical_prompt_id'] = None

    working = ensure_visibility_columns(working)
    working['record_id'] = _build_record_ids(working)
    return working


def _find_column(columns, candidates):
    lowered = {c.lower(): c for c in columns}
    for candidate in candidates:
        found = lowered.get(candidate.lower())
        if found:
            return found
    return None


def _build_record_ids(df: pd.DataFrame) -> list[str]:
    values = []
    for idx, row in df.reset_index(drop=True).iterrows():
        prompt = normalise_prompt_text(row.get('prompt_text_snapshot', ''))[:20]
        prompt_token = re.sub(r'[^a-z0-9]+', '', prompt) or 'prompt'
        values.append(f'R{idx + 1:05d}_{prompt_token}')
    return values
