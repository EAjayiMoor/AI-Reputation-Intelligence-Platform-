from dataclasses import replace

from src.runs.store import RunStore
from src.tenants.models import TenantConfig, TenantDataPaths


def resolve_run_tenant(tenant: TenantConfig, run_id: str | None, *, store: RunStore | None = None) -> TenantConfig:
    """Return effective data paths without editing the tenant's saved configuration."""
    if not run_id:
        return tenant
    store = store or RunStore()
    run = store.get(tenant.org_id, run_id)
    if run['archived']:
        raise ValueError('This run is archived. Restore it before selecting it.')
    paths = store.paths(tenant.org_id, run_id)
    return replace(tenant, data_paths=TenantDataPaths(
        prompts_path=str(paths['prompts']), results_path=str(paths['results'])))
