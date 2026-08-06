from __future__ import annotations

import pandas as pd

from src.ui.data import apply_prompt_scope_filter


def test_prompt_scope_combined_returns_all_rows() -> None:
    frame = pd.DataFrame(
        [
            {'PromptID': 'P001', 'PromptSource': 'client'},
            {'PromptID': 'P002', 'PromptSource': 'generated'},
        ]
    )

    filtered = apply_prompt_scope_filter(frame, scope='Combined')

    assert len(filtered) == 2


def test_prompt_scope_client_only_returns_client_rows() -> None:
    frame = pd.DataFrame(
        [
            {'PromptID': 'P001', 'PromptSource': 'client'},
            {'PromptID': 'P002', 'PromptSource': 'generated'},
            {'PromptID': 'P003', 'PromptSource': 'client'},
        ]
    )

    filtered = apply_prompt_scope_filter(frame, scope='Client only')

    assert filtered['PromptID'].tolist() == ['P001', 'P003']


def test_prompt_scope_generated_only_returns_generated_rows() -> None:
    frame = pd.DataFrame(
        [
            {'PromptID': 'P001', 'PromptSource': 'client'},
            {'PromptID': 'P002', 'PromptSource': 'generated'},
            {'PromptID': 'P003', 'PromptSource': 'generated'},
        ]
    )

    filtered = apply_prompt_scope_filter(frame, scope='Generated only')

    assert filtered['PromptID'].tolist() == ['P002', 'P003']


def test_prompt_scope_missing_column_falls_back_to_unfiltered() -> None:
    frame = pd.DataFrame([{'PromptID': 'P001'}, {'PromptID': 'P002'}])

    filtered = apply_prompt_scope_filter(frame, scope='Generated only')

    assert len(filtered) == 2
