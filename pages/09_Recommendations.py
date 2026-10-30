from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from src.analysis import outlier_responses, run_history_summary, format_rate_with_denominator
from src.recommendations import build_leader_evidence_matrix, generate_recommendations
from src.ui import (
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


def _evidence_for_recommendation(recommendation: pd.Series, evidence: pd.DataFrame) -> pd.DataFrame:
    if evidence.empty:
        return evidence
    scope = str(recommendation.get('Scope', '')).strip()
    for column in ['Market', 'Subject', 'Persona', 'ModelName']:
        if column in evidence.columns and evidence[column].astype(str).eq(scope).any():
            return evidence[evidence[column].astype(str).eq(scope)].head(3)
    return evidence.head(3)

st.set_page_config(page_title='Recommendations', page_icon=':material/lightbulb:', layout='wide')
apply_moorhouse_theme()
tenant = require_active_tenant()
data_source = tenant_data_source_label(tenant)
render_page_header('Recommendations', 'Prioritised recommendation output with export', eyebrow='Action planning')
scope = render_prompt_scope_selector(key='reco_scope')
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
    render_empty_state_guidance(tenant, area='Recommendations')
    st.stop()

filters = render_sidebar_filters(scored_df, key_prefix='reco_live_v2')
filtered = apply_filters(scored_df, filters)

if filtered.empty:
    render_empty_state_guidance(tenant, area='Recommendations')
    st.stop()

recommendations = generate_recommendations(filtered)
leader_matrix = build_leader_evidence_matrix(filtered)
evidence_rows = outlier_responses(filtered, limit=12)

high_count = int(recommendations['Priority'].eq('High').sum())
medium_count = int(recommendations['Priority'].eq('Medium').sum())

recommendations = recommendations.copy()
recommendations['Status'] = 'Planned'
with st.container(horizontal=True):
    st.metric('Prioritised actions', len(recommendations))
    st.metric('High priority', high_count)
    st.metric('Medium priority', medium_count)
    st.metric('High-priority share', format_rate_with_denominator(high_count, len(recommendations)))

priority_options = ['All', 'High', 'Medium']
try:
    priority_filter = st.segmented_control(
        'Priority',
        options=priority_options,
        default='All',
        key='recommendation_priority',
    )
except Exception:
    priority_filter = st.radio(
        'Priority',
        options=priority_options,
        index=0,
        key='recommendation_priority',
        horizontal=True,
    )
visible_recommendations = (
    recommendations
    if priority_filter == 'All'
    else recommendations[recommendations['Priority'] == priority_filter].reset_index(drop=True)
)

st.subheader('Leader evidence matrix')
st.caption(
    'Uses every eligible organisation-neutral response in the current filtered view. '
    'Segment rows with fewer than 30 responses are directional. Public evidence is a curated '
    'snapshot reviewed on 6 October 2026 and is not evidence that a competitor practice caused its score.'
)
st.dataframe(
    leader_matrix,
    hide_index=True,
    column_config={
        'Lens': st.column_config.TextColumn('Lens', pinned=True, width='small'),
        'Segment': st.column_config.TextColumn('Segment', pinned=True, width='medium'),
        'Eligible responses': st.column_config.NumberColumn('Eligible responses', format='%d'),
        'Organisation mentions': st.column_config.NumberColumn('Organisation mentions', format='%d'),
        'Organisation rate': st.column_config.NumberColumn('Organisation rate', format='%.1f%%'),
        'Leader mentions': st.column_config.NumberColumn('Leader mentions', format='%d'),
        'Leader rate': st.column_config.NumberColumn('Leader rate', format='%.1f%%'),
        'Gap (pp)': st.column_config.NumberColumn('Gap (pp)', format='%.1f'),
    },
)
st.subheader('Action plan')
st.info(
    'Recommendations are evidence-led hypotheses, not guarantees about proprietary model behaviour. '
    'Where the benchmark has at least 30 responses, the target is the minimum next-run signal above a '
    'one-sided 95% binomial threshold under the baseline rate: a measurement threshold, not a forecast. '
    'Smaller samples remain directional and receive no percentage uplift target.',
    icon=':material/science:',
)
st.caption('Recommendations are generated from the captured responses under the current sidebar filters.')

for _, recommendation in visible_recommendations.iterrows():
    label = f"{recommendation['Priority']} · {recommendation['Action']}"
    with st.expander(label, icon=':material/task_alt:'):
        st.caption(
            f"{recommendation['Intervention level']} · {recommendation['Category']} · "
            f"{recommendation['Scope']} · {recommendation['Timing']}"
        )
        st.markdown(f"**Evidence**  \n{recommendation['Evidence']}")
        linked_evidence = _evidence_for_recommendation(recommendation, evidence_rows)
        if not linked_evidence.empty:
            st.markdown('**Response evidence behind this action**')
            for _, evidence in linked_evidence.iterrows():
                excerpt = ' '.join(str(evidence.get('ResponseText', '')).split())[:280]
                st.caption(
                    f"{evidence.get('OutlierType', '')} · {evidence.get('OutlierReason', '')} · "
                    f"{evidence.get('PromptID', '')} · {evidence.get('ModelName', '')}"
                )
                st.write(excerpt)
        st.markdown(f"**Objective**  \n{recommendation['Objective']}")
        st.markdown(f"**Signal affected**  \n{recommendation['Affected signal']}")
        st.markdown(f"**Why this may matter**  \n{recommendation['Why this may matter']}")
        st.caption(
            f"Evidence strength: {recommendation['Evidence strength']} · "
            f"Confidence: {recommendation['Confidence']}"
        )
        st.markdown(f"**Method basis**  \n{recommendation['Method basis']}")
        st.markdown(f"**Benchmark comparator**  \n{recommendation['Comparator']}")
        st.markdown(f"**Comparative performance**  \n{recommendation['Comparative performance']}")
        st.markdown(
            f"**Comparator evidence pattern**  \n{recommendation['Comparator evidence pattern']}"
        )
        st.markdown(
            f"**{tenant.display_name} evidence position**  \n"
            f"{recommendation['Organisation evidence position']}"
        )
        st.caption(
            f"Comparative evidence quality: {recommendation['Evidence quality rating']} "
            f"({int(recommendation['Evidence quality score'])}/100)"
        )
        if recommendation['Comparator sources']:
            st.markdown(f"**Comparator sources**  \n{recommendation['Comparator sources']}")
        st.markdown(f"**Comparative limitation**  \n{recommendation['Comparative limitation']}")
        st.markdown(f"**Comparable peer**  \n{recommendation['Comparable peer']}")
        st.markdown(f"**Peer performance**  \n{recommendation['Peer performance']}")
        st.markdown(f"**Peer evidence pattern**  \n{recommendation['Peer evidence pattern']}")
        if recommendation['Peer sources']:
            st.markdown(f"**Peer sources**  \n{recommendation['Peer sources']}")
        st.markdown('**Actions**')
        st.markdown(recommendation['Action plan'])
        st.markdown(f"**Owner**  \n{recommendation['Owner']}")
        st.markdown(f"**Baseline**  \n{recommendation['Baseline']}")
        st.markdown(f"**Target calculation**  \n{recommendation['Target calculation']}")
        st.markdown(f"**Validation method**  \n{recommendation['Validation method']}")

st.subheader('Portfolio view')
st.dataframe(
    visible_recommendations,
    hide_index=True,
    column_order=[
        'Priority', 'Action', 'Intervention level', 'Scope', 'Affected signal',
        'Comparator', 'Comparative performance', 'Comparable peer', 'Peer performance',
        'Evidence quality rating',
        'Evidence strength', 'Method basis', 'Baseline', 'Target calculation', 'Confidence',
        'Owner', 'Timing', 'Status',
    ],
    column_config={
        'Priority': st.column_config.TextColumn('Priority', pinned=True, width='small'),
        'Action': st.column_config.TextColumn('Action', pinned=True, width='large'),
        'Scope': st.column_config.TextColumn('Scope', width='medium'),
        'Intervention level': st.column_config.TextColumn('Level', width='small'),
        'Affected signal': st.column_config.TextColumn('Signal affected', width='medium'),
        'Comparator': st.column_config.TextColumn('Comparator', width='medium'),
        'Comparative performance': st.column_config.TextColumn('Comparative performance', width='large'),
        'Comparable peer': st.column_config.TextColumn('Comparable peer', width='medium'),
        'Peer performance': st.column_config.TextColumn('Peer performance', width='large'),
        'Evidence quality rating': st.column_config.TextColumn('Comparative evidence', width='small'),
        'Evidence strength': st.column_config.TextColumn('Evidence strength', width='medium'),
        'Method basis': st.column_config.TextColumn('Method basis', width='large'),
        'Baseline': st.column_config.TextColumn('Baseline', width='medium'),
        'Target calculation': st.column_config.TextColumn('Target calculation', width='large'),
        'Confidence': st.column_config.TextColumn('Confidence', width='medium'),
        'Owner': st.column_config.TextColumn('Owner', width='medium'),
        'Timing': st.column_config.TextColumn('Timing', width='small'),
        'Status': st.column_config.TextColumn('Status', width='small'),
    },
)

st.download_button(
    label='Export recommendations (CSV)',
    data=visible_recommendations.to_csv(index=False).encode('utf-8'),
    file_name=f'{tenant.org_id}_recommendations.csv',
    mime='text/csv',
)

st.subheader('Evidence register')
st.caption('These are the highest-signal response rows used to ground the action plan. Open the execution page for full response text and request metadata.')
if evidence_rows.empty:
    st.info('No gap or strength evidence rows are available for this filtered view.')
else:
    evidence_display = evidence_rows.copy()
    evidence_display['Response excerpt'] = (
        evidence_display['ResponseText'].astype(str).str.replace(r'\s+', ' ', regex=True).str.slice(0, 360)
    )
    evidence_display = evidence_display[
        [
            'OutlierType', 'OutlierReason', 'OutlierScore', 'PromptID', 'ModelName',
            'Persona', 'Subject', 'ExpertiseArea', 'Market', 'Response excerpt',
            'CitationSources', 'CompetitorsMentioned',
        ]
    ]
    st.dataframe(
        evidence_display,
        hide_index=True,
        column_config={
            'OutlierType': st.column_config.TextColumn('Type', pinned=True),
            'OutlierReason': st.column_config.TextColumn('Why it surfaced'),
            'OutlierScore': st.column_config.NumberColumn('Signal score', format='%.1f'),
            'ModelName': st.column_config.TextColumn('Model'),
            'Response excerpt': st.column_config.TextColumn('Response evidence', width='large'),
        },
    )
    st.download_button(
        'Download evidence register (CSV)',
        data=evidence_rows.to_csv(index=False).encode('utf-8'),
        file_name=f'{tenant.org_id}_recommendation_evidence.csv',
        mime='text/csv',
    )

history = run_history_summary(filtered)
st.subheader('Run-over-run tracking')
st.caption('Run history is grouped by captured RunDate so matched sweeps can be compared without treating partial request batches as separate runs.')
if history.empty:
    st.info('Run dates are not available in this result set yet.')
else:
    if len(history) < 2:
        st.info('This tenant currently has one captured run date. A later matched rerun will populate the change columns.')
    history_chart = history.melt(
        id_vars=['Run'],
        value_vars=['MentionRate', 'ReputationScore'],
        var_name='Metric',
        value_name='Score',
    )
    history_chart['Metric'] = history_chart['Metric'].replace(
        {'MentionRate': 'Mention rate', 'ReputationScore': 'Reputation score'}
    )
    st.altair_chart(
        alt.Chart(history_chart)
        .mark_line(point=True)
        .encode(
            x=alt.X('Run:N', title='Captured run date', sort=history['Run'].tolist()),
            y=alt.Y('Score:Q', title='Score / rate', scale=alt.Scale(domain=[0, 100])),
            color=alt.Color('Metric:N', title='Metric'),
            tooltip=[alt.Tooltip('Run:N'), alt.Tooltip('Metric:N'), alt.Tooltip('Score:Q', format='.1f')],
        )
        .properties(height=340)
    )
    st.dataframe(
        history,
        hide_index=True,
        column_config={
            'Run': st.column_config.TextColumn('Captured run', pinned=True),
            'Responses': st.column_config.NumberColumn('Responses', format='%d'),
            'Prompts': st.column_config.NumberColumn('Prompts', format='%d'),
            'Models': st.column_config.NumberColumn('Models', format='%d'),
            'MentionRate': st.column_config.NumberColumn('Mention rate', format='%.1f%%'),
            'RecommendationRate': st.column_config.NumberColumn('Recommended when mentioned', format='%.1f%%'),
            'ShortlistRate': st.column_config.NumberColumn('Shortlisted when mentioned', format='%.1f%%'),
            'CitationRate': st.column_config.NumberColumn('Citation coverage', format='%.1f%%'),
            'AverageProminence': st.column_config.NumberColumn('Average prominence', format='%.1f'),
            'ReputationScore': st.column_config.NumberColumn('Reputation score', format='%.1f'),
            'MentionRateChange': st.column_config.NumberColumn('Mention-rate change', format='%.1f'),
            'ReputationScoreChange': st.column_config.NumberColumn('Reputation-score change', format='%.1f'),
        },
    )
