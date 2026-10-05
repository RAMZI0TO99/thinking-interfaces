[CmdletBinding()]
param(
    [string]$ProjectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..')),
    [Parameter(Mandatory)][string]$OutputDirectory,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$SourceSha256,
    [Parameter(Mandatory)][ValidateRange(1, 1000000)][int]$SourceFileCount,
    [Parameter(Mandatory)][string]$DeadlineUtc,
    [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}$')]
    [string]$PeerThreadId
)

# Prospective package construction only. No Python, runtime inventory, tests,
# process launch, Job, data/weight read, release or scientific admission occurs.
$ErrorActionPreference = 'Stop'
$taskDeadline = [DateTimeOffset]::MinValue
if ($DeadlineUtc -cnotmatch '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$' -or
    -not [DateTimeOffset]::TryParseExact($DeadlineUtc, "yyyy-MM-dd'T'HH:mm:ss'Z'",
        [Globalization.CultureInfo]::InvariantCulture,
        [Globalization.DateTimeStyles]::AssumeUniversal -bor
        [Globalization.DateTimeStyles]::AdjustToUniversal, [ref]$taskDeadline) -or
    $taskDeadline -eq [DateTimeOffset]::MinValue -or $taskDeadline -eq [DateTimeOffset]::MaxValue) {
    throw 'DeadlineUtc must be an exact finite UTC second in yyyy-MM-ddTHH:mm:ssZ format'
}

function Get-TaskBytesSha([byte[]]$Bytes) {
    $taskHasher = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($taskHasher.ComputeHash($Bytes))).Replace('-', '').ToLowerInvariant() }
    finally { $taskHasher.Dispose() }
}

