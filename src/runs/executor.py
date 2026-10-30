"""Execution for isolated uploads; committed responses are the resume checkpoint."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import uuid

import pandas as pd

from src.execution.openrouter_runner import OpenRouterConfig, OpenRouterRunner
from src.execution.pipeline import _to_result_row
from src.execution.storage import load_openrouter_results
from src.runs.locking import RunBusyError
from src.runs.store import RunStore
from src.tenants.models import TenantConfig


def _now():
    return datetime.now(timezone.utc).isoformat()


def _completed(results):
    return set(zip(results['PromptID'].astype(str), results['ModelName'].astype(str)))


def _atomic_results(path: Path, results: pd.DataFrame):
    temporary = path.with_name(f'results-{uuid.uuid4().hex}.tmp')
    try:
        results.to_csv(temporary, index=False)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def run_summary(store: RunStore, tenant_id: str, run_id: str) -> dict:
    manifest = store.get(tenant_id, run_id)
    results = load_openrouter_results(store.paths(tenant_id, run_id)['results'])
    manifest['completed_requests'] = len(_completed(results))
    manifest['expected_requests'] = manifest['prompt_count'] * len(manifest['models'])
    manifest['active'] = store.is_busy(tenant_id, run_id)
    done = _completed(results)
    manifest['failures'] = [item for item in manifest.get('failures', [])
                            if (item['prompt_id'], item['model']) not in done]
    manifest['failed_requests'] = len(manifest['failures'])
    manifest['display_status'] = ('Interrupted' if manifest['status'] == 'Running' and not manifest['active']
                                  else manifest['status'])
    return manifest


def execute_run(
    store: RunStore, tenant: TenantConfig, run_id: str, models: list[str], *,
    api_key: str = '', base_url: str = 'https://openrouter.ai/api/v1/chat/completions',
    timeout_seconds: int = 45, app_name: str = 'AI Reputation Intelligence Platform',
    app_url: str = 'http://localhost:8501', on_progress=None, runner_factory=None,
) -> dict:
    models = list(dict.fromkeys(model.strip() for model in models if model.strip()))
    if not models:
        raise ValueError('Select one or more models before starting.')
    if timeout_seconds <= 0:
        raise ValueError('Request timeout must be greater than zero.')
    with store.execution_lock(tenant.org_id, run_id):
        manifest = store.get(tenant.org_id, run_id)
        if manifest['archived']:
            raise ValueError('An archived run cannot be executed.')
        if manifest['models'] and set(manifest['models']) != set(models):
            raise ValueError('The models are fixed for this run. Create a new run to change models.')
        models = manifest['models'] or models
        paths = store.paths(tenant.org_id, run_id)
        if hashlib.sha256(paths['prompts'].read_bytes()).hexdigest() != manifest['prompts_sha256']:
            raise ValueError('The saved prompt file has changed. Create a new run from the original upload.')
        prompts = pd.read_csv(paths['prompts'], keep_default_na=False)
        results = load_openrouter_results(paths['results'])
        pairs = [(str(row['PromptID']), model) for model in models for _, row in prompts.iterrows()]
        done = _completed(results)
        if len(done) != len(results) or not done.issubset(set(pairs)):
            raise ValueError('Saved results contain duplicate or unexpected prompt/model pairs.')
        pending = [pair for pair in pairs if pair not in done]
        dry_run = manifest['mode'] == 'dry_run'
        if pending and not dry_run and not api_key.strip():
            raise ValueError('OPENROUTER_API_KEY is not configured. Add it before running live requests.')
        if pending and manifest.get('endpoint') and manifest['endpoint'] != base_url:
            raise ValueError('The OpenRouter endpoint changed. Create a new run for a different endpoint.')

        manifest.update(models=models, endpoint=base_url, expected_requests=len(pairs),
                        completed_requests=len(done), failed_requests=0,
                        attempted_requests=manifest.get('attempted_requests', 0),
                        status='Running', interrupted=False, last_error=None)
        manifest.setdefault('started_at', _now())
        failures = {(item['prompt_id'], item['model']): item for item in manifest.get('failures', [])
                    if (item['prompt_id'], item['model']) not in done}
        prompt_lookup = prompts.set_index('PromptID').to_dict('index')
        runners = {}

        def save_state():
            manifest.update(updated_at=_now(), completed_requests=len(done),
                            failed_requests=len(failures), failures=list(failures.values()))
            store._save_manifest(paths['manifest'].parent, manifest)

        def notify():
            if on_progress is not None:
                on_progress(deepcopy(manifest))

        save_state()
        try:
            notify()
            for prompt_id, model in pending:
                manifest['attempted_requests'] += 1
                manifest['current_request'] = {'prompt_id': prompt_id, 'model': model}
                save_state()
                if model not in runners:
                    runners[model] = (runner_factory or OpenRouterRunner)(OpenRouterConfig(
                        api_key=api_key, model_name=model, base_url=base_url,
                        timeout_seconds=timeout_seconds, app_name=app_name, app_url=app_url))
                result = None
                try:
                    result = runners[model].run_prompt(prompt_id=prompt_id,
                        prompt_text=str(prompt_lookup[prompt_id]['Prompt']), run_batch_id=run_id, dry_run=dry_run)
                    valid = (result.success and isinstance(result.response_text, str)
                             and bool(result.response_text.strip()) and result.prompt_id == prompt_id
                             and result.model_name == model and result.provider == 'OpenRouter'
                             and (dry_run or not result.response_text.startswith('DRY_RUN:')))
                    error = result.error_message or 'Provider returned no usable response for this request.'
                except Exception as exc:
                    valid, error = False, str(exc)
                if valid:
                    row = _to_result_row(result, pairs.index((prompt_id, model)) + 1,
                        intent=str(prompt_lookup[prompt_id].get('Intent', '')),
                        organisation_name=tenant.display_name, organisation_aliases=tenant.aliases,
                        competitor_aliases=tenant.competitors.aliases_by_name)
                    updated = pd.concat([results, pd.DataFrame([row])], ignore_index=True)
                    _atomic_results(paths['results'], updated)
                    results = updated
                    done.add((prompt_id, model))
                    failures.pop((prompt_id, model), None)
                else:
                    failures[(prompt_id, model)] = {'prompt_id': prompt_id, 'model': model,
                        'error': error.replace(api_key, '[redacted]') if api_key else error, 'at': _now()}
                event = {'prompt_id': prompt_id, 'model': model, 'success': bool(valid), 'at': _now(),
                         'request_id': getattr(result, 'request_id', None),
                         'error': failures.get((prompt_id, model), {}).get('error')}
                with (paths['manifest'].parent / 'attempts.jsonl').open('a', encoding='utf-8') as audit:
                    audit.write(json.dumps(event) + '\n')
                manifest['current_request'] = None
                save_state()
                notify()
            manifest['status'] = 'Complete' if len(done) == len(pairs) else ('Partial' if done else 'Failed')
            manifest['finished_at'] = _now()
            manifest['current_request'] = None
            save_state()
            notify()
            return deepcopy(manifest)
        except BaseException:
            # Streamlit stops/reruns and process-level interruptions must also
            # leave committed successes intact and release the file lock.
            complete = len(done) == len(pairs)
            manifest.update(status='Complete' if complete else 'Partial' if done else 'Failed',
                            interrupted=not complete,
                            last_error=None if complete else 'Execution was interrupted before completion.')
            save_state()
            raise
