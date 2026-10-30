from dataclasses import replace
import json
from pathlib import Path
import subprocess
import sys

import pandas as pd
import pytest

from src.execution.openrouter_runner import OpenRouterConfig, OpenRouterRunner
from src.runs.store import RunStore
from src.runs.upload import INPUT_COLUMNS, prepare_prompts
from src.tenants import load_tenant

try:
    from src.runs import executor
except ImportError:
    executor = None


def engine():
    assert executor is not None, 'Isolated run executor has not been implemented'
    return executor


def setup_run(tmp_path, mode='dry_run'):
    store = RunStore(tmp_path)
    frame = pd.DataFrame([['UK', 'Student', subject, 'Careers', f'Compare {subject} careers.']
                          for subject in ['Medicine', 'Engineering']], columns=INPUT_COLUMNS)
    prompts = prepare_prompts(frame, organisation_name='University of Southampton').prompts
    run = store.create(tenant_id='southampton', name='Rehearsal', prompts=prompts,
                       source_name='input.csv', source_bytes=b'original', mode=mode)
    return store, run, load_tenant('southampton')


def test_all_client_prompts_execute_and_resume_does_not_repeat_successes(tmp_path):
    service = engine()
    store, run, tenant = setup_run(tmp_path)
    progress = []
    def saved_before_progress(state):
        saved = pd.read_csv(store.paths(tenant.org_id, run['run_id'])['results'])
        assert len(saved) == state['completed_requests']
        progress.append(state['completed_requests'])
    outcome = service.execute_run(store, tenant, run['run_id'], ['test/a', 'test/b'], on_progress=saved_before_progress)
    assert outcome['status'] == 'Complete'
    assert outcome['completed_requests'] == outcome['expected_requests'] == 4
    assert progress[-1] == 4
    results = pd.read_csv(store.paths(tenant.org_id, run['run_id'])['results'])
    assert results['ResultID'].is_unique
    assert set(results['RunBatchID']) == {run['run_id']}
    assert results['ResponseText'].str.startswith('DRY_RUN:').all()
    before = store.paths(tenant.org_id, run['run_id'])['results'].read_bytes()
    again = service.execute_run(store, tenant, run['run_id'], ['test/b', 'test/a'])
    assert again['completed_requests'] == 4
    assert again['attempted_requests'] == 4
    assert store.paths(tenant.org_id, run['run_id'])['results'].read_bytes() == before
    with pytest.raises(ValueError, match='models'):
        service.execute_run(store, tenant, run['run_id'], ['test/c'])


def test_failure_persists_then_only_failed_pair_is_retried(tmp_path):
    service = engine()
    store, run, tenant = setup_run(tmp_path)
    calls = []
    class FailFirst:
        def __init__(self, config):
            self.runner = OpenRouterRunner(config)
        def run_prompt(self, **kwargs):
            calls.append(kwargs['prompt_id'])
            result = self.runner.run_prompt(**kwargs)
            if kwargs['prompt_id'].endswith('00001'):
                return replace(result, success=False, error_message='Temporary provider failure', response_text='')
            return result
    partial = service.execute_run(store, tenant, run['run_id'], ['test/a'], runner_factory=FailFirst)
    assert partial['status'] == 'Partial'
    assert partial['completed_requests'] == partial['failed_requests'] == 1
    assert partial['failures'][0]['prompt_id'] == 'UPLOAD-00001'
    assert len(calls) == 2
    completed = service.execute_run(store, tenant, run['run_id'], ['test/a'])
    assert completed['status'] == 'Complete'
    assert completed['attempted_requests'] == 3
    assert completed['failures'] == []
    assert completed['failed_requests'] == 0
    assert len(pd.read_csv(store.paths(tenant.org_id, run['run_id'])['results'])) == 2
    attempts = [json.loads(line) for line in (store.paths(tenant.org_id, run['run_id'])['results'].parent / 'attempts.jsonl').read_text().splitlines()]
    assert [item['success'] for item in attempts] == [False, True, True]


