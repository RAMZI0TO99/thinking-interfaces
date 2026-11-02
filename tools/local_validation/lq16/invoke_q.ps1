param([Parameter(Mandatory=$true)][string]$Admission,[Parameter(Mandatory=$true)][string]$AdmissionSha256)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$originUtc=[DateTime]::UtcNow
$originQpc=[Diagnostics.Stopwatch]::GetTimestamp()
$frequency=[Diagnostics.Stopwatch]::Frequency
# Establish the independent hard deadline before any pin, PDH query or compiler
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
    $hardDeadline.CancelAfter([Math]::Max(1,[int](65000-([Diagnostics.Stopwatch]::GetTimestamp()-$originQpc)*1000/$frequency)))
    $startupDeadline=[Threading.CancellationTokenSource]::new()
    $startupRegistration=$startupDeadline.Token.Register($killAction)
    $startupDeadline.CancelAfter([Math]::Max(1,[int](5000-([Diagnostics.Stopwatch]::GetTimestamp()-$originQpc)*1000/$frequency)))
    $faultDeadline=[Threading.CancellationTokenSource]::new()
    $faultRegistration=$faultDeadline.Token.Register($killAction)
} catch {
    # No pin/compiler/child effect has occurred. If the independent deadline
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
$phase=Join-Path $projectRoot 'runs/coordination/cho51_p3_probe_20261101_q3'
$stopPath=Join-Path $projectRoot 'runs/coordination/PROJECT_STOP.json'
$bootstrapPhase=$true;$bootstrapOwner=$null;$bootstrapCustody=$null;$bootstrapHelperLoaded=$false;$bootstrapIdentityRefusedBeforeLoad=$false;$nativeReady=$false;$inputPins=[Collections.Generic.List[object]]::new();$finalInputVerified=$false;$bootstrapControls=@();$inputs=[Collections.Generic.List[IO.FileStream]]::new()
$outputs=[Collections.Generic.List[IO.FileStream]]::new()
$callerOutputReservations=[Collections.Generic.Dictionary[string,long]]::new([StringComparer]::OrdinalIgnoreCase)
$callerOutputReservedBytes=0L
$owner=$null;$accepted=$false;$callerError=$null;$operation=$null;$claimCreated=$false
$apiMapping=$null;$apiIdentity=$null;$nativeDiagnostic=$null;$diagnosticIdentity=$null
$callerArtifacts=[Collections.Generic.List[object]]::new()
$lNativeArtifacts=[Collections.Generic.List[object]]::new()
$lToolInputs=[Collections.Generic.List[object]]::new()
$lBuildOperations=[Collections.Generic.List[object]]::new()
$lDirectoryHandles=@{}
$lBundle=$null;$lFinalVerified=$false
$artifactHandoff=@{consumers_reaped=$false;final_original_recheck=$false;original_writers_held_through_consumers=$false;artifacts=@()}
$outText='';$errText='';$state=@{};$samples=@();$supervisorExit=$null;$initialPrivate=$null
# This exact inline guard is part of the pinned invoke_q source. Its whole
# pipeline runs in its own dedicated runspace, independently of Add-Type and
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
    $keys=if($Role -ceq 'P'){@('schema','stage','operation_id','created_utc','expires_utc','root','python','runtime','caller_runtime','sources','review','adoption','qualification','native_helper','map_index','coverage_review','extra_paths','limits','forbidden','scientific_admission','api_mapping','native_diagnostic','l_native_bundle','plan_spec','bootstrap_qualification','qualification_aggregate')}else{@('schema','stage','operation_id','created_utc','expires_utc','root','python','runtime','caller_runtime','sources','review','adoption','predecessor','limits','modes','expected_tests','forbidden','scientific_admission','compiler','native_compiler','bootstrap_qualification','bootstrap_controls')}
    ClosedRecord $request $keys
    $stage=if($Role -ceq 'P'){'P'}else{'Q'}
    if($request.schema -cne $(if($stage -ceq 'P'){'cho51_resolver_p_admission_v1'}else{'cho51_q_admission_v1'}) -or $request.stage -cne $stage -or $request.operation_id -cne $journal.operation -or $request.root -cne $projectRoot -or $request.scientific_admission -isnot [bool] -or $request.scientific_admission){throw 'bootstrap current stage authority'}
    AdmissionWindow $request.created_utc $request.expires_utc $originUtc
    $controls=@{}
    foreach($key in @('review','adoption')){
        $r=$request[$key];ClosedRecord $r @('path','bytes','sha256')
        $leaf=if($key -ceq 'review'){'source-review.json'}else{'contract-adoption.json'}
        $expected=if($stage -ceq 'P'){$phase.Replace('\','/')+'/'+$leaf}else{$leaf}
        $relative=if($stage -ceq 'P'){'runs/coordination/cho51_p3_probe_20261101_p3/'+$leaf}else{$leaf}
        if($r.path -cne $relative){throw 'bootstrap current review namespace'}
        $controls[$key]=ReadPinnedJson @{path=$phase.Replace('\','/')+'/'+$leaf;bytes=$r.bytes;sha256=$r.sha256}
    }
    $review=$controls.review;$adoption=$controls.adoption
    $status=if($stage -ceq 'P'){'ACCEPTED_SOURCE_LP1'}else{'ACCEPTED_SOURCE_LQ1'}
    if($review.status -cne $status -or $review.reviewer -isnot [string] -or $review.reviewer -cnotmatch '^[a-z][a-z0-9_-]{0,63}$' -or $review.authors -isnot [array] -or $review.authors.Count -lt 1 -or $review.authors -ccontains $review.reviewer -or $review.findings -isnot [array] -or $review.findings.Count -ne 0 -or $review.sources.Count -ne $request.sources.Count){throw 'bootstrap current independent source review'}
    foreach($row in $request.sources.GetEnumerator()){
        if(-not $review.sources.ContainsKey($row.Key) -or $review.sources[$row.Key].bytes -ne $row.Value.bytes -or $review.sources[$row.Key].sha256 -cne $row.Value.sha256){throw 'bootstrap current reviewed sources'}
    }
    $contract='docs/phase2/cho51_p3_probe_v3_contract_20261101.md'
    if($adoption.author -cne 'project_root' -or $adoption.status -cne ('ADOPTED_'+$stage+'_ONLY') -or $adoption.source_review_sha256 -cne $request.review.sha256 -or $adoption.supplement_sha256 -cne $request.sources[$contract].sha256 -or $adoption.bootstrap_qualification_sha256 -cne $request.bootstrap_qualification.sha256){throw 'bootstrap current scoped adoption'}
    if((UtcString $review.created_utc) -gt (UtcString $adoption.created_utc) -or (UtcString $adoption.created_utc) -gt (UtcString $request.created_utc)){throw 'bootstrap current review/adoption order'}
    foreach($key in @('historical_custody_closed','historical_operation_released','historical_retry_allowed','restart_qualified','boundary_qualified','complete_dependency_closure','launch_authorized','scientific_admission')){if($adoption[$key] -isnot [bool] -or $adoption[$key]){throw 'bootstrap current scope expansion'}}
    if($stage -ceq 'P'){
        # Both accepted Q cohorts are prerequisites even for the P native bootstrap.
        function EqualTree($a,$b){
            if($a -is [Collections.IDictionary]){
                if($b -isnot [Collections.IDictionary] -or $a.Count -ne $b.Count){return $false}
                foreach($k in $a.Keys){if(-not(@($b.Keys) -ccontains $k) -or -not(EqualTree $a[$k] $b[$k])){return $false}}
                return $true
            }
            if($a -is [array]){
                if($b -isnot [array] -or $a.Count -ne $b.Count){return $false}
                for($i=0;$i -lt $a.Count;$i++){if(-not(EqualTree $a[$i] $b[$i])){return $false}}
                return $true
            }
            if($null -eq $a){return ($null -eq $b)}
            if($a -is [bool]){return ($b -is [bool] -and $a -eq $b)}
            if($a -is [string]){return ($b -is [string] -and $a -ceq $b)}
            return ($b -isnot [bool] -and $a -eq $b)
        }
        $qPhase='runs/coordination/cho51_p3_probe_20261101_q3/'
        $ar=$request.qualification_aggregate
        ClosedRecord $ar @('path','bytes','sha256')
        if($ar.path -cne ($qPhase+'qualification-aggregate.json') -or $adoption.qualification_aggregate_sha256 -cne $ar.sha256){throw 'both Q aggregate adoption'}
        $aggregate=ReadPinnedJson @{path=$projectRoot+'/'+$ar.path;bytes=$ar.bytes;sha256=$ar.sha256}
        $refs=@('source_review','primary_qualification','primary_admission','primary_actual','secondary_qualification','secondary_admission','secondary_actual')
        ClosedRecord $aggregate (@('schema','status','author','created_utc','expected_counts','launch_authorized','scientific_admission')+$refs)
        if($aggregate.schema -cne 'cho51_resolver_q_aggregate_v1' -or $aggregate.status -cne 'ACCEPTED_BOTH_Q_COHORTS' -or $aggregate.author -cne 'project_root' -or -not(EqualTree $aggregate.expected_counts @{inherited=384;resolver=40})){throw 'both Q aggregate status/counts'}
        foreach($flag in @('launch_authorized','scientific_admission')){if($aggregate[$flag] -isnot [bool] -or $aggregate[$flag]){throw 'aggregate scope'}}
        $fixed=@{source_review='source-review.json';primary_qualification='root-qualification.json';primary_actual='actual-review.json';secondary_qualification='resolver-qualification.json';secondary_actual='resolver-actual-review.json'}
        $docs=@{}
        foreach($key in $refs){
            $r=$aggregate[$key];ClosedRecord $r @('path','bytes','sha256')
            if($fixed.ContainsKey($key)){if($r.path -cne ($qPhase+$fixed[$key])){throw 'aggregate fixed reference'}}
            elseif($r.path -cnotmatch ('^'+[regex]::Escape($qPhase)+'admission_[0-9a-f-]{36}\.json$')){throw 'aggregate admission namespace'}
            $docs[$key]=ReadPinnedJson @{path=$projectRoot+'/'+$r.path;bytes=$r.bytes;sha256=$r.sha256}
        }
        if(-not(EqualTree $aggregate.primary_qualification $request.qualification) -or -not(EqualTree $docs.source_review.sources $request.sources) -or $docs.source_review.status -cne 'ACCEPTED_SOURCE_LQ1'){throw 'aggregate primary/current source join'}
        $operations=@()
        foreach($cohortRole in @('primary','secondary')){
            $count=if($cohortRole -ceq 'primary'){384}else{40}
            $q=$docs[$cohortRole+'_qualification'];$a=$docs[$cohortRole+'_actual'];$qa=$docs[$cohortRole+'_admission']
            $operations+=,$q.operation_id
            if($q.status -cne 'QUALIFIED_LQ1_MECHANISMS_ONLY' -or $q.author -cne 'project_root' -or $a.status -cne 'ACCEPTED_LQ1_TESTED_SCOPE' -or $a.reviewer -ceq $docs.source_review.reviewer -or $a.authors -ccontains $a.reviewer -or $docs.source_review.authors -ccontains $a.reviewer -or $a.findings.Count -ne 0 -or $docs.source_review.findings.Count -ne 0){throw 'aggregate independent accepted reviews'}
            if($qa.operation_id -cne $q.operation_id -or $a.operation_id -cne $q.operation_id -or $qa.stage -cne 'Q' -or $qa.schema -cne 'cho51_q_admission_v1' -or $aggregate[$cohortRole+'_admission'].path -cne ($qPhase+'admission_'+$q.operation_id+'.json')){throw 'aggregate distinct admitted cohort'}
            if(-not(EqualTree $q.source_review $aggregate.source_review) -or -not(EqualTree $q.actual_review $aggregate[$cohortRole+'_actual']) -or -not(EqualTree $a.admission $aggregate[$cohortRole+'_admission']) -or $a.source_review_sha256 -cne $aggregate.source_review.sha256){throw 'aggregate review reference join'}
            foreach($field in @('sources','runtime','caller_runtime','python','root')){if(-not(EqualTree $qa[$field] $request[$field])){throw 'aggregate current source/runtime identity'}}
            $seen=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
            if($qa.expected_tests -isnot [array] -or $qa.expected_tests.Count -ne $count){throw 'aggregate complete cohort count'}
            foreach($name in $qa.expected_tests){if($name -isnot [string] -or -not $seen.Add($name) -or $name.StartsWith('tools.local_validation.lplan13.test_compiler.ResolverTests.',[StringComparison]::Ordinal) -ne ($cohortRole -ceq 'secondary')){throw 'aggregate cohort partition'}}
            $rosterBytes=[Text.Encoding]::UTF8.GetBytes((ConvertTo-Json -InputObject $qa.expected_tests -Compress -Depth 5))
            if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($rosterBytes)).ToLowerInvariant() -cne $a.test_roster_sha256 -or $q.test_count -ne $count -or $a.tests_run -ne $count -or $a.actual_tool_exit_code -ne 0){throw 'aggregate actual exact tests'}
            foreach($field in @('new_operation_owned_lifecycle_closed','final_input_verification')){if($a[$field] -isnot [bool] -or -not $a[$field]){throw 'aggregate verified cleanup'}}
            foreach($field in @('historical_custody_closed','historical_operation_released','historical_retry_allowed','restart_qualified','boundary_qualified','complete_dependency_closure','launch_authorized','scientific_admission')){if($q[$field] -isnot [bool] -or $q[$field] -or $a[$field] -isnot [bool] -or $a[$field]){throw 'aggregate no authority expansion'}}
            if($q.timestamp_controls -ne 8 -or $q.native_fault_controls -ne 2 -or $a.timestamp_controls_passed -ne 8 -or $a.native_fault_controls_passed -ne 2){throw 'aggregate all controls'}
            foreach($field in @('native_helper','native_builder_controls','api_mapping','api_mapping_native_identity','native_diagnostic','native_diagnostic_native_identity','artifact_handoff','sharing_controls','l_native_bundle','l_native_bundle_identity','l_native_cases','bootstrap_controls')){if(-not(EqualTree $q[$field] $a[$field])){throw 'aggregate native actual join'}}
            if((UtcString $docs.source_review.created_utc) -gt (UtcString $qa.created_utc) -or (UtcString $qa.created_utc) -gt (UtcString $a.created_utc) -or (UtcString $a.created_utc) -gt (UtcString $q.created_utc) -or (UtcString $q.created_utc) -gt (UtcString $aggregate.created_utc) -or (UtcString $aggregate.created_utc) -gt (UtcString $request.created_utc)){throw 'aggregate authority order'}
        }
        if($operations[0] -ceq $operations[1]){throw 'aggregate repeated operation'}
        foreach($field in @('compiler','native_compiler')){if(-not(EqualTree $docs.primary_admission[$field] $docs.secondary_admission[$field])){throw 'aggregate compiler roles'}}
    }
    $relative='tools/local_validation/lp16/native_bootstrap.ps1';$modulePin=$request.sources[$relative]
    $rawRef=@{path=$projectRoot+'/'+$relative;bytes=$modulePin.bytes;sha256=$modulePin.sha256}
    $pinned=PinBytes $rawRef.path
    if($pinned.bytes -ne $rawRef.bytes -or $pinned.sha256 -cne $rawRef.sha256 -or $pinned.bytes -gt 1MB){throw 'shared bootstrap exact reviewed module'}
    $stream=$inputs[$inputs.Count-1];$reader=[IO.StreamReader]::new($stream,[Text.UTF8Encoding]::new($false,$true),$false,65536,$true)
    try{$source=$reader.ReadToEnd()}finally{$reader.Dispose();$stream.Position=0}
    # The current independent review and Root adoption were checked before this
    # execution. Source strings are never accepted solely on an admission pin.
    . ([scriptblock]::Create($source))
    if($Role -cne $stage){throw 'bootstrap role drift before native initialization'}
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
    if($bootstrapPhase){if((Elapsed) -ge 5 -or [DateTime]::UtcNow -ge $originUtc.AddSeconds(5)){throw 'bootstrap original five-second deadline'};$callerProcess.Refresh();if($callerProcess.PrivateMemorySize64 -gt 512MB -or [IO.DriveInfo]::new('D').AvailableFreeSpace -lt 20GB){throw 'bootstrap private/disk limits'};$directory=[IO.FileInfo]::new($stopPath).Directory;while($null -ne $directory){$attr=[IO.File]::GetAttributes($directory.FullName);if(($attr -band [IO.FileAttributes]::ReparsePoint) -or -not ($attr -band [IO.FileAttributes]::Directory)){throw 'bootstrap stop ancestry'};$directory=$directory.Parent};try{[void][IO.File]::GetAttributes($stopPath);throw 'bootstrap stop present'}catch [IO.FileNotFoundException]{};return}

    if((Elapsed) -ge 60 -or [DateTime]::UtcNow -ge $originUtc.AddSeconds(60)){throw 'original Q work deadline'}
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
function ReserveCallerOutput([string]$path,[long]$cap) {
    $full=[IO.Path]::GetFullPath($path).Replace('\','/')
    $base=[IO.Path]::GetFullPath($phase).Replace('\','/')+'/'
    if(-not $full.StartsWith($base,[StringComparison]::Ordinal) -or $cap -lt 1 -or $cap -gt 1MB -or $callerOutputReservations.ContainsKey($full) -or $callerOutputReservations.Count -ge 40 -or $script:callerOutputReservedBytes+$cap -gt 20MB){throw 'reserved caller output allocation'}
    $callerOutputReservations.Add($full,$cap);$script:callerOutputReservedBytes+=$cap
}
function NewOutput($name) {
    if($name -notmatch '^(claim|origin|caller-return|timestamp-controls|native-build|api-mapping|native-diagnostic)_[0-9a-f-]{36}\.json$'){throw 'output name'}
    ReserveCallerOutput (Join-Path $phase $name) 1MB
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
function PublishNativeRecord($name,$value) {
    Check;$stream=NewOutput $name;$identity=[PNative3.Owner]::FileIdentity($stream.SafeFileHandle)
    $value.artifact_native_identity=$identity
    $raw=[Text.Encoding]::UTF8.GetBytes(($value|ConvertTo-Json -Depth 24 -Compress)+[Environment]::NewLine)
    if($raw.Length -gt 1MB){throw 'native diagnostic/mapping cap'}
    $offset=0;while($offset -lt $raw.Length){Check;$count=[Math]::Min(65536,$raw.Length-$offset);$stream.Write($raw,$offset,$count);$offset+=$count}
    $stream.Flush($true);$stream.Position=0;$copy=[byte[]]::new($raw.Length);$offset=0
    while($offset -lt $copy.Length){Check;$n=$stream.Read($copy,$offset,[Math]::Min(65536,$copy.Length-$offset));if($n -le 0){throw 'native record original readback'};$offset+=$n}
    $sha=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($raw)).ToLowerInvariant()
    if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($copy)).ToLowerInvariant() -cne $sha -or [PNative3.Owner]::FileIdentity($stream.SafeFileHandle) -cne $identity){throw 'native record original identity'}
    $stream.Position=0
    return @{reference=@{path='runs/coordination/cho51_p3_probe_20261101_q3/'+$name;bytes=$raw.Length;sha256=$sha};native_identity=$identity;stream=$stream}
}
function VerifyCallerArtifacts {
    foreach($item in $callerArtifacts){
        Check;$stream=$item.stream
        if($stream.SafeFileHandle.IsClosed -or [PNative3.Owner]::FileIdentity($stream.SafeFileHandle) -cne $item.native_identity -or $stream.Length -ne $item.reference.bytes){throw 'caller artifact original identity/length'}
        $stream.Position=0;$hash=[Security.Cryptography.IncrementalHash]::CreateHash([Security.Cryptography.HashAlgorithmName]::SHA256)
        try{$buffer=[byte[]]::new(65536);$count=0L;do{Check;$n=$stream.Read($buffer,0,$buffer.Length);if($n){$count+=$n;if($count -gt $item.reference.bytes){throw 'caller artifact original grew'};$hash.AppendData($buffer,0,$n)}}while($n)
            $sha=[Convert]::ToHexString($hash.GetHashAndReset()).ToLowerInvariant()
        }finally{$hash.Dispose();$stream.Position=0}
        if($count -ne $item.reference.bytes -or $sha -cne $item.reference.sha256 -or [PNative3.Owner]::FileIdentity($stream.SafeFileHandle) -cne $item.native_identity){throw 'caller artifact final original byte/native identity'}
    }
}
function UtcString($value) {
    if($value -isnot [string] -or $value.Length -gt 64 -or $value -cnotmatch '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,7})?(Z|\+00:00)$'){throw 'explicit UTC string required'}
    $parsed=[DateTimeOffset]::Parse($value,[Globalization.CultureInfo]::InvariantCulture,[Globalization.DateTimeStyles]::None)
    if($parsed.Offset -ne [TimeSpan]::Zero){throw 'explicit UTC string required'}
    return $parsed.UtcDateTime
}
function AdmissionWindow($created,$expires,[DateTime]$original) {
    $start=UtcString $created;$end=UtcString $expires
    if($original.Kind -ne [DateTimeKind]::Utc -or $start -gt $original -or $end -lt $original.AddSeconds(90) -or ($end-$start).TotalSeconds -lt 90 -or ($end-$start).TotalSeconds -gt 900){throw 'original caller window'}
}
function ExpectedRefusal([scriptblock]$body,[string]$message) {
    try{& $body|Out-Null}catch{if($_.Exception.Message.Contains($message)){return $true};throw}
    throw 'timestamp control did not refuse'
}
function TimestampControls {
    Check
    $literal='2026-10-29T09:00:00.1234567Z'
    $parsed=('{"utc":"'+$literal+'"}'|ConvertFrom-Json -AsHashtable -DateKind String).utc
    if($parsed -isnot [string] -or $parsed -cne $literal -or (UtcString $parsed).ToString('o') -cne $literal){throw 'UTC literal/fraction control'}
    $original=[DateTime]::SpecifyKind([DateTime]::new(2026,10,29,9,0,0),[DateTimeKind]::Utc)
    AdmissionWindow '2026-10-29T09:00:00Z' '2026-10-29T09:01:30Z' $original
    $short=ExpectedRefusal {AdmissionWindow '2026-10-29T09:00:00Z' '2026-10-29T09:01:29Z' $original} 'original caller window'
    $nonUtc=ExpectedRefusal {UtcString '2026-10-29T12:00:00+03:00'} 'explicit UTC string required'
    $coerced=ExpectedRefusal {UtcString $original} 'explicit UTC string required'
    $expired=ExpectedRefusal {AdmissionWindow '2026-10-29T08:59:00Z' '2026-10-29T09:00:30Z' $original.AddMinutes(1)} 'original caller window'
    $future=ExpectedRefusal {AdmissionWindow '2026-10-29T09:00:01Z' '2026-10-29T09:01:31Z' $original} 'original caller window'
    $previousCulture=[Threading.Thread]::CurrentThread.CurrentCulture
    $culture=$false
    try {
        [Threading.Thread]::CurrentThread.CurrentCulture=[Globalization.CultureInfo]::GetCultureInfo('ar-SA')
        if((UtcString $literal).Ticks -ne $original.Ticks+1234567){throw 'changed-culture UTC control'}
        AdmissionWindow '2026-10-29T09:00:00Z' '2026-10-29T09:01:30Z' $original
        $culture=$true
    } finally {[Threading.Thread]::CurrentThread.CurrentCulture=$previousCulture}
    Check
    return @{json_utc_literal_exact=$true;exact_90_second_window=$true;short_89_second_window_refused=$short;non_utc_refused=$nonUtc;datetime_object_refused=$coerced;expired_window_refused=$expired;future_creation_refused=$future;changed_culture_utc_exact=$culture}
}
try {
    if($PSVersionTable.PSVersion.Major -lt 7){throw 'PowerShell7 required'}
    if([IO.Path]::GetDirectoryName([IO.Path]::GetFullPath($Admission)) -ne [IO.Path]::GetFullPath($phase)){throw 'bootstrap admission namespace'}
    $stem=[IO.Path]::GetFileNameWithoutExtension($Admission)
    if($stem -cnotmatch '^admission_([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$'){throw 'bootstrap canonical operation'}
    $journal.operation=$Matches[1];$journal.caller_pid=$callerProcess.Id;$journal.creation_filetime=$callerProcess.StartTime.ToUniversalTime().ToFileTimeUtc()
    ReserveCallerOutput (Join-Path $phase ('bootstrap_'+$journal.operation+'.jsonl')) 65536
    $journal.stream=[IO.FileStream]::new((Join-Path $phase ('bootstrap_'+$journal.operation+'.jsonl')),[IO.FileMode]::CreateNew,[IO.FileAccess]::ReadWrite,[IO.FileShare]::Read)
    Journal $journal 'caller_entry'
    $bootstrapOwner=LoadReviewedNativeBootstrap 'Q';
    Journal $journal 'runspace_create'
    $guardRunspace=[Management.Automation.Runspaces.RunspaceFactory]::CreateRunspace()
    $guardRunspace.Open()
    $guardPowerShell=[Management.Automation.PowerShell]::Create()
    $guardPowerShell.Runspace=$guardRunspace
    [void]$guardPowerShell.AddScript($NativeBootstrapGuardScript).AddArgument($callerProcess).AddArgument($killAction).AddArgument($originQpc).AddArgument($originUtc).AddArgument($frequency).AddArgument($stopPath).AddArgument($guardState).AddArgument($journal).AddArgument($faultDeadline).AddArgument($bootstrapOwner).AddArgument(60).AddArgument(512MB)
    Journal $journal 'runspace_begin'
    $guardInvocation=$guardPowerShell.BeginInvoke()
    while(-not $guardState.ready){
        if($guardState.done -or $guardInvocation.IsCompleted -or $null -ne $guardState.error -or (Elapsed) -ge 5){$faultDeadline.CancelAfter(50);try{Journal $journal 'startup_refused' ('stage='+$guardState.stage+'; ready='+$guardState.ready+'; samples='+$guardState.samples+'; error='+$guardState.error)}finally{$killAction.Invoke()};throw 'independent guard startup refused'}
        [Threading.Thread]::Sleep(20)
    }
    if((Elapsed) -ge 5 -or $startupDeadline.IsCancellationRequested -or $guardState.second_sample.elapsed_seconds -ge 5){$killAction.Invoke();throw 'late startup readiness'}
    $startupDeadline.CancelAfter([Threading.Timeout]::Infinite)
    $startupRegistration.Dispose();$startupDeadline.Dispose()
    $startupDisarmed=$true;$bootstrapPhase=$false
    $samples=@($guardState.first_sample,$guardState.second_sample)
    Journal $journal 'startup_ready'
    $initialPrivate=$samples[0].caller_private_bytes
    if(($samples[1].qpc-$samples[0].qpc)/$frequency -lt 0.2){throw 'independent startup sample spacing'}
    Check
    if([IO.Path]::GetDirectoryName([IO.Path]::GetFullPath($Admission)) -ne [IO.Path]::GetFullPath($phase)){throw 'admission location'}
    $pin=PinBytes $Admission
    if($pin.sha256 -cne $AdmissionSha256 -or $pin.bytes -gt 8MB){throw 'admission caller hash'}
    $request=[IO.File]::ReadAllText($Admission)|ConvertFrom-Json -AsHashtable -DateKind String;$operation=$request.operation_id
    if($operation -notmatch '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' -or $request.schema -cne 'cho51_q_admission_v1' -or $request.stage -cne 'Q' -or $request.root -cne $projectRoot){throw 'Q request identity'}
    $resolverPrefix='tools.local_validation.lplan13.test_compiler.ResolverTests.'
    $resolverCount=@($request.expected_tests|Where-Object {$_ -is [string] -and $_.StartsWith($resolverPrefix,[StringComparison]::Ordinal)}).Count
    $frontierPrefix='tools.local_validation.lplan13.test_compiler.FrontierTests.'
    $frontierCount=@($request.expected_tests|Where-Object {$_ -is [string] -and $_.StartsWith($frontierPrefix,[StringComparison]::Ordinal)}).Count
    $losslessPrefix='tools.local_validation.lplan13.test_compiler.LosslessTests.'
    $losslessCount=@($request.expected_tests|Where-Object {$_ -is [string] -and $_.StartsWith($losslessPrefix,[StringComparison]::Ordinal)}).Count
    $probePrefix='tools.local_validation.lplan13.test_compiler.SourceProbeTests.'
    $probeCount=@($request.expected_tests|Where-Object {$_ -is [string] -and $_.StartsWith($probePrefix,[StringComparison]::Ordinal)}).Count
    if(-not (($request.expected_tests.Count -eq 384 -and $resolverCount -eq 0 -and $frontierCount -eq 0 -and $losslessCount -eq 0 -and $probeCount -eq 0) -or ($request.expected_tests.Count -eq 100 -and $resolverCount -eq 40 -and $frontierCount -eq 32 -and $losslessCount -eq 28 -and $probeCount -eq 0) -or ($request.expected_tests.Count -eq 32 -and $resolverCount -eq 0 -and $frontierCount -eq 0 -and $losslessCount -eq 0 -and $probeCount -eq 32))){throw 'Q exact inherited384/combined100/probe32 cohort'}
    $windowOperands=@{created_literal=$request.created_utc;expires_literal=$request.expires_utc;created_utc=(UtcString $request.created_utc).ToString('o');expires_utc=(UtcString $request.expires_utc).ToString('o');original_utc=$originUtc.ToString('o');original_deadline_utc=$originUtc.AddSeconds(90).ToString('o')}
    Journal $journal 'window_operands' ($windowOperands|ConvertTo-Json -Compress)
    AdmissionWindow $request.created_utc $request.expires_utc $originUtc
    [Threading.Monitor]::Enter($guardState.SyncRoot)
    try{$callerPath=$callerProcess.MainModule.FileName.Replace('\','/')}finally{[Threading.Monitor]::Exit($guardState.SyncRoot)}
    if($initialPrivate -gt 512MB -or $callerPath -cne $request.caller_runtime.path -or $PSVersionTable.PSVersion.ToString() -cne $request.caller_runtime.version){throw 'caller runtime/initial memory'}
    $a=PinBytes $callerPath
    if($a.bytes -ne $request.caller_runtime.bytes -or $a.sha256 -cne $request.caller_runtime.sha256){throw 'caller executable pin'}
    foreach($row in $request.sources.GetEnumerator()){
        if($row.Key -match '(^/|\\|:|\.\.)'){throw 'source path'}
        $a=PinBytes (Join-Path $projectRoot $row.Key)
        if($a.bytes -ne $row.Value.bytes -or $a.sha256 -cne $row.Value.sha256){throw ('source changed: '+$row.Key)}
    }
    foreach($key in @('review','adoption')){
        $ref=$request[$key];$expected=if($key -eq 'review'){'source-review.json'}else{'contract-adoption.json'}
        if($ref.path -cne $expected){throw 'review path'}
        $a=PinBytes (Join-Path $phase $ref.path)
        if($a.bytes -ne $ref.bytes -or $a.sha256 -cne $ref.sha256){throw 'review/adoption pin'}
    }
    $review=[IO.File]::ReadAllText((Join-Path $phase 'source-review.json'))|ConvertFrom-Json -AsHashtable -DateKind String
    $adoption=[IO.File]::ReadAllText((Join-Path $phase 'contract-adoption.json'))|ConvertFrom-Json -AsHashtable -DateKind String
    if($review.status -cne 'ACCEPTED_SOURCE_LQ1' -or $review.authors -contains $review.reviewer -or $adoption.status -cne 'ADOPTED_Q_ONLY' -or $adoption.source_review_sha256 -cne $request.review.sha256 -or $review.sources.Count -ne $request.sources.Count){throw 'independent review/adoption'}
    foreach($row in $request.sources.GetEnumerator()){
        if(-not $review.sources.ContainsKey($row.Key) -or $review.sources[$row.Key].bytes -ne $row.Value.bytes -or $review.sources[$row.Key].sha256 -cne $row.Value.sha256){throw 'reviewed source mismatch'}
    }
    if($adoption.contract_sha256 -cne $request.sources['docs/phase2/cho51_p3_local_validation_contract_20261029.md'].sha256 -or $adoption.design_review_sha256 -cne $request.sources['runs/coordination/cho51_p3_local_validation_design_20261029_v1/design-review.json'].sha256 -or [DateTimeOffset]::Parse($adoption.created_utc) -gt [DateTimeOffset]::Parse($request.created_utc)){throw 'adoption joins/order'}
    if($adoption.schema -cne 'cho51_q_contract_adoption_v2' -or $adoption.supplement_sha256 -cne $request.sources['docs/phase2/cho51_p3_probe_v3_contract_20261101.md'].sha256){throw 'LQ1 supplement adoption'}
    foreach($key in @('historical_custody_closed','historical_operation_released','historical_retry_allowed','restart_qualified','boundary_qualified','complete_dependency_closure','launch_authorized','scientific_admission')){
        if($adoption[$key] -isnot [bool] -or $adoption[$key]){throw 'adoption authority'}
    }
    $journal.authority_pending=$false;Journal $journal 'authority_verified'
    # Admitted Q effect: compile exact verified C# bytes in memory through the
    # pinned PowerShell/.NET compiler. No OutputAssembly or compiler subprocess.
    WriteRecord ('claim_'+$operation+'.json') @{schema='cho51_q_external_claim_v1';operation_id=$operation;admission_sha256=$AdmissionSha256;origin_utc=$originUtc.ToString('o');origin_qpc=$originQpc;frequency=$frequency}
    $claimCreated=$true
    $timestampControls=TimestampControls
    if($timestampControls.Count -ne 8 -or @($timestampControls.Values|Where-Object {$_ -isnot [bool] -or -not $_}).Count -ne 0){throw 'timestamp control outcomes'}
    WriteRecord ('timestamp-controls_'+$operation+'.json') @{schema='cho51_q_timestamp_controls_v1';operation_id=$operation;controls=$timestampControls;culture_exercised='ar-SA';actual_window_operands=$windowOperands;historical_custody_closed=$false;historical_operation_released=$false;historical_retry_allowed=$false;restart_qualified=$false;boundary_qualified=$false;complete_dependency_closure=$false;launch_authorized=$false;scientific_admission=$false}
    $helper=[IO.File]::ReadAllBytes((Join-Path $projectRoot 'tools/local_validation/lq16/caller_native.cs'))
    if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($helper)).ToLowerInvariant() -cne $request.sources['tools/local_validation/lq16/caller_native.cs'].sha256){throw 'helper same-byte pin'}
    Check

    foreach($row in $request.compiler.files.GetEnumerator()){
        $a=PinBytes $row.Key
        if($a.bytes -ne $row.Value.bytes -or $a.sha256 -cne $row.Value.sha256){throw 'compiler pin'}
    }
    $expectedCompiler=@(Get-ChildItem -LiteralPath (Join-Path $PSHOME 'ref') -File -Filter '*.dll'|ForEach-Object {$_.FullName.Replace('\','/')})+@(($PSHOME.Replace('\','/')+'/Microsoft.CodeAnalysis.dll'),($PSHOME.Replace('\','/')+'/Microsoft.CodeAnalysis.CSharp.dll'))
    if($request.compiler.root -cne $PSHOME.Replace('\','/') -or @($expectedCompiler|Where-Object {-not $request.compiler.files.ContainsKey($_)}).Count -ne 0 -or $expectedCompiler.Count -ne $request.compiler.files.Count){throw 'exact compiler recipe'}

    Journal $journal 'compiler_begin'
    Add-Type -TypeDefinition ([Text.Encoding]::UTF8.GetString($helper)) -Language CSharp -ErrorAction Stop
    Check
    Journal $journal 'compiler_return'

    $builderPath=Join-Path $projectRoot 'tools/local_validation/lp16/build_native.ps1'
    $builderBytes=[IO.File]::ReadAllBytes($builderPath)
    if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($builderBytes)).ToLowerInvariant() -cne $request.sources['tools/local_validation/lp16/build_native.ps1'].sha256){throw 'builder same-byte pin'}
    . ([scriptblock]::Create([Text.Encoding]::UTF8.GetString($builderBytes)))
    $pSource=[IO.File]::ReadAllBytes((Join-Path $projectRoot 'tools/local_validation/lp16/caller_native.cs'))
    if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($pSource)).ToLowerInvariant() -cne $request.sources['tools/local_validation/lp16/caller_native.cs'].sha256){throw 'P helper same-byte pin'}
    $pe=Build-PNative $pSource $request.compiler {Check}
    Check
    $pePath=Join-Path $phase ('native-helper_'+$operation+'.dll')
    ReserveCallerOutput $pePath 1MB
    $peStream=[IO.FileStream]::new($pePath,[IO.FileMode]::CreateNew,[IO.FileAccess]::ReadWrite,[IO.FileShare]::Read)
    $outputs.Add($peStream);$peStream.Write($pe,0,$pe.Length);$peStream.Flush($true);$peStream.Position=0
    $peCopy=[byte[]]::new($pe.Length);$offset=0
    while($offset -lt $peCopy.Length){Check;$n=$peStream.Read($peCopy,$offset,$peCopy.Length-$offset);if($n -le 0){throw 'PE same-handle readback'};$offset+=$n}
    $peSha=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($pe)).ToLowerInvariant()
    if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($peCopy)).ToLowerInvariant() -cne $peSha){throw 'PE digest readback'}
    [void][Reflection.Assembly]::Load($peCopy)
    $peIdentity=[PNative3.Owner]::FileIdentity($peStream.SafeFileHandle)
    $probe=$null
    try{$probe=[PNative3.Owner]::new($originQpc,$originUtc.ToString('o'),$stopPath);if(-not $probe.LimitsVerified){throw 'P native limits query'}}
    finally{if($null -ne $probe){$probe.Dispose()}}
    if(-not($probe.JobEmpty -and $probe.JobClosed -and $probe.WatchdogJoined) -or $null -ne $probe.CleanupError -or $null -ne $probe.Fault){throw 'P empty Job probe closure'}
    if($probe.ActiveProcessLimit -ne 1){throw 'P one-process custody query'}
    $lProbe=$null
    try{$lProbe=[PNative3.Owner]::new($originQpc,$originUtc.ToString('o'),$stopPath,[uint32]2);if(-not $lProbe.LimitsVerified -or $lProbe.ActiveProcessLimit -ne 2){throw 'L two-process limits query'}}
    finally{if($null -ne $lProbe){$lProbe.Dispose()}}
    if(-not($lProbe.JobEmpty -and $lProbe.JobClosed -and $lProbe.WatchdogJoined) -or $null -ne $lProbe.CleanupError -or $null -ne $lProbe.Fault){throw 'L empty Job probe closure'}
    $invalidProcessCount=ExpectedRefusal {$unexpected=$null;try{$unexpected=[PNative3.Owner]::new($originQpc,$originUtc.ToString('o'),$stopPath,[uint32]3)}finally{if($null -ne $unexpected){$unexpected.Dispose()}}} 'only P one-process or L two-process custody allowed'
    $nativeArtifact=@{path='runs/coordination/cho51_p3_probe_20261101_q3/native-helper_'+$operation+'.dll';bytes=$pe.Length;sha256=$peSha}
    $callerArtifacts.Add(@{role='helper';reference=$nativeArtifact;native_identity=$peIdentity;stream=$peStream})
    $builderControls=@{emitted_pe_verified=$true;original_output_identity_retained=$true;loaded_same_pe_bytes=$true;p_limits_query_verified=$true;empty_job_closed=$true;l_two_process_limits_query_verified=$true;l_empty_job_closed=$true;l_invalid_process_count_refused=$invalidProcessCount;helper_identity=$peIdentity}
    WriteRecord ('native-build_'+$operation+'.json') @{schema='cho51_p2_native_build_v1';operation_id=$operation;native_helper=$nativeArtifact;controls=$builderControls;source_sha256=$request.sources['tools/local_validation/lp16/caller_native.cs'].sha256;compiler=$request.compiler;launch_authorized=$false;scientific_admission=$false}
    Journal $journal 'native_builder_return'

    # Exact Q-only running-schema query; no returned target host is loaded.
    Check
    $planRelative='tools/local_validation/lp16/api_query_plan.json'
    $planBytes=[IO.File]::ReadAllBytes((Join-Path $projectRoot $planRelative))
    if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($planBytes)).ToLowerInvariant() -cne $request.sources[$planRelative].sha256){throw 'API query plan pin'}
    $queryPlan=[Text.Encoding]::UTF8.GetString($planBytes)|ConvertFrom-Json -AsHashtable -DateKind String
    if($queryPlan.schema -cne 'cho51_p9_resident_reference_plan_v1' -or $queryPlan.exact_query_names.Count -ne 14 -or $queryPlan.baseline_modules.Count -ne 3 -or $adoption.query_plan_sha256 -cne $request.sources[$planRelative].sha256){throw 'resident reference scope/adoption'}
    $observedOs=[Environment]::OSVersion.Version.ToString(3)
    if($observedOs -cne $queryPlan.os_version){throw 'running OS identity differs'}
    $platformInputs=[Collections.Generic.List[object]]::new()
    foreach($file in $queryPlan.files){
        Check
        if($file.path -cnotmatch '^C:/Windows/System32/(apisetschema|kernelbase|kernel32|ntdll|cabinet|fontsub|mswsock)\.dll$'){throw 'query OS pin scope'}
        $pin=PinBytes $file.path
        if($pin.bytes -ne $file.bytes -or $pin.sha256 -cne $file.sha256 -or [Diagnostics.FileVersionInfo]::GetVersionInfo($file.path).FileVersion -cne $file.file_version){throw 'query OS/schema bytes/version'}
        $platformInputs.Add(@{path=$file.path;stream=$inputs[$inputs.Count-1];identity=([PNative3.Owner]::FileIdentity($inputs[$inputs.Count-1].SafeFileHandle));pin=$pin})
    }
    Check
    $queryObserved=[QNative.ResidentContracts]::Run([string[]]$queryPlan.exact_query_names,$queryPlan.negative_query)
    Check
    # Run returns only after finally. Persist BOTH success and failure before
    # refusing a negative observation; no source-inferred release claim.
    $diagnosticRecord=@{schema='cho51_q9_native_diagnostic_v1';operation_id=$operation;plan_sha256=$request.sources[$planRelative].sha256;native_helper=$nativeArtifact;native_helper_native_identity=$peIdentity;os_version=$observedOs;platform_files=$queryPlan.files;observation=$queryObserved;target_modules_loaded=$false;loader_qualified=$false;scientific_admission=$false}
    $publishedDiagnostic=PublishNativeRecord ('native-diagnostic_'+$operation+'.json') $diagnosticRecord
    $nativeDiagnostic=$publishedDiagnostic.reference;$diagnosticIdentity=$publishedDiagnostic.native_identity
    $callerArtifacts.Add(@{role='diagnostic';reference=$nativeDiagnostic;native_identity=$diagnosticIdentity;stream=$publishedDiagnostic.stream})
    if(-not $queryObserved.success){throw ('resident reference observation refused: '+$queryObserved.exception_type+': '+$queryObserved.exception_message)}
    foreach($item in $platformInputs){
        if([PNative3.Owner]::FileIdentity($item.stream.SafeFileHandle) -cne $item.identity){throw 'query original OS identity changed'}
        $item.stream.Position=0
        $hash=[Security.Cryptography.IncrementalHash]::CreateHash([Security.Cryptography.HashAlgorithmName]::SHA256)
        try{
            $buffer=[byte[]]::new(65536);$count=0L
            do{Check;$n=$item.stream.Read($buffer,0,$buffer.Length);if($n){$count+=$n;if($count -gt $item.pin.bytes){throw 'query OS original stream grew'};$hash.AppendData($buffer,0,$n)}}while($n)
            if($count -ne $item.pin.bytes){throw 'query OS original stream length'}
            $digest=[Convert]::ToHexString($hash.GetHashAndReset()).ToLowerInvariant()
        }finally{$hash.Dispose();$item.stream.Position=0}
        Check;if($digest -cne $item.pin.sha256){throw 'query OS original bytes changed'}
    }
    $apiRecord=@{schema='cho51_q9_api_mapping_v1';operation_id=$operation;plan_sha256=$request.sources[$planRelative].sha256;native_helper=$nativeArtifact;native_helper_native_identity=$peIdentity;os_version=$observedOs;platform_files=$queryPlan.files;observation=$queryObserved;native_diagnostic=$nativeDiagnostic;native_diagnostic_native_identity=$diagnosticIdentity;target_modules_loaded=$false;loader_qualified=$false;scientific_admission=$false}
    $publishedMapping=PublishNativeRecord ('api-mapping_'+$operation+'.json') $apiRecord
    $apiMapping=$publishedMapping.reference;$apiIdentity=$publishedMapping.native_identity;$apiSha=$apiMapping.sha256
    $callerArtifacts.Add(@{role='mapping';reference=$apiMapping;native_identity=$apiIdentity;stream=$publishedMapping.stream})

    $lBuilderPath=Join-Path $projectRoot 'tools/local_validation/lq16/build_l_native.ps1'
    $lBuilderBytes=[IO.File]::ReadAllBytes($lBuilderPath)
    if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($lBuilderBytes)).ToLowerInvariant() -cne $request.sources['tools/local_validation/lq16/build_l_native.ps1'].sha256){throw 'L native builder pin'}
    . ([scriptblock]::Create([Text.Encoding]::UTF8.GetString($lBuilderBytes)))
    $lBundle=BuildLNative
    # Both controls keep the original Q clock and precede the main supervisor.
    $controlPath=$projectRoot+'/tools/local_validation/lq16/bootstrap_controls.ps1'
    $controlPin=PinBytes $controlPath
    if($controlPin.bytes -ne $request.sources['tools/local_validation/lq16/bootstrap_controls.ps1'].bytes -or $controlPin.sha256 -cne $request.sources['tools/local_validation/lq16/bootstrap_controls.ps1'].sha256){throw 'bootstrap controls reviewed source pin'}
    $controlStream=$inputs[$inputs.Count-1];$controlReader=[IO.StreamReader]::new($controlStream,[Text.UTF8Encoding]::new($false,$true),$false,65536,$true)
    try{$controlText=$controlReader.ReadToEnd()}finally{$controlReader.Dispose();$controlStream.Position=0}
    . ([scriptblock]::Create($controlText))
    $bootstrapControls=RunBootstrapControls
    $owner=[QNative.Owner]::new($originQpc,$originUtc.ToString('o'),$stopPath)
    foreach($row in $request.runtime.files.GetEnumerator()){
        if(-not $row.Key.StartsWith($request.runtime.root+'/',[StringComparison]::Ordinal)){throw 'runtime scope'}
        $a=PinBytes $row.Key
        if($a.bytes -ne $row.Value.bytes -or $a.sha256 -cne $row.Value.sha256){throw ('runtime changed: '+$row.Key)}
    }
    $attempt=Join-Path $phase ('attempts/'+$operation);$cache=[IO.Path]::GetFullPath((Join-Path $phase ('disabled-bytecode/'+$operation)))
    foreach($path in @($attempt,$cache)){if(Test-Path -LiteralPath $path){throw 'occupied attempt/cache'}}
    foreach($name in @('python312.zip','python._pth','python312._pth','pyvenv.cfg')){if(Test-Path -LiteralPath (Join-Path $request.runtime.root $name)){throw 'unlisted startup configuration/archive'}}
    if(Test-Path -LiteralPath (Join-Path (Split-Path $request.runtime.root) 'pyvenv.cfg')){throw 'parent venv configuration'}
    WriteRecord ('origin_'+$operation+'.json') @{schema='cho51_q_caller_origin_v1';operation_id=$operation;origin_utc=$originUtc.ToString('o');origin_qpc=$originQpc;frequency=$frequency;startup_samples=$samples;initial_caller_private_bytes=$initialPrivate;caller_version=$PSVersionTable.PSVersion.ToString();caller_pid=$PID}
    foreach($key in @('PYTHONPATH','PYTHONHOME','PYTHONSTARTUP','PYTHONUSERBASE')){[Environment]::SetEnvironmentVariable($key,$null,'Process')}
    foreach($key in @('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS')){[Environment]::SetEnvironmentVariable($key,'1','Process')}
    [Environment]::SetEnvironmentVariable('CUDA_VISIBLE_DEVICES','-1','Process')
    $bootstrap=@'
