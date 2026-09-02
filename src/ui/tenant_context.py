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
        return tenant

    st.warning('Select or create an organisation from the Start page before using this view.')
    st.info('Open `Start` from the sidebar to choose your active workspace.')
    st.stop()


def tenant_data_source_label(tenant: TenantConfig) -> str:
    return 'Demo' if tenant.org_id.startswith('demo') else 'Live'


def render_empty_state_guidance(tenant: TenantConfig, *, area: str = 'this page') -> None:
    source = tenant_data_source_label(tenant)
    if source == 'Live':
        st.warning(f'No live data is available for {tenant.display_name} in {area}.')
        st.info(
            'Next steps: (1) upload/import a prompt bank for this organisation, '
            '(2) run prompt execution capture, and (3) refresh this page.'
        )
    else:
        st.warning(f'No demo data is available for {tenant.display_name} in {area}.')
