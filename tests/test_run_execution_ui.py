from pathlib import Path
import json

import pandas as pd
from streamlit.testing.v1 import AppTest

from src.runs.store import RunStore
from src.runs.upload import INPUT_COLUMNS, prepare_prompts


def ready_run(tmp_path, monkeypatch, mode='dry_run'):
    monkeypatch.setenv('AIRP_RUNS_DIR', str(tmp_path))
    monkeypatch.setenv('OPENROUTER_API_KEY', '')
    monkeypatch.setenv('OPENROUTER_MODELS', 'test/a,test/b,test/c')
    store = RunStore(tmp_path)
    prompts = prepare_prompts(pd.DataFrame([['UK', 'Student', s, 'Careers', 'Q']
                             for s in ['Engineering', 'Medicine']], columns=INPUT_COLUMNS),
                             organisation_name='University of Southampton').prompts
    return store, store.create(tenant_id='southampton', name='Rehearsal', prompts=prompts,
                               source_name='test.csv', source_bytes=b'input', mode=mode)


def open_execution(run):
    app = AppTest.from_file('app.py', default_timeout=30)
    app.session_state['active_org_id'] = 'southampton'
    app.session_state['selected_run_ids'] = {'southampton': run['run_id']}
    return app.run().switch_page('pages/03_Execution.py').run()


def test_simulated_execution_completes_all_rows_and_dashboard_loads(tmp_path, monkeypatch):
    store, run = ready_run(tmp_path, monkeypatch)
    banked_paths = [Path('data/UoS_Prompt_Library_normalised.csv'), Path('data/uos_openrouter_results.csv'),
                    Path('src/tenants/registry/southampton.json')]
    banked = {p: p.read_bytes() for p in banked_paths}
    app = open_execution(run)
    assert not app.exception
    assert any(m.label == 'Planned requests' and m.value == '6' for m in app.metric)
    assert not app.button(key=f"execute_run_{run['run_id']}").disabled
    app.button(key=f"execute_run_{run['run_id']}").click().run()
    assert not app.exception
    manifest = store.get('southampton', run['run_id'])
    assert manifest['status'] == 'Complete'
    assert manifest['mode'] == 'dry_run'
    assert manifest['completed_requests'] == 6
    assert app.multiselect[0].disabled
    assert app.button(key=f"execute_run_{run['run_id']}").disabled
    app.switch_page('pages/04_Executive_Dashboard.py').run()
    assert not app.exception
    assert not app.error
    assert all(path.read_bytes() == value for path, value in banked.items())


def test_live_execution_without_credentials_is_disabled(tmp_path, monkeypatch):
    store, run = ready_run(tmp_path, monkeypatch, mode='live')
    app = open_execution(run)
    assert not app.exception
    assert app.button(key=f"execute_run_{run['run_id']}").disabled
    assert any('OPENROUTER_API_KEY' in item.value for item in app.info)
    assert store.get('southampton', run['run_id'])['status'] == 'Ready'


def test_active_run_cannot_be_executed_from_second_session(tmp_path, monkeypatch):
    store, run = ready_run(tmp_path, monkeypatch)
    with store.execution_lock('southampton', run['run_id']):
        app = open_execution(run)
        assert not app.exception
        assert app.button(key=f"execute_run_{run['run_id']}").disabled
        assert any('another session' in item.value for item in app.info)


def test_retry_button_executes_only_unfinished_requests(tmp_path, monkeypatch):
    from dataclasses import replace
    from src.runs import executor
    from src.execution.openrouter_runner import OpenRouterRunner
    store, run = ready_run(tmp_path, monkeypatch)
    monkeypatch.setenv('OPENROUTER_MODELS', 'test/a')
    calls = []
    class FailOnce:
        def __init__(self, config):
            self.runner = OpenRouterRunner(config)
        def run_prompt(self, **kwargs):
            calls.append((kwargs['prompt_id'], self.runner._config.model_name))
            result = self.runner.run_prompt(**kwargs)
            if len(calls) == 1:
                return replace(result, success=False, response_text='', error_message='Temporary failure')
            return result
    monkeypatch.setattr(executor, 'OpenRouterRunner', FailOnce)
    app = open_execution(run)
    app.multiselect[0].set_value(['test/a']).run()
    button = f"execute_run_{run['run_id']}"
    app.button(key=button).click().run()
    assert not app.exception
    assert store.get('southampton', run['run_id'])['status'] == 'Partial'
    assert app.button(key=button).label == 'Retry unfinished requests'
    app.button(key=button).click().run()
    assert not app.exception
    assert store.get('southampton', run['run_id'])['status'] == 'Complete'
    assert len(calls) == 3


def test_interrupted_run_with_all_responses_can_finalize_without_repeating_calls(tmp_path, monkeypatch):
    store, run = ready_run(tmp_path, monkeypatch)
    app = open_execution(run)
    button = f"execute_run_{run['run_id']}"
    app.button(key=button).click().run()
    path = store.paths('southampton', run['run_id'])['manifest']
    manifest = json.loads(path.read_text())
    attempted = manifest['attempted_requests']
    manifest.update(status='Running', completed_requests=0)
    path.write_text(json.dumps(manifest))
    app.run()
    assert app.button(key=button).label == 'Finalize saved run'
    assert not app.button(key=button).disabled
    app.button(key=button).click().run()
    assert not app.exception
    assert store.get('southampton', run['run_id'])['status'] == 'Complete'
    assert store.get('southampton', run['run_id'])['attempted_requests'] == attempted
