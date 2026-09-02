from __future__ import annotations

import pandas as pd
import streamlit as st

from src.recommendations import key_gap_text
from src.scoring import aggregate_scores, competitor_mentions
from src.ui import (
    METRIC_DEFINITIONS,
    apply_prompt_mention_mode_filter,
    apply_moorhouse_theme,
    render_page_header,
    render_empty_state_guidance,
    require_active_tenant,
    tenant_data_source_label,
    apply_prompt_scope_filter,
    load_core_data,
    render_prompt_mention_mode_selector,
    render_prompt_scope_selector,
)


def _metric_defs_for_org(organisation_name: str) -> dict[str, str]:
    if organisation_name == 'University of Southampton':
        return dict(METRIC_DEFINITIONS)
    return {
        key: value.replace('University of Southampton', organisation_name).replace('Southampton', organisation_name)
        for key, value in METRIC_DEFINITIONS.items()
    }


def _render_metric_definitions_for_org(metric_defs: dict[str, str]) -> None:
    with st.expander('How these metrics are calculated', icon=':material/info:'):
        st.markdown(f"**Overall visibility score**  \n{metric_defs['visibility']}")
        st.markdown(f"**Reputation score**  \n{metric_defs['reputation']}")
        st.markdown(f"**Average rank**  \n{metric_defs['average_rank']}")
        st.markdown(f"**Prompts in view**  \n{metric_defs['prompts_in_view']}")
        st.markdown(f"**Organisation mentions**  \n{metric_defs['mentions']}")

st.set_page_config(page_title='Audience journey simulator', page_icon=':material/route:', layout='wide')
apply_moorhouse_theme()
tenant = require_active_tenant()
data_source = tenant_data_source_label(tenant)
render_page_header('Audience journey simulator', 'Simulate one audience pathway and narrative summary', eyebrow='Journey simulation')
scope = render_prompt_scope_selector(key='journey_scope')
mention_mode = render_prompt_mention_mode_selector(
    key='journey_mention_mode',
    default='Organic',
    organisation_name=tenant.display_name,
)
st.caption(
    f'Active organization: {tenant.display_name} | Data source: {data_source} | Results source: OpenRouter captured outputs | Prompt bank scope: {scope} | '
    f'Prompt mention mode: {mention_mode}'
)

try:
    _, _, scored_df = load_core_data(org_id=tenant.org_id)
    scored_df = apply_prompt_scope_filter(scored_df, scope=scope)
    scored_df = apply_prompt_mention_mode_filter(scored_df, mode=mention_mode)
except Exception as exc:
    st.error(f'Unable to load captured data: {exc}')
    st.stop()

if scored_df.empty:
    render_empty_state_guidance(tenant, area='Audience Journey Simulator')
    st.stop()

PERSONA_KEY = 'journey_live_v3_persona'
SUBJECT_KEY = 'journey_live_v3_subject'
EXPERTISE_KEY = 'journey_live_v3_expertise'
MARKET_KEY = 'journey_live_v3_market'


def clear_dependent_journey_filters(*keys: str) -> None:
    for key in keys:
        st.session_state.pop(key, None)


def _sorted_non_empty(series: pd.Series) -> list[str]:
    values = series.dropna().astype(str).str.strip()
    values = values[values != '']
    return sorted(values.unique())


col1, col2, col3, col4 = st.columns(4)
persona_options = _sorted_non_empty(scored_df['Persona'])
if not persona_options:
    st.error('No persona values are available for the current filters.')
    st.stop()

with col1:
    persona = st.selectbox(
        'Persona',
        persona_options,
        key=PERSONA_KEY,
        on_change=clear_dependent_journey_filters,
        args=(SUBJECT_KEY, EXPERTISE_KEY, MARKET_KEY),
    )

persona_df = scored_df[scored_df['Persona'].astype(str) == persona]
subject_options = _sorted_non_empty(persona_df['Subject'])
if not subject_options:
    st.error('No subject values are available for the selected persona.')
    st.stop()

with col2:
    subject = st.selectbox(
        'Subject',
        subject_options,
        key=SUBJECT_KEY,
        on_change=clear_dependent_journey_filters,
        args=(EXPERTISE_KEY, MARKET_KEY),
    )

subject_df = persona_df[persona_df['Subject'].astype(str) == subject]
expertise_options = _sorted_non_empty(subject_df['ExpertiseArea'])
if not expertise_options:
    st.error('No expertise areas are available for the selected persona and subject.')
    st.stop()

with col3:
    expertise = st.selectbox(
        'Expertise area',
        expertise_options,
        key=EXPERTISE_KEY,
        on_change=clear_dependent_journey_filters,
        args=(MARKET_KEY,),
    )

pathway_df = subject_df[subject_df['ExpertiseArea'].astype(str) == expertise]
market_options = _sorted_non_empty(pathway_df['Market'])
if not market_options:
    st.error('No markets are available for the selected journey path.')
    st.stop()

with col4:
    market = st.selectbox(
        'Market',
        market_options,
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
metric_defs = _metric_defs_for_org(tenant.display_name)

st.subheader('Journey metrics')
m1, m2, m3 = st.columns(3)
m1.metric('Visibility score', f"{summary['visibility_score']:.1f}/100", help=metric_defs['visibility'], border=True)
m2.metric('Reputation score', f"{summary['reputation_score']:.1f}/100", help=metric_defs['reputation'], border=True)
rank_display = '-' if summary['average_rank'] is None else f"{summary['average_rank']:.2f}"
m3.metric('Average rank', rank_display, help=metric_defs['average_rank'], border=True)

_render_metric_definitions_for_org(metric_defs)

st.subheader('Narrative summary')
key_gap = key_gap_text(journey)
st.write(
    (
        f"For a {persona.lower()} audience in {market} focused on {subject} ({expertise}), "
        f"{tenant.display_name} has a visibility score of {summary['visibility_score']:.1f}. "
        f"Top competitors in this journey are {top_competitors}. "
        f"Key gap: {key_gap}"
    )
)

st.subheader('Relevant prompts and results')
visible_column = 'OrgVisible' if 'OrgVisible' in journey.columns else 'SouthamptonVisible'
rank_column = 'OrgRank' if 'OrgRank' in journey.columns else 'SouthamptonRank'
show_cols = [
    'PromptID',
    'Model',
    'Prompt',
    visible_column,
    rank_column,
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
