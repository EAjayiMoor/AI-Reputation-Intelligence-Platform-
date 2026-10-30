"""Session-local dataset selection shared by every data page."""
import streamlit as st
import pandas as pd

from src.runs.selection import resolve_run_tenant
from src.runs.store import RunStore
from src.runs.executor import run_summary
from src.analysis import format_rate_with_denominator
from src.ui.run_dates import dated_run_name, format_run_timestamp

SELECTION_KEY = 'selected_run_ids'


def selected_run_id(org_id: str) -> str | None:
    return st.session_state.get(SELECTION_KEY, {}).get(org_id)


def select_run(org_id: str, run_id: str | None) -> None:
    selections = dict(st.session_state.get(SELECTION_KEY, {}))
    selections[org_id] = run_id
    st.session_state[SELECTION_KEY] = selections


def render_run_selector(tenant):
    store = RunStore()
    runs = store.list_runs(tenant.org_id)
    lookup = {run['run_id']: run for run in runs}
    current = selected_run_id(tenant.org_id)
    if current and current not in lookup:
        select_run(tenant.org_id, None)
        current = None
        st.sidebar.warning('The previous run is unavailable. Showing the saved demo.')
    widget_key = f'_run_picker_{tenant.org_id}'
    # Durable selection lives outside widget state so navigation preserves it.
    st.session_state[widget_key] = current

    def changed():
        select_run(tenant.org_id, st.session_state[widget_key])

    def label(run_id):
        if run_id is None:
            return 'Saved demo'
        run = lookup[run_id]
        mode = 'Simulated' if run['mode'] == 'dry_run' else 'Live'
        return f"{mode}: {dated_run_name(run)} · {run['status']} · {run['run_id'][-8:]}"

    st.sidebar.selectbox('Data run', options=[None, *lookup], format_func=label,
                         key=widget_key, on_change=changed)
    if current:
        run = lookup[current]
        st.sidebar.caption(f"{run['prompt_count']} prompts · Created {format_run_timestamp(run['created_at'])}")
        if run['mode'] == 'dry_run':
            st.warning('Simulated run selected. Its responses are not live model evidence.')
    effective = resolve_run_tenant(tenant, current, store=store)
    if current:
        state = run_summary(store, tenant.org_id, current)
        mode = 'Simulated' if state['mode'] == 'dry_run' else 'Live'
        expected = state['expected_requests']
        saved = state['completed_requests']
        coverage = (f"Coverage {format_rate_with_denominator(saved, expected)} saved responses"
                    if expected else f'{saved} saved responses · Models not selected yet')
        st.caption(f"{mode}: {dated_run_name(state)} · {state['display_status']} · {coverage}")
        if state['display_status'] in {'Partial', 'Failed', 'Interrupted', 'Running'}:
            st.info('This run has unfinished requests. Analysis uses the responses saved so far; resume it from Execution.')
    else:
        try:
            prompts = pd.read_csv(tenant.data_paths.prompts_path)
            results = pd.read_csv(tenant.data_paths.results_path)
        except (OSError, ValueError):
            # Missing baseline files must not prevent onboarding a fresh run.
            st.caption(f'Saved demo: {tenant.display_name} · No readable saved snapshot available')
        else:
            models = results['ModelName'].nunique() if 'ModelName' in results else 0
            st.caption(f'Saved demo: {tenant.display_name} · Saved snapshot · {len(prompts):,} prompts · '
                       f'{len(results):,} captured responses · {models} models represented')
    return effective
