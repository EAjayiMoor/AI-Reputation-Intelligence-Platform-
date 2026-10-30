# Azure demo-readiness deployment — 30 October 2026

Live app: https://holdingapp2-fedbexbjdnbuchfs.ukwest-01.azurewebsites.net/

## Release identity

- App Service: `holdingapp2`, resource group `RG-DEMO-UKW`.
- Source revision: `0360ec754cade634040308225f0c015d16a5ba5b` on `codex/demo-readiness`.
- Image: `crmhcdemo.azurecr.io/holdingapp2:20261030122046-demo-0360ec7`.
- Image digest: `sha256:5161acfd9418dd2310c611aadee0f863e11c68d96495c18d7b9577d0ba2b8fb4`.
- ACR build: `dc22`, Succeeded.
- Image configured at 12:26:58 UTC; final verification at 12:56:56 UTC.
- Previous image retained for rollback: `holdingapp2:20261006-comparator-1`.

The build context was a clean Git archive of the source revision. Local
credentials, uncommitted edits and uploaded run directories were not included.
The context's direct dependencies were pinned to the locally verified versions:
Streamlit 1.60.0, pandas 3.0.5, Plotly 6.9.0, openpyxl 3.1.5 and pytest 9.1.1.
The pre-existing local dependency-pin and deployment-wrapper edits were preserved.

## Run storage

Azure previously had persistent App Service storage disabled. The release sets:

```text
WEBSITES_ENABLE_APP_SERVICE_STORAGE=true
AIRP_RUNS_DIR=/home/airp/runs
WEBSITES_PORT=8501
```

The two approved banked demo snapshots were copied through authenticated Kudu
into `/home/airp/runs/southampton/`. Their original inputs, selected prompts,
results, manifests and attempt logs were verified against local SHA-256 hashes.
Existing folders are preserved rather than overwritten by a release copy.
The container's application user can create run folders and checkpoints there.
Existing OpenRouter credentials were retained without copying them into the image.

Run files are stored separately from Git and from the container image. Future
image updates must retain these app settings and the persistent home directory.
See [Microsoft's custom-container storage documentation](https://learn.microsoft.com/en-us/azure/app-service/configure-custom-container#use-persistent-shared-storage).

## Verification

- The public health endpoint responded successfully, and Azure's configured image
  matched the exact release tag.
- The four pre-existing workspace profiles matched the committed registry.
- The hosted Start page showed both dated demo cards, each with 50 prompts,
  five models and 250 saved responses.
- Careers displayed Southampton presence 41/250 and Manchester competitor
  presence 139/250. Research displayed Southampton presence 48/250 and Cambridge
  competitor presence 131/250, matching the verified local datasets.
- Uploaded a six-row, five-column deployment fixture through the hosted UI;
  created an isolated simulated run and selected one model.
- Simulation completed with six saved responses and zero failures. No paid
  OpenRouter calls were made during deployment verification.
- Restarted App Service after the simulation completed. All five simulation
  files had identical hashes after restart; the run reappeared as Complete in
  the hosted Run History.
- Both banked snapshots and a separate persistence marker also retained their
  hashes after deployment/restart (11 files verified).
- Archived the deployment-only simulation through Run History. Its six outputs
  and original input remain preserved; only its archive metadata changed.

Validation run: `20261030T124744_0a5473c1cc184dfcae9c40befc12b6b5`, named
`Azure storage validation - simulated` (archived).

## Remaining rehearsal scope

The smaller 18-prompt, three-model live client rehearsal is still outstanding.
This deployment verifies run persistence, not an independent backup/restore
procedure or concurrent multi-instance execution. Organisation profiles remain
in the application registry; persistence for newly created runtime profiles
was not changed by this release.
