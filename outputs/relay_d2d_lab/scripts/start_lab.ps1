$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
Set-Location -LiteralPath $projectRoot
$pythonExe = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $pythonExe)) { throw 'Run scripts\setup.ps1 first to install the local environment.' }
$existing = $null
try { $existing = Invoke-RestMethod -Uri 'http://127.0.0.1:8765/api/status' -TimeoutSec 2 } catch {}
if ($existing.version -eq '2.6.1') {
    Write-Host "Relay Lab is already running at http://127.0.0.1:8765"
    Start-Process 'http://127.0.0.1:8765'
    exit 0
}
if ($existing) { throw 'An older Relay Lab is running on port 8765. Stop that server before launching Relay Lab 2.6.' }
Write-Host 'Relay Lab: http://127.0.0.1:8765 — Ctrl+C to stop'
& $pythonExe -m uvicorn lab.server:app --host 0.0.0.0 --port 8765 --no-access-log
