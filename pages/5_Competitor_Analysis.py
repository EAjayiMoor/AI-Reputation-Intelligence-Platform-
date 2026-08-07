from __future__ import annotations

import streamlit as st

from src.scoring import competitor_mentions, institution_mention_index, institution_mentions_by_model
from src.ui import (
    apply_filters,
    apply_moorhouse_theme,
    render_page_header,
    apply_prompt_scope_filter,
    load_core_data,
    render_prompt_scope_selector,
    render_sidebar_filters,
)

st.set_page_config(page_title='Competitor analysis', page_icon=':material/groups:', layout='wide')
apply_moorhouse_theme()
render_page_header('Competitor analysis', 'Understand competitor mention patterns', eyebrow='Competitor diagnostics')
scope = render_prompt_scope_selector(key='competitor_scope')
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

filters = render_sidebar_filters(scored_df, key_prefix='competitor_live_v2')
filtered = apply_filters(scored_df, filters)

if filtered.empty:
    st.warning('No records match the selected filter set.')
    st.stop()

st.markdown(
    """
    <div class='mh-callout'>
        <strong>How to read this page</strong>
        <p>Competitor counts use institution-neutral discovery prompts only. Any prompt that explicitly names Southampton or another university is excluded before counting. The tables therefore answer: when someone asks for suitable or leading universities without supplying a name, which institutions appear?</p>
    </div>
    """,
    unsafe_allow_html=True,
)

eligible_response_count = int(filtered['CompetitorPromptEligible'].fillna(False).astype(bool).sum())
st.caption(f'{eligible_response_count:,} institution-neutral responses are included in this competitor analysis.')
if eligible_response_count == 0:
    st.info(
        'No institution-neutral prompts match this view. Switch the prompt mention mode to Organic or All.'
    )
    st.stop()

st.subheader('Organic mentions by model')
comparison = institution_mention_index(filtered, competitor_limit=20)
by_model = institution_mentions_by_model(filtered, competitor_limit=20)
model_table = by_model.pivot_table(
    index='Institution',
    columns='ModelName',
    values='Mentions',
    aggfunc='sum',
    fill_value=0,
).rename(
    columns={
        'openai/gpt-4.1-mini': 'GPT-4.1 Mini',
        'anthropic/claude-haiku-4.5': 'Claude Haiku 4.5',
        'google/gemini-3.6-flash': 'Gemini 3.6 Flash',
        'qwen/qwen3-max': 'Qwen3 Max',
        'deepseek/deepseek-chat': 'DeepSeek Chat',
    }
)
model_table = model_table.reindex(comparison['Institution'].tolist())
model_table['Total'] = model_table.sum(axis=1)
model_table['Organic mention rate'] = model_table['Total'].div(eligible_response_count).mul(100).round(1)
model_table = model_table.reset_index()
st.caption('Raw response-level counts from institution-neutral prompts; named comparison prompts are excluded.')
st.dataframe(
    model_table,
    hide_index=True,
    column_config={
        'Institution': st.column_config.TextColumn('Institution', pinned=True, width='large'),
        'Organic mention rate': st.column_config.NumberColumn('Organic mention rate', format='%.1f%%'),
    },
)

st.subheader('Competitors by subject')
by_subject = competitor_mentions(filtered, group_column='Subject')
st.dataframe(by_subject.head(50), hide_index=True)

st.subheader('Competitors by market')
by_market = competitor_mentions(filtered, group_column='Market')
st.dataframe(by_market.head(50), hide_index=True)
