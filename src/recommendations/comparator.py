from __future__ import annotations

import pandas as pd

from src.recommendations.public_evidence import public_evidence_for


LEADER_MATRIX_COLUMNS = [
    'Lens', 'Segment', 'Eligible responses', 'Organisation mentions', 'Organisation rate',
    'Leader', 'Leader mentions', 'Leader rate', 'Gap (pp)', 'Comparison confidence',
    'Public evidence status',
]

COMPARABLE_PEERS = {
    'PA Consulting', 'Baringa', 'Elixirr', 'Gate One', 'Q5', 'North Highland',
    'Newton', 'Kearney',
}


def _eligible_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if 'CompetitorPromptEligible' in frame.columns:
        return frame[frame['CompetitorPromptEligible'].fillna(False).astype(bool)]
    if 'PromptMentionType' in frame.columns:
        return frame[frame['PromptMentionType'].astype(str).eq('Organic')]
    return frame


def _competitor_counts(frame: pd.DataFrame) -> pd.Series:
    counts: dict[str, int] = {}
    values = frame.get('CompetitorsMentioned', pd.Series(dtype='object')).fillna('')
    for raw in values:
        for name in {item.strip() for item in str(raw).split(',') if item.strip()}:
            counts[name] = counts.get(name, 0) + 1
    return pd.Series(counts, dtype='int64').sort_values(ascending=False)


def comparator_context(frame: pd.DataFrame, organisation_name: str) -> dict[str, object]:
    eligible = _eligible_frame(frame)
    response_count = int(len(eligible))
    organisation_mentions = int(eligible['visible_bool'].sum()) if 'visible_bool' in eligible else 0
    competitor_counts = _competitor_counts(eligible)
    if response_count == 0 or competitor_counts.empty:
        return {
            'comparator': 'No eligible comparator',
            'performance': 'No organisation-neutral comparator responses are available for this scope.',
            'pattern': 'No comparator practice is inferred.',
            'organisation_position': 'No comparative evidence position can be established.',
            'sources': '',
            'score': 20,
            'rating': 'Insufficient',
            'limitation': 'No causal or comparative conclusion can be drawn without eligible evidence.',
            'comparable_peer': 'No configured comparable peer',
            'peer_performance': 'No configured comparable peer appears in this response scope.',
            'peer_pattern': 'No peer practice is inferred.',
            'peer_sources': '',
        }

    comparator = str(competitor_counts.index[0])
    comparator_mentions = int(competitor_counts.iloc[0])
    organisation_rate = organisation_mentions / response_count * 100
    comparator_rate = comparator_mentions / response_count * 100
    gap = comparator_rate - organisation_rate
    comparator_evidence = public_evidence_for(comparator)
    organisation_evidence = public_evidence_for(organisation_name)
    peer_counts = competitor_counts[competitor_counts.index.isin(COMPARABLE_PEERS)]
    comparable_peer = str(peer_counts.index[0]) if not peer_counts.empty else 'No configured comparable peer'
    peer_mentions = int(peer_counts.iloc[0]) if not peer_counts.empty else 0
    peer_rate = peer_mentions / response_count * 100 if response_count else 0.0
    peer_evidence = public_evidence_for(comparable_peer)
    sample_points = 10 if response_count >= 30 else 5
    source_points = 20 if comparator_evidence['status'] == 'Curated' else 0
    score = min(100, 25 + 20 + 15 + source_points + sample_points + 10)
    if response_count < 30:
        score = min(score, 59)
        rating = 'Directional'
    elif comparator_evidence['status'] != 'Curated':
        score = min(score, 79)
        rating = 'Moderate'
    else:
        rating = 'Strong' if score >= 80 else 'Moderate'
    return {
        'comparator': comparator,
        'performance': (
            f'{comparator} appears in {comparator_mentions} of {response_count} eligible responses '
            f'({comparator_rate:.1f}%); {organisation_name} appears in {organisation_mentions} of '
            f'{response_count} ({organisation_rate:.1f}%), a {gap:.1f} percentage-point gap.'
        ),
        'pattern': str(comparator_evidence['pattern']),
        'organisation_position': str(organisation_evidence['pattern']),
        'sources': '; '.join(str(source) for source in comparator_evidence['sources']),
        'comparable_peer': comparable_peer,
        'peer_performance': (
            f'{comparable_peer} appears in {peer_mentions} of {response_count} eligible responses '
            f'({peer_rate:.1f}%).'
            if peer_mentions
            else 'No configured comparable peer appears in this response scope.'
        ),
        'peer_pattern': str(peer_evidence['pattern']),
        'peer_sources': '; '.join(str(source) for source in peer_evidence['sources']),
        'score': score,
        'rating': rating,
        'limitation': (
            'The observed association does not prove causation. '
            'Organisation scale, history, model training, retrieval and prompt wording may also explain the difference.'
        ),
    }


def _matrix_row(frame: pd.DataFrame, organisation_name: str, lens: str, segment: str) -> dict[str, object]:
    eligible = _eligible_frame(frame)
    context = comparator_context(eligible, organisation_name)
    response_count = int(len(eligible))
    organisation_mentions = int(eligible['visible_bool'].sum()) if 'visible_bool' in eligible else 0
    counts = _competitor_counts(eligible)
    leader_mentions = int(counts.iloc[0]) if not counts.empty else 0
    organisation_rate = organisation_mentions / response_count * 100 if response_count else 0.0
    leader_rate = leader_mentions / response_count * 100 if response_count else 0.0
    return {
        'Lens': lens,
        'Segment': segment,
        'Eligible responses': response_count,
        'Organisation mentions': organisation_mentions,
        'Organisation rate': round(organisation_rate, 1),
        'Leader': context['comparator'],
        'Leader mentions': leader_mentions,
        'Leader rate': round(leader_rate, 1),
        'Gap (pp)': round(leader_rate - organisation_rate, 1),
        'Comparison confidence': (
            'Insufficient' if response_count == 0 else 'Benchmark' if response_count >= 30 else 'Directional'
        ),
        'Public evidence status': public_evidence_for(str(context['comparator']))['status'],
    }


def build_leader_evidence_matrix(scored_df: pd.DataFrame) -> pd.DataFrame:
    if scored_df.empty:
        return pd.DataFrame(columns=LEADER_MATRIX_COLUMNS)
    organisation_name = 'Primary organisation'
    if 'Organisation' in scored_df.columns:
        names = scored_df['Organisation'].dropna().astype(str).str.strip()
        if not names.empty:
            organisation_name = str(names.iloc[0])

    rows = [_matrix_row(scored_df, organisation_name, 'Overall', 'All')]
    for column in ['Subject', 'Market', 'Persona', 'ModelName']:
        if column not in scored_df.columns or scored_df[column].nunique(dropna=True) <= 1:
            continue
        for segment, segment_frame in scored_df.groupby(column, dropna=False):
            rows.append(_matrix_row(segment_frame, organisation_name, column, str(segment)))
    return pd.DataFrame(rows, columns=LEADER_MATRIX_COLUMNS)
