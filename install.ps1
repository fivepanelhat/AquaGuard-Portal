# AquaGuard-Portal - dual-platform installer (Windows / PowerShell)
# One-line: irm https://raw.githubusercontent.com/fivepanelhat/AquaGuard-Portal/main/install.ps1 | iex
# From clone: powershell -ExecutionPolicy Bypass -File .\install.ps1

$ErrorActionPreference = "Stop"

$RepoUrl = if ($env:PORTAL_REPO_URL) { $env:PORTAL_REPO_URL } else { "https://github.com/fivepanelhat/AquaGuard-Portal.git" }
$InstallDir = if ($env:PORTAL_HOME) { $env:PORTAL_HOME } else { Join-Path $env:USERPROFILE ".aquaguard-portal-app" }

function Info($m) { Write-Host "[aquaguard-portal] $m" -ForegroundColor Cyan }
function Warn($m) { Write-Host "[aquaguard-portal] $m" -ForegroundColor Yellow }
function Fail($m) { Write-Host "[aquaguard-portal] $m" -ForegroundColor Red; exit 1 }
function Require-Ok([string]$Step) {
 if ($null -ne $LASTEXITCODE -and $LASTEXITCODE -ne 0) { Fail "$Step failed (exit code $LASTEXITCODE)" }
}

$PythonBin = $null
foreach ($cand in @("python", "python3", "py")) {
 if (Get-Command $cand -ErrorAction SilentlyContinue) { $PythonBin = $cand; break }
}
if (-not $PythonBin) {
 Fail "Python 3.10+ is required. Install from https://www.python.org (Add to PATH) and re-run."
}
$PyVer = & $PythonBin -c "import sys; print('%d.%d' % sys.version_info[:2])"
& $PythonBin -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"
if ($LASTEXITCODE -ne 0) { Fail "Python 3.10+ required (found $PyVer)" }
Info "Using Python $PyVer ($PythonBin)"

if ((Test-Path "bootstrap.py") -and ((Test-Path "requirements.txt") -or (Test-Path "setup.py") -or (Test-Path "pyproject.toml"))) {
 $SrcDir = (Get-Location).Path
 Info "Installing from current checkout: $SrcDir"
} else {
 if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
 Fail "git is required. Install Git for Windows from https://git-scm.com or run from a clone."
 }
 New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
 $SrcDir = Join-Path $InstallDir "src"
 if (Test-Path (Join-Path $SrcDir ".git")) {
 Info "Updating existing checkout in $SrcDir"
 git -C $SrcDir pull --ff-only 2>$null
 } else {
 Info "Cloning $RepoUrl"
 git clone --depth 1 $RepoUrl $SrcDir
 Require-Ok "git clone"
 }
}

Set-Location $SrcDir
Info "Running bootstrap.py"
& $PythonBin bootstrap.py --portal-only
Require-Ok "bootstrap.py"
Write-Host ""
Info "Done. Activate: .\venv\Scripts\Activate.ps1"
