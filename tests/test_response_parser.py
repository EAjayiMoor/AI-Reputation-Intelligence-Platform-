from __future__ import annotations

import pandas as pd

from src.analysis import (
    enrich_results_frame,
    extract_competitors,
    extract_southampton_rank,
    prompt_names_institution,
)


def test_extracts_numbered_southampton_rank() -> None:
    response = '1. University of Oxford\n6. **University of Southampton** – Strong engineering.'
    assert extract_southampton_rank(response, intent='Subject-Specific Reputation') == 6


def test_does_not_treat_comparison_section_number_as_rank() -> None:
    response = '1. **University of Southampton**\n2. **University of Bristol**'
    assert extract_southampton_rank(response, intent='Direct Comparison') is None


def test_extracts_and_canonicalises_competitors_without_southampton() -> None:
    response = 'Oxford University, UCL, the University of Bath, and the University of Southampton.'
    assert extract_competitors(response) == [
        'University of Oxford',
        'University College London',
        'University of Bath',
    ]


def test_enrichment_updates_live_analysis_fields() -> None:
    results = pd.DataFrame(
        [
            {
                'PromptID': 'P1',
                'ResponseText': '1. University of Oxford\n4. University of Southampton',
            }
        ]
    )
    prompts = pd.DataFrame([{'PromptID': 'P1', 'Intent': 'General Awareness'}])

    enriched = enrich_results_frame(results, prompts)

    assert enriched.iloc[0]['SouthamptonVisible'] == 1
    assert enriched.iloc[0]['SouthamptonRank'] == 4
    assert enriched.iloc[0]['CompetitorsMentioned'] == 'University of Oxford'


def test_prompt_institution_detection_excludes_named_comparisons() -> None:
    assert prompt_names_institution(
        'How does Southampton compare with Durham for AI?',
        intent='Direct Comparison',
    )
    assert prompt_names_institution(
        'What is the University of Oxford known for?',
        intent='General Awareness',
    )
    assert not prompt_names_institution(
        'Which UK universities are best for engineering?',
        intent='General Awareness',
    )
