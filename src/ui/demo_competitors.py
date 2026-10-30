"""Auditable competitor comparisons derived from saved demo response text."""
import altair as alt
import pandas as pd
import streamlit as st

from src.analysis import format_rate_with_denominator
from src.analysis.response_parser import UNIVERSITY_ALIASES
from src.scoring import institution_mention_index, institution_mentions_by_model
from src.ui.moorhouse import MOORHOUSE_PURPLE


def _eligible(frame):
    if 'CompetitorPromptEligible' in frame:
        return frame[frame['CompetitorPromptEligible'].fillna(False).astype(bool)]
    return frame


def render_demo_competitors(tenant, demo, frame, *, compact=False):
    frame = frame.copy()
    if 'CompetitorsMentioned' not in frame:
        frame['CompetitorsMentioned'] = ''
    eligible = _eligible(frame)
    st.subheader('Competitor presence')
    st.caption(f'{len(eligible)} neutral-prompt responses from {eligible["PromptID"].nunique()} prompts. '
               'Prompts naming Southampton or a recognised competitor are excluded. '
               'Each recognised university counts once per response, regardless of repeated mentions.')
    st.caption('Names are matched against the recognised university list using full names and approved aliases. '
               'The list is not exhaustive; city names alone are not counted. These are model mention rates, '
               'not university quality rankings.')
    if eligible.empty:
        st.info('No neutral-prompt responses match these filters. Broaden the filters to compare competitors.')
        return
    comparison = institution_mention_index(eligible, competitor_limit=10)
    competitors = comparison[comparison['InstitutionType'] == 'Competitor']
    if competitors.empty:
        st.info('No universities from the recognised university list were detected in these responses. '
                'This does not establish that no other universities were mentioned; inspect the original answers.')
    else:
        top = competitors.iloc[0]
        columns = st.columns(2)
        columns[0].metric('Top recognised competitor', top['Institution'])
        columns[1].metric('Competitor response mention rate',
                          format_rate_with_denominator(int(top['Mentions']), len(eligible)))
    comparison = comparison.copy()
    comparison['Responses evaluated'] = len(eligible)
    comparison['Mention rate (%)'] = comparison['Mentions'].div(len(eligible)).mul(100).round(1)
    table = comparison[['Institution', 'Mentions', 'Responses evaluated', 'Mention rate (%)']]
    st.dataframe(table, hide_index=True)
    if compact:
        if st.button('Explore competitor analysis', key=f"demo_competitors_{demo['run_id']}"):
            st.switch_page('pages/08_Competitor_Analysis.py')
        return
    chart = alt.Chart(table).mark_bar(color=MOORHOUSE_PURPLE, cornerRadiusEnd=4).encode(
        x=alt.X('Mention rate (%):Q', scale=alt.Scale(domain=[0, 100])),
        y=alt.Y('Institution:N', sort='-x', title=None),
        tooltip=['Institution', 'Mentions', 'Responses evaluated', 'Mention rate (%)'])
    st.altair_chart(chart.properties(height=max(220, len(table) * 32)))
    st.subheader('Competitor mentions by model')
    models = institution_mentions_by_model(eligible, competitor_limit=10)
    st.dataframe(models[['Institution', 'ModelName', 'Mentions', 'EligibleResponses', 'MentionRate']], hide_index=True,
                 column_config={'EligibleResponses': 'Responses evaluated', 'MentionRate': 'Mention rate (%)'})
    st.download_button('Download competitor model comparison', models.to_csv(index=False).encode('utf-8'),
                       file_name=f"{demo['scenario']}_competitors_by_model.csv", mime='text/csv')
    dimensions = ('Subject', 'Market', 'Persona' if demo['scenario'] == 'careers' else 'Category')
    for dimension in dimensions:
        rows = []
        for value, group in eligible.groupby(dimension, dropna=False):
            group_comparison = institution_mention_index(group, competitor_limit=1)
            for _, row in group_comparison.iterrows():
                rows.append({dimension: value, 'Institution': row['Institution'],
                             'Mentions': int(row['Mentions']), 'Responses evaluated': len(group),
                             'Mention rate (%)': round(row['Mentions'] / len(group) * 100, 1)})
        st.subheader(f'Leading competitor and Southampton by {dimension.lower()}')
        st.dataframe(pd.DataFrame(rows), hide_index=True)
    with st.expander('Recognised university list'):
        st.write(sorted(UNIVERSITY_ALIASES))
        st.caption('This catalogue covers recognised UK university names and approved aliases. '
                   'An institution outside this list will not be included in the comparison.')
    st.subheader('Response evidence for competitor mentions')
    institutions = ['All', *table['Institution'].tolist()]
    selected = st.selectbox('University evidence', institutions, key=f"competitor_evidence_{demo['run_id']}")
    evidence = eligible
    if selected == tenant.display_name:
        evidence = evidence[evidence['visible_bool'].fillna(False).astype(bool)]
    elif selected != 'All':
        evidence = evidence[evidence['CompetitorsMentioned'].fillna('').map(
            lambda text: selected in [name.strip() for name in str(text).split(',')])]
    columns = [c for c in ('PromptID', 'SourceExcelRow', 'Market', 'Persona', 'Subject', 'Category',
                          'ModelName', 'Prompt', 'CompetitorsMentioned', 'ResponseText') if c in evidence]
    st.dataframe(evidence[columns], hide_index=True)
    st.download_button('Download competitor response evidence', evidence[columns].to_csv(index=False).encode('utf-8'),
                       file_name=f"{demo['scenario']}_competitor_evidence.csv", mime='text/csv')
