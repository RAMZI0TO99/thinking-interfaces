param(
    [Parameter(Mandatory=$true)][ValidateSet('eegnet','labram_linear','labram_lora','labram_full')][string]$Method,
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-f0-9]{64}$')][string]$PinsSha256
)
$ErrorActionPreference = 'Stop'
$ProbeRun = $PSScriptRoot
$ProbeProject = 'D:\Aenv\pro3'
$ProbePins = Join-Path $ProbeRun 'pins.json'
$ProbeOutput = Join-Path $ProbeRun ('output_' + $Method + '_001')
if (Test-Path -LiteralPath $ProbeOutput) { throw 'Unused numerical method output required' }
if ((Get-FileHash -Algorithm SHA256 -LiteralPath $ProbePins).Hash.ToLowerInvariant() -ne $PinsSha256) {
    throw 'Fresh numerical probe pins changed'
}
$ProbePython = Join-Path $ProbeProject '.venv\Scripts\python.exe'
$ProbeChildCommand = @(
    $ProbePython, '-I', '-S', '-B', (Join-Path $ProbeRun 'child.py'),
    '--pins', $ProbePins, '--expect-pins', $PinsSha256,
    '--output', $ProbeOutput, '--method', $Method
)

function Write-ProbeJsonOnce([string]$Path, [object]$Value) {
    $ProbeStream = [System.IO.File]::Open($Path, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write, [System.IO.FileShare]::Read)
    try {
        $ProbeWriter = [System.IO.StreamWriter]::new($ProbeStream, [System.Text.UTF8Encoding]::new($false))
        try {
            $ProbeWriter.WriteLine(($Value | ConvertTo-Json -Depth 12))
            $ProbeWriter.Flush()
            $ProbeStream.Flush($true)
        } finally { $ProbeWriter.Dispose() }
    } finally { $ProbeStream.Dispose() }
}

$ProbeDispatch = Join-Path $ProbeRun ('dispatch_' + $Method + '_001.json')
$ProbeDispatchResult = Join-Path $ProbeRun ('dispatch_result_' + $Method + '_001.json')
if (Test-Path -LiteralPath $ProbeDispatchResult) { throw 'Unused numerical dispatch result required' }
Write-ProbeJsonOnce $ProbeDispatch ([ordered]@{
    schema = 'cho51_numerical_probe_dispatch_v1'
    observed_utc = [DateTime]::UtcNow.ToString('o')
    method = $Method
    pins_sha256 = $PinsSha256
    child_command = $ProbeChildCommand
    expected_output = $ProbeOutput
    scientific_admission = $false
})
$ProbeGuardArguments = @(
    '-I', '-S', '-B', (Join-Path $ProbeProject 'tools\migration\guard.py'),
    '--purpose', ('seeded synthetic numerical probe only: ' + $Method + ', two candidate rates and eight gradient steps, no study arrays or pretrained weights'),
    '--seconds', '300', '--process-mib', '2048', '--job-mib', '3072',
    '--pause-file', 'D:\Aenv\pro2\WORK\resume-20261015-001\coordination\PRO2_REQUEST_PRO3_PAUSE.json',
    '--'
) + $ProbeChildCommand
$ProbeGuardLines = @(& $ProbePython @ProbeGuardArguments)
$ProbeGuardExit = $LASTEXITCODE
foreach ($ProbeLine in $ProbeGuardLines) { Write-Output $ProbeLine }
if ($ProbeGuardLines.Count -lt 1) { throw 'Native guard returned no result directory' }
$ProbeNativeDirectory = [string]$ProbeGuardLines[0]
$ProbeNativeRoot = Join-Path $ProbeProject 'runs\migration'
if (-not [System.IO.Path]::IsPathFullyQualified($ProbeNativeDirectory) -or
    [System.IO.Path]::GetFullPath($ProbeNativeDirectory) -ne $ProbeNativeDirectory -or
    [System.IO.Path]::GetDirectoryName($ProbeNativeDirectory) -ne $ProbeNativeRoot -or
    [System.IO.Path]::GetFileName($ProbeNativeDirectory) -notmatch '^\d{8}T\d{6}Z_[a-f0-9]{10}$' -or
    -not (Test-Path -LiteralPath $ProbeNativeDirectory -PathType Container)) {
    throw 'First guard output line is not its direct native migration directory'
}
Write-ProbeJsonOnce $ProbeDispatchResult ([ordered]@{
    schema = 'cho51_numerical_probe_dispatch_result_v1'
    observed_utc = [DateTime]::UtcNow.ToString('o')
    method = $Method
    pins_sha256 = $PinsSha256
    native_directory = $ProbeNativeDirectory
    guard_exit_code = $ProbeGuardExit
    child_command = $ProbeChildCommand
    expected_output = $ProbeOutput
    scientific_admission = $false
})
exit $ProbeGuardExit
