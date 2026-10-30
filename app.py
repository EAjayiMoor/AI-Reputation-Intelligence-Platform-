from __future__ import annotations

import streamlit as st

from src.ui import apply_moorhouse_theme, render_page_header, require_active_tenant, tenant_data_source_label, get_active_org_id

st.set_page_config(
    page_title='AI Reputation Intelligence Platform',
    page_icon=':material/track_changes:',
    layout='wide',
)

apply_moorhouse_theme()
if not get_active_org_id():
    st.switch_page('pages/01_Start.py')
tenant = require_active_tenant()
data_source = tenant_data_source_label(tenant)
render_page_header(
    'AI reputation intelligence platform',
    f'{tenant.display_name} visibility and reputation analytics',
    eyebrow='Overview',
)
st.caption(f'Active organization: {tenant.display_name} · Data source: {data_source}')

st.markdown(
    """
    <div class='mh-callout'>
    <p>Use the Executive Dashboard page for the scorecard and chart-based summary. Visibility Analysis and Topic and Persona Diagnostics explain presence by segment, while Competitor Analysis shows competitive pressure. Upload prepared prompts through Data Onboarding, then use Execution for OpenRouter runs. Prompt Bank Explorer is the filterable prompt audit surface.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('### App purpose')
st.markdown(
    f'This Streamlit PoC supports a consultant-led AI visibility audit for {tenant.display_name} across market, subject, persona, expertise, and platform views.',
)

st.markdown('### Recommended entry points')
st.markdown(
    '- Executive Dashboard: headline summary and benchmark charts\n'
    '- Prompt Bank Explorer: inspect prompt coverage and export filtered prompt sets\n'
    '- Topic and Persona Diagnostics: find segment strengths, gaps and supporting response evidence\n'
    '- Recommendations: connect measured gaps to owned actions, evidence and rerun tracking\n'
    '- Data Onboarding: upload a prepared Excel or CSV prompt sheet and create a named run\n'
    '- Run History: reopen, rename, archive, restore and download saved runs\n'
    '- Execution: run every uploaded prompt through selected OpenRouter models and retry unfinished requests'
)
