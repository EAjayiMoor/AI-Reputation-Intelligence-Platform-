from io import BytesIO
import json
from pathlib import Path
from zipfile import ZipFile

import pytest
from streamlit.testing.v1 import AppTest

from src.runs.locking import RunBusyError
from src.runs.store import RunStore
from tests.test_run_dashboard_views import demo_run, open_page

from src.runs.history import build_run_archive


def test_run_download_is_a_consistent_snapshot_and_cannot_read_active_writer(tmp_path):
    store, run = demo_run(tmp_path, 'Partial')
    archive = build_run_archive(store, 'southampton', run['run_id'])
    with ZipFile(BytesIO(archive)) as bundle:
        assert set(bundle.namelist()) == {'input.csv', 'prompts.csv', 'results.csv', 'manifest.json', 'attempts.jsonl'}
        assert bundle.read('input.csv') == b'fixture input'
        assert json.loads(bundle.read('manifest.json'))['mode'] == 'dry_run'
        assert bundle.read('results.csv') == store.paths('southampton', run['run_id'])['results'].read_bytes()
    with store.execution_lock('southampton', run['run_id']):
        with pytest.raises(RunBusyError):
            build_run_archive(store, 'southampton', run['run_id'])


def test_history_rename_archive_restore_open_and_saved_switch(tmp_path, monkeypatch):
    monkeypatch.setenv('AIRP_RUNS_DIR', str(tmp_path))
    store, run = demo_run(tmp_path)
    banked = {path: Path(path).read_bytes() for path in [
        'data/UoS_Prompt_Library_normalised.csv', 'data/uos_openrouter_results.csv', 'src/tenants/registry/southampton.json']}
    app = open_page(run, 'pages/12_Run_History.py')
    assert not app.exception
    app.text_input(key=f"rename_{run['run_id']}").set_value('Client rehearsal').run()
    app.button(key=f"save_name_{run['run_id']}").click().run()
    assert not app.exception
    assert store.get('southampton', run['run_id'])['name'] == 'Client rehearsal'
    app.toggle(key='history_archived_southampton').set_value(True).run()
    app.button(key=f"archive_{run['run_id']}").click().run()
    assert not app.exception
    assert store.get('southampton', run['run_id'])['archived']
    assert app.session_state['selected_run_ids']['southampton'] is None
    app.button(key=f"restore_{run['run_id']}").click().run()
    assert not app.exception
    assert not store.get('southampton', run['run_id'])['archived']
    app.button(key=f"open_{run['run_id']}").click().run()
    assert not app.exception
    assert app.session_state['selected_run_ids']['southampton'] == run['run_id']
    app.sidebar.selectbox(key='_run_picker_southampton').set_value(None).run()
    assert not app.exception
    assert all(Path(path).read_bytes() == data for path, data in banked.items())


def test_history_blocks_metadata_updates_and_downloads_during_execution(tmp_path, monkeypatch):
    monkeypatch.setenv('AIRP_RUNS_DIR', str(tmp_path))
    store, run = demo_run(tmp_path)
    with store.execution_lock('southampton', run['run_id']):
        app = open_page(run, 'pages/12_Run_History.py')
        assert not app.exception
        assert app.button(key=f"archive_{run['run_id']}").disabled
        assert app.button(key=f"save_name_{run['run_id']}").disabled
        assert not app.get('download_button')
