# British Airways workspace onboarding — 24 November 2026

Scope: configuration/data onboarding using the existing tenant registry and RunStore. Operational data isolation matters; no execution-engine or UI changes, deployment or live model calls.

Acceptance: BA-01 discoverable British Airways tenant; BA-02 all 750 unique source IDs and original field values preserved after cp1252 to UTF-8 conversion; BA-03 isolated ready run with original upload and empty results; BA-04 existing tenant configurations unchanged. Verify through the actual tenant/data loaders, source equality, run manifest and focused existing tests.

Plan: validate bank, register tenant with existing five model identifiers, import a named ready run using RunStore, verify acceptance and record evidence. Source Model 1–3 assignments are metadata; existing execution uses the models selected on the Execution page. Bank specifies OpenAI/Anthropic/Gemini (2,250 calls); all five would be 3,750. No models executed or availability checked.

Roles: user is product owner; Codex performs configuration, verification and self-review. No independent review. Reversible local onboarding; rollback by removing the new tenant and BA data only.

Skills used:
- C:/Users/EmmanuelAjayi/.agents/skills/ai-sdlc/SKILL.md — light-path delivery
- C:/Users/EmmanuelAjayi/.codex/skills/graphify/SKILL.md — repository navigation (no existing graph)
- C:/Users/EmmanuelAjayi/.codex/skills/karpathy-guidelines/SKILL.md — minimal scope
- C:/Users/EmmanuelAjayi/.codex/skills/verification-before-completion/SKILL.md — fresh verification
- C:/Users/EmmanuelAjayi/.codex/plugins/cache/openai-primary-runtime/spreadsheets/26.1123.11515/skills/spreadsheets/SKILL.md — CSV source inspection

Status: implementation pending. AI response evaluation deferred until responses exist. Existing user edits in requirements.txt and scripts/deploy_latest.ps1 are outside scope.

## Verification outcome

Implemented and verified locally on 24 November 2026 against the working tree. No deployment or API calls. BA-01 through BA-04 passed: tenant discovery; exact equality of all nine original CSV fields for 750 rows; original uploaded bytes retained; isolated ready run; empty baseline/run results; model mapping matches Moorhouse; baseline and run both load through src.ui.data._load_core_data. Existing tenants were not edited.

Run: 20261124T150137_1dc5b31146e546d0b0a7899632bc7ea5. Files live under data/runs/british_airways/ (git-ignored runtime storage). Run name: British Airways — 750 prompt baseline. Select British Airways on Start, then this run in the run selector. The registry also provides a default bank and empty results under data/british_airways_*.csv.

Commands: PYTHONPATH=<project root> .venv/Scripts/python.exe .tmp/verify_british_airways.py (PASS); .venv/Scripts/python.exe -m pytest tests/test_tenant_loader.py -q (3 passed; harmless existing pytest-cache write-permission warning). Verification scripts are local scratch files, not product code. Self-review only. Browser/UI interaction and deployment not performed.

The existing Execution page selects models independently of Model 1–3 columns. To match the source bank, select openai/gpt-4.1-mini, anthropic/claude-haiku-4.5 and google/gemini-3.6-flash. No provider availability or output-quality claim is made. All five configured models remain available for a separately chosen 3,750-response run.

Initial competitor catalogue: Virgin Atlantic, Emirates, Qatar Airways, Singapore Airlines, Lufthansa, Air France, KLM, easyJet, Ryanair, Turkish Airlines, Etihad Airways. This is a provisional operational catalogue for airline mention analysis, not a researched market ranking. Review with the product owner before interpreting competitor results.

Limitation: the original input and ready run are local runtime data excluded from Git. A later deployment needs explicit transfer to its persistent run storage. No remote environment was changed. Rollback scope is the new british_airways registry/data/run and this note; preserve other organisations and existing user edits.


## Confirmed three-model scope — 24 November 2026

User selected only OpenAI, Anthropic and Gemini. This supersedes the five-model onboarding configuration above. Tenant mapping and the existing ready-run model selection now contain exactly openai/gpt-4.1-mini, anthropic/claude-haiku-4.5 and google/gemini-3.6-flash. Planned requests: 750 × 3 = 2,250. Verified via load_tenant and run_summary: exact model list, expected_requests=2250, completed_requests=0, status=Ready. No model calls or deployment. Other organisations unchanged.

## Authorised live pilot

