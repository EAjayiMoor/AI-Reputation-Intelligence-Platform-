from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from src.analysis import competitive_breakdown, competitive_cooccurrence
from src.scoring import competitor_mentions, institution_mention_index, institution_mentions_by_model
from src.ui import (
    MOORHOUSE_PURPLE_SCALE,
    apply_filters,
    apply_moorhouse_theme,
    render_page_header,
    render_empty_state_guidance,
    require_active_tenant,
    tenant_data_source_label,
    apply_prompt_scope_filter,
    load_core_data,
    render_prompt_scope_selector,
    render_sidebar_filters,
)


MODEL_LABELS = {
    'openai/gpt-4.1-mini': 'GPT-4.1 Mini',
    'anthropic/claude-haiku-4.5': 'Claude Haiku 4.5',
    'google/gemini-3.6-flash': 'Gemini 3.6 Flash',
    'qwen/qwen3-max': 'Qwen3 Max',
    'deepseek/deepseek-chat': 'DeepSeek Chat',
    'perplexity/sonar': 'Perplexity Sonar',
}


def _competitive_rows(frame: pd.DataFrame, tenant) -> pd.DataFrame:
    return competitive_breakdown(
        frame,
        organisation_name=tenant.display_name,
        organisation_aliases=tenant.aliases,
        competitor_aliases=tenant.competitors.aliases_by_name or None,
    )


def _target_row(summary: pd.DataFrame, tenant) -> pd.Series | None:
    matches = summary[summary['Entity'].astype(str).str.casefold() == tenant.display_name.casefold()]
    return matches.iloc[0] if not matches.empty else None

st.set_page_config(page_title='Competitor analysis', page_icon=':material/groups:', layout='wide')
apply_moorhouse_theme()
tenant = require_active_tenant()
data_source = tenant_data_source_label(tenant)
render_page_header('Competitor analysis', 'Understand competitor mention patterns', eyebrow='Competitor diagnostics')
scope = render_prompt_scope_selector(key='competitor_scope')
st.caption(
    f'Active organization: {tenant.display_name} | Data source: {data_source} | Results source: OpenRouter captured outputs | Prompt bank scope: {scope}'
)

try:
    _, _, scored_df = load_core_data(org_id=tenant.org_id)
    scored_df = apply_prompt_scope_filter(scored_df, scope=scope)
except Exception as exc:
    st.error(f'Unable to load captured data: {exc}')
    st.stop()

if scored_df.empty:
    render_empty_state_guidance(tenant, area='Competitor Analysis')
    st.stop()

filters = render_sidebar_filters(scored_df, key_prefix='competitor_live_v2')
filtered = apply_filters(scored_df, filters)

if filtered.empty:
    render_empty_state_guidance(tenant, area='Competitor Analysis')
    st.stop()

st.markdown(
    f"""
    <div class='mh-callout'>
        <strong>How to read this page</strong>
        <p>Competitor counts use neutral discovery prompts only. Any prompt that explicitly names {tenant.display_name} or another organisation is excluded before counting. The tables therefore answer: when someone asks for suitable or leading organisations without supplying a name, which organisations appear?</p>
    </div>
    """,
    unsafe_allow_html=True,
)

eligible_response_count = int(filtered['CompetitorPromptEligible'].fillna(False).astype(bool).sum())
st.caption(f'{eligible_response_count:,} organisation-neutral responses are included in this competitor analysis.')
if eligible_response_count == 0:
    st.info(
        'No organisation-neutral prompts match this view. Switch the prompt mention mode to Organic or All.'
    )
    st.stop()

competitive_summary = _competitive_rows(filtered, tenant)
target_summary = _target_row(competitive_summary, tenant)
competitor_summary = competitive_summary[competitive_summary['EntityType'] == 'Competitor']

