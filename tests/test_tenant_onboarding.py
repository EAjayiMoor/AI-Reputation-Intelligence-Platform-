from __future__ import annotations

from pathlib import Path
import shutil

from src.tenants import load_tenant
from src.tenants import loader as tenant_loader
from src.tenants import onboarding


def test_slugify_org_id_normalises_name() -> None:
    assert onboarding.slugify_org_id(' University of Example ') == 'university_of_example'


def test_create_tenant_profile_writes_registry_entry(monkeypatch) -> None:
    temp_registry = Path('.tmp') / 'test_tenant_registry'
    if temp_registry.exists():
        shutil.rmtree(temp_registry)
    temp_registry.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(tenant_loader, 'TENANT_REGISTRY_DIR', temp_registry)
    monkeypatch.setattr(onboarding, 'TENANT_REGISTRY_DIR', temp_registry)

    created_id = onboarding.create_tenant_profile(
        display_name='Example Org',
        aliases=['Example'],
        domains=['example.org'],
    )

    assert created_id == 'example_org'
    tenant = load_tenant(created_id)
    assert tenant.display_name == 'Example Org'
    assert tenant.aliases[0] == 'Example Org'
    assert tenant.domains == ('example.org',)
    assert tenant.data_paths.prompts_path == 'data/example_org_prompts_empty.csv'
    assert tenant.data_paths.results_path == 'data/example_org_results_empty.csv'
    assert Path(tenant.data_paths.prompts_path).exists()
    assert Path(tenant.data_paths.results_path).exists()

    shutil.rmtree(temp_registry)
    Path(tenant.data_paths.prompts_path).unlink(missing_ok=True)
    Path(tenant.data_paths.results_path).unlink(missing_ok=True)


def test_update_tenant_data_paths_updates_registry(monkeypatch) -> None:
    temp_registry = Path('.tmp') / 'test_tenant_registry_update'
    if temp_registry.exists():
        shutil.rmtree(temp_registry)
    temp_registry.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(tenant_loader, 'TENANT_REGISTRY_DIR', temp_registry)
    monkeypatch.setattr(onboarding, 'TENANT_REGISTRY_DIR', temp_registry)

    tenant_id = onboarding.create_tenant_profile(display_name='Update Org')
    onboarding.update_tenant_data_paths(
        org_id=tenant_id,
        prompts_path='data/tenants/update_org/prompts.csv',
        results_path='data/tenants/update_org/results.csv',
    )

    updated = load_tenant(tenant_id)
    assert updated.data_paths.prompts_path == 'data/tenants/update_org/prompts.csv'
    assert updated.data_paths.results_path == 'data/tenants/update_org/results.csv'

    shutil.rmtree(temp_registry)
    Path(f'data/{tenant_id}_prompts_empty.csv').unlink(missing_ok=True)
    Path(f'data/{tenant_id}_results_empty.csv').unlink(missing_ok=True)
