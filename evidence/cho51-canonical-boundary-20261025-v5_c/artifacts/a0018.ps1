param([Parameter(Mandatory)][string]$ReviewSha256,[Parameter(Mandatory)][int]$ExpectedTests)
$ErrorActionPreference='Stop'
$root='D:\Aenv\pro3'
$run=$PSScriptRoot
$utf8=[Text.UTF8Encoding]::new($false)
function Get-Sha($path){
    $before=Get-Item -LiteralPath $path -Force
    $ancestor=$before
    while($null -ne $ancestor){if($ancestor.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Reparse source/runtime refused'};$ancestor=if($ancestor -is [IO.FileInfo]){$ancestor.Directory}else{$ancestor.Parent}}
    $sha=(Get-FileHash -LiteralPath $path).Hash.ToLowerInvariant()
    $after=Get-Item -LiteralPath $path -Force
    if($before.Length -ne $after.Length -or $before.LastWriteTimeUtc -ne $after.LastWriteTimeUtc -or $before.CreationTimeUtc -ne $after.CreationTimeUtc){throw 'Source/runtime identity changed'}
    $sha
}
function Write-New($path,$value){
    $raw=$utf8.GetBytes(($value|ConvertTo-Json -Depth 40)+[char]10)
    $stream=[IO.File]::Open($path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
    try{$stream.Write($raw,0,$raw.Length);$stream.Flush($true)}finally{$stream.Dispose()}
}
if((Get-Sha (Join-Path $run 'source-review.json')) -cne $ReviewSha256){throw 'Review changed'}
$review=Get-Content (Join-Path $run 'source-review.json') -Raw|ConvertFrom-Json -DateKind String
if($review.source_only -ne $true -or @($review.remaining_actionable_findings).Count -ne 0 -or $review.expected_tests -ne $ExpectedTests -or $ExpectedTests -le 0 -or $review.expected_stdlib_controls -ne 34){throw 'Settled source/test/current-control inventory review required'}
$batchId='b'
$planPath=Join-Path $root 'docs/phase2/cho51_canonical_boundary_batch_plan_20261025.json'
$planSha='d1467ae85739115f2f65ab1ca23a8f6624b1a09d1a6b40384f64c07eab62497f'
$scopeDocument=Join-Path $root 'docs/phase2/cho51_canonical_boundary_split_validation_20261025.md'
if((Get-Sha $planPath) -cne $planSha -or (Get-Sha $scopeDocument) -cne 'e792de74461fe54269714c0e3a175ee6ee357ed99943ac345a54c7b6f48bb55b'){throw 'Frozen split plan or scope changed'}
$plan=Get-Content -LiteralPath $planPath -Raw|ConvertFrom-Json -DateKind String
$batch=$plan.batches.$batchId
$functions=@($batch.function_counts.PSObject.Properties.Name)
if($ExpectedTests -ne $batch.expected_tests -or $review.batch_id -cne $batchId -or $review.expected_full_tests -ne 133 -or $review.batch_plan_sha256 -cne $planSha -or ((@($review.batch_functions) -join [char]10) -cne ($functions -join [char]10))){throw 'Exact reviewed full collection and selected function plan required'}
$reviewed=[ordered]@{}
$files=[ordered]@{}
foreach($entry in $review.files.PSObject.Properties){$path=Join-Path $root $entry.Name;$sha=Get-Sha $path;if($sha -cne $entry.Value){throw 'Reviewed source changed'};$reviewed[$entry.Name]=$sha;$files[$path]=$sha}
$familySources=@($plan.candidate_files.PSObject.Properties.Name)
foreach($member in @('a','b','c')){foreach($name in @('metadata_common.py','guard.py','runner.py','closeout.py','prepare.ps1','launch.ps1')){$familySources+=('runs/coordination/cho51_canonical_boundary_20261025_v5_'+$member+'/'+$name)}}
$familySources+='runs/coordination/cho51_canonical_boundary_20261025_v5_aggregate/aggregate.py'
if($reviewed.Count -ne 22 -or @(Compare-Object -CaseSensitive ($familySources|Sort-Object) (@($reviewed.Keys)|Sort-Object)).Count -ne 0){throw 'Exact complete22-source family review required'}
foreach($member in @('a','b','c')){foreach($name in @('source-review.json','owner-resource-amendment.json')){$path=Join-Path $root ('runs/coordination/cho51_canonical_boundary_20261025_v5_'+$member+'/'+$name);$files[$path]=Get-Sha $path}}
$files[$planPath]=$planSha
$files[$scopeDocument]=Get-Sha $scopeDocument
$manifestPath=Join-Path $root 'tools/migration/source-files.json'
if((Get-Sha $manifestPath) -cne '778386aa52d354614c689055d26a2bbc844f063f7f6cf267cc1f7ba9048bbe68'){throw 'Canonical source manifest changed'}
$manifest=Get-Content $manifestPath -Raw|ConvertFrom-Json -DateKind String
if(@($manifest.files).Count -ne 432){throw 'Canonical inventory count'}
foreach($entry in $manifest.files){$path=Join-Path $root $entry.path;$sha=Get-Sha $path;if($sha -cne $entry.sha256){throw 'Canonical source bytes changed'};$files[$path]=$sha}
$files[$manifestPath]=Get-Sha $manifestPath
foreach($directory in @('tools/migration','docs/phase2')){foreach($file in Get-ChildItem -LiteralPath (Join-Path $root $directory) -Recurse -File){$relative=[IO.Path]::GetRelativePath($root,$file.FullName).Replace('\','/');if(($directory -eq 'tools/migration' -and $file.Extension -in @('.py','.ps1','.json','.lock')) -or ($file.Extension -eq '.py' -and $relative -match '^docs/phase2/cho51[^/]*/')){$files[$file.FullName]=Get-Sha $file.FullName}}}
$base='C:\Users\aladdin-alyanai\.cache\codex-runtimes\codex-primary-runtime\dependencies\python'
foreach($directory in @((Join-Path $root '.venv/Lib/site-packages'),(Join-Path $base 'Lib'),(Join-Path $base 'DLLs'))){
    foreach($file in Get-ChildItem -LiteralPath $directory -Recurse -File){if($file.Extension.ToLowerInvariant() -in @('.py','.pyd','.dll')){$files[$file.FullName]=Get-Sha $file.FullName}}
}
$previousPath=Join-Path $root 'runs/coordination/cho51_provenance_numerical_worker_20261025_v7/pins.json'
if((Get-Sha $previousPath) -cne 'fbb97f491e52deb7f7d2c600fd647fe3f4f4099dd5135916fddcfc27f8040ce7'){throw 'Historical runtime inventory changed'}
$previous=Get-Content $previousPath -Raw|ConvertFrom-Json -DateKind String
$runtime=[ordered]@{}
foreach($group in @('runtime','runtime_modules','supporting_runtime_sources')){foreach($entry in $previous.$group.PSObject.Properties){$runtime[$entry.Name]=Get-Sha $entry.Name;$files[$entry.Name]=$runtime[$entry.Name]}}
if($runtime.Count -ne 27){throw 'Exact fresh runtime27 inventory required'}
$resource=Join-Path $root '.venv/Lib/site-packages/mne/data/fsaverage/fsaverage-fiducials.fif'
$resourceSha=Get-Sha $resource
if((Get-Item $resource).Length -ne 260 -or $resourceSha -cne '0043895fd3167871a947a43019228ee30060c0335967df63f571c0e71bf344a3'){throw 'Exact bounded runtime fiducial resource required'}
$files[$resource]=$resourceSha
$metadata=@(
'evidence/cho51-adoption-route-20261013/owner/adoption.json',
'evidence/cho51-adoption-route-20261013/owner/accepted-proposal.json',
'evidence/phase2-readiness-20261012/worker/roster.json',
'runs/coordination/cho51_provenance_numerical_worker_20261025_v7/origin-contract.json',
'runs/coordination/cho51_provenance_numerical_worker_20261025_v7/final-review.json',
'runs/coordination/cho51_provenance_restore_20261025_v2/final-review.json',
'runs/phase2/freeze_readiness/20260923_cho60hz_scope/proposed_four_method_candidates.json',
'docs/phase2/cho51_canonical_boundary_plan_20261025.md',
'docs/phase2/cho51_canonical_pipeline_interface_audit_20261025.md',
'docs/phase2/cho51_canonical_boundary_implementation_20261025.md',
'docs/phase2/cho51_canonical_boundary_operations_successor_20261025.md',
'docs/phase2/cho51_canonical_boundary_available_ram_successor_20261025.md',
'docs/phase2/cho51_canonical_boundary_windows_command_successor_20261025.md',
'runs/coordination/cho51_canonical_boundary_20261025_v4/timeout-closeout_001.json',
'runs/coordination/cho51_canonical_boundary_20261025_v4/timeout-closeout-supervision_001.json',
'runs/coordination/cho51_canonical_boundary_20261025_v4/lease-closeout_001.json',
'runs/migration/20261025T182023Z_be9e746d5e/receipt.json',
'runs/coordination/cho51_canonical_boundary_20261025_v3/t1/failure.json',
'runs/coordination/cho51_canonical_boundary_20261025_v3/failure-closeout_001.json',
'runs/coordination/cho51_canonical_boundary_20261025_v3/failure-closeout-supervision_001.json',
'runs/coordination/cho51_canonical_boundary_20261025_v3/lease-closeout_001.json',
'runs/migration/20261025T174304Z_a04cf394b0/receipt.json',
'runs/coordination/cho51_canonical_boundary_20261025_v2/lease-closeout_001.json',
'runs/coordination/cho51_canonical_boundary_20261025_v2/refusal-closeout_001.json',
'runs/migration/20261025T170414Z_bd82341364/receipt.json',
'runs/coordination/cho51_canonical_boundary_20261025_v1/lease-closeout_001.json',
'runs/coordination/cho51_canonical_boundary_20261025_v1/failure-closeout_001.json',
'runs/migration/20261025T163106Z_e0e0f64c37/receipt.json'
)
foreach($relative in $metadata){$path=Join-Path $root $relative;$files[$path]=Get-Sha $path}
$amendmentPath=Join-Path $run 'owner-resource-amendment.json'
$amendmentSha=Get-Sha $amendmentPath
$files[$amendmentPath]=$amendmentSha
$amendment=Get-Content $amendmentPath -Raw|ConvertFrom-Json -DateKind String
if($amendment.owner_instruction_exact -cne 'use what you have . i have freed the ram you have more now!' -or $amendment.startup_ram_gib -ne 4 -or $amendment.active_ram_gib -ne 4){throw 'New owner startup4 authority required'}
$files[(Join-Path $run 'source-review.json')]=$ReviewSha256
$value=[ordered]@{schema='cho51_canonical_boundary_pins_v1';scope='cho51_canonical_boundary_20261025_v5_b_tests';created_utc=[DateTimeOffset]::UtcNow.ToString('o');source_review_sha256=$ReviewSha256;reviewed_files=$reviewed;files=$files;runtime_files=$runtime;expected_tests=$ExpectedTests;expected_stdlib_controls=34;startup_ram_gib=4;active_ram_gib=4;disk_gib=20;seconds=600;process_mib=4096;job_mib=5120;threads=1;gpu_hidden=$true;owner_resource_amendment_sha256=$amendmentSha;expected_numerical_budget=[ordered]@{source_updates=0;restore_count=0;support_updates=0;gradient_updates=0;target_inference_calls=0;query_count=0;model_constructions=0;measured_cells=0};scientific_admission=$false}
$value.batch_id=$batchId
$value.batch_plan_sha256=$planSha
$value.expected_full_tests=133
$value.batch_functions=$functions
$value.batch_function_counts=$batch.function_counts
Write-New (Join-Path $run 'pins.json') $value
[ordered]@{passed=$true;files=$files.Count;runtime_files=$runtime.Count;expected_tests=$ExpectedTests;pins_sha256=Get-Sha (Join-Path $run 'pins.json');python_executed=$false;scientific_admission=$false}|ConvertTo-Json
