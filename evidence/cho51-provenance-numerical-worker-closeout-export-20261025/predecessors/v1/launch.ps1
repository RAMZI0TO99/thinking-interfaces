param([Parameter(Mandatory=$true)][ValidatePattern('^[a-f0-9]{64}$')][string]$PinsSha256)
$ErrorActionPreference = 'Stop'
if (-not (Get-Command ConvertFrom-Json).Parameters.ContainsKey('DateKind')) { throw 'This launcher requires ConvertFrom-Json -DateKind String to preserve lease UTC timestamps' }
$FactoryProject = 'D:\Aenv\pro3'
$FactoryRun = $PSScriptRoot
$FactoryPinsPath = Join-Path $FactoryRun 'pins.json'
$FactoryOutput = Join-Path $FactoryRun 'validation_001'
$FactoryContractPath = Join-Path $FactoryRun 'origin-contract.json'
if (Test-Path -LiteralPath $FactoryOutput) { throw 'Unused factory validation output required' }
if ((Get-FileHash -LiteralPath $FactoryPinsPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $PinsSha256) { throw 'Fresh admitted pins changed' }
$FactoryPins = Get-Content -LiteralPath $FactoryPinsPath -Raw | ConvertFrom-Json -DateKind String
$FactoryAdmission = Get-Content -LiteralPath (Join-Path $FactoryRun 'admission.json') -Raw | ConvertFrom-Json -DateKind String
if ($FactoryAdmission.schema -ne 'cho51_provenance_numerical_worker_admission_v1' -or $FactoryAdmission.pins_sha256 -ne $PinsSha256 -or
    $FactoryAdmission.accepted -ne $true -or $FactoryAdmission.scientific_admission -ne $false -or
    $FactoryAdmission.max_job_seconds -ne 600 -or $FactoryAdmission.process_mib -ne 4096 -or $FactoryAdmission.job_mib -ne 5120 -or
    $FactoryAdmission.startup_ram_gib -ne 4 -or $FactoryAdmission.active_ram_gib -ne 4 -or $FactoryAdmission.disk_gib -ne 20 -or
    $FactoryAdmission.owner_resource_amendment_path -ne $FactoryPins.owner_resource_amendment_path -or
    $FactoryAdmission.owner_resource_amendment_sha256 -ne $FactoryPins.owner_resource_amendment_sha256 -or
    $FactoryAdmission.source_review_sha256 -ne $FactoryPins.source_review_sha256) { throw 'Exact fresh accepted engineering admission required' }
if ((Get-FileHash -LiteralPath (Join-Path $FactoryRun 'source-review.json') -Algorithm SHA256).Hash.ToLowerInvariant() -ne $FactoryPins.source_review_sha256) { throw 'Accepted settled source review changed' }
if ($FactoryPins.owner_resource_amendment_path -ne (Join-Path $FactoryRun 'owner-resource-amendment.json') -or
    (Get-FileHash -LiteralPath $FactoryPins.owner_resource_amendment_path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $FactoryPins.owner_resource_amendment_sha256) { throw 'Pinned direct-owner resource amendment changed' }
if (@($FactoryPins.reviewed_files.PSObject.Properties).Count -ne 13) { throw 'Exactly13 settled candidate and operation sources required' }
foreach ($FactoryReviewed in $FactoryPins.reviewed_files.PSObject.Properties) {
    if ((Get-FileHash -LiteralPath (Join-Path $FactoryProject $FactoryReviewed.Name) -Algorithm SHA256).Hash.ToLowerInvariant() -ne $FactoryReviewed.Value) { throw 'Reviewed candidate or containment source changed before Python' }
}
if (-not [System.IO.Path]::IsPathFullyQualified($FactoryAdmission.peer_release_path) -or
    [System.IO.Path]::GetFullPath($FactoryAdmission.peer_release_path) -ne $FactoryAdmission.peer_release_path -or
    (Get-FileHash -LiteralPath $FactoryAdmission.peer_release_path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $FactoryAdmission.peer_release_sha256) { throw 'Exact peer compute release evidence required' }
$FactoryPeerRelease = Get-Content -LiteralPath $FactoryAdmission.peer_release_path -Raw | ConvertFrom-Json -DateKind String
if ($FactoryPeerRelease.schema -ne 'pro2_pro3_compute_release_v1' -or $FactoryPeerRelease.scope -ne 'cho51_provenance_numerical_worker_20261025_v1' -or
    $FactoryPeerRelease.released -ne $true -or $FactoryPeerRelease.pins_sha256 -ne $PinsSha256 -or $FactoryPeerRelease.maximum_jobs -ne 1 -or
    $FactoryPeerRelease.max_job_seconds -ne 600 -or $FactoryPeerRelease.process_mib -ne 4096 -or $FactoryPeerRelease.job_mib -ne 5120 -or
    $FactoryPeerRelease.window_start_utc -ne $FactoryAdmission.window_start_utc -or $FactoryPeerRelease.window_end_utc -ne $FactoryAdmission.window_end_utc) { throw 'Peer release differs from exact pinned finite request' }
$FactoryWindowStart = [DateTimeOffset]::Parse($FactoryAdmission.window_start_utc).ToUniversalTime()
$FactoryWindowEnd = [DateTimeOffset]::Parse($FactoryAdmission.window_end_utc).ToUniversalTime()
$FactoryNow = [DateTimeOffset]::UtcNow
if ($FactoryNow -lt $FactoryWindowStart -or $FactoryNow -gt $FactoryWindowEnd.AddSeconds(-690)) { throw 'Peer release must be active with at least690 seconds remaining' }
foreach ($FactoryGroup in @('runtime', 'runtime_modules', 'supporting_runtime_sources')) {
    foreach ($FactoryProperty in $FactoryPins.$FactoryGroup.PSObject.Properties) {
        if ((Get-FileHash -LiteralPath $FactoryProperty.Name -Algorithm SHA256).Hash.ToLowerInvariant() -ne $FactoryProperty.Value) { throw 'Fresh runtime pin changed before Python launch' }
    }
}
foreach ($FactoryDay in @('20261007', '20261012', '20261013', '20261015', '20261025')) {
    $FactoryPause = 'D:\Aenv\pro2\WORK\resume-' + $FactoryDay + '-001\coordination\PRO2_REQUEST_PRO3_PAUSE.json'
    if (Test-Path -LiteralPath $FactoryPause) { throw ('Genuine peer pause: ' + $FactoryPause) }
}
$FactoryPython = Join-Path $FactoryProject '.venv\Scripts\python.exe'
$FactoryCommand = @($FactoryPython, '-I', '-S', '-B', (Join-Path $FactoryRun 'parent.py'), '--pins', $FactoryPinsPath, '--expect-pins', $PinsSha256, '--output', $FactoryOutput)
$FactoryContractSha = (Get-FileHash -LiteralPath $FactoryContractPath -Algorithm SHA256).Hash.ToLowerInvariant()
function Write-FactoryJsonOnce([string]$Path, [object]$Value) {
    $FactoryStream = [System.IO.File]::Open($Path, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write, [System.IO.FileShare]::Read)
    try {
        $FactoryWriter = [System.IO.StreamWriter]::new($FactoryStream, [System.Text.UTF8Encoding]::new($false))
        try { $FactoryWriter.WriteLine(($Value | ConvertTo-Json -Depth 14)); $FactoryWriter.Flush(); $FactoryStream.Flush($true) } finally { $FactoryWriter.Dispose() }
    } finally { $FactoryStream.Dispose() }
}
Write-FactoryJsonOnce (Join-Path $FactoryRun 'dispatch_001.json') ([ordered]@{
    schema='cho51_provenance_numerical_worker_dispatch_v1'; observed_utc=[DateTime]::UtcNow.ToString('o'); pins_sha256=$PinsSha256
    origin_contract_file_sha256=$FactoryContractSha; child_command=$FactoryCommand; expected_output=$FactoryOutput
    expected_numerical_budget=[ordered]@{source_updates=0; restore_count=1; support_updates=1; gradient_updates=1; target_inference_calls=1; query_count=2; model_constructions=1; measured_cells=0}; actual_current_counter_ledger=$null; scientific_admission=$false
    admission_sha256=(Get-FileHash -LiteralPath (Join-Path $FactoryRun 'admission.json') -Algorithm SHA256).Hash.ToLowerInvariant()
    peer_release_path=$FactoryAdmission.peer_release_path; peer_release_sha256=$FactoryAdmission.peer_release_sha256
    window_start_utc=$FactoryAdmission.window_start_utc; window_end_utc=$FactoryAdmission.window_end_utc
})
$FactoryArguments = @('-I', '-S', '-B', (Join-Path $FactoryRun 'guard.py'),
    '--purpose', 'one engineering-only typed parent and numerical worker using provenance-aware factory restore, one head support update and two-trial query inside a fresh real CaseRecorder lock; no source fitting or study cells',
    '--seconds', '600', '--process-mib', '4096', '--job-mib', '5120',
    '--pause-file', 'D:\Aenv\pro2\WORK\resume-20261025-001\coordination\PRO2_REQUEST_PRO3_PAUSE.json', '--') + $FactoryCommand
$FactoryLines = @(& $FactoryPython @FactoryArguments)
$FactoryExit = $LASTEXITCODE
foreach ($FactoryLine in $FactoryLines) { Write-Output $FactoryLine }
if ($FactoryLines.Count -lt 1) { throw 'Native guard returned no directory' }
$FactoryNative = [string]$FactoryLines[0]
$FactoryNativeRoot = Join-Path $FactoryProject 'runs\migration'
if (-not [System.IO.Path]::IsPathFullyQualified($FactoryNative) -or [System.IO.Path]::GetFullPath($FactoryNative) -ne $FactoryNative -or
    [System.IO.Path]::GetDirectoryName($FactoryNative) -ne $FactoryNativeRoot -or [System.IO.Path]::GetFileName($FactoryNative) -notmatch '^\d{8}T\d{6}Z_[a-f0-9]{10}$' -or
    -not (Test-Path -LiteralPath $FactoryNative -PathType Container)) { throw 'Direct fresh migration directory required' }
Write-FactoryJsonOnce (Join-Path $FactoryRun 'dispatch_result_001.json') ([ordered]@{
    schema='cho51_provenance_numerical_worker_dispatch_result_v1'; observed_utc=[DateTime]::UtcNow.ToString('o'); pins_sha256=$PinsSha256
    origin_contract_file_sha256=$FactoryContractSha; child_command=$FactoryCommand; expected_output=$FactoryOutput
    native_directory=$FactoryNative; guard_exit_code=$FactoryExit; expected_numerical_budget=[ordered]@{source_updates=0; restore_count=1; support_updates=1; gradient_updates=1; target_inference_calls=1; query_count=2; model_constructions=1; measured_cells=0}; actual_current_counter_ledger=$null; scientific_admission=$false
    admission_sha256=(Get-FileHash -LiteralPath (Join-Path $FactoryRun 'admission.json') -Algorithm SHA256).Hash.ToLowerInvariant()
    peer_release_path=$FactoryAdmission.peer_release_path; peer_release_sha256=$FactoryAdmission.peer_release_sha256
    window_start_utc=$FactoryAdmission.window_start_utc; window_end_utc=$FactoryAdmission.window_end_utc
})
exit $FactoryExit
