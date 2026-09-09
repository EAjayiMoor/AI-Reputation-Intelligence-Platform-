from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.config import load_settings
from src.execution import (
    AzurePromptGenerator,
    AzurePromptGeneratorConfig,
    append_generated_prompts_to_bank,
    generated_prompt_subset,
    load_openrouter_results,
    run_model_sweep,
)
from src.ui import (
    apply_moorhouse_theme,
    load_core_data,
    render_page_header,
    require_active_tenant,
    tenant_data_source_label,
)

PROMPT_BANK_HEADERS = [
    'PromptID',
    'Organisation',
    'Market',
    'Persona',
    'Subject',
    'ExpertiseArea',
    'Intent',
    'Platform',
    'Prompt',
    'PromptSource',
    'PersonaTemplateID',
    'GenerationMethod',
]


def _load_prompt_bank_frame(path: str | Path) -> pd.DataFrame:
    file_path = Path(path)
    if not file_path.exists() or file_path.stat().st_size == 0:
        return pd.DataFrame(columns=PROMPT_BANK_HEADERS)
    try:
        return pd.read_csv(file_path)
    except Exception:
        return pd.DataFrame(columns=PROMPT_BANK_HEADERS)


st.set_page_config(page_title='Model execution', page_icon=':material/play_circle:', layout='wide')
apply_moorhouse_theme()
tenant = require_active_tenant()
data_source = tenant_data_source_label(tenant)
RESULTS_PATH = tenant.data_paths.results_path
PROMPTS_PATH = tenant.data_paths.prompts_path
render_page_header(
    'Model execution',
    'Generate prompts with Azure OpenAI from your own request, then run generated prompts through selected models',
    eyebrow='Execution control',
)

settings = load_settings()
provider_slug = settings.provider_slug
provider_label = settings.provider_label
existing = load_openrouter_results(RESULTS_PATH)

prompt_bank_df = _load_prompt_bank_frame(PROMPTS_PATH)
try:
    prompts_df, _, _ = load_core_data(org_id=tenant.org_id)
except Exception:
    prompts_df = prompt_bank_df.copy()

if prompts_df.empty:
    st.info('No prompt bank rows are loaded yet. You can generate prompts below without uploading a file first.')

actual_models = sorted(existing['ModelName'].dropna().astype(str).unique())
assigned_models = sorted(set(tenant.model_assignment.labels_to_models.values()))
configured_models = list(settings.default_execution_models())
catalog_models = list(settings.openrouter_catalog_models)
available_models = sorted(set(catalog_models + actual_models + assigned_models + configured_models))
default_models = [model for model in configured_models if model in available_models] or catalog_models[:6]

st.subheader('Generate prompts with Azure OpenAI')
st.caption('Use free text to generate prompt rows with Azure only. OpenRouter model selection is used later in the execution section.')

source_df = prompts_df if not prompts_df.empty else prompt_bank_df
market_options = sorted(source_df['Market'].dropna().astype(str).unique()) if 'Market' in source_df.columns else []
persona_options = sorted(source_df['Persona'].dropna().astype(str).unique()) if 'Persona' in source_df.columns else []
subject_options = sorted(source_df['Subject'].dropna().astype(str).unique()) if 'Subject' in source_df.columns else []
intent_options = sorted(source_df['Intent'].dropna().astype(str).unique()) if 'Intent' in source_df.columns else []

