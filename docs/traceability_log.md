# Traceability Log

This log maps implemented work to source documents and evidence.

## Source precedence

1. `docs/references/product_spec.md`
2. CSV and XLSX factual data structures
3. `docs/references/sprint_plan.md` and `docs/references/SKILL.md`
4. `docs/references/Moorhouse-UI-Standard.md` for UI standards

## Slice 1 Foundation

| Item | Source | Status | Evidence |
|---|---|---|---|
| Repo scaffold | sprint_plan Epic 1 | Done | folders under root workspace |
| App entrypoint | sprint_plan Story 1.1 | Done | `app.py` |
| Dependencies manifest | sprint_plan Story 1.1 | Done | `requirements.txt` |
| Source docs imported | project governance decision | Done | files in `docs/references/` |
| UI standard baseline gate | Moorhouse UI Standard | In progress | `docs/ui/moorhouse_ui_checklist.md` |
| Prompt traceability contract scaffolding | product_spec section 9 and sprint plan data model epics | In progress | `src/prompts/` stubs |

## Slice 2 Core Analytics

| Item | Source | Status | Evidence |
|---|---|---|---|
| Scoring engine (visibility, rank, reputation) | sprint_plan Epic 4 | Done | `src/scoring/engine.py` |
| Sidebar filters | sprint_plan Story 5.2 | Done | `src/ui/data.py` |
| Executive dashboard headline metrics and charts | sprint_plan Epic 6 | Done | `pages/1_Executive_Dashboard.py` |
| Prompt explorer with export and coverage summary | sprint_plan Epic 7 | Done | `pages/2_Prompt_Bank_Explorer.py` |
| Slice 2 sample data defaults | sprint_plan Epics 2 and 5 | Done | `data/sample_prompts.csv`, `data/sample_results.csv` |

## Slice 3 Client Value

| Item | Source | Status | Evidence |
|---|---|---|---|
| Audience journey selector and narrative | sprint_plan Epic 8 | Done | `pages/3_Audience_Journey_Simulator.py` |
| Visibility heatmap and rank analysis | sprint_plan Epic 9 | Done | `pages/4_Visibility_Analysis.py` |
| Competitor parsing and dashboards | sprint_plan Epic 10 | Done | `src/scoring/engine.py`, `pages/5_Competitor_Analysis.py` |
| Recommendation rule engine and export page | sprint_plan Epic 11 | Done | `src/recommendations/engine.py`, `pages/6_Recommendations.py` |


## Architecture Direction Update

| Item | Source | Status | Evidence |
|---|---|---|---|
| Hybrid prompt-bank strategy (client + persona-generated) | user architecture decision, product_spec, sprint_plan | Updated in docs | `docs/references/product_spec.md`, `docs/references/sprint_plan.md` |
| OpenRouter execution pipeline as core flow | user architecture decision, product_spec, sprint_plan | Updated in docs | `docs/references/product_spec.md`, `docs/references/sprint_plan.md` |

## Execution Scaffold Update

| Item | Source | Status | Evidence |
|---|---|---|---|
| OpenRouter runner scaffold | updated sprint plan Story 3.4 | Done | `src/execution/openrouter_runner.py` |
| Environment config scaffold | updated product spec NFR + architecture | Done | `src/config/settings.py`, `.env.example` |
