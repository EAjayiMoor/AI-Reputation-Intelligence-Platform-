from __future__ import annotations

import streamlit as st

from src.recommendations import key_gap_text
from src.scoring import aggregate_scores, competitor_mentions
from src.ui import (
    apply_moorhouse_theme,
    render_page_header,
    apply_prompt_scope_filter,
    load_core_data_with_source,
    render_data_source_selector,
    render_prompt_scope_selector,
)

st.set_page_config(page_title='Audience Journey Simulator', page_icon='🧩', layout='wide')
apply_moorhouse_theme()
render_page_header('Audience journey simulator', 'Simulate one audience pathway and narrative summary', eyebrow='Journey simulation')
source = render_data_source_selector(key='journey_source')
scope = render_prompt_scope_selector(key='journey_scope')
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

col1, col2, col3, col4 = st.columns(4)
with col1:
    market = st.selectbox('Market', sorted(scored_df['Market'].dropna().astype(str).unique()))
with col2:
    subject = st.selectbox('Subject', sorted(scored_df['Subject'].dropna().astype(str).unique()))
with col3:
    persona = st.selectbox('Persona', sorted(scored_df['Persona'].dropna().astype(str).unique()))
with col4:
    expertise = st.selectbox('Expertise Area', sorted(scored_df['ExpertiseArea'].dropna().astype(str).unique()))

journey = scored_df[
    (scored_df['Market'].astype(str) == market)
    & (scored_df['Subject'].astype(str) == subject)
    & (scored_df['Persona'].astype(str) == persona)
    & (scored_df['ExpertiseArea'].astype(str) == expertise)
]

if journey.empty:
    st.warning('No records match this journey combination.')
    st.stop()

summary = aggregate_scores(journey).iloc[0]
comps = competitor_mentions(journey).head(3)
top_competitors = ', '.join(comps['Competitor'].tolist()) if not comps.empty else 'No clear competitor mentions'

st.subheader('Journey metrics')
m1, m2, m3 = st.columns(3)
m1.metric('Visibility Score', f"{summary['visibility_score']:.1f}")
m2.metric('Reputation Score', f"{summary['reputation_score']:.1f}")
rank_display = '-' if summary['average_rank'] is None else f"{summary['average_rank']:.2f}"
m3.metric('Average Rank', rank_display)

st.subheader('Narrative summary')
key_gap = key_gap_text(journey)
st.write(
    (
        f"For a {persona.lower()} audience in {market} focused on {subject} ({expertise}), "
        f"Southampton has a visibility score of {summary['visibility_score']:.1f}. "
        f"Top competitors in this journey are {top_competitors}. "
        f"Key gap: {key_gap}"
    )
)

st.subheader('Relevant prompts and results')
show_cols = [
    'PromptID',
    'Platform',
    'Prompt',
    'SouthamptonVisible',
    'SouthamptonRank',
    'CompetitorsMentioned',
    'CitationSources',
]
st.dataframe(journey[show_cols].drop_duplicates().reset_index(drop=True), use_container_width=True, hide_index=True)
