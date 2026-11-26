$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
Set-Location -LiteralPath $projectRoot
if (-not (Test-Path '.venv\Scripts\python.exe')) { python -m venv .venv; if ($LASTEXITCODE) { throw 'venv failed' } }
$wheelFolder = Join-Path $projectRoot 'wheels'
$runtimeTag = & '.venv\Scripts\python.exe' -c "import sys,struct;print(str(sys.version_info.major)+'.'+str(sys.version_info.minor)+'-'+str(8*struct.calcsize('P')))"
if ($runtimeTag -eq '3.9-64' -and (Test-Path $wheelFolder)) {
    & '.venv\Scripts\python.exe' -m pip install --disable-pip-version-check --no-index --find-links $wheelFolder -r requirements.txt
} else {
    & '.venv\Scripts\python.exe' -m pip install -r requirements.txt
}
if ($LASTEXITCODE) { throw 'Python dependencies failed' }
if (-not (Test-Path 'web\vendor\three.module.js')) {
    npm.cmd ci
    if ($LASTEXITCODE) { throw 'npm failed' }
    New-Item -ItemType Directory -Force -Path 'web\vendor' | Out-Null
    Copy-Item -LiteralPath 'node_modules\three\build\three.module.js','node_modules\three\build\three.core.js' -Destination 'web\vendor'
    Copy-Item -LiteralPath 'node_modules\three\examples\jsm\controls\OrbitControls.js' -Destination 'web\vendor\OrbitControls.js'
}
Write-Host 'Setup complete. Run START_LAB.cmd'
