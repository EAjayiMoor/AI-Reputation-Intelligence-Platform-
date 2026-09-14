from __future__ import annotations

from datetime import datetime

import streamlit as st

from src.analysis import compute_scope_metrics, split_scope_frames
from src.export.microsite import build_microsite_archive, default_microsite_paths, missing_microsite_assets
from src.export.rendered_microsite import build_rendered_microsite_archive
from src.ui import (
    apply_filters,
    apply_moorhouse_theme,
    apply_prompt_mention_mode_filter,
    apply_prompt_scope_filter,
    load_core_data,
    render_empty_state_guidance,
    render_page_header,
    render_prompt_scope_selector,
    render_sidebar_filters,
    require_active_tenant,
    tenant_data_source_label,
)


st.set_page_config(page_title='Microsite export', page_icon=':material/language:', layout='wide')
apply_moorhouse_theme()
tenant = require_active_tenant()
data_source = tenant_data_source_label(tenant)
render_page_header('Microsite export', 'Download a client-ready static microsite pack', eyebrow='Export')
st.caption(f'Active organization: {tenant.display_name} | Data source: {data_source}')

st.info(
    'This export is UI-faithful and read-only: charts, layouts, and styling are preserved as captured visuals. '
    'Interactive filters are not active in the downloaded copy.'
)

paths = default_microsite_paths()
missing_assets = missing_microsite_assets()

st.markdown(f"- Microsite HTML: `{paths['html']}`")
st.markdown(f"- Snapshot assets: `{paths['snapshots_dir']}`")

if missing_assets:
    st.warning('Snapshot microsite assets are missing. You can still use the rendered microsite export below.')
    st.code(
        'python scripts/capture_streamlit_pages.py\n'
        'python scripts/build_screenshot_html.py',
        language='bash',
    )
    for missing_path in missing_assets:
        st.caption(f'Missing: {missing_path}')
else:
    archive_bytes = build_microsite_archive()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'{tenant.org_id}_microsite_export_{timestamp}.zip'

    st.success('Snapshot microsite pack is ready to download.')
    st.download_button(
        label='Download snapshot microsite (.zip)',
        data=archive_bytes,
        file_name=filename,
        mime='application/zip',
    )

st.divider()
st.subheader('Rendered microsite export (pro)')
st.caption('Generates a polished static report with real text, structured cards, charts, and tables.')

prompt_scope = render_prompt_scope_selector(key='microsite_scope')
try:
    _, _, scored_df = load_core_data(org_id=tenant.org_id)
except Exception as exc:
    st.error(f'Unable to load captured data: {exc}')
    st.stop()

scored_df = apply_prompt_scope_filter(scored_df, scope=prompt_scope)
filters = render_sidebar_filters(scored_df, key_prefix='microsite_export')
mention_mode = str(filters.get('PromptMentionType', 'All'))
base_filters = {column: value for column, value in filters.items() if column != 'PromptMentionType'}
filtered_scope = apply_filters(scored_df, base_filters)
filtered = apply_prompt_mention_mode_filter(filtered_scope, mention_mode)

if filtered.empty:
    render_empty_state_guidance(tenant, area='Microsite export')
    st.stop()

scope_frames = split_scope_frames(filtered_scope)
st.caption('Rendered report standard: Coverage -> Presence -> Proof -> Pressure -> Priority moves.')
scope_cols = st.columns(3)
for scope_col, scope_frame in zip(scope_cols, scope_frames):
    scope_metrics = compute_scope_metrics(scope_frame.frame, owned_domains=tenant.domains)
    scope_col.metric(f'{scope_frame.label} responses', int(scope_metrics['responses']))
    scope_col.caption(
        f"Presence {float(scope_metrics['presence_rate_response']):.1f}% | "
        f"Citation {float(scope_metrics['citation_coverage']):.1f}%"
    )

pro_archive = build_rendered_microsite_archive(
    scored_df=filtered,
    scope_df=filtered_scope,
    organisation_name=tenant.display_name,
    org_id=tenant.org_id,
    prompt_scope=prompt_scope,
    mention_mode=mention_mode,
    filters=filters,
    owned_domains=tenant.domains,
    organisation_aliases=tenant.aliases,
    competitor_aliases=tenant.competitors.aliases_by_name or None,
)
pro_filename = f'{tenant.org_id}_rendered_microsite_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip'

st.success('Rendered microsite pack is ready to download.')
st.download_button(
    label='Download rendered microsite (pro) (.zip)',
    data=pro_archive,
    file_name=pro_filename,
    mime='application/zip',
)
