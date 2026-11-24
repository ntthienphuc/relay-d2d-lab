$ErrorActionPreference = 'Stop'
$root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$source = Join-Path $root 'outputs\relay_presentation\Relay_D2D_Thuyet_trinh.pptx'
$renderDir = Join-Path $PSScriptRoot 'powerpoint_renders'
New-Item -ItemType Directory -Force -Path $renderDir | Out-Null
$existingIds = @(Get-Process POWERPNT -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id)
$ppt = New-Object -ComObject PowerPoint.Application
$deck = $null
try {
    $deck = $ppt.Presentations.Open($source, -1, 0, 0)
    $deck.Export($renderDir, 'PNG', 1280, 720)
    [PSCustomObject]@{slides=$deck.Slides.Count; rendered=(Get-ChildItem -LiteralPath $renderDir -Filter '*.PNG').Count; source=$source} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'powerpoint_check.json') -Encoding utf8
    Write-Output "PowerPoint opened read-only and exported $($deck.Slides.Count) slides."
} finally {
    if ($null -ne $deck) { $deck.Close(); [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($deck) }
    if ($existingIds.Count -eq 0 -and $ppt.Presentations.Count -eq 0) { $ppt.Quit() }
    [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($ppt)
}
