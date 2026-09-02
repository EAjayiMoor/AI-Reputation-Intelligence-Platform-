from __future__ import annotations

from datetime import datetime, timezone

from src.tenants import load_tenant


def _default_organisation() -> str:
    try:
        return load_tenant('southampton').display_name
    except Exception:
        return 'University of Southampton'


DEFAULT_ORGANISATION = _default_organisation()

VISIBILITY_CANONICAL_COLUMNS = [
    'record_id',
    'organisation',
    'canonical_prompt_id',
    'prompt_text_snapshot',
    'market',
    'platform',
    'model',
    'response_text',
    'mentions_raw',
    'citation_sources',
    'found_not_cited',
    'updated_at',
    'source_type',
    'source_file',
    'source_sheet',
    'source_row_ref',
    'ingested_at',
    'prompt_match_status',
    'prompt_match_confidence',
]

PROMPT_REGISTRY_COLUMNS = [
    'canonical_prompt_id',
    'prompt_text',
    'prompt_text_normalised',
    'created_from_source',
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_visibility_columns(df):
    for column in VISIBILITY_CANONICAL_COLUMNS:
        if column not in df.columns:
            df[column] = None
    return df[VISIBILITY_CANONICAL_COLUMNS]
