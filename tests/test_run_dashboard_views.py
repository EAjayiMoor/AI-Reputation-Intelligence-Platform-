from dataclasses import replace

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from src.execution.openrouter_runner import OpenRouterRunner
from src.runs.executor import execute_run
from src.runs.store import RunStore
from src.runs.upload import INPUT_COLUMNS, prepare_prompts
from src.tenants import load_tenant


def demo_run(tmp_path, state='Complete', categories=None):
    store = RunStore(tmp_path)
    categories = categories or ['Careers & Employability', 'Research', 'Careers & Employability']
    prompts = prepare_prompts(pd.DataFrame([
        ['UK', 'Student', subject, category, f'Which universities offer strong {subject} opportunities?']
        for subject, category in zip(['Engineering', 'Medicine', 'Business'], categories)
    ], columns=INPUT_COLUMNS), organisation_name='University of Southampton').prompts
    run = store.create(tenant_id='southampton', name=f'{state} rehearsal', prompts=prompts,
                       source_name='fixture.csv', source_bytes=b'fixture input', mode='dry_run')
    class FixtureRunner:
        def __init__(self, config):
            self.runner = OpenRouterRunner(config)
        def run_prompt(self, **kwargs):
            result = self.runner.run_prompt(**kwargs)
            if state == 'Partial' and kwargs['prompt_id'] == 'UPLOAD-00001' and self.runner._config.model_name == 'test/a':
                return replace(result, success=False, response_text='', error_message='Fixture failure')
            return replace(result, response_text='DRY_RUN: Fixture. 1. University of Southampton is recommended for strong careers support. 2. University of Cambridge offers research. Cited pages: https://southampton.ac.uk/careers')
    if state != 'Ready':
        execute_run(store, load_tenant('southampton'), run['run_id'], ['test/a', 'test/b'], runner_factory=FixtureRunner)
    return store, run


def open_page(run, page):
    app = AppTest.from_file('app.py', default_timeout=40)
    app.session_state['active_org_id'] = 'southampton'
    app.session_state['selected_run_ids'] = {'southampton': run['run_id']}
    return app.run().switch_page(page).run()


@pytest.mark.parametrize('state', ['Ready', 'Partial', 'Complete'])
@pytest.mark.parametrize('page', [
    'pages/04_Executive_Dashboard.py', 'pages/05_Prompt_Bank_Explorer.py',
    'pages/06_Audience_Journey_Simulator.py', 'pages/07_Visibility_Analysis.py',
    'pages/08_Competitor_Analysis.py', 'pages/09_Recommendations.py',
    'pages/10_Topic_Persona_Diagnostics.py', 'pages/11_Microsite_Export.py',
])
def test_all_views_render_uploaded_run_with_status_and_coverage(tmp_path, monkeypatch, state, page):
    monkeypatch.setenv('AIRP_RUNS_DIR', str(tmp_path))
    _, run = demo_run(tmp_path, state)
    app = open_page(run, page)
    assert not app.exception
    assert not app.error
    captions = [item.value for item in app.caption]
    assert any(state in value and run['name'] in value for value in captions)
    expected = {'Ready': '0 saved responses', 'Partial': '5/6', 'Complete': '6/6'}[state]
    assert any(expected in value for value in captions)


def test_category_filters_results_and_does_not_carry_stale_values_to_another_run(tmp_path, monkeypatch):
    monkeypatch.setenv('AIRP_RUNS_DIR', str(tmp_path))
    _, first = demo_run(tmp_path)
    _, second = demo_run(tmp_path, categories=['Another category'] * 3)
    app = open_page(first, 'pages/04_Executive_Dashboard.py')
    category = next(item for item in app.sidebar.selectbox if item.label == 'Category')
    category.set_value('Careers & Employability').run()
    assert not app.exception
    assert next(metric.value for metric in app.metric if metric.label == 'Prompts in view') == '2'
    assert any('4/4' in metric.value for metric in app.metric if metric.label == 'Response presence')
    app.sidebar.selectbox(key='_run_picker_southampton').set_value(second['run_id']).run()
    assert not app.exception
    assert next(item.value for item in app.sidebar.selectbox if item.label == 'Category') == 'All'
    assert next(metric.value for metric in app.metric if metric.label == 'Prompts in view') == '3'


def test_live_run_export_never_offers_banked_snapshot(tmp_path, monkeypatch):
    from src.export import microsite
    monkeypatch.setattr(microsite, 'missing_microsite_assets', lambda: pytest.fail('A selected live run must not inspect banked screenshot assets'))
    monkeypatch.setenv('AIRP_RUNS_DIR', str(tmp_path))
    _, run = demo_run(tmp_path)
    app = open_page(run, 'pages/11_Microsite_Export.py')
    assert not app.exception
    labels = [item.label for item in app.get('download_button')]
    assert 'Download snapshot microsite (.zip)' not in labels
    assert 'Download rendered microsite (.zip)' in labels or 'Download rendered microsite (pro) (.zip)' in labels


def test_missing_banked_files_do_not_block_uploading_a_new_run(tmp_path, monkeypatch):
    monkeypatch.setenv('AIRP_RUNS_DIR', str(tmp_path))
    app = AppTest.from_string(f'''
from dataclasses import replace
from src.tenants import load_tenant
from src.tenants.models import TenantDataPaths
from src.ui.run_context import render_run_selector
tenant = replace(load_tenant('southampton'), data_paths=TenantDataPaths(
    prompts_path={str(tmp_path / 'missing_prompts.csv')!r}, results_path={str(tmp_path / 'missing_results.csv')!r}))
render_run_selector(tenant)
''', default_timeout=30).run()
    assert not app.exception


@pytest.mark.parametrize('page', [
    'pages/04_Executive_Dashboard.py', 'pages/05_Prompt_Bank_Explorer.py',
    'pages/06_Audience_Journey_Simulator.py', 'pages/07_Visibility_Analysis.py',
    'pages/08_Competitor_Analysis.py', 'pages/09_Recommendations.py',
    'pages/10_Topic_Persona_Diagnostics.py', 'pages/11_Microsite_Export.py',
])
def test_all_analysis_pages_can_switch_back_to_saved_demo(tmp_path, monkeypatch, page):
    monkeypatch.setenv('AIRP_RUNS_DIR', str(tmp_path))
    _, run = demo_run(tmp_path)
    app = open_page(run, page)
    app.sidebar.selectbox(key='_run_picker_southampton').set_value(None).run()
    assert not app.exception
    assert not app.error
    assert app.session_state['selected_run_ids']['southampton'] is None


def test_visibility_percentages_report_real_response_denominators(tmp_path, monkeypatch):
    monkeypatch.setenv('AIRP_RUNS_DIR', str(tmp_path))
    _, run = demo_run(tmp_path)
    app = open_page(run, 'pages/07_Visibility_Analysis.py')
    for label in ['Mention rate', 'Recommended when mentioned', 'Shortlisted when mentioned', 'Citation coverage', 'Positive association']:
        value = next(metric.value for metric in app.metric if metric.label == label)
        assert '/6)' in value


def test_uploaded_category_labels_are_not_reinterpreted_as_missing_values(tmp_path, monkeypatch):
    monkeypatch.setenv('AIRP_RUNS_DIR', str(tmp_path))
    _, run = demo_run(tmp_path, categories=['NA'] * 3)
    app = open_page(run, 'pages/04_Executive_Dashboard.py')
    assert not app.exception
    assert 'NA' in next(item.options for item in app.sidebar.selectbox if item.label == 'Category')
