param(
 [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ReviewSha256,
 [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$PreparationReviewSha256,
 [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$SourceCoordinationObservationSha256,
 [Parameter(Mandatory)][string]$BootstrapAcceptancePath,
 [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$BootstrapAcceptanceSha256
)
$ErrorActionPreference='Stop'
$preparationWatch=[Diagnostics.Stopwatch]::StartNew()
$root='D:\Aenv\pro3'
$run=$PSScriptRoot
if($run -cne (Join-Path $root 'runs\coordination\cho51_p3_contracts_20261027_v1')){throw 'Exact preparation successor root required'}
$scope='cho51_p3_contracts_20261027_v1_tests'
$script:preflightDeadline=[DateTimeOffset]::UtcNow.AddSeconds(300)
if($ReviewSha256 -cne 'ab2df55aa4d36c66ce7f7d238f71683eddcb7dd773543c01da08dac4790df65a'){throw 'Exact original14 independent Source review required'}
$reviewPath=Join-Path $run 'source-review.json'
if((Get-FileHash -LiteralPath $reviewPath -Algorithm SHA256).Hash.ToLowerInvariant() -cne $ReviewSha256){throw 'Independent review changed'}
$initialReview=Get-Content -LiteralPath $reviewPath -Raw|ConvertFrom-Json -DateKind String
$nativePath=Join-Path $run 'native.ps1'
$nativeStream=[IO.File]::Open($nativePath,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
try{
 if($nativeStream.Length -le 0 -or $nativeStream.Length -gt 262144){throw 'Native helper bound exceeded'}
 $nativeRaw=[byte[]]::new([int]$nativeStream.Length)
 $nativeStream.ReadExactly($nativeRaw)
 $nativeSha=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($nativeRaw)).ToLowerInvariant()
 $nativeRelative='runs/coordination/cho51_p3_contracts_20261027_v1/native.ps1'
 if($initialReview.files.$nativeRelative -cne $nativeSha){throw 'Reviewed native helper bytes required'}
 . ([scriptblock]::Create([Text.UTF8Encoding]::new($false,$true).GetString($nativeRaw)))
}finally{$nativeStream.Dispose()}
$pinsHeld=[Collections.Generic.List[object]]::new()
$pauses=@('20261007','20261012','20261013','20261015','20261025')|ForEach-Object{"D:\Aenv\pro2\WORK\resume-$_-001\coordination\PRO2_REQUEST_PRO3_PAUSE.json"}
[ChoP3Native]::ConfigurePinChecks($script:preflightDeadline.UtcDateTime,[string[]]$pauses,(300-$preparationWatch.Elapsed.TotalSeconds))
$script:minRam=[uint64]::MaxValue
$script:minDisk=[uint64]::MaxValue
$script:sourceDeadline=$null
function Floors{
 $ram=[ChoP3Native]::AvailableMemory();$disk=[ChoP3Native]::AvailableDisk()
 $script:minRam=[math]::Min($script:minRam,$ram);$script:minDisk=[math]::Min($script:minDisk,$disk)
 Require ($ram -ge 4GB -and $disk -ge 20GB) 'Native source preparation active resource floor'
 foreach($pausePath in $pauses){Require (-not [ChoP3Native]::Exists($pausePath)) 'Genuine peer pause'}
 Require ([DateTimeOffset]::UtcNow -lt $script:preflightDeadline) 'Bounded native preparation deadline'
 Require ($preparationWatch.Elapsed.TotalSeconds -lt 300) 'Bounded monotonic native preparation deadline'
 if($null -ne $script:sourceDeadline){Require ([DateTimeOffset]::UtcNow -lt $script:sourceDeadline) 'Fresh Source interval and60-second reserve'}
}
$files=[ordered]@{}
$fileBytes=[ordered]@{}
$totalBytes=[long]0
function Write-New([string]$path,$value){
 Floors
 $raw=[Text.UTF8Encoding]::new($false).GetBytes(($value|ConvertTo-Json -Depth 40 -Compress)+[char]10)
 Require ($raw.Length -le 8388608) 'Bounded preparation metadata required'
 $stream=[IO.File]::Open($path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
 try{$stream.Write($raw,0,$raw.Length);$stream.Flush($true)}finally{$stream.Dispose()}
 Floors
 Require ((Get-Sha $path) -ceq [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($raw)).ToLowerInvariant()) 'Preparation effect readback differs'
 Floors
}
function Get-Sha([string]$path){
 $pin=[ChoP3Native]::Pin($path,2147483648,$false)
 try{return $pin.Sha256}finally{$pin.Dispose()}
}
function Read-Json([string]$path,[string]$expected){
 $pin=[ChoP3Native]::Pin($path,8388608,$true)
 try{if($expected){Require ($pin.Sha256 -ceq $expected) 'Pinned metadata changed'};return ,(Parse-Bytes $pin.Raw)}finally{$pin.Dispose()}
}
function Add-File([string]$path,[string]$expected='',[long]$maximumFileBytes=2147483648){
 Floors
 Require ($maximumFileBytes -gt 0 -and $maximumFileBytes -le 2147483648) 'Original physical per-file ceiling cannot increase'
 if($files.Contains($path)){if($expected){Require ($files[$path] -ceq $expected) 'Conflicting physical pin'};return}
 Require ($files.Count -lt 25000) 'Fresh physical inventory count cap'
 $pin=[ChoP3Native]::Pin($path,$maximumFileBytes,$false)
 try{
  if($expected){Require ($pin.Sha256 -ceq $expected) ('Pinned source changed: '+$path)}
  $script:totalBytes+=[long]$pin.Length
  Require ($script:totalBytes -le 4GB) 'Fresh physical inventory aggregate cap'
  $files[$path]=$pin.Sha256;$fileBytes[$path]=[long]$pin.Length
 }finally{$pin.Dispose()}
 Floors
}
Floors
$coordinationPath=Join-Path $run 'coordination-source-observation_003.json'
$coordination=Read-Json $coordinationPath $SourceCoordinationObservationSha256
Require-Text $coordination 'schema' 'cho51_p3_contracts_peer_source_observation_v1'
Require-Boolean $coordination 'pro3_validation_release' $false
Require ($coordination.source_scope_name -is [string] -and $coordination.source_scope_name -cmatch '^Source[0-9]{3}$') 'Exact newly observed Source scope name required'
foreach($reference in @($coordination.source_scope,$coordination.source_adoption)){
 Require ($reference.path -is [string] -and $reference.path.StartsWith('D:\Aenv\pro2\WORK\resume-20261027-002\coordination\',[StringComparison]::Ordinal) -and [IO.Path]::GetFullPath($reference.path) -ceq $reference.path -and $reference.sha256 -is [string] -and $reference.sha256 -cmatch '^[0-9a-f]{64}$') 'Actual bounded Pro2 coordination reference required'
}
$peerSource=Read-Json $coordination.source_scope.path $coordination.source_scope.sha256
$peerAdoption=Read-Json $coordination.source_adoption.path $coordination.source_adoption.sha256
Require-Boolean $peerAdoption 'Source_only_coexistence_adopted' $true
Require-Text $peerAdoption.Source_only_scope 'sha256' $coordination.source_scope.sha256
Require-Integer $peerSource 'Pro3_max_including_Root_and_reviewer' 2
Require-Integer $peerSource 'Pro2_max_including_Root' 3
Require-Integer $peerSource 'shared_max_including_both_roots_and_overlap' 5
$sourceStart=Utc-Time $peerSource 'interval_start';$sourceEnd=Utc-Time $peerSource 'interval_end'
Require ([DateTimeOffset]::UtcNow -ge $sourceStart) 'Fresh Source interval has not begun'
$script:sourceDeadline=$sourceEnd.AddSeconds(-60)
if($script:sourceDeadline -lt $script:preflightDeadline){$script:preflightDeadline=$script:sourceDeadline}
[ChoP3Native]::ConfigurePinChecks($script:preflightDeadline.UtcDateTime,[string[]]$pauses,(300-$preparationWatch.Elapsed.TotalSeconds))
Floors
Add-File $coordination.source_scope.path $coordination.source_scope.sha256
Add-File $coordination.source_adoption.path $coordination.source_adoption.sha256
$review=Read-Json $reviewPath $ReviewSha256
Require-Boolean $review 'source_only' $true
Require ($review.remaining_actionable_findings -is [object[]] -and $review.remaining_actionable_findings.Count -eq 0) 'Zero independent source findings required'
Require-Integer $review 'expected_stdlib_controls' 34
Require ($review.expected_tests -is [long] -and $review.expected_tests -gt 0 -and $review.test_function_counts.Count -gt 0) 'Source-derived complete test inventory required'
$reviewed=[ordered]@{}
foreach($relative in $review.files.Keys){$path=Join-Path $root $relative;Add-File $path $review.files[$relative];$reviewed[$relative]=$files[$path]}
$candidateNames=@('contracts.py','mapping.py','telemetry.py','test_mapping.py','test_telemetry.py','README.md')
$operationNames=@('metadata_common.py','guard.py','runner.py','closeout.py','prepare.ps1','launch.ps1','native.ps1','supervise.ps1')
$expectedSources=@($candidateNames|ForEach-Object{'docs/phase2/cho51_p3_adapter_v1/'+$_})+@($operationNames|ForEach-Object{'runs/coordination/cho51_p3_contracts_20261027_v1/'+$_})
Require ($reviewed.Count -eq 14 -and @(Compare-Object -CaseSensitive ($expectedSources|Sort-Object) (@($reviewed.Keys)|Sort-Object)).Count -eq 0) 'Exact14-source candidate/operations review required'
$preparationReviewPath=Join-Path $run 'preparation-source-review_003.json'
$preparationReview=Read-Json $preparationReviewPath $PreparationReviewSha256
Require-Text $preparationReview 'schema' 'cho51_p3_contracts_preparation_source_review_v3'
Require-Text $preparationReview 'original_source_review_sha256' $ReviewSha256
Require-Boolean $preparationReview 'source_only' $true
Require-Boolean $preparationReview 'independent_review' $true
Require-Boolean $preparationReview 'passed' $true
Require ($preparationReview.remaining_actionable_findings -is [object[]] -and $preparationReview.remaining_actionable_findings.Count -eq 0) 'Zero different-reviewer preparation source findings required'
$ancillaryNames=@('preparation-supervise_003.ps1','preparation-protocol_003.md','prepare_004.ps1')
$ancillarySources=@($ancillaryNames|ForEach-Object{'runs/coordination/cho51_p3_contracts_20261027_v1/'+$_})
Require ($preparationReview.files.Count -eq 3 -and @(Compare-Object -CaseSensitive ($ancillarySources|Sort-Object) (@($preparationReview.files.Keys)|Sort-Object)).Count -eq 0) 'Exact three-source preparation successor inventory required'
foreach($relative in $preparationReview.files.Keys){Add-File (Join-Path $root $relative) $preparationReview.files[$relative]}
Add-File $preparationReviewPath $PreparationReviewSha256
Require ([IO.Path]::GetDirectoryName($BootstrapAcceptancePath) -ceq $run -and [IO.Path]::GetFullPath($BootstrapAcceptancePath) -ceq $BootstrapAcceptancePath) 'Exact owned bootstrap acceptance path required'
$bootstrapAcceptance=Read-Json $BootstrapAcceptancePath $BootstrapAcceptanceSha256
Require-Text $bootstrapAcceptance 'schema' 'cho51_p3_powershell_bootstrap_acceptance_v1'
Require-Boolean $bootstrapAcceptance 'passed' $true
Require-Boolean $bootstrapAcceptance 'observational_only' $true
Require-Boolean $bootstrapAcceptance 'native_same_handle_identity_verified' $false
Require-Boolean $bootstrapAcceptance 'full_pro3_pins_created' $false
$powerShellRuntime='C:\Users\aladdin-alyanai\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell'
Require-Text $bootstrapAcceptance 'runtime_root' $powerShellRuntime
Require ([IO.Path]::GetDirectoryName($bootstrapAcceptance.manifest_path) -ceq $run -and [IO.Path]::GetFullPath($bootstrapAcceptance.manifest_path) -ceq $bootstrapAcceptance.manifest_path) 'Exact owned accepted manifest path required'
$bootstrapManifest=Read-Json $bootstrapAcceptance.manifest_path $bootstrapAcceptance.manifest_sha256
Require-Text $bootstrapManifest 'schema' 'cho51_p3_powershell_bootstrap_observation_v1'
Require-Text $bootstrapManifest 'runtime_root' $powerShellRuntime
Require-Text $bootstrapManifest 'request_sha256' $bootstrapAcceptance.source_request_sha256
Require-Boolean $bootstrapManifest 'native_same_handle_identity_verified' $false
Require-Boolean $bootstrapManifest 'full_pro3_pins_created' $false
Require ($bootstrapManifest.files.Count -ge 6 -and $bootstrapManifest.files.Count -le 2500) 'Bounded accepted runtime roster required'
$bootstrapRoster=[ordered]@{};$bootstrapObservedBytes=[long]0
foreach($path in $bootstrapManifest.files.Keys){Require ($bootstrapManifest.files[$path].bytes -is [long] -and $bootstrapManifest.files[$path].bytes -ge 0) 'Exact runtime bytes required';$bootstrapRoster[$path]=$bootstrapManifest.files[$path];$bootstrapObservedBytes+=$bootstrapManifest.files[$path].bytes}
Require ($bootstrapManifest.file_count -is [long] -and $bootstrapManifest.file_count -eq $bootstrapManifest.files.Count -and $bootstrapManifest.code_bytes -is [long] -and $bootstrapManifest.code_bytes -eq $bootstrapObservedBytes) 'Exact observed runtime totals required'
if($bootstrapAcceptance.ContainsKey('supporting_bootstrap_files')){
 Require ($bootstrapAcceptance.supporting_bootstrap_files -is [Collections.IDictionary] -and $bootstrapAcceptance.supporting_bootstrap_files.Count -le 2500) 'Bounded accepted supporting map required'
 foreach($path in $bootstrapAcceptance.supporting_bootstrap_files.Keys){$entry=$bootstrapAcceptance.supporting_bootstrap_files[$path];if($bootstrapRoster.Contains($path)){Require ($bootstrapRoster[$path].bytes -eq $entry.bytes -and $bootstrapRoster[$path].sha256 -ceq $entry.sha256) 'Conflicting accepted runtime pin'}else{$bootstrapRoster[$path]=$entry}}
}
Require ($bootstrapRoster.Count -le 2500) 'Accepted combined runtime count cap'
foreach($name in @('pwsh.exe','pwsh.dll','coreclr.dll','System.Management.Automation.dll','Microsoft.Management.Infrastructure.CimCmdlets.dll','Microsoft.Management.Infrastructure.dll','System.Diagnostics.Process.dll')){Require ($bootstrapRoster.Contains((Join-Path $powerShellRuntime $name))) 'Critical accepted runtime source missing'}
$bootstrapTotal=[long]0
foreach($path in $bootstrapRoster.Keys){
 Require ($path -is [string] -and $path.StartsWith($powerShellRuntime+'\',[StringComparison]::Ordinal) -and [IO.Path]::GetFullPath($path) -ceq $path -and [IO.Path]::GetExtension($path).ToLowerInvariant() -cin @('.dll','.exe','.json','.ps1','.psm1','.psd1','.ps1xml','.cdxml','.xml','.config','.resources')) 'Bounded accepted runtime path required'
 $entry=$bootstrapRoster[$path]
 Require ($entry.bytes -is [long] -and $entry.bytes -ge 0 -and $entry.bytes -le 67108864 -and $entry.sha256 -is [string] -and $entry.sha256 -cmatch '^[0-9a-f]{64}$') 'Bounded accepted runtime entry required'
 $bootstrapTotal+=$entry.bytes;Require ($bootstrapTotal -le 1073741824) 'Accepted runtime aggregate bound'
 Add-File $path $entry.sha256 67108864
 Require ($fileBytes[$path] -eq $entry.bytes) 'Physical runtime size differs from accepted observation'
}
Add-File $BootstrapAcceptancePath $BootstrapAcceptanceSha256
Add-File $bootstrapAcceptance.manifest_path $bootstrapAcceptance.manifest_sha256
$manifestPath=Join-Path $root 'tools/migration/source-files.json'
$manifest=Read-Json $manifestPath '778386aa52d354614c689055d26a2bbc844f063f7f6cf267cc1f7ba9048bbe68'
Require ($manifest.files.Count -eq 432) 'Exact canonical432 manifest required'
foreach($entry in $manifest.files){Add-File (Join-Path $root $entry.path) $entry.sha256}
Add-File $manifestPath '778386aa52d354614c689055d26a2bbc844f063f7f6cf267cc1f7ba9048bbe68'
foreach($directory in @('tools/migration','docs/phase2')){
 foreach($file in Get-ChildItem -LiteralPath (Join-Path $root $directory) -Recurse -File){
  $relative=[IO.Path]::GetRelativePath($root,$file.FullName).Replace('\','/')
  if(($directory -ceq 'tools/migration' -and $file.Extension -in @('.py','.ps1','.json','.lock')) -or ($file.Extension -ceq '.py' -and $relative -cmatch '^docs/phase2/cho51[^/]*/')){Add-File $file.FullName}
 }
}
$base='C:\Users\aladdin-alyanai\.cache\codex-runtimes\codex-primary-runtime\dependencies\python'
foreach($directory in @((Join-Path $root '.venv/Lib/site-packages'),(Join-Path $base 'Lib'),(Join-Path $base 'DLLs'))){
 foreach($file in Get-ChildItem -LiteralPath $directory -Recurse -File){if($file.Extension.ToLowerInvariant() -in @('.py','.pyd','.dll')){Add-File $file.FullName}}
}
$previousPath=Join-Path $root 'runs/coordination/cho51_provenance_numerical_worker_20261025_v7/pins.json'
$previous=Read-Json $previousPath 'fbb97f491e52deb7f7d2c600fd647fe3f4f4099dd5135916fddcfc27f8040ce7'
$runtime=[ordered]@{}
foreach($group in @('runtime','runtime_modules','supporting_runtime_sources')){
 foreach($path in $previous[$group].Keys){Add-File $path;$runtime[$path]=$files[$path]}
}
Require ($runtime.Count -eq 27) 'Fresh27 physical runtime pin names required; old byte equality is not assumed'
$resource=Join-Path $root '.venv/Lib/site-packages/mne/data/fsaverage/fsaverage-fiducials.fif'
Add-File $resource '0043895fd3167871a947a43019228ee30060c0335967df63f571c0e71bf344a3'
Require ($fileBytes[$resource] -eq 260) 'Exact bounded dependency resource required'
$metadata=@(
 'evidence/cho51-adoption-route-20261013/owner/adoption.json',
 'evidence/cho51-adoption-route-20261013/owner/accepted-proposal.json',
 'evidence/phase2-readiness-20261012/worker/roster.json',
 'runs/coordination/cho51_provenance_numerical_worker_20261025_v7/origin-contract.json',
 'runs/coordination/cho51_provenance_numerical_worker_20261025_v7/final-review.json',
 'runs/coordination/cho51_provenance_restore_20261025_v2/final-review.json',
 'runs/coordination/cho51_linear_lineage_20261015_v2/validation_001/fixture/synthetic-input-identity.json',
 'runs/phase2/freeze_readiness/20260923_cho60hz_scope/proposed_four_method_candidates.json',
 'docs/phase2/cho51_p3_adapter_design_20261027.md',
 'docs/phase2/cho51_p3_telemetry_design_20261027.md',
 'docs/phase2/cho51_p3_adapter_review_20261027.md',
 'docs/phase2/cho51_p3_contracts_implementation_20261027.md',
 'docs/phase2/cho51_canonical_boundary_qualification_20261025.md'
)
foreach($relative in $metadata){Add-File (Join-Path $root $relative)}
Add-File $reviewPath $ReviewSha256
Add-File $coordinationPath $SourceCoordinationObservationSha256
$authorityPath=Join-Path $run 'owner-resource-amendment.json'
$authority=Read-Json $authorityPath ''
Require-Text $authority 'scope' $scope
Require-Text $authority 'applies_to' 'metadata_profile_mapping_and_telemetry_contract_tests_only'
Require ($authority.startup_ram_gib -is [long] -and $authority.startup_ram_gib -in @(4,10)) 'Exact fresh phase startup floor required'
Require-Integer $authority 'active_ram_gib' 4
Require-Integer $authority 'disk_gib' 20
Require-Boolean $authority 'canonical_guard_modified' $false
Require-Boolean $authority 'scientific_admission' $false
Add-File $authorityPath
Floors
$value=[ordered]@{
 schema='cho51_p3_contracts_pins_v1';scope=$scope;created_utc=[DateTimeOffset]::UtcNow.ToString('o')
 source_review_sha256=$ReviewSha256;reviewed_files=$reviewed;files=$files;file_bytes=$fileBytes
 preparation_source_review_sha256=$PreparationReviewSha256;source_coordination_scope=$coordination.source_scope_name;source_coordination_observation_sha256=$SourceCoordinationObservationSha256
 bootstrap_acceptance_sha256=$BootstrapAcceptanceSha256;bootstrap_manifest_sha256=$bootstrapAcceptance.manifest_sha256;accepted_powershell_runtime_files=$bootstrapRoster.Count;accepted_powershell_runtime_bytes=$bootstrapTotal
 runtime_files=$runtime;physical_files=$files.Count;physical_bytes=$script:totalBytes
 expected_tests=$review.expected_tests;test_function_counts=$review.test_function_counts;expected_stdlib_controls=34
 startup_ram_gib=$authority.startup_ram_gib;active_ram_gib=4;disk_gib=20;seconds=600
 process_mib=4096;job_mib=5120;threads=1;gpu_hidden=$true
 owner_resource_amendment_sha256=$files[$authorityPath]
 expected_numerical_budget=[ordered]@{source_updates=0;restore_count=0;support_updates=0;gradient_updates=0;target_inference_calls=0;query_count=0;model_constructions=0;measured_cells=0}
 scientific_admission=$false
}
Write-New (Join-Path $run 'pins.json') $value
[ordered]@{passed=$true;files=$files.Count;physical_bytes=$script:totalBytes;runtime_files=$runtime.Count;expected_tests=$review.expected_tests;pins_sha256=Get-Sha (Join-Path $run 'pins.json');minimum_available_ram_bytes=$script:minRam;minimum_free_disk_bytes=$script:minDisk;python_executed=$false;scientific_admission=$false}|ConvertTo-Json
