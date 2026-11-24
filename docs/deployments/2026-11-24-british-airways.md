# British Airways Azure release — 24 November 2026

Status: deployed; hosted baseline verified with 2,250 saved responses.

Scope: British Airways tenant and 750-prompt library; explicit completed-baseline default; recovery from stale empty-demo selection; Gemini response budget and truncation handling; opt-in bounded parallel execution and Windows checkpoint retry; regression tests and onboarding evidence. Source branch codex/demo-readiness. Pre-existing requirements.txt and scripts/deploy_latest.ps1 edits are excluded from the release commit.

Release order: finish repository tests, commit scoped changes, push branch, build immutable ACR image from that commit with locally verified dependency pins, transfer completed British Airways runtime run folders to persistent /home/airp/runs/british_airways, verify hashes, update existing holdingapp2 App Service, verify live workspace and Executive Dashboard in a real browser. Do not re-execute models. Secrets remain in existing App Service settings and are excluded from Git/build context. Runtime outputs remain outside Git and the image.

Target: RG-DEMO-UKW / holdingapp2, registry crmhcdemo. Existing image for rollback: crmhcdemo.azurecr.io/holdingapp2:20261030122046-demo-0360ec7. Persistent settings verified: AIRP_RUNS_DIR=/home/airp/runs, WEBSITES_ENABLE_APP_SERVICE_STORAGE=true, WEBSITES_PORT=8501. Existing tenants/runs must remain intact. If health or dashboard validation fails, restore previous image and report outcome.

Validation: local full-suite results pending; previous focused run 46 passing tests and live local browser baseline coverage 2250/2250. Deployment verification must separately establish the hosted behaviour. Same-agent review only; no independent review claimed.

## Deployed and verified

- Code commit: ebb6dac2a9cb57f22b5493f5d4367823f5707adf, pushed to origin/codex/demo-readiness before the Azure build.
- Image: crmhcdemo.azurecr.io/holdingapp2:20261124165720-ba-ebb6dac.
- Image digest: sha256:e9ac1564cacbfa930a19ae81804c0a100f5319508e3afa5a87845472762c290b.
- App Service image configuration verified against that exact tag; persistent storage settings retained.
- Test command: .venv/Scripts/python.exe -m pytest -q -p no:cacheprovider. Result: 197 passed in 108.70 seconds.
- Build used a clean Git archive of the pushed code commit with explicit pins matching the tested runtime: Streamlit 1.60.0, pandas 3.0.5, Plotly 6.9.0, openpyxl 3.1.5, pytest 9.1.1. Pre-existing requirements.txt and deployment-wrapper working-tree edits were not included or changed.
- Transferred all three completed British Airways runs (baseline, pilot, Gemini retest): original source, prompts, results, manifest and attempts for each, 15 files total. No checkpoint backups, locks or scratch logs uploaded. Original pilot's known incomplete Gemini rows are retained as historical evidence; the full baseline uses the verified completeness fix.
- All 15 Azure persistent files matched local SHA-256 hashes before and after the App Service restart. Existing remote run folders were preserved. No live model requests made during deployment.
- First navigation/storage probes timed out during the container restart. Azure logs then confirmed the new image pulled and its startup probe succeeded at 17:01:37 UTC. Hosted Chromium verification subsequently opened British Airways from Start and Executive Dashboard showed Live baseline, Complete, 750 prompts and Coverage 100.0% (2250/2250), with no empty-demo warning. This verifies the hosted app, not just local tests.
- Live app: https://holdingapp2-fedbexbjdnbuchfs.ukwest-01.azurewebsites.net/Start

Rollback: configure App Service back to crmhcdemo.azurecr.io/holdingapp2:20261030122046-demo-0360ec7 and restart. Retain /home/airp/runs and current storage settings. The older app would not contain the British Airways registry profile, but runtime outputs remain preserved for redeployment.

Verification performed by the implementing agent; no independent review or user acceptance claimed. Runtime outputs remain outside Git. This documentation update follows deployment and does not alter the deployed application source.

