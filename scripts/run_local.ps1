# scripts/run_local.ps1 - Start application locally
param()

$rootDir = Split-Path -Parent $PSScriptRoot

# .env laden
$envPath = Join-Path $rootDir ".env"
if (!(Test-Path $envPath)) {
    Write-Host "❌ No .env file found at $envPath" -ForegroundColor Red
    exit 1
}

Get-Content $envPath | ForEach-Object {
    $line = $_.Trim()
    if ($line -and !$line.StartsWith('#') -and $line -match '^([^=]+)=(.*)$') {
        Set-Item -Path "env:$($matches[1].Trim())" -Value $matches[2].Trim()
    }
}

# uv sync
uv sync --quiet
if ($LASTEXITCODE -ne 0) { exit 1 }

# App starten
Write-Host "🚀 Starting huABus..." -ForegroundColor Green
Set-Location (Join-Path $rootDir "huawei_solar_modbus_mqtt")
python -m bridge.main
