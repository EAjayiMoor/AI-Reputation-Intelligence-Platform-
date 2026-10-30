import hashlib

import pandas as pd
import pytest

from src.runs.demos import DEMO_RUNS
from src.scoring import competitor_mentions, institution_mentions_by_model
from src.ui.data import _load_core_data


@pytest.fixture
def response_files(tmp_path):
    prompts = pd.DataFrame([
        {'PromptID': str(i), 'Market': 'UK', 'Persona': 'Student', 'Subject': 'Engineering',
         'Category': 'Careers', 'Platform': 'OpenRouter', 'Prompt': prompt}
        for i, prompt in enumerate([
            'Which universities offer engineering?', 'Compare University of Cambridge options.',
            'Where should I study?', 'Which universities have research partnerships?'])
    ])
    results = pd.DataFrame([
        {'ResultID': str(i), 'PromptID': str(i), 'Platform': 'OpenRouter',
         'ResponseText': response, 'OrgVisible': int(i == 0), 'OrgRank': '',
         'CompetitorsMentioned': '', 'CitationSources': '', 'RunDate': '2026-10-29',
         'ModelName': 'model-a' if i < 2 else 'model-b'}
        for i, response in enumerate([
            'University of Cambridge and Cambridge University. UCL. University of Southampton.',
            'University of Cambridge and University of Oxford.',
            'Living in Bath, York, Reading or Cambridge offers options.',
            'Cambridge University and Oxford University.'])
    ])
    paths = (tmp_path / 'prompts.csv', tmp_path / 'results.csv')
    prompts.to_csv(paths[0], index=False)
    results.to_csv(paths[1], index=False)
    return paths


@pytest.mark.parametrize('demo', DEMO_RUNS)
def test_demo_reextracts_deduplicates_and_excludes_named_prompts(response_files, demo):
    before = [hashlib.sha256(p.read_bytes()).hexdigest() for p in response_files]
    prompts, results, scored = _load_core_data(*response_files, demo['org_id'], demo['run_id'])
    assert results.iloc[0]['CompetitorsMentioned'] == 'University of Cambridge, University College London'
    assert results.iloc[2]['CompetitorsMentioned'] == ''
    assert prompts['CompetitorPromptEligible'].tolist() == [True, False, True, True]
    counts = competitor_mentions(scored).set_index('Competitor')['Mentions']
    assert counts['University of Cambridge'] == 2
    assert counts['University of Oxford'] == 1  # named prompt is excluded
    models = institution_mentions_by_model(scored)
    cambridge = models[models['Institution'] == 'University of Cambridge'].set_index('ModelName')
    assert cambridge.loc['model-a', 'EligibleResponses'] == 1
    assert cambridge.loc['model-b', 'EligibleResponses'] == 2
    assert cambridge.loc['model-b', 'MentionRate'] == 50.0
    assert before == [hashlib.sha256(p.read_bytes()).hexdigest() for p in response_files]


def test_ordinary_runs_keep_existing_competitor_data(response_files):
    _, results, _ = _load_core_data(*response_files, 'southampton', 'ordinary-run')
    assert results['CompetitorsMentioned'].fillna('').eq('').all()


@pytest.mark.parametrize('demo', DEMO_RUNS)
def test_competitor_view_renders_rates_and_filters_original_evidence(response_files, demo):
    from streamlit.testing.v1 import AppTest
    script = f'''
from types import SimpleNamespace
from src.ui.data import _load_core_data
from src.ui.demo_competitors import render_demo_competitors
_, _, scored = _load_core_data({str(response_files[0])!r}, {str(response_files[1])!r}, 'southampton', {demo['run_id']!r})
render_demo_competitors(SimpleNamespace(display_name='University of Southampton'), {demo!r}, scored)
'''
    app = AppTest.from_string(script, default_timeout=60).run()
    assert not app.exception
    metrics = {metric.label: metric.value for metric in app.metric}
    assert metrics['Top recognised competitor'] == 'University of Cambridge'
    assert metrics['Competitor response mention rate'] == '66.7% (2/3)'
    assert not any('unavailable' in item.value for item in app.info)
    app.selectbox(key=f"competitor_evidence_{demo['run_id']}").select('University of Cambridge').run()
    assert not app.exception
    evidence = app.dataframe[-1].value
    assert len(evidence) == 2
    assert set(evidence['PromptID'].astype(str)) == {'0', '3'}
    assert 'ResponseText' in evidence
