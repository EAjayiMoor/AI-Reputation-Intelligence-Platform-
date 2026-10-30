from pathlib import Path

import pandas as pd
import pytest

from src.runs.store import RunStore
from src.tenants import load_tenant

from src.runs.selection import resolve_run_tenant


def test_selected_run_changes_both_paths_without_changing_registry(tmp_path):
    store = RunStore(tmp_path)
    tenant = load_tenant('southampton')
    banked = {p: Path(p).read_bytes() for p in [tenant.data_paths.prompts_path, tenant.data_paths.results_path,
              'src/tenants/registry/southampton.json']}
    run = store.create(tenant_id='southampton', name='New upload',
                       prompts=pd.DataFrame([{'PromptID': 'P1', 'Prompt': 'Q'}]),
                       source_name='client.csv', source_bytes=b'input')
    selected = resolve_run_tenant(tenant, run['run_id'], store=store)
    paths = store.paths('southampton', run['run_id'])
    assert Path(selected.data_paths.prompts_path) == paths['prompts']
    assert Path(selected.data_paths.results_path) == paths['results']
    assert resolve_run_tenant(tenant, None, store=store) == tenant
    assert load_tenant('southampton') == tenant
    assert all(Path(p).read_bytes() == content for p, content in banked.items())
    with pytest.raises(FileNotFoundError):
        resolve_run_tenant(load_tenant('moorhouse'), run['run_id'], store=store)
    store.update_details('southampton', run['run_id'], archived=True)
    with pytest.raises(ValueError, match='archived'):
        resolve_run_tenant(tenant, run['run_id'], store=store)
