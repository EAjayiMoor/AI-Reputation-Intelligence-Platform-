# Live demo delivery tracker

Updated: 29 October 2026.

## Agreed workflow

Upload a prepared Excel file → validate and preview every row → select models →
execute every validated prompt through OpenRouter → view the selected run in the
existing dashboards. Any prompt subset is fixed and recorded before execution;
the app does not silently sample prompts.

Input headings: **Market, Persona, Subject, Category, Prompt**.
Demo target: 18 prompts × three models = 54 requests per scenario. This is a
workload target; runtime must be measured during rehearsal.

The two scenarios are Careers & Employability and nine Southampton subject
areas. Category and Subject values must come from the workbook, without fixed
lists in application code.

## Sprint board

| Sprint | Component | Status | Completion evidence |
| --- | --- | --- | --- |
| 1 | Isolated run storage backend | Complete locally | Nine focused tests passed; original upload, prompts, results and manifest persist separately for each run |
| 2 | Excel onboarding and run selection | Complete locally | Five-column Excel/CSV adapter and upload preview; isolated named runs; page navigation, saved-demo switch and session/cache isolation checked |
| 3 | OpenRouter execution and recovery | Complete locally | Model selection, individual response checkpoints, progress, failure history, retries, interrupted-run recovery and OS writer locks verified; 59 focused regression checks passed |
| 4 | Dashboard integration and run history UI | Complete locally | Category filters, run coverage/status, percentage denominators, history actions and coherent downloads; all eight analysis/export pages verified with ready/partial/complete runs and saved-demo fallback |
| 5 | Both scenario rehearsals and hosting readiness | Local banked rehearsal complete; host validation open | Actual workbook reviewed; 50 prompts × five models completed per tab (500 responses total); costs and timings recorded; source-row mapping, dashboard loader and bundles checked; banked files unchanged. Demo-sized live run and hosted-volume persistence remain open |

Statuses describe delivered evidence, not estimates. Backend completion does not
mean the corresponding user interface has been connected.

## Sprint 1 — isolated run storage backend

- [x] Unique organisation-scoped run directories.
- [x] Preserve original upload and its SHA-256 fingerprint.
- [x] Store canonical prompts, an empty results file and a versioned manifest.
- [x] Record run name, organisation, timestamps, prompt count and live/dry-run mode.
- [x] List runs by organisation and support rename, archive and restore in the backend.
- [x] Validate path components to prevent a run resolving outside its storage root.
- [x] Write manifests atomically and publish them after the input files are saved.
- [x] Keep uploaded files/results out of Git through `data/runs/` ignore rule.
- [x] Make storage configurable with `AIRP_RUNS_DIR` for a future persistent mount.

Code: `src/runs/store.py`. Tests: `tests/test_run_store.py`.
Verification: new tests were first run against the missing storage feature and
failed; all nine passed after implementation. Pytest uses a unique local
`--basetemp .tmp/run-store-<verification-id>` because the default OS temporary
pytest directory is inaccessible on this machine.

The store has no API for writing to the tenant registry or banked datasets.
Sprint 2 connects onboarding and run selection to this store. Sprint 3 replaces
the legacy direct-file Execution page with isolated-run execution. Saved demo
files remain unavailable as execution write targets.

## Sprint 2 — Excel onboarding and run selection

- [x] Accept the five agreed headings; trim header whitespace and validate duplicates.
- [x] Generate internal IDs and organisation/provider metadata automatically.
- [x] Preserve Category independently from Subject and Intent.
- [x] Show preview, row count and coverage; flag blank required cells and empty files.
- [x] Let users select a workbook sheet if more than one is present.
- [x] Create a new run with every validated row and the original workbook.
- [x] Keep tenant registry/banked paths intact when uploading.
- [x] Add a shared Saved demo / Live run selector that persists across pages.
- [x] Clearly distinguish simulated runs from live results.

Delivered: XLSX/UTF-8 CSV upload with a blank CSV template, all-row preview,
row-specific errors, named live/simulated runs, retained workbook sheet provenance,
and a session-local selector used by the shared data loader. Header matching
ignores case and surrounding whitespace. Fully blank rows are ignored; partially
blank rows block creation. Repeated questions are retained with separate IDs.
Category is preserved as its own field; dashboard Category controls remain Sprint 4.

Verification: 34 focused backend/UI and existing tenant/model checks passed.
Streamlit AppTest exercises preview → create → selected run, page navigation,
an empty-results dashboard, saved-demo fallback, malformed workbook handling,
and independent session caches. XLSX files used in these tests are generated
fixtures, not the actual client workbooks. No live OpenRouter request was made.

Local review: choose the organisation on Start → Data Onboarding → upload XLSX
or CSV → select a sheet if needed → review errors/coverage → name and create
the run. Use the sidebar Data run selector and Prompt Bank Explorer to inspect
the uploaded rows. Execution was unavailable at the Sprint 2 milestone and is
now connected through Sprint 3.

