[CmdletBinding()]
param(
    [string]$ProjectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..')),
    [string]$OutputDirectory
)

# Reproduce a historical repair template. This script never launches it.
$ErrorActionPreference = 'Stop'
$taskRoot = [IO.Path]::GetFullPath($ProjectRoot)
$taskSource = Join-Path $taskRoot 'runs/coordination/first_case_supervision_20261004_v10'
if (-not $OutputDirectory) {
    $OutputDirectory = Join-Path $taskRoot 'runs/coordination/first_case_supervision_20261005_v11'
}
$taskOutput = [IO.Path]::GetFullPath($OutputDirectory)
$taskAllowed = [IO.Path]::GetFullPath((Join-Path $taskRoot 'runs/coordination')).TrimEnd('\') + '\'
if (-not $taskOutput.StartsWith($taskAllowed, [StringComparison]::OrdinalIgnoreCase) -or
    $taskOutput.Equals($taskSource, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Output must be a fresh directory beneath runs/coordination'
}
if (Test-Path -LiteralPath $taskOutput) { throw 'Output directory already exists; no overwrite allowed' }

function Get-TaskBytesSha([byte[]]$Bytes) {
    $taskHasher = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($taskHasher.ComputeHash($Bytes))).Replace('-', '').ToLowerInvariant() }
    finally { $taskHasher.Dispose() }
}

