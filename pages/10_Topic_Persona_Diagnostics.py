from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from src.analysis import outlier_responses, segment_summary
from src.ui import (
    MOORHOUSE_PURPLE_SCALE,
    apply_filters,
    apply_moorhouse_theme,
    apply_prompt_scope_filter,
    load_core_data,
    render_empty_state_guidance,
    render_page_header,
    render_prompt_scope_selector,
    render_sidebar_filters,
    require_active_tenant,
    tenant_data_source_label,
)


st.set_page_config(page_title='Topic and persona diagnostics', page_icon=':material/insights:', layout='wide')
apply_moorhouse_theme()
tenant = require_active_tenant()
data_source = tenant_data_source_label(tenant)
render_page_header(
    'Topic and persona diagnostics',
    'Find reputation strengths, gaps and the response evidence behind them',
    eyebrow='Segment diagnostics',
)
scope = render_prompt_scope_selector(key='diagnostics_scope')
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
    render_empty_state_guidance(tenant, area='Topic and Persona Diagnostics')
    st.stop()

filters = render_sidebar_filters(scored_df, key_prefix='diagnostics_live_v1')
filtered = apply_filters(scored_df, filters)
if filtered.empty:
    render_empty_state_guidance(tenant, area='Topic and Persona Diagnostics')
    st.stop()

