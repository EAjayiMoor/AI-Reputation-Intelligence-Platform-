from __future__ import annotations

import pandas as pd

from src.recommendations import generate_recommendations
from src.scoring import score_results


def _scored_recommendation_data() -> pd.DataFrame:
    raw = pd.DataFrame(
        [
            {
                'PromptID': f'P{index:03d}',
                'SouthamptonVisible': 1 if index in {1, 2} else 0,
                'SouthamptonRank': 7 if index in {1, 2} else '',
                'CitationSources': 'southampton.ac.uk' if index == 1 else '',
                'Market': 'China' if index <= 5 else 'UK',
                'Subject': 'General' if index <= 5 else 'Engineering',
                'Persona': 'Research Professional' if index % 2 else 'Prospective Student',
                'ModelName': 'model-a' if index <= 5 else 'model-b',
                'CompetitorsMentioned': 'University of Oxford, Imperial College London',
            }
            for index in range(1, 21)
        ]
    )
    return score_results(raw)


def test_recommendations_include_owned_timed_measurable_actions() -> None:
    recommendations = generate_recommendations(_scored_recommendation_data())

    assert not recommendations.empty
    assert {
        'Priority',
        'Action',
        'Evidence',
        'Action plan',
        'Owner',
        'Timing',
        'Success measure',
    }.issubset(recommendations.columns)
    assert recommendations['Action plan'].str.contains('1. ').all()
    assert recommendations['Owner'].str.len().gt(0).all()
    assert recommendations['Success measure'].str.len().gt(0).all()


def test_recommendations_use_segment_and_competitor_evidence() -> None:
    recommendations = generate_recommendations(_scored_recommendation_data())
    combined_evidence = ' '.join(recommendations['Evidence'])

    assert 'China' in combined_evidence
    assert 'General' in combined_evidence
    assert 'University of Oxford' in combined_evidence


def test_recommendation_limit_is_respected() -> None:
    recommendations = generate_recommendations(
        _scored_recommendation_data(), max_recommendations=3
    )

    assert len(recommendations) == 3
