[CmdletBinding()]
param(
    [ValidateSet('all', 'bci_iv_2a', 'cho2017', 'mmidb')][string]$Dataset = 'all',
    [int[]]$Subjects,
    [string]$Profile,
    [string]$Python,
    [switch]$SkipDownload
)
$ErrorActionPreference = 'Stop'
$ProjectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Set-Location -LiteralPath $ProjectRoot
if (-not $Python) { $Python = Join-Path $ProjectRoot '.venv/Scripts/python.exe' }
$Python = [IO.Path]::GetFullPath($Python)
$Arguments = @('-I', '-S', '-B', 'tools/migration/rebuild.py', '--dataset', $Dataset, '--python', $Python)
if ($Subjects) { $Arguments += '--subjects'; $Arguments += @($Subjects | ForEach-Object { [string]$_ }) }
if ($Profile) { $Arguments += @('--profile', $Profile) }
if ($SkipDownload) { $Arguments += '--skip-download' }
& $Python @Arguments
if ($LASTEXITCODE -ne 0) { throw "Verified rebuild failed with exit code $LASTEXITCODE" }
