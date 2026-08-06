from __future__ import annotations

import pandas as pd

from src.scoring import aggregate_scores


def generate_recommendations(scored_df: pd.DataFrame) -> pd.DataFrame:
    if scored_df.empty:
        return pd.DataFrame(
            columns=['Priority', 'Category', 'Scope', 'Rationale', 'Recommendation']
        )

    recommendations: list[dict[str, str]] = []

    overall = aggregate_scores(scored_df).iloc[0]
    if float(overall['visibility_score']) < 65:
        recommendations.append(
            {
                'Priority': 'High',
                'Category': 'Low visibility',
                'Scope': 'Overall',
                'Rationale': f"Visibility score is {overall['visibility_score']:.1f}, below the 65 threshold.",
                'Recommendation': 'Increase Southampton-focused prompts and improve model-facing evidence pages.',
            }
        )

    if float(overall['citation_score']) < 60:
        recommendations.append(
            {
                'Priority': 'High',
                'Category': 'Weak citations',
                'Scope': 'Overall',
                'Rationale': f"Citation score is {overall['citation_score']:.1f}, showing weak source visibility.",
                'Recommendation': 'Publish citation-friendly pages and reinforce authoritative domain signals.',
            }
        )

    market_scores = aggregate_scores(scored_df, ['Market'])
    for _, row in market_scores.iterrows():
        if float(row['visibility_score']) < 60:
            recommendations.append(
                {
                    'Priority': 'High',
                    'Category': 'Market-specific gap',
                    'Scope': str(row['Market']),
                    'Rationale': f"Visibility in {row['Market']} is {row['visibility_score']:.1f}.",
                    'Recommendation': f"Create {row['Market']}-tailored content and prompts to raise visibility.",
                }
            )

    subject_scores = aggregate_scores(scored_df, ['Subject'])
    for _, row in subject_scores.iterrows():
        if float(row['reputation_score']) < 60:
            recommendations.append(
                {
                    'Priority': 'Medium',
                    'Category': 'Subject-level weakness',
                    'Scope': str(row['Subject']),
                    'Rationale': f"Reputation for {row['Subject']} is {row['reputation_score']:.1f}.",
                    'Recommendation': f"Strengthen {row['Subject']} programme and research authority signals.",
                }
            )

    if not recommendations:
        recommendations.append(
            {
                'Priority': 'Medium',
                'Category': 'Maintain momentum',
                'Scope': 'Overall',
                'Rationale': 'No critical threshold breaches are currently detected.',
                'Recommendation': 'Continue monitoring and focus on incremental subject-level optimisation.',
            }
        )

    return pd.DataFrame(recommendations)


def key_gap_text(filtered_df: pd.DataFrame) -> str:
    if filtered_df.empty:
        return 'No data is available for this journey selection.'

    overall = aggregate_scores(filtered_df).iloc[0]
    if float(overall['visibility_score']) < 60:
        return 'Visibility is the main gap: Southampton is not appearing often enough in responses.'
    if float(overall['citation_score']) < 60:
        return 'Citation strength is the main gap: Southampton sources are not referenced consistently.'
    return 'Competitive pressure is the main gap: competitors are still mentioned strongly in this segment.'
