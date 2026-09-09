from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


PROMPT_REQUIRED_COLUMNS = [
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

RESULT_REQUIRED_COLUMNS = [
    'ResultID',
    'PromptID',
    'Platform',
    'ResponseText',
    'OrgVisible',
    'OrgRank',
    'CompetitorsMentioned',
    'CitationSources',
    'RunDate',
]


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    missing_columns: list[str]


def validate_required_columns(df: pd.DataFrame, required_columns: list[str]) -> ValidationResult:
    missing = [column for column in required_columns if column not in df.columns]
    return ValidationResult(valid=not missing, missing_columns=missing)


def validate_result_columns(df: pd.DataFrame) -> ValidationResult:
    """Accept the canonical organisation fields or the legacy Southampton pair."""
    base_columns = [
        column for column in RESULT_REQUIRED_COLUMNS if column not in {'OrgVisible', 'OrgRank'}
    ]
    missing = [column for column in base_columns if column not in df.columns]
    has_canonical = {'OrgVisible', 'OrgRank'}.issubset(df.columns)
    has_legacy = {'SouthamptonVisible', 'SouthamptonRank'}.issubset(df.columns)
    if not has_canonical and not has_legacy:
        missing.extend(['OrgVisible', 'OrgRank'])
    return ValidationResult(valid=not missing, missing_columns=missing)
