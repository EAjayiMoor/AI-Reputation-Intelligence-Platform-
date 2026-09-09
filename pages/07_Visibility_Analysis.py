from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from src.scoring import aggregate_scores
from src.ui import (
    METRIC_DEFINITIONS,
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


def _measurement_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Return the stable measurement columns used by the Sprint 2 views."""
    working = frame.copy()
    if 'Mentioned' not in working.columns:
        working['Mentioned'] = working['visible_bool']
    if 'Recommended' not in working.columns:
        working['Recommended'] = False
    if 'Shortlisted' not in working.columns:
        working['Shortlisted'] = False
    if 'CitationPresent' not in working.columns:
        working['CitationPresent'] = working['citation_score_row'].gt(0)
    if 'AssociationLabel' not in working.columns:
        working['AssociationLabel'] = 'Not available'
    if 'ProminenceScore' not in working.columns:
        working['ProminenceScore'] = working['rank_score_row']
    working['Mentioned'] = working['Mentioned'].fillna(False).astype(bool)
    working['Recommended'] = working['Recommended'].fillna(False).astype(bool)
    working['Shortlisted'] = working['Shortlisted'].fillna(False).astype(bool)
    working['CitationPresent'] = working['CitationPresent'].fillna(False).astype(bool)
    working['AssociationLabel'] = working['AssociationLabel'].fillna('Not available').astype(str)
    if 'ModelName' in working.columns:
        working['Model'] = working['ModelName'].map(MODEL_LABELS).fillna(working['ModelName'].astype(str))
    return working


def _signal_summary(frame: pd.DataFrame, group_columns: list[str]) -> pd.DataFrame:
    working = _measurement_frame(frame)
    for column in group_columns:
        working[column] = working[column].fillna('Unknown').astype(str)
    summary = (
        working.groupby(group_columns, dropna=False)
        .agg(
            Responses=('PromptID', 'size'),
            Mentions=('Mentioned', 'sum'),
            Recommendations=('Recommended', 'sum'),
            Shortlists=('Shortlisted', 'sum'),
            Cited=('CitationPresent', 'sum'),
            AverageProminence=('ProminenceScore', 'mean'),
        )
        .reset_index()
    )
    summary['Mention rate'] = (summary['Mentions'].div(summary['Responses']).mul(100)).round(1)
    summary['Citation rate'] = (summary['Cited'].div(summary['Responses']).mul(100)).round(1)
    summary['Recommendation rate'] = (
        summary['Recommendations'].div(summary['Mentions'].where(summary['Mentions'].gt(0))).mul(100)
    ).fillna(0).round(1)
    summary['Shortlist rate'] = (
        summary['Shortlists'].div(summary['Mentions'].where(summary['Mentions'].gt(0))).mul(100)
    ).fillna(0).round(1)
    summary['Average prominence'] = summary['AverageProminence'].round(1)
    return summary


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

st.set_page_config(page_title='Visibility analysis', page_icon=':material/visibility:', layout='wide')
apply_moorhouse_theme()
tenant = require_active_tenant()
data_source = tenant_data_source_label(tenant)
render_page_header('Visibility analysis', 'Heatmap and rank analysis by segment', eyebrow='Visibility diagnostics')
scope = render_prompt_scope_selector(key='visibility_scope_filter')
metric_defs = _metric_defs_for_org(tenant.display_name)
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
    render_empty_state_guidance(tenant, area='Visibility Analysis')
    st.stop()

filters = render_sidebar_filters(scored_df, key_prefix='visibility_live_v2')
filtered = apply_filters(scored_df, filters)

if filtered.empty:
    render_empty_state_guidance(tenant, area='Visibility Analysis')
    st.stop()

st.markdown(
    f"""
    <div class='mh-callout'>
        <strong>How to read this page</strong>
        <p>The heatmap shows the average visibility score for each market/subject slice. A row is scored as 100 when {tenant.display_name} is visible and 0 when it is absent. Rank contribution is then weighted by placement (1 = 100, 2 = 90, 3 = 80, 4–5 = 70, 6–10 = 50, otherwise 40), and citation presence adds another 100-or-0 signal. The blended reputation score is 0.5 × visibility + 0.3 × rank + 0.2 × citation.</p>
    </div>
    """,
    unsafe_allow_html=True,
)
_render_metric_definitions_for_org(metric_defs, include_components=True)

measurement_df = _measurement_frame(filtered)
response_total = len(measurement_df)
mention_total = int(measurement_df['Mentioned'].sum())
mentioned_denominator = max(mention_total, 1)
mention_rate = mention_total / response_total * 100 if response_total else 0
recommendation_rate = measurement_df['Recommended'].sum() / mentioned_denominator * 100
shortlist_rate = measurement_df['Shortlisted'].sum() / mentioned_denominator * 100
citation_rate = measurement_df['CitationPresent'].sum() / response_total * 100 if response_total else 0
positive_rate = (
    measurement_df.loc[measurement_df['Mentioned'], 'AssociationLabel'].eq('Positive').sum()
    / mentioned_denominator
    * 100
)

st.subheader('LLM presence snapshot')
st.caption(
    'Rates are calculated from captured response rows after the current prompt-bank, scope and sidebar filters. '
    'Recommendation, shortlist and positive-association rates use only responses that mention the organisation.'
)
metric_columns = st.columns(5)
metric_columns[0].metric('Mention rate', f'{mention_rate:.1f}%', border=True)
metric_columns[1].metric('Recommended when mentioned', f'{recommendation_rate:.1f}%', border=True)
metric_columns[2].metric('Shortlisted when mentioned', f'{shortlist_rate:.1f}%', border=True)
metric_columns[3].metric('Citation coverage', f'{citation_rate:.1f}%', border=True)
metric_columns[4].metric('Positive association', f'{positive_rate:.1f}%', border=True)

st.subheader('Presence signals by model')
model_summary = _signal_summary(measurement_df, ['Model'])
signal_long = model_summary.melt(
    id_vars=['Model'],
    value_vars=['Mention rate', 'Recommendation rate', 'Shortlist rate', 'Citation rate'],
    var_name='Signal',
    value_name='Rate',
)
signal_chart = (
    alt.Chart(signal_long)
    .mark_bar(cornerRadiusEnd=3)
    .encode(
        x=alt.X('Model:N', title=None, axis=alt.Axis(labelAngle=-25)),
        y=alt.Y('Rate:Q', title='Rate (%)', scale=alt.Scale(domain=[0, 100])),
        color=alt.Color('Signal:N', title='Signal'),
        xOffset=alt.XOffset('Signal:N'),
        tooltip=[
            alt.Tooltip('Model:N'),
            alt.Tooltip('Signal:N'),
            alt.Tooltip('Rate:Q', title='Rate', format='.1f'),
        ],
    )
    .properties(height=360)
)
st.altair_chart(signal_chart)

model_table = model_summary[
    [
        'Model', 'Responses', 'Mentions', 'Mention rate', 'Average prominence',
        'Recommendation rate', 'Shortlist rate', 'Citation rate',
    ]
].sort_values('Mention rate', ascending=False)
st.dataframe(
    model_table,
    hide_index=True,
    column_config={
        'Model': st.column_config.TextColumn('Model', pinned=True),
        'Responses': st.column_config.NumberColumn('Responses', format='%d'),
        'Mentions': st.column_config.NumberColumn(f'{tenant.display_name} mentions', format='%d'),
        'Mention rate': st.column_config.NumberColumn('Mention rate', format='%.1f%%'),
        'Average prominence': st.column_config.NumberColumn('Average prominence', format='%.1f'),
        'Recommendation rate': st.column_config.NumberColumn('Recommended when mentioned', format='%.1f%%'),
        'Shortlist rate': st.column_config.NumberColumn('Shortlisted when mentioned', format='%.1f%%'),
        'Citation rate': st.column_config.NumberColumn('Citation coverage', format='%.1f%%'),
    },
)

group_columns = [column for column in ['Persona', 'Subject'] if column in measurement_df.columns]
if group_columns:
    st.subheader('Presence by persona and topic')
    topic_summary = _signal_summary(measurement_df, group_columns)
    if len(group_columns) == 2:
        topic_heatmap = (
            alt.Chart(topic_summary)
            .mark_rect(cornerRadius=3)
            .encode(
                x=alt.X('Subject:N', title='Topic', axis=alt.Axis(labelAngle=-35)),
                y=alt.Y('Persona:N', title='Persona'),
                color=alt.Color(
                    'Mention rate:Q',
                    title='Mention rate (%)',
                    scale=alt.Scale(domain=[0, 100], range=MOORHOUSE_PURPLE_SCALE),
                ),
                tooltip=[
                    alt.Tooltip('Persona:N'),
                    alt.Tooltip('Subject:N', title='Topic'),
                    alt.Tooltip('Responses:Q', format=',d'),
                    alt.Tooltip('Mention rate:Q', format='.1f'),
                    alt.Tooltip('Average prominence:Q', format='.1f'),
                    alt.Tooltip('Recommendation rate:Q', title='Recommended when mentioned', format='.1f'),
                    alt.Tooltip('Shortlist rate:Q', title='Shortlisted when mentioned', format='.1f'),
                ],
            )
            .properties(height=420)
        )
        st.altair_chart(topic_heatmap)
    st.dataframe(
        topic_summary.sort_values(['Mention rate', 'Responses'], ascending=[False, False]),
        hide_index=True,
        column_config={
            'Responses': st.column_config.NumberColumn('Responses', format='%d'),
            'Mentions': st.column_config.NumberColumn(f'{tenant.display_name} mentions', format='%d'),
            'Mention rate': st.column_config.NumberColumn('Mention rate', format='%.1f%%'),
            'Average prominence': st.column_config.NumberColumn('Average prominence', format='%.1f'),
            'Recommendation rate': st.column_config.NumberColumn('Recommended when mentioned', format='%.1f%%'),
            'Shortlist rate': st.column_config.NumberColumn('Shortlisted when mentioned', format='%.1f%%'),
            'Citation rate': st.column_config.NumberColumn('Citation coverage', format='%.1f%%'),
        },
    )

st.subheader('Association profile')
association_frame = (
    measurement_df.groupby(['Model', 'AssociationLabel'], as_index=False)
    .size()
    .rename(columns={'size': 'Responses'})
)
association_frame['Rate'] = association_frame.groupby('Model')['Responses'].transform(
    lambda values: values / values.sum() * 100
)
association_chart = (
    alt.Chart(association_frame)
    .mark_bar()
    .encode(
        x=alt.X('Model:N', title=None, axis=alt.Axis(labelAngle=-25)),
        y=alt.Y('Rate:Q', title='Share of responses (%)', scale=alt.Scale(domain=[0, 100])),
        color=alt.Color('AssociationLabel:N', title='Association'),
        tooltip=[
            alt.Tooltip('Model:N'),
            alt.Tooltip('AssociationLabel:N', title='Association'),
            alt.Tooltip('Responses:Q', format=',d'),
            alt.Tooltip('Rate:Q', title='Share', format='.1f'),
        ],
    )
    .properties(height=360)
)
st.altair_chart(association_chart)
st.caption(
    'Association is measured from language in the same sentence or line as the organisation. '
    '“Not mentioned” is kept separate from neutral sentiment.'
)

st.subheader('Visibility heatmap (market × subject)')
heatmap_source = aggregate_scores(filtered, ['Market', 'Subject'])
response_counts = (
    filtered.groupby(['Market', 'Subject'], as_index=False)
    .size()
    .rename(columns={'size': 'Responses'})
)
heatmap_source = heatmap_source.merge(response_counts, on=['Market', 'Subject'], how='left')

# Include every market/subject intersection so absence of prompts is visibly distinct from a score of zero.
heatmap_grid = pd.MultiIndex.from_product(
    [
        sorted(filtered['Market'].dropna().astype(str).unique()),
        sorted(filtered['Subject'].dropna().astype(str).unique()),
    ],
    names=['Market', 'Subject'],
).to_frame(index=False)
heatmap_source = heatmap_grid.merge(heatmap_source, on=['Market', 'Subject'], how='left')
heatmap_source['Has data'] = heatmap_source['Responses'].notna()
heatmap_source['Cell status'] = heatmap_source['Has data'].map(
    {True: 'Captured model responses', False: 'No prompts in this market/subject combination'}
)
heatmap_source['Visibility label'] = heatmap_source.apply(
    lambda row: f"{row['visibility_score']:.1f}" if row['Has data'] else 'No prompts',
    axis=1,
)
for count_column in ['prompt_count', 'org_mentions', 'southampton_mentions', 'Responses']:
    if count_column not in heatmap_source.columns:
        heatmap_source[count_column] = 0
    heatmap_source[count_column] = heatmap_source[count_column].fillna(0).astype(int)

mention_column = 'org_mentions' if 'org_mentions' in heatmap_source.columns else 'southampton_mentions'

st.caption(
    f'A numeric value means captured responses exist. 0.0 means {tenant.display_name} appeared in none of them. '
    'Grey “No prompts” cells were not tested because that market/subject combination is absent from the prompt bank.'
)
base = alt.Chart(heatmap_source).encode(
    x=alt.X('Subject:N', title='Subject', axis=alt.Axis(labelAngle=-35)),
    y=alt.Y('Market:N', title='Market'),
)
heatmap = base.mark_rect(cornerRadius=4).encode(
    color=alt.condition(
        'datum["Has data"]',
        alt.Color(
            'visibility_score:Q',
            title='Visibility score',
            scale=alt.Scale(domain=[0, 100], range=MOORHOUSE_PURPLE_SCALE),
        ),
        alt.value('#e6e1e8'),
    ),
    tooltip=[
        alt.Tooltip('Market:N'),
        alt.Tooltip('Subject:N'),
        alt.Tooltip('Cell status:N', title='Coverage'),
        alt.Tooltip('prompt_count:Q', title='Prompts', format=',d'),
        alt.Tooltip('Responses:Q', title='Model responses', format=',d'),
        alt.Tooltip(f'{mention_column}:Q', title=f'{tenant.display_name} mentions', format=',d'),
        alt.Tooltip('visibility_score:Q', title='Visibility score', format='.1f'),
    ],
)
labels = base.mark_text(font='Poppins', fontSize=12).encode(
    text=alt.Text('Visibility label:N'),
    color=alt.condition(
        'datum["Has data"] && datum.visibility_score >= 55',
        alt.value('#ffffff'),
        alt.value('#181018'),
    ),
)
st.altair_chart((heatmap + labels).properties(height=500))

st.subheader('Average rank by subject and model')
visible_only = filtered[filtered['visible_bool']]
rank_table = (
    visible_only.groupby(['Subject', 'ModelName'], as_index=False)
    .agg(
        Org_mentions=('visible_bool', 'size'),
        Ranked_responses=('rank_float', 'count'),
        Average_rank=('rank_float', 'mean'),
    )
)
if rank_table.empty:
    st.info('No visible prompts with rank data for this selection.')
else:
    rank_table['Model'] = rank_table['ModelName'].replace(
        {
            'openai/gpt-4.1-mini': 'GPT-4.1 Mini',
            'anthropic/claude-haiku-4.5': 'Claude Haiku 4.5',
            'google/gemini-3.6-flash': 'Gemini 3.6 Flash',
            'qwen/qwen3-max': 'Qwen3 Max',
            'deepseek/deepseek-chat': 'DeepSeek Chat',
        }
    )
    rank_table['Average rank'] = rank_table['Average_rank'].map(
        lambda value: 'Not ranked' if pd.isna(value) else f'{value:.2f}'
    )
    rank_table = rank_table[
        ['Subject', 'Model', 'Org_mentions', 'Ranked_responses', 'Average rank']
    ].sort_values(['Subject', 'Model'])
    st.caption(
        f'A ranked mention places {tenant.display_name} at a numerical position in an ordered recommendation list. '
        f'“Not ranked” means {tenant.display_name} was mentioned, but no numerical placement was available.'
    )
    st.dataframe(
        rank_table,
        hide_index=True,
        column_config={
            'Subject': st.column_config.TextColumn('Subject', pinned=True),
            'Model': st.column_config.TextColumn('Model', pinned=True),
            'Org_mentions': st.column_config.NumberColumn(f'{tenant.display_name} mentions', format='%d'),
            'Ranked_responses': st.column_config.NumberColumn('Ranked mentions', format='%d'),
            'Average rank': st.column_config.TextColumn('Average rank'),
        },
    )
