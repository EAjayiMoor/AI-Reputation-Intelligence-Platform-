param(
    [string]$ImageTag,
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$deployScript = Join-Path $PSScriptRoot "deploy_clean.ps1"
if (-not (Test-Path $deployScript)) {
    throw "Missing deploy script: $deployScript"
}

Write-Host "Starting Azure deploy with robust clean-context flow..." -ForegroundColor Cyan

$args = @()
if ($ImageTag) {
    $args += @("-ImageTag", $ImageTag)
}
if ($SkipBuild) {
    $args += "-SkipBuild"
}

& $deployScript @args

Write-Host "Done." -ForegroundColor Green
