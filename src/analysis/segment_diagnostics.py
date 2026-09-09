"""Grouped topic/persona diagnostics for LLM-presence results."""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd


def _prepared(frame: pd.DataFrame) -> pd.DataFrame:
    working = frame.copy()
    fallbacks = {
        'Mentioned': 'visible_bool',
        'CitationPresent': None,
        'Recommended': None,
        'Shortlisted': None,
        'AssociationLabel': None,
        'ProminenceScore': 'rank_score_row',
    }
    for column, fallback in fallbacks.items():
        if column in working.columns:
            continue
        if fallback is None:
            working[column] = False if column != 'AssociationLabel' else 'Not available'
        elif fallback not in working.columns:
            working[column] = False if column in {'Mentioned', 'CitationPresent', 'Recommended', 'Shortlisted'} else 0
        else:
            working[column] = working[fallback]
    for column in ['Mentioned', 'CitationPresent', 'Recommended', 'Shortlisted']:
        working[column] = working[column].fillna(False).astype(bool)
    working['AssociationLabel'] = working['AssociationLabel'].fillna('Not available').astype(str)
    working['ProminenceScore'] = pd.to_numeric(working['ProminenceScore'], errors='coerce').fillna(0)
    if 'reputation_score_row' in working.columns:
        working['ReputationScore'] = pd.to_numeric(
            working['reputation_score_row'], errors='coerce'
        ).fillna(0)
    else:
        working['ReputationScore'] = 0.0
    return working


def segment_summary(
    scored_df: pd.DataFrame,
    group_columns: Sequence[str] = ('Persona', 'Subject'),
) -> pd.DataFrame:
    """Aggregate presence and narrative signals for a topic/persona segment."""
    output_columns = [
        *group_columns,
        'Responses', 'MentionedResponses', 'MentionRate', 'AverageProminence',
        'RecommendationRate', 'ShortlistRate', 'CitationRate', 'PositiveAssociationRate',
        'AverageReputationScore', 'OpportunityScore', 'Diagnosis',
    ]
    if scored_df.empty or any(column not in scored_df.columns for column in group_columns):
        return pd.DataFrame(columns=output_columns)

    working = _prepared(scored_df)
    for column in group_columns:
        working[column] = working[column].fillna('Unknown').astype(str)
    working['PositiveAssociation'] = working['AssociationLabel'].eq('Positive')
    summary = (
        working.groupby(list(group_columns), dropna=False)
        .agg(
            Responses=('PromptID', 'size'),
            MentionedResponses=('Mentioned', 'sum'),
            AverageProminence=('ProminenceScore', 'mean'),
            RecommendedResponses=('Recommended', 'sum'),
            ShortlistedResponses=('Shortlisted', 'sum'),
            CitedResponses=('CitationPresent', 'sum'),
            PositiveResponses=('PositiveAssociation', 'sum'),
            AverageReputationScore=('ReputationScore', 'mean'),
        )
        .reset_index()
    )
    summary['MentionRate'] = summary['MentionedResponses'].div(summary['Responses']).mul(100)
    mentioned = summary['MentionedResponses'].where(summary['MentionedResponses'].gt(0))
    summary['RecommendationRate'] = summary['RecommendedResponses'].div(mentioned).mul(100).fillna(0)
    summary['ShortlistRate'] = summary['ShortlistedResponses'].div(mentioned).mul(100).fillna(0)
    summary['CitationRate'] = summary['CitedResponses'].div(summary['Responses']).mul(100)
    summary['PositiveAssociationRate'] = summary['PositiveResponses'].div(mentioned).mul(100).fillna(0)
    summary['OpportunityScore'] = (100 - summary['AverageReputationScore']).clip(lower=0, upper=100)
    summary['Diagnosis'] = summary.apply(_diagnosis, axis=1)
    for column in [
        'MentionRate', 'AverageProminence', 'RecommendationRate', 'ShortlistRate',
        'CitationRate', 'PositiveAssociationRate', 'AverageReputationScore', 'OpportunityScore',
    ]:
        summary[column] = summary[column].round(1)
    return summary[output_columns].sort_values(
        ['OpportunityScore', 'Responses'], ascending=[False, False]
    ).reset_index(drop=True)


def _diagnosis(row: pd.Series) -> str:
    if float(row['MentionRate']) < 60:
        return 'Presence gap'
    if float(row['CitationRate']) < 60:
        return 'Evidence gap'
    if float(row['PositiveAssociationRate']) < 50:
        return 'Narrative gap'
    return 'Strength'


