from __future__ import annotations

import streamlit as st

from src.ui import apply_moorhouse_theme, render_page_header, require_active_tenant
from src.ui.run_context import selected_run_id
from src.ui.run_execution import render_run_execution


st.set_page_config(page_title='Model execution', page_icon=':material/play_circle:', layout='wide')
apply_moorhouse_theme()
tenant = require_active_tenant()
render_page_header('Model execution', 'Run uploaded prompts through selected OpenRouter models', eyebrow='Execution control')
run_id = selected_run_id(tenant.org_id)
if not run_id:
    st.info('Saved demo data is read-only. Create a run from a prepared Excel file to execute fresh prompts.')
    st.page_link('pages/02_Data_Onboarding.py', label='Upload prepared prompts')
else:
    render_run_execution(tenant, run_id)