User authorised a 10-prompt, three-model pilot (30 requests). Use 10 evenly spaced rows across the bank to sample its subject range, retaining source IDs and text. Separate named pilot run, leaving the 750-prompt baseline untouched. Preflight: credentials present and all three IDs listed by configured provider catalogue. Acceptance: 30 unique prompt/model pairs, nonempty real responses, original prompt IDs, saved accounting and no baseline responses. Quality self-review: relevance to the question, substantive answer, and obvious refusal/error/placeholder text; factual claims and citations are not independently verified. Report missing cost rather than treating it as zero. No automatic full-bank execution.

## Live pilot result — 24 November 2026

Run 20261124T150958_ab38fbcc8ca94fa38242edd477b17f08 completed 30/30 requests, 10 per selected model, with zero request failures and 30 unique nonempty prompt/model responses. The full baseline has zero results. Original pilot prompts, full responses and attempts remain under data/runs/british_airways/<run_id>/. Runtime: 152.41 seconds. All costs below are provider-reported usage.cost values; no missing cost rows.

| Model | Saved responses | Reported cost (USD) | Total tokens |
| --- | ---: | ---: | ---: |
| GPT-4.1 Mini | 10 | 0.0060948 | 4350 |
| Claude Haiku 4.5 | 10 | 0.017955 | 4147 |
| Gemini 3.6 Flash | 10 | 0.045297 | 12556 |
| Total | 30 | 0.0693468 | 21053 |

Cost projection by simple 75x scaling to 750 prompts: approximately USD 5.20; directional only, sensitive to prompt/output lengths and any token-limit change. This is not a quote or spend authorisation.

Quality gate: HOLD full run. Self-review of saved output excerpts found generally relevant answers but incomplete Gemini outputs: BA084 ends at “and”, BA167 starts mid-sentence and ends at “A3”, BA500 and BA750 also end mid-thought. All ten Gemini rows report 1,196 completion tokens; runner payload caps max_tokens at 1,200. This strongly suggests the response budget contributes to truncation, but raw finish_reason/reasoning usage are not retained, so exact provider termination cause is unconfirmed. A nonempty response currently counts as an execution success; Complete does not establish content completeness. Five rows contain extracted citation sources; no factual or citation correctness verification performed. Some responses assert specific routes/products/loyalty benefits without supporting evidence and need caution in downstream interpretation.

Next: investigate/adjust response budget and completeness detection, then validate Gemini in a small rerun before scaling. No runner changes, reruns, or full-bank calls made in this pilot. Evidence commands: .venv/Scripts/python.exe -u .tmp/run_ba_pilot.py; follow-up pandas assertions for 30 unique nonempty real responses, exact ID coverage and empty baseline; token and response-ending inspection. Self-review only; no independent review or deployment.

## Truncation fix plan

Acceptance: TR-01 a provider length stop must fail and remain retryable rather than enter completed results; TR-02 Gemini gets an 8,192-token combined budget and low reasoning effort, preserving other models' 1,200-token behaviour; TR-03 persist finish reason, reasoning tokens and requested output limit for successful responses and failed-attempt audit; TR-04 legacy CSVs still load; TR-05 previously affected pilot prompts finish normally in a separate Gemini-only validation run. Unit/integration regression tests first, then the existing execution/storage suites. No full-bank execution or deployment. Roles: same-agent implementation and self-review. Additional skills: C:/Users/EmmanuelAjayi/.codex/skills/systematic-debugging/SKILL.md and C:/Users/EmmanuelAjayi/.codex/skills/test-driven-development/SKILL.md. Provider documentation consulted: https://openrouter.ai/docs/guides/best-practices/reasoning-tokens and https://openrouter.ai/docs/api_reference/overview.

## Truncation fix verification — 24 November 2026

Root cause confirmed by one live BA167 reproduction using the original runner: finish_reason=length, native_finish_reason=MAX_TOKENS, completion_tokens=1196, reasoning_tokens=1150, visible_chars=222; the old runner still returned success=True. Diagnostic request cost USD 0.00453.

Implementation: Gemini requests through OpenRouter now use max_tokens=8192 and reasoning.effort=low. Other provider/model budgets remain 1200. Explicit non-stop finish reasons are failures, so partial answers do not enter completed result storage and remain retryable; no automatic charge-incurring retry was added. Missing finish_reason remains accepted for compatibility with older compatible providers. FinishReason, ReasoningTokens and OutputTokenLimit are saved in successful results; attempt logs retain these diagnostics and api_cost for explicit incomplete finishes, including reasoning-only empty outputs. Historical result CSVs load with blank new fields.

