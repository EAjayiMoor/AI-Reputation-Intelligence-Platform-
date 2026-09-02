from __future__ import annotations

import streamlit as st

from src.ui import apply_moorhouse_theme, render_page_header, require_active_tenant, tenant_data_source_label

st.set_page_config(
    page_title='AI Reputation Intelligence Platform',
    page_icon=':material/track_changes:',
    layout='wide',
)

apply_moorhouse_theme()
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
        <p>Use the Executive Dashboard page for the scorecard and chart-based summary. OpenRouter Execution is the operational capture page for generated prompt runs. Prompt Bank Explorer is the filterable prompt audit surface.</p>
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
    '- OpenRouter Execution: run generated prompts through OpenRouter and capture outputs'
)