st.markdown(
    f"""
    <div class='mh-callout'>
        <strong>How to read this page</strong>
        <p>Segments combine dimensions so the analysis stays decision-focused: persona × topic, persona, and expertise area. A “gap” means the organisation is absent, weakly placed, poorly cited or associated less positively in that segment. Every summary can be traced to the response-level evidence shown below.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

segment_columns = [column for column in ['Persona', 'Subject'] if column in filtered.columns]
if not segment_columns:
    st.warning('The loaded prompt bank does not contain persona or topic fields for this view.')
    st.stop()

segments = segment_summary(filtered, segment_columns)
if segments.empty:
    st.info('No topic/persona segments are available for the current filters.')
    st.stop()

weakest = segments.sort_values(['AverageReputationScore', 'Responses']).iloc[0]
strongest = segments.sort_values(['AverageReputationScore', 'Responses'], ascending=[False, False]).iloc[0]
metric_columns = st.columns(4)
metric_columns[0].metric('Segments in view', f"{len(segments):,}", border=True)
metric_columns[1].metric('Weakest segment', f"{float(weakest['AverageReputationScore']):.1f}/100", border=True)
metric_columns[2].metric('Strongest segment', f"{float(strongest['AverageReputationScore']):.1f}/100", border=True)
metric_columns[3].metric('Segments needing action', f"{int(segments['Diagnosis'].ne('Strength').sum()):,}", border=True)
st.caption(
    f"Weakest: {', '.join(str(weakest[column]) for column in segment_columns)}. "
    f"Strongest: {', '.join(str(strongest[column]) for column in segment_columns)}."
)

st.subheader('Reputation map by persona and topic')
if len(segment_columns) == 2:
    reputation_map = (
        alt.Chart(segments)
        .mark_rect(cornerRadius=3)
        .encode(
            x=alt.X('Subject:N', title='Topic', axis=alt.Axis(labelAngle=-35)),
            y=alt.Y('Persona:N', title='Persona'),
            color=alt.Color(
                'AverageReputationScore:Q',
                title='Average reputation score',
                scale=alt.Scale(domain=[0, 100], range=MOORHOUSE_PURPLE_SCALE),
            ),
            tooltip=[
                alt.Tooltip('Persona:N'),
                alt.Tooltip('Subject:N', title='Topic'),
                alt.Tooltip('Responses:Q', format=',d'),
                alt.Tooltip('MentionRate:Q', title='Mention rate', format='.1f'),
                alt.Tooltip('AverageProminence:Q', title='Average prominence', format='.1f'),
                alt.Tooltip('AverageReputationScore:Q', title='Reputation score', format='.1f'),
                alt.Tooltip('Diagnosis:N'),
            ],
        )
        .properties(height=460)
    )
    st.altair_chart(reputation_map)
else:
    st.info('A two-dimensional persona × topic map needs both fields populated.')

segment_display = segments[
    [
        *segment_columns, 'Responses', 'MentionedResponses', 'MentionRate', 'AverageProminence',
        'RecommendationRate', 'ShortlistRate', 'CitationRate', 'PositiveAssociationRate',
        'AverageReputationScore', 'OpportunityScore', 'Diagnosis',
    ]
].sort_values(['OpportunityScore', 'Responses'], ascending=[False, False])
st.dataframe(
    segment_display,
    hide_index=True,
    column_config={
        'Responses': st.column_config.NumberColumn('Responses', format='%d'),
        'MentionedResponses': st.column_config.NumberColumn(f'{tenant.display_name} mentions', format='%d'),
        'MentionRate': st.column_config.NumberColumn('Mention rate', format='%.1f%%'),
        'AverageProminence': st.column_config.NumberColumn('Average prominence', format='%.1f'),
        'RecommendationRate': st.column_config.NumberColumn('Recommended when mentioned', format='%.1f%%'),
        'ShortlistRate': st.column_config.NumberColumn('Shortlisted when mentioned', format='%.1f%%'),
        'CitationRate': st.column_config.NumberColumn('Citation coverage', format='%.1f%%'),
        'PositiveAssociationRate': st.column_config.NumberColumn('Positive association', format='%.1f%%'),
        'AverageReputationScore': st.column_config.NumberColumn('Reputation score', format='%.1f'),
        'OpportunityScore': st.column_config.NumberColumn('Opportunity score', format='%.1f'),
    },
)
st.download_button(
    'Download segment diagnostics (CSV)',
    data=segment_display.to_csv(index=False).encode('utf-8'),
    file_name=f'{tenant.org_id}_segment_diagnostics.csv',
    mime='text/csv',
    icon=':material/download:',
)

st.subheader('Persona and expertise patterns')
pattern_columns = [column for column in ['Persona', 'ExpertiseArea'] if column in filtered.columns]
if pattern_columns:
    pattern_tabs = st.tabs(['Persona pattern', 'Expertise pattern'] if len(pattern_columns) == 2 else [pattern_columns[0]])
    for index, column in enumerate(pattern_columns):
        with pattern_tabs[index]:
            pattern_summary = segment_summary(filtered, [column])
            pattern_display = pattern_summary[
                [column, 'Responses', 'MentionRate', 'AverageProminence', 'RecommendationRate', 'CitationRate', 'PositiveAssociationRate', 'AverageReputationScore', 'Diagnosis']
            ].sort_values(['AverageReputationScore', 'Responses'], ascending=[True, False])
            st.dataframe(
                pattern_display,
                hide_index=True,
                column_config={
                    column: st.column_config.TextColumn(column, pinned=True),
                    'Responses': st.column_config.NumberColumn('Responses', format='%d'),
                    'MentionRate': st.column_config.NumberColumn('Mention rate', format='%.1f%%'),
                    'AverageProminence': st.column_config.NumberColumn('Average prominence', format='%.1f'),
                    'RecommendationRate': st.column_config.NumberColumn('Recommended when mentioned', format='%.1f%%'),
                    'CitationRate': st.column_config.NumberColumn('Citation coverage', format='%.1f%%'),
                    'PositiveAssociationRate': st.column_config.NumberColumn('Positive association', format='%.1f%%'),
                    'AverageReputationScore': st.column_config.NumberColumn('Reputation score', format='%.1f'),
                },
            )

st.subheader('Outlier responses and evidence')
st.caption(
    'Gaps surface absent, negative, uncited or low-prominence responses. Strengths surface recommended, shortlisted or positively associated responses.'
)
outlier_mode = st.segmented_control(
    'Evidence set',
    options=['All', 'Gaps', 'Strengths'],
    default='All',
    key='diagnostics_outlier_mode',
)
outliers = outlier_responses(filtered, limit=15)
if outlier_mode != 'All':
    outliers = outliers[outliers['OutlierType'] == outlier_mode[:-1]]
if outliers.empty:
    st.info('No outlier responses match the current filters.')
else:
    evidence = outliers.copy()
    evidence['Model'] = evidence['ModelName'].astype(str)
    evidence['Response excerpt'] = (
        evidence['ResponseText'].astype(str).str.replace(r'\s+', ' ', regex=True).str.slice(0, 360)
    )
    evidence_display = evidence[
        [
            'OutlierType', 'OutlierReason', 'OutlierScore', 'PromptID', 'Model', 'Persona',
            'Subject', 'Intent', 'Response excerpt', 'CitationSources', 'CompetitorsMentioned',
        ]
    ]
    st.dataframe(
        evidence_display,
        hide_index=True,
        column_config={
            'OutlierType': st.column_config.TextColumn('Type', pinned=True),
            'OutlierReason': st.column_config.TextColumn('Why it surfaced'),
            'OutlierScore': st.column_config.NumberColumn('Signal score', format='%.1f'),
            'Model': st.column_config.TextColumn('Model'),
            'Response excerpt': st.column_config.TextColumn('Response evidence', width='large'),
        },
    )
    st.download_button(
        'Download outlier evidence (CSV)',
        data=outliers.to_csv(index=False).encode('utf-8'),
        file_name=f'{tenant.org_id}_outlier_evidence.csv',
        mime='text/csv',
        icon=':material/download:',
    )
