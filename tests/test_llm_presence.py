from __future__ import annotations

import pandas as pd

from src.analysis import (
    MEASUREMENT_COLUMNS,
    competitive_breakdown,
    competitive_cooccurrence,
    enrich_llm_presence,
    outlier_responses,
    run_history_summary,
    segment_summary,
)


def test_enriches_recommendation_citation_rank_and_sentiment() -> None:
    frame = pd.DataFrame(
        [{
            'PromptID': 'P1',
            'PromptMentionType': 'Organic',
            'ResponseText': (
                '1. British Gas Business\n'
                '2. Corona Energy is a strong, trusted choice and is recommended for multi-site customers.\n'
                'Sources: https://coronaenergy.co.uk'
            ),
            'OrgVisible': 1,
            'OrgRank': 2,
            'CitationSources': '',
            'CompetitorsMentioned': 'British Gas Business',
        }]
    )

    enriched = enrich_llm_presence(
        frame,
        organisation_name='Corona Energy',
        competitor_aliases={'British Gas Business': ('British Gas',)},
    )
    row = enriched.iloc[0]

    assert all(column in enriched.columns for column in MEASUREMENT_COLUMNS)
    assert bool(row['Mentioned'])
    assert bool(row['Organic'])
    assert bool(row['Recommended'])
    assert not bool(row['Shortlisted'])
    assert not bool(row['FirstMentioned'])
    assert row['ProminenceScore'] == 90
    assert bool(row['CitationPresent'])
    assert row['CitationCount'] == 1
    assert row['AssociationLabel'] == 'Positive'
    assert row['EvidenceConfidence'] == 'High'


def test_does_not_mark_target_recommended_when_only_competitor_is_recommended() -> None:
    frame = pd.DataFrame(
        [{
            'PromptMentionType': 'Prompted/direct',
            'ResponseText': 'British Gas Business is the recommended option. Corona Energy is also listed.',
            'OrgVisible': 1,
            'OrgRank': '',
            'CitationSources': '',
            'CompetitorsMentioned': 'British Gas Business',
        }]
    )

    row = enrich_llm_presence(
        frame,
        organisation_name='Corona Energy',
        competitor_aliases={'British Gas Business': ('British Gas',)},
    ).iloc[0]

    assert bool(row['Mentioned'])
    assert bool(row['Prompted'])
    assert not bool(row['Recommended'])
    assert row['AssociationLabel'] == 'Neutral'
    assert row['EvidenceConfidence'] == 'Medium'


def test_absent_target_is_low_confidence_and_keeps_row_count() -> None:
    frame = pd.DataFrame(
        [
            {'ResponseText': 'British Gas Business is a leading option.', 'CitationSources': ''},
            {'ResponseText': 'Corona Energy is shortlisted among the top few providers.', 'CitationSources': 'brief'},
        ]
    )
    enriched = enrich_llm_presence(
        frame,
        organisation_name='Corona Energy',
        competitor_aliases={'British Gas Business': ()},
    )

    assert len(enriched) == 2
    assert not bool(enriched.iloc[0]['Mentioned'])
    assert enriched.iloc[0]['AssociationLabel'] == 'Not mentioned'
    assert enriched.iloc[0]['EvidenceConfidence'] == 'Low'
    assert bool(enriched.iloc[1]['Shortlisted'])
    assert enriched.iloc[1]['CitationCount'] == 1


def test_negated_recommendation_and_shortlist_are_not_positive_signals() -> None:
    frame = pd.DataFrame(
        [{
            'ResponseText': 'Corona Energy is not recommended and is unlikely to be shortlisted.',
            'OrgVisible': 1,
            'CitationSources': '',
        }]
    )

    row = enrich_llm_presence(frame, organisation_name='Corona Energy').iloc[0]

    assert not bool(row['Recommended'])
    assert not bool(row['Shortlisted'])
    assert row['AssociationLabel'] == 'Negative'


def test_competitive_breakdown_measures_first_mentions_and_target_signals() -> None:
    frame = pd.DataFrame(
        [
            {
                'CompetitorPromptEligible': True,
                'ResponseText': '1. British Gas Business is recommended. 2. Corona Energy is also listed.',
            },
            {
                'CompetitorPromptEligible': True,
                'ResponseText': 'Corona Energy is shortlisted as an option.\nBritish Gas is also listed.',
            },
            {
                'CompetitorPromptEligible': False,
                'ResponseText': 'Corona Energy is recommended over British Gas.',
            },
        ]
    )
    summary = competitive_breakdown(
        frame,
        organisation_name='Corona Energy',
        competitor_aliases={'British Gas Business': ('British Gas',)},
    )

    target = summary[summary['Entity'] == 'Corona Energy'].iloc[0]
    competitor = summary[summary['Entity'] == 'British Gas Business'].iloc[0]
    assert int(target['EligibleResponses']) == 2
    assert int(target['MentionedResponses']) == 2
    assert int(target['FirstMentionedResponses']) == 1
    assert int(target['ShortlistedResponses']) == 1
    assert int(target['RecommendedResponses']) == 1
    assert int(competitor['MentionedResponses']) == 2
    assert int(competitor['FirstMentionedResponses']) == 1
    assert int(competitor['RecommendedResponses']) == 1


