from __future__ import annotations

import plotly.express as px
import streamlit as st

from src.scoring import aggregate_scores, competitor_mentions
from src.ui import (
    apply_filters,
    apply_moorhouse_theme,
    render_page_header,
    load_core_data_with_source,
    render_data_source_selector,
    render_sidebar_filters,
)

st.set_page_config(page_title='Executive Dashboard', page_icon='📊', layout='wide')
apply_moorhouse_theme()
render_page_header(
    'Executive dashboard',
    'Headline metrics and visibility patterns',
    eyebrow='Executive view',
    icon='📊',
)
source = render_data_source_selector(key='exec_source')
st.caption(f'Results source: {source}')

try:
    _, _, scored_df = load_core_data_with_source(source=source)
except Exception as exc:
    st.error(f'Unable to load sample data: {exc}')
    st.stop()

selections = render_sidebar_filters(scored_df, key_prefix='exec')
filtered = apply_filters(scored_df, selections)

if filtered.empty:
    st.warning('No records match the selected filter set.')
    st.stop()

overall = aggregate_scores(filtered).iloc[0]

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric('Overall Visibility', f"{overall['visibility_score']:.1f}")
m2.metric('Reputation Score', f"{overall['reputation_score']:.1f}")
m3.metric('Prompt Count', int(overall['prompt_count']))
m4.metric('Southampton Mentions', int(overall['southampton_mentions']))
rank_display = '-' if overall['average_rank'] is None else f"{overall['average_rank']:.2f}"
m5.metric('Average Rank', rank_display)

market_scores = aggregate_scores(filtered, ['Market']).sort_values('visibility_score', ascending=False)
subject_scores = aggregate_scores(filtered, ['Subject']).sort_values('visibility_score', ascending=False)
competitors = competitor_mentions(filtered).head(10)

left, right = st.columns(2)
with left:
    fig_market = px.bar(
        market_scores,
        x='Market',
        y='visibility_score',
        title='Visibility by Market',
        text='visibility_score',
        labels={'visibility_score': 'Visibility Score'},
    )
    fig_market.update_layout(yaxis_range=[0, 100])
    st.plotly_chart(fig_market, use_container_width=True)

with right:
    fig_subject = px.bar(
        subject_scores,
        x='Subject',
        y='visibility_score',
        title='Visibility by Subject',
        text='visibility_score',
        labels={'visibility_score': 'Visibility Score'},
    )
    fig_subject.update_layout(yaxis_range=[0, 100])
    st.plotly_chart(fig_subject, use_container_width=True)

fig_competitors = px.bar(
    competitors,
    x='Competitor',
    y='Mentions',
    title='Top Competitors Mentioned',
    text='Mentions',
)
st.plotly_chart(fig_competitors, use_container_width=True)

st.markdown('### High-priority recommendation preview')
recommendations = []
if overall['visibility_score'] < 65:
    recommendations.append(
        {
            'Priority': 'High',
            'Category': 'Visibility',
            'Rationale': 'Overall visibility is below 65. Increase Southampton presence in high-volume prompts.',
        }
    )
if overall['citation_score'] < 60:
    recommendations.append(
        {
            'Priority': 'High',
            'Category': 'Citations',
            'Rationale': 'Citation strength is weak. Improve authoritative citation coverage in model responses.',
        }
    )

if not recommendations:
    recommendations.append(
        {
            'Priority': 'Medium',
            'Category': 'Sustain',
            'Rationale': 'Current scores are stable. Focus on subject-level gap closure in underperforming areas.',
        }
    )

st.dataframe(recommendations, use_container_width=True)
