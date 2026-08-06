from __future__ import annotations

import pandas as pd

RANK_SCORE_MAP = {
    1: 100,
    2: 90,
    3: 80,
}

REPUTATION_FORMULA = 'Reputation = 0.5 * Visibility + 0.3 * Rank + 0.2 * Citation'


def _parse_visible(value: object) -> bool:
    if pd.isna(value):
        return False
    text = str(value).strip().lower()
    return text in {'1', 'true', 'yes', 'y'}


def _parse_rank(value: object) -> float | None:
    if pd.isna(value):
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        parsed = float(text)
        return None if pd.isna(parsed) else parsed
    except ValueError:
        return None


def _rank_score(visible: bool, rank: float | None) -> int:
    if not visible:
        return 0
    if rank is None or pd.isna(rank):
        return 40
    rank_int = int(rank)
    if rank_int in RANK_SCORE_MAP:
        return RANK_SCORE_MAP[rank_int]
    if rank_int in {4, 5}:
        return 70
    if 6 <= rank_int <= 10:
        return 50
    return 40


def _citation_score(value: object) -> int:
    if pd.isna(value):
        return 0
    text = str(value).strip()
    return 100 if text else 0


def score_results(results_df: pd.DataFrame) -> pd.DataFrame:
    scored = results_df.copy()
    scored['visible_bool'] = scored['SouthamptonVisible'].map(_parse_visible)
    scored['rank_float'] = scored['SouthamptonRank'].map(_parse_rank)

    scored['visibility_score_row'] = scored['visible_bool'].map(lambda is_visible: 100 if is_visible else 0)
    scored['rank_score_row'] = scored.apply(
        lambda row: _rank_score(visible=bool(row['visible_bool']), rank=row['rank_float']),
        axis=1,
    )
    scored['citation_score_row'] = scored['CitationSources'].map(_citation_score)

    scored['reputation_score_row'] = (
        0.5 * scored['visibility_score_row']
        + 0.3 * scored['rank_score_row']
        + 0.2 * scored['citation_score_row']
    )
    return scored


def aggregate_scores(scored_df: pd.DataFrame, group_columns: list[str] | None = None) -> pd.DataFrame:
    group_columns = group_columns or []

    if scored_df.empty:
        columns = [
            *group_columns,
            'prompt_count',
            'southampton_mentions',
            'average_rank',
            'visibility_score',
            'rank_score',
            'citation_score',
            'reputation_score',
        ]
        return pd.DataFrame(columns=columns)

    if group_columns:
        grouped = scored_df.groupby(group_columns, dropna=False)
    else:
        grouped = [((), scored_df)]

    rows: list[dict[str, object]] = []
    for key, frame in grouped:
        row: dict[str, object] = {}
        if group_columns:
            keys = key if isinstance(key, tuple) else (key,)
            row.update(dict(zip(group_columns, keys)))

        visible_only = frame[frame['visible_bool']]

        row['prompt_count'] = int(frame['PromptID'].nunique())
        row['southampton_mentions'] = int(frame['visible_bool'].sum())
        row['average_rank'] = round(float(visible_only['rank_float'].mean()), 2) if not visible_only.empty else None
        row['visibility_score'] = round(float(frame['visibility_score_row'].mean()), 2)
        row['rank_score'] = round(float(frame['rank_score_row'].mean()), 2)
        row['citation_score'] = round(float(frame['citation_score_row'].mean()), 2)
        row['reputation_score'] = round(float(frame['reputation_score_row'].mean()), 2)
        rows.append(row)

    return pd.DataFrame(rows)


def competitor_mentions(scored_df: pd.DataFrame, group_column: str | None = None) -> pd.DataFrame:
    if scored_df.empty:
        return pd.DataFrame(columns=['Competitor', 'Mentions'])

    records: list[dict[str, object]] = []
    for _, row in scored_df.iterrows():
        raw = row.get('CompetitorsMentioned', '')
        if pd.isna(raw):
            continue
        for name in str(raw).split(','):
            competitor = name.strip()
            if not competitor:
                continue
            item = {'Competitor': competitor, 'Mentions': 1}
            if group_column:
                item[group_column] = row.get(group_column)
            records.append(item)

    if not records:
        columns = [group_column, 'Competitor', 'Mentions'] if group_column else ['Competitor', 'Mentions']
        return pd.DataFrame(columns=columns)

    frame = pd.DataFrame(records)
    if group_column:
        aggregated = frame.groupby([group_column, 'Competitor'], dropna=False, as_index=False)['Mentions'].sum()
        return aggregated.sort_values('Mentions', ascending=False)

    aggregated = frame.groupby('Competitor', as_index=False)['Mentions'].sum()
    return aggregated.sort_values('Mentions', ascending=False)
