from __future__ import annotations

import pandas as pd
import streamlit as st
from io import BytesIO
from zipfile import ZipFile

from src.runs.executor import run_summary
from src.runs.history import build_run_archive
from src.runs.locking import RunBusyError
from src.runs.store import RunStore
from src.ui import apply_moorhouse_theme, render_page_header, require_active_tenant
from src.ui.run_context import select_run, selected_run_id
from src.ui.run_dates import dated_run_name, format_run_timestamp, run_timing_caption


st.set_page_config(page_title='Run history', page_icon=':material/history:', layout='wide')
apply_moorhouse_theme()
tenant = require_active_tenant()
store = RunStore()
render_page_header('Run history', 'Revisit, download and organise runs for this workspace', eyebrow='Saved work')
st.markdown(f'**Saved demo — {tenant.display_name}** · Protected fallback')
if st.button('Use saved demo', key='history_saved_demo'):
    select_run(tenant.org_id, None)
    st.switch_page('pages/04_Executive_Dashboard.py')
include_archived = st.toggle('Include archived runs', key=f'history_archived_{tenant.org_id}')
runs = store.list_runs(tenant.org_id, include_archived=include_archived)
if not runs:
    st.info('No runs match this view. Upload a prepared prompt sheet to create one.')
    st.stop()
states = {run['run_id']: run_summary(store, tenant.org_id, run['run_id']) for run in runs}
st.caption('Dates and times are shown in UK time (GMT/BST). Newest runs appear first.')
st.dataframe(pd.DataFrame([{
    'Name': state['name'], 'Status': state['display_status'],
    'Mode': 'Simulated' if state['mode'] == 'dry_run' else 'Live',
    'Prompts': state['prompt_count'], 'Saved responses': state['completed_requests'],
    'Planned requests': state['expected_requests'], 'Models': ', '.join(state['models']),
    'Created': format_run_timestamp(state['created_at']),
    'Started': format_run_timestamp(state.get('started_at')),
    'Last execution finished': format_run_timestamp(state.get('finished_at')),
    'Last updated': format_run_timestamp(state.get('updated_at')),
    'Archived': state['archived'], 'Run ID': state['run_id'],
} for state in states.values()]), hide_index=True)
picker = f'history_run_{tenant.org_id}'
if st.session_state.get(picker) not in states:
    st.session_state[picker] = next(iter(states))
run_id = st.selectbox('Run details', options=list(states), key=picker,
                       format_func=lambda key: f"{dated_run_name(states[key])} · {key[-8:]}")
state = states[run_id]
st.caption(run_timing_caption(state))
active = state['active']
if active:
    st.info('Another session is updating this run. Rename, archive and downloads are available after it finishes.')
new_name = st.text_input('Run name', value=state['name'], key=f'rename_{run_id}', disabled=active)
if st.button('Save name', key=f'save_name_{run_id}', disabled=active or not new_name.strip()):
    try:
        store.update_details(tenant.org_id, run_id, name=new_name)
    except (RunBusyError, OSError, ValueError) as exc:
        st.error(str(exc))
    else:
        st.rerun()
if st.button('Open run', key=f'open_{run_id}', disabled=state['archived']):
    select_run(tenant.org_id, run_id)
    st.switch_page('pages/04_Executive_Dashboard.py')
action = 'restore' if state['archived'] else 'archive'
if st.button('Restore run' if state['archived'] else 'Archive run', key=f'{action}_{run_id}', disabled=active):
    try:
        store.update_details(tenant.org_id, run_id, archived=not state['archived'])
    except (RunBusyError, OSError, ValueError) as exc:
        st.error(str(exc))
    else:
        if action == 'archive' and selected_run_id(tenant.org_id) == run_id:
            select_run(tenant.org_id, None)
        st.rerun()
if not active:
    try:
        bundle = build_run_archive(store, tenant.org_id, run_id)
    except (RunBusyError, OSError) as exc:
        st.info(f'The run could not be downloaded yet: {exc}')
    else:
        prefix = f"{'simulated' if state['mode'] == 'dry_run' else 'live'}_{run_id}"
        st.download_button('Download run bundle (.zip)', bundle, file_name=f'{prefix}.zip', mime='application/zip')
        with ZipFile(BytesIO(bundle)) as snapshot:
            st.download_button('Download original upload', snapshot.read(f"input{state['source_suffix']}"),
                               file_name=f"{prefix}_input{state['source_suffix']}")
            st.download_button('Download responses (CSV)', snapshot.read('results.csv'),
                               file_name=f'{prefix}_responses.csv', mime='text/csv')
st.caption('Archiving hides a run from the dashboard selector. Its inputs and results remain saved and can be restored.')
