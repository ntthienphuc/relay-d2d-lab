$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$sdkRoot = if ($env:ANDROID_HOME) { $env:ANDROID_HOME } else { Join-Path $env:LOCALAPPDATA 'Android\Sdk' }
$jdkRoot = 'C:\Program Files\Java\jdk-21'
if ($env:JAVA_HOME -and (Test-Path (Join-Path $env:JAVA_HOME 'bin\javac.exe'))) { $jdkRoot = $env:JAVA_HOME }
$buildTools = Join-Path $sdkRoot 'build-tools\35.0.0'
$androidJar = Join-Path $sdkRoot 'platforms\android-35\android.jar'
$buildDir = Join-Path $projectRoot 'android\build'
New-Item -ItemType Directory -Force -Path $buildDir,(Join-Path $buildDir 'classes'),(Join-Path $buildDir 'dex') | Out-Null
function Assert-Exit { if ($LASTEXITCODE -ne 0) { throw "Build command failed: $LASTEXITCODE" } }
$sources = @(Get-ChildItem (Join-Path $projectRoot 'android\src') -Filter '*.java' -Recurse | ForEach-Object FullName)
& (Join-Path $jdkRoot 'bin\javac.exe') -encoding UTF-8 -source 8 -target 8 -classpath $androidJar -d (Join-Path $buildDir 'classes') $sources
Assert-Exit
$classFiles = @(Get-ChildItem (Join-Path $buildDir 'classes') -Filter '*.class' -Recurse | ForEach-Object FullName)
& (Join-Path $buildTools 'd8.bat') --lib $androidJar --min-api 26 --output (Join-Path $buildDir 'dex') $classFiles
Assert-Exit
& (Join-Path $buildTools 'aapt.exe') package -f -S (Join-Path $projectRoot 'android\res') -M (Join-Path $projectRoot 'android\AndroidManifest.xml') -I $androidJar -F (Join-Path $buildDir 'unsigned.apk')
Assert-Exit
Push-Location (Join-Path $buildDir 'dex')
try { & (Join-Path $buildTools 'aapt.exe') add (Join-Path $buildDir 'unsigned.apk') classes.dex; Assert-Exit } finally { Pop-Location }
& (Join-Path $buildTools 'zipalign.exe') -f 4 (Join-Path $buildDir 'unsigned.apk') (Join-Path $buildDir 'aligned.apk')
Assert-Exit
$keyPath = Join-Path $buildDir 'debug.keystore'
if (-not (Test-Path $keyPath)) {
  & (Join-Path $jdkRoot 'bin\keytool.exe') -genkeypair -keystore $keyPath -storepass android -keypass android -alias relaylab -keyalg RSA -keysize 2048 -validity 3650 -dname 'CN=RelayLab Local Demo'
  Assert-Exit
}
& (Join-Path $buildTools 'apksigner.bat') sign --ks $keyPath --ks-pass pass:android --key-pass pass:android --out (Join-Path $buildDir 'relaylab.apk') (Join-Path $buildDir 'aligned.apk')
Assert-Exit
& (Join-Path $buildTools 'apksigner.bat') verify (Join-Path $buildDir 'relaylab.apk')
Assert-Exit
Write-Output (Join-Path $buildDir 'relaylab.apk')