with st.container(border=True):
    generation_request = st.text_area(
        'What prompts should be generated?',
        placeholder='Example: Generate prompts for professionals comparing AI governance platforms, implementation effort, compliance risk, and ROI.',
        height=110,
    )
    target_context = st.text_input(
        'Target organisation/context (optional)',
        value=tenant.display_name,
        placeholder='Example: B2B SaaS procurement in EMEA, healthcare diagnostics market, or consumer fintech in LATAM',
    )

    g1, g2 = st.columns([1, 1])
    with g1:
        generation_count = int(st.number_input('Prompt count', min_value=1, max_value=200, value=20, step=1))
        generation_dry_run = st.toggle('Generation dry run (no Azure API call)', value=True)
        show_azure_response = st.toggle('Show Azure API response payload', value=False)
        use_taxonomy_hints = st.toggle('Use existing market/persona/subject/intent hints', value=False)
        selected_markets = st.multiselect(
            'Markets (optional)',
            options=market_options,
            default=[],
            disabled=not use_taxonomy_hints,
        )
        selected_personas = st.multiselect(
            'Personas (optional)',
            options=persona_options,
            default=[],
            disabled=not use_taxonomy_hints,
        )
    with g2:
        selected_subjects = st.multiselect(
            'Subjects (optional)',
            options=subject_options,
            default=[],
            disabled=not use_taxonomy_hints,
        )
        selected_intents = st.multiselect(
            'Intents (optional)',
            options=intent_options,
            default=[],
            disabled=not use_taxonomy_hints,
        )
        additional_brief = st.text_area(
            'Additional constraints (optional)',
            placeholder='Optional: exclude pricing prompts, focus on enterprise buyers, include security and deployment constraints.',
            height=90,
        )

    azure_deployment = settings.prompt_generation_model()
    st.caption(
        f'Azure endpoint: {settings.azure_foundry_endpoint} | deployment: {azure_deployment} | '
        f'api-version: {settings.azure_foundry_api_version}'
    )

    generate_button = st.button('Generate prompts and append to prompt bank', type='secondary')

if generate_button:
    if not generation_request.strip():
        st.error('Please enter what prompts should be generated before running Azure generation.')
        st.stop()

    azure_key = settings.azure_api_key
    if not generation_dry_run and not azure_key:
        st.error('AZURE_OPENAI_API_KEY is not set. Add it to your .env before live generation.')
        st.stop()
    if not settings.azure_foundry_endpoint:
        st.error('AZURE_FOUNDRY_ENDPOINT is not set. Add it to your .env before generation.')
        st.stop()
    if not azure_deployment:
        st.error('AZURE_FOUNDRY_MODELS is empty. Add your Azure deployment name before generation.')
        st.stop()

    generator = AzurePromptGenerator(
        AzurePromptGeneratorConfig(
            api_key=azure_key or 'dry_run_key',
            endpoint=settings.azure_foundry_endpoint,
            deployment_name=azure_deployment,
            api_version=settings.azure_foundry_api_version,
            timeout_seconds=settings.azure_foundry_timeout_seconds,
        )
    )

    organisation_context = target_context.strip() or tenant.display_name
    full_brief = generation_request.strip()
    if additional_brief.strip():
        full_brief = f'{full_brief}\\n\\nConstraints: {additional_brief.strip()}'

    try:
        trace = generator.generate_prompts_with_trace(
            organisation_name=organisation_context,
            prompt_count=generation_count,
            markets=selected_markets if use_taxonomy_hints else [],
            personas=selected_personas if use_taxonomy_hints else [],
            subjects=selected_subjects if use_taxonomy_hints else [],
            intents=selected_intents if use_taxonomy_hints else [],
            additional_brief=full_brief,
            dry_run=generation_dry_run,
        )
        generated_rows = trace.rows
    except Exception as exc:
        st.error(f'Azure prompt generation failed: {exc}')
        st.stop()

    if not generated_rows:
        st.warning('Azure generation returned no prompts to append.')
    else:
        prompt_bank_path = Path(PROMPTS_PATH)
        before_count = len(_load_prompt_bank_frame(prompt_bank_path))
        try:
            inserted = append_generated_prompts_to_bank(
                prompts_path=prompt_bank_path,
                organisation_name=target_context.strip() or tenant.display_name,
                rows=generated_rows,
                platform='OpenRouter',
            )
        except Exception as exc:
            st.error(f'Failed to append generated prompts: {exc}')
            st.stop()

        after_frame = _load_prompt_bank_frame(prompt_bank_path)
        after_count = len(after_frame)
        gen_ids: list[str] = []
        if 'PromptID' in after_frame.columns:
            gen_ids = after_frame['PromptID'].fillna('').astype(str)
            gen_ids = [value for value in gen_ids if value.startswith('GEN-')]
        recent_ids = ', '.join(gen_ids[-min(5, len(gen_ids)):]) if gen_ids else 'none yet'

        st.cache_data.clear()
        st.success(f'Added {inserted} generated prompts to {PROMPTS_PATH}.')
        st.info(
            f'Prompt bank rows before: {before_count:,} | after: {after_count:,} | '
            f'latest GEN IDs: {recent_ids}'
        )
        preview_rows = pd.DataFrame(generated_rows)
        st.markdown('**Generated Prompt Preview**')
        st.dataframe(preview_rows, hide_index=True)
        if show_azure_response:
            with st.expander('Azure API Response (Raw)', expanded=False):
                st.caption(f'Request URL: {trace.request_url}')
                st.json(trace.raw_response)

