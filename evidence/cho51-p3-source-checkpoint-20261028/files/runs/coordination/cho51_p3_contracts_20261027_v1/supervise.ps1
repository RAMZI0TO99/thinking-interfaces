param(
 [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$PinsSha256,
 [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExternalAdmissionSha256
)
$ErrorActionPreference='Stop'
$entry=[DateTimeOffset]::UtcNow
$watch=[Diagnostics.Stopwatch]::StartNew()
$script:preflightDeadline=$entry.AddSeconds(300)
$root='D:\Aenv\pro3'
$run=$PSScriptRoot
$scope='cho51_p3_contracts_20261027_v1_tests'
if($run -cne (Join-Path $root 'runs\coordination\cho51_p3_contracts_20261027_v1')){throw 'Exact fresh supervisor root required'}
$initialPinsPath=Join-Path $run 'pins.json'
if((Get-FileHash -LiteralPath $initialPinsPath -Algorithm SHA256).Hash.ToLowerInvariant() -cne $PinsSha256){throw 'Pinned preparation changed'}
$initialPins=Get-Content -LiteralPath $initialPinsPath -Raw|ConvertFrom-Json -DateKind String
$initialReviewPath=Join-Path $run 'source-review.json'
if((Get-FileHash -LiteralPath $initialReviewPath -Algorithm SHA256).Hash.ToLowerInvariant() -cne $initialPins.source_review_sha256){throw 'Independent source review changed'}
$initialReview=Get-Content -LiteralPath $initialReviewPath -Raw|ConvertFrom-Json -DateKind String
$nativePath=Join-Path $run 'native.ps1'
$nativeStream=[IO.File]::Open($nativePath,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
try{
 if($nativeStream.Length -le 0 -or $nativeStream.Length -gt 262144){throw 'Native helper bound exceeded'}
 $nativeRaw=[byte[]]::new([int]$nativeStream.Length)
 $nativeStream.ReadExactly($nativeRaw)
 $nativeSha=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($nativeRaw)).ToLowerInvariant()
 if($initialReview.files.'runs/coordination/cho51_p3_contracts_20261027_v1/native.ps1' -cne $nativeSha){throw 'Reviewed native helper required'}
 . ([scriptblock]::Create([Text.UTF8Encoding]::new($false,$true).GetString($nativeRaw)))
}finally{$nativeStream.Dispose()}
$pinsHeld=[Collections.Generic.List[object]]::new()
function Hold-File([string]$path,[string]$expected,[long]$maximum=8388608,[bool]$retain=$true){
 $pin=[ChoP3Native]::Pin($path,$maximum,$retain);$pinsHeld.Add($pin)
 if($expected){Require ($pin.Sha256 -ceq $expected) ('Retained physical hash changed: '+$path)}
 return $pin
}
function Write-New([string]$path,$value){
 $raw=[Text.UTF8Encoding]::new($false).GetBytes(($value|ConvertTo-Json -Depth 24 -Compress)+[char]10)
 Require ($raw.Length -le 8388608) 'Bounded closeout metadata required'
 $stream=[IO.File]::Open($path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
 try{$stream.Write($raw,0,$raw.Length);$stream.Flush($true)}finally{$stream.Dispose()}
}
$pauses=@('20261007','20261012','20261013','20261015','20261025')|ForEach-Object{"D:\Aenv\pro2\WORK\resume-$_-001\coordination\PRO2_REQUEST_PRO3_PAUSE.json"}
[ChoP3Native]::ConfigurePinChecks($script:preflightDeadline.UtcDateTime,[string[]]$pauses,(300-$watch.Elapsed.TotalSeconds))
$script:minRam=[uint64]::MaxValue;$script:minDisk=[uint64]::MaxValue
function Floors{
 $ram=[ChoP3Native]::AvailableMemory();$disk=[ChoP3Native]::AvailableDisk()
 $script:minRam=[math]::Min($script:minRam,$ram);$script:minDisk=[math]::Min($script:minDisk,$disk)
 Require ($ram -ge 4GB -and $disk -ge 20GB) 'External active resource floor'
 foreach($pausePath in $pauses){Require (-not [ChoP3Native]::Exists($pausePath)) 'Genuine peer pause'}
}
$unused=@('closeout-result.json','closeout-supervision_001.json','closeout-supervisor-attempt_001.json','closeout-stdout_001.json','closeout-stderr_001.json')
function Unused([bool]$attemptWritten=$false){
 foreach($name in $unused){if($attemptWritten -and $name -ceq 'closeout-supervisor-attempt_001.json'){continue};Require (-not [ChoP3Native]::Exists((Join-Path $run $name))) 'External closeout attempt already used'}
}
$process=$null;$tree=$null;$outDrain=$null;$errDrain=$null
try{
 $pinsPin=Hold-File $initialPinsPath $PinsSha256
 $pins=Parse-Bytes $pinsPin.Raw
 Require-Text $pins 'schema' 'cho51_p3_contracts_pins_v1'
 Require-Text $pins 'scope' $scope
 Require-Zero $pins.expected_numerical_budget
 Require-Boolean $pins 'scientific_admission' $false
 $reviewPin=Hold-File $initialReviewPath $pins.source_review_sha256
 $review=Parse-Bytes $reviewPin.Raw
 Require-Boolean $review 'source_only' $true
 Require ($review.remaining_actionable_findings -is [object[]] -and $review.remaining_actionable_findings.Count -eq 0) 'Independent source review findings remain'
 $self=Hold-File $PSCommandPath $review.files.'runs/coordination/cho51_p3_contracts_20261027_v1/supervise.ps1' 262144
 $supervisorSha=$self.Sha256
 [void](Hold-File $nativePath $nativeSha 262144)
 $source=Join-Path $run 'closeout.py'
 $sourceSha=$review.files.'runs/coordination/cho51_p3_contracts_20261027_v1/closeout.py'
 [void](Hold-File $source $sourceSha 262144)
 foreach($name in @('metadata_common.py')){[void](Hold-File (Join-Path $run $name) $review.files[('runs/coordination/cho51_p3_contracts_20261027_v1/'+$name)] 262144)}
 $admissionPin=Hold-File (Join-Path $run 'closeout-admission_001.json') $ExternalAdmissionSha256
 $approved=Parse-Bytes $admissionPin.Raw
 Require-Text $approved 'schema' 'cho51_p3_contracts_external_admission_v1'
 Require-Boolean $approved 'accepted' $true
 Require-Text $approved 'pins_sha256' $PinsSha256
 Require-Text $approved 'source_review_sha256' $pins.source_review_sha256
 Require-Text $approved 'supervisor_sha256' $supervisorSha
 Require-Integer $approved 'maximum_jobs' 0
 Require-Integer $approved 'maximum_interpreter_invocations' 1
 Require-Integer $approved 'maximum_seconds' 300
 Require-Boolean $approved 'automatic_retry_permitted' $false
 Require-Boolean $approved 'scientific_admission' $false
 Require-Zero $approved.expected_numerical_budget
 $rootPin=Hold-File (Join-Path $run 'admission.json') $approved.root_admission_sha256
 $rootAdmission=Parse-Bytes $rootPin.Raw
 Require-Text $rootAdmission 'schema' 'cho51_p3_contracts_admission_v1'
 Require-Boolean $rootAdmission 'accepted' $true
 Require-Text $rootAdmission 'pins_sha256' $PinsSha256
 Require-Text $approved 'peer_release_path' $rootAdmission.peer_release_path
 Require-Text $approved 'peer_release_sha256' $rootAdmission.peer_release_sha256
 $peerPin=Hold-File $rootAdmission.peer_release_path $rootAdmission.peer_release_sha256
 $peer=Parse-Bytes $peerPin.Raw
 foreach($record in @($peer,$rootAdmission)){
  Require-Text $record 'scope' $scope
  Require-Text $record 'pins_sha256' $PinsSha256
  Require-Integer $record 'maximum_jobs' 1
  Require-Integer $record 'max_job_seconds' 600
  Require-Integer $record 'process_mib' 4096
  Require-Integer $record 'job_mib' 5120
  Require-Integer $record 'startup_ram_gib' $pins.startup_ram_gib
  Require-Integer $record 'active_ram_gib' 4
  Require-Integer $record 'disk_gib' 20
  Require-Integer $record 'expected_metadata_tests' $pins.expected_tests
  Require-Integer $record 'expected_stdlib_controls' 34
  Require-Integer $record 'external_stdlib_closeout_maximum_seconds' 300
  Require-Boolean $record 'scientific_admission' $false
  Require-Zero $record.expected_numerical_budget
 }
 Require-Text $peer 'schema' 'pro2_pro3_compute_release_v1'
 Require-Boolean $peer 'released' $true
 Require-Text $peer 'owner_resource_amendment_sha256' $pins.owner_resource_amendment_sha256
 $windowStart=Utc-Time $peer 'window_start_utc';$windowEnd=Utc-Time $peer 'window_end_utc'
 foreach($record in @($approved,$rootAdmission)){Require-Text $record 'window_start_utc' $peer.window_start_utc;Require-Text $record 'window_end_utc' $peer.window_end_utc}
 $deadline=Utc-Time $approved 'deadline_utc'
 $observedAdmission=Utc-Time $approved 'observed_utc'
 Require ($observedAdmission -le $entry -and $windowStart -le $entry -and $entry -lt $windowEnd) 'Fresh external admission and live exact peer window required'
 $hardEnd=$entry.AddSeconds(300);if($deadline -lt $hardEnd){$hardEnd=$deadline};if($windowEnd -lt $hardEnd){$hardEnd=$windowEnd}
 $script:preflightDeadline=$hardEnd
 [ChoP3Native]::ConfigurePinChecks($hardEnd.UtcDateTime,[string[]]$pauses,(300-$watch.Elapsed.TotalSeconds))
 $cleanupEnd=$hardEnd.AddSeconds(-2);$stopAt=$hardEnd.AddSeconds(-45)
 $maximumTotalSeconds=[math]::Min(300,($hardEnd-$entry).TotalSeconds)
 $stopAfterSeconds=$maximumTotalSeconds-45;$cleanupAfterSeconds=$maximumTotalSeconds-2
 Require (($stopAt-[DateTimeOffset]::UtcNow).TotalSeconds -ge 60) 'Insufficient complete external closeout reserve'
 $resultPin=Hold-File (Join-Path $run 't1/result.json') $approved.result_sha256
 $result=Parse-Bytes $resultPin.Raw
 Require-Boolean $result 'passed' $true
 Require-Text $result 'pins_sha256' $PinsSha256
 Require-Zero $result.current_counter_ledger
 Require ($result.native_directory -is [string] -and [IO.Path]::GetDirectoryName($result.native_directory) -ceq (Join-Path $root 'runs\migration')) 'Exact native output directory required'
 $receiptPin=Hold-File (Join-Path $result.native_directory 'receipt.json') $approved.native_receipt_sha256
 $receipt=Parse-Bytes $receiptPin.Raw
 Require-Boolean $receipt 'accepted' $true
 Require-Boolean $receipt 'job_absent' $true
 Require-Text $receipt.result 'reason' 'normal'
 Require-Integer $receipt.result 'exit_code' 0
 $runtime=@('D:\Aenv\pro3\.venv\Scripts\python.exe','C:\Users\aladdin-alyanai\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python3.dll','C:\Users\aladdin-alyanai\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python312.dll')
 foreach($path in $runtime){Require-Hash $pins.runtime_files $path;[void](Hold-File $path $pins.runtime_files[$path] 67108864 $false)}
 Floors;Unused
 foreach($pin in $pinsHeld){$pin.Recheck()}
 $info=[Diagnostics.ProcessStartInfo]::new($runtime[0]);$info.UseShellExecute=$false;$info.CreateNoWindow=$true;$info.WindowStyle=[Diagnostics.ProcessWindowStyle]::Hidden;$info.WorkingDirectory=$root;$info.RedirectStandardOutput=$true;$info.RedirectStandardError=$true
 foreach($argument in @('-I','-S','-B',$source,'--expect-pins',$PinsSha256,'--expect-external-admission',$ExternalAdmissionSha256)){[void]$info.ArgumentList.Add($argument)}
 foreach($name in @('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS')){$info.Environment[$name]='1'}
 $info.Environment['CUDA_VISIBLE_DEVICES']='';$info.Environment['PYTHONDONTWRITEBYTECODE']='1'
 $process=[Diagnostics.Process]::new();$process.StartInfo=$info;$tree=[ChoP3Native+OwnedTree]::new()
 $rootPid=$null;$started=$false;$exitCode=$null;$timedOut=$false;$stopReason=$null;$stdoutEof=$false;$stderrEof=$false;$reaped=$false;$launchTime=$null;$discoveryComplete=$true
 $errors=[Collections.Generic.List[string]]::new()
 Write-New (Join-Path $run 'closeout-supervisor-attempt_001.json') ([ordered]@{schema='cho51_p3_contracts_external_supervisor_attempt_v1';observed_utc=[DateTimeOffset]::UtcNow.ToString('o');pins_sha256=$PinsSha256;admission_sha256=$ExternalAdmissionSha256;supervisor_sha256=$supervisorSha;supervisor_review_sha256=$pins.source_review_sha256;maximum_interpreter_invocations=1;maximum_jobs=0;automatic_retry_permitted=$false;scientific_admission=$false})
 function Remaining-Milliseconds([int]$maximum){$remaining=[math]::Min(($cleanupEnd-[DateTimeOffset]::UtcNow).TotalMilliseconds,($cleanupAfterSeconds-$watch.Elapsed.TotalSeconds)*1000);return [int][math]::Max(0,[math]::Min($maximum,[math]::Floor($remaining)))}
 try{
  Floors;Unused $true
  foreach($pin in $pinsHeld){$pin.Recheck()}
  Require ([DateTimeOffset]::UtcNow -ge $windowStart -and ([DateTimeOffset]::UtcNow-$entry).TotalSeconds -lt 255 -and ($stopAt-[DateTimeOffset]::UtcNow).TotalSeconds -ge 60 -and $watch.Elapsed.TotalSeconds -le ($stopAfterSeconds-60)) 'Immediate deadline/window check refused interpreter start'
  $launchTime=[DateTimeOffset]::UtcNow
  if(-not $process.Start()){throw 'Owned interpreter start failed'}
  $started=$true;$rootPid=$process.Id;$tree.Root([uint32]$rootPid,$process.Handle)
  $outDrain=[ChoP3Native+BoundedDrain]::new($process.StandardOutput.BaseStream);$errDrain=[ChoP3Native+BoundedDrain]::new($process.StandardError.BaseStream)
  try{$tree.Discover()}catch{$discoveryComplete=$false;throw}
  while($true){
   if($outDrain.Overflow -or $errDrain.Overflow){throw 'Bounded output overflow'}
   if($outDrain.Error -or $errDrain.Error){throw 'Bounded pipe drain failed'}
   Floors
   if([DateTimeOffset]::UtcNow -ge $stopAt -or $watch.Elapsed.TotalSeconds -ge $stopAfterSeconds){$timedOut=$true;throw 'External closeout stop trigger with cleanup reserve'}
   $wait=[int][math]::Max(0,[math]::Min(100,[math]::Floor(($stopAt-[DateTimeOffset]::UtcNow).TotalMilliseconds)))
   if($process.WaitForExit($wait)){$exitCode=$process.ExitCode;break}
   try{$tree.Discover()}catch{$discoveryComplete=$false;throw}
  }
 }catch{$stopReason=$_.Exception.Message;$errors.Add('execution: '+$_.Exception.Message)}finally{
  if($started){
   if($tree.Records.Count -eq 0){$discoveryComplete=$false;try{[void][ChoP3Native]::StopRetainedRoot($process.Handle,(Remaining-Milliseconds 1000))}catch{$errors.Add('retained root fallback cleanup: '+$_.Exception.Message)}}
   for($round=0;$round -lt 4 -and [DateTimeOffset]::UtcNow -lt $cleanupEnd -and $watch.Elapsed.TotalSeconds -lt $cleanupAfterSeconds;$round++){
    try{$tree.Discover()}catch{$discoveryComplete=$false;$errors.Add('final descendant discovery: '+$_.Exception.Message)}
    foreach($member in @($tree.Records)){try{$tree.Terminate($member)}catch{$errors.Add('exact owned termination: '+$_.Exception.Message)}}
    foreach($member in @($tree.Records)){try{[void]$tree.Reap($member,(Remaining-Milliseconds 500))}catch{$errors.Add('bounded owned reap: '+$_.Exception.Message)}}
    $alive=$false;foreach($member in @($tree.Records)){try{if(-not $tree.Exited($member)){$alive=$true}}catch{$alive=$true;$errors.Add('owned final liveness: '+$_.Exception.Message)}}
    if(-not $alive -and $round -ge 1){break}
   }
   try{if($process.HasExited){$exitCode=$process.ExitCode}else{$errors.Add('root process remains alive')}}catch{$errors.Add('root exit query: '+$_.Exception.Message)}
   $reaped=$discoveryComplete -and $tree.Records.Count -gt 0
   foreach($member in @($tree.Records)){try{if(-not $tree.Exited($member)){$reaped=$false}}catch{$reaped=$false;$errors.Add('final owned identity reap: '+$_.Exception.Message)}}
  }
  foreach($drain in @($outDrain,$errDrain)){if($null -ne $drain){try{[void]$drain.Wait((Remaining-Milliseconds 1000))}catch{$errors.Add('bounded pipe wait: '+$_.Exception.Message)};try{$drain.Dispose()}catch{$errors.Add('pipe disposal: '+$_.Exception.Message)};try{[void]$drain.Wait((Remaining-Milliseconds 500))}catch{$errors.Add('bounded post-disposal pipe wait: '+$_.Exception.Message)}}}
  if($null -ne $outDrain){$stdoutEof=$outDrain.Eof -and -not $outDrain.Overflow -and -not $outDrain.Error;if($outDrain.Overflow){$errors.Add('stdout exceeded 1 MiB')};if($outDrain.Error){$errors.Add('stdout drain: '+$outDrain.Error)}}
  if($null -ne $errDrain){$stderrEof=$errDrain.Eof -and -not $errDrain.Overflow -and -not $errDrain.Error;if($errDrain.Overflow){$errors.Add('stderr exceeded 1 MiB')};if($errDrain.Error){$errors.Add('stderr drain: '+$errDrain.Error)}}
  foreach($row in @(@('closeout-stdout_001.json',$outDrain),@('closeout-stderr_001.json',$errDrain))){if($null -ne $row[1]){try{$bytes=$row[1].Bytes();Write-New (Join-Path $run $row[0]) ([ordered]@{bytes=$bytes.Length;text=[Text.UTF8Encoding]::new($false).GetString($bytes);overflow=$row[1].Overflow;eof=$row[1].Eof;error=$row[1].Error})}catch{$errors.Add('bounded output evidence: '+$_.Exception.Message)}}}
  foreach($pin in $pinsHeld){try{$pin.Recheck()}catch{$errors.Add('final retained source/input identity: '+$_.Exception.Message)}}
  if($null -ne $process){try{$process.Dispose()}catch{$errors.Add('root handle disposal: '+$_.Exception.Message)}}
  if($null -ne $tree){try{$tree.Dispose()}catch{$errors.Add('owned handle disposal: '+$_.Exception.Message)}}
  $observedEnd=[DateTimeOffset]::UtcNow;$watch.Stop()
  if($observedEnd -ge $hardEnd -or $watch.Elapsed.TotalSeconds -gt $maximumTotalSeconds){$timedOut=$true;$errors.Add('absolute external deadline exceeded')}
  if($errors.Count -gt 0 -and -not $stopReason){$stopReason='Supervision or cleanup failure'}
  $identities=@($tree.Records|ForEach-Object{[ordered]@{pid=$_.Pid;parent_pid=$_.ParentPid;creation_filetime=$_.Created.ToString();snapshot_cutoff_filetime=$_.SnapshotCutoff.ToString()}})
  $super=[ordered]@{schema='cho51_p3_contracts_external_supervision_v1';started_utc=$entry.ToString('o');interpreter_started_utc=$(if($launchTime){$launchTime.ToString('o')}else{$null});ended_utc=$observedEnd.ToString('o');elapsed_seconds=$watch.Elapsed.TotalSeconds;owned_pid=$rootPid;observed_owned_pids=@($tree.Records|ForEach-Object{$_.Pid}|Sort-Object);observed_owned_identities=$identities;descendant_snapshots=$tree.Snapshots;owned_tree_discovery_complete=$discoveryComplete;limit_seconds=300;absolute_deadline_utc=$deadline.ToString('o');absolute_window_end_utc=$windowEnd.ToString('o');cleanup_reserve_seconds=45;stop_trigger_utc=$stopAt.ToString('o');timed_out=$timedOut;stop_reason=$stopReason;errors=@($errors);exit_code=$exitCode;interpreter_started=$started;owned_tree_reaped=$reaped;stdout_eof=$stdoutEof;stderr_eof=$stderrEof;stdout_maximum_bytes=1048576;stderr_maximum_bytes=1048576;minimum_available_ram_bytes=$script:minRam;minimum_available_disk_bytes=$script:minDisk;closeout_source_sha256=$sourceSha;supervisor_sha256=$supervisorSha;supervisor_review_sha256=$pins.source_review_sha256;pins_sha256=$PinsSha256;admission_sha256=$ExternalAdmissionSha256;candidate_imported=$false;job_created=$false;maximum_interpreter_invocations=1;scientific_admission=$false}
  Write-New (Join-Path $run 'closeout-supervision_001.json') $super
  $super|ConvertTo-Json -Depth 12
 }
 if(-not $started -or $exitCode -ne 0 -or -not $reaped -or -not $stdoutEof -or -not $stderrEof -or $stopReason -or $errors.Count -ne 0 -or $timedOut -or $observedEnd -gt $hardEnd){exit 1}
}finally{
 foreach($pin in $pinsHeld){$pin.Dispose()}
}
