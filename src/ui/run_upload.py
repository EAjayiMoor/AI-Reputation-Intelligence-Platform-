from pathlib import Path
from xml.etree.ElementTree import ParseError
from zipfile import BadZipFile

import streamlit as st
from openpyxl.utils.exceptions import InvalidFileException

from src.runs.store import RunStore
from src.runs.upload import INPUT_COLUMNS, list_sheets, prepare_prompts, read_upload
from src.ui.run_context import select_run


def render_upload_preview(content: bytes, filename: str, tenant) -> None:
    try:
        sheets = list_sheets(content, filename)
        sheet = st.selectbox('Workbook sheet', sheets) if len(sheets) > 1 else (sheets[0] if sheets else None)
        frame = read_upload(content, filename, sheet_name=sheet)
        upload = prepare_prompts(frame, organisation_name=tenant.display_name)
    except (ValueError, OSError, ImportError, BadZipFile, InvalidFileException, ParseError, KeyError) as exc:
        st.error(f'Unable to read the prompt file: {exc}')
        return

    prompts = upload.prompts
    st.subheader('Prompt preview')
    st.dataframe(prompts[INPUT_COLUMNS], hide_index=True)
    st.caption(f"{len(prompts)} prompt rows · {prompts['Market'].nunique()} markets · "
               f"{prompts['Persona'].nunique()} personas · {prompts['Subject'].nunique()} subjects · "
               f"{prompts['Category'].nunique()} categories")
    if not upload.valid:
        st.error('Correct the issues below in the spreadsheet, then upload it again.')
        st.dataframe(upload.issues, hide_index=True)
        return

    name = st.text_input('Run name', value=Path(filename).stem)
    mode_label = st.radio('Run mode', ['Live', 'Simulated'], horizontal=True,
                          help='Live runs will call the selected models when execution starts. Simulated runs are for checking the workflow.')
    st.info(f'All {len(prompts)} prompts will be included. Model selection happens on the Execution page.')
    if st.button('Create run', type='primary', disabled=not name.strip()):
        try:
            run = RunStore().create(tenant_id=tenant.org_id, name=name, prompts=prompts,
                                    source_name=filename, source_bytes=content, source_sheet=sheet,
                                    mode='live' if mode_label == 'Live' else 'dry_run')
        except (ValueError, OSError) as exc:
            st.error(f'Unable to save the run: {exc}')
            return
        select_run(tenant.org_id, run['run_id'])
        st.session_state['created_run_notice'] = f"Created {run['name']} with {len(prompts)} prompts."
        st.rerun()
