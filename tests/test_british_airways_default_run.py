from streamlit.testing.v1 import AppTest


def test_british_airways_opens_completed_baseline_and_can_switch_to_demo(tmp_path, monkeypatch):
    import json
    import pandas as pd
    from src.runs.store import RunStore
    from src.tenants import loader
    registry = tmp_path / 'registry'
    registry.mkdir()
    profile = json.loads((loader.TENANT_REGISTRY_DIR / 'british_airways.json').read_text())
    monkeypatch.setenv('AIRP_RUNS_DIR', str(tmp_path / 'runs'))
    store = RunStore()
    run = store.create(tenant_id='british_airways', name='Completed baseline',
        prompts=pd.DataFrame([{'PromptID':'BA001','Prompt':'Question'}]),
        source_name='input.csv', source_bytes=b'input')
    run['status'] = 'Complete'
    store._save_manifest(store.paths('british_airways',run['run_id'])['manifest'].parent,run)
    profile['default_run_id'] = run['run_id']
    demo_results = tmp_path / 'demo.csv'
    demo_results.write_text('ResultID\nDEMO-1\n')
    profile['data_paths']['results_path'] = str(demo_results)
    (registry / 'british_airways.json').write_text(json.dumps(profile))
    monkeypatch.setattr(loader, 'TENANT_REGISTRY_DIR', registry)
    app = AppTest.from_string('''
from src.tenants import load_tenant
from src.ui.run_context import render_run_selector, selected_run_id
import streamlit as st
render_run_selector(load_tenant('british_airways'))
st.write(selected_run_id('british_airways'))
''', default_timeout=30).run()
    assert not app.exception
    expected = run['run_id']
    assert app.sidebar.selectbox(key='_run_picker_british_airways').value == expected
    app.sidebar.selectbox(key='_run_picker_british_airways').set_value(None).run()
    assert not app.exception
    assert app.sidebar.selectbox(key='_run_picker_british_airways').value is None


def test_existing_empty_demo_selection_recovers_to_configured_baseline():
    app = AppTest.from_string('''
import streamlit as st
from src.ui.run_context import selected_run_id
st.session_state['selected_run_ids'] = {'british_airways': None}
st.write(selected_run_id('british_airways'))
''').run()
    assert not app.exception
    assert app.markdown[0].value == '20261124T150137_1dc5b31146e546d0b0a7899632bc7ea5'