import hashlib,sys
p=sys.argv[1]
with open(p,'rb') as f: b=f.read(1048577)
if len(b)>1048576 or hashlib.sha256(b).hexdigest()!=sys.argv[2]: raise ValueError('supervisor byte pin')
g={'__name__':'q_supervisor','__file__':p}
exec(compile(b,p,'exec'),g)
raise SystemExit(g['main'](*sys.argv[3:]))
'@
    $command=@('-I','-S','-B','-X',('pycache_prefix='+$cache),'-c',$bootstrap,(Join-Path $projectRoot 'tools/local_validation/lq16/supervisor.py'),$request.sources['tools/local_validation/lq16/supervisor.py'].sha256,$Admission,$AdmissionSha256,$originUtc.ToString('o'),$originQpc.ToString(),$frequency.ToString(),$apiSha,$apiIdentity,$apiMapping.bytes.ToString(),$lBundle.reference.sha256,$lBundle.native_identity,$lBundle.reference.bytes.ToString())
    Check;if((Elapsed) -ge 45){throw 'insufficient remaining work'}
    Journal $journal 'supervisor_dispatch'
    $owner.Start($request.python,[string[]]$command,$projectRoot)
    while(-not $owner.Poll()){Start-Sleep -Milliseconds 50}
    $supervisorExit=$owner.ExitCode()
    $owner.Dispose()
    $outText=$owner.StdoutText();$errText=$owner.StderrText()
    if($supervisorExit -ne 0){throw 'supervisor exit refused'}
    $ret=$outText|ConvertFrom-Json -AsHashtable -DateKind String
    if($ret.api_mapping.path -cne $apiMapping.path -or $ret.api_mapping.bytes -ne $apiMapping.bytes -or $ret.api_mapping.sha256 -cne $apiMapping.sha256 -or $ret.api_mapping_native_identity -cne $apiIdentity){throw 'Q accepted mapping original receipt join'}
    if($ret.native_diagnostic.path -cne $nativeDiagnostic.path -or $ret.native_diagnostic.bytes -ne $nativeDiagnostic.bytes -or $ret.native_diagnostic.sha256 -cne $nativeDiagnostic.sha256 -or $ret.native_diagnostic_native_identity -cne $diagnosticIdentity){throw 'Q accepted diagnostic original receipt join'}
    if($ret.caller_artifact_capabilities.Count -ne 3){throw 'three returned caller artifact capabilities'}
    foreach($item in $callerArtifacts){
        $cap=@($ret.caller_artifact_capabilities|Where-Object {$_.role -ceq $item.role})
        if($cap.Count -ne 1 -or $cap[0].path -cne ($projectRoot+'/'+$item.reference.path) -or $cap[0].bytes -ne $item.reference.bytes -or $cap[0].sha256 -cne $item.reference.sha256 -or $cap[0].native_identity -cne $item.native_identity -or $cap[0].read_share -ne 3){throw 'caller artifact exact capability join'}
    }
    if($ret.schema -cne 'cho51_q_supervisor_return_v1' -or $ret.operation_id -cne $operation -or $ret.accepted_by_supervisor -isnot [bool] -or -not $ret.accepted_by_supervisor -or $ret.handle_closure.inputs -isnot [bool] -or -not $ret.handle_closure.inputs -or $ret.handle_closure.outputs -isnot [bool] -or -not $ret.handle_closure.outputs){throw 'supervisor return/closure'}
    ClosedRecord $ret.output_allocation @('supervisor_files','supervisor_bytes','supervisor_file_cap','supervisor_byte_cap','fixture_files','fixture_bytes','fixture_largest')
    foreach($key in $ret.output_allocation.Keys){$number=$ret.output_allocation[$key];if(($number -isnot [int] -and $number -isnot [long]) -or $number -lt 0){throw 'exact output allocation integer'}}
    $allocation=$ret.output_allocation
    if($allocation.supervisor_file_cap -ne 40 -or $allocation.supervisor_byte_cap -ne 8MB -or $allocation.supervisor_files -gt 40 -or $allocation.supervisor_bytes -gt 8MB -or $allocation.fixture_files -gt 160 -or $allocation.fixture_bytes -gt 32MB -or $allocation.fixture_largest -gt 8MB -or $allocation.fixture_largest -gt $allocation.fixture_bytes){throw 'whole operation allocation'}
    VerifyCallerInputs
    $accepted=$true
}catch{$callerError=$_.Exception.GetType().Name+': '+$_.Exception.Message;if($null -ne $journal.stream -and -not $journal.faulted){Journal $journal 'caller_error' $callerError}}
finally {
    try {
        if($null -ne $owner){
            $owner.Dispose()
            $state=@{creation_attempted=$owner.CreationAttempted;pid=$owner.Pid;creation_filetime=$owner.CreationFileTime;limits_verified=$owner.LimitsVerified;atomic_membership=$owner.AtomicMembership;resumed=$owner.Resumed;job_empty=$owner.JobEmpty;job_closed=$owner.JobClosed;process_closed=$owner.ProcessClosed;thread_closed=$owner.ThreadClosed;reaped=$owner.Reaped;fault=$owner.Fault;cleanup_error=$owner.CleanupError;samples=$owner.Samples;minimum_ram=$owner.MinimumRam;minimum_disk=$owner.MinimumDisk;peak_caller_private=$owner.PeakCallerPrivate;peak_process=$owner.PeakProcessBytes;peak_job=$owner.PeakJobBytes;watchdog_joined=$owner.WatchdogJoined;owned_nul_closed=$owner.InputClosed;stdout_eof=$owner.StdoutEof;stderr_eof=$owner.StderrEof;stdout_overflow=$owner.StdoutOverflow;stderr_overflow=$owner.StderrOverflow;stdout_reader_closed=$owner.StdoutReaderClosed;stderr_reader_closed=$owner.StderrReaderClosed;stdout_writer_closed=$owner.StdoutWriterClosed;stderr_writer_closed=$owner.StderrWriterClosed;stdout_reader_thread_handle_closed=$owner.StdoutThreadClosed;stderr_reader_thread_handle_closed=$owner.StderrThreadClosed;stdout_reader_joined=$owner.StdoutJoined;stderr_reader_joined=$owner.StderrJoined;stdout_cancel_attempted=$owner.StdoutCancelled;stderr_cancel_attempted=$owner.StderrCancelled;stdout_retained_bytes=$owner.StdoutBytes;stderr_retained_bytes=$owner.StderrBytes;stdout_observed_bytes=$owner.StdoutObserved;stderr_observed_bytes=$owner.StderrObserved;stdout_error=$owner.StdoutError;stderr_error=$owner.StderrError}
            if(-not($owner.JobEmpty -and $owner.JobClosed -and $owner.ProcessClosed -and $owner.ThreadClosed -and $owner.Reaped -and $owner.WatchdogJoined -and $owner.InputClosed -and $owner.StdoutEof -and $owner.StderrEof -and $owner.StdoutReaderClosed -and $owner.StderrReaderClosed -and $owner.StdoutWriterClosed -and $owner.StderrWriterClosed -and $owner.StdoutThreadClosed -and $owner.StderrThreadClosed -and $owner.StdoutJoined -and $owner.StderrJoined) -or $owner.StdoutOverflow -or $owner.StderrOverflow -or $null -ne $owner.CleanupError -or $null -ne $owner.Fault){$accepted=$false}
            if($owner.StdoutJoined -and $owner.StdoutEof -and -not $owner.StdoutOverflow -and $null -eq $owner.StdoutError){$outText=$owner.StdoutText()}
            if($owner.StderrJoined -and $owner.StderrEof -and -not $owner.StderrOverflow -and $null -eq $owner.StderrError){$errText=$owner.StderrText()}
        }
        $noConsumers=($null -eq $owner -or -not $owner.CreationAttempted)
        $artifactHandoff.consumers_reaped=(-not $noConsumers -and $owner.Reaped -and $owner.JobEmpty -and $owner.JobClosed -and $owner.ProcessClosed)
        if($noConsumers -or $artifactHandoff.consumers_reaped){
            try{VerifyCallerArtifacts;foreach($item in $lNativeArtifacts){VerifyLNativeItem $item};foreach($item in $lToolInputs){VerifyLNativeItem $item};$lFinalVerified=($null -ne $lBundle);$artifactHandoff.final_original_recheck=$true;$artifactHandoff.original_writers_held_through_consumers=($artifactHandoff.consumers_reaped -and $callerArtifacts.Count -eq 3)}
            catch{$accepted=$false;$callerError='caller artifact final recheck: '+$_.Exception.Message}
        }else{$accepted=$false}
        $artifactHandoff.artifacts=@($callerArtifacts|ForEach-Object {@{role=$_.role;reference=$_.reference;native_identity=$_.native_identity;writer_share=1}})
        if($accepted -and ($callerArtifacts.Count -ne 3 -or -not $artifactHandoff.final_original_recheck -or -not $artifactHandoff.original_writers_held_through_consumers)){$accepted=$false}
        if($claimCreated){WriteRecord ('caller-return_'+$operation+'.json') @{schema='cho51_q_caller_return_v1';operation_id=$operation;accepted_by_caller=$accepted;error=$callerError;origin_utc=$originUtc.ToString('o');origin_qpc=$originQpc;frequency=$frequency;return_utc=[DateTime]::UtcNow.ToString('o');return_qpc=[Diagnostics.Stopwatch]::GetTimestamp();elapsed_seconds=(Elapsed);outer_custody=$state;bootstrap_native_custody=$bootstrapCustody;bootstrap_controls=$bootstrapControls;final_input_verification=$finalInputVerified;stdout=$outText;stderr=$errText;stdio_capture_kind='owned_anonymous_pipes_strict_EOF_1MiB_retained_each';bootstrap_hard_deadline_seconds=65;bootstrap_original_process_handle_retained=$true;bootstrap_guard=(GuardSnapshot);guard_shutdown_pending=$true;startup_samples=$samples;initial_caller_private_bytes=$initialPrivate;supervisor_exit=$supervisorExit;api_mapping=$apiMapping;api_mapping_native_identity=$apiIdentity;native_diagnostic=$nativeDiagnostic;native_diagnostic_native_identity=$diagnosticIdentity;l_native_build=@{bundle=$lBundle;operations=$lBuildOperations.ToArray();final_original_recheck=$lFinalVerified;tool_inputs=$lToolInputs.Count};artifact_handoff=$artifactHandoff;caller_output_allocation=@{file_cap=40;byte_cap=20MB;reserved_files=$callerOutputReservations.Count;reserved_bytes=$script:callerOutputReservedBytes;reservations=$callerOutputReservations};input_handle_count=$inputs.Count;tool_return_pending=$true;independent_actual_review_pending=$true;historical_custody_closed=$false;historical_operation_released=$false;historical_retry_allowed=$false;restart_qualified=$false;boundary_qualified=$false;complete_dependency_closure=$false;launch_authorized=$false;scientific_admission=$false}}
    }finally{
        $closeErrors=[Collections.Generic.List[string]]::new()
        foreach($s in $outputs){try{$s.Dispose()}catch{$closeErrors.Add($_.Exception.Message)}}
        foreach($s in $inputs){try{$s.Dispose()}catch{$closeErrors.Add($_.Exception.Message)}}
        foreach($handle in $lDirectoryHandles.Values){try{$handle.Dispose();if(-not $handle.IsClosed){throw 'L compiler directory handle close'}}catch{$closeErrors.Add($_.Exception.Message)}}
        $fileClosure.closed=$closeErrors.Count -eq 0
        if($null -ne $bootstrapOwner){$bootstrapOwner.Dispose()}
    if(-not $fileClosure.closed){throw ('original input/output close failure: '+($closeErrors -join '; '))}
    }
}
Journal $journal 'caller_ready_to_close'
$journal.stream.Dispose();$journal.closed=$true
StopGuard
if($null -ne $bootstrapOwner){$bootstrapOwner.Dispose();$bootstrapCustody=OwnerState $bootstrapOwner;if($bootstrapCustody.creation_attempted -or -not $bootstrapCustody.job_closed -or -not $bootstrapCustody.job_empty -or -not $bootstrapCustody.watchdog_joined -or $null -ne $bootstrapCustody.cleanup_error -or $null -ne $bootstrapCustody.fault){$accepted=$false}}
$finalGuard=GuardSnapshot
if(-not $finalGuard.joined -or -not $finalGuard.closed -or -not $finalGuard.done -or $null -ne $finalGuard.error){$accepted=$false}
@{schema='cho51_q_external_return_v1';operation_id=$operation;accepted_by_caller=$accepted;error=$callerError;outer_custody=$state;bootstrap_native_custody=$bootstrapCustody;bootstrap_controls=$bootstrapControls;final_input_verification=$finalInputVerified;api_mapping=$apiMapping;api_mapping_native_identity=$apiIdentity;native_diagnostic=$nativeDiagnostic;native_diagnostic_native_identity=$diagnosticIdentity;l_native_build=@{bundle=$lBundle;operations=$lBuildOperations.ToArray();final_original_recheck=$lFinalVerified;tool_inputs=$lToolInputs.Count};artifact_handoff=$artifactHandoff;caller_output_allocation=@{file_cap=40;byte_cap=20MB;reserved_files=$callerOutputReservations.Count;reserved_bytes=$script:callerOutputReservedBytes;reservations=$callerOutputReservations};bootstrap_guard=$finalGuard;original_file_handles_closed=($fileClosure.closed -and $journal.closed);bootstrap_journal_closed=$journal.closed;bootstrap_journal_bytes=$journal.bytes;bootstrap_journal_records=$journal.records;elapsed_seconds=(Elapsed);historical_custody_closed=$false;historical_operation_released=$false;historical_retry_allowed=$false;restart_qualified=$false;boundary_qualified=$false;complete_dependency_closure=$false;launch_authorized=$false;scientific_admission=$false}|ConvertTo-Json -Depth 8 -Compress
if(-not $accepted){throw ('Q qualification not accepted: '+$callerError)}
} finally {
    # Deadline remains armed through final record publication and original
    # input/output closure; disarm only after emitting the external return.
    if($null -ne $bootstrapOwner){$bootstrapOwner.Dispose()}
    if(-not $fileClosure.closed){$killAction.Invoke();throw 'original file closure uncertain; self termination failed'}
    if(-not $guardLifecycle.closed){StopGuard}
    if($null -ne $journal.stream -and -not $journal.closed){$journal.stream.Dispose();$journal.closed=$true}
    if(-not $startupDisarmed){$startupDeadline.CancelAfter([Threading.Timeout]::Infinite);$startupRegistration.Dispose();$startupDeadline.Dispose();$startupDisarmed=$true;$bootstrapPhase=$false}
    $hardDeadline.CancelAfter([Threading.Timeout]::Infinite)
    $deadlineRegistration.Dispose()
    $hardDeadline.Dispose()
    $faultDeadline.CancelAfter([Threading.Timeout]::Infinite)
    $faultRegistration.Dispose();$faultDeadline.Dispose()
    $callerProcess.Dispose()
}
















