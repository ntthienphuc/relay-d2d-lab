$ErrorActionPreference = 'Continue'
$labRoot = Split-Path $PSScriptRoot -Parent
Write-Host 'Relay Lab 2.5 - local preflight'
foreach ($relative in @('.venv\Scripts\python.exe','android\build\relaylab.apk','esp32\build\cam\RelayBox.ino.bin','web\vendor\three.module.js')) {
    Write-Host (('{0,-8} {1}' -f $(if (Test-Path (Join-Path $labRoot $relative)) {'READY'} else {'MISSING'}),$relative))
}
try {
    $s=Invoke-RestMethod http://127.0.0.1:8765/api/preflight -TimeoutSec 3
    Write-Host "Server $($s.version) at http://$($s.server_ip):8765"
    $s.devices | Select-Object id,model,role,platform,online,local_ip,bridge_id,pending_events,queue_lost | Format-Table
} catch { Write-Host 'Server not reachable. Run START_LAB.cmd first.' }
if (Get-Command adb -ErrorAction SilentlyContinue) { & adb devices -l }
Write-Host 'Android on router: enter laptop IP. Android sink on RelayBox: enter 192.168.50.1.'
Write-Host 'A compiled ESP32 binary does not establish radio, wiring or two-phone test success.'
