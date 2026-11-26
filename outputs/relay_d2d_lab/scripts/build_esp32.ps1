param([string]$ArduinoCli = '', [string]$Port = '', [switch]$Upload,
      [ValidateSet('devkit','cam')][string]$Board = 'devkit')
$ErrorActionPreference = 'Stop'
$labRoot = Split-Path $PSScriptRoot -Parent
if (-not $ArduinoCli) {
    $found = Get-Command arduino-cli -ErrorAction SilentlyContinue
    if ($found) { $ArduinoCli = $found.Source }
    else { $ArduinoCli = Join-Path $labRoot '..\..\work\tools\arduino-cli\arduino-cli.exe' }
}
if (-not (Test-Path -LiteralPath $ArduinoCli)) { throw 'Install Arduino CLI, then pass -ArduinoCli with its path. See esp32/README.md.' }
$sketch = Join-Path $labRoot 'esp32\RelayBox'
$outputDir = Join-Path $labRoot 'esp32\build'
$buildDir = Join-Path $labRoot '.build\esp32'
$fqbn = 'esp32:esp32:esp32'
if ($Board -eq 'cam') {
    $fqbn = 'esp32:esp32:esp32cam:FlashMode=dio,FlashFreq=40'
    $outputDir = Join-Path $outputDir 'cam'
    $buildDir = Join-Path $labRoot '.build\esp32-cam'
}
& $ArduinoCli compile --fqbn $fqbn --jobs 4 --build-path $buildDir --output-dir $outputDir $sketch
if ($LASTEXITCODE) { throw 'ESP32 compile failed' }
if ($Upload) {
    if (-not $Port) { throw 'Specify the confirmed ESP32 USB port, e.g. -Port COM4 -Upload' }
    & $ArduinoCli upload --fqbn $fqbn --port $Port --input-dir $outputDir $sketch
    if ($LASTEXITCODE) { throw 'ESP32 upload failed' }
}
Write-Host "ESP32 build complete: $outputDir"
