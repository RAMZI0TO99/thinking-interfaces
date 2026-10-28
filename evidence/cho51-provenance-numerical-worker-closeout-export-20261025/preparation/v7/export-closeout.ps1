param([Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$FinalReviewSha256)
$ErrorActionPreference = 'Stop'
$root = 'D:\Aenv\pro3'
$run = Join-Path $root 'runs\coordination\cho51_provenance_numerical_worker_20261025_v7'
$destination = Join-Path $root 'evidence\cho51-provenance-numerical-worker-closeout-export-20261025'
$utf8 = [Text.UTF8Encoding]::new($false, $true)
$proofPins = [Collections.Generic.Dictionary[string,string]]::new([StringComparer]::OrdinalIgnoreCase)
if (-not (Get-Command ConvertFrom-Json).Parameters.ContainsKey('DateKind')) { throw 'Explicit JSON date-string preservation requires PowerShell DateKind support' }
Add-Type -AssemblyName System.Text.Json
Add-Type -TypeDefinition @'
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;
using Microsoft.Win32.SafeHandles;
public static class Pro3ExportFileIdentity {
    [StructLayout(LayoutKind.Sequential)]
    public struct Info {
        public uint Attributes;
        public System.Runtime.InteropServices.ComTypes.FILETIME Creation, Access, Write;
        public uint Volume, SizeHigh, SizeLow, Links, IndexHigh, IndexLow;
    }
    [DllImport("kernel32.dll", SetLastError=true)]
    private static extern bool GetFileInformationByHandle(SafeFileHandle handle, out Info info);
    public static string Fingerprint(SafeFileHandle handle) {
        Info info;
        if (!GetFileInformationByHandle(handle, out info)) throw new Win32Exception(Marshal.GetLastWin32Error());
        if (info.Links != 1 || (info.Attributes & 0x410) != 0) throw new InvalidOperationException("Single-link regular direct file required");
        return String.Join(":", info.Volume, info.IndexHigh, info.IndexLow, info.SizeHigh, info.SizeLow,
            info.Creation.dwHighDateTime, info.Creation.dwLowDateTime, info.Write.dwHighDateTime, info.Write.dwLowDateTime);
    }
}
'@
function Get-Sha($path) {
    (Read-Bounded $path).sha256
}
function Write-New($path, [byte[]]$bytes) {
    $path = [IO.Path]::GetFullPath($path)
    if (-not $path.StartsWith($destination + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Export write escapes destination' }
    $parent = Split-Path -Parent $path
    $existing = $parent
    while (-not (Test-Path -LiteralPath $existing)) { $existing = Split-Path -Parent $existing }
    Assert-Direct $existing
    [IO.Directory]::CreateDirectory($parent) | Out-Null
    Assert-Direct $parent
    if (-not ([IO.Path]::GetFullPath($path)).StartsWith($destination + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Export destination containment changed after directory creation' }
    $stream = [IO.File]::Open($path, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::Read)
    try {
        $stream.Write($bytes, 0, $bytes.Length)
        $stream.Flush($true)
    } finally {
        $stream.Dispose()
    }
}
function Assert-Direct($path) {
    $current = Get-Item -LiteralPath $path -Force
    while ($null -ne $current) {
        if ($current.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Reparse path: $path" }
        if ($current -is [IO.FileInfo]) { $current = $current.Directory }
        else { $current = $current.Parent }
    }
}
function Read-Bounded($path, $expected = $null) {
    Assert-Direct $path
    $before = Get-Item -LiteralPath $path -Force
    if ($before -isnot [IO.FileInfo] -or $before.Length -gt 8MB) { throw 'Bounded regular metadata file required' }
    $stream = [IO.File]::Open($path, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::Read)
    try {
        $identity = [Pro3ExportFileIdentity]::Fingerprint($stream.SafeFileHandle)
        if ($stream.Length -ne $before.Length -or $stream.Length -gt 8MB) { throw 'Source length changed before open' }
        $bytes = [byte[]]::new([int]$stream.Length + 1)
        $count = 0
        while ($count -lt $bytes.Length) {
            $read = $stream.Read($bytes, $count, $bytes.Length - $count)
            if ($read -eq 0) { break }
            $count += $read
        }
        $after = Get-Item -LiteralPath $path -Force
        Assert-Direct $path
        $pathStream = [IO.File]::Open($path, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::Read)
        try {
            if ([Pro3ExportFileIdentity]::Fingerprint($pathStream.SafeFileHandle) -cne $identity -or
                [Pro3ExportFileIdentity]::Fingerprint($stream.SafeFileHandle) -cne $identity) { throw 'Source file identity changed' }
        } finally { $pathStream.Dispose() }
        if ($count -ne $before.Length -or $stream.Length -ne $before.Length -or
            $after.Length -ne $before.Length -or $after.CreationTimeUtc.Ticks -ne $before.CreationTimeUtc.Ticks -or
            $after.LastWriteTimeUtc.Ticks -ne $before.LastWriteTimeUtc.Ticks) { throw 'Unstable metadata file' }
        $retained = [byte[]]::new($count)
        [Array]::Copy($bytes, $retained, $count)
        $sha = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($retained)).ToLowerInvariant()
        if ($expected -and $sha -cne $expected) { throw "External metadata pin differs: $path" }
        return [pscustomobject]@{ bytes = $retained; sha256 = $sha; length = $count }
    } finally { $stream.Dispose() }
}
function Assert-JsonElement($element) {
    if ($element.ValueKind -eq [Text.Json.JsonValueKind]::Object) {
        $names = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
        foreach ($property in $element.EnumerateObject()) {
            if (-not $names.Add($property.Name)) { throw 'Duplicate JSON key refused' }
            Assert-JsonElement $property.Value
        }
    } elseif ($element.ValueKind -eq [Text.Json.JsonValueKind]::Array) {
        foreach ($item in $element.EnumerateArray()) { Assert-JsonElement $item }
    } elseif ($element.ValueKind -eq [Text.Json.JsonValueKind]::Number) {
        $number = [double]0
        if (-not $element.TryGetDouble([ref]$number) -or -not [double]::IsFinite($number)) { throw 'Nonfinite JSON number refused' }
    }
}
function Read-JsonPinned($path, [string]$expected) {
    if ($expected -cnotmatch '^[0-9a-f]{64}$') { throw 'Explicit JSON SHA256 required' }
    $retained = Read-Bounded $path $expected
    $text = $utf8.GetString($retained.bytes)
    $options = [Text.Json.JsonDocumentOptions]::new()
    $options.MaxDepth = 64
    $document = [Text.Json.JsonDocument]::Parse([string]$text, $options)
    try { Assert-JsonElement $document.RootElement } finally { $document.Dispose() }
    $proofPins[[IO.Path]::GetFullPath($path)] = $expected
    return $text | ConvertFrom-Json -DateKind String
}
function Assert-Fields($value, [hashtable]$expected) {
    foreach ($entry in $expected.GetEnumerator()) {
        $property = $value.PSObject.Properties[$entry.Key]
        if ($null -eq $property) { throw "Required proof field absent: $($entry.Key)" }
        $actual = $property.Value
        if ($entry.Value -is [bool]) {
            if ($actual -isnot [bool] -or $actual -ne $entry.Value) { throw "Boolean proof field differs: $($entry.Key)" }
        } elseif ($entry.Value -is [string]) {
            if ($actual -isnot [string] -or $actual -cne $entry.Value) { throw "String proof field differs: $($entry.Key)" }
        } elseif ($entry.Value -is [int] -or $entry.Value -is [long]) {
            if (($actual -isnot [int] -and $actual -isnot [long]) -or $actual -ne $entry.Value) { throw "Integer proof field differs: $($entry.Key)" }
        } elseif ($null -eq $entry.Value) {
            if ($null -ne $actual) { throw "Null proof field differs: $($entry.Key)" }
        } else { throw 'Unsupported finite proof expectation' }
    }
}
function Read-ReviewedProof($review, [string]$prefix, [string]$filename) {
    $path = Join-Path $run $filename
    Assert-Fields $review @{ ($prefix + '_path') = $path }
    $expected = $review.PSObject.Properties[$prefix + '_sha256']
    if ($null -eq $expected -or $expected.Value -isnot [string]) { throw 'Mandatory independently reviewed proof SHA256 absent' }
    return Read-JsonPinned $path $expected.Value
}
function Assert-NativeCloseout($closeout) {
    Assert-Fields $closeout.native @{ accepted = $true; closed_empty_handles_closed_freshly_absent = $true }
    $directory = [IO.Path]::GetFullPath($closeout.native.native_directory)
    $name = [IO.Path]::GetFileName($directory)
    if ((Split-Path -Parent $directory) -cne (Join-Path $root 'runs\migration') -or $name -cnotmatch '^\d{8}T\d{6}Z_[a-f0-9]{10}$') { throw 'Exact direct native proof directory required' }
    Assert-Direct $directory
    $job = 'pro3_migration_' + $name
    Assert-Fields $closeout.native @{ job_name = $job }
    $receipt = Read-JsonPinned (Join-Path $directory 'receipt.json') $closeout.native.receipt_sha256
    Assert-Fields $receipt @{ schema = 'migration_guard_receipt_v1'; accepted = $true; job_name = $job; job_absent = $true; scientific_admission = $false; error = $null }
    Assert-Fields $receipt.result @{ reason = 'normal'; exit_code = 0 }
    Assert-Fields $receipt.native_state @{ job_named = $job; process_limit_bytes = 4294967296; aggregate_limit_bytes = 5368709120 }
    foreach ($flag in @('job_created','created_suspended','limits_set','limits_query_verified','atomic_job_assignment_requested',
        'atomic_job_assignment_verified','assigned','membership_verified','resumed','job_empty_before_close','job_closed',
        'process_handle_closed','thread_handle_closed','root_exit_after_job_close','assignment_step_seen','attribute_cleanup_confirmed')) {
        Assert-Fields $receipt.native_state @{ $flag = $true }
    }
    foreach ($field in @('cleanup_errors','peak_sampling_errors')) {
        $property = $receipt.native_state.PSObject.Properties[$field]
        if ($null -eq $property -or $property.Value -isnot [array] -or $property.Value.Count -ne 0) { throw 'Native cleanup or sampling errors are not empty' }
    }
    if ($closeout.native.elapsed_seconds -isnot [double] -or -not [double]::IsFinite($closeout.native.elapsed_seconds) -or
        $closeout.native.elapsed_seconds -le 0 -or $closeout.native.elapsed_seconds -gt 600) { throw 'Actual bounded native duration required' }
}
function Assert-InputAudit($value, $initial) {
    Assert-Fields $value @{ files = $initial.files; bytes = $initial.bytes; fixture_root = $initial.fixture_root;
        input_identity_file_sha256 = $initial.input_identity_file_sha256 }
    if (@($value.PSObject.Properties).Count -ne 4) { throw 'Exact original-input audit taxonomy required' }
}
if (Test-Path -LiteralPath $destination) { throw 'Fresh export directory required' }
Assert-Direct (Split-Path -Parent $destination)
$reviewPath = Join-Path $run 'final-review.json'
$review = Read-JsonPinned $reviewPath $FinalReviewSha256
if ($review.schema -cne 'cho51_provenance_numerical_worker_final_review_v1' -or
    $review.passed -isnot [bool] -or $review.passed -ne $true -or $review.remaining_actionable_findings -isnot [array] -or @($review.remaining_actionable_findings).Count -ne 0 -or
    $review.scientific_admission -isnot [bool] -or $review.scientific_admission -ne $false -or
    @($review.document_bindings.PSObject.Properties).Count -ne 7) {
    throw 'Passed independent final review with seven exact documents required'
}
$tests = Read-ReviewedProof $review 'tests_closeout' 'closeout-tests-result.json'
$integration = Read-ReviewedProof $review 'integration_closeout' 'closeout-integration-result.json'
$integrationLease = Read-ReviewedProof $review 'integration_lease_closeout' 'lease-closeout_integration_001.json'
Assert-Fields $tests @{ schema = 'cho51_provenance_numerical_worker_tests_closeout_v1'; phase = 'tests'; passed = $true; tests = 63;
    backend_calls = 0; verifier_calls = 0; scientific_admission = $false; native_closeout_status = 'verified_external_post_job';
    post_terminal_validation_status = 'not_applicable_tests'; post_terminal_validation_deferred = $false; backend_input_audit_observation_count = 0 }
if ($tests.backend_input_audit_observations -isnot [array] -or $tests.backend_input_audit_observations.Count -ne 0) { throw 'Unit phase must not claim numerical audit observations or performed deferral' }
Assert-Fields $integration @{ schema = 'cho51_provenance_numerical_worker_closeout_v1'; phase = 'integration'; passed = $true;
    tests_current_job = 0; prior_accepted_tests = 63; engineering_successes = 1; backend_calls = 1; verifier_calls = 2;
    measured_cells = 0; scientific_admission = $false; native_closeout_status = 'verified_external_post_job';
    post_terminal_validation_status = 'fulfilled_external_post_job'; post_terminal_validation_deferred = $true;
    backend_input_audit_observation_count = 2; child_native_flag_remains_pending = $true }
if ($integration.backend_input_audit_observations -isnot [array] -or $integration.backend_input_audit_observations.Count -ne 2) { throw 'Two real independently verified backend input observations required' }
$zeroBudget = @{ source_updates = 0; restore_count = 0; support_updates = 0; gradient_updates = 0;
    target_inference_calls = 0; query_count = 0; model_constructions = 0; measured_cells = 0 }
$fullBudget = @{ source_updates = 0; restore_count = 1; support_updates = 1; gradient_updates = 1;
    target_inference_calls = 1; query_count = 2; model_constructions = 1; measured_cells = 0 }
Assert-Fields $tests.current_counter_ledger $zeroBudget
Assert-Fields $integration.current_counter_ledger $fullBudget
if (@($tests.current_counter_ledger.PSObject.Properties).Count -ne 8 -or @($integration.current_counter_ledger.PSObject.Properties).Count -ne 8) { throw 'Exact separate zero-test and numerical integration ledger taxonomies required' }
Assert-Fields $integration.factory_local_counts @{ selected_restores = 1; source_updates = 0; support_updates = 0; query_calls = 0 }
if ($integration.pins_sha256 -isnot [string] -or $integration.pins_sha256 -cnotmatch '^[0-9a-f]{64}$' -or
    $tests.pins_sha256 -cne $integration.pins_sha256 -or $tests.source_review_sha256 -cne $integration.source_review_sha256 -or
    $integration.source_review_sha256 -cnotmatch '^[0-9a-f]{64}$') { throw 'Both accepted phases must bind the exact same current pins and source review' }
Assert-Fields $integrationLease @{ schema = 'cho51_provenance_numerical_worker_lease_closeout_v1'; phase = 'integration';
    pins_sha256 = $integration.pins_sha256; closed = $true; custody_released = $true; outstanding_owned_children = 0;
    native_job_name = $integration.native.job_name;
    guard_and_launcher_reaped = $true; external_closeout_reaped = $true; full_compute_custody_explicitly_released = $true; scientific_admission = $false }
Assert-NativeCloseout $tests
Assert-NativeCloseout $integration
$currentPins = Read-JsonPinned (Join-Path $run 'pins.json') $integration.pins_sha256
Assert-Fields $currentPins @{ schema = 'cho51_provenance_numerical_worker_pins_v1'; expected_tests = 63;
    operational_scope = 'cho51_provenance_numerical_worker_20261025_v7'; source_review_sha256 = $integration.source_review_sha256;
    seconds = 600; process_mib = 4096; job_mib = 5120; startup_ram_gib = 4; active_ram_gib = 4; disk_gib = 20;
    threads = 1; gpu_hidden = $true; scientific_admission = $false }
$postTerminalPolicy = @{ schema = 'cho51_post_terminal_validation_policy_v1'; scope = 'integration_after_frozen_parent_pipeline_only';
    full_original_input_sweeps_deferred = 2; full_origin_revalidations_deferred = 1; actual_backend_scope_input_audits = 2;
    full_origin_physical_verifier_callbacks = 2; final_contract_identity_check_retained = $true; final_fixture_source_check_retained = $true;
    final_runtime_source_loaded_module_checks_retained = $true; mandatory_external_full_origin_and_original_input_validation = $true;
    scientific_admission = $false }
foreach ($policy in @($currentPins.post_terminal_validation_policy, $tests.post_terminal_validation_policy, $integration.post_terminal_validation_policy)) {
    Assert-Fields $policy $postTerminalPolicy
    if (@($policy.PSObject.Properties).Count -ne $postTerminalPolicy.Count) { throw 'Exact post-terminal external validation policy required' }
}
$contract = Read-JsonPinned (Join-Path $run 'origin-contract.json') $currentPins.origin_contract_file_sha256
Assert-Fields $contract @{ schema = 'cho51_linear_worker_origin_contract_v1' }
$initial = $contract.summary.input_audit
Assert-Fields $initial @{ files = 213; bytes = 734579463;
    fixture_root = (Join-Path $root 'runs\coordination\cho51_linear_lineage_20261015_v2\validation_001\fixture');
    input_identity_file_sha256 = '34851cf72d33257bcf57a23b540eb7a0e368b0f6c5ff46f41bbf90b92de1289c' }
Assert-InputAudit $initial $initial
foreach ($observation in $integration.backend_input_audit_observations) { Assert-InputAudit $observation $initial }
$case = $integration.proof.case_id
if ($case -isnot [string] -or $case -cne '9d3596b5e7653e1708eb208d6b150b86cae02227e6cd73a25e4358e675afc141') { throw 'Exact single admitted engineering case required' }
foreach ($field in @('execution_file_sha256','request_sha256','factory_request_sha256','claim_sha256','pins_sha256')) {
    $value = $integration.proof.PSObject.Properties[$field]
    if ($null -eq $value -or $value.Value -isnot [string] -or $value.Value -cnotmatch '^[0-9a-f]{64}$') { throw 'Strict physical current-execution proof SHA256 required' }
}
Assert-Fields $integration.proof @{ pins_sha256 = $integration.pins_sha256 }
$workspace = Join-Path $run ('i1\cases\' + $case)
$execution = Read-JsonPinned (Join-Path $workspace 'current-execution.json') $integration.proof.execution_file_sha256
Assert-Fields $execution @{ schema_version = 1; phase = 2; kind = 'engineering_smoke' }
Assert-Fields $execution.payload @{ schema = 'cho51_provenance_numerical_execution_v1'; engineering_only = $true; scientific_admission = $false;
    measured_cells = 0; native_closeout_status = 'pending_external_post_job'; pins_sha256 = $integration.pins_sha256;
    request_sha256 = $integration.proof.request_sha256; factory_request_sha256 = $integration.proof.factory_request_sha256;
    claim_sha256 = $integration.proof.claim_sha256; workspace = $workspace }
Assert-InputAudit $execution.payload.input_audit_before $initial
Assert-InputAudit $execution.payload.input_audit_after $initial
Assert-Fields $execution.payload.current_counter_ledger $fullBudget
Assert-Fields $execution.payload.expected_numerical_budget $fullBudget
$sources = [Collections.Generic.List[object]]::new()
function Add-Source($source, $copy, $expected = $null) {
    $absolute = [IO.Path]::GetFullPath((Join-Path $root $source))
    if (-not $absolute.StartsWith($root + '\', [StringComparison]::OrdinalIgnoreCase) -or
        [IO.Path]::GetExtension($absolute).ToLowerInvariant() -notin @('.json','.md','.py','.ps1','.log')) {
        throw "Unbounded metadata source: $source"
    }
    Assert-Direct $absolute
    if ($null -eq $expected -and $proofPins.ContainsKey($absolute)) { $expected = $proofPins[$absolute] }
    $relative = [IO.Path]::GetRelativePath($root, $absolute).Replace('\','/')
    $sourcePin = $currentPins.files.PSObject.Properties[$relative]
    if ($null -eq $expected -and $null -ne $sourcePin) {
        if ($sourcePin.Value -isnot [string] -or $sourcePin.Value -cnotmatch '^[0-9a-f]{64}$') { throw 'Strict admitted historical metadata SHA256 required' }
        $expected = $sourcePin.Value
    }
    $sources.Add([pscustomobject]@{ absolute = $absolute; source = $relative; path = $copy; expected = $expected })
}
Add-Source 'runs/coordination/cho51_provenance_numerical_worker_20261025_v7/final-review.json' 'final-review.json' $FinalReviewSha256
foreach ($binding in $review.document_bindings.PSObject.Properties) {
    if ($binding.Value -isnot [string] -or $binding.Value -cnotmatch '^[0-9a-f]{64}$') { throw 'Strict reviewed document SHA256 required' }
    if (-not [IO.Path]::IsPathFullyQualified($binding.Name) -or [IO.Path]::GetFullPath($binding.Name) -cne $binding.Name -or
        [IO.Path]::GetExtension($binding.Name).ToLowerInvariant() -cne '.md') { throw 'Exact absolute reviewed Markdown document path required' }
    $relative = [IO.Path]::GetRelativePath($root, $binding.Name).Replace('\','/')
    if ($relative.Contains('/') -and -not $relative.StartsWith('docs/', [StringComparison]::Ordinal)) { throw 'Reviewed resume snapshots must be top-level or documentation files, never live run/cache trees' }
    Add-Source $relative ('snapshots/' + $relative) $binding.Value
}
foreach ($name in @('plan','split_validation_plan','operations_successor','audit_acceleration_plan','external_audit_plan')) {
    $relative = 'docs/phase2/cho51_provenance_numerical_worker_' + $name + '_20261025.md'
    Add-Source $relative ('preparation/' + [IO.Path]::GetFileName($relative))
}
foreach ($version in 1..4) {
    $relative = 'runs/coordination/cho51_provenance_numerical_worker_20261025_v' + $version
    $files = @('closeout.py','guard.py','launch.ps1','native_pins.ps1','origin.py','parent.py','prepare.py','runtime.py',
        'pins.json','source-review.json')
    if ($version -eq 4) { $files += @('failed-attempt-native-audit_tests_001.json','lease-closeout_tests_001.json') }
    else { $files += @('failed-attempt-native-audit_001.json','lease-closeout_001.json') }
    foreach ($name in $files) { Add-Source ($relative + '/' + $name) ('predecessors/v' + $version + '/' + $name) }
}
foreach ($name in @('README.md','backend.py','numerical_worker.py','pipeline.py','test_integration.py')) {
    Add-Source ('docs/phase2/cho51_provenance_numerical_worker_v1/' + $name) ('predecessors/candidate-v1/' + $name)
}
$v5Files = @('closeout.py','guard.py','launch.ps1','native_pins.ps1','origin.py','parent.py','prepare.py','runtime.py',
    'pins.json','source-review.json',
    'failed-attempt-native-audit_integration_001.json','failed-attempt-native-audit_integration_002.json','lease-closeout_integration_001.json',
    'closeout-tests-result.json','tests-final-review.json','lease-closeout_tests_001.json')
foreach ($name in $v5Files) {
    Add-Source ('runs/coordination/cho51_provenance_numerical_worker_20261025_v5/' + $name) ('predecessors/v5/' + $name)
}
$v6Files = @('closeout.py','guard.py','launch.ps1','native_pins.ps1','origin.py','parent.py','prepare.py','runtime.py',
    'pins.json','source-review.json','failed-attempt-native-audit_integration_001.json','lease-closeout_integration_001.json',
    'closeout-tests-result.json','tests-final-review.json','lease-closeout_tests_001.json')
foreach ($name in $v6Files) {
    Add-Source ('runs/coordination/cho51_provenance_numerical_worker_20261025_v6/' + $name) ('predecessors/v6/' + $name)
}
$currentFiles = @('admission_tests.json','admission_integration.json','closeout-tests-result.json','closeout-integration-result.json',
    'closeout-tests-stderr_001.log','closeout-tests-stdout_001.log','closeout-tests-supervision_001.json',
    'closeout-integration-stderr_001.log','closeout-integration-stdout_001.log','closeout-integration-supervision_001.json',
    'compute-request_tests_001.json','compute-request_integration_001.json','dispatch_tests_001.json','dispatch_integration_001.json',
    'dispatch_result_tests_001.json','dispatch_result_integration_001.json','lease-closeout_tests_001.json','lease-closeout_integration_001.json',
    'native-utc-path-regression.json','owner-resource-amendment.json','peer-release-authenticated_tests.json','peer-release-authenticated_integration.json',
    'preflight_tests_001.json','preflight_integration_001.json','prepare-stderr_001.log','prepare-stdout_001.log','prepare-supervision_001.json',
    'tests-final-review.json','tests-root-native-check_001.json','final-git-native-check_001.json','export-closeout.ps1')
foreach ($name in $currentFiles) {
    Add-Source ('runs/coordination/cho51_provenance_numerical_worker_20261025_v7/' + $name) ('preparation/v7/' + $name)
}
if ($sources.Count -ne 128 -or $sources.Count -gt 128 -or @($sources.path | Select-Object -Unique).Count -ne $sources.Count) {
    throw 'Exact unique128-artifact bounded inventory required'
}
$rows = [Collections.Generic.List[object]]::new()
$total = [long]0
foreach ($source in $sources) {
    $file = Get-Item -LiteralPath $source.absolute
    if ($file.Length -gt 8MB) { throw "Metadata file exceeds8MiB: $($source.source)" }
    $total += $file.Length
    if ($total -gt 64MB) { throw 'Metadata export exceeds64MiB' }
    $retained = Read-Bounded $source.absolute $source.expected
    if ($retained.length -ne $file.Length) { throw 'Source length changed during selection' }
    $sha = $retained.sha256
    $bytes = $retained.bytes
    $copied = Join-Path $destination $source.path
    Write-New $copied $bytes
    if ((Get-Sha $copied) -cne $sha -or (Get-Sha $source.absolute) -cne $sha) { throw 'Copy hash differs' }
    $rows.Add([ordered]@{ source = $source.source; path = $source.path; bytes = $bytes.LongLength; sha256 = $sha })
}
Write-New (Join-Path $destination '.gitattributes') $utf8.GetBytes(("* -text" + [char]10))
$readme = @'
# Provenance-aware numerical worker engineering closeout export, 25 October 2026

This inert metadata-only export preserves the independent final review, seven
exact qualification/resume snapshots, phase plans, failed predecessor sources
and failure/custody metadata, and fresh v7 control-plane/closeout records.
The manifest authenticates physical SHA256 and sizes, not future execution.
The separate evidence/cho51-provenance-numerical-worker-tests-20261025-v7
packet has63 passing cases and all numerical counters0. The separate
evidence/cho51-provenance-numerical-worker-20261025-v7 packet preserves one identity-locked real
selected-source restoration, one head-only SGD update and one two-trial query.
The integration Job runs no current tests; prior accepted tests63 remain separate.
Factory-local support/query0 remain distinct from aggregate support/query1.
Source fitting and measured cells remain0; no accuracy threshold is imposed.

Both actual before/after-scope complete input audits and both full-origin physical
verifier callbacks remain inside the hard600-second integration Job. Only the
redundant post-terminal sweeps move to mandatory independent external closeout.
That closeout joins both genuine parent observations to the pinned initial
inventory and physical execution, then freshly rehashes the full origin and213
original inputs. Child native/post-terminal flags remain pending; only the
external closeout reports fulfilled_external_post_job. The unit phase performs
no numerical transaction or post-terminal deferral.

Both once-only guarded stages and external stdlib closeouts closed/reaped;
full compute custody was explicitly released. The same scope-bound owner
startup4GiB allowance retains active4GiB, disk20GiB,600s,4096/5120MiB caps,
threads1/1, hiddenGPU and genuine peer/pause controls. Historical10GiB receipts,
failed attempts, producer provenance and current executor identities stay distinct.
Archived grants are consumed/closed: never replay any used launcher or infer
another lease, another runtime qualification, host quiet or scientific admission.

V5 and V6 accepted only their independent zero-numerical unit phases. Their
integrations hit the hard600-second deadline. Failure audits, closed custody
and physical partial engineering intent/success remain FAILED, incomplete/unknown
and quarantined history; this export does not accept or replay either episode.

Historical copying is deliberately selective, not a complete asset migration.
Older native-runtime, owner-amendment and origin-contract metadata remain live,
frozen and authenticated by the main execution origin rather than duplicated
here. No omitted frozen file or receipt is deleted or rewritten.

Arrays, weights, caches, environments and live run trees are excluded.
Another device needs authenticated assets and fresh pins/admission/coordination.
Unchanged canonical factories/workers, remaining methods, full1,020-cell study,
checkpoint-cohort/overlap lineage and final owner freeze remain pending.
Original target01 attempts remain exhausted; adopted targets02–52/source52,
narrow GateA acceptance and unsigned final scientific freeze stay unchanged.
'@
Write-New (Join-Path $destination 'README.md') $utf8.GetBytes(($readme + [char]10))
$inventory = @($rows | ForEach-Object { $_.path }) + @('.gitattributes','README.md','manifest.json')
$manifest = [ordered]@{
    schema = 'cho51_provenance_numerical_worker_closeout_export_v1'
    metadata_only = $true
    created_utc = [DateTimeOffset]::UtcNow.ToString('o')
    final_review_sha256 = $FinalReviewSha256
    all_copies_byte_identical_to_sources = $true
    all_seven_document_copies_match_review_bindings = $true
    copied_artifact_count = $rows.Count
    copied_payload_bytes = $total
    artifacts = @($rows.ToArray())
    exact_inventory = @($inventory | Sort-Object)
    explanatory_readme_sha256 = Get-Sha (Join-Path $destination 'README.md')
    byte_attributes_sha256 = Get-Sha (Join-Path $destination '.gitattributes')
    arrays_weights_and_environment_excluded = $true
    scientific_admission = $false
    post_terminal_validation_status = 'fulfilled_external_post_job'
    child_pending_flags_unchanged = $true
    future_head_binding = 'Review hashes bind these snapshots, not later mutable resume heads.'
}
Write-New (Join-Path $destination 'manifest.json') $utf8.GetBytes((($manifest | ConvertTo-Json -Depth 20) + [char]10))
$actual = @(Get-ChildItem -LiteralPath $destination -Recurse -File -Force | ForEach-Object { [IO.Path]::GetRelativePath($destination, $_.FullName).Replace('\','/') } | Sort-Object)
if (@(Compare-Object $actual ($inventory | Sort-Object)).Count -ne 0) { throw 'Unexpected export inventory' }
foreach ($row in $rows) {
    if ((Get-Sha (Join-Path $root $row.source)) -cne $row.sha256 -or
        (Get-Sha (Join-Path $destination $row.path)) -cne $row.sha256) { throw 'Final export binding changed' }
}
foreach ($proof in $proofPins.GetEnumerator()) {
    if ((Get-Sha $proof.Key) -cne $proof.Value) { throw 'Externally reviewed acceptance proof changed during export' }
}
[ordered]@{ passed = $true; artifacts = $rows.Count; payload_bytes = $total; exact_files = $actual.Count;
    manifest_sha256 = Get-Sha (Join-Path $destination 'manifest.json'); readme_sha256 = $manifest.explanatory_readme_sha256;
    final_review_sha256 = $manifest.final_review_sha256; scientific_admission = $false } | ConvertTo-Json


