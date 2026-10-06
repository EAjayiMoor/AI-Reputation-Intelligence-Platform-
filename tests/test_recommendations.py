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
        'Intervention level',
        'Affected signal',
        'Why this may matter',
        'Evidence strength',
        'Method basis',
        'Baseline',
        'Target calculation',
        'Validation method',
        'Confidence',
    }.issubset(recommendations.columns)
    assert recommendations['Action plan'].str.contains('1. ').all()
    assert recommendations['Owner'].str.len().gt(0).all()
    assert recommendations['Success measure'].str.len().gt(0).all()
    assert recommendations['Why this may matter'].str.len().gt(0).all()
    assert recommendations['Method basis'].str.len().gt(0).all()
    assert recommendations['Validation method'].str.contains('matched', case=False).all()


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


def test_small_samples_are_labelled_directional_without_an_uplift_promise() -> None:
    recommendations = generate_recommendations(_scored_recommendation_data())

    assert recommendations['Confidence'].eq('Low — directional sample').all()
    assert recommendations['Target calculation'].str.contains(
        'No percentage uplift target', case=False
    ).all()
    assert not recommendations.astype(str).apply(
        lambda column: column.str.contains('Expected lift', case=False)
    ).any().any()


def test_visibility_threshold_is_calculated_from_baseline_and_sample_size() -> None:
    raw = pd.DataFrame(
        [
            {
                'PromptID': f'P{index:03d}',
                'SouthamptonVisible': 1 if index <= 8 else 0,
                'SouthamptonRank': 3 if index <= 8 else '',
                'CitationSources': 'southampton.ac.uk' if index <= 8 else '',
                'Market': 'UK',
                'Subject': 'General',
                'Persona': 'Decision maker',
                'ModelName': 'model-a',
                'CompetitorsMentioned': 'University of Oxford',
            }
            for index in range(1, 41)
        ]
    )

    recommendations = generate_recommendations(score_results(raw))
    visibility = recommendations[recommendations['Category'].eq('Visibility')].iloc[0]

    assert visibility['Baseline'] == '8 of 40 responses (20.0%).'
    assert '13 of 40 responses (32.5%)' in visibility['Target calculation']
    assert 'one-sided 95% binomial threshold' in visibility['Target calculation']
    assert visibility['Confidence'] == 'Medium — benchmark threshold'
    assert 'not a forecast' in visibility['Success measure'].lower()


def test_intervention_levels_match_the_observed_segment() -> None:
    recommendations = generate_recommendations(_scored_recommendation_data())

    firm_wide = recommendations[recommendations['Category'].eq('Visibility')].iloc[0]
    subject = recommendations[recommendations['Category'].eq('Subject visibility')].iloc[0]
    market = recommendations[recommendations['Category'].eq('Market visibility')].iloc[0]

    assert firm_wide['Intervention level'] == 'Firm-wide'
    assert subject['Intervention level'] == 'Sector/service'
    assert market['Intervention level'] == 'Market'


def test_large_benchmarks_do_not_overflow_target_calculation() -> None:
    raw = pd.DataFrame(
        [
            {
                'PromptID': f'P{index:04d}',
                'SouthamptonVisible': 1 if index <= 500 else 0,
                'SouthamptonRank': 3 if index <= 500 else '',
                'CitationSources': '',
                'Market': 'UK',
                'Subject': 'General',
                'Persona': 'Decision maker',
                'ModelName': 'model-a',
                'CompetitorsMentioned': 'University of Oxford',
            }
            for index in range(1, 2601)
        ]
    )

    recommendations = generate_recommendations(score_results(raw), max_recommendations=1)

    assert len(recommendations) == 1
    assert 'one-sided 95% binomial threshold' in recommendations.iloc[0]['Target calculation']