st.subheader('Competitive presence signals')
st.caption(
    'Each rate is based on organisation-neutral responses. Mention, first-mentioned, recommendation and shortlist '
    'rates are response-level measures; first-mentioned, recommendation and shortlist rates use the entity’s own mentions as the denominator.'
)
if target_summary is not None:
    target_metrics = st.columns(4)
    target_metrics[0].metric(f'{tenant.display_name} mention rate', f"{float(target_summary['MentionRate']):.1f}%", border=True)
    target_metrics[1].metric('First-mentioned share', f"{float(target_summary['FirstMentionedRate']):.1f}%", border=True)
    target_metrics[2].metric('Shortlist share', f"{float(target_summary['ShortlistRate']):.1f}%", border=True)
    target_metrics[3].metric('Recommendation share', f"{float(target_summary['RecommendationRate']):.1f}%", border=True)

signal_entities = pd.concat(
    [
        competitive_summary[competitive_summary['EntityType'] == 'Target'],
        competitor_summary.head(8),
    ],
    ignore_index=True,
)
if not signal_entities.empty:
    signal_long = signal_entities.melt(
        id_vars=['Entity', 'EntityType'],
        value_vars=['MentionRate', 'FirstMentionedRate', 'ShortlistRate'],
        var_name='Signal',
        value_name='Rate',
    )
    signal_long['Signal'] = signal_long['Signal'].replace(
        {
            'MentionRate': 'Mention rate',
            'FirstMentionedRate': 'First-mentioned share',
            'ShortlistRate': 'Shortlist share',
        }
    )
    competitive_signal_chart = (
        alt.Chart(signal_long)
        .mark_bar(cornerRadiusEnd=3)
        .encode(
            x=alt.X('Entity:N', title=None, sort='-y', axis=alt.Axis(labelAngle=-30, labelLimit=180)),
            y=alt.Y('Rate:Q', title='Rate (%)', scale=alt.Scale(domain=[0, 100])),
            color=alt.Color('Signal:N', title='Signal'),
            xOffset=alt.XOffset('Signal:N'),
            tooltip=[
                alt.Tooltip('Entity:N', title='Organisation'),
                alt.Tooltip('EntityType:N', title='Type'),
                alt.Tooltip('Signal:N'),
                alt.Tooltip('Rate:Q', title='Rate', format='.1f'),
            ],
        )
        .properties(height=420)
    )
    st.altair_chart(competitive_signal_chart)
    st.dataframe(
        signal_entities[
            [
                'Entity', 'EntityType', 'EligibleResponses', 'MentionedResponses', 'MentionRate',
                'FirstMentionedResponses', 'FirstMentionedRate', 'RecommendedResponses', 'RecommendationRate',
                'ShortlistedResponses', 'ShortlistRate',
            ]
        ],
        hide_index=True,
        column_config={
            'Entity': st.column_config.TextColumn('Organisation', pinned=True),
            'EligibleResponses': st.column_config.NumberColumn('Eligible responses', format='%d'),
            'MentionedResponses': st.column_config.NumberColumn('Mentioned responses', format='%d'),
            'MentionRate': st.column_config.NumberColumn('Mention rate', format='%.1f%%'),
            'FirstMentionedResponses': st.column_config.NumberColumn('First-mentioned responses', format='%d'),
            'FirstMentionedRate': st.column_config.NumberColumn('First-mentioned share', format='%.1f%%'),
            'RecommendedResponses': st.column_config.NumberColumn('Recommended responses', format='%d'),
            'RecommendationRate': st.column_config.NumberColumn('Recommendation share', format='%.1f%%'),
            'ShortlistedResponses': st.column_config.NumberColumn('Shortlisted responses', format='%d'),
            'ShortlistRate': st.column_config.NumberColumn('Shortlist share', format='%.1f%%'),
        },
    )
    st.download_button(
        'Download competitive signal data (CSV)',
        data=signal_entities.to_csv(index=False).encode('utf-8'),
        file_name=f'{tenant.org_id}_competitive_signals.csv',
        mime='text/csv',
        icon=':material/download:',
    )

