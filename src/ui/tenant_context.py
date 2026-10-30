from __future__ import annotations

import streamlit as st

from src.tenants import TenantConfig, load_tenant


ACTIVE_ORG_KEY = 'active_org_id'
RECENT_ORGS_KEY = 'recent_org_ids'


def get_active_org_id() -> str | None:
    value = st.session_state.get(ACTIVE_ORG_KEY)
    if value is None:
        return None
    text = str(value).strip().lower()
    return text or None


def set_active_org_id(org_id: str) -> None:
    normalised = org_id.strip().lower()
    st.session_state[ACTIVE_ORG_KEY] = normalised
    recent = list(st.session_state.get(RECENT_ORGS_KEY, []))
    recent = [value for value in recent if str(value).strip().lower() != normalised]
    recent.insert(0, normalised)
    st.session_state[RECENT_ORGS_KEY] = recent[:6]


def list_recent_org_ids() -> list[str]:
    values = st.session_state.get(RECENT_ORGS_KEY, [])
    return [str(value).strip().lower() for value in values if str(value).strip()]


def get_active_tenant() -> TenantConfig | None:
    org_id = get_active_org_id()
    if not org_id:
        return None
    try:
        return load_tenant(org_id)
    except Exception:
        return None


def require_active_tenant() -> TenantConfig:
    tenant = get_active_tenant()
    if tenant is not None:
        from src.ui.run_context import render_run_selector
        return render_run_selector(tenant)

    st.warning('Select or create an organisation from the Start page before using this view.')
    st.info('Open `Start` from the sidebar to choose your active workspace.')
    st.stop()


def tenant_data_source_label(tenant: TenantConfig) -> str:
    from src.runs.store import RunStore
    from src.ui.run_context import selected_run_id
    run_id = selected_run_id(tenant.org_id)
    if not run_id:
        return 'Saved demo'
    from src.runs.executor import run_summary
    run = run_summary(RunStore(), tenant.org_id, run_id)
    mode = 'Simulated' if run['mode'] == 'dry_run' else 'Live'
    from src.ui.run_dates import dated_run_name
    return f"{mode}: {dated_run_name(run)} ({run['display_status']})"


def render_empty_state_guidance(tenant: TenantConfig, *, area: str = 'this page') -> None:
    from src.ui.run_context import selected_run_id
    if selected_run_id(tenant.org_id):
        st.info(f'The selected run has no captured responses for {area} yet. Its uploaded prompts are available in Prompt Bank Explorer.')
    else:
        st.warning(f'No saved demo data is available for {tenant.display_name} in {area}.')
