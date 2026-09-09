from __future__ import annotations

import altair as alt
import streamlit as st

from src.recommendations import generate_recommendations
from src.scoring import aggregate_scores, institution_mention_index, institution_mentions_by_model
from src.ui import (
    METRIC_DEFINITIONS,
    MOORHOUSE_PURPLE,
    apply_filters,
    apply_moorhouse_theme,
    render_page_header,
    render_empty_state_guidance,
    require_active_tenant,
    tenant_data_source_label,
    load_core_data,
    render_sidebar_filters,
)

st.set_page_config(page_title='Executive dashboard', page_icon=':material/dashboard:', layout='wide')
apply_moorhouse_theme()
tenant = require_active_tenant()
data_source = tenant_data_source_label(tenant)
render_page_header(
    'Executive dashboard',
    'Headline metrics and visibility patterns',
    eyebrow='Executive view',
)


def _metric_defs_for_org(organisation_name: str) -> dict[str, str]:
    if organisation_name == 'University of Southampton':
        return dict(METRIC_DEFINITIONS)
    return {
        key: value.replace('University of Southampton', organisation_name).replace('Southampton', organisation_name)
        for key, value in METRIC_DEFINITIONS.items()
    }


def _render_metric_definitions_for_org(metric_defs: dict[str, str], *, include_components: bool = False) -> None:
    with st.expander('How these metrics are calculated', icon=':material/info:'):
        st.markdown(f"**Overall visibility score**  \n{metric_defs['visibility']}")
        st.markdown(f"**Reputation score**  \n{metric_defs['reputation']}")
        st.markdown(f"**Average rank**  \n{metric_defs['average_rank']}")
        st.markdown(f"**Prompts in view**  \n{metric_defs['prompts_in_view']}")
        st.markdown(f"**Organisation mentions**  \n{metric_defs['mentions']}")
        if include_components:
            st.markdown(f"**Rank score**  \n{metric_defs['rank_score']}")
            st.markdown(f"**Citation score**  \n{metric_defs['citation_score']}")
st.caption(
    f'Active organization: {tenant.display_name} · Data source: {data_source} · '
    'Results source: OpenRouter captured outputs'
)

try:
    _, _, scored_df = load_core_data(org_id=tenant.org_id)
except Exception as exc:
    st.error(f'Unable to load captured data: {exc}')
    st.stop()

selections = render_sidebar_filters(scored_df, key_prefix='exec_live_v2')
filtered = apply_filters(scored_df, selections)

if filtered.empty:
    render_empty_state_guidance(tenant, area='Executive Dashboard')
    st.stop()

overall = aggregate_scores(filtered).iloc[0]
org_mentions = int(overall.get('org_mentions', overall.get('southampton_mentions', 0)))
metric_defs = _metric_defs_for_org(tenant.display_name)

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric('Overall visibility', f"{overall['visibility_score']:.1f}/100", help=metric_defs['visibility'], border=True)
m2.metric('Reputation score', f"{overall['reputation_score']:.1f}/100", help=metric_defs['reputation'], border=True)
m3.metric('Prompts in view', int(filtered['PromptID'].nunique()), help=metric_defs['prompts_in_view'], border=True)
m4.metric(f'{tenant.display_name} mentions', org_mentions, help=metric_defs['mentions'], border=True)
rank_display = '-' if overall['average_rank'] is None else f"{overall['average_rank']:.2f}"
m5.metric('Average rank', rank_display, help=metric_defs['average_rank'], border=True)

_render_metric_definitions_for_org(metric_defs, include_components=True)

market_scores = aggregate_scores(filtered, ['Market']).sort_values('visibility_score', ascending=False)
subject_scores = aggregate_scores(filtered, ['Subject']).sort_values('visibility_score', ascending=False)
institution_comparison = institution_mention_index(filtered, competitor_limit=10)
model_mention_breakdown = institution_mentions_by_model(filtered, competitor_limit=10)
institution_type_domain = (
    institution_comparison['InstitutionType'].dropna().astype(str).unique().tolist()
    if not institution_comparison.empty
    else ['Competitor', 'Primary organisation']
)
institution_type_range = [MOORHOUSE_PURPLE if value == 'Competitor' else '#00ab8e' for value in institution_type_domain]

left, right = st.columns(2)
with left:
    st.subheader('Visibility by market')
    st.bar_chart(
        market_scores,
        x='Market',
        y='visibility_score',
        x_label='Market',
        y_label='Visibility score',
        color=MOORHOUSE_PURPLE,
    )

