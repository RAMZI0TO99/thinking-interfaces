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
$scope='cho51_p3_contracts_20261027_v1_bootstrap_observation_005'
$scopeSha='';$adoptionSha=''
$amendmentSha='733d6505fb24ee552ae0abd7e1bec46c14f6fc33e66a71d1adb3cf2f30c9fe75'
$pausePaths=@('20261007','20261012','20261013','20261015','20261025')|ForEach-Object{"D:\Aenv\pro2\WORK\resume-$_-001\coordination\PRO2_REQUEST_PRO3_PAUSE.json"}
$outputNames=@('bootstrap-dispatch_005.json','bootstrap-attempt_005.json','bootstrap-supervision_005.json','bootstrap-stdout_005.txt','bootstrap-stderr_005.txt','bootstrap-caller-completion_005.json','bootstrap-release_005.json','bootstrap-failure_005.json','bootstrap-helper-attempt_005.json','preparation-bootstrap-pins_005.json')
$held=[Collections.Generic.Dictionary[string,IO.FileStream]]::new([StringComparer]::Ordinal)
$commonQpc=$modeEntryQpc;$commonUtc=$modeEntryUtc
$windowStart=$null;$windowEnd=$null;$sourceEnd=$null
$authenticated=$false;$dispatch=$null;$process=$null;$safeHandle=$null;$handleRef=$false
$childStarted=$false;$childReaped=$false;$custodyClosed=($Mode -cin @('Begin','Invoke'));$childId=0;$childStartTicks=0
$startAttempted=$false;$startOutcome=if($custodyClosed){'not_attempted'}else{'unknown'}
$minimumRam=[long]::MaxValue;$minimumDisk=[long]::MaxValue
$failure=$null;$stdout=$null;$stderr=$null
$cleanupOnly=($Mode -cin @('Complete','Release'))
$closureGuardPassed=$true;$closureGuardRefusal=$null
$lastFloorQpc=[long]0
function Need([bool]$condition,[string]$message){if(-not $condition){throw $message}}
$diagnostics=[ordered]@{schema='cho51_p3_bootstrap_diagnostics_v5';complete=$true;overflow=$false;controller=[ordered]@{pid=[long]$PID;start_utc_ticks=$null;process_path=$null;path_truncated=$false;metadata_complete=$false};helper=[ordered]@{pid=$null;start_utc_ticks=$null};primary_failure=$null;first_refusal=$null;events=[Collections.Generic.List[object]]::new();table_summaries=[ordered]@{};rows=[Collections.Generic.List[object]]::new();custody_refused=$false;final_table_verified=$false;table_call_ordinal=0}
$operationStage='preflight'
$diagnosticRowBytes=0;$diagnosticNormalEventBytes=0;$diagnosticCleanupEventBytes=0
function Diagnostic-Failed{$script:diagnostics.complete=$false}
function Diagnostic-Exception($exception){
 $type=$exception.GetType().FullName;$message=[string]$exception.Message
 return [ordered]@{type=$type.Substring(0,[math]::Min(128,$type.Length));hresult=[long]$exception.HResult;message=$message.Substring(0,[math]::Min(256,$message.Length));type_truncated=($type.Length -gt 128);message_truncated=($message.Length -gt 256)}
}
function Diagnostic-Event([string]$stage,[string]$outcome,$exception=$null){
 try{
  if($diagnostics.events.Count -ge 32){$diagnostics.overflow=$true;$diagnostics.complete=$false;return}
  $details=$null;if($null -ne $exception){$details=Diagnostic-Exception $exception}
  $value=[ordered]@{stage=$stage;outcome=$outcome;qpc=[Diagnostics.Stopwatch]::GetTimestamp();utc=[DateTimeOffset]::UtcNow.ToString('o');exception=$details}
  $bytes=[Text.UTF8Encoding]::new($false).GetByteCount(($value|ConvertTo-Json -Depth 8 -Compress))
  if($stage.StartsWith('cleanup_',[StringComparison]::Ordinal)){
   if($diagnosticCleanupEventBytes+$bytes -gt 8192 -or @($diagnostics.events|Where-Object{$_.stage.StartsWith('cleanup_',[StringComparison]::Ordinal)}).Count -ge 16){$diagnostics.overflow=$true;$diagnostics.complete=$false;return}
   $script:diagnosticCleanupEventBytes+=$bytes
  }else{
   if($diagnosticNormalEventBytes+$bytes -gt 8192 -or @($diagnostics.events|Where-Object{-not $_.stage.StartsWith('cleanup_',[StringComparison]::Ordinal)}).Count -ge 16){$diagnostics.overflow=$true;$diagnostics.complete=$false;return}
   $script:diagnosticNormalEventBytes+=$bytes
  }
  $diagnostics.events.Add($value)
 }catch{Diagnostic-Failed}
}
function Diagnostic-Controller{
 try{
  $self=[Diagnostics.Process]::GetCurrentProcess()
  try{$diagnostics.controller.start_utc_ticks=$self.StartTime.ToUniversalTime().Ticks}finally{$self.Dispose()}
  $path=[Environment]::ProcessPath
  if($null -ne $path){$diagnostics.controller.process_path=$path.Substring(0,[math]::Min(512,$path.Length));$diagnostics.controller.path_truncated=($path.Length -gt 512)}
  $diagnostics.controller.metadata_complete=($null -ne $diagnostics.controller.start_utc_ticks -and $null -ne $path -and -not $diagnostics.controller.path_truncated)
  if(-not $diagnostics.controller.metadata_complete){Diagnostic-Failed}
 }catch{Diagnostic-Failed}
}
function Diagnostic-Row($row){
 $name=$null;$path=$null;$creation=$null
 if($null -ne $row.Name){$name=[string]$row.Name}
 if($null -ne $row.ExecutablePath){$path=[string]$row.ExecutablePath}
 if($row.CreationDate -is [datetime]){$creation=$row.CreationDate.ToUniversalTime().ToString('o')}
 return [ordered]@{pid=[long]$row.ProcessId;parent_pid=[long]$row.ParentProcessId;creation_utc=$creation;name=if($null -eq $name){$null}else{$name.Substring(0,[math]::Min(128,$name.Length))};executable_path=if($null -eq $path){$null}else{$path.Substring(0,[math]::Min(256,$path.Length))};creation_unknown=($null -eq $creation);name_unknown=($null -eq $name);path_unknown=($null -eq $path);name_truncated=($null -ne $name -and $name.Length -gt 128);path_truncated=($null -ne $path -and $path.Length -gt 256)}
}
function Diagnostic-ObserveRow($row,[string]$site,[long]$parent,[string]$filter,[string]$refusal=''){
 try{
  $value=Diagnostic-Row $row
  if($refusal -cne '' -and $null -eq $diagnostics.first_refusal){$diagnostics.first_refusal=[ordered]@{site=$site;table_call_ordinal=[long]$diagnostics.table_call_ordinal;query='Win32_Process';filter=$filter;qpc=[Diagnostics.Stopwatch]::GetTimestamp();utc=[DateTimeOffset]::UtcNow.ToString('o');reason=$refusal;row=$value}}
  $already=$false
  foreach($retained in $diagnostics.rows){if($retained.pid -eq $value.pid -and $retained.parent_pid -eq $value.parent_pid -and $retained.creation_utc -ceq $value.creation_utc){$already=$true;break}}
  if(-not $already){
   $bytes=[Text.UTF8Encoding]::new($false).GetByteCount(($value|ConvertTo-Json -Depth 8 -Compress))
   if($diagnostics.rows.Count -ge 32 -or $diagnosticRowBytes+$bytes -gt 16384){$diagnostics.overflow=$true;$diagnostics.complete=$false}
   else{$diagnostics.rows.Add($value);$script:diagnosticRowBytes+=$bytes}
  }
 }catch{Diagnostic-Failed}
}
function Diagnostic-Payload{
 try{
  $diagnostics.helper.pid=if($childId -gt 0){[long]$childId}else{$null}
  $diagnostics.helper.start_utc_ticks=if($childStartTicks -gt 0){[long]$childStartTicks}else{$null}
  $raw=[Text.UTF8Encoding]::new($false).GetBytes(($diagnostics|ConvertTo-Json -Depth 16 -Compress))
  if($raw.Length -gt 65536){$diagnostics.overflow=$true;$diagnostics.complete=$false;$diagnostics.rows.Clear()}
 }catch{Diagnostic-Failed}
 return ,$diagnostics
}
function Diagnostic-ValidateException($value){
 Closed $value @('type','hresult','message','type_truncated','message_truncated')
 Need ($value.type -is [string] -and $value.type.Length -le 128 -and $value.message -is [string] -and $value.message.Length -le 256 -and $value.hresult -is [long] -and $value.type_truncated -is [bool] -and $value.message_truncated -is [bool]) 'Malformed bounded diagnostic exception'
}
function Diagnostic-ValidateRow($value){
 Closed $value @('pid','parent_pid','creation_utc','name','executable_path','creation_unknown','name_unknown','path_unknown','name_truncated','path_truncated')
 Need ($value.pid -is [long] -and $value.pid -gt 0 -and $value.parent_pid -is [long] -and $value.parent_pid -ge 0) 'Malformed diagnostic process identifiers'
 foreach($field in @('creation_unknown','name_unknown','path_unknown','name_truncated','path_truncated')){Need ($value[$field] -is [bool]) 'Malformed diagnostic row flags'}
 foreach($pair in @(@('creation_utc',64,'creation_unknown'),@('name',128,'name_unknown'),@('executable_path',256,'path_unknown'))){
  Need (($null -eq $value[$pair[0]] -and $value[$pair[2]]) -or ($value[$pair[0]] -is [string] -and $value[$pair[0]].Length -le $pair[1] -and -not $value[$pair[2]])) 'Diagnostic unknown/string mismatch'
 }
 if($null -ne $value.creation_utc){[void](Utc $value.creation_utc)}
}
function Diagnostic-Validate($value,[bool]$attempted,[string]$outcome,[bool]$failureExpected){
 Closed $value @('schema','complete','overflow','controller','helper','primary_failure','first_refusal','events','table_summaries','rows','custody_refused','final_table_verified','table_call_ordinal')
 Need ($value.table_call_ordinal -is [long] -and $value.table_call_ordinal -ge 0 -and $value.table_call_ordinal -le 128 -and $value.schema -ceq 'cho51_p3_bootstrap_diagnostics_v5') 'Exact diagnostic schema required'
 foreach($field in @('complete','overflow','custody_refused','final_table_verified')){Need ($value[$field] -is [bool]) 'Diagnostic state must be Boolean'}
 Need ([Text.UTF8Encoding]::new($false).GetByteCount(($value|ConvertTo-Json -Depth 16 -Compress)) -le 65536) 'Diagnostic payload byte cap exceeded'
 Closed $value.controller @('pid','start_utc_ticks','process_path','path_truncated','metadata_complete')
 Need ($value.controller.pid -is [long] -and $value.controller.pid -gt 0 -and $value.controller.path_truncated -is [bool] -and $value.controller.metadata_complete -is [bool]) 'Malformed diagnostic controller'
 Need (($null -eq $value.controller.start_utc_ticks -or ($value.controller.start_utc_ticks -is [long] -and $value.controller.start_utc_ticks -gt 0)) -and ($null -eq $value.controller.process_path -or ($value.controller.process_path -is [string] -and $value.controller.process_path.Length -le 512))) 'Malformed nullable controller metadata'
 Closed $value.helper @('pid','start_utc_ticks')
 foreach($field in @('pid','start_utc_ticks')){Need ($null -eq $value.helper[$field] -or ($value.helper[$field] -is [long] -and $value.helper[$field] -gt 0)) 'Malformed nullable helper generation'}
 Need ($value.events -is [array] -and $value.events.Count -le 32 -and $value.rows -is [array] -and $value.rows.Count -le 32 -and $value.table_summaries -is [Collections.IDictionary] -and $value.table_summaries.Count -le 8) 'Diagnostic collection cap/type differs'
 $criticalCleanupFailed=$false
 $stageWitnesses=[Collections.Generic.Dictionary[string,object]]::new([StringComparer]::Ordinal)
 $normalStages=@('identity','wait_reap','eof','final_table','stream_preservation')
 $cleanupStages=@('cleanup_identity','cleanup_has_exited_kill','cleanup_wait_reap','cleanup_eof','cleanup_final_table','cleanup_stream_preservation')
 $normalCount=0;$cleanupCount=0;$normalBytes=0;$cleanupBytes=0
 $previousEventQpc=[long]0;$previousEventUtc=$null;$cleanupSeen=$false;$coherentTrace=$true
 foreach($event in $value.events){
  Closed $event @('stage','outcome','qpc','utc','exception')
  Need ($event.stage -cin @('identity','has_exited_kill','wait_reap','eof','final_table','stream_preservation','cleanup_identity','cleanup_has_exited_kill','cleanup_wait_reap','cleanup_eof','cleanup_final_table','cleanup_stream_preservation') -and $event.outcome -cin @('ok','failed') -and $event.qpc -is [long] -and $event.qpc -gt 0) 'Malformed diagnostic stage'
  $eventUtc=Utc $event.utc
  Need ($event.qpc -ge $previousEventQpc -and ($null -eq $previousEventUtc -or $eventUtc -ge $previousEventUtc)) 'Diagnostic event clocks regressed'
  $previousEventQpc=$event.qpc;$previousEventUtc=$eventUtc
  Need (-not $stageWitnesses.ContainsKey($event.stage)) 'Duplicate diagnostic stage'
  $stageWitnesses.Add($event.stage,$event)
  $eventBytes=[Text.UTF8Encoding]::new($false).GetByteCount(($event|ConvertTo-Json -Depth 8 -Compress))
  if($event.stage.StartsWith('cleanup_',[StringComparison]::Ordinal)){$cleanupSeen=$true;$cleanupCount++;$cleanupBytes+=$eventBytes}
  else{
   if($cleanupSeen -or $normalCount -ge $normalStages.Count -or $event.stage -cne $normalStages[$normalCount] -or $event.outcome -cne 'ok'){$coherentTrace=$false}
   $normalCount++;$normalBytes+=$eventBytes
  }
  if($null -ne $event.exception){Diagnostic-ValidateException $event.exception}
  Need (($event.outcome -ceq 'ok' -and $null -eq $event.exception) -or ($event.outcome -ceq 'failed' -and $null -ne $event.exception)) 'Diagnostic event exception/outcome mismatch'
  if($event.outcome -ceq 'failed' -and $event.stage.StartsWith('cleanup_',[StringComparison]::Ordinal)){$criticalCleanupFailed=$true}
 }
 Need ($normalCount -le 16 -and $cleanupCount -le 16 -and $normalBytes -le 8192 -and $cleanupBytes -le 8192) 'Diagnostic event reservation exceeded'
 $rowKeys=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal);$rowBytes=0
 foreach($row in $value.rows){
  Diagnostic-ValidateRow $row
  $rowKey=[string]$row.pid+'/'+[string]$row.parent_pid+'/'+$(if($null -eq $row.creation_utc){'<unknown>'}else{$row.creation_utc})
  Need ($rowKeys.Add($rowKey)) 'Duplicate retained diagnostic generation'
  $rowBytes+=[Text.UTF8Encoding]::new($false).GetByteCount(($row|ConvertTo-Json -Depth 8 -Compress))
 }
 Need ($rowBytes -le 16384) 'Diagnostic retained row byte reservation exceeded'
 foreach($key in $value.table_summaries.Keys){
  $table=$value.table_summaries[$key]
  Closed $table @('site','parent_kind','parent_pid','query','filter','calls','first_qpc','first_utc','last_qpc','last_utc','last_observed_rows','total_observed_rows','completed')
  Need ($table.site -cin @('initial','periodic','final','cleanup_final') -and $table.parent_kind -cin @('controller','helper') -and $key -ceq ($table.site+'/'+$table.parent_kind) -and $table.query -ceq 'Win32_Process' -and $table.parent_pid -is [long] -and $table.parent_pid -gt 0 -and $table.filter -ceq "ParentProcessId = $($table.parent_pid)" -and $table.completed -is [bool]) 'Malformed diagnostic table query'
  foreach($field in @('calls','first_qpc','last_qpc','last_observed_rows','total_observed_rows')){Need ($table[$field] -is [long] -and $table[$field] -ge 0) 'Malformed table count/clock'}
  Need ($table.calls -gt 0 -and $table.calls -le 128 -and $table.last_qpc -ge $table.first_qpc -and $table.last_observed_rows -le 65 -and $table.total_observed_rows -ge $table.last_observed_rows -and $table.parent_pid -eq $(if($table.parent_kind -ceq 'controller'){$value.controller.pid}else{$value.helper.pid})) 'Inconsistent diagnostic table counts'
  [void](Utc $table.first_utc);[void](Utc $table.last_utc)
 }
 if($null -ne $value.first_refusal){
  Closed $value.first_refusal @('site','table_call_ordinal','query','filter','qpc','utc','reason','row')
  Need ($value.first_refusal.table_call_ordinal -is [long] -and $value.first_refusal.table_call_ordinal -gt 0 -and $value.first_refusal.table_call_ordinal -le $value.table_call_ordinal -and $value.first_refusal.site -cin @('initial','periodic','final','cleanup_final') -and $value.first_refusal.query -ceq 'Win32_Process' -and $value.first_refusal.filter -is [string] -and $value.first_refusal.filter.Length -le 64 -and $value.first_refusal.reason -is [string] -and $value.first_refusal.reason.Length -le 128 -and $value.first_refusal.qpc -is [long] -and $value.custody_refused) 'Malformed first refusal'
  [void](Utc $value.first_refusal.utc);Diagnostic-ValidateRow $value.first_refusal.row
 }
 if($failureExpected){Need ($null -ne $value.primary_failure) 'Original diagnostic failure required'}
 else{Need ($null -eq $value.primary_failure -and $null -eq $value.first_refusal -and -not $value.custody_refused) 'Successful diagnostics cannot contain refusal'}
 if($null -ne $value.primary_failure){
  Closed $value.primary_failure @('stage','exception')
  Need ($value.primary_failure.stage -is [string] -and $value.primary_failure.stage.Length -le 64) 'Malformed primary failure stage'
  Diagnostic-ValidateException $value.primary_failure.exception
 }
 $usable=$value.complete -and -not $value.overflow -and $value.controller.metadata_complete -and -not $value.controller.path_truncated -and $null -ne $value.controller.start_utc_ticks -and $value.controller.process_path -ceq (Join-Path $runtime 'pwsh.exe') -and -not $value.custody_refused -and -not $criticalCleanupFailed -and $coherentTrace
 if($attempted){
  $requiredStages=if($failureExpected){$cleanupStages}else{$normalStages}
  $previousRequiredQpc=[long]0
  foreach($stage in $requiredStages){
   if(-not $stageWitnesses.ContainsKey($stage) -or $stageWitnesses[$stage].outcome -cne 'ok'){$usable=$false;continue}
   if($stageWitnesses[$stage].qpc -lt $previousRequiredQpc){$usable=$false}
   $previousRequiredQpc=$stageWitnesses[$stage].qpc
  }
  if($failureExpected){
   if(-not $stageWitnesses.ContainsKey('identity') -or $stageWitnesses['identity'].outcome -cne 'ok' -or -not $stageWitnesses.ContainsKey('cleanup_identity') -or $stageWitnesses['identity'].qpc -gt $stageWitnesses['cleanup_identity'].qpc){$usable=$false}
  }else{$usable=$usable -and $value.events.Count -eq $normalStages.Count}
 }else{$usable=$usable -and $outcome -ceq 'not_attempted' -and $null -eq $value.helper.pid -and $null -eq $value.helper.start_utc_ticks -and $value.events.Count -eq 0 -and $value.rows.Count -eq 0 -and $value.table_summaries.Count -eq 0 -and -not $value.final_table_verified}
 if($attempted -and $value.final_table_verified){
  $finalSite=if($value.table_summaries.Contains('cleanup_final/controller')){'cleanup_final'}else{'final'}
  foreach($kind in @('controller','helper')){Need ($value.table_summaries.Contains($finalSite+'/'+$kind) -and $value.table_summaries[$finalSite+'/'+$kind].completed) 'Final diagnostic table evidence missing'}
 }
 if($attempted){$usable=$usable -and $outcome -ceq 'started' -and $null -ne $value.helper.pid -and $null -ne $value.helper.start_utc_ticks -and $value.final_table_verified}
 return [bool]$usable
}
function Diagnostic-ValidateFailureIdentity($value){
 Need ($value.mode -ceq 'Invoke') 'Only original Invoke failure diagnostics may complete or release'
 Need ($null -eq $value.child_pid -or ($value.child_pid -is [long] -and $value.child_pid -gt 0)) 'Malformed nullable failure child PID'
 Need ($value.child_pid -eq $value.diagnostics.helper.pid) 'Failure helper PID differs from original diagnostic identity'
 if($value.start_outcome -ceq 'started'){
  Need ($value.start_attempted -and $value.child_started -and $value.child_pid -is [long] -and $null -ne $value.diagnostics.helper.start_utc_ticks) 'Started failure requires original known helper generation'
 }elseif(-not $value.start_attempted){
  Need (-not $value.child_started -and $null -eq $value.child_pid -and $null -eq $value.diagnostics.helper.pid -and $null -eq $value.diagnostics.helper.start_utc_ticks) 'Unattempted failure cannot invent helper identity'
 }
}


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
function Clock([double]$limit=85,[bool]$checkPauses=(-not $script:cleanupOnly)){
 $now=[DateTimeOffset]::UtcNow
 Need ((Seconds) -lt $limit -and $now -ge $commonUtc -and $now -lt $commonUtc.AddSeconds($limit)) 'Common caller deadline reached'
 if($null -ne $windowStart){Need ($now -ge $windowStart -and $now -lt $windowEnd.AddSeconds(-60)) 'Strict peer publication reserve reached'}
 if($null -ne $sourceEnd){Need ($now -lt $sourceEnd.AddSeconds(-60)) 'Strict Source publication reserve reached'}
 if($checkPauses){foreach($pausePath in $pausePaths){Need (-not (Present $pausePath)) 'Peer pause requested'}}
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
 Need ($name -cin @('bootstrap-stdout_005.txt','bootstrap-stderr_005.txt') -and $raw.Length -le 1048576) 'Bounded owned stream required'
 Clock 85
 $stream=[IO.File]::Open((Join-Path $run $name),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
 try{$stream.Write($raw,0,$raw.Length);$stream.Flush($true)}finally{$stream.Dispose()}
 Clock 85
 $read=[IO.File]::OpenRead((Join-Path $run $name))
 try{Need ($read.Length -eq $raw.Length) 'Stream readback size differs';$copy=[byte[]]::new($raw.Length);$read.ReadExactly($copy);Need ((Hash $copy) -ceq (Hash $raw)) 'Stream readback SHA differs'}finally{$read.Dispose()}
 Clock 85
 return [ordered]@{path=(Join-Path $run $name);bytes=$raw.Length;sha256=(Hash $raw)}
}
function Read-PreservedStream([string]$name,[byte[]]$expectedRaw){
 Need ($name -cin @('bootstrap-stdout_005.txt','bootstrap-stderr_005.txt') -and $expectedRaw.Length -le 1048576) 'Bounded owned preserved stream required'
 Clock 85
 $path=Join-Path $run $name
 $stream=[IO.File]::Open($path,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
 try{
  Need ($stream.Length -eq $expectedRaw.Length) 'Preserved stream size differs from retained bytes'
  $raw=[byte[]]::new($expectedRaw.Length);$stream.ReadExactly($raw)
  Clock 85
  Need ((Hash $raw) -ceq (Hash $expectedRaw)) 'Preserved stream digest differs from retained bytes'
 }finally{$stream.Dispose()}
 Clock 85
 return [ordered]@{path=$path;bytes=$expectedRaw.Length;sha256=(Hash $expectedRaw)}
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
function Original-Handle{
 Need ($null -ne $process -and $startAttempted) 'Only the exact Start-attempted Process may be inspected'
 $flags=[Reflection.BindingFlags]'Instance,NonPublic'
 $haveField=[Diagnostics.Process].GetField('_haveProcessHandle',$flags)
 $handleField=[Diagnostics.Process].GetField('_processHandle',$flags)
 Need ($null -ne $haveField -and $null -ne $handleField) 'Pinned retained-handle implementation fields required'
 $have=$haveField.GetValue($process)
 Need ($have -is [bool] -and $have) 'Original Start-owned process handle is not established'
 $original=$handleField.GetValue($process)
 Need ($original -is [Microsoft.Win32.SafeHandles.SafeProcessHandle] -and -not $original.IsClosed -and -not $original.IsInvalid) 'Valid original Start-owned handle required'
 if($null -eq $safeHandle){$script:safeHandle=$original;$script:safeHandle.DangerousAddRef([ref]$script:handleRef);$script:handleValue=$script:safeHandle.DangerousGetHandle()}
 Need ([object]::ReferenceEquals($original,$safeHandle) -and $original.DangerousGetHandle() -eq $handleValue) 'Original retained handle changed'
}
function Identity{
 Original-Handle
 Need ($childStarted -and $childId -gt 0 -and $childStartTicks -gt 0 -and $process.Id -eq $childId -and $process.StartTime.ToUniversalTime().Ticks -eq $childStartTicks) 'Retained process generation differs'
}
function Cleanup-Identity{
 Original-Handle
 if($childId -gt 0){Need ($process.Id -eq $childId) 'Owned process PID changed'}
 if($childStartTicks -gt 0){Need ($process.StartTime.ToUniversalTime().Ticks -eq $childStartTicks) 'Owned process generation changed'}
}
function Child-Table([ValidateSet('initial','periodic','final','cleanup_final')][string]$site){
 Clock 80 $false
 try{
  $script:diagnostics.table_call_ordinal++
  $count=0;$seenHelper=$false
  foreach($parentId in @($PID,$childId)){
   $kind=if($parentId -eq $PID){'controller'}else{'helper'}
   $filter="ParentProcessId = $parentId";$key=$site+'/'+$kind
   try{
    $nowQpc=[Diagnostics.Stopwatch]::GetTimestamp();$nowUtc=[DateTimeOffset]::UtcNow.ToString('o')
    if(-not $diagnostics.table_summaries.Contains($key)){$diagnostics.table_summaries[$key]=[ordered]@{site=$site;parent_kind=$kind;parent_pid=[long]$parentId;query='Win32_Process';filter=$filter;calls=0;first_qpc=$nowQpc;first_utc=$nowUtc;last_qpc=$nowQpc;last_utc=$nowUtc;last_observed_rows=0;total_observed_rows=0;completed=$false}}
    $summary=$diagnostics.table_summaries[$key];$summary.calls++;$summary.last_qpc=$nowQpc;$summary.last_utc=$nowUtc;$summary.last_observed_rows=0;$summary.completed=$false
   }catch{Diagnostic-Failed;$summary=$null}
   foreach($row in Get-CimInstance -ClassName Win32_Process -Filter $filter -OperationTimeoutSec 3){
    $count++
    try{if($null -ne $summary){$summary.last_observed_rows++;$summary.total_observed_rows++}}catch{Diagnostic-Failed}
    $reason=''
    if($count -gt 64){$reason='Process table row cap exceeded'}
    elseif(-not ($parentId -eq $PID -and [long]$row.ProcessId -eq $childId -and [long]$row.ParentProcessId -eq $PID)){$reason='Unexpected descendant; no authority to kill it'}
    elseif(-not ($row.CreationDate -is [datetime] -and [math]::Abs($row.CreationDate.ToUniversalTime().Ticks-$childStartTicks) -le 10000)){$reason='CIM helper generation differs'}
    Diagnostic-ObserveRow $row $site $parentId $filter $reason
    Need ($reason -ceq '') $reason
    $seenHelper=$true
   }
   try{if($null -ne $summary){$summary.completed=$true;$summary.last_qpc=[Diagnostics.Stopwatch]::GetTimestamp();$summary.last_utc=[DateTimeOffset]::UtcNow.ToString('o')}}catch{Diagnostic-Failed}
  }
  Need ($process.HasExited -or $seenHelper) 'Live retained helper missing from process table'
  Clock 80 $false
  if($site -cin @('final','cleanup_final') -and -not $diagnostics.custody_refused){$diagnostics.final_table_verified=$true}
 }catch{$script:custodyClosed=$false;$script:diagnostics.custody_refused=$true;$script:diagnostics.final_table_verified=$false;throw}
}
Diagnostic-Controller
try{
 Need ($PSScriptRoot -ceq $run -and $PSCommandPath -ceq (Join-Path $run 'bootstrap-supervise_005.ps1')) 'Exact supervisor Source path required'
 if($Mode -ceq 'Begin'){
  Need ($ExternalFrequency -eq $frequency -and $ExternalEntryQpc -gt 0 -and $ExternalEntryQpc -le $modeEntryQpc) 'Fresh external pre-dispatch QPC required'
  $commonUtc=Utc $ExternalEntryUtc;$commonQpc=$ExternalEntryQpc
  Need (($modeEntryQpc-$commonQpc)/[double]$frequency -lt 5 -and $modeEntryUtc -ge $commonUtc -and $modeEntryUtc -lt $commonUtc.AddSeconds(5)) 'External pre-dispatch observation is stale'
 }else{
  Need ($ExternalEntryQpc -eq 0 -and $ExternalEntryUtc -ceq '' -and $ExternalFrequency -eq 0) 'Only Begin accepts external entry'
  $dispatchRef=Existing 'bootstrap-dispatch_005.json';$dispatch=$dispatchRef.value
  Closed $dispatch @('schema','scope','observed_utc','request_sha256','root_admission_sha256','scientific_admission','external_entry_qpc','external_entry_utc','qpc_frequency','begin_entry_qpc','begin_entry_utc','maximum_seconds','caller_return_observed','automatic_retry_permitted')
  Receipt $dispatch 'cho51_p3_bootstrap_dispatch_v5'
  Need ($dispatch.external_entry_qpc -is [long] -and $dispatch.qpc_frequency -is [long] -and $dispatch.qpc_frequency -eq $frequency -and $dispatch.maximum_seconds -is [long] -and $dispatch.maximum_seconds -eq 90 -and $dispatch.caller_return_observed -is [bool] -and -not $dispatch.caller_return_observed -and $dispatch.automatic_retry_permitted -is [bool] -and -not $dispatch.automatic_retry_permitted) 'Exact common dispatch clock required'
  $commonQpc=$dispatch.external_entry_qpc;$commonUtc=Utc $dispatch.external_entry_utc
 }
 Clock
 $request=Metadata 'bootstrap-request_005.json' $RequestSha256 $true
 $scopeSha=$request.source_scope_sha256;$adoptionSha=$request.source_adoption_sha256
 foreach($path in @($request.source_scope_path,$request.source_adoption_path)){Need ($path -is [string] -and $path.Length -le 512 -and $path -cmatch '^D:\\Aenv\\pro2\\WORK\\resume-\d{8}-\d{3}\\(?:[A-Za-z0-9_-]+\\){1,4}[A-Za-z0-9_.-]+\.json$' -and [IO.Path]::GetFullPath($path) -ceq $path) 'Direct normalized genuine peer coordination path required'}
 $admission=Metadata 'bootstrap-admission_005.json' $RootAdmissionSha256 $true
 Need ($request.schema -ceq 'cho51_p3_bootstrap_observation_request_v2' -and $admission.schema -ceq 'cho51_p3_bootstrap_observation_admission_v2' -and $admission.accepted -is [bool] -and $admission.accepted) 'Exact fresh Root admission required'
 Need ($admission.peer_decision_path -is [string] -and $admission.peer_decision_path.Length -le 512 -and $admission.peer_decision_path -cmatch '^D:\\Aenv\\pro2\\WORK\\resume-\d{8}-\d{3}\\(?:[A-Za-z0-9_-]+\\){1,4}[A-Za-z0-9_.-]+\.json$' -and [IO.Path]::GetFullPath($admission.peer_decision_path) -ceq $admission.peer_decision_path) 'Direct normalized actual Pro2 peer decision path required'
 $peer=Parse (Bytes $admission.peer_decision_path $admission.peer_decision_sha256 1048576 $true)
 Need ($peer.schema -ceq 'pro2_pro3_bootstrap_observation_decision_v2' -and $peer.released -is [bool] -and $peer.released) 'Genuine explicit peer bootstrap grant required'
 foreach($record in @($request,$admission,$peer)){
  Need ($record.scope -ceq $scope -and $record.source_scope_path -ceq $request.source_scope_path -and $record.source_adoption_path -ceq $request.source_adoption_path) 'Exact bootstrap005 scope and coordination paths required'
  foreach($field in @('predecessor_disposition_sha256','source_sha256','supervisor_sha256','protocol_sha256','source_review_sha256','owner_resource_amendment_sha256','source_scope_sha256','source_adoption_sha256','runtime_executable_sha256','process_dll_sha256')){Need ($record[$field] -is [string] -and $record[$field] -ceq $request[$field] -and $record[$field] -cmatch '^[0-9a-f]{64}$') 'Exact admitted Source/runtime join required'}
  foreach($pair in @(@('maximum_seconds',90),@('maximum_files',2500),@('maximum_code_bytes',1073741824),@('maximum_enumerated_entries',10000),@('maximum_directory_depth',16),@('maximum_manifest_bytes',1048576),@('startup_ram_gib',4),@('active_ram_gib',4),@('disk_gib',20),@('outer_child_processes',1),@('helper_child_processes',0),@('python_invocations',0),@('jobs',0),@('publication_reserve_seconds',60))){Need ($record[$pair[0]] -is [long] -and $record[$pair[0]] -eq $pair[1]) 'Exact integer admission cap required'}
  foreach($field in @('automatic_retry_permitted','native_helper_compilation_admitted','scientific_admission')){Need ($record[$field] -is [bool] -and -not $record[$field]) 'Admission cannot widen scope'}
  Need ($record.bounded_cleanup_after_pause_admitted -is [bool] -and $record.bounded_cleanup_after_pause_admitted) 'Explicit bounded cleanup-only publication authority required'
  $zeroFields=@('source_updates','restore_count','support_updates','gradient_updates','target_inference_calls','query_count','model_constructions','measured_cells')
  Closed $record.expected_numerical_budget $zeroFields
  foreach($field in $zeroFields){Need ($record.expected_numerical_budget[$field] -is [long] -and $record.expected_numerical_budget[$field] -eq 0) 'Exact zero numerical budget required'}
  Need ($record.window_start_utc -ceq $request.window_start_utc -and $record.window_end_utc -ceq $request.window_end_utc) 'Exact peer/Root/request window required'
 }
 foreach($record in @($peer,$admission)){Need ($record.request_sha256 -ceq $RequestSha256 -and (Utc $record.observed_utc) -le $commonUtc -and (Utc $record.observed_utc) -ge (Utc $request.created_utc)) 'Actual decisions must follow this request and predate external dispatch'}
 $windowStart=Utc $request.window_start_utc;$windowEnd=Utc $request.window_end_utc
 $sourceScope=Parse (Bytes $request.source_scope_path $scopeSha)
 $sourceAdoption=Parse (Bytes $request.source_adoption_path $adoptionSha)
 $sourceEnd=Utc $sourceScope.interval_end
 Need ($request.source_scope_sha256 -ceq $scopeSha -and $request.source_adoption_sha256 -ceq $adoptionSha -and $sourceAdoption.Source_only_coexistence_adopted -is [bool] -and $sourceAdoption.Source_only_coexistence_adopted -and $sourceAdoption.Source_only_scope.sha256 -ceq $scopeSha) 'Actual current Source authority required'
 Need ($sourceAdoption.interval_start -ceq $sourceScope.interval_start -and $sourceAdoption.interval_end -ceq $sourceScope.interval_end -and (Utc $sourceAdoption.created_utc) -le $commonUtc) 'Actual Source adoption must precede entry with exact interval joins'
 foreach($pair in @(@('Pro2_max_including_Root',3),@('Pro3_max_including_Root_and_reviewer',2),@('shared_max_including_both_roots_reviewers_children_and_overlap',5))){Need ($sourceScope[$pair[0]] -is [long] -and $sourceScope[$pair[0]] -eq $pair[1]) 'current Source concurrency caps differ'}
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
 $review=Metadata 'bootstrap-source-review_005.json' $request.source_review_sha256
 Need ($review.schema -ceq 'cho51_p3_bootstrap_source_review_v5' -and $review.source_only -is [bool] -and $review.source_only -and @($review.remaining_actionable_findings).Count -eq 0 -and $review.source_sha256 -ceq $request.source_sha256 -and $review.files.Count -eq 3) 'Exact clean consolidated three-Source review required'
 foreach($pair in @(@('bootstrap-observation_005.ps1','source_sha256'),@('bootstrap-supervise_005.ps1','supervisor_sha256'),@('bootstrap-protocol_005.md','protocol_sha256'))){
  $path=Join-Path $run $pair[0]
  Need ($review.files[$path] -ceq $request[$pair[1]]) 'Composite Source map differs'
  [void](Bytes $path $request[$pair[1]] 1048576 $true)
 }
 [void](Bytes (Join-Path $runtime 'pwsh.exe') $request.runtime_executable_sha256 1048576 $true)
 Need ($request.process_dll_sha256 -ceq '2b4871e02b366113c6ccf3b1436fadde5e69fc0a3e3ac421e2fa0f7af8c2bc3b') 'Source-reviewed retained-handle Kill implementation pin differs'
 Need ([Diagnostics.Process].Assembly.Location -ceq (Join-Path $runtime 'System.Diagnostics.Process.dll')) 'Actual retained-handle Process implementation differs'
 [void](Bytes (Join-Path $runtime 'System.Diagnostics.Process.dll') $request.process_dll_sha256 1048576 $true)

 Need ($request.predecessor_disposition_sha256 -ceq '1faf198894e0f210e5bb8692a8c0c4b35f10963a1e2c8c928d545eb808c335ec') 'Exact preserved predecessor disposition required'
 $predecessor=Metadata 'bootstrap-disposition_004.json' $request.predecessor_disposition_sha256 $true
 Need ($predecessor.schema -ceq 'cho51_p3_bootstrap_failed_attempt_disposition_v1' -and $predecessor.scope -ceq 'cho51_p3_contracts_20261027_v1_bootstrap_observation_004' -and $predecessor.disposition -ceq 'FAILED_UNRELEASED_CONSUMED' -and $predecessor.custody_closed -is [bool] -and -not $predecessor.custody_closed -and $predecessor.operation_released -is [bool] -and -not $predecessor.operation_released) 'Historical predecessor failure must remain unchanged'
 if($Mode -cin @('Begin','Invoke')){throw 'Predecessor custody unresolved: separate independently reviewed current custody-resolution source and actual disposition required before a new operational successor'}

 $authenticated=$true
 if($cleanupOnly){try{[void](Floor 85)}catch{$closureGuardPassed=$false;$closureGuardRefusal=$_.Exception.Message}}
 else{[void](Floor)}
 if($Mode -ceq 'Begin'){
  foreach($name in $outputNames){Need (-not (Present (Join-Path $run $name))) 'Bootstrap005 namespace already used'}
  $record=Common 'cho51_p3_bootstrap_dispatch_v5'
  $record.external_entry_qpc=$commonQpc;$record.external_entry_utc=$commonUtc.ToString('o');$record.qpc_frequency=$frequency
  $record.begin_entry_qpc=$modeEntryQpc;$record.begin_entry_utc=$modeEntryUtc.ToString('o');$record.maximum_seconds=90
  $record.caller_return_observed=$false;$record.automatic_retry_permitted=$false
  [void](Write-New 'bootstrap-dispatch_005.json' $record 65)
 }elseif($Mode -ceq 'Invoke'){
  Need ($null -ne $BeginToolExitCode -and $BeginToolExitCode -eq 0) 'Actual successful Begin tool exit required before child launch'
  foreach($name in $outputNames|Where-Object{$_ -cne 'bootstrap-dispatch_005.json'}){Need (-not (Present (Join-Path $run $name))) 'Once-only invocation output already used'}
  $attempt=Common 'cho51_p3_bootstrap_attempt_v5';$attempt.dispatch_sha256=$dispatchRef.sha256;$attempt.helper_invocations=0;$attempt.automatic_retry_permitted=$false
  [void](Write-New 'bootstrap-attempt_005.json' $attempt 65)
  $samples=[Collections.Generic.List[object]]::new();$samples.Add((Floor));[Threading.Thread]::Sleep(200);$samples.Add((Floor))
  Need ((Seconds) -lt 15) 'Insufficient helper work and cleanup reserve'
  $startInfo=[Diagnostics.ProcessStartInfo]::new();$startInfo.FileName=Join-Path $runtime 'pwsh.exe';$startInfo.WorkingDirectory='D:\Aenv\pro3'
  $startInfo.UseShellExecute=$false;$startInfo.CreateNoWindow=$true;$startInfo.RedirectStandardOutput=$true;$startInfo.RedirectStandardError=$true
  foreach($argument in @('-NoProfile','-NonInteractive','-File',(Join-Path $run 'bootstrap-observation_005.ps1'),'-RequestSha256',$RequestSha256,'-RootAdmissionSha256',$RootAdmissionSha256)){[void]$startInfo.ArgumentList.Add($argument)}
  Clock 65
  $process=[Diagnostics.Process]::new();$process.StartInfo=$startInfo
  $startAttempted=$true;$startOutcome='unknown';$custodyClosed=$false
  $operationStage='start_identity'
  Need ($process.Start()) 'Owned helper launch failed or uncertain'
  $childStarted=$true;Original-Handle
  $childId=$process.Id;$childStartTicks=$process.StartTime.ToUniversalTime().Ticks
  $operationStage='identity';Identity;Diagnostic-Event 'identity' 'ok'
  $startOutcome='started';$custodyClosed=$true
  $stdout=Drain-New $process.StandardOutput.BaseStream;$stderr=Drain-New $process.StandardError.BaseStream
  $operationStage='initial_table';Child-Table 'initial'
  $nextFloor=Seconds;$nextTable=Seconds
  while(-not $process.HasExited){
   Clock 65
   $operationStage='identity';Identity;Drain-Poll $stdout;Drain-Poll $stderr
   if((Seconds) -ge $nextFloor){[void](Floor);$nextFloor=(Seconds)+1}
   if((Seconds) -ge $nextTable){$operationStage='periodic_table';Child-Table 'periodic';$nextTable=(Seconds)+1}
   [Threading.Thread]::Sleep(20)
  }
  $operationStage='wait_reap';$childReaped=$process.WaitForExit(0)
  Need ($childReaped -and $process.ExitCode -eq 0) 'Helper failed or unreaped'
  Diagnostic-Event 'wait_reap' 'ok'
  $operationStage='eof'
  while((-not $stdout.eof -or -not $stderr.eof) -and (Seconds) -lt 80){Clock 80;Drain-Poll $stdout;Drain-Poll $stderr;[Threading.Thread]::Sleep(10)}
  Need ($stdout.eof -and $stderr.eof) 'Both stream EOF receipts required'
  Diagnostic-Event 'eof' 'ok'
  $operationStage='final_table';Child-Table 'final';Diagnostic-Event 'final_table' 'ok'
  $operationStage='stream_preservation'
  $stdoutRef=Write-Stream 'bootstrap-stdout_005.txt' $stdout.data.ToArray();$stderrRef=Write-Stream 'bootstrap-stderr_005.txt' $stderr.data.ToArray()
  Diagnostic-Event 'stream_preservation' 'ok'
  $helperAttempt=Existing 'bootstrap-helper-attempt_005.json';$manifest=Existing 'preparation-bootstrap-pins_005.json'
  Need ($manifest.value.schema -ceq 'cho51_p3_powershell_bootstrap_observation_v5' -and $manifest.value.scope -ceq $scope -and $manifest.value.request_sha256 -ceq $RequestSha256 -and $manifest.value.root_admission_sha256 -ceq $RootAdmissionSha256) 'Helper observational output join differs'
  $record=Common 'cho51_p3_bootstrap_supervision_v5'
  $record.dispatch_sha256=$dispatchRef.sha256;$record.attempt_sha256=(Existing 'bootstrap-attempt_005.json').sha256
  $record.helper_attempt_sha256=$helperAttempt.sha256;$record.manifest_sha256=$manifest.sha256;$record.helper_pid=$childId;$record.helper_creation_utc_ticks=$childStartTicks
  $record.start_attempted=$startAttempted;$record.start_outcome=$startOutcome
  $record.helper_invocations=1;$record.helper_exit_code=$process.ExitCode;$record.helper_reaped=$childReaped;$record.custody_closed=$custodyClosed
  $record.stdout=$stdoutRef;$record.stderr=$stderrRef;$record.stdout_eof=$stdout.eof;$record.stderr_eof=$stderr.eof
  $record.startup_samples=@($samples);$record.minimum_available_ram_bytes=$minimumRam;$record.minimum_free_disk_bytes=$minimumDisk
  $record.elapsed_seconds=Seconds;$record.caller_return_observed=$false;$record.full_caller_accepted=$false;$record.observational_manifest_accepted=$false
  $record.diagnostics=Diagnostic-Payload
  Need ($diagnostics.complete -and -not $diagnostics.overflow -and -not $diagnostics.custody_refused -and $diagnostics.final_table_verified) 'Incomplete diagnostics cannot succeed'
  [void](Write-New 'bootstrap-supervision_005.json' $record 85)
 }elseif($Mode -ceq 'Complete'){
  Need ($InvokeToolCallId.Length -gt 0 -and $InvokeToolCallId.Length -le 256 -and $InvokeToolCallId -notmatch '[\r\n]') 'Actual completed Invoke tool identity required'
  Need ($null -ne $InvokeToolExitCode) 'Actual completed Invoke tool exit required'
  $supervisionSha=$null;$failureSha=$null;$operationSucceeded=$false;$operationCustody=$false
  $operationAttempted=$false;$operationOutcome='unknown'
  if((Present (Join-Path $run 'bootstrap-failure_005.json'))){
   $failureRef=Existing 'bootstrap-failure_005.json';$failureRecord=$failureRef.value
   Receipt $failureRecord 'cho51_p3_bootstrap_failure_v5'
   Closed $failureRecord @('schema','scope','observed_utc','request_sha256','root_admission_sha256','scientific_admission','mode','failure','start_attempted','start_outcome','child_started','child_pid','child_reaped','custody_closed','stdout_eof','stderr_eof','stdout','stderr','partial_outputs_preserved','automatic_retry_permitted','full_caller_accepted','diagnostics')
   foreach($field in @('child_started','child_reaped','custody_closed','stdout_eof','stderr_eof')){Need ($failureRecord[$field] -is [bool]) 'Exact failure custody booleans required'}
   Need ($failureRecord.start_attempted -is [bool] -and $failureRecord.start_outcome -cin @('not_attempted','unknown','started')) 'Explicit failure start state required'
   $operationAttempted=$failureRecord.start_attempted;$operationOutcome=$failureRecord.start_outcome
   $diagnosticUsable=Diagnostic-Validate $failureRecord.diagnostics $failureRecord.start_attempted $failureRecord.start_outcome $true
   Diagnostic-ValidateFailureIdentity $failureRecord
   $operationCustody=$diagnosticUsable -and $failureRecord.custody_closed -and $operationOutcome -cne 'unknown' -and ((-not $operationAttempted -and $operationOutcome -ceq 'not_attempted') -or ($operationAttempted -and $operationOutcome -ceq 'started' -and $failureRecord.child_started -and $failureRecord.child_reaped -and $failureRecord.stdout_eof -and $failureRecord.stderr_eof))
   $failureSha=$failureRef.sha256
  }else{
   $supervisionRef=Existing 'bootstrap-supervision_005.json';$supervision=$supervisionRef.value
   Receipt $supervision 'cho51_p3_bootstrap_supervision_v5'
   Closed $supervision @('schema','scope','observed_utc','request_sha256','root_admission_sha256','scientific_admission','dispatch_sha256','attempt_sha256','helper_attempt_sha256','manifest_sha256','helper_pid','helper_creation_utc_ticks','start_attempted','start_outcome','helper_invocations','helper_exit_code','helper_reaped','custody_closed','stdout','stderr','stdout_eof','stderr_eof','startup_samples','minimum_available_ram_bytes','minimum_free_disk_bytes','elapsed_seconds','caller_return_observed','full_caller_accepted','observational_manifest_accepted','diagnostics')
   foreach($field in @('helper_reaped','custody_closed','stdout_eof','stderr_eof')){Need ($supervision[$field] -is [bool] -and $supervision[$field]) 'Incomplete custody cannot complete successfully'}
   Need ($supervision.dispatch_sha256 -ceq $dispatchRef.sha256 -and $supervision.helper_invocations -is [long] -and $supervision.helper_invocations -eq 1 -and $supervision.helper_exit_code -is [long] -and $supervision.helper_exit_code -eq 0) 'Failed/partial operation cannot pass'
   Need ($supervision.start_attempted -is [bool] -and $supervision.start_attempted -and $supervision.start_outcome -ceq 'started') 'Successful retained start state required'
   Need (Diagnostic-Validate $supervision.diagnostics $true 'started' $false) 'Incomplete diagnostic evidence cannot pass'
   Need ($supervision.diagnostics.helper.pid -eq $supervision.helper_pid -and $supervision.diagnostics.helper.start_utc_ticks -eq $supervision.helper_creation_utc_ticks) 'Diagnostic helper generation join differs'
   $operationAttempted=$true;$operationOutcome='started'
   $supervisionSha=$supervisionRef.sha256;$operationSucceeded=$true;$operationCustody=$true
  }
  $record=Common 'cho51_p3_bootstrap_caller_completion_v5';$record.dispatch_sha256=$dispatchRef.sha256;$record.supervision_sha256=$supervisionSha;$record.failure_sha256=$failureSha
  $record.invoke_tool_call_id=$InvokeToolCallId;$record.post_invoke_return_upper_bound_qpc=$modeEntryQpc;$record.post_invoke_return_upper_bound_utc=$modeEntryUtc.ToString('o')
  $record.invoke_tool_exit_code=[int]$InvokeToolExitCode;$record.start_attempted=$operationAttempted;$record.start_outcome=$operationOutcome
  $record.qpc_frequency=$frequency;$record.external_entry_qpc=$commonQpc;$record.elapsed_upper_bound_seconds=($modeEntryQpc-$commonQpc)/[double]$frequency
  $record.observation_semantics='Root dispatched Complete only after actual Invoke tool completion; Complete entry is an upper bound, not the exact return instant'
  $record.invoke_tool_return_observed_by_root=$true;$record.operation_succeeded=($operationSucceeded -and $closureGuardPassed -and $InvokeToolExitCode -eq 0);$record.custody_closed=$operationCustody;$record.closure_guard_passed=$closureGuardPassed;$record.closure_guard_refusal=$closureGuardRefusal;$record.release_published=$false;$record.full_caller_accepted=$false
  [void](Write-New 'bootstrap-caller-completion_005.json' $record 85)
 }else{
  Need ($null -ne $CompleteToolExitCode) 'Actual completed Complete tool exit required'
  $completionRef=Existing 'bootstrap-caller-completion_005.json';$completion=$completionRef.value
  Receipt $completion 'cho51_p3_bootstrap_caller_completion_v5'
  Closed $completion @('schema','scope','observed_utc','request_sha256','root_admission_sha256','scientific_admission','dispatch_sha256','supervision_sha256','failure_sha256','invoke_tool_call_id','post_invoke_return_upper_bound_qpc','post_invoke_return_upper_bound_utc','invoke_tool_exit_code','start_attempted','start_outcome','qpc_frequency','external_entry_qpc','elapsed_upper_bound_seconds','observation_semantics','invoke_tool_return_observed_by_root','operation_succeeded','custody_closed','closure_guard_passed','closure_guard_refusal','release_published','full_caller_accepted')
  Need ($completion.invoke_tool_return_observed_by_root -is [bool] -and $completion.invoke_tool_return_observed_by_root -and $completion.post_invoke_return_upper_bound_qpc -is [long] -and $completion.post_invoke_return_upper_bound_qpc -lt $modeEntryQpc -and $completion.external_entry_qpc -eq $commonQpc -and $completion.qpc_frequency -eq $frequency -and $completion.dispatch_sha256 -ceq $dispatchRef.sha256 -and $completion.operation_succeeded -is [bool] -and $completion.custody_closed -is [bool]) 'Actual earlier caller completion required'
  Need ($completion.invoke_tool_exit_code -is [long] -and (-not $completion.operation_succeeded -or $completion.invoke_tool_exit_code -eq 0)) 'Actual nonzero Invoke cannot become successful'
  Need ($completion.start_attempted -is [bool] -and $completion.start_outcome -cin @('not_attempted','unknown','started') -and (-not $completion.custody_closed -or $completion.start_outcome -cne 'unknown')) 'Unknown start custody cannot be released'
  if($null -ne $completion.supervision_sha256){$finalEvidence=Existing 'bootstrap-supervision_005.json';Need ($finalEvidence.sha256 -ceq $completion.supervision_sha256 -and $null -eq $completion.failure_sha256 -and -not (Present (Join-Path $run 'bootstrap-failure_005.json'))) 'Supervision changed after caller observation'}
  else{$finalEvidence=Existing 'bootstrap-failure_005.json';Need ($finalEvidence.sha256 -ceq $completion.failure_sha256 -and $null -eq $completion.supervision_sha256) 'Failure changed after caller observation'}
  $finalDiagnosticUsable=Diagnostic-Validate $finalEvidence.value.diagnostics $completion.start_attempted $completion.start_outcome ($null -ne $completion.failure_sha256)
  Need ($finalEvidence.value.start_attempted -is [bool] -and $finalEvidence.value.start_attempted -eq $completion.start_attempted -and $finalEvidence.value.start_outcome -ceq $completion.start_outcome) 'Release must retain original Invoke start state'
  if($null -ne $completion.failure_sha256){
   Receipt $finalEvidence.value 'cho51_p3_bootstrap_failure_v5'
   Diagnostic-ValidateFailureIdentity $finalEvidence.value
  }else{
   Receipt $finalEvidence.value 'cho51_p3_bootstrap_supervision_v5'
   Need ($finalEvidence.value.diagnostics.helper.pid -eq $finalEvidence.value.helper_pid -and $finalEvidence.value.diagnostics.helper.start_utc_ticks -eq $finalEvidence.value.helper_creation_utc_ticks) 'Release helper generation differs from original supervision'
  }
  Need (-not $completion.custody_closed -or $finalDiagnosticUsable) 'Incomplete diagnostic evidence cannot release custody'
  Need (-not $completion.operation_succeeded -or ($finalDiagnosticUsable -and $null -ne $completion.supervision_sha256)) 'Failure diagnostics cannot become success'
  $record=Common 'cho51_p3_bootstrap_release_v5';$record.dispatch_sha256=$dispatchRef.sha256;$record.caller_completion_sha256=$completionRef.sha256
  $record.external_entry_qpc=$commonQpc;$record.qpc_frequency=$frequency;$record.release_publication_elapsed_seconds=Seconds
  $record.start_attempted=$completion.start_attempted;$record.start_outcome=$completion.start_outcome
  $record.complete_tool_exit_code=[int]$CompleteToolExitCode;$record.operation_succeeded=($completion.operation_succeeded -and $closureGuardPassed -and $CompleteToolExitCode -eq 0);$record.custody_closed=$completion.custody_closed;$record.operation_released=$completion.custody_closed;$record.closure_guard_passed=$closureGuardPassed;$record.closure_guard_refusal=$closureGuardRefusal;$record.release_tool_return_observed=$false;$record.post_release_external_audit_required=$true;$record.full_caller_accepted=$false;$record.observational_manifest_accepted=$false
  [void](Write-New 'bootstrap-release_005.json' $record 85)
 }
}catch{
 $primaryException=$_.Exception;$failure=$primaryException.Message
 try{if($null -eq $diagnostics.primary_failure){$diagnostics.primary_failure=[ordered]@{stage=$operationStage;exception=(Diagnostic-Exception $primaryException)}}}catch{Diagnostic-Failed}
 $cleanupOnly=$true
 $failureStdout=$null;$failureStderr=$null;$partialPreserved=(-not $startAttempted -and $startOutcome -ceq 'not_attempted')
 if($startAttempted){
  $cleanupStage='cleanup_identity'
  try{
   Cleanup-Identity;Diagnostic-Event $cleanupStage 'ok'
   $cleanupStage='cleanup_has_exited_kill'
   if(-not $process.HasExited){$process.Kill()}
   Diagnostic-Event $cleanupStage 'ok'
   $cleanupStage='cleanup_wait_reap'
   while((Seconds) -lt 80 -and -not $process.HasExited){
    Clock 80 $false
    if($null -ne $stdout){Drain-Poll $stdout};if($null -ne $stderr){Drain-Poll $stderr}
    [void]$process.WaitForExit(20)
   }
   $childReaped=$process.WaitForExit(0)
   Need ($childReaped) 'Owned helper remained unreaped'
   Diagnostic-Event $cleanupStage 'ok'
   $cleanupStage='cleanup_eof'
   if($null -eq $stdout){$stdout=Drain-New $process.StandardOutput.BaseStream}
   if($null -eq $stderr){$stderr=Drain-New $process.StandardError.BaseStream}
   while((Seconds) -lt 80 -and (-not $stdout.eof -or -not $stderr.eof)){
    Clock 80 $false;Drain-Poll $stdout;Drain-Poll $stderr;[Threading.Thread]::Sleep(10)
   }
   Need ($stdout.eof -and $stderr.eof) 'Cleanup did not reach both EOFs'
   Diagnostic-Event $cleanupStage 'ok'
   $cleanupStage='cleanup_final_table'
   if($childStartTicks -gt 0){Child-Table 'cleanup_final'}else{throw 'Owned helper generation remains unknown'}
   Diagnostic-Event $cleanupStage 'ok'
  }catch{$custodyClosed=$false;Diagnostic-Event $cleanupStage 'failed' $_.Exception}
  try{
   if($null -ne $stdout){
    if(Present (Join-Path $run 'bootstrap-stdout_005.txt')){$failureStdout=Read-PreservedStream 'bootstrap-stdout_005.txt' $stdout.data.ToArray()}
    else{$failureStdout=Write-Stream 'bootstrap-stdout_005.txt' $stdout.data.ToArray()}
   }
   if($null -ne $stderr){
    if(Present (Join-Path $run 'bootstrap-stderr_005.txt')){$failureStderr=Read-PreservedStream 'bootstrap-stderr_005.txt' $stderr.data.ToArray()}
    else{$failureStderr=Write-Stream 'bootstrap-stderr_005.txt' $stderr.data.ToArray()}
   }
   $partialPreserved=($null -ne $failureStdout -and $null -ne $failureStderr)
   Need ($partialPreserved) 'Both retained stream preservation witnesses are required for an ok outcome'
   Diagnostic-Event 'cleanup_stream_preservation' 'ok'
  }catch{$partialPreserved=$false;Diagnostic-Event 'cleanup_stream_preservation' 'failed' $_.Exception}
 }
 if($startOutcome -ceq 'unknown' -or $diagnostics.custody_refused){$custodyClosed=$false}
 if($authenticated){
  try{
   $record=Common 'cho51_p3_bootstrap_failure_v5';$record.mode=$Mode;$record.failure=$failure.Substring(0,[math]::Min(512,$failure.Length))
   $record.start_attempted=$startAttempted;$record.start_outcome=$startOutcome;$record.child_started=$childStarted;$record.child_pid=if($childId -gt 0){$childId}else{$null};$record.child_reaped=$childReaped;$record.custody_closed=$custodyClosed
   $record.stdout_eof=($null -ne $stdout -and $stdout.eof);$record.stderr_eof=($null -ne $stderr -and $stderr.eof)
   $record.stdout=$failureStdout;$record.stderr=$failureStderr;$record.partial_outputs_preserved=$partialPreserved;$record.automatic_retry_permitted=$false;$record.full_caller_accepted=$false
   $record.diagnostics=Diagnostic-Payload
   if(-not $diagnostics.complete -or $diagnostics.overflow){$record.custody_closed=$false}
   [void](Write-New 'bootstrap-failure_005.json' $record 85)
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