$taskExpected = [ordered]@{
    'Invoke-FirstCaseSupervisorV1.ps1' = '72e03974ac7140e0d823d1c9165dd0d81928b456efbdaed5ea48615fcd06dd8b'
    'Prepare-FirstCaseRuntimeV1.ps1' = 'b7f95393740186d3db1a79a7af4445fd877b6ae8e5c6772a084b6572539cf3a7'
    'parent.py' = '67889194aa04b7f83aaf9dcea3ff3532be701098931d41cc93f0bb69ae62b430'
    'child.py' = '80fa45115ba3809db5b4eda8bef3b400e214656050eb38612ae8d909941444eb'
    'design.json' = '79dc609e7bc111376ea69dbb3cd715fc91c35779620e0ae4424be88eeab648ec'
    'runtime_preparation_20261004.json' = 'ad86880703145b2229e12b98d33ea9da0509582387b87d696c6010e1e6cf6c60'
}
$taskChanges = @(
    [pscustomobject]@{ file = 'Invoke-FirstCaseSupervisorV1.ps1'; old = '$taskChildResult.result.completion.measured_cases'; new = '$taskChildResult.result.completion.measured' },
    [pscustomobject]@{ file = 'Invoke-FirstCaseSupervisorV1.ps1'; old = '2026-10-04T21:00:00Z'; new = '2026-10-05T10:00:00Z' },
    [pscustomobject]@{ file = 'parent.py'; old = 'GLOBAL_DEADLINE = datetime(2026, 10, 4, 21, 0, 0, tzinfo=UTC)'; new = 'GLOBAL_DEADLINE = datetime(2026, 10, 5, 10, 0, 0, tzinfo=UTC)' },
    [pscustomobject]@{ file = 'parent.py'; old = 'Only stdlib supervisor outside 6GiB Job; entire numerical CLI inside'; new = 'Stdlib supervisor outside 6GiB process/7.5GiB aggregate Job; numerical CLI inside' },
    [pscustomobject]@{ file = 'parent.py'; old = 'Exit0/candidate, unchanged exact witnesses, verified6GiB process+aggregate/emptyJob;'; new = 'Exit0/candidate, exact witnesses, verified6GiB process/7.5GiB aggregate/emptyJob;' },
    [pscustomobject]@{ file = 'design.json'; old = '"global_deadline_utc": "2026-10-04T21:00:00Z"'; new = '"global_deadline_utc": "2026-10-05T10:00:00Z"' },
    [pscustomobject]@{ file = 'design.json'; old = 'global_deadline_utc=2026-10-04T21:00:00+00:00'; new = 'global_deadline_utc=2026-10-05T10:00:00+00:00' }
)
# Latin-1 is a reversible byte mapping. All replacement strings are ASCII;
# untouched bytes, BOM state, line endings and final newlines are preserved.
$taskEncoding = [Text.Encoding]::GetEncoding(28591)
$taskImages = @{}
$taskRows = @()
foreach ($taskFile in $taskExpected.Keys) {
    $taskBytes = [IO.File]::ReadAllBytes((Join-Path $taskSource $taskFile))
    $taskBefore = Get-TaskBytesSha $taskBytes
    if ($taskBefore -cne $taskExpected[$taskFile]) { throw "Frozen V10 artifact differs: $taskFile" }
    $taskText = $taskEncoding.GetString($taskBytes)
    $taskFileChanges = @($taskChanges | Where-Object { $_.file -ceq $taskFile })
    foreach ($taskChange in $taskFileChanges) {
        if ([regex]::Matches($taskText, [regex]::Escape($taskChange.old)).Count -ne 1) {
            throw "Replacement must occur exactly once: $taskFile / $($taskChange.old)"
        }
        $taskText = $taskText.Replace($taskChange.old, $taskChange.new)
    }
    $taskNewBytes = $taskEncoding.GetBytes($taskText)
    $taskReverse = $taskText
    for ($taskIndex = $taskFileChanges.Count - 1; $taskIndex -ge 0; $taskIndex--) {
        $taskChange = $taskFileChanges[$taskIndex]
        if ([regex]::Matches($taskReverse, [regex]::Escape($taskChange.new)).Count -ne 1) {
            throw "Reverse replacement must occur exactly once: $taskFile"
        }
        $taskReverse = $taskReverse.Replace($taskChange.new, $taskChange.old)
    }
    if ((Get-TaskBytesSha ($taskEncoding.GetBytes($taskReverse))) -cne $taskBefore) {
        throw "Reverse substitution does not reconstruct frozen bytes: $taskFile"
    }
    $taskImages[$taskFile] = $taskNewBytes
    $taskRows += [pscustomobject]@{
        file = $taskFile; before_sha256 = $taskBefore; after_sha256 = Get-TaskBytesSha $taskNewBytes
        before_bytes = $taskBytes.Length; after_bytes = $taskNewBytes.Length
        replacement_count = $taskFileChanges.Count; reverse_substitution_reproduces_original_bytes = $true
    }
}
# Recheck all inputs before creating any output. There are no cleanup/deletion
# operations: an interrupted partial directory must be preserved and reviewed.
foreach ($taskFile in $taskExpected.Keys) {
    if ((Get-TaskBytesSha ([IO.File]::ReadAllBytes((Join-Path $taskSource $taskFile)))) -cne $taskExpected[$taskFile]) {
        throw "Frozen V10 artifact changed during preparation: $taskFile"
    }
}
New-Item -ItemType Directory -Path $taskOutput -ErrorAction Stop | Out-Null
foreach ($taskFile in $taskExpected.Keys) {
    [IO.File]::WriteAllBytes((Join-Path $taskOutput $taskFile), $taskImages[$taskFile])
    if ((Get-TaskBytesSha ([IO.File]::ReadAllBytes((Join-Path $taskOutput $taskFile)))) -cne
        ($taskRows | Where-Object { $_.file -ceq $taskFile }).after_sha256) {
        throw "Output byte verification failed: $taskFile"
    }
    if ((Get-TaskBytesSha ([IO.File]::ReadAllBytes((Join-Path $taskSource $taskFile)))) -cne $taskExpected[$taskFile]) {
        throw "Frozen V10 artifact changed during output: $taskFile"
    }
}
$taskProvenance = [ordered]@{
    schema = 'pro3_first_case_v11_template_build_v1'
    created_utc = [DateTimeOffset]::UtcNow.ToString('o')
    state = 'historical_baseline_repair_template_only_no_execution_release'
    source_package = 'runs/coordination/first_case_supervision_20261004_v10'
    builder_sha256 = Get-TaskBytesSha ([IO.File]::ReadAllBytes($PSCommandPath))
    baseline_source_sha256 = '62536382eb85a7626d6d45b110b688dbb374281d136733e75cf77301a4c77cf0'
    live_source_verified = $false
    runtime_record_reused_as_historical_template_only = $true
    phase_deadline_utc = '2026-10-05T10:00:00Z'
    deadline_scope = 'bounded repair staging only; not a compute lease or user expiry'
    source_package_unchanged = $true
    replacements = $taskChanges
    artifacts = $taskRows
    release_created = $false; launcher_invoked = $false; python_invoked = $false
    training_invoked = $false; scientific_claims_made = 0
    gate_a_signed = $false; scientific_freeze_ratified = $false
}
[IO.File]::WriteAllText((Join-Path $taskOutput 'v11_build_provenance.json'),
    ($taskProvenance | ConvertTo-Json -Depth 12) + "`n", [Text.UTF8Encoding]::new($false))
[pscustomobject]@{ state = $taskProvenance.state; output_directory = $taskOutput; artifact_count = $taskRows.Count; replacement_count = $taskChanges.Count } | ConvertTo-Json
