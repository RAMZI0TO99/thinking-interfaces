# Definitions loaded only from exact source-review/admission bytes by invoke_q.
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
function OwnedClosed($state) {
    foreach($key in @('creation_attempted','limits_verified','atomic_membership','resumed','job_empty','job_closed','process_closed','thread_closed','reaped','watchdog_joined','owned_nul_closed','stdout_eof','stderr_eof','stdout_reader_closed','stderr_reader_closed','stdout_writer_closed','stderr_writer_closed','stdout_reader_thread_handle_closed','stderr_reader_thread_handle_closed','stdout_reader_joined','stderr_reader_joined')){if($state[$key] -isnot [bool] -or -not $state[$key]){return $false}}
    foreach($key in @('fault','cleanup_error','stdout_error','stderr_error')){if($null -ne $state[$key]){return $false}}
    return (-not $state.stdout_overflow -and -not $state.stderr_overflow)
}
function ReadControlIndex {
    $expected=$phase.Replace('\','/')+'/control-index_'+$operation+'.json'
    if([IO.Path]::GetFullPath($ControlIndex).Replace('\','/') -cne $expected -or $ControlIndexSha256 -cnotmatch '^[0-9a-f]{64}$'){throw 'control index authority argument'}
    $pin=PinBytes $ControlIndex
    if($pin.sha256 -cne $ControlIndexSha256 -or $pin.bytes -gt 8MB){throw 'control index argument pin'}
    $index=ReadPinnedJson @{path=$expected;bytes=$pin.bytes;sha256=$pin.sha256}
    ClosedRecord $index @('schema','operation_id','admission','controls')
    if($index.schema -cne 'cho51_startup_q_control_index_v1' -or $index.operation_id -cne $operation){throw 'control index operation'}
    ClosedRecord $index.admission @('path','bytes','sha256')
    if($index.admission.path -cne [IO.Path]::GetFullPath($Admission).Replace('\','/') -or $index.admission.sha256 -cne $AdmissionSha256 -or $index.admission.bytes -ne (Get-Item -LiteralPath $Admission).Length){throw 'control index enclosing Q join'}
    if($index.controls -isnot [array] -or $index.controls.Count -ne 8){throw 'eight fixed startup controls'}
    $seen=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
    for($i=0;$i -lt 8;$i++){
        $entry=$index.controls[$i];ClosedRecord $entry @('name','probe','expectation','capsule')
        $names=@('fast','stall','empty','malformed','reordered','partial','review_findings','review_identity')
        $probes=@('fast','stall','empty','malformed','reordered','partial','fast','fast')
        $expectations=@('observed','observed','marker_refused','marker_refused','marker_refused','marker_refused','review_refused','review_refused')
        if($entry.name -cne $names[$i] -or $entry.probe -cne $probes[$i] -or $entry.expectation -cne $expectations[$i]){throw 'startup control order/scope'}
        $capsule=ReadPinnedJson $entry.capsule
        if($capsule.schema -cne 'cho51_startup_capsule_v1' -or $capsule.role -cne 'Q_STARTUP_CONTROL' -or $capsule.probe -cne $entry.probe -or -not $seen.Add($capsule.operation_id)){throw 'startup control role/identity'}
        if($capsule.enclosing_q.operation_id -cne $operation -or $capsule.enclosing_q.admission.path -cne $index.admission.path -or $capsule.enclosing_q.admission.sha256 -cne $AdmissionSha256 -or $capsule.enclosing_q.admission.bytes -ne $index.admission.bytes -or $capsule.enclosing_q.limits.process_mib -ne 512 -or $capsule.enclosing_q.limits.job_mib -ne 768){throw 'enclosing Q scope'}
        if($capsule.caller_runtime.executable.path -cne $request.caller_runtime.path -or $capsule.caller_runtime.executable.sha256 -cne $request.caller_runtime.sha256 -or $capsule.caller_runtime.executable.bytes -ne $request.caller_runtime.bytes){throw 'control runtime join'}
        foreach($row in $capsule.sources.GetEnumerator()){
            if(-not $row.Key.StartsWith($projectRoot+'/',[StringComparison]::Ordinal)){throw 'control source root'}
            $relative=$row.Key.Substring($projectRoot.Length+1)
            if(-not $request.sources.ContainsKey($relative) -or $request.sources[$relative].bytes -ne $row.Value.bytes -or $request.sources[$relative].sha256 -cne $row.Value.sha256){throw 'Q must cover exact controller sources'}
        }
        $entry['record']=$capsule
    }
    return $index
}
function VerifyOriginalInputs {
    foreach($item in $inputPins){
        Check;$stream=$item.stream;$stream.Position=0
        if($stream.Length -ne $item.pin.bytes -or [QNative.Owner]::FileIdentity($stream.SafeFileHandle) -cne $item.native_identity){throw 'final retained input length/identity'}
        $hash=[Security.Cryptography.IncrementalHash]::CreateHash([Security.Cryptography.HashAlgorithmName]::SHA256)
        try{$buffer=[byte[]]::new(65536);do{Check;$n=$stream.Read($buffer,0,$buffer.Length);if($n){$hash.AppendData($buffer,0,$n)}}while($n);$sha=[Convert]::ToHexString($hash.GetHashAndReset()).ToLowerInvariant()}finally{$hash.Dispose();$stream.Position=0}
        if($sha -cne $item.pin.sha256){throw 'final retained input hash'}
    }
}
function RunStartupControls($index) {
    $results=[Collections.Generic.List[object]]::new()
    foreach($entry in $index.controls){
        Check;if((Elapsed) -ge 44){throw 'insufficient Q work for diagnostic and cleanup'}
        $controlOwner=[QNative.Owner]::new($originQpc,$originUtc.ToString('o'),$stopPath)
        $owned=@{kind=('startup_'+$entry.name);owner=$controlOwner;exit_code=$null;stdout='';stderr=''}
        $outerOperations.Add($owned)
        $command=@('-NoLogo','-NoProfile','-NonInteractive','-File',($projectRoot+'/tools/local_validation/startup2/diagnostic.ps1'),'-Capsule',$entry.capsule.path,'-CapsuleBytes',[string]$entry.capsule.bytes,'-CapsuleSha256',$entry.capsule.sha256)
        try{
            $controlOwner.Start($request.caller_runtime.path,[string[]]$command,$projectRoot)
            while(-not $controlOwner.Poll()){Check;[Threading.Thread]::Sleep(20)}
            $owned.exit_code=$controlOwner.ExitCode()
        }finally{
            $controlOwner.Dispose()
            if($controlOwner.StdoutJoined -and $controlOwner.StdoutEof){$owned.stdout=$controlOwner.StdoutText()}
            if($controlOwner.StderrJoined -and $controlOwner.StderrEof){$owned.stderr=$controlOwner.StderrText()}
        }
        $expectedExit=if($entry.expectation -ceq 'observed'){0}else{1}
        if(-not (OwnedClosed (OwnerState $controlOwner)) -or $owned.exit_code -ne $expectedExit -or $owned.stderr.Length -ne 0){throw ('owned startup control failed: '+$entry.name)}
        $report=StrictJson $owned.stdout
        $validated=ValidateStartupReturn $entry $report $controlOwner
        $results.Add($validated)
    }
    return $results.ToArray()
}
function ObservedReference($ref,[string]$path) {
    ClosedRecord $ref @('path','bytes','sha256','native_identity')
    if($ref.path -cne $path -or $ref.native_identity -cnotmatch '^[0-9a-f]{16}:[0-9a-f]{32}$'){throw 'observed reference identity/path'}
    $value=ReadPinnedJson @{path=$ref.path;bytes=$ref.bytes;sha256=$ref.sha256}
    if([QNative.Owner]::FileIdentity($inputs[$inputs.Count-1].SafeFileHandle) -cne $ref.native_identity){throw 'observed original output identity'}
    return $value
}
function ValidateStartupReturn($entry,$report,$controlOwner) {
    ClosedRecord $report @('schema','operation_id','role','probe','status','failure','origin','caller','elapsed_seconds','authority_verified','native_ids_bound','dispose_registration_joined','owned_lifecycle_closed','custody','original_streams_closed','final_input_verification','final_output_verification','guard','observation','outputs','actual_tool_return_pending','exit_code','termination_cause','historical_custody_closed','historical_operation_released','historical_retry_allowed','restart_qualified','scientific_admission','candidate_tests_executed','successor_controls_executed')
    $capsule=$entry.record
    if($report.schema -cne 'cho51_startup_external_return_v1' -or $report.operation_id -cne $capsule.operation_id -or $report.role -cne 'Q_STARTUP_CONTROL' -or $report.probe -cne $entry.probe){throw 'startup return identity/status'}
    if($entry.expectation -ceq 'observed'){
        if($report.status -cne 'observed_diagnostic_only' -or $null -ne $report.failure){throw 'positive startup status'}
    }else{
        if($report.status -cne 'refused' -or $report.failure -isnot [string] -or -not $report.failure){throw 'required startup refusal'}
    }
    if($entry.expectation -ceq 'review_refused'){
        $reason=if($entry.name -ceq 'review_findings'){'unresolved startup source review findings'}else{'startup source review reviewer identity'}
        if(-not $report.failure.Contains($reason)){throw 'wrong authority refusal reason'}
        foreach($key in @('authority_verified','native_ids_bound','dispose_registration_joined','owned_lifecycle_closed','final_input_verification','final_output_verification')){if($report[$key] -isnot [bool] -or $report[$key]){throw 'authority negative reached privileged effect'}}
        if($report.original_streams_closed -isnot [bool] -or -not $report.original_streams_closed -or $null -ne $report.custody -or $null -ne $report.observation -or $report.outputs -isnot [array] -or $report.outputs.Count -ne 0 -or (Test-Path -LiteralPath $capsule.output_root)){throw 'authority negative effects or input closure'}
        if($report.caller.pid -ne $controlOwner.Pid -or $report.caller.creation_filetime -ne $controlOwner.CreationFileTime -or $report.origin.frequency -ne $frequency -or $report.origin.qpc -lt $originQpc -or (UtcString $report.origin.utc) -lt $originUtc -or $report.elapsed_seconds -lt 0 -or $report.elapsed_seconds -ge 5){throw 'authority negative original process/clock'}
        foreach($key in @('historical_custody_closed','historical_operation_released','historical_retry_allowed','restart_qualified','scientific_admission')){if($report[$key] -isnot [bool] -or $report[$key]){throw 'authority negative scope'}}
        if($report.candidate_tests_executed -ne 0 -or $report.successor_controls_executed -ne 0){throw 'authority negative candidate scope'}
        return @{name=$entry.name;probe=$entry.probe;expectation=$entry.expectation;capsule=$entry.capsule;external_return=$report;independent_actual_review_pending=$true}
    }
    foreach($key in @('authority_verified','native_ids_bound','dispose_registration_joined','owned_lifecycle_closed','original_streams_closed','final_input_verification','final_output_verification','actual_tool_return_pending')){if($report[$key] -isnot [bool] -or -not $report[$key]){throw ('startup return predicate '+$key)}}
    foreach($key in @('historical_custody_closed','historical_operation_released','historical_retry_allowed','restart_qualified','scientific_admission')){if($report[$key] -isnot [bool] -or $report[$key]){throw 'startup no authority escalation'}}
    foreach($key in @('candidate_tests_executed','successor_controls_executed')){if($report[$key] -is [bool] -or $report[$key] -ne 0){throw 'startup zero candidates'}}
    if($null -ne $report.exit_code -or $report.termination_cause -cne 'unobserved' -or $report.elapsed_seconds -is [bool] -or $report.elapsed_seconds -lt 5 -or $report.elapsed_seconds -ge 15){throw 'honest startup exit/time scope'}
    ClosedRecord $report.origin @('utc','qpc','frequency');ClosedRecord $report.caller @('pid','creation_filetime')
    if($report.caller.pid -ne $controlOwner.Pid -or $report.caller.creation_filetime -ne $controlOwner.CreationFileTime -or $report.origin.frequency -ne $frequency -or $report.origin.qpc -lt $originQpc -or (UtcString $report.origin.utc) -lt $originUtc){throw 'original controller/clock join'}
    foreach($key in @('ready','done','joined','closed','completion_wait_closed')){if($report.guard[$key] -isnot [bool] -or -not $report.guard[$key]){throw ('startup guard '+$key)}}
    if($null -ne $report.guard.error -or $report.guard.samples -lt 2){throw 'startup guard outcome'}
    foreach($key in @('LimitsVerified','AtomicMembership','Resumed','Reaped','JobEmpty','JobClosed','ProcessClosed','ThreadClosed','InputClosed','StdoutEof','StderrEof','StdoutReaderClosed','StderrReaderClosed','StdoutWriterClosed','StderrWriterClosed','StdoutThreadClosed','StderrThreadClosed','StdoutJoined','StderrJoined','WatchdogJoined')){if($report.custody[$key] -isnot [bool] -or -not $report.custody[$key]){throw ('diagnostic custody '+$key)}}
    foreach($key in @('Fault','CleanupError','StdoutError','StderrError')){if(-not $report.custody.ContainsKey($key) -or $null -ne $report.custody[$key]){throw 'diagnostic custody error'}}
    if($report.custody.StdoutOverflow -isnot [bool] -or $report.custody.StdoutOverflow -or $report.custody.StderrOverflow -isnot [bool] -or $report.custody.StderrOverflow){throw 'diagnostic stream overflow'}
    if($report.outputs -isnot [array] -or $report.outputs.Count -ne 5){throw 'five exact diagnostic output descriptors'}
    $expectedOutputs=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    foreach($name in @('claim.json','stdout.bin','stderr.bin','observation.json','journal.json')){[void]$expectedOutputs.Add($capsule.output_root+'/'+$name)}
    foreach($ref in $report.outputs){
        ClosedRecord $ref @('path','bytes','sha256','native_identity')
        if(-not $expectedOutputs.Remove($ref.path) -or $ref.bytes -is [bool] -or $ref.bytes -lt 0 -or $ref.bytes -gt 8MB -or $ref.native_identity -cnotmatch '^[0-9a-f]{16}:[0-9a-f]{32}$'){throw 'diagnostic output descriptor scope'}
        $pin=PinBytes $ref.path
        if($pin.bytes -ne $ref.bytes -or $pin.sha256 -cne $ref.sha256 -or [QNative.Owner]::FileIdentity($inputs[$inputs.Count-1].SafeFileHandle) -cne $ref.native_identity){throw 'diagnostic output original byte/identity join'}
    }
    if($expectedOutputs.Count){throw 'diagnostic output omission'}
    $observation=ObservedReference $report.observation ($capsule.output_root+'/observation.json')
    if($observation.schema -cne 'cho51_startup_observation_v1' -or $observation.operation_id -cne $capsule.operation_id -or $observation.role -cne 'Q_STARTUP_CONTROL' -or $observation.probe -cne $entry.probe -or $null -ne $observation.exit_code -or $observation.termination_cause -cne 'unobserved' -or $observation.origin.qpc -ne $report.origin.qpc -or $observation.origin.utc -cne $report.origin.utc -or $observation.origin.frequency -ne $frequency){throw 'observed control join'}
    $directories=@('AppData','AppData/Local','AppData/Local/Microsoft','AppData/Local/Microsoft/PowerShell')
    if($observation.output_directories -isnot [array] -or ($observation.output_directories -join '|') -cne ($directories -join '|')){throw 'declared cache directory census'}
    ClosedRecord $observation.profile_gathering_setting @('key','value','scope')
    if($observation.profile_gathering_setting.key -cne 'DOTNET_MultiCoreJitNoProfileGather' -or $observation.profile_gathering_setting.value -cne '1' -or $observation.profile_gathering_setting.scope -cne 'probe_environment_only_not_runtime_attestation' -or $capsule.environment.DOTNET_MultiCoreJitNoProfileGather -cne '1'){throw 'fixed profile gathering declaration'}
    $expectedLayout=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    foreach($relative in $directories){[void]$expectedLayout.Add($capsule.output_root+'/'+$relative)}
    foreach($row in $report.outputs){[void]$expectedLayout.Add($row.path)}
    $queue=[Collections.Generic.Queue[string]]::new();$queue.Enqueue($capsule.output_root);$nodes=0
    while($queue.Count){
        $directory=$queue.Dequeue();Check
        foreach($path in [IO.Directory]::EnumerateFileSystemEntries($directory)){
            $normalized=$path.Replace('\','/');$nodes++
            if($nodes -gt 9 -or -not $expectedLayout.Remove($normalized)){throw 'unknown cache/output layout entry'}
            $attributes=[IO.File]::GetAttributes($path)
            if($attributes -band [IO.FileAttributes]::ReparsePoint){throw 'cache/output layout reparse'}
            $relative=$normalized.Substring($capsule.output_root.Length+1)
            if($directories -ccontains $relative){if(-not ($attributes -band [IO.FileAttributes]::Directory)){throw 'cache directory type'};$queue.Enqueue($normalized)}
            elseif($attributes -band [IO.FileAttributes]::Directory){throw 'output file became directory'}
        }
    }
    if($expectedLayout.Count -ne 0 -or $nodes -ne 9){throw 'cache/output census incomplete'}
    if($observation.deadline.target_qpc -ne $report.origin.qpc+5*$frequency -or $observation.deadline.cancel_observed_qpc -lt $observation.deadline.target_qpc -or ($observation.deadline.cancel_observed_qpc-$observation.deadline.target_qpc)/$frequency -gt .25 -or $observation.deadline.registration_joined -isnot [bool] -or -not $observation.deadline.registration_joined){throw 'original disposal deadline/join'}
    if($entry.expectation -ceq 'marker_refused'){
        if($report.failure -cnotlike 'marker evidence refused: *' -or $observation.marker_error -isnot [string] -or -not $observation.marker_error -or $observation.status -cne 'refused_marker_evidence'){throw 'marker refusal not observed'}
        $expectedCount=@{empty=0;malformed=1;reordered=0;partial=1}[$entry.name]
        if($observation.markers.Count -ne $expectedCount){throw 'negative marker prefix count'}
        return @{name=$entry.name;probe=$entry.probe;expectation=$entry.expectation;capsule=$entry.capsule;external_return=$report;observation=$observation;effective_outer_process_mib=512;effective_outer_job_mib=768;independent_actual_review_pending=$true}
    }
    if($null -ne $observation.marker_error){throw 'positive marker error'}
    $events=if($entry.probe -ceq 'fast'){@('fixture_fast_begin','fixture_fast_end')}else{@('fixture_stall_begin')}
    if($observation.markers.Count -ne $events.Count){throw 'exact startup fixture marker count'}
    $last=$report.origin.qpc
    for($i=0;$i -lt $events.Count;$i++){
        $marker=$observation.markers[$i]
        ClosedRecord $marker @('schema','sequence','event','origin_utc','origin_qpc','frequency','qpc','elapsed_seconds','detail')
        if($marker.schema -cne 'cho51_startup_probe_marker_v1' -or $marker.sequence -is [bool] -or $marker.sequence -ne $i -or $marker.event -cne $events[$i] -or $marker.origin_utc -cne $report.origin.utc -or $marker.origin_qpc -ne $report.origin.qpc -or $marker.frequency -ne $frequency -or $marker.qpc -lt $last -or $marker.elapsed_seconds -lt 0 -or $marker.elapsed_seconds -ge 5 -or [Math]::Abs(($marker.qpc-$report.origin.qpc)/$frequency-$marker.elapsed_seconds) -gt .000001){throw 'startup fixture marker order/clock'}
        $last=$marker.qpc
    }
    return @{name=$entry.name;expectation=$entry.expectation;probe=$entry.probe;capsule=$entry.capsule;external_return=$report;observation=$observation;effective_outer_process_mib=512;effective_outer_job_mib=768;independent_actual_review_pending=$true}
}
