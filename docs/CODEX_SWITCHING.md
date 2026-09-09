# Codex Provider Switching Runbook (OpenAI ↔ Foundry)

Use this guide to switch Codex quickly across **all projects** in VS Code.

## 1) Daily commands

- OpenAI mode:
  - `codex-openai`
- Foundry mode:
  - `codex-foundry`

## 2) Recovery/reset commands

- Reset OpenAI profile config:
  - `Reset-CodexOpenAI`
- Reset Foundry profile config:
  - `Reset-CodexFoundry`

## 3) Quick health checks

- Confirm active profile home:
  - `echo $env:CODEX_HOME`
- Confirm Codex CLI responds:
  - `codex --version`

## 4) One-time setup commands

- Set Foundry key (user-level env var):
  - `setx AZURE_OPENAI_API_KEY "YOUR_REAL_KEY"`
- Reopen terminal after `setx`.

## 5) File locations (global)

- PowerShell profile:
  - `notepad $PROFILE`
- OpenAI Codex config:
  - `notepad $HOME\.codex-openai\config.toml`
- Foundry Codex config:
  - `notepad $HOME\.codex-foundry\config.toml`
- Default Codex config (used when `CODEX_HOME` not set):
  - `notepad $HOME\.codex\config.toml`

## 6) Recommended operating pattern

- Use **OpenAI mode** when you want flexible model switching in UI.
- Use **Foundry mode** when you want a stable Azure setup.
- Avoid changing provider/model in Foundry UI unless intentional.
- If config drifts, run the reset command and relaunch the mode.

## 7) VS Code usage

- Use terminal profile **Codex OpenAI** for OpenAI work.
- Use terminal profile **Codex Foundry** for Foundry work.
- After switching mode, open a fresh terminal for that profile.

## 8) Apply to all projects

This is already global because it uses your user-level PowerShell profile and user-level Codex homes:

- `C:\Users\EmmanuelAjayi\.codex-openai`
- `C:\Users\EmmanuelAjayi\.codex-foundry`
- `C:\Users\EmmanuelAjayi\Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1`

Any repo you open in VS Code can use the same commands without reconfiguration.
