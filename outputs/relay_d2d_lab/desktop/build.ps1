param(
    [Parameter(Mandatory)][string]$SdkRoot,
    [Parameter(Mandatory)][string]$RuntimeRoot,
    [Parameter(Mandatory)][string]$OutputRoot,
    [string]$InnoCompiler = 'C:\\Program Files (x86)\Inno Setup 6\ISCC.exe'
)
$ErrorActionPreference='Stop'
# SDK input is the unpacked Microsoft.Web.WebView2 1.0.2903.40 NuGet package.
# RuntimeRoot contains the Python 3.9 x64 runtime from the offline Relay Lab installer.
$demo=(Get-Item -LiteralPath $PSScriptRoot).Parent.FullName
$out=New-Item -ItemType Directory -Force -Path $OutputRoot
$bin=New-Item -ItemType Directory -Force -Path (Join-Path $out.FullName 'native')
$files=@('lib/net462/Microsoft.Web.WebView2.Core.dll','lib/net462/Microsoft.Web.WebView2.WinForms.dll','runtimes/win-x64/native/WebView2Loader.dll','LICENSE.txt','NOTICE.txt')
foreach($name in $files){Copy-Item -LiteralPath (Join-Path $SdkRoot $name) -Destination $bin.FullName}
$csc=Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
& $csc /nologo /target:winexe /platform:x64 /optimize+ /codepage:65001 "/out:$($bin.FullName)\RelayLab.exe" "/win32icon:$PSScriptRoot\relaylab.ico" /r:System.Windows.Forms.dll /r:System.Drawing.dll /r:System.Web.Extensions.dll "/r:$($bin.FullName)\Microsoft.Web.WebView2.WinForms.dll" "/r:$($bin.FullName)\Microsoft.Web.WebView2.Core.dll" (Join-Path $PSScriptRoot 'RelayLab.cs')
if($LASTEXITCODE){throw 'Cannot build RelayLab.exe'}
& $InnoCompiler "/DDemoSource=$demo" "/DRuntimeRoot=$((Resolve-Path -LiteralPath $RuntimeRoot).Path)" "/DHostRoot=$($bin.FullName)" "/DOutputRoot=$($out.FullName)" (Join-Path $PSScriptRoot 'relaylab.iss')
if($LASTEXITCODE){throw 'Cannot build the installer'}

