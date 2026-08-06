from __future__ import annotations

import streamlit as st

from src.recommendations import generate_recommendations
from src.ui import (
    apply_filters,
    apply_moorhouse_theme,
    render_page_header,
    apply_prompt_scope_filter,
    load_core_data_with_source,
    render_data_source_selector,
    render_prompt_scope_selector,
    render_sidebar_filters,
)

st.set_page_config(page_title='Recommendations', page_icon='💡', layout='wide')
apply_moorhouse_theme()
render_page_header('Recommendations', 'Prioritised recommendation output with export', eyebrow='Action planning')
source = render_data_source_selector(key='reco_source')
scope = render_prompt_scope_selector(key='reco_scope')
st.caption(f'Results source: {source} | Prompt bank scope: {scope}')

try:
    _, _, scored_df = load_core_data_with_source(source=source)
    scored_df = apply_prompt_scope_filter(scored_df, scope=scope)
except Exception as exc:
    st.error(f'Unable to load sample data: {exc}')
    st.stop()

if scored_df.empty:
    st.warning('No records match this selection.')
    st.stop()

filters = render_sidebar_filters(scored_df, key_prefix='reco')
filtered = apply_filters(scored_df, filters)

if filtered.empty:
    st.warning('No records match the selected filter set.')
    st.stop()

recommendations = generate_recommendations(filtered)

st.dataframe(recommendations, use_container_width=True, hide_index=True)

st.download_button(
    label='Export recommendations (CSV)',
    data=recommendations.to_csv(index=False).encode('utf-8'),
    file_name='recommendations.csv',
    mime='text/csv',
)
