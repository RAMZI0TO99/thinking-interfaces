[CmdletBinding()]
param(
    [string]$Python,
    [switch]$CoreOnly,
    [switch]$SkipInstall,
    [switch]$SkipHistory,
    [switch]$DownloadWeights,
    [switch]$RestoreData
)
$ErrorActionPreference = 'Stop'
$ProjectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Set-Location -LiteralPath $ProjectRoot
if (-not $Python) {
    if (Get-Command py.exe -ErrorAction SilentlyContinue) {
        $Python = (& py.exe -3.12 -I -S -c 'import sys; print(sys.executable)' | Select-Object -Last 1)
    } else {
        $Python = (Get-Command python.exe -ErrorAction Stop).Source
    }
}
$Python = [IO.Path]::GetFullPath($Python.Trim())
$PythonVersion = & $Python -I -S -c 'import struct,sys; print(str(sys.version_info[0])+chr(46)+str(sys.version_info[1])+chr(58)+str(struct.calcsize(chr(80))*8))'
if ($LASTEXITCODE -ne 0 -or $PythonVersion -ne '3.12:64') {
    throw 'Install 64-bit Python 3.12 and pass -Python C:\path\to\python.exe.'
}
function Invoke-Checked([string[]]$Arguments) {
    & $Python @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Setup command failed with exit code $LASTEXITCODE" }
}
Invoke-Checked @('-I', '-S', '-B', 'tools/migration/restore.py', 'normalize')
$VenvPython = Join-Path $ProjectRoot '.venv/Scripts/python.exe'
if (-not $SkipInstall) {
    if (-not (Test-Path -LiteralPath $VenvPython)) {
        Invoke-Checked @('-I', '-S', '-B', 'tools/migration/guard.py', '--purpose', 'create isolated Python 3.12 environment', '--', $Python, '-I', '-B', '-m', 'venv', '.venv')
    }
    $Lock = if ($CoreOnly) { 'tools/migration/requirements-windows-core.lock' } else { 'tools/migration/requirements-windows-full.lock' }
    Invoke-Checked @('-I', '-S', '-B', 'tools/migration/guard.py', '--purpose', "install pinned Windows dependencies from $Lock", '--', $VenvPython, '-I', '-B', '-X', 'faulthandler', '-m', 'pip', '--isolated', '--disable-pip-version-check', 'install', '--no-index', '--no-deps', '--require-hashes', '--only-binary=:all:', '--no-compile', '-r', $Lock)
    Invoke-Checked @('-I', '-S', '-B', 'tools/migration/guard.py', '--purpose', 'install project entry points', '--', $VenvPython, '-I', '-B', '-m', 'pip', '--isolated', '--disable-pip-version-check', 'install', '--no-deps', '--no-build-isolation', '-e', '.')
    Invoke-Checked @('-I', '-S', '-B', 'tools/migration/guard.py', '--purpose', 'verify dependency consistency', '--', $VenvPython, '-I', '-B', '-m', 'pip', 'check')
    $ImportProfile = if ($CoreOnly) { 'core' } else { 'full' }
    Invoke-Checked @('-I', '-S', '-B', 'tools/migration/guard.py', '--purpose', 'verify installed runtime imports without loading a model', '--', $VenvPython, '-I', '-B', 'tools/migration/doctor.py', '--imports', $ImportProfile)
}
if (-not $SkipHistory) {
    $HistoryManifest = Get-Content -LiteralPath 'evidence/portable-20261012-v2/manifest.json' -Raw | ConvertFrom-Json
    foreach ($HistoryPart in $HistoryManifest.parts) {
        $PartName = [IO.Path]::GetFileName($HistoryPart.path)
        Invoke-Checked @('-I', '-S', '-B', 'tools/migration/guard.py', '--purpose', "download or verify inert history archive part $PartName", '--', $Python, '-I', '-S', '-B', 'tools/migration/restore.py', 'history-part', '--part', $PartName)
    }
    Invoke-Checked @('-I', '-S', '-B', 'tools/migration/guard.py', '--purpose', 'restore and verify inert historical evidence from locally verified parts', '--', $Python, '-I', '-S', '-B', 'tools/migration/restore.py', 'history', '--local-parts-only')
}
if ($DownloadWeights) {
    Invoke-Checked @('-I', '-S', '-B', 'tools/migration/guard.py', '--purpose', 'download exact public checkpoint bytes without loading models', '--', $Python, '-I', '-S', '-B', 'tools/migration/restore.py', 'fetch', '--dataset', 'weights')
}
if ($RestoreData) {
    if ($CoreOnly) { throw 'Data reconstruction requires the full environment.' }
    Invoke-Checked @('-I', '-S', '-B', 'tools/migration/rebuild.py', '--dataset', 'all', '--python', $Python)
}
Invoke-Checked @('-I', '-S', '-B', 'tools/migration/doctor.py')
Write-Host 'Setup completed. Read CONTINUE_HERE.md before launching experiments.'
