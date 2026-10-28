param(
 [Parameter(Mandatory)][ValidateSet('Begin','Invoke','Complete','Release')][string]$Mode,
 [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$RequestSha256,
 [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$RootAdmissionSha256,
 [long]$ExternalEntryQpc=0,
 [string]$ExternalEntryUtc='',
 [long]$ExternalFrequency=0,
 [string]$InvokeToolCallId='',
 [Nullable[int]]$BeginToolExitCode=$null,
 [Nullable[int]]$InvokeToolExitCode=$null,
 [Nullable[int]]$CompleteToolExitCode=$null
)
$ErrorActionPreference='Stop'
$modeEntryQpc=[Diagnostics.Stopwatch]::GetTimestamp()
$modeEntryUtc=[DateTimeOffset]::UtcNow
$frequency=[Diagnostics.Stopwatch]::Frequency
$run='D:\Aenv\pro3\runs\coordination\cho51_p3_contracts_20261027_v1'
$runtime='C:\Users\aladdin-alyanai\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell'
$scope='cho51_p3_contracts_20261027_v1_bootstrap_observation_002'
$scopeSha='b04507102cc00306e99ce9992cd0a526da03101e7d972e79eed6d20aab354739'
$adoptionSha='29dce6bd6b7767449b0bc28d8daeed1023581748d82be41d4eb82cabcf8804ab'
$amendmentSha='733d6505fb24ee552ae0abd7e1bec46c14f6fc33e66a71d1adb3cf2f30c9fe75'
$pausePaths=@('20261007','20261012','20261013','20261015','20261025')|ForEach-Object{"D:\Aenv\pro2\WORK\resume-$_-001\coordination\PRO2_REQUEST_PRO3_PAUSE.json"}
$outputNames=@('bootstrap-dispatch_002.json','bootstrap-attempt_002.json','bootstrap-supervision_002.json','bootstrap-stdout_002.txt','bootstrap-stderr_002.txt','bootstrap-caller-completion_002.json','bootstrap-release_002.json','bootstrap-failure_002.json','bootstrap-helper-attempt_002.json','preparation-bootstrap-pins_002.json')
$held=[Collections.Generic.Dictionary[string,IO.FileStream]]::new([StringComparer]::Ordinal)
$commonQpc=$modeEntryQpc;$commonUtc=$modeEntryUtc
$windowStart=$null;$windowEnd=$null;$sourceEnd=$null
$authenticated=$false;$dispatch=$null;$process=$null;$safeHandle=$null;$handleRef=$false
$childStarted=$false;$childReaped=$false;$custodyClosed=$true;$childId=0;$childStartTicks=0
$minimumRam=[long]::MaxValue;$minimumDisk=[long]::MaxValue
$failure=$null;$stdout=$null;$stderr=$null
$cleanupOnly=($Mode -cin @('Complete','Release'))
$closureGuardPassed=$true;$closureGuardRefusal=$null
$lastFloorQpc=[long]0
function Need([bool]$condition,[string]$message){if(-not $condition){throw $message}}
function Utc([string]$value){
 Need ($value -cmatch '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,7})?(Z|\+00:00)$') 'Explicit UTC required'
 return [DateTimeOffset]::Parse($value,[Globalization.CultureInfo]::InvariantCulture)
}
function Seconds{
 $nowQpc=[Diagnostics.Stopwatch]::GetTimestamp()
 Need ($nowQpc -ge $commonQpc -and $frequency -gt 0) 'Monotonic clock regression'
 return ($nowQpc-$commonQpc)/[double]$frequency
}
function Clock([double]$limit=85,[bool]$checkPauses=(-not $script:cleanupOnly)){
 $now=[DateTimeOffset]::UtcNow
 Need ((Seconds) -lt $limit -and $now -ge $commonUtc -and $now -lt $commonUtc.AddSeconds($limit)) 'Common caller deadline reached'
 if($null -ne $windowStart){Need ($now -ge $windowStart -and $now -lt $windowEnd.AddSeconds(-60)) 'Strict peer publication reserve reached'}
 if($null -ne $sourceEnd){Need ($now -lt $sourceEnd.AddSeconds(-60)) 'Strict Source publication reserve reached'}
 if($checkPauses){foreach($pausePath in $pausePaths){Need (-not [IO.File]::Exists($pausePath)) 'Peer pause requested'}}
}
function Floor([double]$limit=65){
 Clock $limit $true
 $rows=@(Get-CimInstance -ClassName Win32_OperatingSystem -OperationTimeoutSec 3)
 Need ($rows.Count -eq 1) 'One local resource observation required'
 $available=[long]$rows[0].FreePhysicalMemory*1024
 $disk=[IO.DriveInfo]::new('D:\').AvailableFreeSpace
 $script:minimumRam=[math]::Min($script:minimumRam,$available)
 $script:minimumDisk=[math]::Min($script:minimumDisk,$disk)
 $script:lastFloorQpc=[Diagnostics.Stopwatch]::GetTimestamp()
 Clock $limit $true
 Need ($available -ge 4GB -and $disk -ge 20GB) 'Active resource floor refused'
 return [ordered]@{observed_utc=[DateTimeOffset]::UtcNow.ToString('o');available_ram_bytes=$available;free_disk_bytes=$disk}
}
function Input-Guard{
 Clock
 if(([Diagnostics.Stopwatch]::GetTimestamp()-$lastFloorQpc)/[double]$frequency -ge 1){
  if($cleanupOnly){try{[void](Floor 85)}catch{$script:closureGuardPassed=$false;$script:closureGuardRefusal=$_.Exception.Message}}
  else{[void](Floor)}
 }
}
function Bytes([string]$path,[string]$expected,[long]$maximum=1048576,[bool]$retain=$false){
 Input-Guard
 Need ($expected -cmatch '^[0-9a-f]{64}$' -and [IO.Path]::IsPathFullyQualified($path)) 'Exact independent file pin required'
 $stream=[IO.File]::Open($path,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
 $keep=$false
 try{
  Need ($stream.Length -gt 0 -and $stream.Length -le $maximum) 'Bounded nonempty control file required'
  $raw=[byte[]]::new([int]$stream.Length);$offset=0
  while($offset -lt $raw.Length){
   Input-Guard
   $disk=[IO.DriveInfo]::new('D:\').AvailableFreeSpace
   Need ($disk -ge 20GB) 'Read disk floor refused'
   $count=$stream.Read($raw,$offset,[math]::Min(65536,$raw.Length-$offset))
   Need ($count -gt 0) 'Truncated pinned input'
   $offset+=$count
   Clock
  }
  Need ($stream.ReadByte() -eq -1) 'Pinned input grew'
  Need ([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($raw)).ToLowerInvariant() -ceq $expected) 'Independent input SHA differs'
  if($retain){Need (-not $held.ContainsKey($path)) 'Duplicate retained input';$held.Add($path,$stream);$keep=$true}
  return ,$raw
 }finally{if(-not $keep){$stream.Dispose()}}
}
function Parse([byte[]]$raw){
 $document=[Text.Json.JsonDocument]::Parse([ReadOnlyMemory[byte]]::new($raw))
 try{
  $script:jsonNodes=0
  function Inspect($element,[int]$depth){
   $script:jsonNodes++;Need ($depth -le 32 -and $script:jsonNodes -le 50000) 'Bounded JSON graph required'
   if($element.ValueKind -eq [Text.Json.JsonValueKind]::Object){
    $names=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    foreach($property in $element.EnumerateObject()){Need ($names.Add($property.Name)) 'Duplicate JSON property';Inspect $property.Value ($depth+1)}
   }elseif($element.ValueKind -eq [Text.Json.JsonValueKind]::Array){foreach($item in $element.EnumerateArray()){Inspect $item ($depth+1)}}
   elseif($element.ValueKind -eq [Text.Json.JsonValueKind]::Number){$number=$element.GetDouble();Need (-not [double]::IsInfinity($number) -and -not [double]::IsNaN($number)) 'Finite JSON number required'}
  }
  Inspect $document.RootElement 0
 }finally{$document.Dispose()}
 return ,([Text.UTF8Encoding]::new($false,$true).GetString($raw)|ConvertFrom-Json -AsHashtable -DateKind String)
}
function Metadata([string]$name,[string]$expected,[bool]$retain=$false){return ,(Parse (Bytes (Join-Path $run $name) $expected 1048576 $retain))}
function Hash([byte[]]$raw){return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($raw)).ToLowerInvariant()}
function Existing([string]$name){
 Clock
 $path=Join-Path $run $name
 $stream=[IO.File]::Open($path,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
 try{
  Need ($stream.Length -gt 0 -and $stream.Length -le 1048576) 'Bounded existing receipt required'
  $raw=[byte[]]::new([int]$stream.Length);$stream.ReadExactly($raw)
  Clock
  return [ordered]@{value=(Parse $raw);sha256=(Hash $raw)}
 }finally{$stream.Dispose()}
}
function Closed($value,[string[]]$fields){
 Need ($value -is [Collections.IDictionary] -and $value.Count -eq $fields.Count) 'Closed receipt fields required'
 foreach($field in $fields){Need ($value.Contains($field)) 'Required receipt field missing'}
}
function Write-New([string]$name,$value,[double]$limit=85){
 Need ($name -cin $outputNames) 'Unowned output refused'
 Clock $limit
 $raw=[Text.UTF8Encoding]::new($false).GetBytes(($value|ConvertTo-Json -Depth 16 -Compress)+[char]10)
 Need ($raw.Length -le 1048576) 'Bounded output required'
 Clock $limit
 $stream=[IO.File]::Open((Join-Path $run $name),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
 try{$stream.Write($raw,0,$raw.Length);$stream.Flush($true)}finally{$stream.Dispose()}
 Clock $limit
 [void](Bytes (Join-Path $run $name) (Hash $raw))
 Clock $limit
 if($cleanupOnly -and $value.Contains('operation_succeeded') -and $value.operation_succeeded){Need ($closureGuardPassed) 'Closure guard changed during publication; no accepted pass'}
 return (Hash $raw)
}
function Write-Stream([string]$name,[byte[]]$raw){
 Need ($name -cin @('bootstrap-stdout_002.txt','bootstrap-stderr_002.txt') -and $raw.Length -le 1048576) 'Bounded owned stream required'
 Clock 85
 $stream=[IO.File]::Open((Join-Path $run $name),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
 try{$stream.Write($raw,0,$raw.Length);$stream.Flush($true)}finally{$stream.Dispose()}
 Clock 85
 $read=[IO.File]::OpenRead((Join-Path $run $name))
 try{Need ($read.Length -eq $raw.Length) 'Stream readback size differs';$copy=[byte[]]::new($raw.Length);$read.ReadExactly($copy);Need ((Hash $copy) -ceq (Hash $raw)) 'Stream readback SHA differs'}finally{$read.Dispose()}
 Clock 85
 return [ordered]@{path=(Join-Path $run $name);bytes=$raw.Length;sha256=(Hash $raw)}
}
function Common([string]$schema){return [ordered]@{schema=$schema;scope=$scope;observed_utc=[DateTimeOffset]::UtcNow.ToString('o');request_sha256=$RequestSha256;root_admission_sha256=$RootAdmissionSha256;scientific_admission=$false}}
function Receipt($value,[string]$schema){
 Need ($value.schema -ceq $schema -and $value.scope -ceq $scope -and $value.request_sha256 -ceq $RequestSha256 -and $value.root_admission_sha256 -ceq $RootAdmissionSha256) 'Receipt authority join differs'
 Need ($value.scientific_admission -is [bool] -and -not $value.scientific_admission) 'No scientific admission permitted'
}
function Drain-New($stream){return [ordered]@{stream=$stream;buffer=[byte[]]::new(65536);data=[IO.MemoryStream]::new();task=$null;eof=$false}}
function Drain-Poll($state){
 for($iteration=0;$iteration -lt 16 -and -not $state.eof;$iteration++){
  if($null -eq $state.task){$state.task=$state.stream.ReadAsync($state.buffer,0,$state.buffer.Length)}
  if(-not $state.task.IsCompleted){break}
  $count=$state.task.GetAwaiter().GetResult();$state.task=$null
  if($count -eq 0){$state.eof=$true;break}
  Need ($state.data.Length+$count -le 1048576) 'Helper output exceeded one MiB'
  $state.data.Write($state.buffer,0,$count)
 }
}
function Identity{
 Need ($null -ne $process -and $null -ne $safeHandle -and -not $safeHandle.IsClosed -and -not $safeHandle.IsInvalid) 'Retained process handle required'
 Need ([object]::ReferenceEquals($process.SafeHandle,$safeHandle) -and $process.SafeHandle.DangerousGetHandle() -eq $handleValue -and $process.Id -eq $childId -and $process.StartTime.ToUniversalTime().Ticks -eq $childStartTicks) 'Retained process generation differs'
}
function Cleanup-Identity{
 Need ($null -ne $process -and $childStarted) 'Only the actual started Process may be terminated'
 if($null -eq $safeHandle){$script:safeHandle=$process.SafeHandle;$script:safeHandle.DangerousAddRef([ref]$script:handleRef);$script:handleValue=$script:safeHandle.DangerousGetHandle()}
 Need (-not $safeHandle.IsClosed -and -not $safeHandle.IsInvalid -and [object]::ReferenceEquals($process.SafeHandle,$safeHandle) -and $process.SafeHandle.DangerousGetHandle() -eq $handleValue) 'Original retained Start handle required for cleanup'
 if($childId -eq 0){$script:childId=$process.Id}else{Need ($process.Id -eq $childId) 'Owned process PID changed'}
 if($childStartTicks -gt 0){Need ($process.StartTime.ToUniversalTime().Ticks -eq $childStartTicks) 'Owned process generation changed'}
}
function Child-Table{
 Clock 80 $false
 try{
  $count=0;$seenHelper=$false
  foreach($parentId in @($PID,$childId)){
   foreach($row in Get-CimInstance -ClassName Win32_Process -Filter "ParentProcessId = $parentId" -OperationTimeoutSec 3){
    $count++;Need ($count -le 64) 'Process table row cap exceeded'
    Need ($parentId -eq $PID -and [long]$row.ProcessId -eq $childId -and [long]$row.ParentProcessId -eq $PID) 'Unexpected descendant; no authority to kill it'
    Need ($row.CreationDate -is [datetime] -and [math]::Abs($row.CreationDate.ToUniversalTime().Ticks-$childStartTicks) -le 10000) 'CIM helper generation differs'
    $seenHelper=$true
   }
  }
  Need ($process.HasExited -or $seenHelper) 'Live retained helper missing from process table'
  Clock 80 $false
 }catch{$script:custodyClosed=$false;throw}
}
try{
 Need ($PSScriptRoot -ceq $run -and $PSCommandPath -ceq (Join-Path $run 'bootstrap-supervise_002.ps1')) 'Exact supervisor Source path required'
 if($Mode -ceq 'Begin'){
  Need ($ExternalFrequency -eq $frequency -and $ExternalEntryQpc -gt 0 -and $ExternalEntryQpc -le $modeEntryQpc) 'Fresh external pre-dispatch QPC required'
  $commonUtc=Utc $ExternalEntryUtc;$commonQpc=$ExternalEntryQpc
  Need (($modeEntryQpc-$commonQpc)/[double]$frequency -lt 5 -and $modeEntryUtc -ge $commonUtc -and $modeEntryUtc -lt $commonUtc.AddSeconds(5)) 'External pre-dispatch observation is stale'
 }else{
  Need ($ExternalEntryQpc -eq 0 -and $ExternalEntryUtc -ceq '' -and $ExternalFrequency -eq 0) 'Only Begin accepts external entry'
  $dispatchRef=Existing 'bootstrap-dispatch_002.json';$dispatch=$dispatchRef.value
  Closed $dispatch @('schema','scope','observed_utc','request_sha256','root_admission_sha256','scientific_admission','external_entry_qpc','external_entry_utc','qpc_frequency','begin_entry_qpc','begin_entry_utc','maximum_seconds','caller_return_observed','automatic_retry_permitted')
  Receipt $dispatch 'cho51_p3_bootstrap_dispatch_v2'
  Need ($dispatch.external_entry_qpc -is [long] -and $dispatch.qpc_frequency -is [long] -and $dispatch.qpc_frequency -eq $frequency -and $dispatch.maximum_seconds -is [long] -and $dispatch.maximum_seconds -eq 90 -and $dispatch.caller_return_observed -is [bool] -and -not $dispatch.caller_return_observed -and $dispatch.automatic_retry_permitted -is [bool] -and -not $dispatch.automatic_retry_permitted) 'Exact common dispatch clock required'
  $commonQpc=$dispatch.external_entry_qpc;$commonUtc=Utc $dispatch.external_entry_utc
 }
 Clock
 $request=Metadata 'bootstrap-request_002.json' $RequestSha256 $true
 $admission=Metadata 'bootstrap-admission_002.json' $RootAdmissionSha256 $true
 Need ($request.schema -ceq 'cho51_p3_bootstrap_observation_request_v1' -and $admission.schema -ceq 'cho51_p3_bootstrap_observation_admission_v1' -and $admission.accepted -is [bool] -and $admission.accepted) 'Exact fresh Root admission required'
 Need ($admission.peer_decision_path -is [string] -and $admission.peer_decision_path.StartsWith('D:\Aenv\pro2\WORK\resume-20261027-002\coordination\',[StringComparison]::Ordinal)) 'Actual Pro2 peer decision path required'
 $peer=Parse (Bytes $admission.peer_decision_path $admission.peer_decision_sha256 1048576 $true)
 Need ($peer.schema -ceq 'pro2_pro3_bootstrap_observation_decision_v1' -and $peer.released -is [bool] -and $peer.released) 'Genuine explicit peer bootstrap grant required'
 foreach($record in @($request,$admission,$peer)){
  Need ($record.scope -ceq $scope) 'Exact bootstrap002 scope required'
  foreach($field in @('source_sha256','supervisor_sha256','protocol_sha256','source_review_sha256','helper_source_review_sha256','supervisor_source_review_sha256','owner_resource_amendment_sha256','source_scope_sha256','source_adoption_sha256','runtime_executable_sha256','process_dll_sha256')){Need ($record[$field] -is [string] -and $record[$field] -ceq $request[$field] -and $record[$field] -cmatch '^[0-9a-f]{64}$') 'Exact admitted Source/runtime join required'}
  foreach($pair in @(@('maximum_seconds',90),@('maximum_files',2500),@('maximum_code_bytes',1073741824),@('maximum_enumerated_entries',10000),@('maximum_directory_depth',16),@('maximum_manifest_bytes',1048576),@('startup_ram_gib',4),@('active_ram_gib',4),@('disk_gib',20),@('outer_child_processes',1),@('helper_child_processes',0),@('python_invocations',0),@('jobs',0),@('publication_reserve_seconds',60))){Need ($record[$pair[0]] -is [long] -and $record[$pair[0]] -eq $pair[1]) 'Exact integer admission cap required'}
  foreach($field in @('automatic_retry_permitted','native_helper_compilation_admitted','scientific_admission')){Need ($record[$field] -is [bool] -and -not $record[$field]) 'Admission cannot widen scope'}
  Need ($record.bounded_cleanup_after_pause_admitted -is [bool] -and $record.bounded_cleanup_after_pause_admitted) 'Explicit bounded cleanup-only publication authority required'
  $zeroFields=@('source_updates','restore_count','support_updates','gradient_updates','target_inference_calls','query_count','model_constructions','measured_cells')
  Closed $record.expected_numerical_budget $zeroFields
  foreach($field in $zeroFields){Need ($record.expected_numerical_budget[$field] -is [long] -and $record.expected_numerical_budget[$field] -eq 0) 'Exact zero numerical budget required'}
  Need ($record.window_start_utc -ceq $request.window_start_utc -and $record.window_end_utc -ceq $request.window_end_utc) 'Exact peer/Root/request window required'
 }
 foreach($record in @($peer,$admission)){Need ($record.request_sha256 -ceq $RequestSha256 -and (Utc $record.observed_utc) -le $commonUtc) 'Actual decisions must predate external dispatch'}
 $windowStart=Utc $request.window_start_utc;$windowEnd=Utc $request.window_end_utc
 $sourceScope=Parse (Bytes 'D:\Aenv\pro2\WORK\resume-20261027-002\coordination\ROOT_PRO3_NEW_FINITE_SOURCE_ONLY_COEXISTENCE_SCOPE_009_001.json' $scopeSha)
 $sourceAdoption=Parse (Bytes 'D:\Aenv\pro2\WORK\resume-20261027-002\coordination\ROOT_PRO3_SOURCE_ONLY_COEXISTENCE009_DIFFERENT_REVIEW_ADOPTION_001.json' $adoptionSha)
 $sourceEnd=Utc $sourceScope.interval_end
 Need ($request.source_scope_sha256 -ceq $scopeSha -and $request.source_adoption_sha256 -ceq $adoptionSha -and $sourceAdoption.Source_only_coexistence_adopted -is [bool] -and $sourceAdoption.Source_only_coexistence_adopted -and $sourceAdoption.Source_only_scope.sha256 -ceq $scopeSha) 'Actual Source009 authority required'
 foreach($pair in @(@('Pro2_max_including_Root',3),@('Pro3_max_including_Root_and_reviewer',2),@('shared_max_including_both_roots_and_overlap',5))){Need ($sourceScope[$pair[0]] -is [long] -and $sourceScope[$pair[0]] -eq $pair[1]) 'Source009 concurrency caps differ'}
 Need ($commonUtc -ge $windowStart -and $commonUtc -ge (Utc $sourceScope.interval_start) -and $commonUtc.AddSeconds(90) -lt $windowEnd.AddSeconds(-60) -and $commonUtc.AddSeconds(90) -lt $sourceEnd.AddSeconds(-60)) 'External whole caller and strict reserve must fit both windows'
 Clock
 Need ($request.output_root -ceq $run -and @($request.create_once_outputs).Count -eq $outputNames.Count) 'Exact owned output namespace required'
 for($index=0;$index -lt $outputNames.Count;$index++){Need ($request.create_once_outputs[$index] -ceq $outputNames[$index]) 'Exact ordered output names required'}
 Need ($request.runtime_root -ceq $runtime -and $PSHOME -ceq $runtime -and [Environment]::ProcessPath -ceq (Join-Path $runtime 'pwsh.exe')) 'Exact installed PowerShell process required'
 Need ($request.owner_resource_amendment_sha256 -ceq $amendmentSha) 'Exact fresh human resource amendment required'
 $amendment=Metadata 'owner-resource-amendment.json' $amendmentSha
 Need ($amendment.scope -ceq 'cho51_p3_contracts_20261027_v1_tests' -and $amendment.applies_to -ceq 'metadata_profile_mapping_and_telemetry_contract_tests_only') 'Phase-only resource amendment required'
 foreach($pair in @(@('startup_ram_gib',4),@('active_ram_gib',4),@('disk_gib',20))){Need ($amendment[$pair[0]] -is [long] -and $amendment[$pair[0]] -eq $pair[1]) 'Resource amendment cap differs'}
 foreach($field in @('canonical_guard_modified','scientific_admission')){Need ($amendment[$field] -is [bool] -and -not $amendment[$field]) 'Canonical/scientific guard cannot change'}
 $review=Metadata 'bootstrap-source-review_002.json' $request.source_review_sha256
 Need ($review.schema -ceq 'cho51_p3_bootstrap_source_review_v2' -and $review.source_only -is [bool] -and $review.source_only -and @($review.remaining_actionable_findings).Count -eq 0 -and $review.source_sha256 -ceq $request.source_sha256 -and $review.files.Count -eq 3) 'Exact clean consolidated three-Source review required'
 Need ($review.helper_source_review_path -ceq (Join-Path $run 'helper-source-review_002.json') -and $review.supervisor_source_review_path -ceq (Join-Path $run 'bootstrap-supervisor-source-review_002.json') -and $review.helper_source_review_sha256 -ceq $request.helper_source_review_sha256 -and $review.supervisor_source_review_sha256 -ceq $request.supervisor_source_review_sha256) 'Exact different-author receipts required'
 $helperReview=Metadata 'helper-source-review_002.json' $request.helper_source_review_sha256
 $supervisorReview=Metadata 'bootstrap-supervisor-source-review_002.json' $request.supervisor_source_review_sha256
 foreach($record in @($helperReview,$supervisorReview)){Need ($record.source_only -is [bool] -and $record.source_only -and @($record.remaining_actionable_findings).Count -eq 0) 'Different-author findings remain'}
 Need ($helperReview.schema -ceq 'cho51_p3_bootstrap_helper_source_review_v2' -and $helperReview.source_sha256 -ceq $request.source_sha256 -and $supervisorReview.schema -ceq 'cho51_p3_bootstrap_supervisor_source_review_v2' -and $supervisorReview.files.Count -eq 2 -and $supervisorReview.files[(Join-Path $run 'bootstrap-supervise_002.ps1')] -ceq $request.supervisor_sha256 -and $supervisorReview.files[(Join-Path $run 'bootstrap-protocol_002.md')] -ceq $request.protocol_sha256) 'Different-author Source review map differs'
 foreach($pair in @(@('bootstrap-observation_002.ps1','source_sha256'),@('bootstrap-supervise_002.ps1','supervisor_sha256'),@('bootstrap-protocol_002.md','protocol_sha256'))){
  $path=Join-Path $run $pair[0]
  Need ($review.files[$path] -ceq $request[$pair[1]]) 'Composite Source map differs'
  [void](Bytes $path $request[$pair[1]] 1048576 $true)
 }
 [void](Bytes (Join-Path $runtime 'pwsh.exe') $request.runtime_executable_sha256 1048576 $true)
 Need ($request.process_dll_sha256 -ceq '2b4871e02b366113c6ccf3b1436fadde5e69fc0a3e3ac421e2fa0f7af8c2bc3b') 'Source-reviewed retained-handle Kill implementation pin differs'
 Need ([Diagnostics.Process].Assembly.Location -ceq (Join-Path $runtime 'System.Diagnostics.Process.dll')) 'Actual retained-handle Process implementation differs'
 [void](Bytes (Join-Path $runtime 'System.Diagnostics.Process.dll') $request.process_dll_sha256 1048576 $true)
 $authenticated=$true
 if($cleanupOnly){try{[void](Floor 85)}catch{$closureGuardPassed=$false;$closureGuardRefusal=$_.Exception.Message}}
 else{[void](Floor)}
 if($Mode -ceq 'Begin'){
  foreach($name in $outputNames){Need (-not [IO.File]::Exists((Join-Path $run $name))) 'Bootstrap002 namespace already used'}
  $record=Common 'cho51_p3_bootstrap_dispatch_v2'
  $record.external_entry_qpc=$commonQpc;$record.external_entry_utc=$commonUtc.ToString('o');$record.qpc_frequency=$frequency
  $record.begin_entry_qpc=$modeEntryQpc;$record.begin_entry_utc=$modeEntryUtc.ToString('o');$record.maximum_seconds=90
  $record.caller_return_observed=$false;$record.automatic_retry_permitted=$false
  [void](Write-New 'bootstrap-dispatch_002.json' $record 65)
 }elseif($Mode -ceq 'Invoke'){
  Need ($null -ne $BeginToolExitCode -and $BeginToolExitCode -eq 0) 'Actual successful Begin tool exit required before child launch'
  foreach($name in $outputNames|Where-Object{$_ -cne 'bootstrap-dispatch_002.json'}){Need (-not [IO.File]::Exists((Join-Path $run $name))) 'Once-only invocation output already used'}
  $attempt=Common 'cho51_p3_bootstrap_attempt_v2';$attempt.dispatch_sha256=$dispatchRef.sha256;$attempt.helper_invocations=0;$attempt.automatic_retry_permitted=$false
  [void](Write-New 'bootstrap-attempt_002.json' $attempt 65)
  $samples=[Collections.Generic.List[object]]::new();$samples.Add((Floor));[Threading.Thread]::Sleep(200);$samples.Add((Floor))
  Need ((Seconds) -lt 15) 'Insufficient helper work and cleanup reserve'
  $startInfo=[Diagnostics.ProcessStartInfo]::new();$startInfo.FileName=Join-Path $runtime 'pwsh.exe';$startInfo.WorkingDirectory='D:\Aenv\pro3'
  $startInfo.UseShellExecute=$false;$startInfo.CreateNoWindow=$true;$startInfo.RedirectStandardOutput=$true;$startInfo.RedirectStandardError=$true
  foreach($argument in @('-NoProfile','-NonInteractive','-File',(Join-Path $run 'bootstrap-observation_002.ps1'),'-RequestSha256',$RequestSha256,'-RootAdmissionSha256',$RootAdmissionSha256)){[void]$startInfo.ArgumentList.Add($argument)}
  Clock 65
  $process=[Diagnostics.Process]::new();$process.StartInfo=$startInfo
  Need ($process.Start()) 'Owned helper launch failed'
  $childStarted=$true;$safeHandle=$process.SafeHandle;$safeHandle.DangerousAddRef([ref]$handleRef);$handleValue=$safeHandle.DangerousGetHandle()
  $childId=$process.Id;$childStartTicks=$process.StartTime.ToUniversalTime().Ticks
  Identity
  $stdout=Drain-New $process.StandardOutput.BaseStream;$stderr=Drain-New $process.StandardError.BaseStream
  Child-Table
  $nextFloor=Seconds;$nextTable=Seconds
  while(-not $process.HasExited){
   Clock 65
   Identity;Drain-Poll $stdout;Drain-Poll $stderr
   if((Seconds) -ge $nextFloor){[void](Floor);$nextFloor=(Seconds)+1}
   if((Seconds) -ge $nextTable){Child-Table;$nextTable=(Seconds)+1}
   [Threading.Thread]::Sleep(20)
  }
  $childReaped=$process.WaitForExit(0)
  Need ($childReaped -and $process.ExitCode -eq 0) 'Helper failed or unreaped'
  while((-not $stdout.eof -or -not $stderr.eof) -and (Seconds) -lt 80){Clock 80;Drain-Poll $stdout;Drain-Poll $stderr;[Threading.Thread]::Sleep(10)}
  Need ($stdout.eof -and $stderr.eof) 'Both stream EOF receipts required'
  Child-Table
  $stdoutRef=Write-Stream 'bootstrap-stdout_002.txt' $stdout.data.ToArray();$stderrRef=Write-Stream 'bootstrap-stderr_002.txt' $stderr.data.ToArray()
  $helperAttempt=Existing 'bootstrap-helper-attempt_002.json';$manifest=Existing 'preparation-bootstrap-pins_002.json'
  Need ($manifest.value.schema -ceq 'cho51_p3_powershell_bootstrap_observation_v1' -and $manifest.value.scope -ceq $scope -and $manifest.value.request_sha256 -ceq $RequestSha256 -and $manifest.value.root_admission_sha256 -ceq $RootAdmissionSha256) 'Helper observational output join differs'
  $record=Common 'cho51_p3_bootstrap_supervision_v2'
  $record.dispatch_sha256=$dispatchRef.sha256;$record.attempt_sha256=(Existing 'bootstrap-attempt_002.json').sha256
  $record.helper_attempt_sha256=$helperAttempt.sha256;$record.manifest_sha256=$manifest.sha256;$record.helper_pid=$childId;$record.helper_creation_utc_ticks=$childStartTicks
  $record.helper_invocations=1;$record.helper_exit_code=$process.ExitCode;$record.helper_reaped=$childReaped;$record.custody_closed=$custodyClosed
  $record.stdout=$stdoutRef;$record.stderr=$stderrRef;$record.stdout_eof=$stdout.eof;$record.stderr_eof=$stderr.eof
  $record.startup_samples=@($samples);$record.minimum_available_ram_bytes=$minimumRam;$record.minimum_free_disk_bytes=$minimumDisk
  $record.elapsed_seconds=Seconds;$record.caller_return_observed=$false;$record.full_caller_accepted=$false;$record.observational_manifest_accepted=$false
  [void](Write-New 'bootstrap-supervision_002.json' $record 85)
 }elseif($Mode -ceq 'Complete'){
  Need ($InvokeToolCallId.Length -gt 0 -and $InvokeToolCallId.Length -le 256 -and $InvokeToolCallId -notmatch '[\r\n]') 'Actual completed Invoke tool identity required'
  Need ($null -ne $InvokeToolExitCode) 'Actual completed Invoke tool exit required'
  $supervisionSha=$null;$failureSha=$null;$operationSucceeded=$false;$operationCustody=$false
  if([IO.File]::Exists((Join-Path $run 'bootstrap-failure_002.json'))){
   $failureRef=Existing 'bootstrap-failure_002.json';$failureRecord=$failureRef.value
   Receipt $failureRecord 'cho51_p3_bootstrap_failure_v2'
   Closed $failureRecord @('schema','scope','observed_utc','request_sha256','root_admission_sha256','scientific_admission','mode','failure','child_started','child_pid','child_reaped','custody_closed','stdout_eof','stderr_eof','stdout','stderr','partial_outputs_preserved','automatic_retry_permitted','full_caller_accepted')
   foreach($field in @('child_started','child_reaped','custody_closed','stdout_eof','stderr_eof')){Need ($failureRecord[$field] -is [bool]) 'Exact failure custody booleans required'}
   $operationCustody=$failureRecord.custody_closed -and (-not $failureRecord.child_started -or ($failureRecord.child_reaped -and $failureRecord.stdout_eof -and $failureRecord.stderr_eof))
   $failureSha=$failureRef.sha256
  }else{
   $supervisionRef=Existing 'bootstrap-supervision_002.json';$supervision=$supervisionRef.value
   Receipt $supervision 'cho51_p3_bootstrap_supervision_v2'
   Closed $supervision @('schema','scope','observed_utc','request_sha256','root_admission_sha256','scientific_admission','dispatch_sha256','attempt_sha256','helper_attempt_sha256','manifest_sha256','helper_pid','helper_creation_utc_ticks','helper_invocations','helper_exit_code','helper_reaped','custody_closed','stdout','stderr','stdout_eof','stderr_eof','startup_samples','minimum_available_ram_bytes','minimum_free_disk_bytes','elapsed_seconds','caller_return_observed','full_caller_accepted','observational_manifest_accepted')
   foreach($field in @('helper_reaped','custody_closed','stdout_eof','stderr_eof')){Need ($supervision[$field] -is [bool] -and $supervision[$field]) 'Incomplete custody cannot complete successfully'}
   Need ($supervision.dispatch_sha256 -ceq $dispatchRef.sha256 -and $supervision.helper_invocations -is [long] -and $supervision.helper_invocations -eq 1 -and $supervision.helper_exit_code -is [long] -and $supervision.helper_exit_code -eq 0) 'Failed/partial operation cannot pass'
   $supervisionSha=$supervisionRef.sha256;$operationSucceeded=$true;$operationCustody=$true
  }
  $record=Common 'cho51_p3_bootstrap_caller_completion_v2';$record.dispatch_sha256=$dispatchRef.sha256;$record.supervision_sha256=$supervisionSha;$record.failure_sha256=$failureSha
  $record.invoke_tool_call_id=$InvokeToolCallId;$record.post_invoke_return_upper_bound_qpc=$modeEntryQpc;$record.post_invoke_return_upper_bound_utc=$modeEntryUtc.ToString('o')
  $record.invoke_tool_exit_code=[int]$InvokeToolExitCode
  $record.qpc_frequency=$frequency;$record.external_entry_qpc=$commonQpc;$record.elapsed_upper_bound_seconds=($modeEntryQpc-$commonQpc)/[double]$frequency
  $record.observation_semantics='Root dispatched Complete only after actual Invoke tool completion; Complete entry is an upper bound, not the exact return instant'
  $record.invoke_tool_return_observed_by_root=$true;$record.operation_succeeded=($operationSucceeded -and $closureGuardPassed -and $InvokeToolExitCode -eq 0);$record.custody_closed=$operationCustody;$record.closure_guard_passed=$closureGuardPassed;$record.closure_guard_refusal=$closureGuardRefusal;$record.release_published=$false;$record.full_caller_accepted=$false
  [void](Write-New 'bootstrap-caller-completion_002.json' $record 85)
 }else{
  Need ($null -ne $CompleteToolExitCode) 'Actual completed Complete tool exit required'
  $completionRef=Existing 'bootstrap-caller-completion_002.json';$completion=$completionRef.value
  Receipt $completion 'cho51_p3_bootstrap_caller_completion_v2'
  Closed $completion @('schema','scope','observed_utc','request_sha256','root_admission_sha256','scientific_admission','dispatch_sha256','supervision_sha256','failure_sha256','invoke_tool_call_id','post_invoke_return_upper_bound_qpc','post_invoke_return_upper_bound_utc','invoke_tool_exit_code','qpc_frequency','external_entry_qpc','elapsed_upper_bound_seconds','observation_semantics','invoke_tool_return_observed_by_root','operation_succeeded','custody_closed','closure_guard_passed','closure_guard_refusal','release_published','full_caller_accepted')
  Need ($completion.invoke_tool_return_observed_by_root -is [bool] -and $completion.invoke_tool_return_observed_by_root -and $completion.post_invoke_return_upper_bound_qpc -is [long] -and $completion.post_invoke_return_upper_bound_qpc -lt $modeEntryQpc -and $completion.external_entry_qpc -eq $commonQpc -and $completion.qpc_frequency -eq $frequency -and $completion.dispatch_sha256 -ceq $dispatchRef.sha256 -and $completion.operation_succeeded -is [bool] -and $completion.custody_closed -is [bool]) 'Actual earlier caller completion required'
  Need ($completion.invoke_tool_exit_code -is [long] -and (-not $completion.operation_succeeded -or $completion.invoke_tool_exit_code -eq 0)) 'Actual nonzero Invoke cannot become successful'
  if($null -ne $completion.supervision_sha256){Need ((Existing 'bootstrap-supervision_002.json').sha256 -ceq $completion.supervision_sha256 -and $null -eq $completion.failure_sha256 -and -not [IO.File]::Exists((Join-Path $run 'bootstrap-failure_002.json'))) 'Supervision changed after caller observation'}
  else{Need ((Existing 'bootstrap-failure_002.json').sha256 -ceq $completion.failure_sha256 -and $null -eq $completion.supervision_sha256) 'Failure changed after caller observation'}
  $record=Common 'cho51_p3_bootstrap_release_v2';$record.dispatch_sha256=$dispatchRef.sha256;$record.caller_completion_sha256=$completionRef.sha256
  $record.external_entry_qpc=$commonQpc;$record.qpc_frequency=$frequency;$record.release_publication_elapsed_seconds=Seconds
  $record.complete_tool_exit_code=[int]$CompleteToolExitCode;$record.operation_succeeded=($completion.operation_succeeded -and $closureGuardPassed -and $CompleteToolExitCode -eq 0);$record.custody_closed=$completion.custody_closed;$record.operation_released=$completion.custody_closed;$record.closure_guard_passed=$closureGuardPassed;$record.closure_guard_refusal=$closureGuardRefusal;$record.release_tool_return_observed=$false;$record.post_release_external_audit_required=$true;$record.full_caller_accepted=$false;$record.observational_manifest_accepted=$false
  [void](Write-New 'bootstrap-release_002.json' $record 85)
 }
}catch{
 $failure=$_.Exception.Message
 $cleanupOnly=$true
 $failureStdout=$null;$failureStderr=$null;$partialPreserved=(-not $childStarted)
 if($childStarted){
  try{
   Cleanup-Identity
   if(-not $process.HasExited){$process.Kill()}
   while((Seconds) -lt 80 -and -not $process.HasExited){
    Clock 80 $false
    if($null -ne $stdout){Drain-Poll $stdout};if($null -ne $stderr){Drain-Poll $stderr}
    [void]$process.WaitForExit(20)
   }
   $childReaped=$process.WaitForExit(0)
   if($null -eq $stdout){$stdout=Drain-New $process.StandardOutput.BaseStream}
   if($null -eq $stderr){$stderr=Drain-New $process.StandardError.BaseStream}
   while((Seconds) -lt 80 -and (-not $stdout.eof -or -not $stderr.eof)){
    Clock 80 $false;Drain-Poll $stdout;Drain-Poll $stderr;[Threading.Thread]::Sleep(10)
   }
   if(-not $childReaped -or -not $stdout.eof -or -not $stderr.eof){$custodyClosed=$false}
   if($childStartTicks -gt 0){Child-Table}else{$custodyClosed=$false}
  }catch{$custodyClosed=$false}
  try{
   if($null -ne $stdout -and -not [IO.File]::Exists((Join-Path $run 'bootstrap-stdout_002.txt'))){$failureStdout=Write-Stream 'bootstrap-stdout_002.txt' $stdout.data.ToArray()}
   if($null -ne $stderr -and -not [IO.File]::Exists((Join-Path $run 'bootstrap-stderr_002.txt'))){$failureStderr=Write-Stream 'bootstrap-stderr_002.txt' $stderr.data.ToArray()}
   $partialPreserved=([IO.File]::Exists((Join-Path $run 'bootstrap-stdout_002.txt')) -and [IO.File]::Exists((Join-Path $run 'bootstrap-stderr_002.txt')))
  }catch{$partialPreserved=$false}
 }
 if($authenticated){
  try{
   $record=Common 'cho51_p3_bootstrap_failure_v2';$record.mode=$Mode;$record.failure=$failure.Substring(0,[math]::Min(512,$failure.Length))
   $record.child_started=$childStarted;$record.child_pid=$childId;$record.child_reaped=$childReaped;$record.custody_closed=$custodyClosed
   $record.stdout_eof=($null -ne $stdout -and $stdout.eof);$record.stderr_eof=($null -ne $stderr -and $stderr.eof)
   $record.stdout=$failureStdout;$record.stderr=$failureStderr;$record.partial_outputs_preserved=$partialPreserved;$record.automatic_retry_permitted=$false;$record.full_caller_accepted=$false
   [void](Write-New 'bootstrap-failure_002.json' $record 85)
  }catch{}
 }
}finally{
 if($null -ne $stdout){$stdout.stream.Dispose();$stdout.data.Dispose()}
 if($null -ne $stderr){$stderr.stream.Dispose();$stderr.data.Dispose()}
 if($handleRef){$safeHandle.DangerousRelease()}
 if($null -ne $process){$process.Dispose()}
 foreach($stream in $held.Values){$stream.Dispose()}
}
if($null -ne $failure){throw $failure}
Clock 85
[ordered]@{mode=$Mode;elapsed_seconds=(Seconds);full_caller_accepted=$false;post_release_external_audit_required=$true;scientific_admission=$false}|ConvertTo-Json -Compress
