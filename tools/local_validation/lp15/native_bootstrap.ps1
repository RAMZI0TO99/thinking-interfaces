$NativeBootstrapGuardScript=@'
param($originalProcess,$directKill,$originalQpc,$originalUtc,$qpcFrequency,$stopFile,$shared,$journal,$faultDeadline,$nativeSampler,$workSeconds,$privateCap)
function Journal($sink,[string]$event,[string]$detail='') {
    [Threading.Monitor]::Enter($sink.lock)
    try {
        if($sink.closed -or $sink.faulted -or $null -eq $sink.stream){throw 'bootstrap journal unavailable'}
        if($sink.records -ge 32){throw 'bootstrap journal record cap'}
        if($detail.Length -gt 1024){$detail=$detail.Substring(0,1024)}
        $row=@{schema=$sink.schema;operation_id=$sink.operation;sequence=$sink.records;event=$event;detail=$detail;utc=[DateTime]::UtcNow.ToString('o');qpc=[Diagnostics.Stopwatch]::GetTimestamp();frequency=[Diagnostics.Stopwatch]::Frequency;caller_pid=$sink.caller_pid;caller_creation_filetime=$sink.creation_filetime;internal_authority_pending=$sink.authority_pending}
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

$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
try {
    $shared.stage='guard_enter';Journal $journal 'guard_enter'
    $shared.stage='native_sensor';Journal $journal 'qualified_native_sensor'
    while(-not $shared.stop) {
        $tick=[Diagnostics.Stopwatch]::GetTimestamp()
        $utc=[DateTime]::UtcNow
        if(($tick-$originalQpc)/$qpcFrequency -lt 0 -or ($tick-$originalQpc)/$qpcFrequency -ge $workSeconds -or $utc -ge $originalUtc.AddSeconds($workSeconds)){throw 'independent caller work deadline'}
        if($shared.last_qpc -ne 0 -and ($tick-$shared.last_qpc)/$qpcFrequency -gt 0.25){throw 'independent guard sampling interval'}
        $directory=[IO.FileInfo]::new($stopFile).Directory
        while($null -ne $directory){
            $attributes=[IO.File]::GetAttributes($directory.FullName)
            if(($attributes -band [IO.FileAttributes]::ReparsePoint) -or -not ($attributes -band [IO.FileAttributes]::Directory)){throw 'independent stop ancestry'}
            $directory=$directory.Parent
        }
        try{[void][IO.File]::GetAttributes($stopFile);throw 'independent project stop present'}catch [IO.FileNotFoundException]{}
        $shared.stage='native_sample'
        if($shared.samples -eq 0){Journal $journal 'native_sample_begin'}
        $nativeSample=$nativeSampler.Sample()
        $shared.stage='resource_check'
        $available=[long]$nativeSample
        $freeDisk=[IO.DriveInfo]::new('D').AvailableFreeSpace
        [Threading.Monitor]::Enter($shared.SyncRoot)
        try {
            # Serialize accesses to the one original Process object's caches.
            # Never construct another Process or look one up by PID.
            $originalProcess.Refresh()
            $private=$originalProcess.PrivateMemorySize64
        } finally {[Threading.Monitor]::Exit($shared.SyncRoot)}
        if(([Diagnostics.Stopwatch]::GetTimestamp()-$tick)/$qpcFrequency -gt 0.25){throw 'independent guard sample duration'}
        if($available -lt 4GB -or $freeDisk -lt 20GB -or $private -gt $privateCap){throw 'independent caller resource floor/cap'}
        $sample=@{qpc=$tick;qpc_end=[Diagnostics.Stopwatch]::GetTimestamp();utc=$utc.ToString('o');elapsed_seconds=($tick-$originalQpc)/$qpcFrequency;available_ram_bytes=$available;free_disk_bytes=$freeDisk;caller_private_bytes=$private;sensor='Q2_qualified_native_GlobalMemoryStatusEx_shared_LP3'}
        [Threading.Monitor]::Enter($shared.SyncRoot)
        try {
            $shared.samples=[int]$shared.samples+1
            $shared.minimum_ram=[Math]::Min([long]$shared.minimum_ram,$available)
            $shared.minimum_disk=[Math]::Min([long]$shared.minimum_disk,[long]$freeDisk)
            $shared.peak_private=[Math]::Max([long]$shared.peak_private,[long]$private)
            $shared.last_qpc=$tick
            if($null -eq $shared.first_sample){$shared.first_sample=$sample}
            if(-not $shared.ready -and ($tick-$shared.first_sample.qpc_end)/$qpcFrequency -ge 0.2){$shared.second_sample=$sample;$shared.ready=$true}
        } finally {[Threading.Monitor]::Exit($shared.SyncRoot)}
        if($shared.samples -eq 1){Journal $journal 'first_sample' ($sample|ConvertTo-Json -Compress)}
        if($shared.ready -and $shared.samples -le 3){Journal $journal 'guard_ready'}
        $shared.stage='active'
        [Threading.Thread]::Sleep(100)
    }
} catch {
    $shared.error=$_.Exception.GetType().Name+': '+$_.Exception.Message
    $faultDeadline.CancelAfter(50)
    try{Journal $journal 'guard_fault' ('stage='+$shared.stage+'; samples='+$shared.samples+'; '+$shared.error)}finally{$directKill.Invoke()}
} finally {
    $shared.done=$true
}
'@

function AssertBootstrapReviewIdentity($review) {
    if($review.reviewer -isnot [string] -or $review.reviewer -cnotmatch '^[a-z][a-z0-9_-]{0,63}$' -or $review.authors -isnot [array] -or $review.authors.Count -lt 1 -or $review.authors.Count -gt 16 -or $review.findings -isnot [array] -or $review.findings.Count -ne 0){throw 'bootstrap independent review identity/findings'}
    $seen=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    foreach($author in $review.authors){if($author -isnot [string] -or $author -cnotmatch '^[a-z][a-z0-9_-]{0,63}$' -or -not $seen.Add($author)){throw 'bootstrap typed unique author identities'}}
    if($seen.Contains($review.reviewer)){throw 'bootstrap reviewer is an author'}
}

function InitializeNativeBootstrap($request,[string]$Role,[string]$Case) {
    if($Role -cnotin @('Q','P','P_Q_CONTROL') -or $Case -cnotin @('accepted','bad_identity')){throw 'closed bootstrap role/case'}
    if($Role -ceq 'P' -and ($request.stage -cne 'P' -or $Case -cne 'accepted')){throw 'P bootstrap cannot select control'}
    if($Role -cne 'P' -and ($request.stage -cne 'Q' -or ($request.bootstrap_controls -join ',') -cne 'accepted,bad_identity')){throw 'explicit Q bootstrap controls'}
    if($Role -ceq 'Q' -and $Case -cne 'accepted'){throw 'actual Q bootstrap cannot inject fault'}
    $sqPath='runs/coordination/cho51_p3_startup_diagnostic_20261031_q3/root-qualification.json'
    $r=$request.bootstrap_qualification;ClosedRecord $r @('path','bytes','sha256')
    if($r.path -cne $sqPath -or $request.sources[$sqPath].bytes -ne $r.bytes -or $request.sources[$sqPath].sha256 -cne $r.sha256){throw 'accepted SQ3 bootstrap qualification pin'}
    $sq=ReadPinnedJson @{path=$projectRoot+'/'+$r.path;bytes=$r.bytes;sha256=$r.sha256}
    if($sq.schema -cne 'cho51_startup_qualification_v1' -or $sq.status -cne 'QUALIFIED_STARTUP2_MECHANISMS_ONLY' -or $sq.author -cne 'project_root' -or $sq.owned_lifecycle_closed -isnot [bool] -or -not $sq.owned_lifecycle_closed -or ($sq.controls -join ',') -cne 'fast,stall'){throw 'accepted SQ3 provenance'}
    $sqActual=ReadPinnedJson $sq.actual_review;$sqSource=ReadPinnedJson $sq.source_review
    $sqQSourcePath='runs/coordination/cho51_p3_startup_diagnostic_20261031_q3/source-review.json';$pin=$request.sources[$sqQSourcePath]
    $sqQSource=ReadPinnedJson @{path=$projectRoot+'/'+$sqQSourcePath;bytes=$pin.bytes;sha256=$pin.sha256}
    foreach($review in @($sqSource,$sqQSource,$sqActual)){
        AssertBootstrapReviewIdentity $review
    }
    if($sqSource.status -cne 'ACCEPTED_SOURCE_STARTUP2' -or $sqQSource.status -cne 'ACCEPTED_SOURCE_SQ3' -or $sqActual.status -cne 'ACCEPTED_STARTUP2_TESTED_SCOPE' -or $sqActual.operation_id -cne $sq.operation_id -or $sqActual.actual_tool_exit_code -ne 0 -or $sqActual.owned_lifecycle_closed -isnot [bool] -or -not $sqActual.owned_lifecycle_closed -or $sqActual.source_review_sha256 -cne $pin.sha256 -or $sqActual.startup_source_review_sha256 -cne $sq.source_review.sha256 -or $sqActual.reviewer -ceq $sqQSource.reviewer -or $sqActual.reviewer -ceq $sqSource.reviewer){throw 'SQ3 accepted actual/source joins'}
    if((UtcString $sqActual.created_utc) -gt (UtcString $sq.created_utc) -or (UtcString $sq.created_utc) -gt (UtcString $request.created_utc)){throw 'SQ3 qualification chronology'}
    foreach($row in $sq.accepted_controller_sources.GetEnumerator()){
        $relative=$row.Key.Substring(($projectRoot+'/').Length)
        if(-not $row.Key.StartsWith($projectRoot+'/',[StringComparison]::Ordinal) -or $request.sources[$relative].sha256 -cne $row.Value.sha256 -or $request.sources[$relative].bytes -ne $row.Value.bytes -or $sqSource.sources[$row.Key].sha256 -cne $row.Value.sha256){throw 'exact SQ3 controller source coverage'}
    }
    $prefix='runs/coordination/cho51_p3_loader_implementation_20261031_q2/'
    $pin=$request.sources[$prefix+'root-qualification.json']
    $qualified=ReadPinnedJson @{path=$projectRoot+'/'+$prefix+'root-qualification.json';bytes=$pin.bytes;sha256=$pin.sha256}
    $records=@{}
    foreach($key in @('source_review','actual_review')){
        $ref=$qualified[$key];ClosedRecord $ref @('path','bytes','sha256')
        $leaf=if($key -ceq 'source_review'){'source-review.json'}else{'actual-review.json'}
        if($ref.path -cne $prefix+$leaf -or $request.sources[$ref.path].sha256 -cne $ref.sha256 -or $request.sources[$ref.path].bytes -ne $ref.bytes){throw 'qualified Q2 review pin'}
        $records[$key]=ReadPinnedJson @{path=$projectRoot+'/'+$ref.path;bytes=$ref.bytes;sha256=$ref.sha256}
    }
    $source=$records.source_review;$actual=$records.actual_review
    AssertBootstrapReviewIdentity $source;AssertBootstrapReviewIdentity $actual
    if($qualified.author -cne 'project_root' -or $qualified.status -cne 'QUALIFIED_LQ1_MECHANISMS_ONLY' -or $source.status -cne 'ACCEPTED_SOURCE_LQ1' -or $source.authors -ccontains $source.reviewer -or $source.findings.Count -ne 0 -or $actual.status -cne 'ACCEPTED_LQ1_TESTED_SCOPE' -or $actual.operation_id -cne $qualified.operation_id -or $actual.source_review_sha256 -cne $qualified.source_review.sha256 -or $actual.actual_tool_exit_code -ne 0 -or $actual.new_operation_owned_lifecycle_closed -isnot [bool] -or -not $actual.new_operation_owned_lifecycle_closed -or $actual.reviewer -ceq $source.reviewer -or $actual.authors -ccontains $actual.reviewer){throw 'qualified Q2 source/actual/Root chain'}
    if((UtcString $source.created_utc) -gt (UtcString $actual.created_utc) -or (UtcString $actual.created_utc) -gt (UtcString $qualified.created_utc) -or (UtcString $qualified.created_utc) -gt (UtcString $request.created_utc)){throw 'Q2 source actual qualification chronology'}
    $helperSource='tools/local_validation/lp2/caller_native.cs'
    if($source.sources[$helperSource].sha256 -cne $request.sources[$helperSource].sha256 -or $source.sources[$helperSource].bytes -ne $request.sources[$helperSource].bytes){throw 'exact Q2 native helper source'}
    $sourcePin=PinBytes ($projectRoot+'/'+$helperSource)
    if($sourcePin.sha256 -cne $source.sources[$helperSource].sha256 -or $sourcePin.bytes -ne $source.sources[$helperSource].bytes){throw 'retained Q2 helper source bytes'}
    foreach($key in @('emitted_pe_verified','original_output_identity_retained','loaded_same_pe_bytes','p_limits_query_verified','empty_job_closed')){
        if($qualified.native_builder_controls[$key] -isnot [bool] -or -not $qualified.native_builder_controls[$key] -or $actual.native_builder_controls[$key] -isnot [bool] -or -not $actual.native_builder_controls[$key]){throw 'qualified Q2 native controls'}
    }
    $r=$qualified.native_helper;ClosedRecord $r @('path','bytes','sha256')
    if($r.path -cne $prefix+'native-helper_'+$qualified.operation_id+'.dll' -or $r.bytes -gt 1MB -or $r.path -cne $actual.native_helper.path -or $r.bytes -ne $actual.native_helper.bytes -or $r.sha256 -cne $actual.native_helper.sha256 -or $qualified.native_builder_controls.helper_identity -cne $actual.native_builder_controls.helper_identity){throw 'qualified Q2 helper artifact join'}
    $expectedIdentity=$qualified.native_builder_controls.helper_identity
    if($expectedIdentity -isnot [string] -or $expectedIdentity -cnotmatch '^[0-9a-f]{16}:[0-9a-f]{32}$'){throw 'typed qualified native helper identity'}
    # Fixed negative under explicit Q-only grant; no arbitrary identity override.
    if($Role -ceq 'P_Q_CONTROL' -and $Case -ceq 'bad_identity'){$expectedIdentity='0000000000000000:00000000000000000000000000000000'}
    if($expectedIdentity -cne $actual.native_builder_controls.helper_identity){$script:bootstrapIdentityRefusedBeforeLoad=$true;throw 'bootstrap expected native identity mismatch'}
    $pin=PinBytes ($projectRoot+'/'+$r.path)
    if($pin.bytes -ne $r.bytes -or $pin.sha256 -cne $r.sha256){throw 'bootstrap retained helper bytes'}
    $original=$inputs[$inputs.Count-1];$raw=[byte[]]::new([int]$original.Length);$offset=0
    while($offset -lt $raw.Length){Check;$count=$original.Read($raw,$offset,$raw.Length-$offset);if($count -le 0){throw 'bootstrap helper short read'};$offset+=$count};$original.Position=0
    [void][Reflection.Assembly]::Load($raw);$script:bootstrapHelperLoaded=$true
    if([PNative.Owner]::FileIdentity($original.SafeFileHandle) -cne $expectedIdentity){throw 'bootstrap original helper identity'}
    Check
    $sampler=[PNative.Owner]::new($originQpc,$originUtc.ToString('o'),$stopPath)
    if(-not $sampler.LimitsVerified -or $sampler.CreationAttempted){$sampler.Dispose();throw 'bootstrap unused empty sampler Job'}
    foreach($entry in $inputPins){$entry.native_identity=[PNative.Owner]::FileIdentity($entry.stream.SafeFileHandle)}
    $script:nativeReady=$true
    Journal $journal 'native_sensor_authorized'
    return $sampler
}
