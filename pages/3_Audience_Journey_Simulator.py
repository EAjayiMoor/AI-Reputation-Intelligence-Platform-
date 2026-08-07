from __future__ import annotations

import streamlit as st

from src.recommendations import key_gap_text
from src.scoring import aggregate_scores, competitor_mentions
from src.ui import (
    METRIC_DEFINITIONS,
    apply_prompt_mention_mode_filter,
    apply_moorhouse_theme,
    render_page_header,
    apply_prompt_scope_filter,
    load_core_data,
    render_prompt_mention_mode_selector,
    render_prompt_scope_selector,
    render_metric_definitions,
)

st.set_page_config(page_title='Audience journey simulator', page_icon=':material/route:', layout='wide')
apply_moorhouse_theme()
render_page_header('Audience journey simulator', 'Simulate one audience pathway and narrative summary', eyebrow='Journey simulation')
scope = render_prompt_scope_selector(key='journey_scope')
mention_mode = render_prompt_mention_mode_selector(key='journey_mention_mode', default='Organic')
st.caption(
    f'Results source: OpenRouter captured outputs | Prompt bank scope: {scope} | '
    f'Prompt mention mode: {mention_mode}'
)

try:
    _, _, scored_df = load_core_data()
    scored_df = apply_prompt_scope_filter(scored_df, scope=scope)
    scored_df = apply_prompt_mention_mode_filter(scored_df, mode=mention_mode)
except Exception as exc:
    st.error(f'Unable to load captured data: {exc}')
    st.stop()

if scored_df.empty:
    st.warning('No records match this selection.')
    st.stop()

PERSONA_KEY = 'journey_live_v3_persona'
SUBJECT_KEY = 'journey_live_v3_subject'
EXPERTISE_KEY = 'journey_live_v3_expertise'
MARKET_KEY = 'journey_live_v3_market'


def clear_dependent_journey_filters(*keys: str) -> None:
    for key in keys:
        st.session_state.pop(key, None)


col1, col2, col3, col4 = st.columns(4)
with col1:
    persona = st.selectbox(
        'Persona',
        sorted(scored_df['Persona'].dropna().astype(str).unique()),
        key=PERSONA_KEY,
        on_change=clear_dependent_journey_filters,
        args=(SUBJECT_KEY, EXPERTISE_KEY, MARKET_KEY),
    )

persona_df = scored_df[scored_df['Persona'].astype(str) == persona]
with col2:
    subject = st.selectbox(
        'Subject',
        sorted(persona_df['Subject'].dropna().astype(str).unique()),
        key=SUBJECT_KEY,
        on_change=clear_dependent_journey_filters,
        args=(EXPERTISE_KEY, MARKET_KEY),
    )

subject_df = persona_df[persona_df['Subject'].astype(str) == subject]
with col3:
    expertise = st.selectbox(
        'Expertise area',
        sorted(subject_df['ExpertiseArea'].dropna().astype(str).unique()),
        key=EXPERTISE_KEY,
        on_change=clear_dependent_journey_filters,
        args=(MARKET_KEY,),
    )

pathway_df = subject_df[subject_df['ExpertiseArea'].astype(str) == expertise]
with col4:
    market = st.selectbox(
        'Market',
        sorted(pathway_df['Market'].dropna().astype(str).unique()),
        key=MARKET_KEY,
    )

journey = pathway_df[pathway_df['Market'].astype(str) == market]

if journey.empty:
    st.warning('No records match this journey combination.')
    st.stop()

available_markets = sorted(pathway_df['Market'].dropna().astype(str).unique())
prompt_sets_by_market = pathway_df.groupby('Market')['Prompt'].apply(
    lambda values: tuple(sorted(values.dropna().astype(str).unique()))
)
st.caption(
    f'Exact pathway: {persona} → {subject} → {expertise}. '
    f'Available in {len(available_markets)} market(s): {", ".join(available_markets)}.'
)
if prompt_sets_by_market.nunique() > 1:
    st.info(
        'This pathway uses market-localised wording, so the country name changes in the underlying question. '
        'The persona, subject, expertise area and question purpose remain fixed.'
    )
else:
    st.success('The underlying prompt wording is identical across every market available for this pathway.')

summary = aggregate_scores(journey).iloc[0]
comps = competitor_mentions(journey).head(3)
top_competitors = ', '.join(comps['Competitor'].tolist()) if not comps.empty else 'No clear competitor mentions'

st.subheader('Journey metrics')
m1, m2, m3 = st.columns(3)
m1.metric('Visibility score', f"{summary['visibility_score']:.1f}/100", help=METRIC_DEFINITIONS['visibility'], border=True)
m2.metric('Reputation score', f"{summary['reputation_score']:.1f}/100", help=METRIC_DEFINITIONS['reputation'], border=True)
rank_display = '-' if summary['average_rank'] is None else f"{summary['average_rank']:.2f}"
m3.metric('Average rank', rank_display, help=METRIC_DEFINITIONS['average_rank'], border=True)

render_metric_definitions()

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
    'Model',
    'Prompt',
    'SouthamptonVisible',
    'SouthamptonRank',
    'CompetitorsMentioned',
    'CitationSources',
]
journey_display = journey.copy()
journey_display['Model'] = journey_display['ModelName'].replace(
    {
        'openai/gpt-4.1-mini': 'GPT-4.1 Mini',
        'anthropic/claude-haiku-4.5': 'Claude Haiku 4.5',
        'google/gemini-3.6-flash': 'Gemini 3.6 Flash',
        'qwen/qwen3-max': 'Qwen3 Max',
        'deepseek/deepseek-chat': 'DeepSeek Chat',
    }
)
st.dataframe(journey_display[show_cols].drop_duplicates().reset_index(drop=True), hide_index=True)
