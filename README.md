# AI Reputation Intelligence Platform

Streamlit proof of concept for AI reputation and visibility auditing, starting with the University of Southampton use case.

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

The app is available at `http://localhost:8501`. To configure OpenRouter, copy
`.env.example` to `.env`, set `OPENROUTER_API_KEY`, and run Compose again. The
`.env` file and `.streamlit/secrets.toml` are excluded from the image build.

To build and run the image directly:

```bash
docker build -t ai-reputation-intelligence-platform .
docker run --rm -p 8501:8501 --env-file .env ai-reputation-intelligence-platform
```

## Current data files

- `data/Southampton_GEO_PromptBank_v2_15Segments_120Prompts 1.csv`
- `data/openrouter_results.csv`

The app uses the V2 prompt bank and captured OpenRouter outputs throughout.

## Source hierarchy

1. `docs/references/product_spec.md` (primary contract)
2. CSV and XLSX factual data structures
3. `docs/references/sprint_plan.md` and `docs/references/SKILL.md`
4. `docs/references/Moorhouse-UI-Standard.md` for UI standards

## Traceability

See `docs/traceability_log.md` for requirement mapping and delivery evidence.

## OpenRouter execution setup (new architecture)

This project now supports a hybrid prompt-bank flow:

- client-supplied prompts
- persona-generated prompts
- execution through OpenRouter across selected models

Set environment variables (or copy `.env.example` values into your environment):

- `OPENROUTER_API_KEY`
- `OPENROUTER_MODEL` (default: `openai/gpt-4.1-mini`)
- `OPENROUTER_TIMEOUT_SECONDS` (default: `45`)
- `OPENROUTER_APP_NAME`
- `OPENROUTER_APP_URL`

Current scaffold modules:

- `src/execution/openrouter_runner.py`
- `src/config/settings.py`

The Streamlit analytics flow can consume captured outputs (CSV replay) or live OpenRouter responses from this runner. OpenRouter execution is cost-safe: only `PromptSource=generated` rows are eligible, and only pending prompts run on explicit button click.

