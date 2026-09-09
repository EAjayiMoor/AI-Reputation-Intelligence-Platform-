from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from src.ingestion.validators import (
    PROMPT_REQUIRED_COLUMNS,
    RESULT_REQUIRED_COLUMNS,
    validate_required_columns,
    validate_result_columns,
)
from src.tenants import update_tenant_data_paths
from src.ui import (
    apply_moorhouse_theme,
    load_core_data,
    render_page_header,
    require_active_tenant,
    tenant_data_source_label,
)


def _read_uploaded_frame(uploaded_file) -> pd.DataFrame:
    suffix = Path(uploaded_file.name).suffix.lower()
    if suffix == '.csv':
        return pd.read_csv(uploaded_file)
    if suffix in {'.xlsx', '.xls'}:
        return pd.read_excel(uploaded_file)
    raise ValueError('Unsupported file type. Please upload CSV or XLSX.')


def _save_frame(frame: pd.DataFrame, tenant_id: str, prefix: str) -> str:
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    target_dir = Path('data') / 'tenants' / tenant_id
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f'{prefix}_{timestamp}.csv'
    frame.to_csv(target, index=False)
    return str(target).replace('\\', '/')


st.set_page_config(page_title='Data Onboarding', page_icon=':material/upload_file:', layout='wide')
apply_moorhouse_theme()
tenant = require_active_tenant()
data_source = tenant_data_source_label(tenant)

render_page_header(
    'Data Onboarding',
    'Upload and activate prompt/result files for the selected organisation workspace',
    eyebrow='Data setup',
)

st.caption(
    f'Active organization: {tenant.display_name} · Data source: {data_source} · '
    f'Current prompts: `{tenant.data_paths.prompts_path}` · Current results: `{tenant.data_paths.results_path}`'
)

st.info(
    'Upload prompt-bank and/or results files here. Files are stored under '
    '`data/tenants/<org_id>/` and tenant paths are updated automatically.'
)

with st.expander('Required columns', icon=':material/rule:'):
    st.markdown('**Prompt file required columns**')
    st.code(', '.join(PROMPT_REQUIRED_COLUMNS))
    st.markdown('**Results file required columns**')
    st.code(', '.join(RESULT_REQUIRED_COLUMNS))

prompt_upload = st.file_uploader(
    'Upload prompt file (CSV/XLSX)',
    type=['csv', 'xlsx', 'xls'],
    key='prompt_upload_file',
)
results_upload = st.file_uploader(
    'Upload results file (CSV/XLSX)',
    type=['csv', 'xlsx', 'xls'],
    key='results_upload_file',
)

if st.button('Validate and activate uploads', type='primary'):
    if prompt_upload is None and results_upload is None:
        st.error('Upload at least one file (prompt or results) before continuing.')
        st.stop()

    saved_prompt_path: str | None = None
    saved_results_path: str | None = None

    if prompt_upload is not None:
        try:
            prompt_df = _read_uploaded_frame(prompt_upload)
            prompt_validation = validate_required_columns(prompt_df, PROMPT_REQUIRED_COLUMNS)
            if not prompt_validation.valid:
                st.error(
                    'Prompt file is missing required columns: '
                    + ', '.join(prompt_validation.missing_columns)
                )
                st.stop()
            saved_prompt_path = _save_frame(prompt_df, tenant.org_id, 'prompts')
        except Exception as exc:
            st.error(f'Unable to process prompt file: {exc}')
            st.stop()

    if results_upload is not None:
        try:
            results_df = _read_uploaded_frame(results_upload)
            results_validation = validate_result_columns(results_df)
            if not results_validation.valid:
                st.error(
                    'Results file is missing required columns: '
                    + ', '.join(results_validation.missing_columns)
                )
                st.stop()
            saved_results_path = _save_frame(results_df, tenant.org_id, 'results')
        except Exception as exc:
            st.error(f'Unable to process results file: {exc}')
            st.stop()

    update_tenant_data_paths(
        org_id=tenant.org_id,
        prompts_path=saved_prompt_path,
        results_path=saved_results_path,
    )
    load_core_data.clear()

    st.success('Uploads validated and activated for this workspace.')
    if saved_prompt_path:
        st.caption(f'Prompt path updated to `{saved_prompt_path}`')
    if saved_results_path:
        st.caption(f'Results path updated to `{saved_results_path}`')
    st.info('Refresh analytics pages from the sidebar to view the new data.')