Test-first evidence: new tests initially failed on the old runner (including executor incorrectly reporting Complete for length stops); the reasoning-only accounting test also failed before its correction. Final command: .venv/Scripts/python.exe -m pytest tests/test_response_completeness.py tests/test_run_execution.py tests/test_openrouter_multi_model.py tests/test_run_store.py tests/test_run_selection.py tests/test_run_dashboard_views.py tests/test_tenant_loader.py -q -p no:cacheprovider. Result: 79 passed in 83.35 seconds. An earlier overlapping run timed out on the Competitor Analysis AppTest at 40 seconds (77 passed, 1 failed); the final run passed it without changes. git diff --check passed (line-ending warnings only). Existing user edits in requirements.txt and scripts/deploy_latest.ps1 preserved.

Live validation run: 20261124T152225_0a19712893d5451d8abf4bd3cb591018, named British Airways — Gemini completeness retest. Same 10 pilot prompts, Gemini only. 10/10 unique responses saved, all FinishReason=stop, OutputTokenLimit=8192, zero failures; completion tokens range 406–1922. Runtime 65.75 seconds; provider-reported cost USD 0.04265325. Beginnings and endings of all ten responses self-reviewed: no observed mid-sentence truncation. Original pilot and the zero-response full baseline preserved.

Acceptance TR-01–TR-05 verified. This validates completeness handling, not factual accuracy or citation correctness. The earlier full-bank cost extrapolation is superseded by changed Gemini settings; no full-bank execution or deployment performed. Readiness: local fix verified, original pilot has known incomplete historical Gemini rows and should not be used as clean analysis evidence. Use the named retest for Gemini validation. Rollback code via the focused runner/storage/pipeline/executor changes; preserve historical run files. Self-review only.

## Full baseline started — 24 November 2026

User explicitly authorised full execution. Started existing run 20261124T150137_1dc5b31146e546d0b0a7899632bc7ea5 with 750 prompts and exactly the three selected models (2,250 planned requests), using the verified completeness fix and a 90-second per-request timeout. Launch: PYTHONPATH=<project root> .venv/Scripts/python.exe -u .tmp/run_ba_full.py. Execution runs in a continuing local process; checkpoints and execution.log are in the baseline run directory. Initial verification: status=Running, active lock=true, 5 committed responses, all FinishReason=stop, 0 failures. This records start only, not completion. No deployment.

## Bounded parallel capture plan — 24 November 2026

User requested faster execution of the already-authorised baseline. Current bottleneck: src/runs/executor.py waits for each provider request sequentially. CP-01 add opt-in max_workers with default 1 (existing callers unchanged), bounded to 1–16. CP-02 at most N requests in flight; worker threads only call providers, while the coordinator remains the single results/manifest/audit writer under the existing process lock. CP-03 resume skips every committed prompt/model pair and retains stable ResultIDs. CP-04 worker exceptions and truncated outputs remain retryable and recorded. Validate with synchronisation-based fake runners and existing execution regression tests before resuming baseline at eight workers. No model changes or additional prompts. Existing sequential process must be stopped before its replacement acquires the same run lock; an in-flight uncommitted request may need to be retried. Record count and preserve existing output bytes before switching. Same-agent implementation and self-review.

## Parallel switch verification

Opt-in bounded max_workers implemented (default 1, valid 1–16). Tests first failed due to missing max_workers; then 34 execution/completeness/multimodel tests passed. Only provider calls run on a bounded pool; the coordinator retains the run lock and owns all result/manifest/audit writes. Stable ResultIDs and committed-pair skip logic retained.

Stopped only the two identified Python launcher/worker processes for .tmp/run_ba_full.py, preserved all 154 committed responses in checkpoint_before_parallel.csv inside the run, and resumed with max_workers=8. Verified through run_summary: active=true, status=Running, max_workers=8, 188 completed, zero failures. Compared every pre-switch row/field against the active results: unchanged. One old in-flight request may have reached the provider before termination; its uncommitted result is retried on resume. No saved response repeated. git diff --check passed (line ending warnings only). Full run is ongoing, not complete.

## Full run complete — 24 November 2026, 16:00 London time

Final result: 750 prompts × three selected models = 2,250 saved real responses, 750 per model. Run status Complete; process lock released; zero unresolved request failures. All saved responses have FinishReason=stop, nonempty text, unique prompt/model pairs and unique ResultIDs. Every prompt has exactly three responses. Application data loader returned 750 prompts, 2,250 results and 2,250 merged rows.