with right:
    st.subheader('Visibility by subject')
    st.bar_chart(
        subject_scores,
        x='Subject',
        y='visibility_score',
        x_label='Subject',
        y_label='Visibility score',
        color=MOORHOUSE_PURPLE,
    )

st.subheader(f'{tenant.display_name} relative to leading competitors')
st.caption(
    'Relative mention index: the most-mentioned organisation in the filtered results is set to 100. '
    f'{tenant.display_name} is shown in teal; raw mention counts are available in the tooltip.'
)
comparison_chart = (
    alt.Chart(institution_comparison)
    .mark_bar(cornerRadiusEnd=4)
    .encode(
        x=alt.X(
            'RelativeMentionIndex:Q',
            title='Relative mention index (highest organisation = 100)',
            scale=alt.Scale(domain=[0, 100]),
            axis=alt.Axis(grid=True, tickCount=6),
        ),
        y=alt.Y(
            'Institution:N',
            title=None,
            sort='-x',
            axis=alt.Axis(labelLimit=260),
        ),
        color=alt.Color(
            'InstitutionType:N',
            title=None,
            scale=alt.Scale(
                domain=institution_type_domain,
                range=institution_type_range,
            ),
        ),
        tooltip=[
            alt.Tooltip('Institution:N', title='Organisation'),
            alt.Tooltip('Mentions:Q', title='Raw mentions', format=',d'),
            alt.Tooltip('RelativeMentionIndex:Q', title='Relative mention index', format='.1f'),
        ],
    )
    .properties(height=420)
)
comparison_labels = (
    alt.Chart(institution_comparison)
    .mark_text(align='right', baseline='middle', dx=-6, color='white', font='Poppins', fontSize=12)
    .encode(
        x=alt.X('RelativeMentionIndex:Q'),
        y=alt.Y('Institution:N', sort='-x'),
        text=alt.Text('RelativeMentionIndex:Q', format='.1f'),
    )
)
if institution_comparison.empty:
    st.info(
        'No organisation-neutral prompts match this view. Competitor counts exclude prompts that name the target or a configured competitor.'
    )
else:
    st.altair_chart(comparison_chart + comparison_labels)

    model_labels = {
        'openai/gpt-4.1-mini': 'GPT-4.1 Mini',
        'anthropic/claude-haiku-4.5': 'Claude Haiku 4.5',
        'google/gemini-3.6-flash': 'Gemini 3.6 Flash',
        'qwen/qwen3-max': 'Qwen3 Max',
        'deepseek/deepseek-chat': 'DeepSeek Chat',
        'perplexity/sonar': 'Perplexity Sonar',
    }
    model_table = model_mention_breakdown.pivot_table(
        index='Institution',
        columns='ModelName',
        values='Mentions',
        aggfunc='sum',
        fill_value=0,
    ).rename(columns=model_labels)
    institution_order = institution_comparison['Institution'].tolist()
    model_table = model_table.reindex(institution_order)
    model_table['Total'] = model_table.sum(axis=1)
    neutral_responses = int(filtered['CompetitorPromptEligible'].fillna(False).astype(bool).sum())
    model_table['Organic mention rate'] = model_table['Total'].div(neutral_responses).mul(100).round(1)
    model_table = model_table.reset_index()

    st.subheader('Organic mentions by model')
    st.caption(
        'Raw response-level mentions from organisation-neutral prompts only. '
        'Each model contributes up to one mention per organisation per response.'
    )
    st.dataframe(
        model_table,
        hide_index=True,
        column_config={
            'Institution': st.column_config.TextColumn('Organisation', pinned=True, width='large'),
            'Organic mention rate': st.column_config.NumberColumn('Organic mention rate', format='%.1f%%'),
        },
    )

st.markdown('### High-priority recommendation preview')
recommendations = generate_recommendations(filtered, max_recommendations=3)
st.dataframe(
    recommendations,
    hide_index=True,
    column_order=['Priority', 'Action', 'Scope', 'Evidence', 'Timing'],
    column_config={
        'Priority': st.column_config.TextColumn('Priority', pinned=True, width='small'),
        'Action': st.column_config.TextColumn('Action', pinned=True, width='large'),
        'Evidence': st.column_config.TextColumn('Evidence', width='large'),
    },
)
st.caption('Open Recommendations from the sidebar for the detailed action plan and export.')
