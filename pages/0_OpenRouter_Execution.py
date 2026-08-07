from __future__ import annotations

import pandas as pd
import streamlit as st

from src.config import load_settings
from src.execution import (
    generated_prompt_subset,
    load_openrouter_results,
    run_model_sweep,
)
from src.ui import apply_moorhouse_theme, load_core_data, render_page_header

RESULTS_PATH = 'data/openrouter_results.csv'
DEFAULT_MODEL_OPTIONS = [
    'openai/gpt-4.1-mini',
    'anthropic/claude-haiku-4.5',
    'google/gemini-3.6-flash',
    'qwen/qwen3-max',
    'deepseek/deepseek-chat',
]

st.set_page_config(page_title='OpenRouter execution', page_icon=':material/play_circle:', layout='wide')
apply_moorhouse_theme()
render_page_header(
    'OpenRouter execution',
    'Operational page for running pending generated prompts once, collecting model outputs, and replaying them safely',
    eyebrow='Execution control',
)

try:
    prompts_df, _, _ = load_core_data()
except Exception as exc:
    st.error(f'Unable to load prompt data: {exc}')
    st.stop()

if 'PromptSource' not in prompts_df.columns:
    st.error(
        "Prompt bank is missing 'PromptSource'. Add this column and tag persona prompts as 'generated'. "
        "Client prompts should be tagged as 'client'."
    )
    st.stop()

settings = load_settings()
dry_run = st.toggle('Dry run (no API call)', value=True)
selected_models = st.multiselect(
    'Models to run',
    options=DEFAULT_MODEL_OPTIONS,
    default=DEFAULT_MODEL_OPTIONS,
    help='Each selected model will receive the generated prompt bank as a separate OpenRouter run.',
)

generated_df = generated_prompt_subset(prompts_df)
existing = load_openrouter_results(RESULTS_PATH)
captured_model_count = existing['ModelName'].dropna().astype(str).nunique()

m1, m2, m3, m4 = st.columns(4)
m1.metric('Total prompts', len(prompts_df), border=True)
m2.metric('Generated prompts', len(generated_df), border=True)
m3.metric('Models', captured_model_count, border=True)
m4.metric('Captured outputs', len(existing), border=True)

st.info(
    'This page is for operational capture only. It runs generated persona prompts through OpenRouter, stores the responses, and supports replay for audit QA. '
    'It is not the executive summary page.'
)

execute = st.button('Run selected models across the generated prompt bank', type='primary', disabled=(len(selected_models) == 0))

if execute:
    api_key = settings.openrouter_api_key if not dry_run else (settings.openrouter_api_key or 'dry_run_key')
    if not api_key:
        st.error('OPENROUTER_API_KEY is not set. Configure it or run in dry-run mode.')
        st.stop()

    updated, summary = run_model_sweep(
        prompt_df=prompts_df,
        existing_results_df=existing,
        results_path=RESULTS_PATH,
        model_names=selected_models,
        dry_run=dry_run,
        api_key=api_key,
        app_name=settings.openrouter_app_name,
        app_url=settings.openrouter_app_url,
    )

    st.success(
        f"Sweep complete. Executed {summary['executed_prompts']} generated prompt runs across {len(selected_models)} models; "
        f"success={summary['success_count']}, failed={summary['failure_count']}."
    )
    st.caption(f"Saved results to {RESULTS_PATH}")
    st.dataframe(updated.tail(20), hide_index=True)

st.subheader('Captured output table')
st.caption('Explore saved model responses. These controls only filter captured data and do not make API calls.')

if existing.empty:
    st.info('No captured OpenRouter responses are available yet.')
else:
    output_table = existing.merge(
        prompts_df[
            ['PromptID', 'Prompt', 'Market', 'Persona', 'Subject', 'Intent', 'ExpertiseArea']
        ],
        on='PromptID',
        how='left',
    )

    available_models = sorted(output_table['ModelName'].dropna().astype(str).unique())
    with st.container(horizontal=True, vertical_alignment='bottom'):
        output_models = st.multiselect(
            'Filter by model',
            options=available_models,
            default=available_models,
            key='captured_output_models',
        )
        visibility_filter = st.segmented_control(
            'Southampton visibility',
            options=['All', 'Visible', 'Not visible'],
            default='All',
            key='captured_output_visibility',
        )
        output_search = st.text_input(
            'Search prompts and responses',
            placeholder='Enter a prompt ID, phrase, persona or response text',
            key='captured_output_search',
        )

    filtered_outputs = output_table[
        output_table['ModelName'].astype(str).isin(output_models)
    ].copy()

    if visibility_filter == 'Visible':
        filtered_outputs = filtered_outputs[
            pd.to_numeric(filtered_outputs['SouthamptonVisible'], errors='coerce').fillna(0).eq(1)
        ]
    elif visibility_filter == 'Not visible':
        filtered_outputs = filtered_outputs[
            pd.to_numeric(filtered_outputs['SouthamptonVisible'], errors='coerce').fillna(0).eq(0)
        ]

    search_term = output_search.strip()
    if search_term:
        searchable_columns = [
            'PromptID',
            'Prompt',
            'ResponseText',
            'ModelName',
            'Market',
            'Persona',
            'Subject',
            'Intent',
        ]
        search_mask = pd.Series(False, index=filtered_outputs.index)
        for column in searchable_columns:
            search_mask |= filtered_outputs[column].fillna('').astype(str).str.contains(
                search_term,
                case=False,
                regex=False,
            )
        filtered_outputs = filtered_outputs[search_mask]

    display_columns = [
        'PromptID',
        'ModelName',
        'Prompt',
        'ResponseText',
        'SouthamptonVisible',
        'CitationSources',
        'Market',
        'Persona',
        'Subject',
        'Intent',
        'RunDate',
    ]
    display_outputs = filtered_outputs[display_columns].reset_index(drop=True)

    st.caption(f'{len(display_outputs):,} captured outputs match the current filters.')
    selection = st.dataframe(
        display_outputs,
        hide_index=True,
        height=600,
        key='captured_output_table',
        on_select='rerun',
        selection_mode='single-row',
        column_config={
            'PromptID': st.column_config.TextColumn('Prompt ID', pinned=True, width='small'),
            'ModelName': st.column_config.TextColumn('Model', pinned=True, width='medium'),
            'Prompt': st.column_config.TextColumn('Prompt', width='large'),
            'ResponseText': st.column_config.TextColumn('Model response', width='large'),
            'SouthamptonVisible': st.column_config.CheckboxColumn('Southampton visible'),
            'CitationSources': st.column_config.TextColumn('Citations', width='large'),
        },
    )

    selected_rows = selection.selection.rows
    if selected_rows:
        selected_output = display_outputs.iloc[selected_rows[0]]
        with st.container(border=True):
            st.markdown(
                f"**{selected_output['PromptID']} · {selected_output['ModelName']}**"
            )
            st.caption(str(selected_output['Prompt']))
            st.markdown(str(selected_output['ResponseText']))
            if str(selected_output['CitationSources']).strip() not in {'', 'nan'}:
                st.markdown(f"**Citations:** {selected_output['CitationSources']}")

    st.download_button(
        'Download filtered outputs as CSV',
        data=display_outputs.to_csv(index=False).encode('utf-8'),
        file_name='filtered_openrouter_outputs.csv',
        mime='text/csv',
        icon=':material/download:',
    )
