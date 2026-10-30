"""Scenario views for the two explicitly selected saved demos."""
import altair as alt
import pandas as pd
import streamlit as st

from src.analysis import compute_scope_metrics, format_rate_with_denominator
from src.ui.data import apply_filters
from src.ui.moorhouse import MOORHOUSE_PURPLE
from src.ui.demo_competitors import render_demo_competitors


def _breakdown(frame, dimension, domains):
    rows = []
    for value, group in frame.groupby(dimension, dropna=False):
        metrics = compute_scope_metrics(group, owned_domains=domains)
        rows.append({dimension: value, 'Responses': len(group),
                     'Southampton mentions': metrics['mention_responses'],
                     'Mention rate (%)': round(metrics['presence_rate_response'], 1),
                     'Responses with citations': metrics['citation_responses'],
                     'Citation rate (%)': round(metrics['citation_coverage'], 1)})
    return pd.DataFrame(rows).sort_values('Mention rate (%)', ascending=False)


def filter_demo_responses(demo, scored):
    selections = {}
    st.sidebar.subheader('Demo filters')
    for field in ('Market', 'Persona', 'Subject', 'Category', 'ModelName'):
        values = sorted(scored[field].dropna().astype(str).unique())
        selections[field] = st.sidebar.selectbox(
            'Model' if field == 'ModelName' else field, ['All', *values],
            key=f"demo_{demo['run_id']}_{field}")
    return apply_filters(scored, selections)


def render_demo_dashboard(tenant, demo, scored):
    careers = demo['scenario'] == 'careers'
    frame = filter_demo_responses(demo, scored)
    st.caption('Measures reflect the saved model responses in this selected prompt sample. '
               'They do not measure graduate outcomes or research quality.')
    if frame.empty:
        st.info('No responses match these filters. Choose All in one or more filters.')
        return
    metrics = compute_scope_metrics(frame, owned_domains=tenant.domains)
    total = metrics['responses']
    columns = st.columns(4)
    columns[0].metric('Prompts in view', frame['PromptID'].nunique())
    columns[1].metric('Saved responses', total)
    columns[2].metric('Southampton mention rate', format_rate_with_denominator(metrics['mention_responses'], total))
    columns[3].metric('Citation coverage', format_rate_with_denominator(metrics['citation_responses'], total))
    st.caption(f"{frame['ModelName'].nunique()} models represented. Rates count responses, not unique prompts; "
               'the same prompt is answered by each selected model.')
    if careers:
        st.subheader('Careers and employability signals')
        detected = int((frame['Recommended'].fillna(False).astype(bool) & frame['visible_bool'].fillna(False).astype(bool)).sum())
        st.metric('Recommendation wording when Southampton is mentioned',
                  format_rate_with_denominator(detected, metrics['mention_responses'])
                  if metrics['mention_responses'] else 'No Southampton mentions in this view')
        st.caption('Existing wording rules detect recommendation language near Southampton. '
                   'Review the original responses below to judge context; this is not a graduate-employment metric.')
        dimensions = ('Market', 'Subject', 'Persona')
    else:
        st.subheader('Research visibility and evidence')
        st.metric('Citations in responses mentioning Southampton',
                  format_rate_with_denominator(metrics['citation_when_mentioned_count'], metrics['mention_responses'])
                  if metrics['mention_responses'] else 'No Southampton mentions in this view')
        st.caption('A citation is a detected source or link in the response. Its presence does not establish '
                   'that it supports every claim or refers specifically to Southampton.')
        dimensions = ('Subject', 'Category', 'Market')
    st.subheader('Compare models')
    st.dataframe(_breakdown(frame, 'ModelName', tenant.domains), hide_index=True)
    for dimension in dimensions:
        st.subheader(f'Mentions by {dimension.lower()}')
        table = _breakdown(frame, dimension, tenant.domains)
        chart = alt.Chart(table).mark_bar(color=MOORHOUSE_PURPLE, cornerRadiusEnd=4).encode(
            x=alt.X('Mention rate (%):Q', scale=alt.Scale(domain=[0, 100])),
            y=alt.Y(f'{dimension}:N', sort='-x', title=None),
            tooltip=[dimension, 'Southampton mentions', 'Responses', 'Mention rate (%)'])
        st.altair_chart(chart.properties(height=max(180, len(table) * 32)))
        st.dataframe(table, hide_index=True)
    render_demo_competitors(tenant, demo, frame, compact=True)
    with st.expander('How to read these measures'):
        st.write('Mention rate counts responses where the existing Southampton name rules detected a mention. '
                 'Citation coverage counts responses with detected citations. Each table includes the response '
                 'denominator. Filters apply to every metric, chart and response below. '
                 'Zero counts describe this selected sample only.')
    st.subheader('Inspect the captured responses')
    evidence_columns = [c for c in ('PromptID', 'SourceExcelRow', 'Market', 'Persona', 'Subject',
                        'Category', 'ModelName', 'Prompt', 'CompetitorsMentioned', 'ResponseText') if c in frame.columns]
    evidence = frame[evidence_columns].reset_index(drop=True)
    st.dataframe(evidence, hide_index=True)
    choice = st.selectbox('Read a full response', range(len(evidence)),
                         format_func=lambda i: f"{evidence.iloc[i]['PromptID']} · {evidence.iloc[i]['ModelName']}",
                         key=f"demo_evidence_{demo['run_id']}")
    st.write(evidence.iloc[choice]['Prompt'])
    st.text(evidence.iloc[choice]['ResponseText'])
    st.download_button('Download filtered demo evidence', evidence.to_csv(index=False).encode('utf-8'),
                       file_name=f"{demo['label'].replace(' ', '_')}_evidence.csv", mime='text/csv')
