from __future__ import annotations

import pandas as pd

from src.scoring import institution_mention_index, institution_mentions_by_model, score_results


def test_institution_index_adds_southampton_and_normalises_leader_to_100() -> None:
    raw = pd.DataFrame(
        [
            {
                'PromptID': f'P{index}',
                'SouthamptonVisible': 1 if index <= 2 else 0,
                'SouthamptonRank': '',
                'CitationSources': '',
                'CompetitorsMentioned': 'Competitor A, Competitor B' if index <= 2 else 'Competitor A',
            }
            for index in range(1, 5)
        ]
    )

    comparison = institution_mention_index(score_results(raw))
    values = comparison.set_index('Institution')

    assert values.loc['Competitor A', 'RelativeMentionIndex'] == 100.0
    assert values.loc['University of Southampton', 'Mentions'] == 2
    assert values.loc['University of Southampton', 'RelativeMentionIndex'] == 50.0
    assert values.loc['University of Southampton', 'InstitutionType'] == 'Southampton'


def test_institution_index_excludes_southampton_from_competitor_duplicates() -> None:
    raw = pd.DataFrame(
        [{
            'PromptID': 'P1',
            'SouthamptonVisible': 1,
            'SouthamptonRank': '',
            'CitationSources': '',
            'CompetitorsMentioned': 'University of Southampton, Competitor A',
        }]
    )

    comparison = institution_mention_index(score_results(raw))

    assert comparison['Institution'].eq('University of Southampton').sum() == 1


def test_institution_index_excludes_named_prompt_rows() -> None:
    raw = pd.DataFrame(
        [
            {
                'PromptID': 'P1',
                'SouthamptonVisible': 1,
                'SouthamptonRank': '',
                'CitationSources': '',
                'CompetitorsMentioned': 'Prompted Competitor',
                'CompetitorPromptEligible': False,
            },
            {
                'PromptID': 'P2',
                'SouthamptonVisible': 0,
                'SouthamptonRank': '',
                'CitationSources': '',
                'CompetitorsMentioned': 'Organic Competitor',
                'CompetitorPromptEligible': True,
            },
        ]
    )

    comparison = institution_mention_index(score_results(raw))

    assert 'Prompted Competitor' not in comparison['Institution'].tolist()
    assert 'Organic Competitor' in comparison['Institution'].tolist()


def test_model_breakdown_reconciles_to_organic_totals() -> None:
    raw = pd.DataFrame(
        [
            {
                'PromptID': 'P1',
                'ModelName': 'model-a',
                'SouthamptonVisible': 1,
                'SouthamptonRank': '',
                'CitationSources': '',
                'CompetitorsMentioned': 'Competitor A',
                'CompetitorPromptEligible': True,
            },
            {
                'PromptID': 'P1',
                'ModelName': 'model-b',
                'SouthamptonVisible': 0,
                'SouthamptonRank': '',
                'CitationSources': '',
                'CompetitorsMentioned': 'Competitor A',
                'CompetitorPromptEligible': True,
            },
            {
                'PromptID': 'P2',
                'ModelName': 'model-a',
                'SouthamptonVisible': 1,
                'SouthamptonRank': '',
                'CitationSources': '',
                'CompetitorsMentioned': 'Prompted Competitor',
                'CompetitorPromptEligible': False,
            },
        ]
    )

    breakdown = institution_mentions_by_model(score_results(raw))
    totals = breakdown.groupby('Institution')['Mentions'].sum()

    assert totals['Competitor A'] == 2
    assert totals['University of Southampton'] == 1
    assert 'Prompted Competitor' not in totals.index
