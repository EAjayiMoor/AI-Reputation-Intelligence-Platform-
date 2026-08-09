from __future__ import annotations

from pathlib import Path
import re

import pandas as pd
import streamlit as st

from src.analysis import prompt_names_institution
from src.execution import load_openrouter_results
from src.ingestion.validators import (
    PROMPT_REQUIRED_COLUMNS,
    RESULT_REQUIRED_COLUMNS,
    validate_required_columns,
)
from src.scoring import score_results

DEFAULT_PROMPTS_PATH = Path('data/UoS_Prompt_Library_normalised.csv')
DEFAULT_RESULTS_PATH = Path('data/uos_openrouter_results.csv')

FILTER_COLUMNS = [
    'PromptMentionType',
    'Market',
    'Subject',
    'Persona',
    'ExpertiseArea',
    'Intent',
    'ModelName',
    'Platform',
]
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
        if 'market' in working.columns:
            working['Market'] = working['market']
        elif 'country' in working.columns:
            working['Market'] = working['country']
        else:
            working['Market'] = 'Unknown'

    if 'Persona' not in working.columns:
        if 'persona' in working.columns:
            working['Persona'] = working['persona']
        elif 'persona_name' in working.columns:
            working['Persona'] = working['persona_name']
        elif 'persona_type' in working.columns:
            working['Persona'] = working['persona_type']
        else:
            working['Persona'] = 'Persona'

    if 'Subject' not in working.columns:
        working['Subject'] = working['subject'] if 'subject' in working.columns else ''

    if 'ExpertiseArea' not in working.columns:
        working['ExpertiseArea'] = (
            working['geo_objective']
            if 'geo_objective' in working.columns
            else working['expected_analysis_dimension']
            if 'expected_analysis_dimension' in working.columns
            else ''
        )

    if 'Intent' not in working.columns:
        if 'intent' in working.columns:
            working['Intent'] = working['intent']
        elif 'prompt_type' in working.columns:
            working['Intent'] = working['prompt_type']
        elif 'prompt_category' in working.columns:
            working['Intent'] = working['prompt_category']
        else:
            working['Intent'] = ''

    if 'Platform' not in working.columns:
        working['Platform'] = 'OpenRouter'

    if 'Prompt' not in working.columns:
        working['Prompt'] = working['prompt_text'] if 'prompt_text' in working.columns else ''

    working['PromptMentionType'] = (
        working['Prompt']
        .fillna('')
        .astype(str)
        .str.contains(r'\bsouthampton\b', case=False, regex=True)
        .map({True: 'Prompted/direct', False: 'Organic'})
    )
    working['CompetitorPromptEligible'] = ~working.apply(
        lambda row: prompt_names_institution(row.get('Prompt', ''), row.get('Intent', '')),
        axis=1,
    )

    if 'PromptSource' not in working.columns:
        working['PromptSource'] = 'generated'

    if 'PersonaTemplateID' not in working.columns:
        working['PersonaTemplateID'] = working['persona_id'] if 'persona_id' in working.columns else ''

    if 'GenerationMethod' not in working.columns:
        working['GenerationMethod'] = 'persona_bank'

    for column in ['PromptID', 'Organisation', 'Market', 'Persona', 'Subject', 'ExpertiseArea', 'Intent', 'Platform', 'Prompt', 'PromptMentionType', 'CompetitorPromptEligible', 'PromptSource', 'PersonaTemplateID', 'GenerationMethod']:
        if column not in working.columns:
            working[column] = ''

    return working.reset_index(drop=True)


@st.cache_data(show_spinner=False, ttl=5)
def load_core_data(
    prompts_path: str | Path = DEFAULT_PROMPTS_PATH,
    results_path: str | Path = DEFAULT_RESULTS_PATH,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    prompts_df = normalise_prompt_bank_frame(pd.read_csv(prompts_path))
    results_df = load_openrouter_results(results_path)

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


def render_sidebar_filters(df: pd.DataFrame, key_prefix: str = 'global') -> dict[str, str]:
    st.sidebar.header('Filters')
    selections: dict[str, str] = {}
    filter_keys = [f'{key_prefix}_{column}' for column in FILTER_COLUMNS if column in df.columns]

    def clear_filters() -> None:
        for filter_key in filter_keys:
            st.session_state.pop(filter_key, None)

    st.sidebar.button(
        'Clear filters',
        key=f'{key_prefix}_clear_filters',
        icon=':material/filter_alt_off:',
        on_click=clear_filters,
    )

    for column in FILTER_COLUMNS:
        if column not in df.columns:
            continue
        if column == 'PromptMentionType':
            selections[column] = render_prompt_mention_mode_selector(
                key=f'{key_prefix}_{column}',
                default='Organic',
            )
            continue
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


def render_prompt_mention_mode_selector(
    key: str = 'prompt_mention_mode',
    default: str = 'Organic',
) -> str:
    mode = st.sidebar.segmented_control(
        'Prompt mention mode',
        options=['Organic', 'Prompted/direct', 'All'],
        default=default,
        key=key,
        help=(
            'Organic prompts do not name Southampton. Prompted/direct prompts explicitly include '
            'Southampton in the prompt text.'
        ),
    )
    st.sidebar.caption(
        'Organic = Southampton is not named in the prompt. Prompted/direct = Southampton is explicitly named.'
    )
    return mode or default


def apply_prompt_mention_mode_filter(df: pd.DataFrame, mode: str) -> pd.DataFrame:
    if mode == 'All' or 'PromptMentionType' not in df.columns:
        return df.reset_index(drop=True)
    return df[df['PromptMentionType'].astype(str) == mode].reset_index(drop=True)
