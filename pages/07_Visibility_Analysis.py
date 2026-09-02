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
