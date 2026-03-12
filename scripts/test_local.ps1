# scripts/test_local.ps1 - Run tests locally

param(
    [switch]$Shell,      # BATS Shell-Tests
    [switch]$Coverage,   # pytest + HTML Coverage
    [switch]$All         # Beide: BATS + pytest
)

$rootDir = Split-Path -Parent $PSScriptRoot

function ConvertTo-UnixPath([string]$WinPath) {
    $unix = $WinPath -replace "\\", "/"
    if ($unix -match "^([A-Za-z]):(.*)") {
        $unix = "/" + $Matches[1].ToLower() + $Matches[2]
    }
    return $unix
}

function Get-GitBash {
    $candidates = @(
        "C:\Program Files\Git\bin\bash.exe",
        "C:\Program Files (x86)\Git\bin\bash.exe"
    )
    $found = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
    if (!$found) {
        Write-Host "❌ Git Bash not found. Install Git for Windows!" -ForegroundColor Red
        exit 1
    }
    return $found
}

# uv sync
uv sync --all-extras --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Dependency sync failed!" -ForegroundColor Red
    exit 1
}

Push-Location $rootDir

# ===== BATS =====
if ($Shell -or $All) {
    $batsDir = Join-Path $rootDir ".tools\bats-core"
    $batsBin = Join-Path $batsDir "bin\bats"
    $batsLibDir = Join-Path $batsDir "lib"

    # Prüfen ob Clone vollständig (Datei + lib existieren)
    $batsReady = (Test-Path $batsBin) -and (!(Get-Item $batsBin).PSIsContainer) -and (Test-Path $batsLibDir)

    if (!$batsReady) {
        Write-Host "🗑️  Removing incomplete bats-core..." -ForegroundColor Yellow
        Remove-Item $batsDir -Recurse -Force -ErrorAction SilentlyContinue

        Write-Host "📦 Cloning bats-core..." -ForegroundColor Yellow
        git clone https://github.com/bats-core/bats-core.git $batsDir
        if ($LASTEXITCODE -ne 0) { Pop-Location; exit 1 }

        # CRLF-Fix nur für Textdateien
        Write-Host "🔧 Fixing line endings..." -ForegroundColor Yellow
        @("*.bash", "*.bats", "*.sh", "*.md") | ForEach-Object {
            Get-ChildItem $batsDir -Recurse -Filter $_ |
            Where-Object { $_.FullName -notlike "*\bin\bats" } |
            ForEach-Object {
                (Get-Content $_.FullName -Raw) -replace "`r`n", "`n" |
                Set-Content $_.FullName -NoNewline -Encoding UTF8
            }
        }
    }

    # Jetzt ausführen
    $batsBinUnix = ConvertTo-UnixPath $batsBin
    $gitBash = Get-GitBash
    Write-Host "🐚 Running BATS tests..." -ForegroundColor Cyan
    & "$gitBash" "$batsBinUnix" "tests/test_run.bats"

    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ BATS tests failed!" -ForegroundColor Red
        Pop-Location; exit $LASTEXITCODE
    }
    Write-Host "✅ BATS tests passed!" -ForegroundColor Green
}

# ===== PYTEST =====
if (!$Shell -or $All) {
    if ($Coverage) {
        Write-Host "🧪 Running pytest with coverage..." -ForegroundColor Cyan
        uv run pytest tests -v --cov=huawei_solar_modbus_mqtt/bridge --cov-report=html
        if ($LASTEXITCODE -eq 0) {
            Write-Host "📊 Opening coverage report..." -ForegroundColor Cyan
            Start-Process "htmlcov/index.html"
        }
    }
    else {
        Write-Host "🧪 Running pytest..." -ForegroundColor Cyan
        uv run pytest tests -v
    }

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ All tests passed!" -ForegroundColor Green
    }
    else {
        Write-Host "❌ Tests failed!" -ForegroundColor Red
    }
}

Pop-Location
exit $LASTEXITCODE
