from __future__ import annotations

import streamlit as st

from src.tenants import create_tenant_profile, list_tenants, load_tenant
from src.ui import (
    apply_moorhouse_theme,
    get_active_org_id,
    list_recent_org_ids,
    render_page_header,
    set_active_org_id,
    tenant_data_source_label,
)


st.set_page_config(page_title='Start', page_icon=':material/home:', layout='wide')
apply_moorhouse_theme()
render_page_header(
    'Start',
    'Select an organisation workspace or create a new profile',
    eyebrow='Workspace setup',
)

tenant_ids = list_tenants()
tenant_map: dict[str, str] = {}
for tenant_id in tenant_ids:
    tenant = load_tenant(tenant_id)
    source_label = tenant_data_source_label(tenant)
    tenant_map[tenant_id] = f"{tenant.display_name} ({tenant.org_id}) · {source_label}"

active_org_id = get_active_org_id()
if active_org_id and active_org_id in tenant_map:
    st.success(f"Active organisation: {tenant_map[active_org_id]}")

search = st.text_input('Find organization', placeholder='Type an organisation name, alias, or ID')
query = search.strip().lower()

filtered_ids: list[str] = []
for tenant_id in tenant_ids:
    tenant = load_tenant(tenant_id)
    haystack = ' '.join(
        [tenant.display_name, tenant.org_id, *tenant.aliases, *tenant.domains]
    ).lower()
    if not query or query in haystack:
        filtered_ids.append(tenant_id)

if filtered_ids:
    options = [tenant_map[tenant_id] for tenant_id in filtered_ids]
    default_index = 0
    if active_org_id and active_org_id in filtered_ids:
        default_index = filtered_ids.index(active_org_id)
    selected_label = st.selectbox('Available organizations', options=options, index=default_index)
    selected_org_id = next(
        tenant_id for tenant_id in filtered_ids if tenant_map[tenant_id] == selected_label
    )
    if st.button('Open workspace', type='primary'):
        set_active_org_id(selected_org_id)
        st.success(f"Workspace set to {tenant_map[selected_org_id]}")
        st.rerun()
else:
    st.info('No matching organizations were found. Create one below.')

recent_ids = [tenant_id for tenant_id in list_recent_org_ids() if tenant_id in tenant_map]
if recent_ids:
    st.markdown('### Recent workspaces')
    for tenant_id in recent_ids:
        tenant_label = tenant_map[tenant_id]
        if st.button(f'Use {tenant_label}', key=f'use_recent_{tenant_id}'):
            set_active_org_id(tenant_id)
            st.success(f"Workspace set to {tenant_label}")
            st.rerun()

st.markdown('---')
st.markdown('### Create new organization')
with st.form('create_org_form'):
    name = st.text_input('Organization name*', placeholder='e.g., Moorhouse')
    aliases_raw = st.text_input('Aliases (comma separated)', placeholder='Moorhouse Consulting, MH')
    domains_raw = st.text_input('Domains (comma separated)', placeholder='moorhouseconsulting.com')
    competitors_raw = st.text_area(
        'Competitors (optional, one per line)',
        placeholder='Competitor name | Alias one | Alias two',
        help='Use a vertical bar to add aliases that should map to the same competitor.',
    )
    prompts_path = st.text_input('Prompts file path (optional)', value='')
    results_path = st.text_input('Results file path (optional)', value='')
    submitted = st.form_submit_button('Create organization')

if submitted:
    try:
        competitors: dict[str, list[str]] = {}
        for line in competitors_raw.splitlines():
            values = [value.strip() for value in line.split('|') if value.strip()]
            if values:
                competitors[values[0]] = values[1:]
        tenant_id = create_tenant_profile(
            display_name=name,
            aliases=[value.strip() for value in aliases_raw.split(',') if value.strip()],
            domains=[value.strip() for value in domains_raw.split(',') if value.strip()],
            competitors=competitors,
            prompts_path=prompts_path,
            results_path=results_path,
        )
        set_active_org_id(tenant_id)
        created_tenant = load_tenant(tenant_id)
        st.success(f"Created and activated {created_tenant.display_name} ({created_tenant.org_id})")
        st.rerun()
    except Exception as exc:
        st.error(f'Unable to create organization: {exc}')
