[CmdletBinding()]
param([string]$Python)
$ErrorActionPreference = 'Stop'
$ProjectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Set-Location -LiteralPath $ProjectRoot
if (-not $Python) { $Python = Join-Path $ProjectRoot '.venv/Scripts/python.exe' }
& $Python -I -S -B tools/migration/guard.py --quality --seconds 4200 --purpose 'Fresh full implementation quality on this device; no scientific admission'
if ($LASTEXITCODE -ne 0) { throw "Guarded quality failed with exit code $LASTEXITCODE" }