## Sprint 3 — OpenRouter execution and recovery

- [x] Execute every uploaded row, including client/generated sources, in isolated runs.
- [x] Select models and preview prompts × models before starting.
- [x] Freeze the run's models after execution begins; changed models create a new run.
- [x] Save each successful response before reporting progress.
- [x] Record failures and maintain Ready / Running / Partial / Complete / Failed states.
- [x] Retry unfinished requests without duplicating saved prompt/model pairs.
- [x] Distinguish interrupted runs from active execution; prevent concurrent writers to one run.
- [x] Keep dry-run responses separate and visibly labelled.
- [x] Handle empty or malformed provider responses as failures.

Delivered: `src/runs/executor.py` and `src/ui/run_execution.py` power the new
Execution page. It defaults to up to three configured/assigned models, displays
planned/saved/unfinished/failed counts, streams progress, shows captured responses
and current errors, and offers a CSV download. Live runs require the configured
OpenRouter key; simulations bypass HTTP entirely. Refresh model choices using
OpenRouter's documented [models endpoint](https://openrouter.ai/docs/api/api-reference/models/get-models).
Static configured choices remain available if a refresh is not requested.

Each success is atomically saved to the run's results CSV before its progress
callback. `attempts.jsonl` retains attempt outcomes after a successful retry
clears the current failure list. Models and endpoint are fixed for pending
requests once execution starts; prompt fingerprints detect changed inputs.
The store also locks rename/archive updates during execution.

Locks use Windows byte-range locks or POSIX flock and are released by the OS
when the worker exits. A Running manifest with no active lock is displayed as
Interrupted. Resume reconstructs completed pairs from committed responses. If
all responses were already saved, Finalize saved run reconciles status without
another model request. An interrupted request that reached the provider but
was not saved locally may be billed again when explicitly retried; this case
is identified on the Execution page. Execution is currently sequential, and
real API latency must still be measured in Sprint 5.

Verification: **59 focused tests passed** across storage, Excel onboarding,
run selection, execution, catalogue refresh, Streamlit UI, and existing tenant/model
flows. New execution cases were checked failing before their implementation.
Tests cover mocked live HTTP payloads/authentication, token/cost capture,
partial/all failures, redacted errors, no repeat of committed successes,
model freezing, two competing processes, worker termination, and interruptions
after intermediate/final saves. AppTest covers simulated run → responses →
dashboard, missing live credentials, active-writer prevention and retry/finalize
buttons. Real banked prompt/results and registry bytes remain unchanged in these
UI checks. No paid API requests, real client rehearsal or deployment were performed.

## Sprint 4 — dashboards and run history

- [x] Resolve both prompts and responses from the same selected run through the shared loader (Sprint 2 prerequisite).
- [x] Include run-specific paths in caching so changing runs cannot show another run's data (verified in Sprint 2).
- [x] Add Category to the shared filters; preserve existing market/persona/subject/model filters.
- [x] Show run name, status and response coverage, including partial runs.
- [x] Provide counts alongside headline percentages so small samples are interpretable.
- [x] Add history UI with rename, archive/restore and downloads.
- [x] Switch to the banked demo instantly without changing its files.
- [x] Handle newly uploaded runs with no responses across all eight analysis/export pages.

Delivered:

- Shared run captions show name, live/simulated mode, effective status and saved
  response coverage. Partial/interrupted runs explain that only saved responses
  are analysed. Saved snapshots show observed counts without assuming a completed
  execution plan.
- Category is preserved independently from Subject/Intent and is included in
  shared filters and Prompt Bank Explorer. Filter widget keys are scoped to the
  organisation/run, preventing stale selections from carrying into another run.
  Literal uploaded labels such as `NA` are retained; baseline parsing is preserved.
- Percentage metrics include the supporting counts. Citation count numerators are
  retained directly rather than reconstructed from rounded rates. Prompt Explorer
  counts unique prompts rather than prompt/model rows.
- Audience Journey uses Category when uploaded files have no Expertise Area.
  This supports the agreed five-column schema without inventing an expertise label.
- Run History lists ready, partial, completed and archived runs. It supports rename,
  archive/restore, opening a run, switching to Saved demo, original upload/results
  downloads and a ZIP bundle containing prompts, responses, provenance and attempts.
- Bundle downloads take the execution lock to capture a consistent snapshot.
  Rename/archive and downloads are disabled during active execution. Archiving
  retains files and removes a run from the normal dataset selector; restore makes
  it selectable again. No delete action is introduced.
- Selected-run exports use the rendered report, with run name/mode/status and ID
  in its metadata. Prebuilt screenshot exports remain with Saved demo, so live
  results cannot be presented through banked screenshot assets.