def outlier_responses(scored_df: pd.DataFrame, *, limit: int = 20) -> pd.DataFrame:
    """Return auditable strength and gap response rows behind segment summaries."""
    columns = [
        'OutlierType', 'OutlierReason', 'OutlierScore', 'PromptID', 'ModelName', 'Persona',
        'Subject', 'ExpertiseArea', 'Market', 'Intent', 'ResponseText', 'CitationSources',
        'CompetitorsMentioned',
    ]
    if scored_df.empty:
        return pd.DataFrame(columns=columns)

    working = _prepared(scored_df)
    working['OutlierType'] = ''
    working['OutlierReason'] = ''
    gap_rules = [
        (~working['Mentioned'], 'Not mentioned'),
        (working['AssociationLabel'].eq('Negative'), 'Negative association'),
        (working['Mentioned'] & ~working['CitationPresent'], 'Uncited mention'),
        (working['Mentioned'] & working['ProminenceScore'].lt(50), 'Low prominence'),
    ]
    for condition, reason in gap_rules:
        update = condition & working['OutlierType'].eq('')
        working.loc[update, 'OutlierType'] = 'Gap'
        working.loc[update, 'OutlierReason'] = reason

    strength = (
        working['Mentioned']
        & working['OutlierType'].eq('')
        & (working['Recommended'] | working['Shortlisted'] | working['AssociationLabel'].eq('Positive'))
    )
    working.loc[strength, 'OutlierType'] = 'Strength'
    working.loc[strength & working['Recommended'], 'OutlierReason'] = 'Recommended'
    working.loc[
        strength & working['OutlierReason'].eq('') & working['Shortlisted'], 'OutlierReason'
    ] = 'Shortlisted'
    working.loc[ strength & working['OutlierReason'].eq(''), 'OutlierReason'] = 'Positive association'
    working = working[working['OutlierType'].ne('')].copy()
    if working.empty:
        return pd.DataFrame(columns=columns)
    working['OutlierScore'] = working.apply(
        lambda row: 100 - float(row['ReputationScore']) if row['OutlierType'] == 'Gap' else float(row['ReputationScore']),
        axis=1,
    ).round(1)
    for column in columns:
        if column not in working.columns:
            working[column] = ''
    gaps = working[working['OutlierType'] == 'Gap'].sort_values('OutlierScore', ascending=False).head(limit)
    strengths = working[working['OutlierType'] == 'Strength'].sort_values('OutlierScore', ascending=False).head(limit)
    return pd.concat([gaps, strengths], ignore_index=True)[columns]


def run_history_summary(scored_df: pd.DataFrame) -> pd.DataFrame:
    """Summarise matched captured sweeps so future reruns can be compared safely."""
    columns = [
        'Run', 'Responses', 'Prompts', 'Models', 'MentionRate', 'RecommendationRate',
        'ShortlistRate', 'CitationRate', 'AverageProminence', 'ReputationScore',
        'MentionRateChange', 'ReputationScoreChange',
    ]
    if scored_df.empty or 'RunDate' not in scored_df.columns:
        return pd.DataFrame(columns=columns)

    working = _prepared(scored_df)
    run_values = working['RunDate'].fillna('').astype(str).str.strip()
    if run_values.eq('').all() and 'RunBatchID' in working.columns:
        run_values = working['RunBatchID'].fillna('').astype(str).str.strip()
    working['Run'] = run_values.replace('', 'Unknown run')
    rows: list[dict[str, object]] = []
    for run, frame in working.groupby('Run', sort=True, dropna=False):
        mentions = int(frame['Mentioned'].sum())
        denominator = max(mentions, 1)
        rows.append(
            {
                'Run': str(run),
                'Responses': int(len(frame)),
                'Prompts': int(frame['PromptID'].nunique()),
                'Models': int(frame['ModelName'].nunique()) if 'ModelName' in frame.columns else 0,
                'MentionRate': round(frame['Mentioned'].mean() * 100, 1),
                'RecommendationRate': round(frame['Recommended'].sum() / denominator * 100, 1),
                'ShortlistRate': round(frame['Shortlisted'].sum() / denominator * 100, 1),
                'CitationRate': round(frame['CitationPresent'].mean() * 100, 1),
                'AverageProminence': round(frame['ProminenceScore'].mean(), 1),
                'ReputationScore': round(frame['ReputationScore'].mean(), 1),
            }
        )
    history = pd.DataFrame(rows)
    history['MentionRateChange'] = history['MentionRate'].diff().round(1).fillna(0.0)
    history['ReputationScoreChange'] = history['ReputationScore'].diff().round(1).fillna(0.0)
    return history[columns]
