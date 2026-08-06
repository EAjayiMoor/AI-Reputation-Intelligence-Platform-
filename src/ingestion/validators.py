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
    'SouthamptonVisible',
    'SouthamptonRank',
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
