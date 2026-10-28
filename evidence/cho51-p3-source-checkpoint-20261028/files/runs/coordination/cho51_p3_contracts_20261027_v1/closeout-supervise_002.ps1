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
$scope='cho51_p3_contracts_20261027_v1_external_closeout_002'
$unitScope='cho51_p3_contracts_20261027_v1_tests'
$python='D:\Aenv\pro3\.venv\Scripts\python.exe'
$pythonBase='C:\Users\aladdin-alyanai\.cache\codex-runtimes\codex-primary-runtime\dependencies\python'
$originalReviewSha='ab2df55aa4d36c66ce7f7d238f71683eddcb7dd773543c01da08dac4790df65a'
$amendmentSha='733d6505fb24ee552ae0abd7e1bec46c14f6fc33e66a71d1adb3cf2f30c9fe75'
$pausePaths=@('20261007','20261012','20261013','20261015','20261025')|ForEach-Object{"D:\Aenv\pro2\WORK\resume-$_-001\coordination\PRO2_REQUEST_PRO3_PAUSE.json"}
$outputNames=@('closeout-dispatch_002.json','closeout-attempt_002.json','closeout-supervision_002.json','closeout-stdout_002.txt','closeout-stderr_002.txt','closeout-caller-completion_002.json','closeout-release_002.json','closeout-failure_002.json','closeout-result.json')
$held=[Collections.Generic.Dictionary[string,IO.FileStream]]::new([StringComparer]::Ordinal)
$commonQpc=$modeEntryQpc;$commonUtc=$modeEntryUtc
$windowStart=$null;$windowEnd=$null;$sourceEnd=$null
$authenticated=$false;$dispatch=$null;$process=$null;$safeHandle=$null;$handleRef=$false
$childStarted=$false;$childReaped=$false;$custodyClosed=$true;$childId=0;$childStartTicks=0
$startAttempted=$false;$startOutcome='known_not_started'
$processHaveHandleField=[Diagnostics.Process].GetField('_haveProcessHandle',([Reflection.BindingFlags]::Instance -bor [Reflection.BindingFlags]::NonPublic))
$processHandleField=[Diagnostics.Process].GetField('_processHandle',([Reflection.BindingFlags]::Instance -bor [Reflection.BindingFlags]::NonPublic))
$minimumRam=[long]::MaxValue;$minimumDisk=[long]::MaxValue
$failure=$null;$stdout=$null;$stderr=$null
$cleanupOnly=($Mode -cin @('Complete','Release'))
if($cleanupOnly){$custodyClosed=$false;$startOutcome='unknown'}
$closureGuardPassed=$true;$closureGuardRefusal=$null
$lastFloorQpc=[long]0
function Need([bool]$condition,[string]$message){if(-not $condition){throw $message}}
function Missing-Path($exception){
 $depth=0
 while($null -ne $exception.InnerException -and ($exception -is [Management.Automation.RuntimeException] -or $exception -is [Reflection.TargetInvocationException])){
  $depth++;if($depth -gt 4){throw 'Excessive filesystem exception wrapping'}
  $exception=$exception.InnerException
 }
 return (($exception -is [IO.FileNotFoundException] -and ($exception.HResult -band 65535) -eq 2) -or ($exception -is [IO.DirectoryNotFoundException] -and ($exception.HResult -band 65535) -eq 3))
}
function Present([string]$path){
 Need ([IO.Path]::IsPathFullyQualified($path) -and [IO.Path]::GetFullPath($path) -ceq $path) 'Direct normalized presence path required'
 try{[void][IO.File]::GetAttributes($path);return $true}
 catch{if(-not (Missing-Path $_.Exception)){throw}}
 $parent=[IO.Path]::GetDirectoryName($path);$depth=0
 while(-not [string]::IsNullOrEmpty($parent)){
  $depth++;Need ($depth -le 16) 'Bounded presence ancestry required'
  try{
   $attributes=[IO.File]::GetAttributes($parent)
   Need (($attributes -band [IO.FileAttributes]::Directory) -ne 0 -and ($attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0) 'Accessible direct directory ancestor required for known absence'
   return $false
  }catch{if(-not (Missing-Path $_.Exception)){throw}}
  $parent=[IO.Path]::GetDirectoryName($parent)
 }
 throw 'No accessible directory ancestor establishes known absence'
}
function Utc([string]$value){
 Need ($value -cmatch '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,7})?(Z|\+00:00)$') 'Explicit UTC required'
 return [DateTimeOffset]::Parse($value,[Globalization.CultureInfo]::InvariantCulture)
}
function Seconds{
 $nowQpc=[Diagnostics.Stopwatch]::GetTimestamp()
 Need ($nowQpc -ge $commonQpc -and $frequency -gt 0) 'Monotonic clock regression'
 return ($nowQpc-$commonQpc)/[double]$frequency
}
function Clock([double]$limit=285,[bool]$checkPauses=(-not $script:cleanupOnly)){
 $now=[DateTimeOffset]::UtcNow
 Need ((Seconds) -lt $limit -and $now -ge $commonUtc -and $now -lt $commonUtc.AddSeconds($limit)) 'Common caller deadline reached'
 if($null -ne $windowStart){Need ($now -ge $windowStart -and $now -lt $windowEnd.AddSeconds(-60)) 'Strict peer publication reserve reached'}
 if($null -ne $sourceEnd){Need ($now -lt $sourceEnd.AddSeconds(-60)) 'Strict Source publication reserve reached'}
 if($checkPauses){foreach($pausePath in $pausePaths){Need (-not (Present $pausePath)) 'Peer pause requested'}}
}
function Floor([double]$limit=240){
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
  if($cleanupOnly){try{[void](Floor 285)}catch{$script:closureGuardPassed=$false;$script:closureGuardRefusal=$_.Exception.Message}}
  else{[void](Floor)}
 }
}
function Bytes([string]$path,[string]$expected,[long]$maximum=8388608,[bool]$retain=$false){
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
   $script:jsonNodes++;Need ($depth -le 32 -and $script:jsonNodes -le 100000) 'Bounded JSON graph required'
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
function Metadata([string]$name,[string]$expected,[bool]$retain=$false){return ,(Parse (Bytes (Join-Path $run $name) $expected 8388608 $retain))}
function Retain-CloseoutRuntime($pins){
 Need ($pins.files -is [Collections.IDictionary] -and $pins.file_bytes -is [Collections.IDictionary] -and $pins.files.Count -le 25000 -and $pins.file_bytes.Count -eq $pins.files.Count) 'Bounded native pin map required'
 Need ($pins.runtime_files -is [Collections.IDictionary] -and $pins.runtime_files.Count -eq 27) 'Exact inherited27 runtime names required'
 $roster=[ordered]@{}
 foreach($path in $pins.files.Keys){
  Need ($path -is [string] -and [IO.Path]::IsPathFullyQualified($path) -and [IO.Path]::GetFullPath($path) -ceq $path) 'Normalized native pin path required'
  $powerShell=$path.StartsWith($runtime+'\',[StringComparison]::Ordinal)
  $standardLibrary=$path.StartsWith($pythonBase+'\Lib\',[StringComparison]::Ordinal) -or $path.StartsWith($pythonBase+'\DLLs\',[StringComparison]::Ordinal)
  if($powerShell -or $standardLibrary -or $pins.runtime_files.Contains($path)){$roster[$path]=$pins.files[$path]}
 }
 Need ($roster.Count -ge 34 -and $roster.Count -le 12500) 'Bounded accepted runtime selection required'
 foreach($path in @($python,(Join-Path $pythonBase 'python3.dll'),(Join-Path $pythonBase 'python312.dll'),(Join-Path $runtime 'pwsh.exe'),(Join-Path $runtime 'System.Diagnostics.Process.dll'))){Need ($roster.Contains($path)) 'Critical interpreter/outer runtime pin missing'}
 Need ($roster[$python] -ceq $request.python_executable_sha256 -and $roster[(Join-Path $runtime 'pwsh.exe')] -ceq $request.runtime_executable_sha256 -and $roster[(Join-Path $runtime 'System.Diagnostics.Process.dll')] -ceq $request.process_dll_sha256) 'Independent critical runtime hashes differ'
 $total=[long]0
 foreach($path in $roster.Keys){
  Input-Guard
  $length=$pins.file_bytes[$path];$expected=$roster[$path]
  Need ($length -is [long] -and $length -ge 0 -and $length -le 67108864 -and $expected -is [string] -and $expected -cmatch '^[0-9a-f]{64}$') 'Bounded exact runtime record required'
  $total+=$length;Need ($total -le 2147483648) 'Selected runtime aggregate exceeded'
  if($Mode -cne 'Invoke' -or $held.ContainsKey($path)){continue}
  Clock 60
  $stream=[IO.File]::Open($path,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
  $keep=$false;$digest=$null
  try{
   Need ($stream.Length -eq $length) 'Native runtime length changed'
   $digest=[Security.Cryptography.IncrementalHash]::CreateHash([Security.Cryptography.HashAlgorithmName]::SHA256)
   $buffer=[byte[]]::new(65536);$counted=[long]0
   while($true){
    Input-Guard;Clock 60
    Need ([IO.DriveInfo]::new('D:\').AvailableFreeSpace -ge 20GB) 'Runtime read disk floor refused'
    $count=$stream.Read($buffer,0,$buffer.Length);if($count -eq 0){break}
    $counted+=$count;Need ($counted -le $length) 'Native runtime file grew';$digest.AppendData($buffer,0,$count)
    Clock 60
   }
   Need ($counted -eq $length -and [Convert]::ToHexString($digest.GetHashAndReset()).ToLowerInvariant() -ceq $expected) 'Native runtime byte pin changed'
   $held.Add($path,$stream);$keep=$true
  }finally{if($null -ne $digest){$digest.Dispose()};if(-not $keep){$stream.Dispose()}}
 }
}
function Hash([byte[]]$raw){return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($raw)).ToLowerInvariant()}
function Existing([string]$name){
 Clock
 $path=Join-Path $run $name
 $stream=[IO.File]::Open($path,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
 try{
  Need ($stream.Length -gt 0 -and $stream.Length -le 8388608) 'Bounded existing receipt required'
  $raw=[byte[]]::new([int]$stream.Length);$stream.ReadExactly($raw)
  Clock
  return [ordered]@{value=(Parse $raw);sha256=(Hash $raw)}
 }finally{$stream.Dispose()}
}
function Closed($value,[string[]]$fields){
 Need ($value -is [Collections.IDictionary] -and $value.Count -eq $fields.Count) 'Closed receipt fields required'
 foreach($field in $fields){Need ($value.Contains($field)) 'Required receipt field missing'}
}
function Write-New([string]$name,$value,[double]$limit=285){
 Need ($name -cin $outputNames) 'Unowned output refused'
 Clock $limit
 $raw=[Text.UTF8Encoding]::new($false).GetBytes(($value|ConvertTo-Json -Depth 16 -Compress)+[char]10)
 Need ($raw.Length -le 8388608) 'Bounded output required'
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
 Need ($name -cin @('closeout-stdout_002.txt','closeout-stderr_002.txt') -and $raw.Length -le 1048576) 'Bounded owned stream required'
 Clock 285
 $stream=[IO.File]::Open((Join-Path $run $name),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
 try{$stream.Write($raw,0,$raw.Length);$stream.Flush($true)}finally{$stream.Dispose()}
 Clock 285
 $read=[IO.File]::OpenRead((Join-Path $run $name))
 try{Need ($read.Length -eq $raw.Length) 'Stream readback size differs';$copy=[byte[]]::new($raw.Length);$read.ReadExactly($copy);Need ((Hash $copy) -ceq (Hash $raw)) 'Stream readback SHA differs'}finally{$read.Dispose()}
 Clock 285
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
  Need ($state.data.Length+$count -le 1048576) 'Interpreter output exceeded one MiB'
  $state.data.Write($state.buffer,0,$count)
 }
}
function Original-Handle{
 Need ($null -ne $process -and $null -ne $processHaveHandleField -and $null -ne $processHandleField -and $processHaveHandleField.GetValue($process) -eq $true) 'Original Start-owned handle is not provable; no PID reopening permitted'
 $original=$processHandleField.GetValue($process)
 Need ($original -is [Microsoft.Win32.SafeHandles.SafeProcessHandle] -and -not $original.IsClosed -and -not $original.IsInvalid) 'Original retained Start handle missing'
 return ,$original
}
function Identity{
 Need ($null -ne $process -and $null -ne $safeHandle -and -not $safeHandle.IsClosed -and -not $safeHandle.IsInvalid) 'Retained process handle required'
 Need ([object]::ReferenceEquals((Original-Handle),$safeHandle) -and $safeHandle.DangerousGetHandle() -eq $handleValue -and $process.Id -eq $childId -and $process.StartTime.ToUniversalTime().Ticks -eq $childStartTicks) 'Retained process generation differs'
}
function Cleanup-Identity{
 Need ($null -ne $process -and $startAttempted) 'Only an actual Start-attempt Process may be considered for cleanup'
 $original=Original-Handle
 if($null -eq $safeHandle){$script:safeHandle=$original;$script:safeHandle.DangerousAddRef([ref]$script:handleRef);$script:handleValue=$script:safeHandle.DangerousGetHandle()}
 Need (-not $safeHandle.IsClosed -and -not $safeHandle.IsInvalid -and [object]::ReferenceEquals($original,$safeHandle) -and $safeHandle.DangerousGetHandle() -eq $handleValue) 'Original retained Start handle required for cleanup'
 if($childId -eq 0){$script:childId=$process.Id}else{Need ($process.Id -eq $childId) 'Owned process PID changed'}
 if($childStartTicks -gt 0){Need ($process.StartTime.ToUniversalTime().Ticks -eq $childStartTicks) 'Owned process generation changed'}
}
function Child-Table{
 Clock 270 $false
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
  Clock 270 $false
 }catch{$script:custodyClosed=$false;throw}
}
try{
 Need ($PSScriptRoot -ceq $run -and $PSCommandPath -ceq (Join-Path $run 'closeout-supervise_002.ps1')) 'Exact supervisor Source path required'
 if($Mode -ceq 'Begin'){
  Need ($ExternalFrequency -eq $frequency -and $ExternalEntryQpc -gt 0 -and $ExternalEntryQpc -le $modeEntryQpc) 'Fresh external pre-dispatch QPC required'
  $commonUtc=Utc $ExternalEntryUtc;$commonQpc=$ExternalEntryQpc
  Need (($modeEntryQpc-$commonQpc)/[double]$frequency -lt 5 -and $modeEntryUtc -ge $commonUtc -and $modeEntryUtc -lt $commonUtc.AddSeconds(5)) 'External pre-dispatch observation is stale'
 }else{
  Need ($ExternalEntryQpc -eq 0 -and $ExternalEntryUtc -ceq '' -and $ExternalFrequency -eq 0) 'Only Begin accepts external entry'
  $dispatchRef=Existing 'closeout-dispatch_002.json';$dispatch=$dispatchRef.value
  Closed $dispatch @('schema','scope','observed_utc','request_sha256','root_admission_sha256','scientific_admission','external_entry_qpc','external_entry_utc','qpc_frequency','begin_entry_qpc','begin_entry_utc','maximum_seconds','caller_return_observed','automatic_retry_permitted')
  Receipt $dispatch 'cho51_p3_contracts_external_dispatch_v2'
  Need ($dispatch.external_entry_qpc -is [long] -and $dispatch.qpc_frequency -is [long] -and $dispatch.qpc_frequency -eq $frequency -and $dispatch.maximum_seconds -is [long] -and $dispatch.maximum_seconds -eq 300 -and $dispatch.caller_return_observed -is [bool] -and -not $dispatch.caller_return_observed -and $dispatch.automatic_retry_permitted -is [bool] -and -not $dispatch.automatic_retry_permitted) 'Exact common dispatch clock required'
  $commonQpc=$dispatch.external_entry_qpc;$commonUtc=Utc $dispatch.external_entry_utc
 }
 Clock
 $request=Metadata 'closeout-request_002.json' $RequestSha256 $true
 $admission=Metadata 'closeout-admission_001.json' $RootAdmissionSha256 $true
 Need ($request.schema -ceq 'cho51_p3_contracts_external_request_v2' -and $admission.schema -ceq 'cho51_p3_contracts_external_admission_v1' -and $admission.accepted -is [bool] -and $admission.accepted) 'Exact fresh external Root admission required'
 Need ($admission.external_peer_decision_path -is [string] -and $admission.external_peer_decision_path.StartsWith('D:\Aenv\pro2\WORK\resume-20261027-002\coordination\',[StringComparison]::Ordinal) -and [IO.Path]::GetFullPath($admission.external_peer_decision_path) -ceq $admission.external_peer_decision_path) 'Direct actual separate external peer path required'
 $peer=Parse (Bytes $admission.external_peer_decision_path $admission.external_peer_decision_sha256 1048576 $true)
 Need ($peer.schema -ceq 'pro2_pro3_contracts_external_closeout_decision_v2' -and $peer.released -is [bool] -and $peer.released) 'Genuine explicit separate external closeout grant required'
 foreach($record in @($request,$admission,$peer)){
  if([object]::ReferenceEquals($record,$admission)){Need ($record.scope -ceq $unitScope -and $record.external_operation_scope -ceq $scope) 'Legacy unit scope plus exact external scope required'}
  else{Need ($record.scope -ceq $scope) 'Exact external closeout002 scope required'}
  foreach($field in @('source_sha256','supervisor_sha256','protocol_sha256','external_source_review_sha256','original_source_review_sha256','source_review_sha256','source_coordination_observation_sha256','owner_resource_amendment_sha256','source_scope_sha256','source_adoption_sha256','runtime_executable_sha256','process_dll_sha256','python_executable_sha256','pins_sha256','root_admission_sha256','peer_release_sha256','result_sha256','native_receipt_sha256')){Need ($record[$field] -is [string] -and $record[$field] -ceq $request[$field] -and $record[$field] -cmatch '^[0-9a-f]{64}$') 'Exact external admitted Source/runtime/result join required'}
  foreach($pair in @(@('maximum_seconds',300),@('maximum_runtime_files',12500),@('maximum_runtime_code_bytes',2147483648),@('maximum_runtime_file_bytes',67108864),@('maximum_metadata_bytes',8388608),@('startup_ram_gib',4),@('active_ram_gib',4),@('disk_gib',20),@('outer_child_processes',1),@('helper_child_processes',0),@('maximum_interpreter_invocations',1),@('maximum_jobs',0),@('publication_reserve_seconds',60),@('native_threads',1))){Need ($record[$pair[0]] -is [long] -and $record[$pair[0]] -eq $pair[1]) 'Exact external integer cap required'}
  foreach($field in @('automatic_retry_permitted','scientific_admission','native_helper_compilation_admitted','candidate_imported','numerical_execution_admitted')){Need ($record[$field] -is [bool] -and -not $record[$field]) 'External admission cannot widen execution'}
  Need ($record.native_helper_loads_parent -is [long] -and $record.native_helper_loads_parent -eq 0 -and $record.native_helper_loads_child -is [long] -and $record.native_helper_loads_child -eq 0) 'No native-helper load in external operation'
  Need ($record.bounded_cleanup_after_pause_admitted -is [bool] -and $record.bounded_cleanup_after_pause_admitted) 'Explicit bounded cleanup-only publication authority required'
  $zeroFields=@('source_updates','restore_count','support_updates','gradient_updates','target_inference_calls','query_count','model_constructions','measured_cells')
  Closed $record.expected_numerical_budget $zeroFields
  foreach($field in $zeroFields){Need ($record.expected_numerical_budget[$field] -is [long] -and $record.expected_numerical_budget[$field] -eq 0) 'Exact zero numerical budget required'}
  Need ($record.window_start_utc -ceq $request.window_start_utc -and $record.window_end_utc -ceq $request.window_end_utc) 'Exact external peer/Root/request window required'
 }
 Need ($admission.external_request_sha256 -ceq $RequestSha256 -and $peer.request_sha256 -ceq $RequestSha256) 'Actual external request joins required'
 foreach($record in @($peer,$admission)){Need ((Utc $record.observed_utc) -ge (Utc $request.created_utc) -and (Utc $record.observed_utc) -le $commonUtc) 'Actual decisions must follow request and predate dispatch'}
 $windowStart=Utc $request.window_start_utc;$windowEnd=Utc $request.window_end_utc
 foreach($field in @('source_scope_path','source_adoption_path','source_coordination_scope','peer_release_path')){foreach($record in @($peer,$admission)){Need ($record[$field] -is [string] -and $record[$field] -ceq $request[$field]) 'Exact admitted dynamic reference required'}}
 foreach($path in @($request.source_scope_path,$request.source_adoption_path)){Need ($path -is [string] -and $path.StartsWith('D:\Aenv\pro2\WORK\resume-20261027-002\coordination\',[StringComparison]::Ordinal) -and [IO.Path]::GetFullPath($path) -ceq $path) 'Actual bounded Pro2 coordination path required'}
 $coordination=Metadata 'coordination-source-observation_003.json' $request.source_coordination_observation_sha256 $true
 Need ($coordination.schema -ceq 'cho51_p3_contracts_peer_source_observation_v1' -and $coordination.pro3_validation_release -is [bool] -and -not $coordination.pro3_validation_release -and $coordination.source_scope_name -is [string] -and $coordination.source_scope_name -cmatch '^Source[0-9]{3}$' -and $coordination.source_scope_name -ceq $request.source_coordination_scope) 'Exact genuinely observed Source coexistence required'
 Need ($coordination.source_scope.path -ceq $request.source_scope_path -and $coordination.source_scope.sha256 -ceq $request.source_scope_sha256 -and $coordination.source_adoption.path -ceq $request.source_adoption_path -and $coordination.source_adoption.sha256 -ceq $request.source_adoption_sha256) 'Actual Source observation joins differ'
 $sourceScope=Parse (Bytes $request.source_scope_path $request.source_scope_sha256)
 $sourceAdoption=Parse (Bytes $request.source_adoption_path $request.source_adoption_sha256)
 $sourceEnd=Utc $sourceScope.interval_end
 Need ($sourceAdoption.Source_only_coexistence_adopted -is [bool] -and $sourceAdoption.Source_only_coexistence_adopted -and $sourceAdoption.Source_only_scope.sha256 -ceq $request.source_scope_sha256) 'Genuine separately adopted finite Source required'
 foreach($pair in @(@('Pro2_max_including_Root',3),@('Pro3_max_including_Root_and_reviewer',2),@('shared_max_including_both_roots_and_overlap',5))){Need ($sourceScope[$pair[0]] -is [long] -and $sourceScope[$pair[0]] -eq $pair[1]) 'Actual Source concurrency caps differ'}
 Need ($commonUtc -ge $windowStart -and $commonUtc -ge (Utc $sourceScope.interval_start) -and $commonUtc.AddSeconds(300) -lt $windowEnd.AddSeconds(-60) -and $commonUtc.AddSeconds(300) -lt $sourceEnd.AddSeconds(-60)) 'External whole caller and strict reserve must fit both finite windows'
 Clock
 Need ($request.output_root -ceq $run -and @($request.create_once_outputs).Count -eq $outputNames.Count) 'Exact owned output namespace required'
 for($index=0;$index -lt $outputNames.Count;$index++){Need ($request.create_once_outputs[$index] -ceq $outputNames[$index]) 'Exact ordered output names required'}
 Need ($request.runtime_root -ceq $runtime -and $PSHOME -ceq $runtime -and [Environment]::ProcessPath -ceq (Join-Path $runtime 'pwsh.exe')) 'Exact installed PowerShell process required'
 Need ($request.owner_resource_amendment_sha256 -ceq $amendmentSha) 'Exact phase-only human resource amendment required'
 $amendment=Metadata 'owner-resource-amendment.json' $amendmentSha
 Need ($amendment.scope -ceq $unitScope -and $amendment.applies_to -ceq 'metadata_profile_mapping_and_telemetry_contract_tests_only') 'Phase-only resource amendment required'
 foreach($pair in @(@('startup_ram_gib',4),@('active_ram_gib',4),@('disk_gib',20))){Need ($amendment[$pair[0]] -is [long] -and $amendment[$pair[0]] -eq $pair[1]) 'Resource amendment cap differs'}
 foreach($field in @('canonical_guard_modified','scientific_admission')){Need ($amendment[$field] -is [bool] -and -not $amendment[$field]) 'Canonical/scientific guard cannot change'}
 Need ($request.original_source_review_sha256 -ceq $originalReviewSha -and $request.source_review_sha256 -ceq $originalReviewSha) 'Exact frozen original14 Source review required'
 $originalReview=Metadata 'source-review.json' $originalReviewSha $true
 Need ($originalReview.files -is [Collections.IDictionary] -and $originalReview.files.Count -eq 14) 'Original14 review inventory required'
 foreach($relative in $originalReview.files.Keys){Need ($relative -is [string] -and $relative -notmatch '(^|/)\.\.(/|$)') 'Bounded original Source relative path';[void](Bytes (Join-Path 'D:\Aenv\pro3' $relative) $originalReview.files[$relative] 8388608 $true)}
 $review=Metadata 'closeout-source-review_002.json' $request.external_source_review_sha256 $true
 Need ($review.schema -ceq 'cho51_p3_contracts_external_source_review_v2' -and $review.source_only -is [bool] -and $review.source_only -and $review.independent_review -is [bool] -and $review.independent_review -and $review.passed -is [bool] -and $review.passed -and @($review.remaining_actionable_findings).Count -eq 0 -and $review.original_source_review_sha256 -ceq $originalReviewSha -and $review.files -is [Collections.IDictionary] -and $review.files.Count -eq 2) 'Exact clean different-author external Source review required'
 foreach($pair in @(@('closeout-supervise_002.ps1','supervisor_sha256'),@('closeout-protocol_002.md','protocol_sha256'))){
  $relative='runs/coordination/cho51_p3_contracts_20261027_v1/'+$pair[0]
  Need ($review.files[$relative] -ceq $request[$pair[1]]) 'New external Source map differs'
  [void](Bytes (Join-Path $run $pair[0]) $request[$pair[1]] 8388608 $true)
 }
 Need ($request.source_sha256 -ceq $originalReview.files['runs/coordination/cho51_p3_contracts_20261027_v1/closeout.py']) 'Frozen closeout Source join differs'
 $pins=Metadata 'pins.json' $request.pins_sha256 $true
 Need ($pins.schema -ceq 'cho51_p3_contracts_pins_v1' -and $pins.scope -ceq $unitScope -and $pins.source_review_sha256 -ceq $originalReviewSha -and $pins.reviewed_files -is [Collections.IDictionary] -and $pins.reviewed_files.Count -eq 14) 'Actual fresh fixed14 pins required'
 foreach($relative in $originalReview.files.Keys){Need ($pins.reviewed_files[$relative] -ceq $originalReview.files[$relative]) 'Fixed14 native pins cannot be replaced by external Source review'}
 foreach($pair in @(@('expected_tests',117),@('expected_stdlib_controls',34),@('startup_ram_gib',4),@('active_ram_gib',4),@('disk_gib',20))){Need ($pins[$pair[0]] -is [long] -and $pins[$pair[0]] -eq $pair[1]) 'Actual phase pins cap/inventory differs'}
 $unitAdmission=Metadata 'admission.json' $request.root_admission_sha256 $true
 Need ($unitAdmission.schema -ceq 'cho51_p3_contracts_admission_v1' -and $unitAdmission.accepted -is [bool] -and $unitAdmission.accepted -and $unitAdmission.scope -ceq $unitScope -and $unitAdmission.pins_sha256 -ceq $request.pins_sha256 -and $unitAdmission.peer_release_path -ceq $request.peer_release_path -and $unitAdmission.peer_release_sha256 -ceq $request.peer_release_sha256) 'Exact historical unit Root/peer joins required'
 Need ($request.peer_release_path -is [string] -and $request.peer_release_path.StartsWith('D:\Aenv\pro2\WORK\resume-20261027-002\coordination\',[StringComparison]::Ordinal) -and [IO.Path]::GetFullPath($request.peer_release_path) -ceq $request.peer_release_path) 'Actual historical unit peer path required'
 $unitPeer=Parse (Bytes $request.peer_release_path $request.peer_release_sha256 1048576 $true)
 Need ($unitPeer.schema -ceq 'pro2_pro3_compute_release_v1' -and $unitPeer.released -is [bool] -and $unitPeer.released -and $unitPeer.scope -ceq $unitScope -and $unitPeer.pins_sha256 -ceq $request.pins_sha256) 'Historical unit grant is distinct from fresh external grant'
 $unitResult=Metadata 't1/result.json' $request.result_sha256 $true
 Need ($unitResult.passed -is [bool] -and $unitResult.passed -and $unitResult.pins_sha256 -ceq $request.pins_sha256 -and $unitResult.native_closeout_status -ceq 'pending_external_post_job') 'Only actual passing unit result may enter external closeout'
 Need ($unitResult.native_directory -is [string] -and [IO.Path]::GetDirectoryName($unitResult.native_directory) -ceq 'D:\Aenv\pro3\runs\migration' -and [IO.Path]::GetFullPath($unitResult.native_directory) -ceq $unitResult.native_directory) 'Actual bounded native receipt directory required'
 $nativeReceipt=Parse (Bytes (Join-Path $unitResult.native_directory 'receipt.json') $request.native_receipt_sha256 8388608 $true)
 Need ($nativeReceipt.accepted -is [bool] -and $nativeReceipt.accepted -and $nativeReceipt.job_absent -is [bool] -and $nativeReceipt.job_absent -and $nativeReceipt.result.reason -ceq 'normal' -and $nativeReceipt.result.exit_code -is [long] -and $nativeReceipt.result.exit_code -eq 0) 'Accepted normal-zero closed native unit receipt required'
 [void](Bytes (Join-Path $runtime 'pwsh.exe') $request.runtime_executable_sha256 1048576 $true)
 Need ($request.process_dll_sha256 -ceq '2b4871e02b366113c6ccf3b1436fadde5e69fc0a3e3ac421e2fa0f7af8c2bc3b') 'Source-reviewed retained-handle Kill implementation pin differs'
 Need ([Diagnostics.Process].Assembly.Location -ceq (Join-Path $runtime 'System.Diagnostics.Process.dll')) 'Actual retained-handle Process implementation differs'
 [void](Bytes (Join-Path $runtime 'System.Diagnostics.Process.dll') $request.process_dll_sha256 1048576 $true)
 Retain-CloseoutRuntime $pins
 $authenticated=$true
 if($cleanupOnly){try{[void](Floor 285)}catch{$closureGuardPassed=$false;$closureGuardRefusal=$_.Exception.Message}}
 else{[void](Floor)}
 if($Mode -ceq 'Begin'){
  foreach($name in $outputNames){Need (-not (Present (Join-Path $run $name))) 'External closeout002 namespace already used'}
  foreach($name in @('closeout-supervision_001.json','closeout-supervisor-attempt_001.json','closeout-stdout_001.json','closeout-stderr_001.json')){Need (-not (Present (Join-Path $run $name))) 'Historical external attempt already used'}
  Need (-not (Present 'D:\Aenv\pro3\evidence\cho51-p3-contracts-20261027-v1')) 'Base evidence archive namespace already used'
  $record=Common 'cho51_p3_contracts_external_dispatch_v2'
  $record.external_entry_qpc=$commonQpc;$record.external_entry_utc=$commonUtc.ToString('o');$record.qpc_frequency=$frequency
  $record.begin_entry_qpc=$modeEntryQpc;$record.begin_entry_utc=$modeEntryUtc.ToString('o');$record.maximum_seconds=300
  $record.caller_return_observed=$false;$record.automatic_retry_permitted=$false
  [void](Write-New 'closeout-dispatch_002.json' $record 240)
 }elseif($Mode -ceq 'Invoke'){
  Need ($null -ne $BeginToolExitCode -and $BeginToolExitCode -eq 0) 'Actual successful Begin tool exit required before child launch'
  foreach($name in $outputNames|Where-Object{$_ -cne 'closeout-dispatch_002.json'}){Need (-not (Present (Join-Path $run $name))) 'Once-only invocation output already used'}
  $attempt=Common 'cho51_p3_contracts_external_attempt_v2';$attempt.dispatch_sha256=$dispatchRef.sha256;$attempt.helper_invocations=0;$attempt.automatic_retry_permitted=$false
  [void](Write-New 'closeout-attempt_002.json' $attempt 240)
  $samples=[Collections.Generic.List[object]]::new();$samples.Add((Floor));[Threading.Thread]::Sleep(200);$samples.Add((Floor))
  Need ((Seconds) -lt 60) 'Insufficient interpreter work and cleanup reserve'
  $startInfo=[Diagnostics.ProcessStartInfo]::new();$startInfo.FileName=$python;$startInfo.WorkingDirectory='D:\Aenv\pro3'
  $startInfo.UseShellExecute=$false;$startInfo.CreateNoWindow=$true;$startInfo.RedirectStandardOutput=$true;$startInfo.RedirectStandardError=$true
  foreach($argument in @('-I','-S','-B',(Join-Path $run 'closeout.py'),'--expect-pins',$request.pins_sha256,'--expect-external-admission',$RootAdmissionSha256)){[void]$startInfo.ArgumentList.Add($argument)}
  foreach($name in @('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS','BLIS_NUM_THREADS')){$startInfo.Environment[$name]='1'}
  $startInfo.Environment['CUDA_VISIBLE_DEVICES']='';$startInfo.Environment['PYTHONDONTWRITEBYTECODE']='1'
  Clock 240
  $process=[Diagnostics.Process]::new();$process.StartInfo=$startInfo
  $startAttempted=$true;$startOutcome='unknown';$custodyClosed=$false
  $startReturned=$process.Start()
  if(-not $startReturned){throw 'Start returned without a proven associated process; outcome remains unknown'}
  $safeHandle=Original-Handle;$safeHandle.DangerousAddRef([ref]$handleRef);$handleValue=$safeHandle.DangerousGetHandle()
  $childId=$process.Id;$childStartTicks=$process.StartTime.ToUniversalTime().Ticks
  Identity
  $childStarted=$true;$startOutcome='started';$custodyClosed=$true
  $stdout=Drain-New $process.StandardOutput.BaseStream;$stderr=Drain-New $process.StandardError.BaseStream
  Child-Table
  $nextFloor=Seconds;$nextTable=Seconds
  while(-not $process.HasExited){
   Clock 240
   Identity;Drain-Poll $stdout;Drain-Poll $stderr
   if((Seconds) -ge $nextFloor){[void](Floor);$nextFloor=(Seconds)+1}
   if((Seconds) -ge $nextTable){Child-Table;$nextTable=(Seconds)+1}
   [Threading.Thread]::Sleep(20)
  }
  $childReaped=$process.WaitForExit(0)
  Need ($childReaped -and $process.ExitCode -eq 0) 'Interpreter failed or unreaped'
  while((-not $stdout.eof -or -not $stderr.eof) -and (Seconds) -lt 270){Clock 270;Drain-Poll $stdout;Drain-Poll $stderr;[Threading.Thread]::Sleep(10)}
  Need ($stdout.eof -and $stderr.eof) 'Both stream EOF receipts required'
  Child-Table
  $stdoutRef=Write-Stream 'closeout-stdout_002.txt' $stdout.data.ToArray();$stderrRef=Write-Stream 'closeout-stderr_002.txt' $stderr.data.ToArray()
  $manifest=Existing 'closeout-result.json'
  Need ($manifest.value.schema -ceq 'cho51_p3_contracts_closeout_v1' -and $manifest.value.passed -is [bool] -and $manifest.value.passed -and $manifest.value.pins_sha256 -ceq $request.pins_sha256 -and $manifest.value.source_review_sha256 -ceq $originalReviewSha -and $manifest.value.scientific_admission -is [bool] -and -not $manifest.value.scientific_admission) 'Actual child base closeout result required; not full caller acceptance'
  $record=Common 'cho51_p3_contracts_external_supervision_v2'
  $record.dispatch_sha256=$dispatchRef.sha256;$record.attempt_sha256=(Existing 'closeout-attempt_002.json').sha256
  $record.manifest_sha256=$manifest.sha256;$record.helper_pid=$childId;$record.helper_creation_utc_ticks=$childStartTicks
  $record.start_attempted=$startAttempted;$record.start_outcome=$startOutcome
  $record.helper_invocations=1;$record.helper_exit_code=$process.ExitCode;$record.helper_reaped=$childReaped;$record.custody_closed=$custodyClosed
  $record.stdout=$stdoutRef;$record.stderr=$stderrRef;$record.stdout_eof=$stdout.eof;$record.stderr_eof=$stderr.eof
  $record.startup_samples=@($samples);$record.minimum_available_ram_bytes=$minimumRam;$record.minimum_free_disk_bytes=$minimumDisk
  $record.elapsed_seconds=Seconds;$record.caller_return_observed=$false;$record.full_caller_accepted=$false;$record.external_result_accepted=$false
  [void](Write-New 'closeout-supervision_002.json' $record 285)
 }elseif($Mode -ceq 'Complete'){
  Need ($InvokeToolCallId.Length -gt 0 -and $InvokeToolCallId.Length -le 256 -and $InvokeToolCallId -notmatch '[\r\n]') 'Actual completed Invoke tool identity required'
  Need ($null -ne $InvokeToolExitCode) 'Actual completed Invoke tool exit required'
  $supervisionSha=$null;$failureSha=$null;$operationSucceeded=$false;$operationCustody=$false;$operationStartAttempted=$false;$operationStartOutcome='unknown'
  if((Present (Join-Path $run 'closeout-failure_002.json'))){
   $failureRef=Existing 'closeout-failure_002.json';$failureRecord=$failureRef.value
   Receipt $failureRecord 'cho51_p3_contracts_external_failure_v2'
   Closed $failureRecord @('schema','scope','observed_utc','request_sha256','root_admission_sha256','scientific_admission','mode','failure','start_attempted','start_outcome','child_started','child_pid','child_reaped','custody_closed','stdout_eof','stderr_eof','stdout','stderr','partial_outputs_preserved','automatic_retry_permitted','full_caller_accepted')
   foreach($field in @('child_started','child_reaped','custody_closed','stdout_eof','stderr_eof')){Need ($failureRecord[$field] -is [bool]) 'Exact failure custody booleans required'}
   Need ($failureRecord.start_attempted -is [bool] -and $failureRecord.start_outcome -cin @('known_not_started','started','unknown')) 'Exact failure Start outcome required'
   $operationStartAttempted=$failureRecord.start_attempted;$operationStartOutcome=$failureRecord.start_outcome
   $operationCustody=$failureRecord.custody_closed -and $operationStartOutcome -cne 'unknown' -and (-not $failureRecord.child_started -or ($failureRecord.child_reaped -and $failureRecord.stdout_eof -and $failureRecord.stderr_eof))
   $failureSha=$failureRef.sha256
  }else{
   $supervisionRef=Existing 'closeout-supervision_002.json';$supervision=$supervisionRef.value
   Receipt $supervision 'cho51_p3_contracts_external_supervision_v2'
   Closed $supervision @('schema','scope','observed_utc','request_sha256','root_admission_sha256','scientific_admission','dispatch_sha256','attempt_sha256','manifest_sha256','helper_pid','helper_creation_utc_ticks','start_attempted','start_outcome','helper_invocations','helper_exit_code','helper_reaped','custody_closed','stdout','stderr','stdout_eof','stderr_eof','startup_samples','minimum_available_ram_bytes','minimum_free_disk_bytes','elapsed_seconds','caller_return_observed','full_caller_accepted','external_result_accepted')
   foreach($field in @('helper_reaped','custody_closed','stdout_eof','stderr_eof')){Need ($supervision[$field] -is [bool] -and $supervision[$field]) 'Incomplete custody cannot complete successfully'}
   Need ($supervision.dispatch_sha256 -ceq $dispatchRef.sha256 -and $supervision.helper_invocations -is [long] -and $supervision.helper_invocations -eq 1 -and $supervision.helper_exit_code -is [long] -and $supervision.helper_exit_code -eq 0) 'Failed/partial operation cannot pass'
   Need ($supervision.start_attempted -is [bool] -and $supervision.start_attempted -and $supervision.start_outcome -ceq 'started') 'Proven successful Start required'
   $operationStartAttempted=$true;$operationStartOutcome='started'
   $supervisionSha=$supervisionRef.sha256;$operationSucceeded=$true;$operationCustody=$true
  }
  $record=Common 'cho51_p3_contracts_external_caller_completion_v2';$record.dispatch_sha256=$dispatchRef.sha256;$record.supervision_sha256=$supervisionSha;$record.failure_sha256=$failureSha
  $record.invoke_tool_call_id=$InvokeToolCallId;$record.post_invoke_return_upper_bound_qpc=$modeEntryQpc;$record.post_invoke_return_upper_bound_utc=$modeEntryUtc.ToString('o')
  $record.invoke_tool_exit_code=[int]$InvokeToolExitCode
  $record.start_attempted=$operationStartAttempted;$record.start_outcome=$operationStartOutcome
  $record.qpc_frequency=$frequency;$record.external_entry_qpc=$commonQpc;$record.elapsed_upper_bound_seconds=($modeEntryQpc-$commonQpc)/[double]$frequency
  $record.observation_semantics='Root dispatched Complete only after actual Invoke tool completion; Complete entry is an upper bound, not the exact return instant'
  $record.invoke_tool_return_observed_by_root=$true;$record.operation_succeeded=($operationSucceeded -and $closureGuardPassed -and $InvokeToolExitCode -eq 0);$record.custody_closed=$operationCustody;$record.closure_guard_passed=$closureGuardPassed;$record.closure_guard_refusal=$closureGuardRefusal;$record.release_published=$false;$record.full_caller_accepted=$false
  [void](Write-New 'closeout-caller-completion_002.json' $record 285)
 }else{
  Need ($null -ne $CompleteToolExitCode) 'Actual completed Complete tool exit required'
  $completionRef=Existing 'closeout-caller-completion_002.json';$completion=$completionRef.value
  Receipt $completion 'cho51_p3_contracts_external_caller_completion_v2'
  Closed $completion @('schema','scope','observed_utc','request_sha256','root_admission_sha256','scientific_admission','dispatch_sha256','supervision_sha256','failure_sha256','invoke_tool_call_id','post_invoke_return_upper_bound_qpc','post_invoke_return_upper_bound_utc','invoke_tool_exit_code','start_attempted','start_outcome','qpc_frequency','external_entry_qpc','elapsed_upper_bound_seconds','observation_semantics','invoke_tool_return_observed_by_root','operation_succeeded','custody_closed','closure_guard_passed','closure_guard_refusal','release_published','full_caller_accepted')
  Need ($completion.invoke_tool_return_observed_by_root -is [bool] -and $completion.invoke_tool_return_observed_by_root -and $completion.post_invoke_return_upper_bound_qpc -is [long] -and $completion.post_invoke_return_upper_bound_qpc -lt $modeEntryQpc -and $completion.external_entry_qpc -eq $commonQpc -and $completion.qpc_frequency -eq $frequency -and $completion.dispatch_sha256 -ceq $dispatchRef.sha256 -and $completion.operation_succeeded -is [bool] -and $completion.custody_closed -is [bool]) 'Actual earlier caller completion required'
  Need ($completion.invoke_tool_exit_code -is [long] -and (-not $completion.operation_succeeded -or $completion.invoke_tool_exit_code -eq 0)) 'Actual nonzero Invoke cannot become successful'
  Need ($completion.start_attempted -is [bool] -and $completion.start_outcome -cin @('known_not_started','started','unknown') -and ($completion.start_outcome -cne 'unknown' -or -not $completion.custody_closed)) 'Unknown Start cannot be released'
  if($null -ne $completion.supervision_sha256){Need ((Existing 'closeout-supervision_002.json').sha256 -ceq $completion.supervision_sha256 -and $null -eq $completion.failure_sha256 -and -not (Present (Join-Path $run 'closeout-failure_002.json'))) 'Supervision changed after caller observation'}
  else{Need ((Existing 'closeout-failure_002.json').sha256 -ceq $completion.failure_sha256 -and $null -eq $completion.supervision_sha256) 'Failure changed after caller observation'}
  $record=Common 'cho51_p3_contracts_external_release_v2';$record.dispatch_sha256=$dispatchRef.sha256;$record.caller_completion_sha256=$completionRef.sha256
  $record.external_entry_qpc=$commonQpc;$record.qpc_frequency=$frequency;$record.release_publication_elapsed_seconds=Seconds
  $record.start_attempted=$completion.start_attempted;$record.start_outcome=$completion.start_outcome
  $record.complete_tool_exit_code=[int]$CompleteToolExitCode;$record.operation_succeeded=($completion.operation_succeeded -and $closureGuardPassed -and $CompleteToolExitCode -eq 0);$record.custody_closed=$completion.custody_closed;$record.operation_released=$completion.custody_closed;$record.closure_guard_passed=$closureGuardPassed;$record.closure_guard_refusal=$closureGuardRefusal;$record.release_tool_return_observed=$false;$record.post_release_external_audit_required=$true;$record.full_caller_accepted=$false;$record.external_result_accepted=$false
  [void](Write-New 'closeout-release_002.json' $record 285)
 }
}catch{
 $failure=$_.Exception.Message
 $cleanupOnly=$true
 $failureStdout=$null;$failureStderr=$null;$partialPreserved=(-not $startAttempted -and $startOutcome -ceq 'known_not_started')
 if($startAttempted -and $startOutcome -cne 'known_not_started'){
  try{
   Cleanup-Identity
   if(-not $process.HasExited){$process.Kill()}
   while((Seconds) -lt 270 -and -not $process.HasExited){
    Clock 270 $false
    if($null -ne $stdout){Drain-Poll $stdout};if($null -ne $stderr){Drain-Poll $stderr}
    [void]$process.WaitForExit(20)
   }
   $childReaped=$process.WaitForExit(0)
   if($null -eq $stdout){$stdout=Drain-New $process.StandardOutput.BaseStream}
   if($null -eq $stderr){$stderr=Drain-New $process.StandardError.BaseStream}
   while((Seconds) -lt 270 -and (-not $stdout.eof -or -not $stderr.eof)){
    Clock 270 $false;Drain-Poll $stdout;Drain-Poll $stderr;[Threading.Thread]::Sleep(10)
   }
   if(-not $childReaped -or -not $stdout.eof -or -not $stderr.eof){$custodyClosed=$false}
   if($childStartTicks -gt 0){Child-Table}else{$custodyClosed=$false}
  }catch{$custodyClosed=$false}
  try{
   if($null -ne $stdout -and -not (Present (Join-Path $run 'closeout-stdout_002.txt'))){$failureStdout=Write-Stream 'closeout-stdout_002.txt' $stdout.data.ToArray()}
   if($null -ne $stderr -and -not (Present (Join-Path $run 'closeout-stderr_002.txt'))){$failureStderr=Write-Stream 'closeout-stderr_002.txt' $stderr.data.ToArray()}
   $partialPreserved=((Present (Join-Path $run 'closeout-stdout_002.txt')) -and (Present (Join-Path $run 'closeout-stderr_002.txt')))
  }catch{$partialPreserved=$false}
 }
 if($startOutcome -ceq 'unknown'){$custodyClosed=$false}
 if($authenticated){
  try{
   $record=Common 'cho51_p3_contracts_external_failure_v2';$record.mode=$Mode;$record.failure=$failure.Substring(0,[math]::Min(512,$failure.Length))
   $record.start_attempted=$startAttempted;$record.start_outcome=$startOutcome
   $record.child_started=$childStarted;$record.child_pid=$childId;$record.child_reaped=$childReaped;$record.custody_closed=$custodyClosed
   $record.stdout_eof=($null -ne $stdout -and $stdout.eof);$record.stderr_eof=($null -ne $stderr -and $stderr.eof)
   $record.stdout=$failureStdout;$record.stderr=$failureStderr;$record.partial_outputs_preserved=$partialPreserved;$record.automatic_retry_permitted=$false;$record.full_caller_accepted=$false
   [void](Write-New 'closeout-failure_002.json' $record 285)
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
Clock 285
[ordered]@{mode=$Mode;elapsed_seconds=(Seconds);full_caller_accepted=$false;post_release_external_audit_required=$true;scientific_admission=$false}|ConvertTo-Json -Compress
