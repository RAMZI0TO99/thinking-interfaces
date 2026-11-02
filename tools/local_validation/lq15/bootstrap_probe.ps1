param([Parameter(Mandatory=$true)][string]$Admission,[Parameter(Mandatory=$true)][string]$AdmissionSha256,[Parameter(Mandatory=$true)][ValidateSet('accepted','bad_identity')][string]$Case,[Parameter(Mandatory=$true)][string]$EnclosingUtc,[Parameter(Mandatory=$true)][long]$EnclosingQpc,[Parameter(Mandatory=$true)][long]$EnclosingFrequency)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$originUtc=[DateTime]::UtcNow
$originQpc=[Diagnostics.Stopwatch]::GetTimestamp()
$frequency=[Diagnostics.Stopwatch]::Frequency
# Establish the independent hard deadline before any pin, PDH query or image
# work. This is a direct managed Action bound to the original Process object;
# no PowerShell scriptblock callback or callback runspace is involved. Caching
# SafeHandle first keeps Process.Kill on this process's original cached handle.
$callerProcess=[Diagnostics.Process]::GetCurrentProcess()
$callerOriginalHandle=$callerProcess.SafeHandle
$fileClosure=@{closed=$false}
$startupDisarmed=$false
try {
    $killAction=[Delegate]::CreateDelegate([Action],$callerProcess,'Kill')
    $hardDeadline=[Threading.CancellationTokenSource]::new()
    $deadlineRegistration=$hardDeadline.Token.Register($killAction)
    $hardDeadline.CancelAfter([Math]::Max(1,[int](10000-([Diagnostics.Stopwatch]::GetTimestamp()-$originQpc)*1000/$frequency)))
    $startupDeadline=[Threading.CancellationTokenSource]::new()
    $startupRegistration=$startupDeadline.Token.Register($killAction)
    $startupDeadline.CancelAfter([Math]::Max(1,[int](5000-([Diagnostics.Stopwatch]::GetTimestamp()-$originQpc)*1000/$frequency)))
    $faultDeadline=[Threading.CancellationTokenSource]::new()
    $faultRegistration=$faultDeadline.Token.Register($killAction)
} catch {
    # No pin/image/child effect has occurred. If the independent deadline
    # cannot be armed, fail by this same cached original process handle.
    $callerProcess.Kill()
    throw 'independent bootstrap deadline could not arm; self termination failed'
}
$journal=@{schema='cho51_q_bootstrap_event_v1';stream=$null;lock=[object]::new();closed=$false;faulted=$false;bytes=0L;records=0;operation=$null;caller_pid=$null;creation_filetime=$null;authority_pending=$true}
$guardPowerShell=$null;$guardRunspace=$null;$guardInvocation=$null
$guardLifecycle=@{joined=$false;closed=$false;completion_wait_closed=$false;shutdown_elapsed_seconds=$null}
$guardState=[hashtable]::Synchronized(@{ready=$false;done=$false;stop=$false;error=$null;samples=0;minimum_ram=[long]::MaxValue;minimum_disk=[long]::MaxValue;peak_private=0L;first_sample=$null;second_sample=$null;last_qpc=0L;stage='not_started'})
try {
$projectRoot='D:/Aenv/pro3'
$phase=Join-Path $projectRoot 'runs/coordination/cho51_p3_probe_20261101_q2'
$stopPath=Join-Path $projectRoot 'runs/coordination/PROJECT_STOP.json'
$bootstrapPhase=$true;$bootstrapOwner=$null;$bootstrapCustody=$null;$bootstrapHelperLoaded=$false;$bootstrapIdentityRefusedBeforeLoad=$false;$nativeReady=$false;$inputPins=[Collections.Generic.List[object]]::new();$finalInputVerified=$false;$bootstrapControls=@();$inputs=[Collections.Generic.List[IO.FileStream]]::new()
$outputs=[Collections.Generic.List[IO.FileStream]]::new()
$owner=$null;$accepted=$false;$callerError=$null;$operation=$null;$claimCreated=$false
$handoff=$null;$outText='';$errText='';$state=@{};$samples=@();$supervisorExit=$null;$initialPrivate=$null
# This exact inline guard is part of the pinned invoke_q source. Its whole
# pipeline runs in its own dedicated runspace, independently of image loading and
# caller pinning. No PowerShell scriptblock is used as a thread/timer callback.
function Journal($sink,[string]$event,[string]$detail='') {
    [Threading.Monitor]::Enter($sink.lock)
    try {
        if($sink.closed -or $sink.faulted -or $null -eq $sink.stream){throw 'bootstrap journal unavailable'}
        if($sink.records -ge 32){throw 'bootstrap journal record cap'}
        if($detail.Length -gt 1024){$detail=$detail.Substring(0,1024)}
        $row=@{schema='cho51_q_bootstrap_event_v1';operation_id=$sink.operation;sequence=$sink.records;event=$event;detail=$detail;utc=[DateTime]::UtcNow.ToString('o');qpc=[Diagnostics.Stopwatch]::GetTimestamp();frequency=[Diagnostics.Stopwatch]::Frequency;caller_pid=$sink.caller_pid;caller_creation_filetime=$sink.creation_filetime;internal_authority_pending=$sink.authority_pending}
        $raw=[Text.Encoding]::UTF8.GetBytes(($row|ConvertTo-Json -Depth 5 -Compress)+[Environment]::NewLine)
        if($raw.Length -gt 4096 -or $sink.bytes+$raw.Length -gt 65536){throw 'bootstrap journal byte cap'}
        $s=$sink.stream
        if($s.Length -ne $sink.bytes){throw 'bootstrap journal length drift'}
        $s.Position=$sink.bytes;$s.Write($raw,0,$raw.Length);$s.Flush($true);$s.Position=$sink.bytes
        $copy=[byte[]]::new($raw.Length);$offset=0
        while($offset -lt $copy.Length){$n=$s.Read($copy,$offset,$copy.Length-$offset);if($n -le 0){throw 'journal short original readback'};$offset+=$n}
        if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($copy)) -cne [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($raw))){throw 'journal original readback'}
        $sink.bytes+=$raw.Length;$sink.records++
    } catch {$sink.faulted=$true;throw}
    finally {[Threading.Monitor]::Exit($sink.lock)}
}
# Native guard script is supplied by the exact reviewed shared bootstrap module.
function ClosedRecord($value,[string[]]$keys) {
    if($value -isnot [Collections.IDictionary] -or $value.Count -ne $keys.Count){throw 'closed record'}
    foreach($key in $keys){if(-not (@($value.Keys) -ccontains $key)){throw ('record key '+$key)}}
}
function StrictJson([string]$text) {
    $options=[Text.Json.JsonDocumentOptions]::new();$options.MaxDepth=32
    $document=[Text.Json.JsonDocument]::Parse($text,$options)
    $budget=@{nodes=0}
    function VisitJson($node,$budget) {
        $budget.nodes++;if($budget.nodes -gt 20000){throw 'JSON node cap'}
        switch($node.ValueKind.ToString()) {
            'Object' {$seen=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase);foreach($property in $node.EnumerateObject()){if(-not $seen.Add($property.Name)){throw 'duplicate/case-alias JSON key'};VisitJson $property.Value $budget}}
            'Array' {if($node.GetArrayLength() -gt 4096){throw 'JSON array cap'};foreach($item in $node.EnumerateArray()){VisitJson $item $budget}}
            'String' {if($node.GetString().Length -gt 32768){throw 'JSON string cap'}}
        }
    }
    try{VisitJson $document.RootElement $budget;return ($text|ConvertFrom-Json -AsHashtable -DateKind String)}finally{$document.Dispose()}
}
function ReadPinnedJson($ref) {
    ClosedRecord $ref @('path','bytes','sha256')
    if($ref.path -isnot [string] -or [IO.Path]::GetFullPath($ref.path).Replace('\','/') -cne $ref.path -or $ref.sha256 -cnotmatch '^[0-9a-f]{64}$' -or $ref.bytes -is [bool] -or $ref.bytes -lt 1 -or $ref.bytes -gt 8MB){throw 'control reference'}
    $pin=PinBytes $ref.path
    if($pin.bytes -ne $ref.bytes -or $pin.sha256 -cne $ref.sha256){throw 'control byte pin'}
    $stream=$inputs[$inputs.Count-1];$reader=[IO.StreamReader]::new($stream,[Text.UTF8Encoding]::new($false,$true),$false,65536,$true)
    try{$text=$reader.ReadToEnd()}finally{$reader.Dispose();$stream.Position=0}
    return StrictJson $text
}


# This file is textually embedded in both reviewed callers, not independently
# executed from a pathname. Kept as the reviewed source comparison reference.
function LoadReviewedNativeBootstrap([string]$Role,[string]$Case='accepted') {
    $pin=PinBytes $Admission
    if($pin.sha256 -cne $AdmissionSha256 -or $pin.bytes -gt 1MB){throw 'bootstrap admission pin'}
    $request=ReadPinnedJson @{path=[IO.Path]::GetFullPath($Admission).Replace('\','/');bytes=$pin.bytes;sha256=$pin.sha256}
    $keys=if($Role -ceq 'P'){@('schema','stage','operation_id','created_utc','expires_utc','root','python','runtime','caller_runtime','sources','review','adoption','qualification','native_helper','map_index','coverage_review','extra_paths','limits','forbidden','scientific_admission','api_mapping','native_diagnostic','l_native_bundle','plan_spec','bootstrap_qualification')}else{@('schema','stage','operation_id','created_utc','expires_utc','root','python','runtime','caller_runtime','sources','review','adoption','predecessor','limits','modes','expected_tests','forbidden','scientific_admission','compiler','native_compiler','bootstrap_qualification','bootstrap_controls')}
    ClosedRecord $request $keys
    $stage=if($Role -ceq 'P'){'P'}else{'Q'}
    if($request.schema -cne ('cho51_'+$stage.ToLowerInvariant()+'_admission_v1') -or $request.stage -cne $stage -or $request.operation_id -cne $journal.operation -or $request.root -cne $projectRoot -or $request.scientific_admission -isnot [bool] -or $request.scientific_admission){throw 'bootstrap current stage authority'}
    AdmissionWindow $request.created_utc $request.expires_utc $originUtc
    $controls=@{}
    foreach($key in @('review','adoption')){
        $r=$request[$key];ClosedRecord $r @('path','bytes','sha256')
        $leaf=if($key -ceq 'review'){'source-review.json'}else{'contract-adoption.json'}
        $expected=if($stage -ceq 'P'){$phase.Replace('\','/')+'/'+$leaf}else{$leaf}
        $relative=if($stage -ceq 'P'){'runs/coordination/cho51_p3_probe_20261101_q2/'+$leaf}else{$leaf}
        if($r.path -cne $relative){throw 'bootstrap current review namespace'}
        $controls[$key]=ReadPinnedJson @{path=$phase.Replace('\','/')+'/'+$leaf;bytes=$r.bytes;sha256=$r.sha256}
    }
    $review=$controls.review;$adoption=$controls.adoption
    $status=if($stage -ceq 'P'){'ACCEPTED_SOURCE_LP1'}else{'ACCEPTED_SOURCE_LQ1'}
    if($review.status -cne $status -or $review.reviewer -isnot [string] -or $review.reviewer -cnotmatch '^[a-z][a-z0-9_-]{0,63}$' -or $review.authors -isnot [array] -or $review.authors.Count -lt 1 -or $review.authors -ccontains $review.reviewer -or $review.findings -isnot [array] -or $review.findings.Count -ne 0 -or $review.sources.Count -ne $request.sources.Count){throw 'bootstrap current independent source review'}
    foreach($row in $request.sources.GetEnumerator()){
        if(-not $review.sources.ContainsKey($row.Key) -or $review.sources[$row.Key].bytes -ne $row.Value.bytes -or $review.sources[$row.Key].sha256 -cne $row.Value.sha256){throw 'bootstrap current reviewed sources'}
    }
    $contract='docs/phase2/cho51_p3_probe_v2_contract_20261101.md'
    if($adoption.author -cne 'project_root' -or $adoption.status -cne ('ADOPTED_'+$stage+'_ONLY') -or $adoption.source_review_sha256 -cne $request.review.sha256 -or $adoption.supplement_sha256 -cne $request.sources[$contract].sha256 -or $adoption.bootstrap_qualification_sha256 -cne $request.bootstrap_qualification.sha256){throw 'bootstrap current scoped adoption'}
    if((UtcString $review.created_utc) -gt (UtcString $adoption.created_utc) -or (UtcString $adoption.created_utc) -gt (UtcString $request.created_utc)){throw 'bootstrap current review/adoption order'}
    foreach($key in @('historical_custody_closed','historical_operation_released','historical_retry_allowed','restart_qualified','boundary_qualified','complete_dependency_closure','launch_authorized','scientific_admission')){if($adoption[$key] -isnot [bool] -or $adoption[$key]){throw 'bootstrap current scope expansion'}}
    $relative='tools/local_validation/lp15/native_bootstrap.ps1';$modulePin=$request.sources[$relative]
    $rawRef=@{path=$projectRoot+'/'+$relative;bytes=$modulePin.bytes;sha256=$modulePin.sha256}
    $pinned=PinBytes $rawRef.path
    if($pinned.bytes -ne $rawRef.bytes -or $pinned.sha256 -cne $rawRef.sha256 -or $pinned.bytes -gt 1MB){throw 'shared bootstrap exact reviewed module'}
    $stream=$inputs[$inputs.Count-1];$reader=[IO.StreamReader]::new($stream,[Text.UTF8Encoding]::new($false,$true),$false,65536,$true)
    try{$source=$reader.ReadToEnd()}finally{$reader.Dispose();$stream.Position=0}
    # The current independent review and Root adoption were checked before this
    # execution. Source strings are never accepted solely on an admission pin.
    . ([scriptblock]::Create($source))
    $sampler=InitializeNativeBootstrap $request $Role $Case
    $script:NativeBootstrapGuardScript=$NativeBootstrapGuardScript
    return $sampler
}

function OwnerState($item) {
    return @{creation_attempted=$item.CreationAttempted;pid=$item.Pid;creation_filetime=$item.CreationFileTime;limits_verified=$item.LimitsVerified;atomic_membership=$item.AtomicMembership;resumed=$item.Resumed;job_empty=$item.JobEmpty;job_closed=$item.JobClosed;process_closed=$item.ProcessClosed;thread_closed=$item.ThreadClosed;reaped=$item.Reaped;fault=$item.Fault;cleanup_error=$item.CleanupError;samples=$item.Samples;minimum_ram=$item.MinimumRam;minimum_disk=$item.MinimumDisk;peak_caller_private=$item.PeakCallerPrivate;peak_process=$item.PeakProcessBytes;peak_job=$item.PeakJobBytes;watchdog_joined=$item.WatchdogJoined;owned_nul_closed=$item.InputClosed;stdout_eof=$item.StdoutEof;stderr_eof=$item.StderrEof;stdout_overflow=$item.StdoutOverflow;stderr_overflow=$item.StderrOverflow;stdout_reader_closed=$item.StdoutReaderClosed;stderr_reader_closed=$item.StderrReaderClosed;stdout_writer_closed=$item.StdoutWriterClosed;stderr_writer_closed=$item.StderrWriterClosed;stdout_reader_thread_handle_closed=$item.StdoutThreadClosed;stderr_reader_thread_handle_closed=$item.StderrThreadClosed;stdout_reader_joined=$item.StdoutJoined;stderr_reader_joined=$item.StderrJoined;stdout_cancel_attempted=$item.StdoutCancelled;stderr_cancel_attempted=$item.StderrCancelled;stdout_retained_bytes=$item.StdoutBytes;stderr_retained_bytes=$item.StderrBytes;stdout_observed_bytes=$item.StdoutObserved;stderr_observed_bytes=$item.StderrObserved;stdout_error=$item.StdoutError;stderr_error=$item.StderrError}
}

function VerifyCallerInputs {
 foreach($entry in $inputPins){Check;$s=$entry.stream;if($s.Length -ne $entry.pin.bytes -or [PNative.Owner]::FileIdentity($s.SafeFileHandle) -cne $entry.native_identity){throw 'final caller native identity/length'};$h=[Security.Cryptography.IncrementalHash]::CreateHash([Security.Cryptography.HashAlgorithmName]::SHA256);try{$s.Position=0;$buffer=[byte[]]::new(65536);do{Check;$n=$s.Read($buffer,0,$buffer.Length);if($n){$h.AppendData($buffer,0,$n)}}while($n);if([Convert]::ToHexString($h.GetHashAndReset()).ToLowerInvariant() -cne $entry.pin.sha256){throw 'final caller original bytes'}}finally{$h.Dispose()}}
 $script:finalInputVerified=$true
}
function Elapsed {([Diagnostics.Stopwatch]::GetTimestamp()-$originQpc)/$frequency}
function GuardSnapshot {
    [Threading.Monitor]::Enter($guardState.SyncRoot)
    try{return @{ready=$guardState.ready;done=$guardState.done;stop_requested=$guardState.stop;error=$guardState.error;samples=$guardState.samples;minimum_ram=$guardState.minimum_ram;minimum_disk=$guardState.minimum_disk;peak_caller_private=$guardState.peak_private;first_sample=$guardState.first_sample;second_sample=$guardState.second_sample;last_qpc=$guardState.last_qpc;joined=$guardLifecycle.joined;closed=$guardLifecycle.closed;completion_wait_closed=$guardLifecycle.completion_wait_closed;shutdown_elapsed_seconds=$guardLifecycle.shutdown_elapsed_seconds;stage=$guardState.stage}}
    finally{[Threading.Monitor]::Exit($guardState.SyncRoot)}
}
function StopGuard {
    if($guardLifecycle.closed){return}
    $shutdownDeadline=[Threading.CancellationTokenSource]::new()
    $shutdownRegistration=$shutdownDeadline.Token.Register($killAction)
    $shutdownDeadline.CancelAfter(1000)
    $shutdownOrigin=[Diagnostics.Stopwatch]::GetTimestamp()
    $guardState.stop=$true
    if($null -ne $guardInvocation){
        $completion=$guardInvocation.AsyncWaitHandle
        if(-not $completion.WaitOne(1000)){$killAction.Invoke();throw 'independent guard did not join within one second'}
        [void]$guardPowerShell.EndInvoke($guardInvocation)
        if(-not $guardState.done -or $null -ne $guardState.error -or $guardPowerShell.HadErrors){$killAction.Invoke();throw 'independent guard completion fault'}
        $guardLifecycle.joined=$true
        $completion.Dispose();$guardLifecycle.completion_wait_closed=$true
    }
    if($null -ne $guardPowerShell){$guardPowerShell.Dispose()}
    if($null -ne $guardRunspace){$guardRunspace.Dispose()}
    $guardLifecycle.shutdown_elapsed_seconds=([Diagnostics.Stopwatch]::GetTimestamp()-$shutdownOrigin)/$frequency
    if($guardLifecycle.shutdown_elapsed_seconds -gt 1){$killAction.Invoke();throw 'independent guard shutdown exceeded one second'}
    $guardLifecycle.closed=$true
    $shutdownDeadline.CancelAfter([Threading.Timeout]::Infinite)
    $shutdownRegistration.Dispose();$shutdownDeadline.Dispose()
}
function Check {
    if($EnclosingFrequency -ne $frequency -or ([Diagnostics.Stopwatch]::GetTimestamp()-$EnclosingQpc)/$frequency -lt 0 -or ([Diagnostics.Stopwatch]::GetTimestamp()-$EnclosingQpc)/$frequency -ge 60){throw 'original enclosing Q work interval'}

    if($bootstrapPhase){if((Elapsed) -ge 5 -or [DateTime]::UtcNow -ge $originUtc.AddSeconds(5)){throw 'bootstrap original five-second deadline'};$callerProcess.Refresh();if($callerProcess.PrivateMemorySize64 -gt 512MB -or [IO.DriveInfo]::new('D').AvailableFreeSpace -lt 20GB){throw 'bootstrap private/disk limits'};$directory=[IO.FileInfo]::new($stopPath).Directory;while($null -ne $directory){$attr=[IO.File]::GetAttributes($directory.FullName);if(($attr -band [IO.FileAttributes]::ReparsePoint) -or -not ($attr -band [IO.FileAttributes]::Directory)){throw 'bootstrap stop ancestry'};$directory=$directory.Parent};try{[void][IO.File]::GetAttributes($stopPath);throw 'bootstrap stop present'}catch [IO.FileNotFoundException]{};return}

    if((Elapsed) -ge 240 -or [DateTime]::UtcNow -ge $originUtc.AddSeconds(240)){throw 'original P work deadline'}
    if(-not $guardState.ready -or $guardState.done -or $null -ne $guardState.error -or $null -eq $guardInvocation -or $guardInvocation.IsCompleted){throw 'independent caller guard not active'}
    if(([Diagnostics.Stopwatch]::GetTimestamp()-$guardState.last_qpc)/$frequency -gt 0.25){$killAction.Invoke();throw 'independent caller guard sample stale'}
    if($null -ne $owner){$owner.Check();return}
    $dir=[IO.DirectoryInfo]::new((Split-Path $stopPath))
    while($null -ne $dir){if([IO.File]::GetAttributes($dir.FullName) -band [IO.FileAttributes]::ReparsePoint){throw 'stop ancestry'};$dir=$dir.Parent}
    try{[IO.File]::GetAttributes($stopPath)|Out-Null;throw 'project stop present'}catch [IO.FileNotFoundException]{}
    if(([IO.DriveInfo]::new('D')).AvailableFreeSpace -lt 20GB){throw 'disk floor'}
}
function PinBytes($path) {
    Check
    $s=[IO.FileStream]::new($path,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read);$inputs.Add($s);$fileClosure.closed=$false
    if($s.Length -gt 64MB){throw 'input byte cap'}
    $h=[Security.Cryptography.IncrementalHash]::CreateHash([Security.Cryptography.HashAlgorithmName]::SHA256)
    try{$b=[byte[]]::new(65536);do{Check;$n=$s.Read($b,0,$b.Length);if($n){$h.AppendData($b,0,$n)}}while($n)
        $s.Position=0;$pin=@{bytes=$s.Length;sha256=[Convert]::ToHexString($h.GetHashAndReset()).ToLowerInvariant()};$entry=@{stream=$s;pin=$pin;native_identity=$null};if($nativeReady){$entry.native_identity=[PNative.Owner]::FileIdentity($s.SafeFileHandle)};$inputPins.Add($entry);return $pin
    }finally{$h.Dispose()}
}
function NewOutput($name) {
    if($name -notmatch '^(claim|origin|caller-return|timestamp-controls)_[0-9a-f-]{36}\.json$'){throw 'output name'}
    $s=[IO.FileStream]::new((Join-Path $phase $name),[IO.FileMode]::CreateNew,[IO.FileAccess]::ReadWrite,[IO.FileShare]::Read)
    $outputs.Add($s);$fileClosure.closed=$false;return $s
}
function WriteRecord($name,$value) {
    $raw=[Text.Encoding]::UTF8.GetBytes(($value|ConvertTo-Json -Depth 30 -Compress)+[Environment]::NewLine)
    if($raw.Length -gt 1MB){throw 'caller record bound'}
    $s=NewOutput $name;$s.Write($raw,0,$raw.Length);$s.Flush($true);$s.Position=0
    $copy=[byte[]]::new($raw.Length)
    if($s.Read($copy,0,$copy.Length) -ne $raw.Length -or -not [Linq.Enumerable]::SequenceEqual[byte]($raw,$copy)){throw 'same-handle readback'}
    $s.Position=0
}
function UtcString($value) {
    if($value -isnot [string] -or $value.Length -gt 64 -or $value -cnotmatch '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,7})?(Z|\+00:00)$'){throw 'explicit UTC string required'}
    $parsed=[DateTimeOffset]::Parse($value,[Globalization.CultureInfo]::InvariantCulture,[Globalization.DateTimeStyles]::None)
    if($parsed.Offset -ne [TimeSpan]::Zero){throw 'explicit UTC string required'}
    return $parsed.UtcDateTime
}
function AdmissionWindow($created,$expires,[DateTime]$original) {
 $start=UtcString $created;$end=UtcString $expires;$outer=UtcString $EnclosingUtc
 if($start -gt $outer -or $end -lt $outer.AddSeconds(90) -or $original -lt $outer -or ($end-$start).TotalSeconds -gt 900){throw 'original enclosing Q admission window'}
}

# A fixed Q-only harness. No P supervisor, compiler, Python or candidate dispatch.
$caseRoot=$null;$caseJournal=$null;$refusedBeforeLoad=$false;$guardStarted=$false
try {
    $requestPin=PinBytes $Admission
    if($requestPin.sha256 -cne $AdmissionSha256){throw 'harness original admission pin'}
    $request=ReadPinnedJson @{path=[IO.Path]::GetFullPath($Admission).Replace('\','/');bytes=$requestPin.bytes;sha256=$AdmissionSha256}
    $operation=$request.operation_id
    if($request.stage -cne 'Q' -or $operation -cne ([guid]$operation).ToString() -or ($request.bootstrap_controls -join ',') -cne 'accepted,bad_identity'){throw 'explicit Q-only harness admission'}
    $caseRoot=$phase.Replace('\','/')+'/bootstrap-controls/'+$operation+'/'+$Case
    if(-not $env:HOME -or $env:HOME.Replace('\','/') -cne $caseRoot -or $env:USERPROFILE.Replace('\','/') -cne $caseRoot -or $env:DOTNET_MultiCoreJitNoProfileGather -cne '1'){throw 'fixed attempt-owned harness environment'}
    if(-not [IO.Directory]::Exists($caseRoot)){throw 'parent-created harness root'}
    $journal.operation=$operation;$journal.caller_pid=$callerProcess.Id;$journal.creation_filetime=$callerProcess.StartTime.ToUniversalTime().ToFileTimeUtc()
    $caseJournal=$caseRoot+'/bootstrap.jsonl'
    $journal.stream=[IO.FileStream]::new($caseJournal,[IO.FileMode]::CreateNew,[IO.FileAccess]::ReadWrite,[IO.FileShare]::Read)
    Journal $journal 'harness_entry'
    $bootstrapOwner=LoadReviewedNativeBootstrap 'P_Q_CONTROL' $Case
    $guardRunspace=[Management.Automation.Runspaces.RunspaceFactory]::CreateRunspace();$guardRunspace.Open()
    $guardPowerShell=[Management.Automation.PowerShell]::Create();$guardPowerShell.Runspace=$guardRunspace
    # Same shared P guard implementation; outer Q caps and this extra caller cap
    # remain512MiB. The child clock is a5s startup subinterval inside original Q.
    [void]$guardPowerShell.AddScript($NativeBootstrapGuardScript).AddArgument($callerProcess).AddArgument($killAction).AddArgument($originQpc).AddArgument($originUtc).AddArgument($frequency).AddArgument($stopPath).AddArgument($guardState).AddArgument($journal).AddArgument($faultDeadline).AddArgument($bootstrapOwner).AddArgument(240).AddArgument(512MB)
    $guardInvocation=$guardPowerShell.BeginInvoke();$guardStarted=$true
    while(-not $guardState.ready){if($guardState.done -or $guardInvocation.IsCompleted -or $null -ne $guardState.error -or (Elapsed) -ge 5){throw 'harness native startup'};[Threading.Thread]::Sleep(5)}
    if((Elapsed) -ge 5 -or ($guardState.second_sample.qpc-$guardState.first_sample.qpc_end)/$frequency -lt .2){throw 'harness original two-sample readiness'}
    $bootstrapPhase=$false;$startupDisarmed=$true;$startupDeadline.CancelAfter([Threading.Timeout]::Infinite)
    VerifyCallerInputs;$accepted=$true
}catch{
    $callerError=$_.Exception.GetType().Name+': '+$_.Exception.Message
    $refusedBeforeLoad=$Case -ceq 'bad_identity' -and $bootstrapIdentityRefusedBeforeLoad -and -not $bootstrapHelperLoaded -and $null -eq $bootstrapOwner
}
finally {
    # Same original streams/guard/sampler ownership discipline as the callers.
    foreach($stream in $inputs){$stream.Dispose()};$fileClosure.closed=$true
    if($null -ne $journal.stream){$journal.stream.Flush($true);$journal.stream.Dispose();$journal.closed=$true}
    StopGuard
    if($null -ne $bootstrapOwner){
        $bootstrapOwner.Dispose();$bootstrapCustody=OwnerState $bootstrapOwner
        if($bootstrapCustody.creation_attempted -or -not $bootstrapCustody.job_closed -or -not $bootstrapCustody.job_empty -or -not $bootstrapCustody.watchdog_joined -or $null -ne $bootstrapCustody.fault -or $null -ne $bootstrapCustody.cleanup_error){$accepted=$false}
    }
}
$ok=if($Case -ceq 'accepted'){$accepted -and $finalInputVerified -and $guardState.ready -and $guardState.done -and $guardLifecycle.joined -and $guardLifecycle.closed -and $null -eq $guardState.error}else{$refusedBeforeLoad -and -not $guardStarted -and $fileClosure.closed -and $journal.closed}
$record=@{schema='cho51_lp4_bootstrap_control_v1';operation_id=$operation;case=$Case;role='P_BOOTSTRAP_Q_CONTROL';expected_outcome_observed=$ok;accepted=$accepted;error=$callerError;helper_loaded=$bootstrapHelperLoaded;refused_before_load=$refusedBeforeLoad;final_input_verification=$finalInputVerified;original_streams_closed=$fileClosure.closed;journal_path=$caseJournal;journal_closed=$journal.closed;guard=GuardSnapshot;sampler_custody=$bootstrapCustody;origin_utc=$originUtc.ToString('o');origin_qpc=$originQpc;frequency=$frequency;enclosing_utc=$EnclosingUtc;enclosing_qpc=$EnclosingQpc;enclosing_frequency=$EnclosingFrequency;elapsed_seconds=(Elapsed);source_bootstrap_sha256=$request.sources['tools/local_validation/lp15/native_bootstrap.ps1'].sha256;exit_is_not_P_acceptance=$true;scientific_admission=$false;candidate_tests_executed=0;successor_controls_executed=0}
$record|ConvertTo-Json -Depth 12 -Compress
if(-not $ok){exit 1}
} finally {
    # The outer original-handle hard timer stays armed through all closure and
    # stdout publication, including failures before the inner harness body.
    if($null -ne $bootstrapOwner){$bootstrapOwner.Dispose()}
    if(-not $guardLifecycle.closed){StopGuard}
    foreach($stream in $inputs){$stream.Dispose()}
    if($null -ne $journal.stream -and -not $journal.closed){$journal.stream.Dispose();$journal.closed=$true}
    $startupDeadline.CancelAfter([Threading.Timeout]::Infinite);$hardDeadline.CancelAfter([Threading.Timeout]::Infinite)
    $startupRegistration.Dispose();$startupDeadline.Dispose();$deadlineRegistration.Dispose();$hardDeadline.Dispose();$faultRegistration.Dispose();$faultDeadline.Dispose();$callerProcess.Dispose()
}
