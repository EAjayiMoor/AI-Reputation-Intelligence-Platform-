from __future__ import annotations

from src.tenants import list_tenants, load_tenant


def test_loader_lists_seeded_tenants() -> None:
    tenants = list_tenants()
    assert 'southampton' in tenants
    assert 'moorhouse' in tenants
    assert 'demo_university' in tenants


def test_loader_returns_southampton_defaults() -> None:
    tenant = load_tenant('southampton')

    assert tenant.org_id == 'southampton'
    assert tenant.display_name == 'University of Southampton'
    assert tenant.data_paths.prompts_path == 'data/UoS_Prompt_Library_normalised.csv'
    assert tenant.data_paths.results_path == 'data/uos_openrouter_results.csv'
    assert tenant.model_assignment.labels_to_models['OpenAI'] == 'openai/gpt-4.1-mini'
