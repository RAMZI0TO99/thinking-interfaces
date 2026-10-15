param([Parameter(Mandatory=$true)][ValidatePattern('^[a-f0-9]{64}$')][string]$PinsSha256)
$ErrorActionPreference = 'Stop'
$TensorRun = $PSScriptRoot
$TensorProject = 'D:\Aenv\pro3'
$TensorPins = Join-Path $TensorRun 'pins_005.json'
$TensorOutput = Join-Path $TensorRun 'validation_005'
if (Test-Path -LiteralPath $TensorOutput) { throw 'Fresh unused tensor validation output required' }
if ((Get-FileHash -Algorithm SHA256 -LiteralPath $TensorPins).Hash.ToLowerInvariant() -ne $PinsSha256) {
    throw 'Fresh tensor qualification pins changed'
}
$TensorPython = Join-Path $TensorProject '.venv\Scripts\python.exe'
& $TensorPython -I -S -B (Join-Path $TensorProject 'tools\migration\guard.py') `
    --purpose 'strict tensor request/native receipt boundary qualification and untrained EEGNet fixture preparation only' `
    --seconds 600 --process-mib 2048 --job-mib 3072 `
    --pause-file 'D:\Aenv\pro2\WORK\resume-20261015-001\coordination\PRO2_REQUEST_PRO3_PAUSE.json' `
    -- $TensorPython -I -S -B (Join-Path $TensorRun 'validate_005.py') `
    --pins $TensorPins --expect-pins $PinsSha256 --output $TensorOutput
exit $LASTEXITCODE
