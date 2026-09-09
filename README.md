# AI Reputation Intelligence Platform

Streamlit proof of concept for multi-organisation AI reputation and visibility auditing, initially developed for the University of Southampton use case.

## Current status

Slice 2 (Core Analytics) is now in place:

- scoring engine for visibility, rank, citation and reputation score
- reusable sidebar filters across market, subject, persona, expertise area, intent and platform
- executive dashboard page with headline metrics and core charts
- prompt bank explorer with filtered table, coverage summary and CSV export

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

The Streamlit analytics flow can consume captured outputs (CSV replay) or live model responses from the selected provider. Execution is cost-safe: only `PromptSource=generated` rows are eligible, and only pending prompts run on explicit button click.

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
