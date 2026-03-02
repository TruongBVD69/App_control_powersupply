param(
    [switch]$Dev
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python is not available in PATH."
}

if (-not (Test-Path ".venv")) {
    python -m venv .venv
}

$pythonExe = ".venv\\Scripts\\python.exe"
if (-not (Test-Path $pythonExe)) {
    throw "Failed to create .venv at .venv\\Scripts\\python.exe"
}

& $pythonExe -m pip install --upgrade pip

if ($Dev) {
    & $pythonExe -m pip install -r requirements-dev.txt
}
else {
    & $pythonExe -m pip install -r requirements.txt
}

Write-Host "Environment is ready. Activate with: .\\.venv\\Scripts\\Activate.ps1"
