from __future__ import annotations

from pathlib import Path

import pandas as pd

OPENROUTER_RESULTS_COLUMNS = [
    'ResultID',
    'PromptID',
    'Platform',
    'ResponseText',
    'SouthamptonVisible',
    'SouthamptonRank',
    'CompetitorsMentioned',
    'CitationSources',
    'RunDate',
    'Provider',
    'ModelName',
    'RequestID',
    'ResponseID',
    'RunBatchID',
    'PromptTokens',
    'CompletionTokens',
    'TotalTokens',
    'CachedPromptTokens',
    'APICost',
]


def load_openrouter_results(path: str | Path) -> pd.DataFrame:
    file_path = Path(path)
    if not file_path.exists():
        return pd.DataFrame(columns=OPENROUTER_RESULTS_COLUMNS)

    frame = pd.read_csv(file_path, encoding='utf-8')
    for column in OPENROUTER_RESULTS_COLUMNS:
        if column not in frame.columns:
            frame[column] = ''
    return frame[OPENROUTER_RESULTS_COLUMNS]


def append_openrouter_results(path: str | Path, rows: list[dict[str, object]]) -> pd.DataFrame:
    file_path = Path(path)
    existing = load_openrouter_results(file_path)
    new_rows = pd.DataFrame(rows)

    if new_rows.empty:
        return existing

    for column in OPENROUTER_RESULTS_COLUMNS:
        if column not in new_rows.columns:
            new_rows[column] = ''

    combined = pd.concat([existing, new_rows[OPENROUTER_RESULTS_COLUMNS]], ignore_index=True)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(file_path, index=False)
    return combined


def generated_prompt_subset(prompt_df: pd.DataFrame) -> pd.DataFrame:
    if 'PromptSource' not in prompt_df.columns:
        return pd.DataFrame(columns=prompt_df.columns)

    subset = prompt_df[prompt_df['PromptSource'].astype(str).str.lower() == 'generated']
    return subset.reset_index(drop=True)


def pending_prompt_rows(
    prompt_df: pd.DataFrame,
    existing_results_df: pd.DataFrame,
    model_name: str,
) -> list[dict[str, str]]:
    if prompt_df.empty:
        return []

    eligible = generated_prompt_subset(prompt_df)
    if eligible.empty:
        return []

    if existing_results_df.empty:
        return eligible[['PromptID', 'Prompt']].astype(str).to_dict(orient='records')

    already_done = existing_results_df[
        (existing_results_df['ModelName'].astype(str) == str(model_name))
        & (existing_results_df['PromptID'].astype(str).isin(eligible['PromptID'].astype(str)))
    ]

    completed_prompt_ids = set(already_done['PromptID'].astype(str).tolist())
    pending = eligible[~eligible['PromptID'].astype(str).isin(completed_prompt_ids)]
    return pending[['PromptID', 'Prompt']].astype(str).to_dict(orient='records')
