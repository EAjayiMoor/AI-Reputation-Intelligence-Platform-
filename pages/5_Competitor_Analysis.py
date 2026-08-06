from __future__ import annotations

import streamlit as st

from src.scoring import competitor_mentions
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

st.set_page_config(page_title='Competitor Analysis', page_icon='🥊', layout='wide')
apply_moorhouse_theme()
render_page_header('Competitor analysis', 'Understand competitor mention patterns', eyebrow='Competitor diagnostics')
source = render_data_source_selector(key='competitor_source')
scope = render_prompt_scope_selector(key='competitor_scope')
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

filters = render_sidebar_filters(scored_df, key_prefix='competitor')
filtered = apply_filters(scored_df, filters)

if filtered.empty:
    st.warning('No records match the selected filter set.')
    st.stop()

st.markdown(
    """
    <div class='mh-callout'>
        <strong>How to read this page</strong>
        <p>Each comma-separated competitor name in the source data is treated as one mention. The tables count those mentions across the filtered prompts and then aggregate them overall, by subject, or by market. A competitor with more mentions is simply appearing more often in the selected prompt set.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.subheader('Most frequently mentioned competitors')
overall = competitor_mentions(filtered)
st.dataframe(overall.head(20), use_container_width=True, hide_index=True)

st.subheader('Competitors by subject')
by_subject = competitor_mentions(filtered, group_column='Subject')
st.dataframe(by_subject.head(50), use_container_width=True, hide_index=True)

st.subheader('Competitors by market')
by_market = competitor_mentions(filtered, group_column='Market')
st.dataframe(by_market.head(50), use_container_width=True, hide_index=True)
