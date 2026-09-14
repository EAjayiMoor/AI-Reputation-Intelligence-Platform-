from __future__ import annotations

import altair as alt
import streamlit as st

from src.analysis import compute_scope_metrics, format_rate_with_denominator, split_scope_frames
from src.recommendations import generate_recommendations
from src.scoring import aggregate_scores, institution_mention_index, institution_mentions_by_model
from src.ui import (
    METRIC_DEFINITIONS,
    MOORHOUSE_PURPLE,
    apply_filters,
    apply_prompt_mention_mode_filter,
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


def _visibility_chart(frame, category: str) -> alt.Chart:
    """Build a readable, consistently aligned visibility chart."""
    chart_data = frame[[category, 'visibility_score']].copy()
    chart_data[category] = chart_data[category].fillna('Unknown').astype(str)
    chart_data['visibility_score'] = chart_data['visibility_score'].fillna(0).astype(float)
    chart_data = chart_data.sort_values('visibility_score', ascending=False).reset_index(drop=True)
    category_order = chart_data[category].tolist()
    chart_height = max(220, min(420, len(chart_data) * 34))

    bars = alt.Chart(chart_data).mark_bar(cornerRadiusEnd=4, color=MOORHOUSE_PURPLE).encode(
        x=alt.X(
            'visibility_score:Q',
            title='Visibility score',
            scale=alt.Scale(domain=[0, 100]),
            axis=alt.Axis(grid=True, values=[0, 20, 40, 60, 80, 100]),
        ),
        y=alt.Y(
            f'{category}:N',
            title=None,
            sort=category_order,
            axis=alt.Axis(labelLimit=180),
        ),
        tooltip=[
            alt.Tooltip(f'{category}:N', title=category),
            alt.Tooltip('visibility_score:Q', title='Visibility score', format='.1f'),
        ],
    )
    return bars.properties(height=chart_height)


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
mention_mode = str(selections.get('PromptMentionType', 'All'))
base_selections = {column: value for column, value in selections.items() if column != 'PromptMentionType'}
filtered_scope = apply_filters(scored_df, base_selections)
filtered = apply_prompt_mention_mode_filter(filtered_scope, mention_mode)

if scored_df.empty:
    render_empty_state_guidance(tenant, area='Executive dashboard')
    st.stop()

if filtered.empty:
    st.warning('No captured responses match the current filters.')
    st.caption('Clear one or more sidebar filters, or choose a different prompt mention mode.')
    st.stop()

scope_frames = split_scope_frames(filtered_scope)
scope_metrics = {
    scope.key: compute_scope_metrics(scope.frame, owned_domains=tenant.domains)
    for scope in scope_frames
}

st.subheader('Presence by prompt scope')
st.caption(
    'This comparison keeps the market, subject, persona, expertise, intent, model and platform filters, '
    'then separates results by whether the prompt names the organisation.'
)
scope_columns = st.columns(3)
for scope_column, scope in zip(scope_columns, scope_frames):
    metrics = scope_metrics[scope.key]
    with scope_column.container(border=True, height='stretch'):
        st.markdown(f'**{scope.label}**')
        st.metric(
            'Response presence',
            format_rate_with_denominator(
                int(metrics['mention_responses']),
                int(metrics['responses']),
            ),
        )
        st.caption(
            f"Prompt presence: {format_rate_with_denominator(int(metrics['mention_prompts']), int(metrics['prompts']))}"
        )
        st.caption(
            f"Citation coverage: {format_rate_with_denominator(int(metrics['citation_responses']), int(metrics['responses']))}"
        )
        pressure = metrics['competitor_pressure_ratio']
        pressure_text = '-' if pressure is None else f'{pressure:.2f}'
        st.caption(f'Competitor-to-organisation mention ratio: {pressure_text}')

overall = aggregate_scores(filtered).iloc[0]
org_mentions = int(overall.get('org_mentions', overall.get('southampton_mentions', 0)))
metric_defs = _metric_defs_for_org(tenant.display_name)

rank_display = '-' if overall['average_rank'] is None else f"{overall['average_rank']:.2f}"
st.subheader(f'Selected view: {mention_mode}')
with st.container(horizontal=True):
    st.metric('Overall visibility', f"{overall['visibility_score']:.1f}/100", help=metric_defs['visibility'], border=True)
    st.metric('Reputation score', f"{overall['reputation_score']:.1f}/100", help=metric_defs['reputation'], border=True)
    st.metric('Prompts in view', int(filtered['PromptID'].nunique()), help=metric_defs['prompts_in_view'], border=True)
    st.metric(f'{tenant.display_name} mentions', org_mentions, help=metric_defs['mentions'], border=True)
    st.metric('Average rank', rank_display, help=metric_defs['average_rank'], border=True)

_render_metric_definitions_for_org(metric_defs, include_components=True)

market_scores = aggregate_scores(filtered, ['Market']).sort_values('visibility_score', ascending=False)
subject_scores = aggregate_scores(filtered, ['Subject']).sort_values('visibility_score', ascending=False)
institution_comparison = institution_mention_index(filtered, competitor_limit=10)
model_mention_breakdown = institution_mentions_by_model(filtered, competitor_limit=10)
comparison_display = institution_comparison.copy()
if not comparison_display.empty:
    comparison_display['InstitutionType'] = comparison_display['InstitutionType'].where(
        comparison_display['InstitutionType'].astype(str) == 'Competitor',
        'Primary organisation',
    )

top_competitor_name = '-'
top_competitor_gap = '-'
if not comparison_display.empty:
    target_rows = comparison_display[
        comparison_display['InstitutionType'].astype(str) == 'Primary organisation'
    ]
    competitor_rows = comparison_display[
        comparison_display['InstitutionType'].astype(str) == 'Competitor'
    ]
    if not target_rows.empty and not competitor_rows.empty:
        target_index = float(target_rows['RelativeMentionIndex'].iloc[0])
        top_competitor = competitor_rows.sort_values('RelativeMentionIndex', ascending=False).iloc[0]
        top_competitor_name = str(top_competitor['Institution'])
        top_competitor_gap = f"{float(top_competitor['RelativeMentionIndex']) - target_index:.1f}"

pressure_value = scope_metrics['organic']['competitor_pressure_ratio']
pressure_display = '-' if pressure_value is None else f'{pressure_value:.2f}'
with st.container(horizontal=True):
    st.metric('Organic competitor-to-organisation ratio', pressure_display, border=True)
    st.metric('Most-mentioned competitor', top_competitor_name, border=True)
    st.metric('Competitor lead (index points)', top_competitor_gap, border=True)

institution_type_domain = (
    comparison_display['InstitutionType'].dropna().astype(str).unique().tolist()
    if not comparison_display.empty
    else ['Competitor', 'Primary organisation']
)
institution_type_range = [MOORHOUSE_PURPLE if value == 'Competitor' else '#00ab8e' for value in institution_type_domain]

left, right = st.columns(2)
with left:
    with st.container(border=True, height='stretch'):
        st.subheader('Visibility by market')
        st.altair_chart(_visibility_chart(market_scores, 'Market'))

with right:
    with st.container(border=True, height='stretch'):
        st.subheader('Visibility by subject')
        st.altair_chart(_visibility_chart(subject_scores, 'Subject'))

st.subheader(f'{tenant.display_name} relative to leading competitors')
st.caption(
    'Relative mention index: the most-mentioned organisation in the filtered results is set to 100. '
    f'{tenant.display_name} is shown in teal; raw mention counts are available in the tooltip.'
)
institution_order = (
    comparison_display.sort_values('RelativeMentionIndex', ascending=False)['Institution'].tolist()
    if not comparison_display.empty
    else []
)
comparison_height = max(260, min(520, len(comparison_display) * 38))
comparison_chart = (
    alt.Chart(comparison_display)
    .mark_bar(cornerRadiusEnd=4)
    .encode(
        x=alt.X(
            'RelativeMentionIndex:Q',
            title='Relative mention index (highest organisation = 100)',
            scale=alt.Scale(domain=[0, 110]),
            axis=alt.Axis(grid=True, values=[0, 20, 40, 60, 80, 100]),
        ),
        y=alt.Y(
            'Institution:N',
            title=None,
            sort=institution_order,
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
    .properties(height=comparison_height)
)
comparison_labels = (
    alt.Chart(comparison_display)
    .mark_text(align='left', baseline='middle', dx=6, color=MOORHOUSE_PURPLE, font='Poppins', fontSize=12)
    .encode(
        x=alt.X('RelativeMentionIndex:Q'),
        y=alt.Y('Institution:N', sort=institution_order),
        text=alt.Text('RelativeMentionIndex:Q', format='.1f'),
    )
)
if comparison_display.empty:
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
