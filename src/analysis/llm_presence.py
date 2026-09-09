"""Explainable row-level measurements for LLM reputation observations.

The functions in this module intentionally use deterministic rules rather than
another model call.  This keeps the measurement layer reproducible, cheap and
auditable while leaving the original response text available for review.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence

import pandas as pd

from src.analysis.response_parser import UNIVERSITY_ALIASES, organisation_name_pattern


MEASUREMENT_COLUMNS = (
    'Mentioned',
    'Prompted',
    'Organic',
    'Recommended',
    'Shortlisted',
    'FirstMentioned',
    'ProminenceScore',
    'CitationPresent',
    'CitationCount',
    'CompetitorMentionCount',
    'AssociationLabel',
    'AssociationScore',
    'EvidenceConfidence',
)

_RECOMMENDATION_PATTERN = re.compile(
    r'\b(?:recommend(?:ed|ation)?|suggest(?:ed|ion)?|consider|preferred|finalist)\b'
    r'|\b(?:top|strong|good|credible|leading)\s+(?:choice|option|pick)\b'
    r'|\bshort[- ]?list(?:ed)?\b',
    flags=re.IGNORECASE,
)
_SHORTLIST_PATTERN = re.compile(
    r'\bshort[- ]?list(?:ed)?\b|\bfinalist\b|\btop\s+(?:\d+|few|options?)\b',
    flags=re.IGNORECASE,
)
_URL_PATTERN = re.compile(r'https?://[^\s)\]>]+', flags=re.IGNORECASE)
_POSITIVE_TERMS = {
    'admired', 'best', 'competitive', 'credible', 'distinctive', 'effective',
    'excellent', 'leading', 'preferred', 'reliable', 'respected', 'strong',
    'successful', 'trusted', 'innovative', 'recommended', 'collaborative',
}
_NEGATIVE_TERMS = {
    'behind', 'commodity', 'concern', 'controversial', 'disappointing',
    'expensive', 'inconsistent', 'limited', 'negative', 'poor', 'risk',
    'unclear', 'unproven', 'weak',
}
_NEGATIVE_PHRASES = ('not recommended', 'not trusted', 'poor fit', 'high risk')


def _as_text(value: object) -> str:
    if value is None or pd.isna(value):
        return ''
    return str(value).strip()


def _as_bool(value: object) -> bool:
    if value is None or pd.isna(value):
        return False
    return str(value).strip().casefold() in {'1', 'true', 'yes', 'y'}


def _target_pattern(organisation_name: str, aliases: Sequence[str]) -> re.Pattern[str]:
    return re.compile(organisation_name_pattern(organisation_name, tuple(aliases)), flags=re.IGNORECASE)


def _chunks(text: str) -> list[str]:
    return [chunk.strip() for chunk in re.split(r'(?<=[.!?])\s+|\r?\n+', text) if chunk.strip()]


def _target_context(text: str, target: re.Pattern[str]) -> list[str]:
    return [chunk for chunk in _chunks(text) if target.search(chunk)]


def _mention_position(text: str, pattern: re.Pattern[str]) -> int | None:
    match = pattern.search(text)
    return match.start() if match else None


def _competitor_patterns(
    competitor_aliases: Mapping[str, Sequence[str]] | None,
    competitor_text: object = '',
) -> dict[str, re.Pattern[str]]:
    aliases = dict(competitor_aliases or {})
    if not aliases:
        for name in _as_text(competitor_text).split(','):
            if name.strip():
                aliases[name.strip()] = ()
    patterns: dict[str, re.Pattern[str]] = {}
    for canonical, values in aliases.items():
        names = [canonical, *values]
        escaped = [re.escape(_as_text(value)) for value in names if _as_text(value)]
        if escaped:
            patterns[canonical] = re.compile(
                rf'(?<!\w)(?:{"|".join(escaped)})(?!\w)', flags=re.IGNORECASE
            )
    return patterns


def _citation_count(response_text: str, citation_sources: object) -> int:
    source_text = _as_text(citation_sources)
    source_items = [item.strip() for item in re.split(r'[,;|\n]+', source_text) if item.strip()]
    urls = _URL_PATTERN.findall(response_text)
    return len(dict.fromkeys([*source_items, *urls]))


def _association(context: Sequence[str]) -> tuple[str, int]:
    if not context:
        return 'Not mentioned', 0
    text = ' '.join(context).casefold()
    negative_phrase_hits = sum(text.count(phrase) for phrase in _NEGATIVE_PHRASES)
    cleaned_text = text
    for phrase in _NEGATIVE_PHRASES:
        cleaned_text = cleaned_text.replace(phrase, ' ')
    tokens = set(re.findall(r"[a-z']+", cleaned_text))
    positive = len(tokens.intersection(_POSITIVE_TERMS))
    negative = (negative_phrase_hits * 2) + len(tokens.intersection(_NEGATIVE_TERMS))
    score = positive - negative
    if score > 0:
        return 'Positive', score
    if score < 0:
        return 'Negative', score
    return 'Neutral', 0


def _has_positive_signal(chunks: Sequence[str], pattern: re.Pattern[str]) -> bool:
    """Match positive recommendation/shortlist language, excluding negation."""
    negative = re.compile(
        r'\b(?:not|never|unlikely to be)\s+(?:recommended|preferred|short[- ]?listed|a\s+finalist)\b',
        flags=re.IGNORECASE,
    )
    return any(pattern.search(chunk) and not negative.search(chunk) for chunk in chunks)


def _prominence_score(mentioned: bool, rank: object) -> int:
    if not mentioned:
        return 0
    try:
        parsed = int(float(_as_text(rank)))
    except (TypeError, ValueError):
        return 40
    if parsed <= 1:
        return 100
    if parsed == 2:
        return 90
    if parsed == 3:
        return 80
    if parsed in {4, 5}:
        return 70
    if 6 <= parsed <= 10:
        return 50
    return 40


def _row_measurements(
    row: pd.Series,
    *,
    target: re.Pattern[str],
    competitor_aliases: Mapping[str, Sequence[str]] | None,
) -> dict[str, object]:
    response = _as_text(row.get('ResponseText', ''))
    mentioned = _as_bool(row.get('OrgVisible', row.get('SouthamptonVisible', False)))
    if not mentioned:
        mentioned = bool(target.search(response))

    prompt_type = _as_text(row.get('PromptMentionType', ''))
    prompted = prompt_type.casefold() == 'prompted/direct'
    context = _target_context(response, target) if mentioned else []
    association, association_score = _association(context)
    citation_count = _citation_count(response, row.get('CitationSources', ''))

    competitor_patterns = _competitor_patterns(competitor_aliases, row.get('CompetitorsMentioned', ''))
    competitor_positions = [
        position
        for pattern in competitor_patterns.values()
        if (position := _mention_position(response, pattern)) is not None
    ]
    target_position = _mention_position(response, target)
    first_mentioned = bool(
        target_position is not None
        and (not competitor_positions or target_position <= min(competitor_positions))
    )

    return {
        'Mentioned': mentioned,
        'Prompted': prompted,
        'Organic': not prompted,
        'Recommended': _has_positive_signal(context, _RECOMMENDATION_PATTERN),
        'Shortlisted': _has_positive_signal(context, _SHORTLIST_PATTERN),
        'FirstMentioned': first_mentioned,
        'ProminenceScore': _prominence_score(mentioned, row.get('OrgRank', row.get('SouthamptonRank', ''))),
        'CitationPresent': citation_count > 0,
        'CitationCount': citation_count,
        'CompetitorMentionCount': len(competitor_positions),
        'AssociationLabel': association,
        'AssociationScore': association_score,
        'EvidenceConfidence': 'High' if mentioned and citation_count else 'Medium' if mentioned else 'Low',
    }


def enrich_llm_presence(
    results_df: pd.DataFrame,
    *,
    organisation_name: str,
    organisation_aliases: Sequence[str] = (),
    competitor_aliases: Mapping[str, Sequence[str]] | None = None,
) -> pd.DataFrame:
    """Add deterministic LLM-presence measurements to each response row."""
    enriched = results_df.copy()
    target = _target_pattern(organisation_name, organisation_aliases)
    measurements = [
        _row_measurements(row, target=target, competitor_aliases=competitor_aliases)
        for _, row in enriched.iterrows()
    ]
    for column in MEASUREMENT_COLUMNS:
        enriched[column] = [measurement[column] for measurement in measurements]
    return enriched


def _entity_patterns(
    organisation_name: str,
    organisation_aliases: Sequence[str],
    competitor_aliases: Mapping[str, Sequence[str]] | None,
) -> dict[str, re.Pattern[str]]:
    patterns = {organisation_name: _target_pattern(organisation_name, organisation_aliases)}
    if competitor_aliases is None:
        patterns.update(
            {
                canonical: re.compile('|'.join(aliases), flags=re.IGNORECASE)
                for canonical, aliases in UNIVERSITY_ALIASES.items()
                if canonical.casefold() != organisation_name.casefold()
            }
        )
    else:
        patterns.update(_competitor_patterns(competitor_aliases))
    return patterns


def competitive_breakdown(
    results_df: pd.DataFrame,
    *,
    organisation_name: str,
    organisation_aliases: Sequence[str] = (),
    competitor_aliases: Mapping[str, Sequence[str]] | None = None,
) -> pd.DataFrame:
    """Summarise response-level competitive signals for neutral prompts."""
    columns = [
        'Entity', 'EntityType', 'EligibleResponses', 'MentionedResponses', 'MentionRate',
        'FirstMentionedResponses', 'FirstMentionedRate', 'RecommendedResponses',
        'RecommendationRate', 'ShortlistedResponses', 'ShortlistRate',
    ]
    if results_df.empty:
        return pd.DataFrame(columns=columns)

    if 'CompetitorPromptEligible' in results_df.columns:
        eligible = results_df[results_df['CompetitorPromptEligible'].fillna(False).astype(bool)]
    elif 'PromptMentionType' in results_df.columns:
        eligible = results_df[results_df['PromptMentionType'].astype(str) == 'Organic']
    else:
        eligible = results_df
    if eligible.empty:
        return pd.DataFrame(columns=columns)

    patterns = _entity_patterns(organisation_name, organisation_aliases, competitor_aliases)
    target_key = organisation_name.casefold()
    observations: list[dict[str, object]] = []
    for _, row in eligible.iterrows():
        response = _as_text(row.get('ResponseText', ''))
        positions = {
            entity: position
            for entity, pattern in patterns.items()
            if (position := _mention_position(response, pattern)) is not None
        }
        first_position = min(positions.values()) if positions else None
        for entity, pattern in patterns.items():
            position = positions.get(entity)
            context = _target_context(response, pattern) if position is not None else []
            mentioned = position is not None
            observations.append(
                {
                    'Entity': entity,
                    'EntityType': 'Target' if entity.casefold() == target_key else 'Competitor',
                    'Mentioned': mentioned,
                    'FirstMentioned': mentioned and position == first_position,
                    'Recommended': _has_positive_signal(context, _RECOMMENDATION_PATTERN),
                    'Shortlisted': _has_positive_signal(context, _SHORTLIST_PATTERN),
                }
            )

    observation_frame = pd.DataFrame(observations)
    summary = (
        observation_frame.groupby(['Entity', 'EntityType'], as_index=False)
        .agg(
            MentionedResponses=('Mentioned', 'sum'),
            FirstMentionedResponses=('FirstMentioned', 'sum'),
            RecommendedResponses=('Recommended', 'sum'),
            ShortlistedResponses=('Shortlisted', 'sum'),
        )
    )
    eligible_count = int(len(eligible))
    summary['EligibleResponses'] = eligible_count
    summary['MentionRate'] = summary['MentionedResponses'].div(eligible_count).mul(100).round(1)
    mentioned = summary['MentionedResponses'].where(summary['MentionedResponses'].gt(0))
    summary['FirstMentionedRate'] = summary['FirstMentionedResponses'].div(mentioned).mul(100).fillna(0).round(1)
    summary['RecommendationRate'] = summary['RecommendedResponses'].div(mentioned).mul(100).fillna(0).round(1)
    summary['ShortlistRate'] = summary['ShortlistedResponses'].div(mentioned).mul(100).fillna(0).round(1)
    return summary[columns].sort_values(
        ['EntityType', 'MentionRate', 'Entity'], ascending=[True, False, True]
    ).reset_index(drop=True)


def competitive_cooccurrence(
    results_df: pd.DataFrame,
    *,
    organisation_name: str,
    organisation_aliases: Sequence[str] = (),
    competitor_aliases: Mapping[str, Sequence[str]] | None = None,
) -> pd.DataFrame:
    """Return pairs of recognised organisations appearing in the same answer."""
    columns = ['EntityA', 'EntityB', 'CooccurrenceResponses', 'CooccurrenceRate']
    if results_df.empty:
        return pd.DataFrame(columns=columns)
    if 'CompetitorPromptEligible' in results_df.columns:
        eligible = results_df[results_df['CompetitorPromptEligible'].fillna(False).astype(bool)]
    elif 'PromptMentionType' in results_df.columns:
        eligible = results_df[results_df['PromptMentionType'].astype(str) == 'Organic']
    else:
        eligible = results_df
    if eligible.empty:
        return pd.DataFrame(columns=columns)

    patterns = _entity_patterns(organisation_name, organisation_aliases, competitor_aliases)
    pair_counts: dict[tuple[str, str], int] = {}
    for _, row in eligible.iterrows():
        response = _as_text(row.get('ResponseText', ''))
        present = sorted(
            entity for entity, pattern in patterns.items() if pattern.search(response)
        )
        for index, entity_a in enumerate(present):
            for entity_b in present[index + 1:]:
                pair = (entity_a, entity_b)
                pair_counts[pair] = pair_counts.get(pair, 0) + 1

    if not pair_counts:
        return pd.DataFrame(columns=columns)
    output = pd.DataFrame(
        [
            {
                'EntityA': entity_a,
                'EntityB': entity_b,
                'CooccurrenceResponses': count,
                'CooccurrenceRate': round(count / len(eligible) * 100, 1),
            }
            for (entity_a, entity_b), count in pair_counts.items()
        ]
    )
    return output.sort_values(
        ['CooccurrenceResponses', 'EntityA', 'EntityB'], ascending=[False, True, True]
    ).reset_index(drop=True)
