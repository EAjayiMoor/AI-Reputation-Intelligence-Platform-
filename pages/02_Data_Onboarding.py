from __future__ import annotations

import streamlit as st

from src.runs.upload import INPUT_COLUMNS
from src.ui import apply_moorhouse_theme, render_page_header, require_active_tenant
from src.ui.run_upload import render_upload_preview


st.set_page_config(page_title='Data Onboarding', page_icon=':material/upload_file:', layout='wide')
apply_moorhouse_theme()
tenant = require_active_tenant()
render_page_header('Data Onboarding', 'Upload prepared prompts and create a live or simulated run', eyebrow='Data setup')
st.caption(f'Active organisation: {tenant.display_name}')
notice = st.session_state.pop('created_run_notice', None)
if notice:
    st.success(notice)
st.info('Upload your prepared sheet, review every row, then create a named run. Each run keeps its own inputs and responses.')
st.markdown('**Required headings:** ' + ', '.join(INPUT_COLUMNS))
st.download_button('Download blank CSV template', data=','.join(INPUT_COLUMNS) + '\n',
                   file_name='prompt_input_template.csv', mime='text/csv')
prompt_upload = st.file_uploader('Upload prompt file (Excel or CSV)', type=['xlsx', 'csv'], key='prompt_upload_file')
if prompt_upload is not None:
    render_upload_preview(prompt_upload.getvalue(), prompt_upload.name, tenant)
st.page_link('pages/05_Prompt_Bank_Explorer.py', label='Inspect the selected prompt bank')
