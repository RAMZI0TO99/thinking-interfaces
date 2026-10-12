# Dot-source this after bootstrap: . ./tools/migration/activate.ps1
$ProjectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$env:HF_HOME = Join-Path $ProjectRoot '.cache/huggingface'
$env:HF_HUB_OFFLINE = '1'
$env:MOABB_DOWNLOAD_PROVIDER = 'upstream'
$env:PYTHONDONTWRITEBYTECODE = '1'
foreach ($ThreadVariable in @('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'NUMEXPR_NUM_THREADS')) {
    [Environment]::SetEnvironmentVariable($ThreadVariable, '1', 'Process')
}
. (Join-Path $ProjectRoot '.venv/Scripts/Activate.ps1')