Verification: the full focused regression passed **122 checks**. After a final
uploaded-label preservation fix, **55 affected view/loader checks passed**, including
the additional `NA` Category case: **123 distinct checks across the verification
runs**. These cover all eight views for Ready/Partial/Complete, switching each
view to Saved demo, category filtering, small-sample denominators, history actions,
archive bundle contents, active-writer prevention and unchanged banked file bytes.
Input/results in the UI scenarios are synthetic fixtures; no paid requests or
deployment were made. A final unused-calculation cleanup and download-label edit
do not change the verified behaviour.

Local review: select a workspace → Run History in the sidebar → choose a run
to rename/archive/download, or Open run to analyse it. Category appears with the
other dashboard filters. Sprints 1–4 are complete locally; the actual client
workbooks, paid rehearsal, runtime measurement and host persistence remain Sprint 5.

## Sprint 5 — rehearsal and hosting

- [x] Inspect the supplied workbook. It contains 100 unique, nonblank prompts on
      each tab and the five required columns. Research covers nine subjects;
      Careers covers those subjects plus General.
- [x] Fix a reproducible, balanced selection of 50 whole rows from each tab.
      Each saved prompt row retains Market, Persona, Subject, Category, Prompt,
      source sheet, original Excel row and selection rule. Prompt IDs encode the
      source row so a retry uses the same prompt/model pair.
- [x] Run both banked samples through the five Southampton models: 250 requests
      per scenario, 500 total. Each run completed with 250/250 saved responses
      and zero failed attempt events.
- [x] Confirm all 50 selected rows in each run match the original workbook and
      that the shared dashboard loader produces 250 joined rows with all five
      dimensions and five models.
- [x] Confirm each run bundle contains the original workbook, selected prompts,
      responses, manifest and attempt history. Original Southampton prompt,
      result and registry files remain unchanged.
- [x] Exercise interruption and resume after a transient Windows manifest-file
      replacement lock. The run resumed from saved responses; no duplicate
      prompt/model result pairs were present. Manifest replacement now retries
      transient permission errors; 10 focused run-store checks passed.
- [x] Record actual banked-run timing and reported cost:
      Careers — 2,513.4 seconds (41m 53s), 179,686 tokens, $0.66790978;
      Research — 1,956.0 seconds (32m 36s), 183,470 tokens, $0.66776729.
      Combined reported cost: $1.33567707. These are recorded OpenRouter API
      cost fields; they are not a quote for future runs.
- [ ] Rehearse the smaller client-demo workload (18 prompts × three models per
      scenario) and measure its actual runtime.
- [ ] Verify storage survives restart and redeployment in the actual host.
- [ ] Record and verify the Azure persistent-volume configuration. Local
      `data/runs/` results are not proof of hosted durability.

Run IDs:

- Careers: `20261029T213634_06a312c914f94a929b4a32c94e12e1dd`
- Research: `20261029T213634_daaaee1c60dd4bc6ac2d5f274f7e74e8`

## Storage layout

Default root: `data/runs/`, or the location configured by `AIRP_RUNS_DIR`.

```text
<root>/<organisation>/<unique-run-id>/
    input.xlsx       # original file, or input.csv / input.xls
    prompts.csv      # canonical prompt rows for this run
    results.csv      # responses for this run
    manifest.json    # identity, provenance, settings and status
    attempts.jsonl   # execution attempt outcomes (created when execution starts)
    .execution.lock  # persistent file; OS controls ownership while a writer runs
```

The manifests form the initial catalogue; a separate database is unnecessary
for this demo scope. The per-run writer lock is implemented in Sprint 3; its
behaviour on the actual hosted volume remains part of Sprint 5. A database or job queue remains a
future decision if concurrent user requirements grow.

The existing banked Southampton dataset remains the source for the Saved demo
option. It contains captured responses, but is not a complete prompt × five-model
matrix. Rehearsal runs must therefore be assessed separately from that baseline.

## Delivery notes

- 30 October: both saved demos now derive competitor mentions from their captured
  response text using the existing university catalogue. The demo-only loader
  falls back to that catalogue when the tenant competitor list is empty, retains
  response-level de-duplication, and excludes institution-naming prompts from
  neutral comparisons. The original run CSVs and organisation profiles are not
  rewritten. Overview summaries and full competitor views include model and
  segment comparisons, denominators, recognition coverage and response evidence.
  Both actual 250-response demos, model filtering, ordinary-workspace regressions
  and unchanged saved-data hashes were checked. Recognition is limited to the
  documented university catalogue; no additional OpenRouter requests were made.

- No paid OpenRouter calls or deployment have been made as part of Sprints 1–4.
- Existing edits in `.streamlit/config.toml`, `requirements.txt`, and
  `scripts/deploy_latest.ps1` predate this work and are left intact.
