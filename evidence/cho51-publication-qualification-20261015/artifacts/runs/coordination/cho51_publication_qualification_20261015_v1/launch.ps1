param([Parameter(Mandatory=$true)][ValidatePattern('^[a-f0-9]{64}$')][string]$PinsSha256)
$ErrorActionPreference = 'Stop'
$PublicationRun = $PSScriptRoot
$PublicationProject = 'D:\Aenv\pro3'
$PublicationPins = Join-Path $PublicationRun 'pins.json'
$PublicationOutput = Join-Path $PublicationRun 'validation_001'
if (Test-Path -LiteralPath $PublicationOutput) { throw 'Fresh unused validation output required' }
if ((Get-FileHash -Algorithm SHA256 -LiteralPath $PublicationPins).Hash.ToLowerInvariant() -ne $PinsSha256) {
    throw 'Fresh publication pins changed'
}
$PublicationPython = Join-Path $PublicationProject '.venv\Scripts\python.exe'
& $PublicationPython -I -S -B (Join-Path $PublicationProject 'tools\migration\guard.py') `
    --purpose '51-target publication mocked-boundary and fabricated-byte qualification only' `
    --seconds 600 --process-mib 2048 --job-mib 3072 `
    --pause-file 'D:\Aenv\pro2\WORK\resume-20261015-001\coordination\PRO2_REQUEST_PRO3_PAUSE.json' `
    -- $PublicationPython -I -S -B (Join-Path $PublicationRun 'validate.py') `
    --pins $PublicationPins --expect-pins $PinsSha256 --output $PublicationOutput
exit $LASTEXITCODE
