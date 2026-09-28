param([Parameter(Mandatory=$true)][string]$Name)

$src = Join-Path "incomings" $Name
$zip = "$src.zip"

if (-not (Test-Path $src) -and (Test-Path $zip)) {
    Expand-Archive -Path $zip -DestinationPath $src -Force
}
if (-not (Test-Path $src)) {
    Write-Error "Not found: $src (or $zip)"; exit 1
}

Copy-Item -Path "$src\*" -Destination . -Recurse -Force
Remove-Item $src -Recurse -Force
if (Test-Path $zip) { Remove-Item $zip -Force }
Write-Host "Applied $Name"