def test_competitive_cooccurrence_counts_each_pair_once_per_response() -> None:
    frame = pd.DataFrame(
        [
            {'CompetitorPromptEligible': True, 'ResponseText': 'Corona Energy and British Gas are options.'},
            {'CompetitorPromptEligible': True, 'ResponseText': 'Corona Energy, British Gas and EDF Energy are listed.'},
            {'CompetitorPromptEligible': False, 'ResponseText': 'Corona Energy and British Gas are compared.'},
        ]
    )
    pairs = competitive_cooccurrence(
        frame,
        organisation_name='Corona Energy',
        competitor_aliases={
            'British Gas Business': ('British Gas',),
            'EDF Energy': ('EDF',),
        },
    )

    target_pair = pairs[(pairs['EntityA'] == 'British Gas Business') & (pairs['EntityB'] == 'Corona Energy')]
    assert len(target_pair) == 1
    assert int(target_pair.iloc[0]['CooccurrenceResponses']) == 2
    assert float(target_pair.iloc[0]['CooccurrenceRate']) == 100.0


def test_segment_summary_classifies_presence_and_evidence_gaps() -> None:
    frame = pd.DataFrame(
        [
            {
                'PromptID': 'P1', 'Persona': 'CFO', 'Subject': 'Energy',
                'Mentioned': True, 'ProminenceScore': 90, 'Recommended': True,
                'Shortlisted': False, 'CitationPresent': True, 'AssociationLabel': 'Positive',
                'reputation_score_row': 90,
            },
            {
                'PromptID': 'P2', 'Persona': 'CFO', 'Subject': 'Energy',
                'Mentioned': False, 'ProminenceScore': 0, 'Recommended': False,
                'Shortlisted': False, 'CitationPresent': False, 'AssociationLabel': 'Not mentioned',
                'reputation_score_row': 0,
            },
            {
                'PromptID': 'P3', 'Persona': 'Operations', 'Subject': 'Energy',
                'Mentioned': True, 'ProminenceScore': 40, 'Recommended': False,
                'Shortlisted': False, 'CitationPresent': False, 'AssociationLabel': 'Neutral',
                'reputation_score_row': 48,
            },
        ]
    )

    summary = segment_summary(frame)
    cfo = summary[(summary['Persona'] == 'CFO') & (summary['Subject'] == 'Energy')].iloc[0]
    operations = summary[summary['Persona'] == 'Operations'].iloc[0]
    assert float(cfo['MentionRate']) == 50.0
    assert cfo['Diagnosis'] == 'Presence gap'
    assert float(operations['CitationRate']) == 0.0
    assert operations['Diagnosis'] == 'Evidence gap'


def test_outlier_responses_keep_auditable_gap_and_strength_evidence() -> None:
    frame = pd.DataFrame(
        [
            {
                'PromptID': 'P1', 'ModelName': 'model-a', 'Persona': 'CFO', 'Subject': 'Energy',
                'Intent': 'Discovery', 'ResponseText': 'No target listed.', 'CitationSources': '',
                'CompetitorsMentioned': 'British Gas Business', 'Mentioned': False,
                'ProminenceScore': 0, 'Recommended': False, 'Shortlisted': False,
                'CitationPresent': False, 'AssociationLabel': 'Not mentioned', 'reputation_score_row': 0,
            },
            {
                'PromptID': 'P2', 'ModelName': 'model-a', 'Persona': 'CFO', 'Subject': 'Energy',
                'Intent': 'Discovery', 'ResponseText': 'Target is a recommended, trusted choice.', 'CitationSources': 'brief',
                'CompetitorsMentioned': '', 'Mentioned': True, 'ProminenceScore': 90,
                'Recommended': True, 'Shortlisted': False, 'CitationPresent': True,
                'AssociationLabel': 'Positive', 'reputation_score_row': 90,
            },
        ]
    )

    outliers = outlier_responses(frame, limit=5)
    assert set(outliers['OutlierType']) == {'Gap', 'Strength'}
    assert set(outliers['OutlierReason']) == {'Not mentioned', 'Recommended'}
    assert set(outliers['PromptID']) == {'P1', 'P2'}


def test_run_history_summary_calculates_matched_sweep_changes() -> None:
    frame = pd.DataFrame(
        [
            {
                'RunDate': '2026-01-01', 'PromptID': 'P1', 'ModelName': 'model-a',
                'Mentioned': False, 'Recommended': False, 'Shortlisted': False,
                'CitationPresent': False, 'ProminenceScore': 0, 'reputation_score_row': 0,
            },
            {
                'RunDate': '2026-01-02', 'PromptID': 'P1', 'ModelName': 'model-a',
                'Mentioned': True, 'Recommended': True, 'Shortlisted': True,
                'CitationPresent': True, 'ProminenceScore': 90, 'reputation_score_row': 90,
            },
        ]
    )

    history = run_history_summary(frame)
    assert history['Run'].tolist() == ['2026-01-01', '2026-01-02']
    assert float(history.iloc[1]['MentionRateChange']) == 100.0
    assert float(history.iloc[1]['ReputationScoreChange']) == 90.0
