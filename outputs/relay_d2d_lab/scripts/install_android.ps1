param(
  [Parameter(Mandatory=$true)][string]$Serial,
  [ValidateSet('source','relay','sink')][string]$Role = 'sink',
  [string]$Server = ''
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
if (-not $Server) { $Server = (Invoke-RestMethod 'http://127.0.0.1:8765/api/status').server_ip }
$apkFile = Join-Path $projectRoot 'android\build\relaylab.apk'
& adb -s $Serial install -r $apkFile
if ($LASTEXITCODE) { throw 'ADB install failed. Check USB debugging authorization.' }
& adb -s $Serial shell am force-stop vn.relaylab
& adb -s $Serial shell am start -W -f 0x10008000 -a android.intent.action.MAIN -c android.intent.category.LAUNCHER -n vn.relaylab/.MainActivity --es server $Server --es role $Role --ez auto true
if ($LASTEXITCODE) { throw 'Android launch failed' }
Write-Host "Started Relay Lab as $Role. Keep the app visible and connect the phone to the lab Wi-Fi."
