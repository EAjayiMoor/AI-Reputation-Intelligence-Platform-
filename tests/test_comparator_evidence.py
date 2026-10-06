from __future__ import annotations

import pandas as pd

from src.recommendations import build_leader_evidence_matrix, generate_recommendations
from src.recommendations.public_evidence import public_evidence_for
from src.scoring import score_results


def _comparison_data() -> pd.DataFrame:
    rows = []
    for index in range(1, 41):
        subject = 'Market reputation' if index <= 25 else 'Sector credibility'
        competitors = []
        if index <= 20:
            competitors.append('Deloitte')
        if index <= 12:
            competitors.append('PA Consulting')
        if index > 25 and index <= 36:
            competitors.append('Baringa')
        rows.append(
            {
                'PromptID': f'MH-{index:04d}',
                'Organisation': 'Moorhouse',
                'OrgVisible': 1 if index in {1, 2, 26, 27} else 0,
                'OrgRank': 4 if index in {1, 2, 26, 27} else '',
                'CitationSources': '',
                'Market': 'UK',
                'Subject': subject,
                'Persona': 'Decision maker',
                'ModelName': 'model-a' if index % 2 else 'model-b',
                'CompetitorPromptEligible': True,
                'CompetitorsMentioned': ', '.join(competitors),
            }
        )
    return score_results(pd.DataFrame(rows))


def test_leader_matrix_uses_all_eligible_responses_and_segment_leaders() -> None:
    matrix = build_leader_evidence_matrix(_comparison_data())

    overall = matrix[(matrix['Lens'] == 'Overall') & (matrix['Segment'] == 'All')].iloc[0]
    market_reputation = matrix[
        (matrix['Lens'] == 'Subject') & (matrix['Segment'] == 'Market reputation')
    ].iloc[0]
    sector = matrix[
        (matrix['Lens'] == 'Subject') & (matrix['Segment'] == 'Sector credibility')
    ].iloc[0]

    assert overall['Eligible responses'] == 40
    assert overall['Organisation mentions'] == 4
    assert overall['Leader'] == 'Deloitte'
    assert overall['Leader mentions'] == 20
    assert overall['Gap (pp)'] == 40.0
    assert market_reputation['Leader'] == 'Deloitte'
    assert sector['Leader'] == 'Baringa'


def test_recommendations_include_comparator_and_public_evidence_fields() -> None:
    recommendations = generate_recommendations(_comparison_data())
    visibility = recommendations[recommendations['Category'].eq('Visibility')].iloc[0]
    subject = recommendations[recommendations['Category'].eq('Subject visibility')].iloc[0]

    assert visibility['Comparator'] == 'Deloitte'
    assert visibility['Comparable peer'] == 'PA Consulting'
    assert '20 of 40' in visibility['Comparative performance']
    assert 'Moorhouse appears in 4 of 40' in visibility['Comparative performance']
    assert visibility['Comparator evidence pattern']
    assert visibility['Organisation evidence position']
    assert 'deloitte.com' in visibility['Comparator sources']
    assert '12 of 40' in visibility['Peer performance']
    assert 'paconsulting.com' in visibility['Peer sources']
    assert visibility['Evidence quality rating'] in {'Strong', 'Moderate', 'Directional'}
    assert 0 <= visibility['Evidence quality score'] <= 100
    assert 'does not prove causation' in visibility['Comparative limitation'].lower()
    assert visibility['Evidence quality rating'] == 'Strong'
    assert subject['Evidence quality rating'] == 'Directional'


def test_unknown_comparator_is_reported_without_inventing_public_evidence() -> None:
    evidence = public_evidence_for('Unknown Consultancy')

    assert evidence['status'] == 'Not curated'
    assert evidence['sources'] == ()
    assert 'manual review' in evidence['pattern'].lower()


def test_curated_comparator_evidence_is_dated_and_sourced() -> None:
    evidence = public_evidence_for('PA Consulting')

    assert evidence['status'] == 'Curated'
    assert evidence['reviewed_on'] == '2026-10-06'
    assert len(evidence['sources']) >= 2
    assert all(source.startswith('https://') for source in evidence['sources'])


def test_recommendation_handles_scope_without_an_eligible_comparator() -> None:
    data = _comparison_data().copy()
    data['CompetitorsMentioned'] = ''

    recommendations = generate_recommendations(data, max_recommendations=1)

    assert recommendations.iloc[0]['Comparator'] == 'No eligible comparator'
    assert recommendations.iloc[0]['Comparable peer'] == 'No configured comparable peer'
    assert recommendations.iloc[0]['Evidence quality rating'] == 'Insufficient'
