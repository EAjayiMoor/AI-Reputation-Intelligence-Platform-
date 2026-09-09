param(
    [string]$ResourceGroup = "RG-DEMO-UKW",
    [string]$AppName = "holdingapp2",
    [string]$AcrName = "crmhcdemo",
    [string]$ImageName = "holdingapp2",
    [string]$ImageTag,
    [string]$RegistryUrl,
    [string]$RegistryUsername,
    [string]$RegistryPassword
)

$ErrorActionPreference = "Stop"

function Normalize-RegistryUrl {
    param([string]$InputUrl)

    if ([string]::IsNullOrWhiteSpace($InputUrl)) {
        return $InputUrl
    }

    $trimmed = $InputUrl.Trim()

    $markdownPattern = '^\[(https?://[^\]]+)\]\(https?://[^\)]+\)$'
    if ($trimmed -match $markdownPattern) {
        return $Matches[1]
    }

    return $trimmed
}

if (-not $ImageTag) {
    $ImageTag = Get-Date -Format "yyyyMMdd-HHmmss"
}

if (-not $RegistryUrl) {
    $RegistryUrl = "https://$AcrName.azurecr.io"
}

$RegistryUrl = Normalize-RegistryUrl -InputUrl $RegistryUrl

if ($RegistryUrl -notmatch '^https://[a-zA-Z0-9.-]+$') {
    throw "Invalid container registry URL: '$RegistryUrl'. Use plain URL format like https://crmhcdemo.azurecr.io"
}

if (($RegistryUsername -and -not $RegistryPassword) -or (-not $RegistryUsername -and $RegistryPassword)) {
    throw "Provide both -RegistryUsername and -RegistryPassword together, or provide neither."
}

Write-Host "Using image tag: $ImageTag" -ForegroundColor Cyan
Write-Host "Using registry URL: $RegistryUrl" -ForegroundColor Cyan

if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    throw "Azure CLI (az) is not installed or not on PATH. Install it first, then rerun this script."
}

az account show 1>$null 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "You are not logged into Azure CLI. Running az login..." -ForegroundColor Yellow
    az login
}

Write-Host "Enabling container continuous deployment..." -ForegroundColor Green
az webapp deployment container config --enable-cd true -g $ResourceGroup -n $AppName

Write-Host "Building and pushing image to ACR..." -ForegroundColor Green
az acr build -r $AcrName -t "$ImageName`:$ImageTag" .

$containerImage = "$AcrName.azurecr.io/$ImageName`:$ImageTag"
Write-Host "Pointing App Service to image: $containerImage" -ForegroundColor Green

$containerSetArgs = @(
    "webapp", "config", "container", "set",
    "-g", $ResourceGroup,
    "-n", $AppName,
    "--container-image-name", $containerImage,
    "--container-registry-url", $RegistryUrl
)

if ($RegistryUsername -and $RegistryPassword) {
    $containerSetArgs += @("--container-registry-user", $RegistryUsername)
    $containerSetArgs += @("--container-registry-password", $RegistryPassword)
}

& az @containerSetArgs
if ($LASTEXITCODE -ne 0) {
    throw "Failed to update web app container configuration."
}

Write-Host "Normalizing key app settings to avoid malformed values..." -ForegroundColor Green
az webapp config appsettings set -g $ResourceGroup -n $AppName --settings "DOCKER_REGISTRY_SERVER_URL=$RegistryUrl" "DOCKER_CUSTOM_IMAGE_NAME=DOCKER|$containerImage" 1>$null

Write-Host "Restarting App Service..." -ForegroundColor Green
az webapp restart -g $ResourceGroup -n $AppName

Write-Host "Configured container:" -ForegroundColor Green
$containerConfig = az webapp config container show -g $ResourceGroup -n $AppName | ConvertFrom-Json
$containerConfig

if ($containerConfig.DOCKER_REGISTRY_SERVER_URL -ne $RegistryUrl) {
    throw "Validation failed: DOCKER_REGISTRY_SERVER_URL is '$($containerConfig.DOCKER_REGISTRY_SERVER_URL)', expected '$RegistryUrl'."
}

if ($containerConfig.DOCKER_CUSTOM_IMAGE_NAME -ne "DOCKER|$containerImage") {
    throw "Validation failed: DOCKER_CUSTOM_IMAGE_NAME is '$($containerConfig.DOCKER_CUSTOM_IMAGE_NAME)', expected 'DOCKER|$containerImage'."
}

Write-Host "Deployment complete and settings validated." -ForegroundColor Cyan