def test_process_lock_prevents_another_writer_and_releases(tmp_path):
    service = engine()
    store, run, tenant = setup_run(tmp_path)
    code = '''
import sys
from src.runs.store import RunStore
from src.runs.locking import RunBusyError
try:
    with RunStore(sys.argv[1]).execution_lock('southampton', sys.argv[2]):
        print('acquired')
except RunBusyError:
    print('busy')
'''
    args = [sys.executable, '-c', code, str(tmp_path), run['run_id']]
    with store.execution_lock(tenant.org_id, run['run_id']):
        assert subprocess.run(args, capture_output=True, text=True, check=True).stdout.strip() == 'busy'
        with pytest.raises(service.RunBusyError):
            service.execute_run(store, tenant, run['run_id'], ['test/a'])
        with pytest.raises(service.RunBusyError):
            store.update_details(tenant.org_id, run['run_id'], archived=True)
    assert subprocess.run(args, capture_output=True, text=True, check=True).stdout.strip() == 'acquired'


def test_os_releases_lock_after_worker_termination(tmp_path):
    engine()
    store, run, tenant = setup_run(tmp_path)
    code = '''
import sys
from src.runs.store import RunStore
with RunStore(sys.argv[1]).execution_lock('southampton', sys.argv[2]):
    print('locked', flush=True)
    sys.stdin.read()
'''
    child = subprocess.Popen([sys.executable, '-c', code, str(tmp_path), run['run_id']],
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        assert child.stdout.readline().strip() == 'locked'
        assert store.is_busy(tenant.org_id, run['run_id'])
    finally:
        child.terminate()
        child.communicate(timeout=10)
    assert not store.is_busy(tenant.org_id, run['run_id'])


def test_live_key_validation_and_modified_prompt_fingerprint(tmp_path):
    service = engine()
    store, run, tenant = setup_run(tmp_path, mode='live')
    with pytest.raises(ValueError, match='OPENROUTER_API_KEY'):
        service.execute_run(store, tenant, run['run_id'], ['test/a'])
    assert store.get(tenant.org_id, run['run_id'])['status'] == 'Ready'
    assert store.get(tenant.org_id, run['run_id'])['models'] == []
    store.paths(tenant.org_id, run['run_id'])['prompts'].write_text('tampered', encoding='utf-8')
    with pytest.raises(ValueError, match='changed'):
        service.execute_run(store, tenant, run['run_id'], ['test/a'], api_key='not-a-real-key')


def test_interruption_preserves_saved_results_and_can_resume(tmp_path):
    service = engine()
    store, run, tenant = setup_run(tmp_path)
    def interrupt(state):
        if state['completed_requests'] == 1:
            raise KeyboardInterrupt()
    with pytest.raises(KeyboardInterrupt):
        service.execute_run(store, tenant, run['run_id'], ['test/a'], on_progress=interrupt)
    interrupted = store.get(tenant.org_id, run['run_id'])
    assert interrupted['interrupted'] is True
    assert interrupted['status'] == 'Partial'
    result = service.execute_run(store, tenant, run['run_id'], ['test/a'])
    assert result['status'] == 'Complete'
    assert result['attempted_requests'] == 2


def test_interruption_after_last_saved_response_keeps_run_complete(tmp_path):
    service = engine()
    store, run, tenant = setup_run(tmp_path)
    def interrupt(state):
        if state['completed_requests'] == state['expected_requests']:
            raise KeyboardInterrupt()
    with pytest.raises(KeyboardInterrupt):
        service.execute_run(store, tenant, run['run_id'], ['test/a'], on_progress=interrupt)
    assert store.get(tenant.org_id, run['run_id'])['status'] == 'Complete'


def test_abandoned_running_manifest_uses_committed_results_on_resume(tmp_path):
    service = engine()
    store, run, tenant = setup_run(tmp_path)
    service.execute_run(store, tenant, run['run_id'], ['test/a'])
    paths = store.paths(tenant.org_id, run['run_id'])
    manifest = json.loads(paths['manifest'].read_text())
    manifest.update(status='Running', completed_requests=0)
    paths['manifest'].write_text(json.dumps(manifest))
    state = service.run_summary(store, tenant.org_id, run['run_id'])
    assert state['display_status'] == 'Interrupted'
    assert state['completed_requests'] == 2
    recovered = service.execute_run(store, tenant, run['run_id'], ['test/a'])
    assert recovered['status'] == 'Complete'
    assert recovered['attempted_requests'] == 2


def test_archived_runs_and_empty_model_selection_cannot_execute(tmp_path):
    service = engine()
    store, run, tenant = setup_run(tmp_path)
    with pytest.raises(ValueError, match='models'):
        service.execute_run(store, tenant, run['run_id'], [])
    store.update_details(tenant.org_id, run['run_id'], archived=True)
    with pytest.raises(ValueError, match='archived'):
        service.execute_run(store, tenant, run['run_id'], ['test/a'])


def test_live_http_requests_preserve_prompts_models_usage_and_cost(tmp_path, monkeypatch):
    from io import BytesIO
    from src.execution import openrouter_runner
    service = engine()
    store, run, tenant = setup_run(tmp_path, mode='live')
    requests = []
    def respond(req, **kwargs):
        payload = json.loads(req.data)
        requests.append(payload)
        assert req.get_method() == 'POST'
        assert req.get_header('Authorization') == 'Bearer fake-test-key'
        return BytesIO(json.dumps({'id': 'mock-response', 'choices': [{'message': {
            'content': 'University of Southampton offers careers support.'}}],
            'usage': {'prompt_tokens': 12, 'completion_tokens': 10, 'total_tokens': 22, 'cost': 0.01}}).encode())
    monkeypatch.setattr(openrouter_runner.request, 'urlopen', respond)
    state = service.execute_run(store, tenant, run['run_id'], ['test/a', 'test/b'], api_key='fake-test-key')
    assert state['status'] == 'Complete'
    assert len(requests) == 4
    assert {request['model'] for request in requests} == {'test/a', 'test/b'}
    assert all(request['messages'][1]['content'].startswith('Compare ') for request in requests)
    results = pd.read_csv(store.paths(tenant.org_id, run['run_id'])['results'])
    assert results['OrgVisible'].tolist() == [1, 1, 1, 1]
    assert results['TotalTokens'].sum() == 88
    assert results['APICost'].sum() == pytest.approx(0.04)


def test_all_failed_requests_record_failure_without_leaking_api_key(tmp_path):
    service = engine()
    store, run, tenant = setup_run(tmp_path, mode='live')
    class FailingRunner:
        def __init__(self, config):
            pass
        def run_prompt(self, **kwargs):
            raise RuntimeError('Provider rejected fake-private-key')
    state = service.execute_run(store, tenant, run['run_id'], ['test/a'],
                                 api_key='fake-private-key', runner_factory=FailingRunner)
    assert state['status'] == 'Failed'
    assert state['completed_requests'] == 0
    assert state['failed_requests'] == 2
    assert 'fake-private-key' not in store.paths(tenant.org_id, run['run_id'])['manifest'].read_text()


@pytest.mark.parametrize('payload', [
    {}, {'choices': []}, {'error': {'message': 'Unavailable'}},
    {'choices': [{'message': {'content': ''}}]},
    {'choices': [{'message': {'content': None}}]},
    {'choices': [{'message': {'content': '   '}}]},
    {'choices': [{'message': {'content': ['not text']}}]},
])
def test_runner_rejects_unusable_provider_responses(monkeypatch, payload):
    from io import BytesIO
    from src.execution import openrouter_runner
    monkeypatch.setattr(openrouter_runner.request, 'urlopen', lambda *a, **k: BytesIO(json.dumps(payload).encode()))
    result = OpenRouterRunner(OpenRouterConfig(api_key='test', model_name='test/a')).run_prompt('P1', 'Q')
    assert result.success is False
    assert result.error_message
