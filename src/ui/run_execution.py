import pandas as pd
import streamlit as st

from src.config import load_settings
from src.execution.openrouter_catalog import list_models
from src.execution.storage import load_openrouter_results
from src.runs.executor import execute_run, run_summary
from src.runs.locking import RunBusyError
from src.runs.store import RunStore
from src.ui.data import load_core_data
from src.ui.run_dates import run_timing_caption


def render_run_execution(tenant, run_id: str) -> None:
    store = RunStore()
    state = run_summary(store, tenant.org_id, run_id)
    settings = load_settings()
    simulated = state['mode'] == 'dry_run'
    st.subheader(state['name'])
    st.caption(run_timing_caption(state))
    st.caption(f"{'Simulated' if simulated else 'Live OpenRouter'} run · {state['display_status']} · "
               f"{state['prompt_count']} uploaded prompts")
    if simulated:
        st.info('Simulation creates labelled placeholder responses and makes no model API calls.')
    if state['active']:
        st.info('This run is being executed or updated by another session. Refresh to see saved progress.')
        if st.button('Refresh status'):
            st.rerun()
    elif state['display_status'] == 'Interrupted' or state.get('interrupted'):
        st.warning('The previous execution was interrupted. Saved responses are retained; unfinished requests can be resumed.')
        if state.get('current_request') and not simulated:
            st.caption('The last request may have reached the provider before interruption. Retrying it can incur another charge.')

    models_key = f'models_{run_id}'
    catalog_key = f'openrouter_catalog_{settings.openrouter_base_url}'
    frozen = bool(state['models'])
    configured = list(dict.fromkeys([*settings.openrouter_models,
                                    *tenant.model_assignment.labels_to_models.values()]))
    if not frozen and not state['active'] and not simulated:
        if st.button('Refresh OpenRouter model list', key=f'refresh_catalog_{run_id}'):
            try:
                st.session_state[catalog_key] = list_models(settings.openrouter_base_url,
                                                            api_key=settings.openrouter_api_key or '')
                st.session_state.pop(models_key, None)
            except (ValueError, OSError, KeyError, TypeError) as exc:
                st.error(f'Unable to refresh the model list: {exc}')
    options = (state['models'] if frozen else st.session_state.get(catalog_key)
               or sorted(set([*settings.openrouter_catalog_models, *configured])))
    preferred = [model for model in configured if model in options]
    selected_models = st.multiselect('Models to run', options=options,
        default=state['models'] if frozen else (preferred[:3] or options[:3]), key=models_key,
        disabled=frozen or state['active'], help='Each model receives every prompt in the uploaded file.')
    if frozen:
        st.caption('The model selection is fixed for this run. Create another run to compare a different set of models.')

    expected = state['prompt_count'] * len(selected_models)
    completed = state['completed_requests']
    pending = max(0, expected - completed)
    columns = st.columns(4)
    columns[0].metric('Planned requests', expected)
    columns[1].metric('Saved responses', completed)
    columns[2].metric('Unfinished requests', pending)
    columns[3].metric('Failed requests', state.get('failed_requests', 0))
    st.caption(f"{state['prompt_count']} prompts × {len(selected_models)} models = {expected} requests. "
               'Every uploaded prompt is included; saved responses are skipped on retry.')
    missing_key = not simulated and not settings.openrouter_api_key and pending > 0
    if missing_key:
        st.info('OPENROUTER_API_KEY is not configured. Add it to the app environment before starting live requests.')
    progress = st.progress(min(1.0, completed / expected) if expected else 0.0)
    progress_text = st.empty()
    if state['status'] == 'Complete':
        st.success('Run complete. Its saved responses are available in the dashboard.')
    needs_finalize = frozen and pending == 0 and state['status'] != 'Complete'
    label = ('Finalize saved run' if needs_finalize else 'Retry unfinished requests' if frozen and pending else
             'Simulate all prompts' if simulated else 'Run all prompts')
    if st.button(label, key=f'execute_run_{run_id}', type='primary',
                 disabled=state['active'] or missing_key or not selected_models or (pending == 0 and not needs_finalize)):
        def update(snapshot):
            total = snapshot['expected_requests']
            saved = snapshot['completed_requests']
            progress.progress(saved / total if total else 0.0)
            progress_text.caption(f"{saved}/{total} responses saved · {snapshot['failed_requests']} failed · {snapshot['status']}")
        try:
            execute_run(store, tenant, run_id, selected_models,
                api_key=settings.openrouter_api_key or '', base_url=settings.openrouter_base_url,
                timeout_seconds=settings.openrouter_timeout_seconds, app_name=settings.openrouter_app_name,
                app_url=settings.openrouter_app_url, on_progress=update)
        except (ValueError, OSError, RunBusyError) as exc:
            st.error(f'Unable to execute the run: {exc}')
        else:
            load_core_data.clear()
            st.rerun()

    if state.get('failures'):
        st.subheader('Requests to retry')
        st.dataframe(pd.DataFrame(state['failures']), hide_index=True)
    st.page_link('pages/04_Executive_Dashboard.py', label='View this run in the dashboard')
    paths = store.paths(tenant.org_id, run_id)
    responses = load_openrouter_results(paths['results'])
    if not responses.empty:
        st.subheader('Saved model responses')
        prompts = pd.read_csv(paths['prompts'], keep_default_na=False)
        view = responses.merge(prompts[['PromptID', 'Market', 'Persona', 'Subject', 'Category', 'Prompt']],
                               on='PromptID', how='left')
        st.dataframe(view[['PromptID', 'ModelName', 'Market', 'Persona', 'Subject', 'Category',
                           'Prompt', 'ResponseText', 'RunDate']], hide_index=True)
        st.download_button('Download responses as CSV', data=view.to_csv(index=False).encode('utf-8'),
                           file_name=f"{run_id}_responses.csv", mime='text/csv')
