from __future__ import annotations

import streamlit as st

from src.ui import (
    apply_filters,
    apply_moorhouse_theme,
    render_page_header,
    load_core_data_with_source,
    render_data_source_selector,
    render_sidebar_filters,
)
from src.ui.data import select_available_output_columns

st.set_page_config(page_title='Prompt Bank Explorer', page_icon='🧭', layout='wide')
apply_moorhouse_theme()
render_page_header(
    'Prompt bank explorer',
    'Inspect prompt coverage and export filtered views',
    eyebrow='Prompt intelligence',
    icon='🧭',
)
source = render_data_source_selector(key='prompts_source')
st.caption(f'Results source: {source}')

try:
    prompts_df, results_df, _ = load_core_data_with_source(source=source)
except Exception as exc:
    st.error(f'Unable to load sample data: {exc}')
    st.stop()

selections = render_sidebar_filters(prompts_df, key_prefix='prompts')
filtered_prompts = apply_filters(prompts_df, selections)

output_columns = select_available_output_columns(results_df)

prompt_columns = [
    'PromptID',
    'Market',
    'Persona',
    'Subject',
    'ExpertiseArea',
    'Intent',
    'Platform',
    'Prompt',
]

output_view = results_df[['PromptID', *output_columns]].copy() if output_columns else results_df[['PromptID']].copy()
if not output_view.empty:
    output_view = output_view.drop_duplicates(subset=['PromptID'])

prompt_bank_view = (
    filtered_prompts[prompt_columns]
    .drop_duplicates(subset=['PromptID'])
    .sort_values(['Market', 'Subject', 'Persona', 'PromptID'])
    .reset_index(drop=True)
)

view_mode = st.radio(
    'Explorer view',
    options=['Prompt bank only', 'Prompt + captured output', 'Captured output only'],
    index=1,
    horizontal=True,
)

if view_mode == 'Prompt bank only':
    prompt_table = prompt_bank_view.copy()
elif view_mode == 'Captured output only':
    prompt_table = output_view.copy()
else:
    prompt_table = (
        prompt_bank_view.merge(output_view, on='PromptID', how='left')
        .loc[:, [*prompt_columns, *output_columns]]
        .reset_index(drop=True)
    )

if view_mode != 'Captured output only':
    prompt_table = prompt_table.sort_values(['Market', 'Subject', 'Persona', 'PromptID'], na_position='last').reset_index(drop=True)

st.metric('Filtered Prompt Count', len(prompt_table))
st.caption('Prompt bank view with any captured OpenRouter response fields joined by PromptID.')
st.dataframe(prompt_table, use_container_width=True, hide_index=True)

st.download_button(
    label='Download filtered prompts (CSV)',
    data=prompt_table.to_csv(index=False).encode('utf-8'),
    file_name='filtered_prompts.csv',
    mime='text/csv',
)

st.markdown('### Coverage summary')
coverage = (
    prompt_table.groupby(['Market', 'Subject', 'Persona'], as_index=False)['PromptID']
    .count()
    .rename(columns={'PromptID': 'PromptCount'})
)
st.dataframe(coverage, use_container_width=True, hide_index=True)

if len(prompt_table) == len(prompts_df):
    st.caption('Showing all prompt bank prompts and any available captured outputs.')
else:
    st.caption('Showing prompts filtered by sidebar selections and any matching captured outputs.')
