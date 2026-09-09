from __future__ import annotations

import json
import os
from pathlib import Path

from src.tenants.models import (
    TenantCompetitorSet,
    TenantConfig,
    TenantDataPaths,
    TenantModelAssignment,
)


TENANT_REGISTRY_DIR = Path(__file__).resolve().parent / 'registry'
DEFAULT_TENANT_ID = 'southampton'
DEFAULT_TENANT_ENV_VAR = 'AIRP_DEFAULT_TENANT'


def default_tenant_id() -> str:
    configured = (os.getenv(DEFAULT_TENANT_ENV_VAR) or '').strip().lower()
    return configured or DEFAULT_TENANT_ID


def list_tenants() -> list[str]:
    if not TENANT_REGISTRY_DIR.exists():
        return []
    return sorted(path.stem for path in TENANT_REGISTRY_DIR.glob('*.json'))


def load_tenant(org_id: str | None = None) -> TenantConfig:
    target_id = (org_id or default_tenant_id()).strip().lower()
    tenant_path = TENANT_REGISTRY_DIR / f'{target_id}.json'
    if not tenant_path.exists():
        available = ', '.join(list_tenants()) or 'none'
        raise ValueError(f"Unknown tenant '{target_id}'. Available tenants: {available}")

    payload = json.loads(tenant_path.read_text(encoding='utf-8'))
    return TenantConfig(
        org_id=str(payload.get('org_id', target_id)).strip().lower(),
        display_name=str(payload['display_name']).strip(),
        aliases=tuple(str(value).strip() for value in payload.get('aliases', []) if str(value).strip()),
        domains=tuple(str(value).strip() for value in payload.get('domains', []) if str(value).strip()),
        data_paths=TenantDataPaths(
            prompts_path=str(payload['data_paths']['prompts_path']).strip(),
            results_path=str(payload['data_paths']['results_path']).strip(),
        ),
        model_assignment=TenantModelAssignment(
            labels_to_models={
                str(label).strip(): str(model).strip()
                for label, model in payload.get('model_assignment', {}).items()
                if str(label).strip() and str(model).strip()
            }
        ),
        competitors=TenantCompetitorSet(
            aliases_by_name={
                str(name).strip(): tuple(
                    str(alias).strip()
                    for alias in ([aliases] if isinstance(aliases, str) else aliases)
                    if str(alias).strip()
                )
                for name, aliases in payload.get('competitors', {}).items()
                if str(name).strip()
            }
        ),
    )