# Native handles reject hard-link input aliases and short-name/other directory
# aliases as well as reparse paths. They do not create a process or a Job.
if (-not ('Pro3LabramPackagePathsV1' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;
using System.Text;
using Microsoft.Win32.SafeHandles;
public static class Pro3LabramPackagePathsV1 {
    [StructLayout(LayoutKind.Sequential)] public struct Info {
        public uint Attributes, CreationLow, CreationHigh, AccessLow, AccessHigh;
        public uint WriteLow, WriteHigh, Volume, SizeHigh, SizeLow, Links, IndexHigh, IndexLow;
    }
    [DllImport("kernel32.dll", SetLastError=true)]
    static extern bool GetFileInformationByHandle(SafeFileHandle h, out Info info);
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
    static extern uint GetFinalPathNameByHandle(SafeFileHandle h, StringBuilder path, uint size, uint flags);
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
    static extern SafeFileHandle CreateFile(string path, uint access, uint share, IntPtr security,
        uint disposition, uint flags, IntPtr template);
    public static Info Inspect(SafeFileHandle h) {
        Info result;
        if (!GetFileInformationByHandle(h, out result)) throw new Win32Exception(Marshal.GetLastWin32Error());
        return result;
    }
    public static string FinalPath(SafeFileHandle h) {
        var text = new StringBuilder(32768);
        uint count = GetFinalPathNameByHandle(h, text, (uint)text.Capacity, 0);
        if (count == 0 || count >= text.Capacity) throw new Win32Exception(Marshal.GetLastWin32Error());
        string result = text.ToString();
        if (!result.StartsWith(@"\\?\", StringComparison.Ordinal)) throw new InvalidOperationException("Local DOS path required");
        return result.Substring(4);
    }
    public static string DirectoryPath(string path) {
        using (var h = CreateFile(path, 0, 7, IntPtr.Zero, 3, 0x02000000, IntPtr.Zero)) {
            if (h.IsInvalid) throw new Win32Exception(Marshal.GetLastWin32Error());
            return FinalPath(h);
        }
    }
}
'@
}

function Assert-TaskOrdinaryPath([string]$Path, [bool]$Directory) {
    $taskFull = [IO.Path]::GetFullPath($Path)
    if ($taskFull -cnotmatch '^[A-Za-z]:\\' -or $taskFull.Length -gt 240) {
        throw 'Bounded absolute local DOS path required'
    }
    $taskLexical = $Path.Replace('/', '\').TrimEnd('\')
    if (-not $taskLexical.Equals($taskFull.TrimEnd('\'), [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Path must already be absolute and canonical; dot/relative aliases are refused'
    }
    $taskCursor = $taskFull
    while ($taskCursor) {
        if (Test-Path -LiteralPath $taskCursor) {
            $taskItem = Get-Item -LiteralPath $taskCursor -Force
            if ($taskItem.Attributes -band [IO.FileAttributes]::ReparsePoint) {
                throw "Reparse path refused: $taskCursor"
            }
        }
        $taskNext = [IO.Path]::GetDirectoryName($taskCursor)
        if ($taskNext -eq $taskCursor) { break }
        $taskCursor = $taskNext
    }
    if ($Directory) {
        if (-not (Test-Path -LiteralPath $taskFull -PathType Container) -or
            -not ([Pro3LabramPackagePathsV1]::DirectoryPath($taskFull)).TrimEnd('\').Equals(
                $taskFull.TrimEnd('\'), [StringComparison]::OrdinalIgnoreCase)) {
            throw 'Ordinary existing non-aliased directory required'
        }
    }
    return $taskFull.TrimEnd('\')
}

function Read-TaskStableBytes([string]$Path) {
    $taskFull = Assert-TaskOrdinaryPath $Path $false
    $taskFile = [IO.File]::Open($taskFull, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::Read)
    try {
        $taskBefore = [Pro3LabramPackagePathsV1]::Inspect($taskFile.SafeFileHandle)
        if ($taskBefore.Links -ne 1 -or $taskFile.Length -lt 1 -or $taskFile.Length -gt 2097152 -or
            ($taskBefore.Attributes -band 0x410) -ne 0 -or
            -not ([Pro3LabramPackagePathsV1]::FinalPath($taskFile.SafeFileHandle)).Equals(
                $taskFull, [StringComparison]::OrdinalIgnoreCase)) {
            throw 'Bounded ordinary single-link input required'
        }
        $taskBuffer = New-Object byte[] ([int]$taskFile.Length)
        $taskRead = 0
        while ($taskRead -lt $taskBuffer.Length) {
            $taskChunk = $taskFile.Read($taskBuffer, $taskRead, $taskBuffer.Length - $taskRead)
            if ($taskChunk -le 0) { throw 'Short descriptor read' }
            $taskRead += $taskChunk
        }
        $taskAfter = [Pro3LabramPackagePathsV1]::Inspect($taskFile.SafeFileHandle)
        # A legitimate read can update AccessLow/AccessHigh. They are not part
        # of immutable descriptor identity. Keep every other native field.
        if ($taskBefore.Attributes -ne $taskAfter.Attributes -or
            $taskBefore.CreationLow -ne $taskAfter.CreationLow -or
            $taskBefore.CreationHigh -ne $taskAfter.CreationHigh -or
            $taskBefore.WriteLow -ne $taskAfter.WriteLow -or
            $taskBefore.WriteHigh -ne $taskAfter.WriteHigh -or
            $taskBefore.Volume -ne $taskAfter.Volume -or
            $taskBefore.SizeHigh -ne $taskAfter.SizeHigh -or
            $taskBefore.SizeLow -ne $taskAfter.SizeLow -or
            $taskBefore.Links -ne $taskAfter.Links -or
            $taskBefore.IndexHigh -ne $taskAfter.IndexHigh -or
            $taskBefore.IndexLow -ne $taskAfter.IndexLow) {
            throw 'Input identity changed during descriptor read'
        }
        return ,$taskBuffer
    } finally { $taskFile.Dispose() }
}

function Write-TaskOnce([string]$Path, [byte[]]$Bytes) {
    [void](Assert-TaskOrdinaryPath ([IO.Path]::GetDirectoryName($Path)) $true)
    [void](Assert-TaskOrdinaryPath $Path $false)
    $taskFile = [IO.File]::Open($Path, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::Read)
    try { $taskFile.Write($Bytes, 0, $Bytes.Length); $taskFile.Flush($true) }
    finally { $taskFile.Dispose() }
}

$taskRoot = Assert-TaskOrdinaryPath $ProjectRoot $true
$taskCoordination = Assert-TaskOrdinaryPath (Join-Path $taskRoot 'runs/coordination') $true
$taskSource = Assert-TaskOrdinaryPath (Join-Path $taskCoordination 'first_case_supervision_20261004_v10') $true
$taskOutput = Assert-TaskOrdinaryPath $OutputDirectory $false
if ([IO.Path]::GetDirectoryName($taskOutput) -ine $taskCoordination -or
    [IO.Path]::GetFileName($taskOutput) -cnotmatch '^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$' -or
    (Test-Path -LiteralPath $taskOutput)) {
    throw 'Output must be a fresh ordinary direct child of runs/coordination with an ASCII basename <=64'
}
$taskBuilderBeforeSha = Get-TaskBytesSha (Read-TaskStableBytes $PSCommandPath)

# This is config_digest(asdict(CasePlan(...))): ordinal keys, compact JSON,
# UTF8 without a trailing newline. Repetition belongs in case_id, while the
# recorder cell identity deliberately omits repetition and attempts.
$taskCase = [ordered]@{
    dataset = 'cho2017'; method = 'labram_linear'; model_seed = 11
    repetition = 1; shots_per_class = 5; target_subject = 'subject_01'
}
$taskCaseCanonical = $taskCase | ConvertTo-Json -Compress
$taskCaseId = Get-TaskBytesSha ([Text.Encoding]::UTF8.GetBytes($taskCaseCanonical))
if ($taskCaseId -cne 'af0f24764e577f2223db4759582852aacc2b1b2b0b0a549f1d4b43f8f14998b5') {
    throw 'Native compact canonical CasePlan digest differs'
}
$taskOldSource = '62536382eb85a7626d6d45b110b688dbb374281d136733e75cf77301a4c77cf0'
$taskOldCase = 'd7036dc25b2b42c898f1588ed890c95fc1c137cb58cd2fb3327ba3a3ca652e29'
$taskOldPeer = '01a0f844-b0d8-79a0-89d7-a823ce1b8962'
if ($SourceSha256 -ceq $taskOldSource -or $PeerThreadId -ceq $taskOldPeer) {
    throw 'The successor cannot reuse the historical source or expired peer identity'
}
$taskExpected = [ordered]@{
    'Invoke-FirstCaseSupervisorV1.ps1' = '72e03974ac7140e0d823d1c9165dd0d81928b456efbdaed5ea48615fcd06dd8b'
    'Prepare-FirstCaseRuntimeV1.ps1' = 'b7f95393740186d3db1a79a7af4445fd877b6ae8e5c6772a084b6572539cf3a7'
    'parent.py' = '67889194aa04b7f83aaf9dcea3ff3532be701098931d41cc93f0bb69ae62b430'
    'child.py' = '80fa45115ba3809db5b4eda8bef3b400e214656050eb38612ae8d909941444eb'
    'design.json' = '79dc609e7bc111376ea69dbb3cd715fc91c35779620e0ae4424be88eeab648ec'
}
$taskChanges = [Collections.Generic.List[object]]::new()
function Add-TaskReplacement([string]$File, [string]$Id, [string]$Old, [string]$New, [int]$Count = 1) {
    # All five hash-pinned originals use LF only. Normalize replacement
    # literals, never original bytes, so Windows checkout newlines cannot
    # change exact multiline matching or introduce mixed line endings.
    $Old = $Old.Replace("`r`n", "`n")
    $New = $New.Replace("`r`n", "`n")
    if ($Old -ceq $New -or $Old.Length -eq 0 -or $New.Length -eq 0 -or
        $Old -match '[^\x00-\x7f]' -or $New -match '[^\x00-\x7f]') {
        throw 'Every substitution must be a nonempty different ASCII string'
    }
    $taskChanges.Add([pscustomobject]@{
        file = $File; id = $Id; old = $Old; new = $New; expected_count = $Count
    })
}
foreach ($taskName in @('parent.py', 'design.json', 'Invoke-FirstCaseSupervisorV1.ps1', 'Prepare-FirstCaseRuntimeV1.ps1')) {
    Add-TaskReplacement $taskName 'settled_source' $taskOldSource $SourceSha256
}
foreach ($taskName in @('parent.py', 'design.json')) {
    Add-TaskReplacement $taskName 'canonical_case_id' $taskOldCase $taskCaseId
}
foreach ($taskName in @('parent.py', 'design.json', 'Invoke-FirstCaseSupervisorV1.ps1')) {
    Add-TaskReplacement $taskName 'peer_thread' $taskOldPeer $PeerThreadId
}
foreach ($taskName in @('parent.py', 'design.json', 'Invoke-FirstCaseSupervisorV1.ps1')) {
    Add-TaskReplacement $taskName 'fixed_method' 'eegnet' 'labram_linear'
}
Add-TaskReplacement 'child.py' 'cli_and_caseplan_method' 'eegnet' 'labram_linear' 2
Add-TaskReplacement 'child.py' 'fixed_method_docstring' (
    'Fixed no-fit environment probe or first EEGNet CLI inside verified outer Job.') (
    'Fixed no-fit environment probe or LaBraM linear CLI inside verified outer Job.')
Add-TaskReplacement 'child.py' 'fresh_worker' 'cho-first-case-9d32' 'cho-labram-linear-20261005-v1'
Add-TaskReplacement 'parent.py' 'deadline' 'GLOBAL_DEADLINE = datetime(2026, 10, 4, 21, 0, 0, tzinfo=UTC)' (
    'GLOBAL_DEADLINE = datetime(' + (@($taskDeadline.Year, $taskDeadline.Month, $taskDeadline.Day,
        $taskDeadline.Hour, $taskDeadline.Minute, $taskDeadline.Second) -join ', ') + ', tzinfo=UTC)')
Add-TaskReplacement 'Invoke-FirstCaseSupervisorV1.ps1' 'deadline' '2026-10-04T21:00:00Z' $DeadlineUtc
Add-TaskReplacement 'design.json' 'deadline' '2026-10-04T21:00:00Z' $DeadlineUtc
Add-TaskReplacement 'design.json' 'release_deadline' '2026-10-04T21:00:00+00:00' ($DeadlineUtc.Replace('Z', '+00:00'))
Add-TaskReplacement 'parent.py' 'correct_process_aggregate_prose' (
    'Only stdlib supervisor outside 6GiB Job; entire numerical CLI inside') (
    'Stdlib supervisor outside 6GiB process/7.5GiB aggregate Job; numerical CLI inside')
Add-TaskReplacement 'parent.py' 'correct_completion_cap_prose' (
    'Exit0/candidate, unchanged exact witnesses, verified6GiB process+aggregate/emptyJob;') (
    'Exit0/candidate, exact witnesses, verified6GiB process/7.5GiB aggregate/emptyJob;')
Add-TaskReplacement 'design.json' 'source_count' '"source_file_count": 430' ('"source_file_count": ' + $SourceFileCount)
Add-TaskReplacement 'design.json' 'runtime_count_unmeasured' '"file_count_native_observed": 33' '"file_count_native_observed": null'
Add-TaskReplacement 'design.json' 'runtime_digest_unmeasured' (
    '"selected_native_digest": "1013164da89254b2930b5c63990edc1d34b4a07444e3bbace48f675d33cf0a41"') (
    '"selected_native_digest": null')
Add-TaskReplacement 'design.json' 'prospective_scope' '"state": "preparation_only_no_execution_release"' (
    '"state": "prospective_labram_linear_package_only_no_execution_release",' + "`r`n" +
    '  "checkpoint_pretraining_cohort_verified": false,' + "`r`n" +
    '  "runtime_and_environment_measured_for_this_package": false,' + "`r`n" +
    '  "execution_release_created": false,' + "`r`n" +
    '  "compatible_schema_semantics": "Legacy first_case v1 schemas identify a one-case contract; this package fixes LaBraM linear, not EEGNet.",'+ "`r`n" +
    '  "case_identity_semantics": "CasePlan case_id includes repetition; recorder cell identity excludes repetition and attempts."')
Add-TaskReplacement 'design.json' 'current_ownership' (
    '"python": "/root/execution_cli: parent.py, child.py, design.json"') (
    '"python": "/root/labram_package_builder: reproducible package from frozen originals"')
Add-TaskReplacement 'design.json' 'current_native_ownership' (
    '"native": "/root/first_case_native: Invoke-FirstCaseSupervisorV1.ps1, Prepare-FirstCaseRuntimeV1.ps1"') (
    '"native": "/root/labram_package_builder: native launcher and preparer substitutions"')
Add-TaskReplacement 'design.json' 'source_count_release_binding' (
    '"source_sha256",' + "`r`n" + '      "operations parent.py/child.py/design.json digests",') (
    '"source_sha256",' + "`r`n" + '      "source_file_count=' + $SourceFileCount + '",' + "`r`n" +
    '      "operations parent.py/child.py/design.json digests",')
Add-TaskReplacement 'parent.py' 'source_count_constant' ('EXPECTED_SOURCE = "' + $SourceSha256 + '"') (
    'EXPECTED_SOURCE = "' + $SourceSha256 + '"' + "`r`n" + 'EXPECTED_SOURCE_FILE_COUNT = ' + $SourceFileCount)
Add-TaskReplacement 'parent.py' 'release_count_binding' '"source_sha256": EXPECTED_SOURCE,' (
    '"source_sha256": EXPECTED_SOURCE,' + "`r`n" + '        "source_file_count": EXPECTED_SOURCE_FILE_COUNT,')
foreach ($taskStage in @('before', 'after')) {
    Add-TaskReplacement 'parent.py' ('source_' + $taskStage + '_count') (
        'source_' + $taskStage + ' = {"source_sha256": provenance.source_fingerprint(ROOT)}') (
        'source_' + $taskStage + ' = {' + "`r`n" +
        '            "source_sha256": provenance.source_fingerprint(ROOT),' + "`r`n" +
        '            "source_file_count": len(provenance.source_files(ROOT)),' + "`r`n" + '        }')
}
Add-TaskReplacement 'parent.py' 'source_count_admission' (
    'if source_before["source_sha256"] != EXPECTED_SOURCE:') (
    'if (' + "`r`n" + '            source_before["source_sha256"] != EXPECTED_SOURCE' + "`r`n" +
    '            or source_before["source_file_count"] != EXPECTED_SOURCE_FILE_COUNT' + "`r`n" + '        ):')
Add-TaskReplacement 'child.py' 'source_count_guard' (
    'or asdict(provenance.capture_source(ROOT)) != source_before') (
    'or asdict(provenance.capture_source(ROOT)) != source_before' + "`r`n" +
    '            or len(provenance.source_files(ROOT)) != ops.EXPECTED_SOURCE_FILE_COUNT')
Add-TaskReplacement 'Invoke-FirstCaseSupervisorV1.ps1' 'source_count_constant' (
    '$taskExpectedSource = ''' + $SourceSha256 + '''') (
    '$taskExpectedSource = ''' + $SourceSha256 + '''' + "`r`n" + '$taskExpectedSourceCount = ' + $SourceFileCount)
Add-TaskReplacement 'Invoke-FirstCaseSupervisorV1.ps1' 'plan_source_count' (
    'source_sha256 = $taskExpectedSource') (
    'source_sha256 = $taskExpectedSource' + "`r`n" + '        source_file_count = $taskExpectedSourceCount')
Add-TaskReplacement 'Invoke-FirstCaseSupervisorV1.ps1' 'runtime_declared_source_count' (
    '$taskRuntimePreparation.source_sha256 -cne $taskExpectedSource -or') (
    '$taskRuntimePreparation.source_sha256 -cne $taskExpectedSource -or' + "`r`n" +
    '    ($taskRuntimePreparation.source_file_count -isnot [int] -and $taskRuntimePreparation.source_file_count -isnot [long]) -or' + "`r`n" +
    '    $taskRuntimePreparation.source_file_count -ne $taskExpectedSourceCount -or' + "`r`n" +
    '    $taskRuntimePreparation.source_binding_is_declared_not_measured -isnot [bool] -or' + "`r`n" +
    '    $taskRuntimePreparation.source_binding_is_declared_not_measured -ne $true -or')
Add-TaskReplacement 'Invoke-FirstCaseSupervisorV1.ps1' 'release_source_count' (
    '$taskRelease.source_sha256 -cne $taskExpectedSource -or') (
    '$taskRelease.source_sha256 -cne $taskExpectedSource -or' + "`r`n" +
    '    ($taskRelease.source_file_count -isnot [int] -and $taskRelease.source_file_count -isnot [long]) -or' + "`r`n" +
    '    $taskRelease.source_file_count -ne $taskExpectedSourceCount -or')
Add-TaskReplacement 'Invoke-FirstCaseSupervisorV1.ps1' 'receipt_source_count' (
    '$taskParentReceipt.source_before.source_sha256 -cne $taskExpectedSource -or $taskParentReceipt.source_after.source_sha256 -cne $taskExpectedSource -or') (
    '$taskParentReceipt.source_before.source_sha256 -cne $taskExpectedSource -or $taskParentReceipt.source_after.source_sha256 -cne $taskExpectedSource -or' + "`r`n" +
    '        $taskParentReceipt.source_before.source_file_count -ne $taskExpectedSourceCount -or' + "`r`n" +
    '        $taskParentReceipt.source_after.source_file_count -ne $taskExpectedSourceCount -or')
Add-TaskReplacement 'Prepare-FirstCaseRuntimeV1.ps1' 'declared_source_count' (
    'source_sha256 = ''' + $SourceSha256 + '''') (
    'source_sha256 = ''' + $SourceSha256 + '''' + "`r`n" +
    '    source_file_count = ' + $SourceFileCount + "`r`n" +
    '    source_binding_is_declared_not_measured = $true')
Add-TaskReplacement 'Invoke-FirstCaseSupervisorV1.ps1' 'strict_case_container_strings' (
    "if (`$taskChildResult.result.case.dataset -cne 'cho2017' -or `$taskChildResult.result.case.method -cne 'labram_linear' -or") (
    "if (`$taskChildResult.result.case.dataset -cne 'cho2017' -or `$taskChildResult.result.case.method -cne 'labram_linear' -or" + "`r`n" +
    '            $taskChildResult.result -isnot [pscustomobject] -or' + "`r`n" +
    '            $taskChildResult.result.case -isnot [pscustomobject] -or' + "`r`n" +
    '            $taskChildResult.result.completion -isnot [pscustomobject] -or' + "`r`n" +
    '            @($taskChildResult.result.case.PSObject.Properties).Count -ne 6 -or' + "`r`n" +
    '            $taskChildResult.result.case.dataset -isnot [string] -or' + "`r`n" +
    '            $taskChildResult.result.case.method -isnot [string] -or' + "`r`n" +
    '            $taskChildResult.result.case.target_subject -isnot [string] -or')
$taskOldPredicateTail = '$taskChildResult.result.case.model_seed -ne 11 -or $taskChildResult.result.case.shots_per_class -ne 5 -or' + "`r`n" +
    '            $taskChildResult.result.case.repetition -ne 1 -or $taskChildResult.result.completion.measured_cases -ne 1)'
$taskNewPredicateTail = @'
($taskChildResult.result.case.model_seed -isnot [int] -and $taskChildResult.result.case.model_seed -isnot [long]) -or
            $taskChildResult.result.case.model_seed -ne 11 -or
            ($taskChildResult.result.case.shots_per_class -isnot [int] -and $taskChildResult.result.case.shots_per_class -isnot [long]) -or
            $taskChildResult.result.case.shots_per_class -ne 5 -or
            ($taskChildResult.result.case.repetition -isnot [int] -and $taskChildResult.result.case.repetition -isnot [long]) -or
            $taskChildResult.result.case.repetition -ne 1 -or
            ($taskChildResult.result.completion.measured -isnot [int] -and $taskChildResult.result.completion.measured -isnot [long]) -or
            $taskChildResult.result.completion.measured -ne 1)
'@
$taskNewPredicateTail = $taskNewPredicateTail.Replace("`r`n", "`n")
Add-TaskReplacement 'Invoke-FirstCaseSupervisorV1.ps1' 'strict_final_case_completion' $taskOldPredicateTail $taskNewPredicateTail

# Latin-1 maps bytes reversibly: untouched CRLF/BOM/final newline bytes survive.
$taskEncoding = [Text.Encoding]::GetEncoding(28591)
$taskImages = @{}
$taskRows = @()
$taskApplied = @()
foreach ($taskName in $taskExpected.Keys) {
    $taskBytes = Read-TaskStableBytes (Join-Path $taskSource $taskName)
    $taskBefore = Get-TaskBytesSha $taskBytes
    if ($taskBefore -cne $taskExpected[$taskName]) { throw "Frozen V10 artifact differs: $taskName" }
    $taskText = $taskEncoding.GetString($taskBytes)
    $taskFileChanges = @($taskChanges | Where-Object { $_.file -ceq $taskName })
    foreach ($taskChange in $taskFileChanges) {
        $taskCount = [regex]::Matches($taskText, [regex]::Escape($taskChange.old)).Count
        if ($taskCount -ne $taskChange.expected_count) { throw "Replacement count differs: $taskName / $($taskChange.id)" }
        $taskText = $taskText.Replace($taskChange.old, $taskChange.new)
        $taskApplied += [pscustomobject]@{
            file = $taskChange.file; id = $taskChange.id; old = $taskChange.old; new = $taskChange.new
            expected_count = $taskChange.expected_count; actual_count = $taskCount
        }
    }
    foreach ($taskStale in @($taskOldSource, $taskOldCase, $taskOldPeer, 'eegnet',
        '2026-10-04T21:00:00', 'measured_cases', 'cho-first-case-9d32',
        '"source_file_count": 430', '"file_count_native_observed": 33',
        '1013164da89254b2930b5c63990edc1d34b4a07444e3bbace48f675d33cf0a41')) {
        if ($taskText.Contains($taskStale)) { throw "Stale operational token remains: $taskName / $taskStale" }
    }
    $taskReverse = $taskText
    for ($taskIndex = $taskFileChanges.Count - 1; $taskIndex -ge 0; $taskIndex--) {
        $taskChange = $taskFileChanges[$taskIndex]
        if ([regex]::Matches($taskReverse, [regex]::Escape($taskChange.new)).Count -ne $taskChange.expected_count) {
            throw "Reverse replacement count differs: $taskName / $($taskChange.id)"
        }
        $taskReverse = $taskReverse.Replace($taskChange.new, $taskChange.old)
    }
    if ((Get-TaskBytesSha ($taskEncoding.GetBytes($taskReverse))) -cne $taskBefore) {
        throw "Reverse substitutions do not reconstruct original bytes: $taskName"
    }
    $taskNewBytes = $taskEncoding.GetBytes($taskText)
    $taskImages[$taskName] = $taskNewBytes
    $taskRows += [pscustomobject]@{
        file = $taskName; before_sha256 = $taskBefore; after_sha256 = Get-TaskBytesSha $taskNewBytes
        before_bytes = $taskBytes.Length; after_bytes = $taskNewBytes.Length
        replacement_count = $taskFileChanges.Count; reverse_substitution_reproduces_original_bytes = $true
    }
}
foreach ($taskName in $taskExpected.Keys) {
    if ((Get-TaskBytesSha (Read-TaskStableBytes (Join-Path $taskSource $taskName))) -cne $taskExpected[$taskName]) {
        throw "Frozen input changed before publication: $taskName"
    }
}
[void](Assert-TaskOrdinaryPath $taskCoordination $true)
New-Item -ItemType Directory -Path $taskOutput -ErrorAction Stop | Out-Null
foreach ($taskName in $taskExpected.Keys) {
    Write-TaskOnce (Join-Path $taskOutput $taskName) $taskImages[$taskName]
    if ((Get-TaskBytesSha (Read-TaskStableBytes (Join-Path $taskOutput $taskName))) -cne
        ($taskRows | Where-Object { $_.file -ceq $taskName }).after_sha256 -or
        (Get-TaskBytesSha (Read-TaskStableBytes (Join-Path $taskSource $taskName))) -cne $taskExpected[$taskName]) {
        throw "Input/output byte verification failed: $taskName"
    }
}
if ((Get-TaskBytesSha (Read-TaskStableBytes $PSCommandPath)) -cne $taskBuilderBeforeSha) {
    throw 'Builder bytes changed during construction; partial output is preserved'
}
$taskProvenance = [ordered]@{
    schema = 'pro3_labram_linear_package_build_v1'
    created_utc = [DateTimeOffset]::UtcNow.ToString('o')
    state = 'prospective_labram_linear_package_only_no_execution_release'
    source_package = 'runs/coordination/first_case_supervision_20261004_v10'
    builder_sha256 = $taskBuilderBeforeSha
    binding = [ordered]@{
        source_sha256 = $SourceSha256; source_file_count = $SourceFileCount
        deadline_utc = $DeadlineUtc; peer_thread = $PeerThreadId
        case = $taskCase; case_canonical_json = $taskCaseCanonical; case_id = $taskCaseId
        worker = 'cho-labram-linear-20261005-v1'
    }
    source_package_unchanged = $true; live_source_verified = $false
    runtime_record_copied = $false; runtime_measured = $false; environment_measured = $false
    checkpoint_pretraining_cohort_verified = $false
    unchanged_resource_and_time_policy = [ordered]@{
        process_memory_limit_bytes = 6442450944L; aggregate_job_memory_bytes = 8053063680L
        startup_ram_bytes = 10737418240L; active_ram_bytes = 4294967296L; disk_floor_bytes = 21474836480L
        inner_attempt_seconds = 480; inner_session_seconds = 520; outer_execute_seconds = 600
        outer_prepare_seconds = 120; cleanup_reserve_seconds = 20; analysis_child_cap_bytes = 5905580032L
    }
    compatibility = 'Legacy first_case v1 schemas and attempt bases retained; operational hashes and fixed LaBraM case distinguish this successor'
    deadline_scope = 'Finite package guard only; no compute lease, new autonomous window or execution authority'
    replacements = $taskApplied; artifacts = $taskRows
    release_created = $false; launcher_invoked = $false; python_invoked = $false
    training_invoked = $false; scientific_claims_made = 0
    gate_a_signed = $false; scientific_freeze_ratified = $false
}
Write-TaskOnce (Join-Path $taskOutput 'package_build_provenance.json') (
    [Text.UTF8Encoding]::new($false).GetBytes(($taskProvenance | ConvertTo-Json -Depth 16) + "`n"))
[pscustomobject]@{
    state = $taskProvenance.state; output_directory = $taskOutput
    artifact_count = $taskRows.Count; replacement_count = $taskApplied.Count
    case_id = $taskCaseId; release_created = $false
} | ConvertTo-Json
