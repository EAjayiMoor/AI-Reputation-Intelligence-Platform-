from __future__ import annotations

import pandas as pd

from src.ingestion.validators import (
    PROMPT_REQUIRED_COLUMNS,
    RESULT_REQUIRED_COLUMNS,
    validate_required_columns,
)
from src.ui.data import select_available_output_columns


def test_prompt_required_columns_validation_passes_when_complete() -> None:
    frame = pd.DataFrame(columns=PROMPT_REQUIRED_COLUMNS)

    result = validate_required_columns(frame, PROMPT_REQUIRED_COLUMNS)

    assert result.valid is True
    assert result.missing_columns == []


def test_results_required_columns_validation_reports_missing_columns() -> None:
    frame = pd.DataFrame(columns=['ResultID', 'PromptID', 'Platform'])

    result = validate_required_columns(frame, RESULT_REQUIRED_COLUMNS)

    assert result.valid is False
    assert 'ResponseText' in result.missing_columns
    assert 'RunDate' in result.missing_columns


def test_select_available_output_columns_ignores_openrouter_only_fields_when_missing() -> None:
    results_df = pd.DataFrame(
        {
            'PromptID': ['P001'],
            'ResponseText': ['Sample response'],
            'CitationSources': ['page-a'],
        }
    )

    available = select_available_output_columns(
        results_df,
        ['ResponseText', 'CitationSources', 'ModelName', 'RunBatchID'],
    )

    assert available == ['ResponseText', 'CitationSources']
