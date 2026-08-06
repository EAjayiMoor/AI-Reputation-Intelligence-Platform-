from __future__ import annotations

import pandas as pd

from src.scoring import aggregate_scores, score_results


def _base_results_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                'PromptID': 'P001',
                'SouthamptonVisible': 1,
                'SouthamptonRank': 1,
                'CitationSources': 'southampton.ac.uk',
            },
            {
                'PromptID': 'P002',
                'SouthamptonVisible': 1,
                'SouthamptonRank': '',
                'CitationSources': '',
            },
            {
                'PromptID': 'P003',
                'SouthamptonVisible': 0,
                'SouthamptonRank': '',
                'CitationSources': '',
            },
        ]
    )


def test_visibility_score_is_visible_divided_by_total_times_100() -> None:
    scored = score_results(_base_results_df())
    overall = aggregate_scores(scored).iloc[0]

    assert overall['visibility_score'] == 66.67


def test_rank_score_mapping_includes_unknown_rank_and_not_visible() -> None:
    raw = pd.DataFrame(
        [
            {'PromptID': 'P001', 'SouthamptonVisible': 1, 'SouthamptonRank': 1, 'CitationSources': ''},
            {'PromptID': 'P002', 'SouthamptonVisible': 1, 'SouthamptonRank': 2, 'CitationSources': ''},
            {'PromptID': 'P003', 'SouthamptonVisible': 1, 'SouthamptonRank': 3, 'CitationSources': ''},
            {'PromptID': 'P004', 'SouthamptonVisible': 1, 'SouthamptonRank': 4, 'CitationSources': ''},
            {'PromptID': 'P005', 'SouthamptonVisible': 1, 'SouthamptonRank': 7, 'CitationSources': ''},
            {'PromptID': 'P006', 'SouthamptonVisible': 1, 'SouthamptonRank': '', 'CitationSources': ''},
            {'PromptID': 'P007', 'SouthamptonVisible': 0, 'SouthamptonRank': '', 'CitationSources': ''},
        ]
    )

    scored = score_results(raw)

    expected_rank_scores = [100, 90, 80, 70, 50, 40, 0]
    assert scored['rank_score_row'].tolist() == expected_rank_scores


def test_rank_nan_for_visible_record_defaults_to_unknown_rank_score() -> None:
    raw = pd.DataFrame(
        [
            {
                'PromptID': 'P001',
                'SouthamptonVisible': 1,
                'SouthamptonRank': float('nan'),
                'CitationSources': '',
            }
        ]
    )

    scored = score_results(raw)
    assert scored.iloc[0]['rank_score_row'] == 40
