param(
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-f0-9]{64}$')][string]$PinsSha256,
    [Parameter(Mandatory=$true)][ValidateSet('eegnet','labram_linear','labram_lora','labram_full')][string]$Method
)
$ErrorActionPreference = 'Stop'
$FoldRun = $PSScriptRoot
$FoldProject = 'D:\Aenv\pro3'
$FoldPins = Join-Path $FoldRun 'pins.json'
$FoldOutput = Join-Path $FoldRun ('output_' + $Method + '_001')
if (Test-Path -LiteralPath $FoldOutput) { throw 'Unused direct source-fold output required' }
if ((Get-FileHash -Algorithm SHA256 -LiteralPath $FoldPins).Hash.ToLowerInvariant() -ne $PinsSha256) {
    throw 'Fresh source-fold pins changed'
}
foreach ($FoldDay in @('20261007','20261012','20261013','20261015')) {
    $FoldPause = 'D:\Aenv\pro2\WORK\resume-' + $FoldDay + '-001\coordination\PRO2_REQUEST_PRO3_PAUSE.json'
    if (Test-Path -LiteralPath $FoldPause) { throw ('Genuine peer pause: ' + $FoldPause) }
}
$FoldPython = Join-Path $FoldProject '.venv\Scripts\python.exe'
$FoldChildCommand = @(
    $FoldPython, '-I', '-S', '-B', (Join-Path $FoldRun 'child.py'),
    '--pins', $FoldPins, '--expect-pins', $PinsSha256,
    '--output', $FoldOutput, '--method', $Method
)
function Write-FoldJsonOnce([string]$Path, [object]$Value) {
    $FoldStream = [System.IO.File]::Open($Path, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write, [System.IO.FileShare]::Read)
    try {
        $FoldWriter = [System.IO.StreamWriter]::new($FoldStream, [System.Text.UTF8Encoding]::new($false))
        try {
            $FoldWriter.WriteLine(($Value | ConvertTo-Json -Depth 12))
            $FoldWriter.Flush()
            $FoldStream.Flush($true)
        } finally { $FoldWriter.Dispose() }
    } finally { $FoldStream.Dispose() }
}
$FoldDispatch = Join-Path $FoldRun ('dispatch_' + $Method + '_001.json')
$FoldDispatchResult = Join-Path $FoldRun ('dispatch_result_' + $Method + '_001.json')
if (Test-Path -LiteralPath $FoldDispatchResult) { throw 'Unused source-fold dispatch result required' }
Write-FoldJsonOnce $FoldDispatch ([ordered]@{
    schema = 'cho51_source_fold_dispatch_v1'
    observed_utc = [DateTime]::UtcNow.ToString('o')
    pins_sha256 = $PinsSha256
    method = $Method
    child_command = $FoldChildCommand
    expected_output = $FoldOutput
    scientific_admission = $false
})
$FoldGuardArguments = @(
    '-I', '-S', '-B', (Join-Path $FoldProject 'tools\migration\guard.py'),
    '--purpose', 'standalone 51-update public source fold on isolated all52 synthetic subjects, one source candidate and one validation fold, no study inputs or measured cells',
    '--seconds', '600', '--process-mib', '4096', '--job-mib', '5120',
    '--pause-file', 'D:\Aenv\pro2\WORK\resume-20261015-001\coordination\PRO2_REQUEST_PRO3_PAUSE.json',
    '--'
) + $FoldChildCommand
$FoldGuardLines = @(& $FoldPython @FoldGuardArguments)
$FoldGuardExit = $LASTEXITCODE
foreach ($FoldLine in $FoldGuardLines) { Write-Output $FoldLine }
if ($FoldGuardLines.Count -lt 1) { throw 'Native guard returned no result directory' }
$FoldNativeDirectory = [string]$FoldGuardLines[0]
$FoldNativeRoot = Join-Path $FoldProject 'runs\migration'
if (-not [System.IO.Path]::IsPathFullyQualified($FoldNativeDirectory) -or
    [System.IO.Path]::GetFullPath($FoldNativeDirectory) -ne $FoldNativeDirectory -or
    [System.IO.Path]::GetDirectoryName($FoldNativeDirectory) -ne $FoldNativeRoot -or
    [System.IO.Path]::GetFileName($FoldNativeDirectory) -notmatch '^\d{8}T\d{6}Z_[a-f0-9]{10}$' -or
    -not (Test-Path -LiteralPath $FoldNativeDirectory -PathType Container)) {
    throw 'First guard output line is not its direct native migration directory'
}
Write-FoldJsonOnce $FoldDispatchResult ([ordered]@{
    schema = 'cho51_source_fold_dispatch_result_v1'
    observed_utc = [DateTime]::UtcNow.ToString('o')
    pins_sha256 = $PinsSha256
    method = $Method
    native_directory = $FoldNativeDirectory
    guard_exit_code = $FoldGuardExit
    child_command = $FoldChildCommand
    expected_output = $FoldOutput
    scientific_admission = $false
})
exit $FoldGuardExit
