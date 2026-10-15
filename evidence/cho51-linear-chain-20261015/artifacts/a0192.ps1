param(
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-f0-9]{64}$')][string]$PinsSha256,
    [Parameter(Mandatory=$true)][string]$RequestPath,
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-f0-9]{64}$')][string]$RequestSha256
)
$ErrorActionPreference = 'Stop'
$LinearRun = $PSScriptRoot
$LinearProject = 'D:\Aenv\pro3'
$LinearPins = Join-Path $LinearRun 'pins.json'
if ((Get-FileHash -Algorithm SHA256 -LiteralPath $LinearPins).Hash.ToLowerInvariant() -ne $PinsSha256) {
    throw 'Immutable generic bundle changed'
}
if (-not [System.IO.Path]::IsPathFullyQualified($RequestPath) -or
    [System.IO.Path]::GetFullPath($RequestPath) -ne $RequestPath -or
    (Get-Item -LiteralPath $RequestPath).Length -gt 1048576 -or
    (Get-FileHash -Algorithm SHA256 -LiteralPath $RequestPath).Hash.ToLowerInvariant() -ne $RequestSha256) {
    throw 'Direct independently pinned bounded request required'
}
$LinearRequest = Get-Content -LiteralPath $RequestPath -Raw | ConvertFrom-Json
$LinearIndex = [int]$LinearRequest.index
if ($LinearIndex -lt 1 -or $LinearIndex -gt 7) { throw 'Exact fragment index required' }
$LinearName = 'fragment_{0:d3}' -f $LinearIndex
if ($RequestPath -ne (Join-Path $LinearRun ('requests\' + $LinearName + '.json')) -or
    $LinearRequest.output_relative -ne ('fragments/' + $LinearName) -or
    $LinearRequest.pins_sha256 -ne $PinsSha256) {
    throw 'Exact sequential immutable request path and output required'
}
$LinearOutput = Join-Path $LinearRun ('fragments\' + $LinearName)
if (Test-Path -LiteralPath $LinearOutput) { throw 'Fragment output has already been used' }
foreach ($LinearDay in @('20261007','20261012','20261013','20261015')) {
    $LinearPause = 'D:\Aenv\pro2\WORK\resume-' + $LinearDay + '-001\coordination\PRO2_REQUEST_PRO3_PAUSE.json'
    if (Test-Path -LiteralPath $LinearPause) { throw ('Genuine peer pause: ' + $LinearPause) }
}
$LinearPython = Join-Path $LinearProject '.venv\Scripts\python.exe'
$LinearChildCommand = @($LinearPython, '-I', '-S', '-B', (Join-Path $LinearRun 'child.py'),
    '--pins', $LinearPins, '--expect-pins', $PinsSha256,
    '--request', $RequestPath, '--expect-request', $RequestSha256, '--output', $LinearOutput)
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
$LinearDispatch = Join-Path $LinearRun ('dispatch\' + $LinearName + '.json')
$LinearDispatchResult = Join-Path $LinearRun ('dispatch\' + $LinearName + '_result.json')
if (Test-Path -LiteralPath $LinearDispatchResult) { throw 'Fragment dispatch result already exists' }
Write-LinearJsonOnce $LinearDispatch ([ordered]@{
    schema = 'cho51_linear_chain_dispatch_v1'
    observed_utc = [DateTime]::UtcNow.ToString('o')
    pins_sha256 = $PinsSha256
    request_path = $RequestPath
    request_sha256 = $RequestSha256
    request_index = $LinearIndex
    mode = $LinearRequest.mode
    child_command = $LinearChildCommand
    expected_output = $LinearOutput
    scientific_admission = $false
})
$LinearArguments = @('-I', '-S', '-B', (Join-Path $LinearProject 'tools\migration\guard.py'),
    '--purpose', 'one independently pinned synthetic linear chain fragment, bounded public folds or fresh final source fit, no study cells',
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
    throw 'First guard line is not a direct native migration output'
}
Write-LinearJsonOnce $LinearDispatchResult ([ordered]@{
    schema = 'cho51_linear_chain_dispatch_result_v1'
    observed_utc = [DateTime]::UtcNow.ToString('o')
    pins_sha256 = $PinsSha256
    request_path = $RequestPath
    request_sha256 = $RequestSha256
    request_index = $LinearIndex
    mode = $LinearRequest.mode
    native_directory = $LinearNative
    guard_exit_code = $LinearExit
    child_command = $LinearChildCommand
    expected_output = $LinearOutput
    scientific_admission = $false
})
exit $LinearExit
