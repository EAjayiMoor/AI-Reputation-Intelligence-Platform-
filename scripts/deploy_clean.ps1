param(
    [string]$ResourceGroup = "RG-DEMO-UKW",
    [string]$AppName = "holdingapp2",
    [string]$AcrName = "crmhcdemo",
    [string]$ImageName = "holdingapp2",
    [string]$ImageTag,
    [switch]$SkipBuild,
    [switch]$DryRun,
    [switch]$KeepBuildContext
)

$ErrorActionPreference = "Stop"
if ($PSVersionTable.PSVersion.Major -ge 7) { $PSNativeCommandUseErrorActionPreference = $false }

function Invoke-LoggedCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,
        [Parameter(Mandatory = $true)]
        [string[]]$Args,
        [string]$WorkingDirectory
    )

    $cmdLine = "$Name $($Args -join ' ')"
    if ($WorkingDirectory) {
        Write-Host "[$WorkingDirectory] $cmdLine" -ForegroundColor DarkGray
    } else {
        Write-Host $cmdLine -ForegroundColor DarkGray
    }

    if ($DryRun) {
        return
    }

    if ($WorkingDirectory) {
        Push-Location $WorkingDirectory
    }

    try {
        & $Name @Args
        if ($LASTEXITCODE -ne 0) {
            throw "Command failed with exit code ${LASTEXITCODE}: $cmdLine"
        }
    } finally {
        if ($WorkingDirectory) {
            Pop-Location
        }
    }
}

if (-not $ImageTag) {
    $ImageTag = Get-Date -Format "yyyyMMddHHmmss"
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$tempContext = Join-Path $env:TEMP "holdingapp2-deploy-$ImageTag"

Write-Host "Using image tag: $ImageTag" -ForegroundColor Cyan
Write-Host "Repository root: $repoRoot" -ForegroundColor Cyan
Write-Host "Build context: $tempContext" -ForegroundColor Cyan
Write-Host "Skip build: $SkipBuild" -ForegroundColor Cyan
Write-Host "Dry run: $DryRun" -ForegroundColor Cyan

if (-not $DryRun) {
    if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
        throw "Azure CLI (az) is not installed or not on PATH."
    }
    Invoke-LoggedCommand -Name "az" -Args @("account", "show")
}

if (Test-Path -LiteralPath $tempContext) {
    Remove-Item -LiteralPath $tempContext -Recurse -Force
}

if (-not $DryRun) {
    New-Item -ItemType Directory -Path $tempContext -Force | Out-Null
}

$robocopyArgs = @(
    $repoRoot,
    $tempContext,
    "/E",
    "/NFL",
    "/NDL",
    "/NJH",
    "/NJS",
    "/NP",
    "/XD", ".git", ".venv", "venv", ".pytest_cache", "__pycache__", ".tmp", "tests", "docs", "scripts"
)

if ($DryRun) {
    Write-Host ("robocopy " + ($robocopyArgs -join " ")) -ForegroundColor DarkGray
} else {
    & robocopy @robocopyArgs | Out-Null
    $robocopyExit = $LASTEXITCODE
    if ($robocopyExit -gt 7) {
        throw "robocopy failed with exit code $robocopyExit while preparing build context."
    }
}

$containerImage = "$AcrName.azurecr.io/$ImageName`:$ImageTag"

if (-not $SkipBuild) {
    Write-Host "Building and pushing image to ACR..." -ForegroundColor Green
    Invoke-LoggedCommand -Name "az" -Args @("acr", "build", "-r", $AcrName, "-t", "$ImageName`:$ImageTag", ".") -WorkingDirectory $tempContext
} else {
    Write-Host "Skipping ACR build (using existing image tag)." -ForegroundColor Yellow
}

Write-Host "Enabling container CD..." -ForegroundColor Green
Invoke-LoggedCommand -Name "az" -Args @("webapp", "deployment", "container", "config", "--enable-cd", "true", "-g", $ResourceGroup, "-n", $AppName)

Write-Host "Updating App Service image: $containerImage" -ForegroundColor Green
Invoke-LoggedCommand -Name "az" -Args @("webapp", "config", "container", "set", "-g", $ResourceGroup, "-n", $AppName, "--container-image-name", $containerImage, "--container-registry-url", "https://$AcrName.azurecr.io")

Write-Host "Restarting App Service..." -ForegroundColor Green
Invoke-LoggedCommand -Name "az" -Args @("webapp", "restart", "-g", $ResourceGroup, "-n", $AppName)

Write-Host "Validating linuxFxVersion..." -ForegroundColor Green
$expectedFx = "DOCKER|$containerImage"
if ($DryRun) {
    Write-Host ("az webapp config show -g $ResourceGroup -n $AppName --query linuxFxVersion -o tsv") -ForegroundColor DarkGray
    Write-Host "Expected linuxFxVersion: $expectedFx" -ForegroundColor Cyan
} else {
    $actualFx = az webapp config show -g $ResourceGroup -n $AppName --query linuxFxVersion -o tsv
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to read linuxFxVersion after deployment."
    }
    if ($actualFx -ne $expectedFx) {
        throw "Validation failed. linuxFxVersion is '$actualFx' but expected '$expectedFx'."
    }
    Write-Host "linuxFxVersion validated: $actualFx" -ForegroundColor Cyan
}

if (-not $KeepBuildContext -and -not $DryRun) {
    Remove-Item -LiteralPath $tempContext -Recurse -Force
    Write-Host "Cleaned temporary build context." -ForegroundColor DarkGray
}

Write-Host "Deployment complete." -ForegroundColor Cyan
