$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
Set-Location -LiteralPath $projectRoot
if (-not (Test-Path '.venv\Scripts\python.exe')) { python -m venv .venv; if ($LASTEXITCODE) { throw 'venv failed' } }
& '.venv\Scripts\python.exe' -m pip install -r requirements.txt
if ($LASTEXITCODE) { throw 'Python dependencies failed' }
if (-not (Test-Path 'web\vendor\three.module.js')) {
    npm.cmd ci
    if ($LASTEXITCODE) { throw 'npm failed' }
    New-Item -ItemType Directory -Force -Path 'web\vendor' | Out-Null
    Copy-Item -LiteralPath 'node_modules\three\build\three.module.js','node_modules\three\build\three.core.js' -Destination 'web\vendor'
    Copy-Item -LiteralPath 'node_modules\three\examples\jsm\controls\OrbitControls.js' -Destination 'web\vendor\OrbitControls.js'
}
Write-Host 'Setup complete. Run START_LAB.cmd'
