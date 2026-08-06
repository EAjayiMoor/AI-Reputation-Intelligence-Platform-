from __future__ import annotations

import pandas as pd
import streamlit as st

from src.config import load_settings
from src.execution import (
    OpenRouterConfig,
    OpenRouterRunner,
    generated_prompt_subset,
    load_openrouter_results,
    pending_prompt_rows,
    run_model_sweep,
)
from src.ui import apply_moorhouse_theme, load_core_data, render_page_header

RESULTS_PATH = 'data/openrouter_results.csv'
DEFAULT_MODEL_OPTIONS = [
    'openai/gpt-4.1-mini',
    'anthropic/claude-3.5-haiku',
    'google/gemini-flash',
    'qwen/qwen-3',
    'deepseek/deepseek-chat',
]

st.set_page_config(page_title='OpenRouter Execution', page_icon='🚀', layout='wide')
apply_moorhouse_theme()
render_page_header(
    'OpenRouter execution',
    'Operational page for running pending generated prompts once, collecting model outputs, and replaying them safely',
    eyebrow='Execution control',
    icon='🚀',
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
dry_run = st.checkbox('Dry run (no API call)', value=True)
selected_models = st.multiselect(
    'Models to run',
    options=DEFAULT_MODEL_OPTIONS,
    default=DEFAULT_MODEL_OPTIONS,
    help='Each selected model will receive the generated prompt bank as a separate OpenRouter run.',
)

generated_df = generated_prompt_subset(prompts_df)
existing = load_openrouter_results(RESULTS_PATH)

pending_counts = {}
for model_name in selected_models:
    pending_counts[model_name] = len(pending_prompt_rows(prompts_df, existing, model_name=model_name))

pending_total = sum(pending_counts.values())

m1, m2, m3, m4 = st.columns(4)
m1.metric('Total prompts', len(prompts_df))
m2.metric('Generated prompts', len(generated_df))
m3.metric('Selected models', len(selected_models))
m4.metric('Pending generated prompts', pending_total)

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
    st.dataframe(updated.tail(20), use_container_width=True, hide_index=True)

if selected_models:
    with st.expander('Pending counts by model', expanded=False):
        pending_summary = pd.DataFrame(
            {
                'Model': list(pending_counts.keys()),
                'Pending prompts': list(pending_counts.values()),
            }
        )
        st.dataframe(pending_summary, use_container_width=True, hide_index=True)
else:
    st.success('Select at least one model to run the sweep.')
