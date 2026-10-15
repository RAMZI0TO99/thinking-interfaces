param([Parameter(Mandatory=$true)][ValidatePattern('^[a-f0-9]{64}$')][string]$PinsSha256)
$ErrorActionPreference = 'Stop'
$LinearRun = $PSScriptRoot
$LinearProject = 'D:\Aenv\pro3'
$LinearPins = Join-Path $LinearRun 'pins.json'
$LinearOutput = Join-Path $LinearRun 'validation_001'
if (Test-Path -LiteralPath $LinearOutput) { throw 'Unused linear lineage output required' }
if ((Get-FileHash -Algorithm SHA256 -LiteralPath $LinearPins).Hash.ToLowerInvariant() -ne $PinsSha256) {
    throw 'Fresh linear lineage pins changed'
}
foreach ($LinearDay in @('20261007','20261012','20261013','20261015')) {
    $LinearPause = 'D:\Aenv\pro2\WORK\resume-' + $LinearDay + '-001\coordination\PRO2_REQUEST_PRO3_PAUSE.json'
    if (Test-Path -LiteralPath $LinearPause) { throw ('Genuine peer pause: ' + $LinearPause) }
}
$LinearPython = Join-Path $LinearProject '.venv\Scripts\python.exe'
$LinearChildCommand = @($LinearPython, '-I', '-S', '-B', (Join-Path $LinearRun 'child.py'),
    '--pins', $LinearPins, '--expect-pins', $PinsSha256, '--output', $LinearOutput)
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
$LinearDispatch = Join-Path $LinearRun 'dispatch_001.json'
$LinearDispatchResult = Join-Path $LinearRun 'dispatch_result_001.json'
if (Test-Path -LiteralPath $LinearDispatchResult) { throw 'Unused linear lineage dispatch result required' }
Write-LinearJsonOnce $LinearDispatch ([ordered]@{
    schema = 'cho51_linear_lineage_dispatch_v1'
    observed_utc = [DateTime]::UtcNow.ToString('o')
    pins_sha256 = $PinsSha256
    actual_gradient_updates = 102
    pretrained_baseline_loaded = $true
    cohort_lineage_verified = $false
    full_selector_verified = $false
    child_command = $LinearChildCommand
    expected_output = $LinearOutput
    scientific_admission = $false
})
$LinearArguments = @('-I', '-S', '-B', (Join-Path $LinearProject 'tools\migration\guard.py'),
    '--purpose', 'fresh synthetic pretrained linear lineage with two public folds and exactly 102 gradient updates, no study cells',
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
    schema = 'cho51_linear_lineage_dispatch_result_v1'
    observed_utc = [DateTime]::UtcNow.ToString('o')
    pins_sha256 = $PinsSha256
    actual_gradient_updates = 102
    pretrained_baseline_loaded = $true
    cohort_lineage_verified = $false
    full_selector_verified = $false
    native_directory = $LinearNative
    guard_exit_code = $LinearExit
    child_command = $LinearChildCommand
    expected_output = $LinearOutput
    scientific_admission = $false
})
exit $LinearExit
