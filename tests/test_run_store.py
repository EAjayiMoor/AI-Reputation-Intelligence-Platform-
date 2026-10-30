import json
from pathlib import Path

import pandas as pd
import pytest

from src.runs.store import RunStore


def store_at(root):
    return RunStore(root)


def prompts():
    return pd.DataFrame([{'PromptID': 'UPLOAD-001', 'Market': 'UK', 'Persona': 'Student',
                          'Subject': 'Engineering', 'Category': 'Careers', 'Prompt': 'Compare careers support.'}])


def create(store, **overrides):
    args = dict(tenant_id='southampton', name='Careers rehearsal', prompts=prompts(),
                source_name='client.xlsx', source_bytes=b'original workbook', mode='live')
    args.update(overrides)
    return store.create(**args)


def test_new_runs_have_separate_files_and_preserve_banked_data(tmp_path):
    banked = tmp_path / 'banked.csv'
    banked.write_bytes(b'banked data')
    store = store_at(tmp_path / 'runs')
    first, second = create(store), create(store)
    assert first['run_id'] != second['run_id']
    first_paths = store.paths('southampton', first['run_id'])
    second_paths = store.paths('southampton', second['run_id'])
    assert first_paths['results'] != second_paths['results']
    pd.DataFrame([{'ResponseText': 'Live response'}]).to_csv(first_paths['results'], index=False)
    assert pd.read_csv(second_paths['results']).empty
    assert banked.read_bytes() == b'banked data'
    assert first_paths['source'].read_bytes() == b'original workbook'
    assert pd.read_csv(first_paths['prompts'])['Category'].tolist() == ['Careers']


def test_run_manifest_survives_new_store_instance(tmp_path):
    store = store_at(tmp_path)
    run = create(store)
    restored = store_at(tmp_path).get('southampton', run['run_id'])
    assert restored['name'] == 'Careers rehearsal'
    assert restored['status'] == 'Ready'
    assert restored['prompt_count'] == 1
    assert restored['models'] == []
    assert len(restored['source_sha256']) == 64


def test_manifest_save_retries_transient_permission_error(tmp_path, monkeypatch):
    original_replace = Path.replace
    attempts = []

    def fail_once(source, target):
        if target.name == 'manifest.json' and not attempts:
            attempts.append(source)
            raise PermissionError('transient Windows file lock')
        return original_replace(source, target)

    monkeypatch.setattr(Path, 'replace', fail_once)
    RunStore._save_manifest(tmp_path, {'status': 'Running'})

    assert len(attempts) == 1
    assert json.loads((tmp_path / 'manifest.json').read_text(encoding='utf-8')) == {'status': 'Running'}
    assert list(tmp_path.glob('manifest-*.tmp')) == []


def test_history_is_scoped_by_organisation_and_supports_archive(tmp_path):
    store = store_at(tmp_path)
    run = create(store)
    create(store, tenant_id='another_org')
    store.update_details('southampton', run['run_id'], name='Client rehearsal', archived=True)
    assert store.list_runs('southampton') == []
    history = store.list_runs('southampton', include_archived=True)
    assert len(history) == 1
    assert history[0]['name'] == 'Client rehearsal'
    store.update_details('southampton', run['run_id'], archived=False)
    assert len(store.list_runs('southampton')) == 1


@pytest.mark.parametrize('tenant_id,run_id', [('../banked', 'run'), ('southampton', '../banked'),
                                             ('southampton', '/absolute'), ('', 'run')])
def test_path_components_cannot_escape_run_storage(tmp_path, tenant_id, run_id):
    store = store_at(tmp_path)
    with pytest.raises(ValueError):
        store.paths(tenant_id, run_id)


def test_dry_runs_are_labelled_separately_and_input_is_validated(tmp_path):
    store = store_at(tmp_path)
    run = create(store, mode='dry_run')
    assert store.get('southampton', run['run_id'])['mode'] == 'dry_run'
    with pytest.raises(ValueError, match='mode'):
        create(store, mode='unknown')
    with pytest.raises(ValueError, match='unique'):
        create(store, prompts=pd.concat([prompts(), prompts()]))
    with pytest.raises(ValueError, match='name'):
        create(store, name=' ')


def test_configured_storage_root_is_respected(tmp_path, monkeypatch):
    monkeypatch.setenv('AIRP_RUNS_DIR', str(tmp_path))
    run = create(RunStore())
    assert (tmp_path / 'southampton' / run['run_id'] / 'manifest.json').exists()
