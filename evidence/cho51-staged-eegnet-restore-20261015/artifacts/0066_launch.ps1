param([Parameter(Mandatory=$true)][ValidatePattern('^[a-f0-9]{64}$')][string]$PinsSha256)
$ErrorActionPreference = 'Stop'
$CompleteRun = $PSScriptRoot
$CompleteProject = 'D:\Aenv\pro3'
$CompletePins = Join-Path $CompleteRun 'pins.json'
$CompleteOutput = Join-Path $CompleteRun 'validation_001'
if (Test-Path -LiteralPath $CompleteOutput) { throw 'Unused complete EEGNet parent output required' }
if ((Get-FileHash -Algorithm SHA256 -LiteralPath $CompletePins).Hash.ToLowerInvariant() -ne $PinsSha256) {
    throw 'Fresh complete EEGNet pins changed'
}
foreach ($CompleteDay in @('20261007','20261012','20261013','20261015')) {
    $CompletePause = 'D:\Aenv\pro2\WORK\resume-' + $CompleteDay + '-001\coordination\PRO2_REQUEST_PRO3_PAUSE.json'
    if (Test-Path -LiteralPath $CompletePause) { throw ('Genuine peer pause: ' + $CompletePause) }
}
$CompletePython = Join-Path $CompleteProject '.venv\Scripts\python.exe'
$CompleteChildCommand = @($CompletePython, '-I', '-S', '-B', (Join-Path $CompleteRun 'parent.py'),
    '--pins', $CompletePins, '--expect-pins', $PinsSha256, '--output', $CompleteOutput)
function Write-CompleteJsonOnce([string]$Path, [object]$Value) {
    $CompleteStream = [System.IO.File]::Open($Path, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write, [System.IO.FileShare]::Read)
    try {
        $CompleteWriter = [System.IO.StreamWriter]::new($CompleteStream, [System.Text.UTF8Encoding]::new($false))
        try {
            $CompleteWriter.WriteLine(($Value | ConvertTo-Json -Depth 12))
            $CompleteWriter.Flush()
            $CompleteStream.Flush($true)
        } finally { $CompleteWriter.Dispose() }
    } finally { $CompleteStream.Dispose() }
}
$CompleteDispatch = Join-Path $CompleteRun 'dispatch_001.json'
$CompleteDispatchResult = Join-Path $CompleteRun 'dispatch_result_001.json'
if (Test-Path -LiteralPath $CompleteDispatchResult) { throw 'Unused complete EEGNet dispatch result required' }
Write-CompleteJsonOnce $CompleteDispatch ([ordered]@{
    schema = 'cho51_complete_eegnet_dispatch_v1'
    observed_utc = [DateTime]::UtcNow.ToString('o')
    pins_sha256 = $PinsSha256
    child_command = $CompleteChildCommand
    expected_output = $CompleteOutput
    scientific_admission = $false
})
$CompleteArguments = @('-I', '-S', '-B', (Join-Path $CompleteProject 'tools\migration\guard.py'),
    '--purpose', 'complete EEGNet synthetic engineering claim, 5253 public selector updates, publication and detached native verification, zero study cells',
    '--seconds', '600', '--process-mib', '4096', '--job-mib', '6144',
    '--pause-file', 'D:\Aenv\pro2\WORK\resume-20261015-001\coordination\PRO2_REQUEST_PRO3_PAUSE.json', '--') + $CompleteChildCommand
$CompleteLines = @(& $CompletePython @CompleteArguments)
$CompleteExit = $LASTEXITCODE
foreach ($CompleteLine in $CompleteLines) { Write-Output $CompleteLine }
if ($CompleteLines.Count -lt 1) { throw 'Native guard returned no directory' }
$CompleteNative = [string]$CompleteLines[0]
$CompleteNativeRoot = Join-Path $CompleteProject 'runs\migration'
if (-not [System.IO.Path]::IsPathFullyQualified($CompleteNative) -or
    [System.IO.Path]::GetFullPath($CompleteNative) -ne $CompleteNative -or
    [System.IO.Path]::GetDirectoryName($CompleteNative) -ne $CompleteNativeRoot -or
    [System.IO.Path]::GetFileName($CompleteNative) -notmatch '^\d{8}T\d{6}Z_[a-f0-9]{10}$' -or
    -not (Test-Path -LiteralPath $CompleteNative -PathType Container)) {
    throw 'First guard output line is not a direct migration result directory'
}
Write-CompleteJsonOnce $CompleteDispatchResult ([ordered]@{
    schema = 'cho51_complete_eegnet_dispatch_result_v1'
    observed_utc = [DateTime]::UtcNow.ToString('o')
    pins_sha256 = $PinsSha256
    native_directory = $CompleteNative
    guard_exit_code = $CompleteExit
    child_command = $CompleteChildCommand
    expected_output = $CompleteOutput
    scientific_admission = $false
})
exit $CompleteExit
