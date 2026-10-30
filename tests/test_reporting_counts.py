import pandas as pd

from src.analysis import compute_scope_metrics, segment_summary


def test_owned_source_share_retains_the_real_cited_response_count():
    frame = pd.DataFrame({'PromptID': ['P1', 'P2'], 'visible_bool': [True, False],
                          'CitationSources': ['https://southampton.ac.uk/careers', 'https://example.com']})
    metrics = compute_scope_metrics(frame, owned_domains=['southampton.ac.uk'])
    assert metrics['owned_citation_responses'] == 1
    assert metrics['citation_responses'] == 2
    assert metrics['owned_source_share'] == 50


def test_segment_citation_percentage_retains_actual_numerator():
    frame = pd.DataFrame({'PromptID': ['P1', 'P2'], 'Persona': ['Student', 'Student'],
                          'Subject': ['Engineering', 'Engineering'],
                          'Mentioned': [True, False], 'CitationPresent': [True, False]})
    row = segment_summary(frame, ['Persona', 'Subject']).iloc[0]
    assert row['CitedResponses'] == 1
    assert row['Responses'] == 2
    assert row['CitationRate'] == 50
