from __future__ import annotations

from pathlib import Path
import re

import pandas as pd
import streamlit as st

from src.execution import load_openrouter_results
from src.ingestion.validators import (
    PROMPT_REQUIRED_COLUMNS,
    RESULT_REQUIRED_COLUMNS,
    validate_required_columns,
)
from src.scoring import score_results

DEFAULT_PROMPTS_PATH = Path('data/Southampton_GEO_6Personas_120Prompts.csv')
DEFAULT_RESULTS_PATH = Path('data/sample_results.csv')
DEFAULT_OPENROUTER_RESULTS_PATH = Path('data/openrouter_results.csv')

FILTER_COLUMNS = ['Market', 'Subject', 'Persona', 'ExpertiseArea', 'Intent', 'Platform']
OUTPUT_COLUMNS = [
    'ResponseText',
    'CitationSources',
    'ModelName',
    'RunBatchID',
]


def select_available_output_columns(results_df: pd.DataFrame, required_output_columns: list[str] | tuple[str, ...] = OUTPUT_COLUMNS) -> list[str]:
    available = [column for column in required_output_columns if column in results_df.columns]
    return available


def normalise_prompt_bank_frame(frame: pd.DataFrame) -> pd.DataFrame:
    working = frame.copy()

    if 'PromptID' not in working.columns and 'prompt_id' in working.columns:
        working['PromptID'] = working['prompt_id']
    if 'PromptID' not in working.columns and 'PromptID' in working.columns:
        working['PromptID'] = working['PromptID']

    if 'Organisation' not in working.columns:
        working['Organisation'] = 'University of Southampton'

    if 'Market' not in working.columns:
        source_market = working['country'] if 'country' in working.columns else working['Market']
        working['Market'] = source_market.fillna('Unknown')

    if 'Persona' not in working.columns:
        if 'persona_name' in working.columns:
            working['Persona'] = working['persona_name']
        elif 'persona_type' in working.columns:
            working['Persona'] = working['persona_type']
        else:
            working['Persona'] = 'Persona'

    if 'Subject' not in working.columns:
        working['Subject'] = working['subject'] if 'subject' in working.columns else ''

    if 'ExpertiseArea' not in working.columns:
        working['ExpertiseArea'] = (
            working['expected_analysis_dimension'] if 'expected_analysis_dimension' in working.columns else ''
        )

    if 'Intent' not in working.columns:
        working['Intent'] = (
            working['prompt_type'] if 'prompt_type' in working.columns else working['prompt_category']
        )

    if 'Platform' not in working.columns:
        working['Platform'] = 'OpenRouter'

    if 'Prompt' not in working.columns:
        working['Prompt'] = working['prompt_text'] if 'prompt_text' in working.columns else ''

    if 'PromptSource' not in working.columns:
        working['PromptSource'] = 'generated'

    if 'PersonaTemplateID' not in working.columns:
        working['PersonaTemplateID'] = working['persona_id'] if 'persona_id' in working.columns else ''

    if 'GenerationMethod' not in working.columns:
        working['GenerationMethod'] = 'persona_bank'

    for column in ['PromptID', 'Organisation', 'Market', 'Persona', 'Subject', 'ExpertiseArea', 'Intent', 'Platform', 'Prompt', 'PromptSource', 'PersonaTemplateID', 'GenerationMethod']:
        if column not in working.columns:
            working[column] = ''

    return working.reset_index(drop=True)


