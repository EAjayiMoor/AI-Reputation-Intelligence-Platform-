from __future__ import annotations

import plotly.express as px
import streamlit as st

from src.scoring import aggregate_scores
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

st.set_page_config(page_title='Visibility Analysis', page_icon='🗺️', layout='wide')
apply_moorhouse_theme()
render_page_header('Visibility analysis', 'Heatmap and rank analysis by segment', eyebrow='Visibility diagnostics')
source = render_data_source_selector(key='visibility_source')
scope = render_prompt_scope_selector(key='visibility_scope_filter')
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

filters = render_sidebar_filters(scored_df, key_prefix='visibility')
filtered = apply_filters(scored_df, filters)

if filtered.empty:
    st.warning('No records match the selected filter set.')
    st.stop()

st.markdown(
    """
    <div class='mh-callout'>
        <strong>How to read this page</strong>
        <p>The heatmap shows the average visibility score for each market/subject slice. A row is scored as 100 when Southampton is visible and 0 when it is absent. Rank contribution is then weighted by placement (1 = 100, 2 = 90, 3 = 80, 4–5 = 70, 6–10 = 50, otherwise 40), and citation presence adds another 100-or-0 signal. The blended reputation score is 0.5 × visibility + 0.3 × rank + 0.2 × citation.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.subheader('Visibility heatmap (Market × Subject)')
heatmap_source = aggregate_scores(filtered, ['Market', 'Subject'])
heatmap_pivot = heatmap_source.pivot(index='Market', columns='Subject', values='visibility_score').fillna(0)
fig_heatmap = px.imshow(
    heatmap_pivot,
    text_auto='.1f',
    aspect='auto',
    labels={'color': 'Visibility %'},
)
fig_heatmap.update_layout(height=500)
st.plotly_chart(fig_heatmap, use_container_width=True)

st.subheader('Average rank by Subject and Platform')
visible_only = filtered[filtered['visible_bool']]
rank_table = (
    visible_only.groupby(['Subject', 'Platform'], as_index=False)['rank_float']
    .mean()
    .rename(columns={'rank_float': 'AverageRank'})
)
if rank_table.empty:
    st.info('No visible prompts with rank data for this selection.')
else:
    rank_table['AverageRank'] = rank_table['AverageRank'].round(2)
    st.dataframe(rank_table.sort_values(['Subject', 'Platform']), use_container_width=True, hide_index=True)
