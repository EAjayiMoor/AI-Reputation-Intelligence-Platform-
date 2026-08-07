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
        average_rank = visible_only['rank_float'].mean() if not visible_only.empty else None

        row['prompt_count'] = int(frame['PromptID'].nunique())
        row['southampton_mentions'] = int(frame['visible_bool'].sum())
        row['average_rank'] = (
            round(float(average_rank), 2)
            if average_rank is not None and not pd.isna(average_rank)
            else None
        )
        row['visibility_score'] = round(float(frame['visibility_score_row'].mean()), 2)
        row['rank_score'] = round(float(frame['rank_score_row'].mean()), 2)
        row['citation_score'] = round(float(frame['citation_score_row'].mean()), 2)
        row['reputation_score'] = round(float(frame['reputation_score_row'].mean()), 2)
        rows.append(row)

    return pd.DataFrame(rows)


def competitor_mentions(scored_df: pd.DataFrame, group_column: str | None = None) -> pd.DataFrame:
    scored_df = _competitor_eligible_frame(scored_df)
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


def institution_mention_index(scored_df: pd.DataFrame, competitor_limit: int = 10) -> pd.DataFrame:
    """Compare Southampton with leading competitors on a top-institution-equals-100 index."""
    columns = ['Institution', 'Mentions', 'RelativeMentionIndex', 'InstitutionType']
    scored_df = _competitor_eligible_frame(scored_df)
    if scored_df.empty:
        return pd.DataFrame(columns=columns)

    competitors = competitor_mentions(scored_df)
    competitors = competitors[
        ~competitors['Competitor'].astype(str).str.contains('southampton', case=False, na=False)
    ].head(competitor_limit)
    comparison = competitors.rename(columns={'Competitor': 'Institution'}).copy()
    comparison['InstitutionType'] = 'Competitor'

    southampton = pd.DataFrame(
        [{
            'Institution': 'University of Southampton',
            'Mentions': int(scored_df['visible_bool'].sum()),
            'InstitutionType': 'Southampton',
        }]
    )
    comparison = pd.concat([comparison, southampton], ignore_index=True)
    maximum_mentions = int(comparison['Mentions'].max())
    comparison['RelativeMentionIndex'] = (
        comparison['Mentions'].div(maximum_mentions).mul(100).round(1)
        if maximum_mentions > 0
        else 0.0
    )
    return comparison[columns].sort_values('RelativeMentionIndex', ascending=False).reset_index(drop=True)


def institution_mentions_by_model(
    scored_df: pd.DataFrame,
    competitor_limit: int = 10,
) -> pd.DataFrame:
    """Return neutral-prompt institution mention counts for each captured model."""
    columns = [
        'Institution',
        'InstitutionType',
        'ModelName',
        'Mentions',
        'EligibleResponses',
        'MentionRate',
    ]
    eligible = _competitor_eligible_frame(scored_df)
    if eligible.empty or 'ModelName' not in eligible.columns:
        return pd.DataFrame(columns=columns)

    institutions = institution_mention_index(eligible, competitor_limit=competitor_limit)[
        ['Institution', 'InstitutionType']
    ]
    rows: list[dict[str, object]] = []
    for model_name, model_frame in eligible.groupby('ModelName', dropna=False):
        competitor_counts = competitor_mentions(model_frame).set_index('Competitor')['Mentions']
        eligible_responses = int(len(model_frame))
        for _, institution_row in institutions.iterrows():
            institution = str(institution_row['Institution'])
            institution_type = str(institution_row['InstitutionType'])
            mentions = (
                int(model_frame['visible_bool'].sum())
                if institution_type == 'Southampton'
                else int(competitor_counts.get(institution, 0))
            )
            rows.append(
                {
                    'Institution': institution,
                    'InstitutionType': institution_type,
                    'ModelName': str(model_name),
                    'Mentions': mentions,
                    'EligibleResponses': eligible_responses,
                    'MentionRate': round(mentions / eligible_responses * 100, 1),
                }
            )
    return pd.DataFrame(rows, columns=columns)


def _competitor_eligible_frame(scored_df: pd.DataFrame) -> pd.DataFrame:
    """Exclude prompts that supplied an institution name from competitor analysis."""
    if scored_df.empty:
        return scored_df
    if 'CompetitorPromptEligible' in scored_df.columns:
        return scored_df[scored_df['CompetitorPromptEligible'].fillna(False).astype(bool)]
    if 'PromptMentionType' in scored_df.columns:
        return scored_df[scored_df['PromptMentionType'].astype(str) == 'Organic']
    return scored_df
