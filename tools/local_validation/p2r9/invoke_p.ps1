param([Parameter(Mandatory=$true)][string]$Admission,[Parameter(Mandatory=$true)][string]$AdmissionSha256)
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
    $hardDeadline.CancelAfter([Math]::Max(1,[int](245000-([Diagnostics.Stopwatch]::GetTimestamp()-$originQpc)*1000/$frequency)))
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
$journal=@{stream=$null;lock=[object]::new();closed=$false;faulted=$false;bytes=0L;records=0;operation=$null;caller_pid=$null;creation_filetime=$null;authority_pending=$true}
$guardPowerShell=$null;$guardRunspace=$null;$guardInvocation=$null
$guardLifecycle=@{joined=$false;closed=$false;completion_wait_closed=$false;shutdown_elapsed_seconds=$null}
$guardState=[hashtable]::Synchronized(@{ready=$false;done=$false;stop=$false;error=$null;samples=0;minimum_ram=[long]::MaxValue;minimum_disk=[long]::MaxValue;peak_private=0L;first_sample=$null;second_sample=$null;last_qpc=0L;stage='not_started'})
try {
$projectRoot='D:/Aenv/pro3'
$phase=Join-Path $projectRoot 'runs/coordination/cho51_p3_dependency_prepare_20261029_p9'
$stopPath=Join-Path $projectRoot 'runs/coordination/PROJECT_STOP.json'
$inputs=[Collections.Generic.List[IO.FileStream]]::new()
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
        $row=@{schema='cho51_p_bootstrap_event_v1';operation_id=$sink.operation;sequence=$sink.records;event=$event;detail=$detail;utc=[DateTime]::UtcNow.ToString('o');qpc=[Diagnostics.Stopwatch]::GetTimestamp();frequency=[Diagnostics.Stopwatch]::Frequency;caller_pid=$sink.caller_pid;caller_creation_filetime=$sink.creation_filetime;internal_authority_pending=$sink.authority_pending}
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
$guardScript=@'
param($originalProcess,$directKill,$originalQpc,$originalUtc,$qpcFrequency,$stopFile,$shared,$journal,$faultDeadline)
function Journal($sink,[string]$event,[string]$detail='') {
    [Threading.Monitor]::Enter($sink.lock)
    try {
        if($sink.closed -or $sink.faulted -or $null -eq $sink.stream){throw 'bootstrap journal unavailable'}
        if($sink.records -ge 32){throw 'bootstrap journal record cap'}
        if($detail.Length -gt 1024){$detail=$detail.Substring(0,1024)}
        $row=@{schema='cho51_p_bootstrap_event_v1';operation_id=$sink.operation;sequence=$sink.records;event=$event;detail=$detail;utc=[DateTime]::UtcNow.ToString('o');qpc=[Diagnostics.Stopwatch]::GetTimestamp();frequency=[Diagnostics.Stopwatch]::Frequency;caller_pid=$sink.caller_pid;caller_creation_filetime=$sink.creation_filetime;internal_authority_pending=$sink.authority_pending}
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
$counter=$null
try {
    $shared.stage='guard_enter';Journal $journal 'guard_enter'
    [void][Reflection.Assembly]::Load('System.Diagnostics.PerformanceCounter')
    $shared.stage='assembly_loaded';Journal $journal 'assembly_loaded'
    $counter=[Diagnostics.PerformanceCounter]::new('Memory','Available Bytes')
    $shared.stage='counter_created';Journal $journal 'counter_created'
    while(-not $shared.stop) {
        $tick=[Diagnostics.Stopwatch]::GetTimestamp()
        $utc=[DateTime]::UtcNow
        if(($tick-$originalQpc)/$qpcFrequency -lt 0 -or ($tick-$originalQpc)/$qpcFrequency -ge 240 -or $utc -ge $originalUtc.AddSeconds(240)){throw 'independent caller work deadline'}
        if($shared.last_qpc -ne 0 -and ($tick-$shared.last_qpc)/$qpcFrequency -gt 0.25){throw 'independent guard sampling interval'}
        $directory=[IO.FileInfo]::new($stopFile).Directory
        while($null -ne $directory){
            $attributes=[IO.File]::GetAttributes($directory.FullName)
            if(($attributes -band [IO.FileAttributes]::ReparsePoint) -or -not ($attributes -band [IO.FileAttributes]::Directory)){throw 'independent stop ancestry'}
            $directory=$directory.Parent
        }
        try{[void][IO.File]::GetAttributes($stopFile);throw 'independent project stop present'}catch [IO.FileNotFoundException]{}
        $shared.stage='counter_read'
        if($shared.samples -eq 0){Journal $journal 'counter_read_begin'}
        $nativeSample=$counter.NextSample()
        $shared.stage='resource_check'
        if($nativeSample.CounterType.ToString() -cne 'NumberOfItems64'){throw 'independent RAM counter type'}
        $available=[long]$nativeSample.RawValue
        $freeDisk=[IO.DriveInfo]::new('D').AvailableFreeSpace
        [Threading.Monitor]::Enter($shared.SyncRoot)
        try {
            # Serialize accesses to the one original Process object's caches.
            # Never construct another Process or look one up by PID.
            $originalProcess.Refresh()
            $private=$originalProcess.PrivateMemorySize64
        } finally {[Threading.Monitor]::Exit($shared.SyncRoot)}
        if(([Diagnostics.Stopwatch]::GetTimestamp()-$tick)/$qpcFrequency -gt 0.25){throw 'independent guard sample duration'}
        if($available -lt 4GB -or $freeDisk -lt 20GB -or $private -gt 4096MB){throw 'independent caller resource floor/cap'}
        $sample=@{qpc=$tick;utc=$utc.ToString('o');elapsed_seconds=($tick-$originalQpc)/$qpcFrequency;available_ram_bytes=$available;free_disk_bytes=$freeDisk;caller_private_bytes=$private;sensor='local_PDH_Available_Bytes_raw_NumberOfItems64'}
        [Threading.Monitor]::Enter($shared.SyncRoot)
        try {
            $shared.samples=[int]$shared.samples+1
            $shared.minimum_ram=[Math]::Min([long]$shared.minimum_ram,$available)
            $shared.minimum_disk=[Math]::Min([long]$shared.minimum_disk,[long]$freeDisk)
            $shared.peak_private=[Math]::Max([long]$shared.peak_private,[long]$private)
            $shared.last_qpc=$tick
            if($null -eq $shared.first_sample){$shared.first_sample=$sample}
            if(-not $shared.ready -and ($tick-$shared.first_sample.qpc)/$qpcFrequency -ge 0.2){$shared.second_sample=$sample;$shared.ready=$true}
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
    try{if($null -ne $counter){$counter.Dispose()}}catch{$shared.error='independent PDH dispose: '+$_.Exception.Message;$directKill.Invoke()}
    $shared.done=$true
}
'@
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
        $s.Position=0;return @{bytes=$s.Length;sha256=[Convert]::ToHexString($h.GetHashAndReset()).ToLowerInvariant()}
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
    $start=UtcString $created;$end=UtcString $expires
    if($original.Kind -ne [DateTimeKind]::Utc -or $start -gt $original -or $end -lt $original.AddSeconds(300) -or ($end-$start).TotalSeconds -lt 300 -or ($end-$start).TotalSeconds -gt 900){throw 'original caller window'}
}
try {
    if($PSVersionTable.PSVersion.Major -lt 7){throw 'PowerShell7 required'}
    if([IO.Path]::GetDirectoryName([IO.Path]::GetFullPath($Admission)) -ne [IO.Path]::GetFullPath($phase)){throw 'bootstrap admission namespace'}
    $stem=[IO.Path]::GetFileNameWithoutExtension($Admission)
    if($stem -cnotmatch '^admission_([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$'){throw 'bootstrap canonical operation'}
    $journal.operation=$Matches[1];$journal.caller_pid=$callerProcess.Id;$journal.creation_filetime=$callerProcess.StartTime.ToUniversalTime().ToFileTimeUtc()
    $journal.stream=[IO.FileStream]::new((Join-Path $phase ('bootstrap_'+$journal.operation+'.jsonl')),[IO.FileMode]::CreateNew,[IO.FileAccess]::ReadWrite,[IO.FileShare]::Read)
    Journal $journal 'caller_entry'
    Journal $journal 'runspace_create'
    $guardRunspace=[Management.Automation.Runspaces.RunspaceFactory]::CreateRunspace()
    $guardRunspace.Open()
    $guardPowerShell=[Management.Automation.PowerShell]::Create()
    $guardPowerShell.Runspace=$guardRunspace
    [void]$guardPowerShell.AddScript($guardScript).AddArgument($callerProcess).AddArgument($killAction).AddArgument($originQpc).AddArgument($originUtc).AddArgument($frequency).AddArgument($stopPath).AddArgument($guardState).AddArgument($journal).AddArgument($faultDeadline)
    Journal $journal 'runspace_begin'
    $guardInvocation=$guardPowerShell.BeginInvoke()
    while(-not $guardState.ready){
        if($guardState.done -or $guardInvocation.IsCompleted -or $null -ne $guardState.error -or (Elapsed) -ge 5){$faultDeadline.CancelAfter(50);try{Journal $journal 'startup_refused' ('stage='+$guardState.stage+'; ready='+$guardState.ready+'; samples='+$guardState.samples+'; error='+$guardState.error)}finally{$killAction.Invoke()};throw 'independent guard startup refused'}
        [Threading.Thread]::Sleep(20)
    }
    if((Elapsed) -ge 5 -or $startupDeadline.IsCancellationRequested -or $guardState.second_sample.elapsed_seconds -ge 5){$killAction.Invoke();throw 'late startup readiness'}
    $startupDeadline.CancelAfter([Threading.Timeout]::Infinite)
    $startupRegistration.Dispose();$startupDeadline.Dispose()
    $startupDisarmed=$true
    $samples=@($guardState.first_sample,$guardState.second_sample)
    Journal $journal 'startup_ready'
    $initialPrivate=$samples[0].caller_private_bytes
    if(($samples[1].qpc-$samples[0].qpc)/$frequency -lt 0.2){throw 'independent startup sample spacing'}
    Check
    if([IO.Path]::GetDirectoryName([IO.Path]::GetFullPath($Admission)) -ne [IO.Path]::GetFullPath($phase)){throw 'admission location'}
    $pin=PinBytes $Admission
    if($pin.sha256 -cne $AdmissionSha256 -or $pin.bytes -gt 8MB){throw 'admission caller hash'}
    $request=[IO.File]::ReadAllText($Admission)|ConvertFrom-Json -AsHashtable -DateKind String;$operation=$request.operation_id
    if($operation -notmatch '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' -or $request.schema -cne 'cho51_p_admission_v1' -or $request.stage -cne 'P' -or $request.root -cne $projectRoot){throw 'P request identity'}
    $windowOperands=@{created_literal=$request.created_utc;expires_literal=$request.expires_utc;created_utc=(UtcString $request.created_utc).ToString('o');expires_utc=(UtcString $request.expires_utc).ToString('o');original_utc=$originUtc.ToString('o');original_deadline_utc=$originUtc.AddSeconds(300).ToString('o')}
    Journal $journal 'window_operands' ($windowOperands|ConvertTo-Json -Compress)
    AdmissionWindow $request.created_utc $request.expires_utc $originUtc
    [Threading.Monitor]::Enter($guardState.SyncRoot)
    try{$callerPath=$callerProcess.MainModule.FileName.Replace('\','/')}finally{[Threading.Monitor]::Exit($guardState.SyncRoot)}
    if($initialPrivate -gt 4096MB -or $callerPath -cne $request.caller_runtime.path -or $PSVersionTable.PSVersion.ToString() -cne $request.caller_runtime.version){throw 'caller runtime/initial memory'}
    $a=PinBytes $callerPath
    if($a.bytes -ne $request.caller_runtime.bytes -or $a.sha256 -cne $request.caller_runtime.sha256){throw 'caller executable pin'}
    foreach($row in $request.sources.GetEnumerator()){
        if($row.Key -match '(^/|\\|:|\.\.)'){throw 'source path'}
        $a=PinBytes (Join-Path $projectRoot $row.Key)
        if($a.bytes -ne $row.Value.bytes -or $a.sha256 -cne $row.Value.sha256){throw ('source changed: '+$row.Key)}
    }

    foreach($key in @('review','adoption','qualification','native_helper','map_index','coverage_review','api_mapping','native_diagnostic')){
        $ref=$request[$key]
        if($ref.path -match '(^/|\\|:|\.\.)'){throw 'control reference path'}
        $a=PinBytes (Join-Path $projectRoot $ref.path)
        if($a.bytes -ne $ref.bytes -or $a.sha256 -cne $ref.sha256){throw ('control pin: '+$key)}
    }
    $review=[IO.File]::ReadAllText((Join-Path $projectRoot $request.review.path))|ConvertFrom-Json -AsHashtable -DateKind String
    $adoption=[IO.File]::ReadAllText((Join-Path $projectRoot $request.adoption.path))|ConvertFrom-Json -AsHashtable -DateKind String
    $qualification=[IO.File]::ReadAllText((Join-Path $projectRoot $request.qualification.path))|ConvertFrom-Json -AsHashtable -DateKind String
    if($review.status -cne 'ACCEPTED_SOURCE_P2' -or $review.authors -contains $review.reviewer -or $adoption.status -cne 'ADOPTED_P_ONLY' -or $adoption.source_review_sha256 -cne $request.review.sha256 -or $review.sources.Count -ne $request.sources.Count){throw 'independent review/adoption'}
    foreach($row in $request.sources.GetEnumerator()){
        if(-not $review.sources.ContainsKey($row.Key) -or $review.sources[$row.Key].bytes -ne $row.Value.bytes -or $review.sources[$row.Key].sha256 -cne $row.Value.sha256){throw 'reviewed source mismatch'}
    }
    if($adoption.schema -cne 'cho51_p_contract_adoption_v1' -or $adoption.contract_sha256 -cne $request.sources['docs/phase2/cho51_p3_local_validation_contract_20261029.md'].sha256 -or $adoption.design_review_sha256 -cne $request.sources['runs/coordination/cho51_p3_local_validation_design_20261029_v1/design-review.json'].sha256 -or $adoption.supplement_sha256 -cne $request.sources['docs/phase2/cho51_p3_p2r9_dependency_contract_20261029.md'].sha256 -or (UtcString $adoption.created_utc) -gt (UtcString $request.created_utc) -or $adoption.qualification_sha256 -cne $request.qualification.sha256 -or $adoption.coverage_review_sha256 -cne $request.coverage_review.sha256){throw 'P adoption joins/order'}
    if($adoption.api_mapping_sha256 -cne $request.api_mapping.sha256){throw 'P API mapping adoption'}
    if($adoption.native_diagnostic_sha256 -cne $request.native_diagnostic.sha256){throw 'P native diagnostic adoption'}
    # Explicit OS platform-trust inputs use retained read-only caller streams;
    # this does not waive the strict physical-map reader's hardlink guard.
    $planRelative='tools/local_validation/p2r9/api_query_plan.json'
    $planRaw=[IO.File]::ReadAllBytes((Join-Path $projectRoot $planRelative))
    if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($planRaw)).ToLowerInvariant() -cne $request.sources[$planRelative].sha256){throw 'P OS/schema plan pin'}
    $platformPlan=[Text.Encoding]::UTF8.GetString($planRaw)|ConvertFrom-Json -AsHashtable -DateKind String
    if($platformPlan.files.Count -ne 7){throw 'P exact OS pin count'}
    foreach($file in $platformPlan.files){
        if($file.path -cnotmatch '^C:/Windows/System32/(apisetschema|kernelbase|kernel32|ntdll|cabinet|fontsub|mswsock)\.dll$'){throw 'P OS pin scope'}
        $observed=PinBytes $file.path
        if($observed.bytes -ne $file.bytes -or $observed.sha256 -cne $file.sha256){throw 'P fresh retained OS/schema pin'}
    }
    foreach($key in @('historical_custody_closed','historical_operation_released','historical_retry_allowed','restart_qualified','boundary_qualified','complete_dependency_closure','launch_authorized','scientific_admission')){
        if($adoption[$key] -isnot [bool] -or $adoption[$key]){throw 'adoption authority'}
    }
    foreach($key in @('source_review','actual_review')){
        $ref=$qualification[$key];$expected='runs/coordination/cho51_p3_dependency_prepare_20261029_q9/'+$(if($key -eq 'source_review'){'source-review.json'}else{'actual-review.json'})
        if($ref.path -cne $expected){throw 'exact Q review reference'}
        $a=PinBytes (Join-Path $projectRoot $ref.path)
        if($a.bytes -ne $ref.bytes -or $a.sha256 -cne $ref.sha256){throw 'Q review pin'}
    }
    $qSource=[IO.File]::ReadAllText((Join-Path $projectRoot $qualification.source_review.path))|ConvertFrom-Json -AsHashtable -DateKind String
    $qActual=[IO.File]::ReadAllText((Join-Path $projectRoot $qualification.actual_review.path))|ConvertFrom-Json -AsHashtable -DateKind String
    if($qualification.status -cne 'QUALIFIED_P2_Q_TESTED_SCOPE' -or $qSource.status -cne 'ACCEPTED_SOURCE_P2Q' -or $qActual.status -cne 'ACCEPTED_P2Q_TESTED_SCOPE' -or $qSource.reviewer -ceq $qActual.reviewer -or $qActual.operation_id -cne $qualification.operation_id -or $qActual.source_review_sha256 -cne $qualification.source_review.sha256 -or $qActual.actual_tool_exit_code -ne 0 -or $qActual.new_operation_owned_lifecycle_closed -isnot [bool] -or -not $qActual.new_operation_owned_lifecycle_closed){throw 'Q artifact authority'}
    foreach($ref in @($qualification.native_helper,$qActual.native_helper)){
        if($ref.path -cne $request.native_helper.path -or $ref.bytes -ne $request.native_helper.bytes -or $ref.sha256 -cne $request.native_helper.sha256){throw 'qualified native artifact join'}
    }
    if($qualification.test_count -ne 195 -or $qActual.tests_run -ne 195 -or $qualification.timestamp_controls -ne 8 -or $qualification.native_fault_controls -ne 2 -or $qActual.timestamp_controls_passed -ne 8 -or $qActual.native_fault_controls_passed -ne 2 -or (UtcString $qualification.created_utc) -gt (UtcString $adoption.created_utc)){throw 'Q qualification counts/order'}
    foreach($key in @('emitted_pe_verified','original_output_identity_retained','loaded_same_pe_bytes','p_limits_query_verified','empty_job_closed')){
        if($qualification.native_builder_controls[$key] -isnot [bool] -or -not $qualification.native_builder_controls[$key] -or $qActual.native_builder_controls[$key] -isnot [bool] -or -not $qActual.native_builder_controls[$key]){throw 'Q native builder controls'}
    }
    $journal.authority_pending=$false;Journal $journal 'authority_verified'
    # P loads only the exact previously Q-emitted PE; no native compilation.
    WriteRecord ('claim_'+$operation+'.json') @{schema='cho51_p_external_claim_v1';operation_id=$operation;admission_sha256=$AdmissionSha256;origin_utc=$originUtc.ToString('o');origin_qpc=$originQpc;frequency=$frequency}
    $claimCreated=$true

    $helperPath=Join-Path $projectRoot $request.native_helper.path
    $helperStream=$inputs | Where-Object {$_.Name -eq [IO.Path]::GetFullPath($helperPath)} | Select-Object -First 1
    if($null -eq $helperStream -or $helperStream.Length -gt 1MB){throw 'original qualified helper stream'}
    $helper=[byte[]]::new($helperStream.Length);$offset=0;$helperStream.Position=0
    while($offset -lt $helper.Length){Check;$n=$helperStream.Read($helper,$offset,$helper.Length-$offset);if($n -le 0){throw 'helper original read'};$offset+=$n}
    if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($helper)).ToLowerInvariant() -cne $request.native_helper.sha256){throw 'helper original bytes'}
    [void][Reflection.Assembly]::Load($helper)
    $helperIdentity=[PNative.Owner]::FileIdentity($helperStream.SafeFileHandle)
    if($helperIdentity -cne $qualification.native_builder_controls.helper_identity -or $helperIdentity -cne $qActual.native_builder_controls.helper_identity){throw 'qualified native identity handoff'}
    Journal $journal 'qualified_native_loaded'
    $owner=[PNative.Owner]::new($originQpc,$originUtc.ToString('o'),$stopPath)
    foreach($row in $request.runtime.files.GetEnumerator()){
        if(-not $row.Key.StartsWith($request.runtime.root+'/',[StringComparison]::Ordinal)){throw 'runtime scope'}
        $a=PinBytes $row.Key
        if($a.bytes -ne $row.Value.bytes -or $a.sha256 -cne $row.Value.sha256){throw ('runtime changed: '+$row.Key)}
    }
    $attempt=Join-Path $phase ('attempts/'+$operation);$cache=[IO.Path]::GetFullPath((Join-Path $phase ('disabled-bytecode/'+$operation)))
    foreach($path in @($attempt,$cache)){if(Test-Path -LiteralPath $path){throw 'occupied attempt/cache'}}
    foreach($name in @('python312.zip','python._pth','python312._pth','pyvenv.cfg')){if(Test-Path -LiteralPath (Join-Path $request.runtime.root $name)){throw 'unlisted startup configuration/archive'}}
    if(Test-Path -LiteralPath (Join-Path (Split-Path $request.runtime.root) 'pyvenv.cfg')){throw 'parent venv configuration'}
    WriteRecord ('origin_'+$operation+'.json') @{schema='cho51_p_caller_origin_v1';operation_id=$operation;origin_utc=$originUtc.ToString('o');origin_qpc=$originQpc;frequency=$frequency;startup_samples=$samples;initial_caller_private_bytes=$initialPrivate;caller_version=$PSVersionTable.PSVersion.ToString();caller_pid=$PID}
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
    $command=@('-I','-S','-B','-X',('pycache_prefix='+$cache),'-c',$bootstrap,(Join-Path $projectRoot 'tools/local_validation/p2r9/supervisor.py'),$request.sources['tools/local_validation/p2r9/supervisor.py'].sha256,$Admission,$AdmissionSha256,$originUtc.ToString('o'),$originQpc.ToString(),$frequency.ToString())
    Check;if((Elapsed) -ge 210){throw 'insufficient remaining work'}
    Journal $journal 'supervisor_dispatch'
    $owner.Start($request.python,[string[]]$command,$projectRoot)
    while(-not $owner.Poll()){Start-Sleep -Milliseconds 50}
    $supervisorExit=$owner.ExitCode()
    $owner.Dispose()
    $outText=$owner.StdoutText();$errText=$owner.StderrText()
    if($supervisorExit -ne 0){throw 'supervisor exit refused'}
    $ret=$outText|ConvertFrom-Json -AsHashtable -DateKind String
    if($ret.schema -cne 'cho51_p_supervisor_return_v1' -or $ret.operation_id -cne $operation -or $ret.accepted_by_supervisor -isnot [bool] -or -not $ret.accepted_by_supervisor -or $ret.handle_closure.inputs -isnot [bool] -or -not $ret.handle_closure.inputs -or $ret.handle_closure.outputs -isnot [bool] -or -not $ret.handle_closure.outputs){throw 'supervisor return/closure'}

    if($ret.outputs.Count -lt 1 -or $ret.outputs.Count -gt 256){throw 'output handoff count'}
    $received=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase);$receivedBytes=0L
    foreach($descriptor in $ret.outputs){
        Check
        $expectedRoot=[IO.Path]::GetFullPath($attempt).Replace('\','/')+'/'
        if(-not $descriptor.path.StartsWith($expectedRoot,[StringComparison]::Ordinal) -or $descriptor.path.Substring($expectedRoot.Length).Contains('/') -or -not $received.Add($descriptor.path) -or $descriptor.bytes -gt 8MB){throw 'output handoff scope/bounds'}
        $receivedBytes+=$descriptor.bytes;if($receivedBytes -gt 64MB){throw 'output handoff aggregate'}
        $a=PinBytes $descriptor.path
        $stream=$inputs[$inputs.Count-1]
        $identity=[PNative.Owner]::FileIdentity($stream.SafeFileHandle)
        if($a.bytes -ne $descriptor.bytes -or $a.sha256 -cne $descriptor.sha256 -or $identity -cne ($descriptor.native_identity.volume_serial+':'+$descriptor.native_identity.file_id)){throw 'authenticated native output handoff'}
    }
    $handoff=@{authenticated_owned_stream=$true;files=$received.Count;bytes=$receivedBytes;native_identity_and_bytes_verified=$true;original_receiver_handles_retained=$true}

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
        if($claimCreated){WriteRecord ('caller-return_'+$operation+'.json') @{schema='cho51_p_caller_return_v1';operation_id=$operation;accepted_by_caller=$accepted;error=$callerError;origin_utc=$originUtc.ToString('o');origin_qpc=$originQpc;frequency=$frequency;return_utc=[DateTime]::UtcNow.ToString('o');return_qpc=[Diagnostics.Stopwatch]::GetTimestamp();elapsed_seconds=(Elapsed);outer_custody=$state;output_handoff=$handoff;stdout=$outText;stderr=$errText;stdio_capture_kind='owned_anonymous_pipes_strict_EOF_1MiB_retained_each';bootstrap_hard_deadline_seconds=245;bootstrap_original_process_handle_retained=$true;bootstrap_guard=(GuardSnapshot);guard_shutdown_pending=$true;startup_samples=$samples;initial_caller_private_bytes=$initialPrivate;supervisor_exit=$supervisorExit;input_handle_count=$inputs.Count;tool_return_pending=$true;independent_actual_review_pending=$true;historical_custody_closed=$false;historical_operation_released=$false;historical_retry_allowed=$false;restart_qualified=$false;boundary_qualified=$false;complete_dependency_closure=$false;launch_authorized=$false;scientific_admission=$false}}
    }finally{
        $closeErrors=[Collections.Generic.List[string]]::new()
        foreach($s in $outputs){try{$s.Dispose()}catch{$closeErrors.Add($_.Exception.Message)}}
        foreach($s in $inputs){try{$s.Dispose()}catch{$closeErrors.Add($_.Exception.Message)}}
        $fileClosure.closed=$closeErrors.Count -eq 0
        if(-not $fileClosure.closed){throw ('original input/output close failure: '+($closeErrors -join '; '))}
    }
}
Journal $journal 'caller_ready_to_close'
$journal.stream.Dispose();$journal.closed=$true
StopGuard
$finalGuard=GuardSnapshot
if(-not $finalGuard.joined -or -not $finalGuard.closed -or -not $finalGuard.done -or $null -ne $finalGuard.error){$accepted=$false}
@{schema='cho51_p_external_return_v1';operation_id=$operation;accepted_by_caller=$accepted;error=$callerError;outer_custody=$state;output_handoff=$handoff;bootstrap_guard=$finalGuard;original_file_handles_closed=($fileClosure.closed -and $journal.closed);bootstrap_journal_closed=$journal.closed;bootstrap_journal_bytes=$journal.bytes;bootstrap_journal_records=$journal.records;elapsed_seconds=(Elapsed);historical_custody_closed=$false;historical_operation_released=$false;historical_retry_allowed=$false;restart_qualified=$false;boundary_qualified=$false;complete_dependency_closure=$false;launch_authorized=$false;scientific_admission=$false}|ConvertTo-Json -Depth 8 -Compress
if(-not $accepted){throw ('P preparation not accepted: '+$callerError)}
} finally {
    # Deadline remains armed through final record publication and original
    # input/output closure; disarm only after emitting the external return.
    if(-not $fileClosure.closed){$killAction.Invoke();throw 'original file closure uncertain; self termination failed'}
    if(-not $guardLifecycle.closed){StopGuard}
    if($null -ne $journal.stream -and -not $journal.closed){$journal.stream.Dispose();$journal.closed=$true}
    if(-not $startupDisarmed){$startupDeadline.CancelAfter([Threading.Timeout]::Infinite);$startupRegistration.Dispose();$startupDeadline.Dispose();$startupDisarmed=$true}
    $hardDeadline.CancelAfter([Threading.Timeout]::Infinite)
    $deadlineRegistration.Dispose()
    $hardDeadline.Dispose()
    $faultDeadline.CancelAfter([Threading.Timeout]::Infinite)
    $faultRegistration.Dispose();$faultDeadline.Dispose()
    $callerProcess.Dispose()
}

















