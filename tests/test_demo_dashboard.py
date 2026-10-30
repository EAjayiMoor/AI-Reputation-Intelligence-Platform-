import pytest
from streamlit.testing.v1 import AppTest

from src.runs.demos import DEMO_RUNS, demo_for_run


def test_demo_profiles_require_both_organisation_and_run():
    for demo in DEMO_RUNS:
        assert demo_for_run(demo['org_id'], demo['run_id']) == demo
        assert demo_for_run('another_org', demo['run_id']) is None
    assert demo_for_run('southampton', None) is None
    assert demo_for_run('southampton', 'another_run') is None


@pytest.mark.parametrize('scenario', ['careers', 'research'])
def test_demo_metrics_filters_and_response_evidence(scenario):
    script = '''
from types import SimpleNamespace
import pandas as pd
from src.ui.demo_dashboard import render_demo_dashboard
from src.runs.demos import DEMO_RUNS
demo = next(d for d in DEMO_RUNS if d['scenario'] == SCENARIO)
frame = pd.DataFrame([
 {'PromptID':'p1','Market':'UK','Persona':'Student','Subject':'Engineering','Category':'Careers',
  'ModelName':'model-a','Prompt':'Question one','ResponseText':'Original response one',
  'visible_bool':True,'Recommended':True,'citation_score_row':100,'CitationSources':'https://example.com'},
 {'PromptID':'p2','Market':'India','Persona':'Researcher','Subject':'Psychology','Category':'Research',
  'ModelName':'model-b','Prompt':'Question two','ResponseText':'Original response two',
  'visible_bool':False,'Recommended':False,'citation_score_row':0,'CitationSources':''},
])
render_demo_dashboard(SimpleNamespace(domains=('southampton.ac.uk',)), demo, frame)
'''.replace('SCENARIO', repr(scenario))
    app = AppTest.from_string(script, default_timeout=30).run()
    assert not app.exception
    metrics = {m.label: m.value for m in app.metric}
    assert metrics['Southampton mention rate'] == '50.0% (1/2)'
    assert metrics['Citation coverage'] == '50.0% (1/2)'
    assert 'Most-mentioned competitor' not in metrics
    assert 'Reputation score' not in metrics
    assert any('recognised university list' in info.value for info in app.info)
    assert any('Original response one' in text.value for text in app.text)
    signal = 'Recommendation wording when Southampton is mentioned'
    assert (signal in metrics) == (scenario == 'careers')
    app.selectbox(key=f"demo_{next(d for d in DEMO_RUNS if d['scenario']==scenario)['run_id']}_Subject").select('Psychology').run()
    assert not app.exception
    metrics = {m.label: m.value for m in app.metric}
    assert metrics['Saved responses'] == '1'
    assert metrics['Southampton mention rate'] == '0.0% (0/1)'
