from __future__ import annotations

from src.execution.uos_library import UOS_MODEL_MAP
from src.ingestion.contracts import DEFAULT_ORGANISATION
from src.tenants import load_tenant
from src.ui.data import DEFAULT_PROMPTS_PATH, DEFAULT_RESULTS_PATH


def test_southampton_compat_defaults_match_tenant_registry() -> None:
    tenant = load_tenant('southampton')

    assert DEFAULT_ORGANISATION == tenant.display_name
    assert str(DEFAULT_PROMPTS_PATH).replace('\\', '/') == tenant.data_paths.prompts_path
    assert str(DEFAULT_RESULTS_PATH).replace('\\', '/') == tenant.data_paths.results_path


def test_uos_model_map_matches_tenant_registry() -> None:
    tenant = load_tenant('southampton')

    assert UOS_MODEL_MAP == tenant.model_assignment.labels_to_models

