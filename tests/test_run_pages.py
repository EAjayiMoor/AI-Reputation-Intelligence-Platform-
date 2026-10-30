from io import BytesIO

import pandas as pd
from streamlit.testing.v1 import AppTest

from src.runs.store import RunStore
from src.runs.upload import prepare_prompts, read_upload


def content():
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        pd.DataFrame([['UK', 'Student', 'Engineering', 'Careers', 'Compare engineering careers.'],
                      ['India', 'Parent', 'Medicine', 'Careers', 'Compare medicine careers.']],
                     columns=['Market', 'Persona', 'Subject', 'Category', 'Prompt']).to_excel(
                         writer, index=False, sheet_name='Prompts')
    return output.getvalue()


def test_preview_creates_simulated_run_with_original_excel_and_all_rows(tmp_path, monkeypatch):
    monkeypatch.setenv('AIRP_RUNS_DIR', str(tmp_path))
    original = content()
    script = f'''
import streamlit as st
from src.tenants import load_tenant
from src.ui.run_context import render_run_selector
from src.ui.run_upload import render_upload_preview
tenant = render_run_selector(load_tenant('southampton'))
render_upload_preview({original!r}, 'client.xlsx', tenant)
'''
    app = AppTest.from_string(script, default_timeout=30).run()
    assert not app.exception
    assert len(app.dataframe[0].value) == 2
    app.radio[0].set_value('Simulated').run()
    app.text_input[0].set_value('Careers rehearsal').run()
    app.button[0].click().run()
    assert not app.exception
    store = RunStore(tmp_path)
    run, = store.list_runs('southampton')
    assert run['name'] == 'Careers rehearsal'
    assert run['mode'] == 'dry_run'
    assert run['source_sheet'] == 'Prompts'
    paths = store.paths('southampton', run['run_id'])
    assert paths['source'].read_bytes() == original
    assert len(pd.read_csv(paths['prompts'])) == 2
    assert app.session_state['selected_run_ids']['southampton'] == run['run_id']
    assert any('Simulated run selected' in item.value for item in app.warning)


def test_invalid_preview_never_offers_run_creation(tmp_path, monkeypatch):
    monkeypatch.setenv('AIRP_RUNS_DIR', str(tmp_path))
    script = '''
from src.tenants import load_tenant
from src.ui.run_upload import render_upload_preview
render_upload_preview(b'Market,Persona,Subject,Category,Prompt\\nUK,,Medicine,Careers,Q',
                      'client.csv', load_tenant('southampton'))
'''
    app = AppTest.from_string(script, default_timeout=30).run()
    assert not app.exception
    assert app.error
    assert not app.button
    assert RunStore(tmp_path).list_runs('southampton') == []


def test_malformed_workbook_shows_error_instead_of_crashing():
    app = AppTest.from_string('''
from src.tenants import load_tenant
from src.ui.run_upload import render_upload_preview
render_upload_preview(b'not an Excel workbook', 'broken.xlsx', load_tenant('southampton'))
''', default_timeout=30).run()
    assert not app.exception
    assert app.error
    assert not app.button


def test_run_selection_survives_page_navigation_and_saved_switch(tmp_path, monkeypatch):
    monkeypatch.setenv('AIRP_RUNS_DIR', str(tmp_path))
    original = content()
    prompts = prepare_prompts(read_upload(original, 'client.xlsx'), organisation_name='University of Southampton').prompts
    store = RunStore(tmp_path)
    run = store.create(tenant_id='southampton', name='Careers', prompts=prompts,
                       source_name='client.xlsx', source_bytes=original)
    app = AppTest.from_file('app.py', default_timeout=30)
    app.session_state['active_org_id'] = 'southampton'
    app.run()
    assert not app.exception
    picker = '_run_picker_southampton'
    app.sidebar.selectbox(key=picker).set_value(run['run_id']).run()
    app.switch_page('pages/02_Data_Onboarding.py').run()
    assert not app.exception
    assert not app.error
    app.switch_page('pages/05_Prompt_Bank_Explorer.py').run()
    assert not app.exception
    assert not app.error
    assert app.session_state['selected_run_ids']['southampton'] == run['run_id']
    assert any(metric.label == 'Prompt bank total' and metric.value == '2' for metric in app.metric)
    app.switch_page('pages/04_Executive_Dashboard.py').run()
    assert not app.exception
    assert not app.error
    app.sidebar.selectbox(key=picker).set_value(None).run()
    assert not app.exception
    assert not app.error
    assert app.session_state['selected_run_ids']['southampton'] is None
    assert any('Saved demo' in item.value for item in app.caption)
    app.switch_page('pages/03_Execution.py').run()
    assert not app.exception
    assert not app.button
    assert any('read-only' in item.value for item in app.info)


def test_sessions_and_cache_keep_same_prompt_ids_in_different_runs_separate(tmp_path, monkeypatch):
    from src.execution.storage import append_openrouter_results
    monkeypatch.setenv('AIRP_RUNS_DIR', str(tmp_path))
    store = RunStore(tmp_path)
    runs = []
    for label in ['Engineering', 'Medicine']:
        prompts = prepare_prompts(pd.DataFrame([['UK', 'Student', label, 'Careers', 'Q']],
                                  columns=['Market', 'Persona', 'Subject', 'Category', 'Prompt']),
                                  organisation_name='University of Southampton').prompts
        run = store.create(tenant_id='southampton', name=label, prompts=prompts,
                           source_name='test.csv', source_bytes=b'test input')
        append_openrouter_results(store.paths('southampton', run['run_id'])['results'], [
            {'PromptID': prompts.iloc[0]['PromptID'], 'Platform': 'OpenRouter',
             'ResponseText': label, 'OrgVisible': 0, 'ModelName': 'test/model'}])
        runs.append(run)
    script = '''
import streamlit as st
from src.ui.data import load_core_data
p, r, s = load_core_data(org_id='southampton')
st.session_state['observed_subject'] = p.iloc[0]['Subject']
st.session_state['observed_response'] = r.iloc[0]['ResponseText']
'''
    apps = []
    for run in runs:
        app = AppTest.from_string(script, default_timeout=30)
        app.session_state['selected_run_ids'] = {'southampton': run['run_id']}
        app.run()
        assert not app.exception
        assert app.session_state['observed_subject'] == run['name']
        assert app.session_state['observed_response'] == run['name']
        apps.append(app)
    apps[0].run()
    assert apps[0].session_state['observed_response'] == 'Engineering'
