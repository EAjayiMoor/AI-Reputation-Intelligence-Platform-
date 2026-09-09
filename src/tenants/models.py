from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TenantDataPaths:
    prompts_path: str
    results_path: str


@dataclass(frozen=True)
class TenantModelAssignment:
    labels_to_models: dict[str, str]


@dataclass(frozen=True)
class TenantCompetitorSet:
    aliases_by_name: dict[str, tuple[str, ...]]


@dataclass(frozen=True)
class TenantConfig:
    org_id: str
    display_name: str
    aliases: tuple[str, ...]
    domains: tuple[str, ...]
    data_paths: TenantDataPaths
    model_assignment: TenantModelAssignment
    competitors: TenantCompetitorSet
