# AI Reputation Intelligence Platform

Streamlit proof of concept for multi-organisation AI reputation and visibility auditing, initially developed for the University of Southampton use case.

## Current status

Slice 2 (Core Analytics) is now in place:

- scoring engine for visibility, rank, citation and reputation score
- reusable sidebar filters across market, subject, persona, expertise area, intent and platform
- executive dashboard page with headline metrics and core charts
- prompt bank explorer with filtered table, coverage summary and CSV export
- microsite export page with both UI-faithful snapshot ZIP and rendered pro-report ZIP outputs

## Run locally

1. Create a Python virtual environment.
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Start the app:
   - `streamlit run app.py`

## Run with Docker

Build and start the app with Docker Compose:

```bash
docker compose up --build
```

The app is available at `http://localhost:8501`. To configure your execution provider and Azure prompt generation, copy
`.env.example` to `.env`, set provider environment values, and run Compose again. The
`.env` file and `.streamlit/secrets.toml` are excluded from the image build.

To build and run the image directly:

```bash
docker build -t ai-reputation-intelligence-platform .
docker run --rm -p 8501:8501 --env-file .env ai-reputation-intelligence-platform
```

## Current data files

- `data/Southampton_GEO_PromptBank_v2_15Segments_120Prompts 1.csv`
- `data/openrouter_results.csv`
- `data/corona_energy_prompts.csv`
- `data/corona_energy_results.csv`

Organisation workspaces select their own prompt bank and captured model outputs through the tenant registry.

## Source hierarchy

1. `docs/references/product_spec.md` (primary contract)
2. CSV and XLSX factual data structures
3. `docs/references/sprint_plan.md` and `docs/references/SKILL.md`
4. `docs/references/Moorhouse-UI-Standard.md` for UI standards

## Traceability

See `docs/traceability_log.md` for requirement mapping and delivery evidence.

Live upload, isolated execution runs, and demo readiness are tracked in
[the demo sprint board](docs/demo-readiness-sprints.md). The run-storage backend
and five-column Excel onboarding are implemented locally, with a shared saved/live
run selector. The Execution page runs every uploaded prompt through selected
OpenRouter models, saves progress and retries unfinished requests. Dashboards
include Category filters, run status, response coverage and sample counts.
Run History supports reopening, renaming, archiving/restoring and downloading
run bundles, original uploads and responses. Both 50-prompt, five-model demo
batches have completed locally; the smaller live rehearsal and hosted storage
verification remain in Sprint 5.

Uploaded workbooks and model outputs live in `data/runs/` (or `AIRP_RUNS_DIR`)
and are excluded from Git. The Demo Careers and Demo Research entry points refer
to those saved runs; preserve and migrate the run storage separately when moving
the app to another environment. Demo cards are unavailable until their saved run
files are present. A Git commit does not back up the uploaded workbooks or outputs.

The evidence standard, intervention levels, uplift-threshold calculation, and interpretation limits for generated recommendations are documented in `docs/recommendation-methodology.md`.

## Microsite export (downloadable stakeholder pack)

Use the `Microsite export` page in Streamlit to download one of two static client-ready microsite ZIPs:

- `Download snapshot microsite (.zip)` for exact captured page visuals
- `Download rendered microsite (pro) (.zip)` for a polished, structured report with real text, cards, charts, and tables

If the page reports missing assets, generate them locally first:

```bash
python scripts/capture_streamlit_pages.py
python scripts/build_screenshot_html.py
```

Both exports are read-only static packages. The snapshot mode preserves exact visuals, while rendered mode preserves structure and readability.

## Model execution setup (Azure OpenAI generation + OpenRouter execution)

This project now supports a hybrid prompt-bank flow:

- client-supplied prompts
- persona-generated prompts
- prompt generation through Azure OpenAI and execution through OpenRouter across selected models

Set environment variables (or copy `.env.example` values into your environment):

- `AIRP_EXECUTION_PROVIDER` (`openrouter` recommended for execution)
- `OPENROUTER_*` values for OpenRouter mode
- `AZURE_OPENAI_API_KEY` + `AZURE_FOUNDRY_*` values for Azure OpenAI prompt generation

Current scaffold modules:

- `src/execution/openrouter_runner.py`
- `src/execution/azure_prompt_generator.py`
- `src/config/settings.py`

The prepared-upload demo flow is Data Onboarding → create a live or simulated
run → Execution → select models → run every uploaded prompt → dashboard.
The Execution page uses OpenRouter settings directly. Configure
`OPENROUTER_API_KEY`, `OPENROUTER_MODELS`, and optionally
`OPENROUTER_BASE_URL` / `OPENROUTER_TIMEOUT_SECONDS`. Refresh the model list on
the page to load current OpenRouter text-model IDs. The chosen models are fixed
after execution starts. Successful responses are checkpointed individually;
retrying skips saved prompt/model pairs. An OS file lock prevents two workers
from writing the same run at once.

Simulated runs make no model requests and retain labelled placeholder responses
separately from live runs. Saved demo data is read-only in Execution. The Azure
prompt-generation modules and legacy capture scripts remain available separately;
the prepared-upload page executes the workbook's existing prompts.

## Azure deployment (robust)

Use the clean-context deploy script to avoid local folder permission issues (for example `.pytest_cache`):

```powershell
.\scripts\deploy_clean.ps1 -ImageTag "20260904-3"
```

Useful options:

- Skip image build and deploy an existing ACR tag:

```powershell
.\scripts\deploy_clean.ps1 -ImageTag "20260904-3" -SkipBuild
```

- Print commands without executing:

```powershell
.\scripts\deploy_clean.ps1 -ImageTag "20260904-3" -DryRun
```

One-click wrapper:

```powershell
.\scripts\deploy_latest.ps1 -ImageTag "20260904-3"
```

A GitHub Actions workflow is also included at `.github/workflows/deploy-holdingapp2.yml` (manual trigger) for repeatable deploys from a clean runner.
