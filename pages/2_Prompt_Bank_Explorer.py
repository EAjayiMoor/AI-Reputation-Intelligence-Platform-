from __future__ import annotations

import streamlit as st

from src.ui import (
    apply_filters,
    apply_moorhouse_theme,
    render_page_header,
    load_core_data,
    render_sidebar_filters,
)
from src.ui.data import select_available_output_columns

st.set_page_config(page_title='Prompt bank explorer', page_icon=':material/explore:', layout='wide')
apply_moorhouse_theme()
render_page_header(
    'Prompt bank explorer',
    'Inspect prompt coverage and export filtered views',
    eyebrow='Prompt intelligence',
)
st.caption('Results source: OpenRouter captured outputs')

try:
    prompts_df, results_df, _ = load_core_data()
except Exception as exc:
    st.error(f'Unable to load captured data: {exc}')
    st.stop()

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
    'PromptMentionType',
]

prompt_bank_view = (
    prompts_df[prompt_columns]
    .drop_duplicates(subset=['PromptID'])
    .sort_values(['Market', 'Subject', 'Persona', 'PromptID'])
    .reset_index(drop=True)
)

output_view = (
    results_df[['PromptID', *output_columns]].copy()
    if output_columns
    else results_df[['PromptID']].copy()
)

combined_view = prompt_bank_view.merge(output_view, on='PromptID', how='left')
captured_view = combined_view[
    combined_view['ResponseText'].fillna('').astype(str).str.strip().ne('')
].reset_index(drop=True)

selections = render_sidebar_filters(combined_view, key_prefix='prompts_live_v2')
filtered_combined = apply_filters(combined_view, selections)
filtered_captured = apply_filters(captured_view, selections)

view_mode = st.segmented_control(
    'Explorer view',
    options=['Prompt bank only', 'Prompt + captured output', 'Captured output only'],
    default='Prompt + captured output',
)

if view_mode == 'Prompt bank only':
    prompt_table = filtered_combined[prompt_columns].drop_duplicates(subset=['PromptID']).reset_index(drop=True)
elif view_mode == 'Captured output only':
    prompt_table = filtered_captured.copy()
else:
    prompt_table = filtered_combined.loc[:, [*prompt_columns, *output_columns]].reset_index(drop=True)

if view_mode != 'Captured output only':
    prompt_table = prompt_table.sort_values(['Market', 'Subject', 'Persona', 'PromptID'], na_position='last').reset_index(drop=True)

st.metric('Filtered prompt count', len(prompt_table), border=True)
st.caption('Prompt bank view with one row per captured prompt/model response. Model outputs are not collapsed.')
st.dataframe(prompt_table, hide_index=True)

st.download_button(
    label='Download filtered prompts (CSV)',
    data=prompt_table.to_csv(index=False).encode('utf-8'),
    file_name='filtered_prompts.csv',
    mime='text/csv',
)

st.markdown('### Coverage summary')
coverage = (
    prompt_table.groupby(['Market', 'Subject', 'Persona'], as_index=False)['PromptID']
    .nunique()
    .rename(columns={'PromptID': 'PromptCount'})
)
st.dataframe(coverage, hide_index=True)

if len(prompt_table) == len(prompts_df):
    st.caption('Showing all prompt bank prompts and any available captured outputs.')
else:
    st.caption('Showing prompts filtered by sidebar selections and any matching captured outputs.')