st.divider()

st.subheader('Run generated prompts through OpenRouter models')
st.caption('This section is execution-only. Model options (e.g., OpenAI/Claude) apply to OpenRouter runs, not Azure prompt generation.')

execution_dry_run = st.toggle('Execution dry run (no API call)', value=True)
selected_models = st.multiselect(
    'Models to run',
    options=available_models,
    default=default_models,
    help='Options include a broad OpenRouter catalog plus configured, assigned, and previously captured models.',
)

generated_df = generated_prompt_subset(prompts_df) if not prompts_df.empty else pd.DataFrame(columns=['PromptID'])
captured_model_count = existing['ModelName'].dropna().astype(str).nunique()

m1, m2, m3, m4 = st.columns(4)
m1.metric('Total prompts', len(prompts_df), border=True)
m2.metric('Generated prompts', len(generated_df), border=True)
m3.metric('Models used', captured_model_count, border=True)
m4.metric('Captured outputs', len(existing), border=True)

st.caption(
    f'Data source: {data_source} | Execution provider: {provider_label} | '
    f'{len(prompts_df):,} prompts | {captured_model_count} assigned models | {len(existing):,} captured outputs'
)

if generated_df.empty:
    st.warning('No generated prompts are available yet. Use Azure generation above first.')

execute = st.button(
    'Run selected models across the generated prompt bank',
    type='primary',
    disabled=(len(selected_models) == 0 or generated_df.empty),
)

if execute:
    execution_api_key = settings.execution_api_key()
    api_key = execution_api_key if not execution_dry_run else (execution_api_key or 'dry_run_key')
    if not api_key:
        st.error(f'{settings.execution_api_key_name()} is not set. Configure it or run in dry-run mode.')
        st.stop()

    if provider_slug == 'azure_foundry' and not settings.azure_foundry_endpoint:
        st.error('AZURE_FOUNDRY_ENDPOINT is not set. Configure it before running live requests.')
        st.stop()

    updated, summary = run_model_sweep(
        prompt_df=prompts_df,
        existing_results_df=existing,
        results_path=RESULTS_PATH,
        model_names=selected_models,
        dry_run=execution_dry_run,
        api_key=api_key,
        provider_name=provider_label,
        base_url=(
            settings.azure_foundry_endpoint
            if provider_slug == 'azure_foundry'
            else settings.openrouter_base_url
        ),
        timeout_seconds=(
            settings.azure_foundry_timeout_seconds
            if provider_slug == 'azure_foundry'
            else settings.openrouter_timeout_seconds
        ),
        api_key_header='api-key' if provider_slug == 'azure_foundry' else 'Authorization',
        api_key_prefix='' if provider_slug == 'azure_foundry' else 'Bearer ',
        include_openrouter_headers=(provider_slug != 'azure_foundry'),
        api_version=(settings.azure_foundry_api_version if provider_slug == 'azure_foundry' else None),
        app_name=settings.openrouter_app_name,
        app_url=settings.openrouter_app_url,
        organisation_name=tenant.display_name,
        organisation_aliases=tenant.aliases,
        competitor_aliases=tenant.competitors.aliases_by_name or None,
    )

    st.success(
        f"Sweep complete. Executed {summary['executed_prompts']} generated prompt runs across {len(selected_models)} models; "
        f"success={summary['success_count']}, failed={summary['failure_count']}."
    )
    st.caption(f"Saved results to {RESULTS_PATH}")
    st.dataframe(updated.tail(20), hide_index=True)