| Model | Responses | Recorded response cost USD |
| --- | ---: | ---: |
| openai/gpt-4.1-mini | 750 | 0.440410 |
| anthropic/claude-haiku-4.5 | 750 | 1.395772 |
| google/gemini-3.6-flash | 750 | 3.030835 |
| Total | 2250 | 4.86701635 |

Costs are usage.cost attached to saved responses, not a reconciled account invoice. They exclude separate pilots/diagnosis and any billed in-flight requests lost during interruptions. Manifest attempted_requests=2259. Elapsed wall time from initial start: 34.07 minutes including sequential phase, implementation, switch and recovery. Eight-worker phase completed the majority of work in about 24 minutes including recovery.

Recovery: at 1,478 saved responses, Windows raised PermissionError/WinError 5 on atomic results.csv replacement. Existing records stayed intact. Added bounded exponential retry (five attempts) matching the existing manifest retry approach. New regression test failed before the correction, then affected suite passed: 46 tests in 7.27 seconds (.venv/Scripts/python.exe -m pytest tests/test_run_execution.py tests/test_response_completeness.py tests/test_openrouter_multi_model.py tests/test_run_store.py tests/test_run_selection.py -q -p no:cacheprovider). Resumed same run and completed. A few in-flight responses may have needed provider re-execution, as reflected in attempt count; committed responses were skipped.

Final integrity procedure: PYTHONPATH=<project root> .venv/Scripts/python.exe .tmp/verify_ba_full.py — PASS. Checkpoint comparison confirms original response texts/identifiers and numeric values preserved. CSV roundtrips change some numeric formatting (3 to 3.0); the legacy loader also normalises literal N/A no-citation placeholders to blank. These semantic normalisations were explicitly handled in comparison, not treated as substantive response changes. Original checkpoint remains available. No factual/citation correctness audit or independent review claimed. No deployment.

Output: data/runs/british_airways/20261124T150137_1dc5b31146e546d0b0a7899632bc7ea5/results.csv. Select British Airways and British Airways — 750 prompt baseline in the local app to analyse. Runtime data stays git-ignored; remote environments have not been updated. Monitoring task complete.


## Executive dashboard default-run fix — 24 November 2026

Root cause: a new session selected Saved demo (empty British Airways baseline results file), while actual responses lived in the completed isolated run. Added optional TenantConfig.default_run_id loaded from registry and configured British Airways to its 750-prompt completed baseline. selected_run_id uses this default only when no explicit session selection exists; manual choices, including Saved demo, remain respected. Existing unavailable-run fallback retained. Other tenants have no default and behave as before.

Test-first: Streamlit regression reproduced default=None before fix. Final verification: actual app.py AppTest navigation to Executive Dashboard with active British Airways and no selected-run state rendered baseline coverage 2250/2250 without exception or empty-demo warning. Fixture-based regression covers default selection and switching to Saved demo without depending on git-ignored live files. Skills: C:/Users/EmmanuelAjayi/.agents/skills/developing-with-streamlit/SKILL.md and installed .venv/Lib/site-packages/streamlit/.agents/skills/developing-with-streamlit/SKILL.md (session-state reference); previously loaded debugging, test-first and verification skills apply. Local fix only, self-review, no deployment.

## Existing-session empty-demo recovery

The first default-run fix covered fresh sessions but respected an existing explicit None (Saved demo) selection. Reproduced the user's persistent case with selected_run_ids={'british_airways': None}; it returned None before this fix. Updated selection to recover to the configured default when the saved-demo CSV has no rows or cannot be read. Explicit real run choices and populated demo snapshots remain respected. Six focused tests pass, including stale-state regression and genuine-demo selection. No browser inspection claim: CUA runtime failed to start. AppTest verification separately covers actual Executive Dashboard rendering with stale selection state. No data changes or deployment.

## Live server verification after restart

User continued seeing the previous view despite passing AppTests. Confirmed port 8501 was served by the original Python Streamlit process started before selection fixes. Restarted that specific verified process with --server.runOnSave true. Then used a real headless Chromium browser against http://localhost:8501: opened Start, activated British Airways and navigated via the Executive Dashboard link. Browser displayed completed baseline, 750 prompts, Active organization British Airways, OpenRouter captured outputs and Coverage 100.0% (2250/2250); no empty-demo warning. Screenshot: .tmp/british-airways-live-dashboard.png. Verification script: .tmp/verify_live_workspace.py. The user's existing tab was not directly controlled; it needs reconnection to the restarted server, and may need workspace re-selection. Earlier AppTests did not verify the already-running server; this check does.
