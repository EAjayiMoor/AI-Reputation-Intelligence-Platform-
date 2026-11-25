# Microsite download repair — 25 November 2026

Status: deployed and verified with repeated hosted ZIP downloads and Range requests.

User reported Chrome “Site wasn't available” downloading microsite ZIPs. Reproduced on Azure twice: /media/<hash>.zip returned HTTP 500, browser download failed with canceled and hash filename, while page had no Streamlit exception. Azure logs: streamlit's starlette_gzip_middleware emitted http.response.body without http.response.start. Build log confirms starlette 1.10.0 was installed as an unconstrained transitive dependency; local tested environment has 1.3.1.

Root-cause regression: exercised the actual Streamlit MediaAwareGZipMiddleware using an isolated temporary starlette 1.10.0 install; tests failed for gzip and identity because the first message was body instead of response headers. This isolates HTTP delivery from report generation. Plan: pin compatible 1.3.1 in constraints.txt and make Docker pip installation enforce it; test download headers/body and ZIP integrity plus existing export tests; push reviewed code, build/deploy immutable image, verify two complete hosted downloads and a Range request and all British Airways stored-data hashes. Preserve unrelated requirements.txt and deployment wrapper edits. No model calls or dataset changes.

Acceptance: normal and resumed ZIP responses begin with correct HTTP headers; downloaded bytes form a valid ZIP with readable report; repeat downloads work; hosted dashboard retains 2250/2250 coverage. Single-agent implementation and self-review. Skills: existing debugging, test-driven-development, verification-before-completion, karpathy-guidelines and installed developing-with-streamlit skill. Small-fix AI SDLC path, no runtime-AI evaluation required for HTTP delivery. See docs/deployments/2026-11-24-british-airways.md for environment and rollback conventions.

Local verification: isolated Starlette 1.10.0 ZIP transport tests failed as expected (http.response.body sent before headers). Compatible 1.3.1 passes compressed/uncompressed response tests. Full suite: .venv/Scripts/python.exe -m pytest -q -p no:cacheprovider — 201 passed in 105.85 seconds. Existing archive-generation tests passed. Pending hosted download and range verification after deployment; no success claimed yet.

## Deployed and verified

- Source commit 7696696e5368e59c631fc8772ebf4782360ff286 pushed to origin/codex/demo-readiness before build.
- Image crmhcdemo.azurecr.io/holdingapp2:20261125160144-download-7696696; digest sha256:61c9685d74f09e574dd1021601717e7b0ad49e467832baadb0585d0af3923b96.
- Docker build log confirms starlette 1.3.1 alongside Streamlit 1.60.0. constraints.txt is consumed by Docker's pip installation, preventing a future unconstrained rebuild from reintroducing 1.10.0.
- App Service container configuration matched release image; existing persistent storage settings retained. Azure reported a transient VNET setup failure during restart, then image/container startup succeeded and the startup probe passed at 16:06:00 UTC. No rollback required.
- Real hosted Chromium journey: Start → British Airways → Microsite Export. Repeated the rendered ZIP download twice. Both completed with failure=None, HTTP 200 and correct british_airways_rendered_microsite_<timestamp>.zip suggested filename. Each saved ZIP opened, passed testzip() and contained microsite/index.html with British Airways text.
- Browser HTTP Range request bytes=0-63 returned status 206, Content-Range bytes 0-63/18293 and exactly 64 bytes, for both repeated downloads. No Streamlit page exceptions.
- All 15 previously verified British Airways persistent run files retained identical SHA-256 hashes after deployment. No data files or model outputs modified. No live model calls.
- Verification scripts/logs retained locally under .tmp/verify_azure_microsite_fixed.py, .tmp/azure-build-20261125160144-download-7696696.log and .tmp/azure-download-release.json. Downloaded reproduction/verification files are scratch artifacts, not additional shipped reports.
- Before-fix browser error and isolated middleware regression, full 201-test suite, clean committed-image build and after-fix hosted download verification establish the fix. Self-review only, no independent review or user acceptance claimed.

Rollback image: crmhcdemo.azurecr.io/holdingapp2:20261124165720-ba-ebb6dac (known to have this download defect with its bundled dependency). Preserve persistent run storage if rolling back. Preferred recovery is the constrained image above. Existing unrelated local requirements.txt and scripts/deploy_latest.ps1 changes were preserved and excluded from this release.

Follow-up: any future Streamlit/Starlette upgrade must pass download transport tests plus real hosted browser ZIP and Range verification; archive-generation-only tests did not catch this server-layer regression. No UI rerun changes were needed because the confirmed failure was HTTP transport, not a download-widget race.

