param([Parameter(Mandatory=$true)][ValidatePattern('^[a-f0-9]{64}$')][string]$PinsSha256)
$ErrorActionPreference = 'Stop'
$SelectorRun = $PSScriptRoot
$SelectorProject = 'D:\Aenv\pro3'
$SelectorPins = Join-Path $SelectorRun 'pins.json'
$SelectorOutput = Join-Path $SelectorRun 'validation_001'
if (Test-Path -LiteralPath $SelectorOutput) { throw 'Unused receipt/selector output required' }
if ((Get-FileHash -Algorithm SHA256 -LiteralPath $SelectorPins).Hash.ToLowerInvariant() -ne $PinsSha256) {
    throw 'Fresh receipt/selector pins changed'
}
$SelectorPython = Join-Path $SelectorProject '.venv\Scripts\python.exe'
& $SelectorPython -I -S -B (Join-Path $SelectorProject 'tools\migration\guard.py') `
    --purpose 'complete51 tensor receipt mocked boundaries and actual public selector checks on fabricated metadata only' `
    --seconds 600 --process-mib 2048 --job-mib 3072 `
    --pause-file 'D:\Aenv\pro2\WORK\resume-20261015-001\coordination\PRO2_REQUEST_PRO3_PAUSE.json' `
    -- $SelectorPython -I -S -B (Join-Path $SelectorRun 'validate.py') `
    --pins $SelectorPins --expect-pins $PinsSha256 --output $SelectorOutput
exit $LASTEXITCODE
