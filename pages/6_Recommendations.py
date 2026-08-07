from __future__ import annotations

import streamlit as st

from src.recommendations import generate_recommendations
from src.ui import (
    apply_filters,
    apply_moorhouse_theme,
    render_page_header,
    apply_prompt_scope_filter,
    load_core_data,
    render_prompt_scope_selector,
    render_sidebar_filters,
)

st.set_page_config(page_title='Recommendations', page_icon=':material/lightbulb:', layout='wide')
apply_moorhouse_theme()
render_page_header('Recommendations', 'Prioritised recommendation output with export', eyebrow='Action planning')
scope = render_prompt_scope_selector(key='reco_scope')
st.caption(f'Results source: OpenRouter captured outputs | Prompt bank scope: {scope}')

try:
    _, _, scored_df = load_core_data()
    scored_df = apply_prompt_scope_filter(scored_df, scope=scope)
except Exception as exc:
    st.error(f'Unable to load captured data: {exc}')
    st.stop()

if scored_df.empty:
    st.warning('No records match this selection.')
    st.stop()

filters = render_sidebar_filters(scored_df, key_prefix='reco_live_v2')
filtered = apply_filters(scored_df, filters)

if filtered.empty:
    st.warning('No records match the selected filter set.')
    st.stop()

recommendations = generate_recommendations(filtered)

high_count = int(recommendations['Priority'].eq('High').sum())
medium_count = int(recommendations['Priority'].eq('Medium').sum())
with st.container(horizontal=True):
    st.metric('Prioritised actions', len(recommendations), border=True)
    st.metric('High priority', high_count, border=True)
    st.metric('Medium priority', medium_count, border=True)

priority_filter = st.segmented_control(
    'Priority',
    options=['All', 'High', 'Medium'],
    default='All',
    key='recommendation_priority',
)
visible_recommendations = (
    recommendations
    if priority_filter == 'All'
    else recommendations[recommendations['Priority'] == priority_filter].reset_index(drop=True)
)

st.subheader('Action plan')
st.caption('Recommendations are generated from the captured responses under the current sidebar filters.')

for _, recommendation in visible_recommendations.iterrows():
    label = f"{recommendation['Priority']} · {recommendation['Action']}"
    with st.expander(label, icon=':material/task_alt:'):
        st.caption(f"{recommendation['Category']} · {recommendation['Scope']} · {recommendation['Timing']}")
        st.markdown(f"**Evidence**  \n{recommendation['Evidence']}")
        st.markdown(f"**Objective**  \n{recommendation['Objective']}")
        st.markdown('**Actions**')
        st.markdown(recommendation['Action plan'])
        st.markdown(f"**Owner**  \n{recommendation['Owner']}")
        st.markdown(f"**Success measure**  \n{recommendation['Success measure']}")

st.subheader('Portfolio view')
st.dataframe(
    visible_recommendations,
    hide_index=True,
    column_order=['Priority', 'Action', 'Scope', 'Evidence', 'Owner', 'Timing', 'Success measure'],
    column_config={
        'Priority': st.column_config.TextColumn('Priority', pinned=True, width='small'),
        'Action': st.column_config.TextColumn('Action', pinned=True, width='large'),
        'Scope': st.column_config.TextColumn('Scope', width='medium'),
        'Evidence': st.column_config.TextColumn('Evidence', width='large'),
        'Owner': st.column_config.TextColumn('Owner', width='medium'),
        'Timing': st.column_config.TextColumn('Timing', width='small'),
        'Success measure': st.column_config.TextColumn('Success measure', width='large'),
    },
)

st.download_button(
    label='Export recommendations (CSV)',
    data=visible_recommendations.to_csv(index=False).encode('utf-8'),
    file_name='recommendations.csv',
    mime='text/csv',
)