st.subheader('Organisation co-occurrence')
cooccurrence = competitive_cooccurrence(
    filtered,
    organisation_name=tenant.display_name,
    organisation_aliases=tenant.aliases,
    competitor_aliases=tenant.competitors.aliases_by_name or None,
)
if cooccurrence.empty:
    st.info('No recognised organisation pairs were mentioned together in the current organic response set.')
else:
    top_entities = signal_entities['Entity'].tolist()
    cooccurrence = cooccurrence[
        cooccurrence['EntityA'].isin(top_entities) & cooccurrence['EntityB'].isin(top_entities)
    ].head(30)
    if cooccurrence.empty:
        st.info('No co-occurrence pairs remain after limiting the view to the leading entities above.')
    else:
        st.caption('A co-occurrence is counted once when both organisations appear in the same response.')
        matrix_entities = signal_entities['Entity'].tolist()
        matrix = pd.DataFrame(0, index=matrix_entities, columns=matrix_entities)
        for _, pair in cooccurrence.iterrows():
            entity_a = str(pair['EntityA'])
            entity_b = str(pair['EntityB'])
            if entity_a in matrix.index and entity_b in matrix.columns:
                matrix.loc[entity_a, entity_b] = int(pair['CooccurrenceResponses'])
                matrix.loc[entity_b, entity_a] = int(pair['CooccurrenceResponses'])
        matrix_long = (
            matrix.rename_axis('Organisation A')
            .reset_index()
            .melt(id_vars='Organisation A', var_name='Organisation B', value_name='Responses together')
        )
        st.altair_chart(
            alt.Chart(matrix_long)
            .mark_rect(cornerRadius=2)
            .encode(
                x=alt.X('Organisation B:N', title=None, axis=alt.Axis(labelAngle=-35, labelLimit=160)),
                y=alt.Y('Organisation A:N', title=None, sort=matrix_entities),
                color=alt.Color(
                    'Responses together:Q',
                    title='Responses together',
                    scale=alt.Scale(domain=[0, max(1, int(matrix_long['Responses together'].max()))], range=MOORHOUSE_PURPLE_SCALE),
                ),
                tooltip=[
                    alt.Tooltip('Organisation A:N'),
                    alt.Tooltip('Organisation B:N'),
                    alt.Tooltip('Responses together:Q', format=',d'),
                ],
            )
            .properties(height=460)
        )
        st.dataframe(
            cooccurrence,
            hide_index=True,
            column_config={
                'EntityA': st.column_config.TextColumn('Organisation A', pinned=True),
                'EntityB': st.column_config.TextColumn('Organisation B', pinned=True),
                'CooccurrenceResponses': st.column_config.NumberColumn('Responses together', format='%d'),
                'CooccurrenceRate': st.column_config.NumberColumn('Share of eligible responses', format='%.1f%%'),
            },
        )
        st.download_button(
            'Download co-occurrence data (CSV)',
            data=cooccurrence.to_csv(index=False).encode('utf-8'),
            file_name=f'{tenant.org_id}_competitive_cooccurrence.csv',
            mime='text/csv',
            icon=':material/download:',
        )

def _group_competitive_view(frame: pd.DataFrame, group_column: str) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    eligible = frame[frame['CompetitorPromptEligible'].fillna(False).astype(bool)]
    for group_value, group_frame in eligible.groupby(group_column, dropna=False):
        summary = _competitive_rows(group_frame, tenant)
        target = _target_row(summary, tenant)
        competitors = summary[summary['EntityType'] == 'Competitor']
        top_competitor = competitors.iloc[0] if not competitors.empty else None
        if target is None:
            continue
        rows.append(
            {
                group_column: str(group_value),
                'Eligible responses': int(len(group_frame)),
                'Target mention rate': float(target['MentionRate']),
                'Target first-mentioned share': float(target['FirstMentionedRate']),
                'Target shortlist share': float(target['ShortlistRate']),
                'Top competitor': str(top_competitor['Entity']) if top_competitor is not None else 'None recognised',
                'Top competitor mention rate': float(top_competitor['MentionRate']) if top_competitor is not None else 0.0,
            }
        )
    return pd.DataFrame(rows)

