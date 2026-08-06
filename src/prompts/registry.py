from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src.ingestion.normalise import normalise_prompt_text


@dataclass(frozen=True)
class PromptMappingSummary:
    total_records: int
    matched_records: int
    unmatched_records: int


def build_prompt_registry(visibility_df: pd.DataFrame) -> pd.DataFrame:
    prompts = visibility_df.get('prompt_text_snapshot', pd.Series([], dtype=str)).fillna('').astype(str)
    normalised = prompts.map(normalise_prompt_text)
    unique = [value for value in pd.unique(normalised) if value]

    rows = []
    for index, prompt in enumerate(unique, start=1):
        rows.append(
            {
                'canonical_prompt_id': f'P{index:04d}',
                'prompt_text': prompt,
                'prompt_text_normalised': prompt,
                'created_from_source': 'auto_registry',
            }
        )

    if not rows:
        return pd.DataFrame(
            columns=[
                'canonical_prompt_id',
                'prompt_text',
                'prompt_text_normalised',
                'created_from_source',
            ]
        )

    return pd.DataFrame(rows)


def map_visibility_to_registry(
    visibility_df: pd.DataFrame, registry_df: pd.DataFrame
) -> tuple[pd.DataFrame, PromptMappingSummary]:
    mapped = visibility_df.copy()
    lookup = {
        row['prompt_text_normalised']: row['canonical_prompt_id']
        for _, row in registry_df.iterrows()
    }

    normalised_prompts = mapped['prompt_text_snapshot'].fillna('').astype(str).map(normalise_prompt_text)
    canonical_ids = normalised_prompts.map(lookup)

    matched_mask = canonical_ids.notna()
    mapped['canonical_prompt_id'] = canonical_ids
    mapped['prompt_match_status'] = matched_mask.map(lambda value: 'matched' if value else 'unmatched')
    mapped['prompt_match_confidence'] = matched_mask.map(lambda value: 1.0 if value else 0.0)

    summary = PromptMappingSummary(
        total_records=int(len(mapped)),
        matched_records=int(matched_mask.sum()),
        unmatched_records=int((~matched_mask).sum()),
    )
    return mapped, summary
