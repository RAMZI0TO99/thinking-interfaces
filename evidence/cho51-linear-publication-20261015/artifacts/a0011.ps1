param([Parameter(Mandatory=$true)][ValidateSet('publication','restoration')][string]$Mode, [Parameter(Mandatory=$true)][ValidatePattern('^[a-f0-9]{64}$')][string]$PinsSha256, [string]$PublicationResultSha256)
$ErrorActionPreference = 'Stop'
$LinearRun = $PSScriptRoot
$LinearProject = 'D:\Aenv\pro3'
$LinearPins = Join-Path $LinearRun 'pins.json'
$LinearOutput = Join-Path $LinearRun ($Mode + '_001')
$LinearPublicationResult = Join-Path $LinearRun 'publication_001\publication-result.json'
if ($Mode -eq 'restoration') {
    if ($PublicationResultSha256 -notmatch '^[a-f0-9]{64}$' -or (Get-FileHash -Algorithm SHA256 -LiteralPath $LinearPublicationResult).Hash.ToLowerInvariant() -ne $PublicationResultSha256) { throw 'Exact externally pinned publication result required' }
    if (-not (Test-Path -LiteralPath (Join-Path $LinearRun 'publication_001\stage-receipt.json'))) { throw 'Publication closeout receipt required first' }
} elseif ($PublicationResultSha256) { throw 'Publication accepts no predecessor result pin' }
if (Test-Path -LiteralPath $LinearOutput) { throw 'Unused linear staged publication output required' }
if ((Get-FileHash -Algorithm SHA256 -LiteralPath $LinearPins).Hash.ToLowerInvariant() -ne $PinsSha256) {
    throw 'Fresh linear staged publication pins changed'
}
foreach ($LinearDay in @('20261007','20261012','20261013','20261015')) {
    $LinearPause = 'D:\Aenv\pro2\WORK\resume-' + $LinearDay + '-001\coordination\PRO2_REQUEST_PRO3_PAUSE.json'
    if (Test-Path -LiteralPath $LinearPause) { throw ('Genuine peer pause: ' + $LinearPause) }
}
$LinearPython = Join-Path $LinearProject '.venv\Scripts\python.exe'
$LinearChildCommand = @($LinearPython, '-I', '-S', '-B', (Join-Path $LinearRun 'child.py'),
    '--mode', $Mode, '--pins', $LinearPins, '--expect-pins', $PinsSha256, '--output', $LinearOutput)
if ($Mode -eq 'restoration') { $LinearChildCommand += @('--publication-result', $LinearPublicationResult, '--expect-publication-result', $PublicationResultSha256) }
function Write-LinearJsonOnce([string]$Path, [object]$Value) {
    $LinearStream = [System.IO.File]::Open($Path, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write, [System.IO.FileShare]::Read)
    try {
        $LinearWriter = [System.IO.StreamWriter]::new($LinearStream, [System.Text.UTF8Encoding]::new($false))
        try {
            $LinearWriter.WriteLine(($Value | ConvertTo-Json -Depth 12))
            $LinearWriter.Flush()
            $LinearStream.Flush($true)
        } finally { $LinearWriter.Dispose() }
    } finally { $LinearStream.Dispose() }
}
$LinearDispatch = Join-Path $LinearRun ('dispatch_' + $Mode + '_001.json')
$LinearDispatchResult = Join-Path $LinearRun ('dispatch_result_' + $Mode + '_001.json')
if (Test-Path -LiteralPath $LinearDispatchResult) { throw 'Unused linear staged publication dispatch result required' }
Write-LinearJsonOnce $LinearDispatch ([ordered]@{
    schema = 'cho51_linear_publication_dispatch_v1'
    observed_utc = [DateTime]::UtcNow.ToString('o')
    pins_sha256 = $PinsSha256
    mode = $Mode
    publication_result_file_sha256 = $PublicationResultSha256
    actual_gradient_updates = 0
    pretrained_baseline_expected = $true
    cohort_lineage_verified = $false
    full_selector_verified = $false
    child_command = $LinearChildCommand
    expected_output = $LinearOutput
    scientific_admission = $false
})
$LinearArguments = @('-I', '-S', '-B', (Join-Path $LinearProject 'tools\migration\guard.py'),
    '--purpose', 'fresh synthetic zero-training linear source publication or detached store restoration, no study cells',
    '--seconds', '600', '--process-mib', '4096', '--job-mib', '5120',
    '--pause-file', 'D:\Aenv\pro2\WORK\resume-20261015-001\coordination\PRO2_REQUEST_PRO3_PAUSE.json', '--') + $LinearChildCommand
$LinearLines = @(& $LinearPython @LinearArguments)
$LinearExit = $LASTEXITCODE
foreach ($LinearLine in $LinearLines) { Write-Output $LinearLine }
if ($LinearLines.Count -lt 1) { throw 'Native guard returned no directory' }
$LinearNative = [string]$LinearLines[0]
$LinearNativeRoot = Join-Path $LinearProject 'runs\migration'
if (-not [System.IO.Path]::IsPathFullyQualified($LinearNative) -or
    [System.IO.Path]::GetFullPath($LinearNative) -ne $LinearNative -or
    [System.IO.Path]::GetDirectoryName($LinearNative) -ne $LinearNativeRoot -or
    [System.IO.Path]::GetFileName($LinearNative) -notmatch '^\d{8}T\d{6}Z_[a-f0-9]{10}$' -or
    -not (Test-Path -LiteralPath $LinearNative -PathType Container)) {
    throw 'First guard output line is not a direct migration result directory'
}
Write-LinearJsonOnce $LinearDispatchResult ([ordered]@{
    schema = 'cho51_linear_publication_dispatch_result_v1'
    observed_utc = [DateTime]::UtcNow.ToString('o')
    pins_sha256 = $PinsSha256
    mode = $Mode
    publication_result_file_sha256 = $PublicationResultSha256
    actual_gradient_updates = 0
    pretrained_baseline_expected = $true
    cohort_lineage_verified = $false
    full_selector_verified = $false
    native_directory = $LinearNative
    guard_exit_code = $LinearExit
    child_command = $LinearChildCommand
    expected_output = $LinearOutput
    scientific_admission = $false
})
exit $LinearExit