st.subheader('Captured output table')
st.caption('Explore saved model responses. These controls only filter captured data and do not make API calls.')

if existing.empty:
    st.info('No captured model responses are available yet.')
else:
    prompt_columns = [
        column
        for column in ['PromptID', 'Prompt', 'Market', 'Persona', 'Subject', 'Intent', 'ExpertiseArea']
        if column in prompts_df.columns
    ]
    output_table = existing.merge(
        prompts_df[prompt_columns] if prompt_columns else prompts_df,
        on='PromptID',
        how='left',
    )

    available_captured_models = sorted(output_table['ModelName'].dropna().astype(str).unique())
    visible_column = 'OrgVisible' if 'OrgVisible' in output_table.columns else 'SouthamptonVisible'
    with st.container(horizontal=True, vertical_alignment='bottom'):
        output_models = st.multiselect(
            'Filter by model',
            options=available_captured_models,
            default=available_captured_models,
            key='captured_output_models',
        )
        visibility_filter = st.segmented_control(
            'Visibility',
            options=['All', 'Visible', 'Not visible'],
            default='All',
            key='captured_output_visibility',
        )
        output_search = st.text_input(
            'Search prompts and responses',
            placeholder='Enter a prompt ID, phrase, persona or response text',
            key='captured_output_search',
        )

    filtered_outputs = output_table[output_table['ModelName'].astype(str).isin(output_models)].copy()

    if visibility_filter == 'Visible':
        filtered_outputs = filtered_outputs[
            pd.to_numeric(filtered_outputs[visible_column], errors='coerce').fillna(0).eq(1)
        ]
    elif visibility_filter == 'Not visible':
        filtered_outputs = filtered_outputs[
            pd.to_numeric(filtered_outputs[visible_column], errors='coerce').fillna(0).eq(0)
        ]

    search_term = output_search.strip()
    if search_term:
        searchable_columns = [
            'PromptID',
            'Prompt',
            'ResponseText',
            'ModelName',
            'Market',
            'Persona',
            'Subject',
            'Intent',
        ]
        search_mask = pd.Series(False, index=filtered_outputs.index)
        for column in searchable_columns:
            if column in filtered_outputs.columns:
                search_mask |= filtered_outputs[column].fillna('').astype(str).str.contains(
                    search_term,
                    case=False,
                    regex=False,
                )
        filtered_outputs = filtered_outputs[search_mask]

    display_columns = [
        column
        for column in [
            'PromptID',
            'Provider',
            'ModelName',
            'Prompt',
            'ResponseText',
            visible_column,
            'CitationSources',
            'Market',
            'Persona',
            'Subject',
            'Intent',
            'RunDate',
        ]
        if column in filtered_outputs.columns
    ]
    display_outputs = filtered_outputs[display_columns].reset_index(drop=True)

    st.caption(f'{len(display_outputs):,} captured outputs match the current filters.')
    selection = st.dataframe(
        display_outputs,
        hide_index=True,
        height=600,
        key='captured_output_table',
        on_select='rerun',
        selection_mode='single-row',
    )

    selected_rows = selection.selection.rows
    if selected_rows:
        selected_output = display_outputs.iloc[selected_rows[0]]
        with st.container(border=True):
            header_parts = [
                str(selected_output.get('PromptID', '')).strip(),
                str(selected_output.get('Provider', '')).strip(),
                str(selected_output.get('ModelName', '')).strip(),
            ]
            header_text = ' | '.join([value for value in header_parts if value])
            st.markdown(f'**{header_text}**')
            st.caption(str(selected_output.get('Prompt', '')))
            st.markdown(str(selected_output.get('ResponseText', '')))
            citations = str(selected_output.get('CitationSources', '')).strip()
            if citations not in {'', 'nan'}:
                st.markdown(f'**Citations:** {citations}')

    st.download_button(
        'Download filtered outputs as CSV',
        data=display_outputs.to_csv(index=False).encode('utf-8'),
        file_name='filtered_openrouter_outputs.csv',
        mime='text/csv',
        icon=':material/download:',
    )



