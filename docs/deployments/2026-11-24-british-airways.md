# British Airways Azure release — 24 November 2026

Status: preparing; not yet deployed.

Scope: British Airways tenant and 750-prompt library; explicit completed-baseline default; recovery from stale empty-demo selection; Gemini response budget and truncation handling; opt-in bounded parallel execution and Windows checkpoint retry; regression tests and onboarding evidence. Source branch codex/demo-readiness. Pre-existing requirements.txt and scripts/deploy_latest.ps1 edits are excluded from the release commit.

Release order: finish repository tests, commit scoped changes, push branch, build immutable ACR image from that commit with locally verified dependency pins, transfer completed British Airways runtime run folders to persistent /home/airp/runs/british_airways, verify hashes, update existing holdingapp2 App Service, verify live workspace and Executive Dashboard in a real browser. Do not re-execute models. Secrets remain in existing App Service settings and are excluded from Git/build context. Runtime outputs remain outside Git and the image.

Target: RG-DEMO-UKW / holdingapp2, registry crmhcdemo. Existing image for rollback: crmhcdemo.azurecr.io/holdingapp2:20261030122046-demo-0360ec7. Persistent settings verified: AIRP_RUNS_DIR=/home/airp/runs, WEBSITES_ENABLE_APP_SERVICE_STORAGE=true, WEBSITES_PORT=8501. Existing tenants/runs must remain intact. If health or dashboard validation fails, restore previous image and report outcome.

Validation: local full-suite results pending; previous focused run 46 passing tests and live local browser baseline coverage 2250/2250. Deployment verification must separately establish the hosted behaviour. Same-agent review only; no independent review claimed.