if 'ModelName' in filtered.columns:
    st.subheader('Competitive differences by model')
    model_competitive = _group_competitive_view(filtered, 'ModelName')
    if not model_competitive.empty:
        model_competitive['Model'] = model_competitive['ModelName'].map(MODEL_LABELS).fillna(model_competitive['ModelName'])
        model_long = model_competitive.melt(
            id_vars=['Model'],
            value_vars=['Target mention rate', 'Target first-mentioned share', 'Target shortlist share'],
            var_name='Signal',
            value_name='Rate',
        )
        st.altair_chart(
            alt.Chart(model_long)
            .mark_bar(cornerRadiusEnd=3)
            .encode(
                x=alt.X('Model:N', title=None, axis=alt.Axis(labelAngle=-25)),
                y=alt.Y('Rate:Q', title='Rate (%)', scale=alt.Scale(domain=[0, 100])),
                color=alt.Color('Signal:N', title='Signal'),
                xOffset=alt.XOffset('Signal:N'),
                tooltip=[alt.Tooltip('Model:N'), alt.Tooltip('Signal:N'), alt.Tooltip('Rate:Q', format='.1f')],
            )
            .properties(height=360)
        )
        st.dataframe(
            model_competitive.drop(columns=['ModelName']),
            hide_index=True,
            column_config={
                'Model': st.column_config.TextColumn('Model', pinned=True),
                'Eligible responses': st.column_config.NumberColumn('Eligible responses', format='%d'),
                'Target mention rate': st.column_config.NumberColumn('Target mention rate', format='%.1f%%'),
                'Target first-mentioned share': st.column_config.NumberColumn('Target first-mentioned share', format='%.1f%%'),
                'Target shortlist share': st.column_config.NumberColumn('Target shortlist share', format='%.1f%%'),
                'Top competitor mention rate': st.column_config.NumberColumn('Top competitor mention rate', format='%.1f%%'),
            },
        )

if 'Persona' in filtered.columns:
    st.subheader('Competitive differences by persona')
    persona_competitive = _group_competitive_view(filtered, 'Persona')
    if not persona_competitive.empty:
        st.dataframe(
            persona_competitive,
            hide_index=True,
            column_config={
                'Persona': st.column_config.TextColumn('Persona', pinned=True),
                'Eligible responses': st.column_config.NumberColumn('Eligible responses', format='%d'),
                'Target mention rate': st.column_config.NumberColumn('Target mention rate', format='%.1f%%'),
                'Target first-mentioned share': st.column_config.NumberColumn('Target first-mentioned share', format='%.1f%%'),
                'Target shortlist share': st.column_config.NumberColumn('Target shortlist share', format='%.1f%%'),
                'Top competitor mention rate': st.column_config.NumberColumn('Top competitor mention rate', format='%.1f%%'),
            },
        )

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
st.caption('Raw response-level counts from organisation-neutral prompts; named comparison prompts are excluded.')
st.dataframe(
    model_table,
    hide_index=True,
    column_config={
        'Institution': st.column_config.TextColumn('Organisation', pinned=True, width='large'),
        'Organic mention rate': st.column_config.NumberColumn('Organic mention rate', format='%.1f%%'),
    },
)

st.subheader('Competitors by subject')
by_subject = competitor_mentions(filtered, group_column='Subject')
st.dataframe(by_subject.head(50), hide_index=True)

st.subheader('Competitors by market')
by_market = competitor_mentions(filtered, group_column='Market')
st.dataframe(by_market.head(50), hide_index=True)
