from __future__ import annotations

import json
import re
from pathlib import Path

from src.tenants.loader import TENANT_REGISTRY_DIR, list_tenants


PROMPTS_EMPTY_HEADERS = [
    'PromptID',
    'Organisation',
    'Market',
    'Persona',
    'Subject',
    'ExpertiseArea',
    'Intent',
    'Platform',
    'Prompt',
    'PromptSource',
    'PersonaTemplateID',
    'GenerationMethod',
]

RESULTS_EMPTY_HEADERS = [
    'ResultID',
    'PromptID',
    'Platform',
    'ResponseText',
    'SouthamptonVisible',
    'SouthamptonRank',
    'OrgVisible',
    'OrgRank',
    'CompetitorsMentioned',
    'CitationSources',
    'RunDate',
]


def slugify_org_id(name: str) -> str:
    base = re.sub(r'[^a-z0-9]+', '_', name.strip().lower())
    slug = base.strip('_')
    return slug or 'organisation'


def _write_empty_csv(relative_path: str, headers: list[str]) -> str:
    target = Path(relative_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        target.write_text(','.join(headers) + '\n', encoding='utf-8')
    return str(target).replace('\\', '/')


def create_tenant_profile(
    *,
    display_name: str,
    aliases: list[str] | tuple[str, ...] = (),
    domains: list[str] | tuple[str, ...] = (),
    org_id: str | None = None,
    prompts_path: str = '',
    results_path: str = '',
) -> str:
    name = display_name.strip()
    if not name:
        raise ValueError('Organisation name is required.')

    tenant_id = slugify_org_id(org_id or name)
    tenant_path = TENANT_REGISTRY_DIR / f'{tenant_id}.json'
    if tenant_path.exists() or tenant_id in list_tenants():
        raise ValueError(f"Organisation '{tenant_id}' already exists.")

    TENANT_REGISTRY_DIR.mkdir(parents=True, exist_ok=True)

    cleaned_aliases = [value.strip() for value in aliases if value and value.strip()]
    if name not in cleaned_aliases:
        cleaned_aliases.insert(0, name)
    cleaned_domains = [value.strip() for value in domains if value and value.strip()]

    resolved_prompts_path = prompts_path.strip() or _write_empty_csv(
        f'data/{tenant_id}_prompts_empty.csv',
        PROMPTS_EMPTY_HEADERS,
    )
    resolved_results_path = results_path.strip() or _write_empty_csv(
        f'data/{tenant_id}_results_empty.csv',
        RESULTS_EMPTY_HEADERS,
    )

    payload = {
        'org_id': tenant_id,
        'display_name': name,
        'aliases': cleaned_aliases,
        'domains': cleaned_domains,
        'data_paths': {
            'prompts_path': resolved_prompts_path,
            'results_path': resolved_results_path,
        },
        'model_assignment': {
            'OpenAI': 'openai/gpt-4.1-mini',
        },
    }

    tenant_path.write_text(json.dumps(payload, indent=2), encoding='utf-8')
    return tenant_id


def update_tenant_data_paths(
    *,
    org_id: str,
    prompts_path: str | None = None,
    results_path: str | None = None,
) -> None:
    tenant_id = slugify_org_id(org_id)
    tenant_path = TENANT_REGISTRY_DIR / f'{tenant_id}.json'
    if not tenant_path.exists():
        raise ValueError(f"Organisation '{tenant_id}' does not exist.")

    payload = json.loads(tenant_path.read_text(encoding='utf-8'))
    data_paths = payload.get('data_paths', {})
    if prompts_path is not None:
        data_paths['prompts_path'] = prompts_path.replace('\\', '/').strip()
    if results_path is not None:
        data_paths['results_path'] = results_path.replace('\\', '/').strip()
    payload['data_paths'] = data_paths
    tenant_path.write_text(json.dumps(payload, indent=2), encoding='utf-8')
