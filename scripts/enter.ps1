$ErrorActionPreference = 'Stop'
$taskProjectRoot = Split-Path -Parent $PSScriptRoot
$taskActivate = Join-Path $taskProjectRoot '.venv\Scripts\Activate.ps1'
if (-not (Test-Path -LiteralPath $taskActivate)) {
    throw 'The project .venv is missing. See README.md for setup.'
}
& $taskActivate
$env:Path = (Join-Path $taskProjectRoot '.venv\Scripts') + [IO.Path]::PathSeparator + (Join-Path $taskProjectRoot '.tools\Scripts') + [IO.Path]::PathSeparator + $env:Path
Set-Location -LiteralPath $taskProjectRoot
Write-Host ('Project Python: ' + (Get-Command python.exe).Source)
Write-Host 'Ready. Run: python scripts/check_env.py'
