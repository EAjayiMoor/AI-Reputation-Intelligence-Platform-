from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import pandas as pd


SCOPE_ALL = 'all'
SCOPE_ORGANIC = 'organic'
SCOPE_PROMPTED = 'prompted_direct'
SCOPE_ORDER = (SCOPE_ALL, SCOPE_ORGANIC, SCOPE_PROMPTED)
SCOPE_LABELS = {
    SCOPE_ALL: 'All',
    SCOPE_ORGANIC: 'Organic',
    SCOPE_PROMPTED: 'Prompted/direct',
}


@dataclass(frozen=True)
class ScopeFrame:
    key: str
    label: str
    frame: pd.DataFrame


def split_scope_frames(frame: pd.DataFrame) -> list[ScopeFrame]:
    working = frame.copy().reset_index(drop=True)
    if 'PromptMentionType' not in working.columns:
        return [
            ScopeFrame(SCOPE_ALL, SCOPE_LABELS[SCOPE_ALL], working),
            ScopeFrame(SCOPE_ORGANIC, SCOPE_LABELS[SCOPE_ORGANIC], working),
            ScopeFrame(SCOPE_PROMPTED, SCOPE_LABELS[SCOPE_PROMPTED], working.iloc[0:0].copy()),
        ]

    prompt_type = working['PromptMentionType'].fillna('').astype(str)
    return [
        ScopeFrame(SCOPE_ALL, SCOPE_LABELS[SCOPE_ALL], working),
        ScopeFrame(SCOPE_ORGANIC, SCOPE_LABELS[SCOPE_ORGANIC], working[prompt_type == 'Organic'].reset_index(drop=True)),
        ScopeFrame(
            SCOPE_PROMPTED,
            SCOPE_LABELS[SCOPE_PROMPTED],
            working[prompt_type == 'Prompted/direct'].reset_index(drop=True),
        ),
    ]


def _non_empty_count(series: pd.Series) -> int:
    values = series.fillna('').astype(str).str.strip()
    return int(values.ne('').sum())


def _rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return float(numerator / denominator * 100)


def _has_citation(frame: pd.DataFrame) -> pd.Series:
    if 'citation_score_row' in frame.columns:
        return frame['citation_score_row'].fillna(0).astype(float).gt(0)
    if 'CitationSources' in frame.columns:
        return frame['CitationSources'].fillna('').astype(str).str.strip().ne('')
    return pd.Series(False, index=frame.index)


def _domain_hits(citation_text: pd.Series, owned_domains: Iterable[str]) -> int:
    clean_domains = [domain.strip().casefold() for domain in owned_domains if domain and domain.strip()]
    if not clean_domains:
        return 0
    citations = citation_text.fillna('').astype(str).str.casefold()
    return int(citations.map(lambda text: any(domain in text for domain in clean_domains)).sum())


def compute_scope_metrics(frame: pd.DataFrame, *, owned_domains: Iterable[str] = ()) -> dict[str, float | int | None]:
    working = frame.copy().reset_index(drop=True)
    responses = int(len(working))
    prompts = int(working['PromptID'].nunique()) if responses and 'PromptID' in working.columns else 0

    mentioned = (
        working['visible_bool'].fillna(False).astype(bool)
        if 'visible_bool' in working.columns
        else pd.Series(False, index=working.index)
    )
    mention_responses = int(mentioned.sum())

    prompt_mentions = 0
    if responses and 'PromptID' in working.columns:
        prompt_mentions = int(working.groupby('PromptID')['visible_bool'].max().sum())

    cited = _has_citation(working)
    citation_responses = int(cited.sum())
    citation_when_mentioned = int(cited[mentioned].sum()) if mention_responses else 0

    competitor_responses = (
        _non_empty_count(working['CompetitorsMentioned'])
        if 'CompetitorsMentioned' in working.columns
        else 0
    )
    pressure_ratio = (
        round(competitor_responses / mention_responses, 2)
        if mention_responses > 0
        else None
    )

    owned_source_share = 0.0
    if 'CitationSources' in working.columns and citation_responses > 0:
        owned_hits = _domain_hits(working['CitationSources'], owned_domains)
        owned_source_share = _rate(owned_hits, citation_responses)

    return {
        'responses': responses,
        'prompts': prompts,
        'mention_responses': mention_responses,
        'mention_prompts': prompt_mentions,
        'presence_rate_response': _rate(mention_responses, responses),
        'presence_rate_prompt': _rate(prompt_mentions, prompts),
        'citation_responses': citation_responses,
        'citation_coverage': _rate(citation_responses, responses),
        'citation_when_mentioned_count': citation_when_mentioned,
        'citation_when_mentioned': _rate(citation_when_mentioned, mention_responses),
        'owned_source_share': owned_source_share,
        'competitor_responses': competitor_responses,
        'competitor_pressure_ratio': pressure_ratio,
    }


def format_rate_with_denominator(numerator: int, denominator: int, *, digits: int = 1) -> str:
    value = _rate(numerator, denominator)
    return f'{value:.{digits}f}% ({numerator}/{denominator})'


def prompt_coverage_index(scored_df: pd.DataFrame, prompts_df: pd.DataFrame | None = None) -> float:
    tested = int(scored_df['PromptID'].nunique()) if 'PromptID' in scored_df.columns else 0
    planned = int(prompts_df['PromptID'].nunique()) if prompts_df is not None and 'PromptID' in prompts_df.columns else tested
    if planned <= 0:
        return 0.0
    return float(tested / planned * 100)


def segment_balance_score(prompt_df: pd.DataFrame, column: str) -> float:
    if column not in prompt_df.columns:
        return 0.0
    counts = prompt_df[column].fillna('Unknown').astype(str).value_counts()
    if counts.empty:
        return 0.0
    mean = float(counts.mean())
    if mean == 0:
        return 0.0
    cv = float(counts.std(ddof=0) / mean)
    return float(max(0.0, (1 - cv) * 100))