@st.cache_data(show_spinner=False)
def load_core_data(
    prompts_path: str | Path = DEFAULT_PROMPTS_PATH,
    results_path: str | Path = DEFAULT_RESULTS_PATH,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    prompts_df = normalise_prompt_bank_frame(pd.read_csv(prompts_path))
    results_df = pd.read_csv(results_path)

    prompt_validation = validate_required_columns(prompts_df, PROMPT_REQUIRED_COLUMNS)
    result_validation = validate_required_columns(results_df, RESULT_REQUIRED_COLUMNS)

    if not prompt_validation.valid:
        missing = ', '.join(prompt_validation.missing_columns)
        raise ValueError(f'Prompt data is missing required columns: {missing}')

    if not result_validation.valid:
        missing = ', '.join(result_validation.missing_columns)
        raise ValueError(f'Results data is missing required columns: {missing}')

    merged = results_df.merge(
        prompts_df,
        on=['PromptID', 'Platform'],
        how='left',
        suffixes=('_result', ''),
    )
    scored = score_results(merged)
    return prompts_df, results_df, scored


@st.cache_data(show_spinner=False)
def load_core_data_with_source(
    source: str,
    prompts_path: str | Path = DEFAULT_PROMPTS_PATH,
    sample_results_path: str | Path = DEFAULT_RESULTS_PATH,
    openrouter_results_path: str | Path = DEFAULT_OPENROUTER_RESULTS_PATH,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    prompts_df = normalise_prompt_bank_frame(pd.read_csv(prompts_path))
    prompt_validation = validate_required_columns(prompts_df, PROMPT_REQUIRED_COLUMNS)
    if not prompt_validation.valid:
        missing = ', '.join(prompt_validation.missing_columns)
        raise ValueError(f'Prompt data is missing required columns: {missing}')

    if source == 'OpenRouter Captured Results':
        results_df = load_openrouter_results(openrouter_results_path)
        result_validation = validate_required_columns(results_df, RESULT_REQUIRED_COLUMNS)
        if not result_validation.valid:
            missing = ', '.join(result_validation.missing_columns)
            raise ValueError(f'OpenRouter results are missing required columns: {missing}')
        merged = results_df.merge(prompts_df, on=['PromptID'], how='left', suffixes=('_result', ''))
    else:
        results_df = pd.read_csv(sample_results_path)
        result_validation = validate_required_columns(results_df, RESULT_REQUIRED_COLUMNS)
        if not result_validation.valid:
            missing = ', '.join(result_validation.missing_columns)
            raise ValueError(f'Results data is missing required columns: {missing}')
        merged = results_df.merge(
            prompts_df,
            on=['PromptID', 'Platform'],
            how='left',
            suffixes=('_result', ''),
        )

    scored = score_results(merged)
    return prompts_df, results_df, scored


def render_data_source_selector(key: str = 'data_source') -> str:
    return st.sidebar.selectbox(
        'Results Source',
        options=['Sample Results', 'OpenRouter Captured Results'],
        index=0,
        key=key,
    )


def render_sidebar_filters(df: pd.DataFrame, key_prefix: str = 'global') -> dict[str, str]:
    st.sidebar.header('Filters')
    selections: dict[str, str] = {}

    for column in FILTER_COLUMNS:
        values = sorted(value for value in df[column].dropna().astype(str).unique())
        options = ['All', *values]
        selections[column] = st.sidebar.selectbox(
            label=column,
            options=options,
            index=0,
            key=f'{key_prefix}_{column}',
        )

    return selections


def apply_filters(df: pd.DataFrame, selections: dict[str, str]) -> pd.DataFrame:
    filtered = df.copy()
    for column, value in selections.items():
        if value != 'All':
            filtered = filtered[filtered[column].astype(str) == value]
    return filtered.reset_index(drop=True)


def render_prompt_scope_selector(key: str = 'prompt_scope') -> str:
    return st.sidebar.selectbox(
        'Prompt Bank Scope',
        options=['Combined', 'Client only', 'Generated only'],
        index=0,
        key=key,
    )


def apply_prompt_scope_filter(df: pd.DataFrame, scope: str) -> pd.DataFrame:
    if 'PromptSource' not in df.columns:
        return df.reset_index(drop=True)

    working = df.copy()
    source = working['PromptSource'].astype(str).str.lower()

    if scope == 'Client only':
        working = working[source == 'client']
    elif scope == 'Generated only':
        working = working[source == 'generated']

    return working.reset_index(drop=True)
