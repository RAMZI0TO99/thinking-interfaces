param([Parameter(Mandatory=$true)][string]$Admission,[Parameter(Mandatory=$true)][string]$AdmissionSha256)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$originUtc=[DateTime]::UtcNow
$originQpc=[Diagnostics.Stopwatch]::GetTimestamp()
$frequency=[Diagnostics.Stopwatch]::Frequency
# Opaque R provisioning only: no Git/Python/compiler or child process is run.
# Establish the independent hard deadline before any pin, PDH query or copying.
# This is a direct managed Action bound to the original Process object;
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
    # No pin/copy/child effect has occurred. If the independent deadline
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
$phase=Join-Path $projectRoot 'runs/coordination/cho51_p3_git_materialization_20261029_r1'
$stopPath=Join-Path $projectRoot 'runs/coordination/PROJECT_STOP.json'
$inputs=[Collections.Generic.List[IO.FileStream]]::new()
$outputs=[Collections.Generic.List[IO.FileStream]]::new()
$accepted=$false;$callerError=$null;$operation=$null;$claimCreated=$false;$samples=@()
# This exact inline guard is part of the pinned invoke_r source. Its whole
# pipeline runs in its own dedicated runspace, independently of caller pinning
# and opaque copying. No scriptblock is used as a thread/timer callback.
function Journal($sink,[string]$event,[string]$detail='') {
    [Threading.Monitor]::Enter($sink.lock)
    try {
        if($sink.closed -or $sink.faulted -or $null -eq $sink.stream){throw 'bootstrap journal unavailable'}
        if($sink.records -ge 32){throw 'bootstrap journal record cap'}
        if($detail.Length -gt 1024){$detail=$detail.Substring(0,1024)}
        $row=@{schema='cho51_r_bootstrap_event_v1';operation_id=$sink.operation;sequence=$sink.records;event=$event;detail=$detail;utc=[DateTime]::UtcNow.ToString('o');qpc=[Diagnostics.Stopwatch]::GetTimestamp();frequency=[Diagnostics.Stopwatch]::Frequency;caller_pid=$sink.caller_pid;caller_creation_filetime=$sink.creation_filetime;internal_authority_pending=$sink.authority_pending}
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
        $row=@{schema='cho51_r_bootstrap_event_v1';operation_id=$sink.operation;sequence=$sink.records;event=$event;detail=$detail;utc=[DateTime]::UtcNow.ToString('o');qpc=[Diagnostics.Stopwatch]::GetTimestamp();frequency=[Diagnostics.Stopwatch]::Frequency;caller_pid=$sink.caller_pid;caller_creation_filetime=$sink.creation_filetime;internal_authority_pending=$sink.authority_pending}
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
        if(($tick-$originalQpc)/$qpcFrequency -lt 0 -or ($tick-$originalQpc)/$qpcFrequency -ge 60 -or $utc -ge $originalUtc.AddSeconds(60)){throw 'independent caller work deadline'}
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
        if($available -lt 4GB -or $freeDisk -lt 20GB -or $private -gt 512MB){throw 'independent caller resource floor/cap'}
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
    if((Elapsed) -ge 60 -or [DateTime]::UtcNow -ge $originUtc.AddSeconds(60)){throw 'original R work deadline'}
    if(-not $guardState.ready -or $guardState.done -or $null -ne $guardState.error -or $null -eq $guardInvocation -or $guardInvocation.IsCompleted){throw 'independent caller guard not active'}
    if(([Diagnostics.Stopwatch]::GetTimestamp()-$guardState.last_qpc)/$frequency -gt 0.25){$killAction.Invoke();throw 'independent caller guard sample stale'}
    $dir=[IO.DirectoryInfo]::new((Split-Path $stopPath))
    while($null -ne $dir){if([IO.File]::GetAttributes($dir.FullName) -band [IO.FileAttributes]::ReparsePoint){throw 'stop ancestry'};$dir=$dir.Parent}
    try{[IO.File]::GetAttributes($stopPath)|Out-Null;throw 'project stop present'}catch [IO.FileNotFoundException]{}
    if(([IO.DriveInfo]::new('D')).AvailableFreeSpace -lt 20GB){throw 'disk floor'}
}

$qPhase='runs/coordination/cho51_p3_dependency_prepare_20261029_q1'
$rPhase='runs/coordination/cho51_p3_git_materialization_20261029_r1'
$gitRoot='C:/Users/aladdin-alyanai/AppData/Local/Programs/Git'
$helperRelative=$qPhase+'/native-helper_9726e95c-1844-49aa-b43f-7dc688052766.dll'
$requiredSources=@('tools/local_validation/r1/invoke_r.ps1','tools/local_validation/r1/README.md',
    'docs/phase2/cho51_p3_git_materialization_contract_20261029.md','docs/PROJECT_EXECUTION_POLICY.md',
    ($qPhase+'/root-qualification.json'),($qPhase+'/source-review.json'),($qPhase+'/actual-review.json'),
    'runs/coordination/cho51_p3_dependency_prepare_20261029_p1/root-disposition.json',($rPhase+'/design-advice.json'))
$falseFlags=@('historical_custody_closed','historical_operation_released','historical_retry_allowed',
    'restart_qualified','boundary_qualified','complete_dependency_closure','launch_authorized','scientific_admission')
$expectedLimits=@{whole_seconds=90;work_seconds=60;cleanup_seconds=5;hard_seconds=65;caller_mib=512;
    startup_ram_gib=4;active_ram_gib=4;disk_gib=20;files=256;file_bytes=16777216;total_bytes=201326592;
    metadata_file_bytes=1048576;metadata_total_bytes=8388608;hash_chunk_bytes=65536}
$controlMap=[Collections.Generic.Dictionary[string,object]]::new([StringComparer]::OrdinalIgnoreCase)
$sourceRows=[Collections.Generic.List[object]]::new()
$targetRows=[Collections.Generic.List[object]]::new()
$metadataRows=[Collections.Generic.List[object]]::new()
$metadataBytes=0L;$nativeReady=$false;$destination=$null;$destinationDirectories=@()
$nativeProbe=$null;$probeState=$null;$sealPin=$null;$environmentChanged=$false
$oldTemp=[Environment]::GetEnvironmentVariable('TEMP','Process')
$oldTmp=[Environment]::GetEnvironmentVariable('TMP','Process')

function Closed($value,[string[]]$keys) {
    if($value -isnot [Collections.IDictionary] -or $value.Count -ne $keys.Count){throw 'closed record fields'}
    $expected=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    foreach($key in $keys){[void]$expected.Add($key)}
    foreach($key in $value.Keys){if($key -isnot [string] -or -not $expected.Contains($key)){throw 'unknown/case-aliased record field'}}
}
function Integer($value,[long]$maximum,[long]$minimum=0) {
    if(($value -isnot [int] -and $value -isnot [long]) -or $value -lt $minimum -or $value -gt $maximum){throw 'exact bounded integer'}
}
function PinShape($value,[long]$cap=8388608) {
    Closed $value @('bytes','sha256');Integer $value.bytes $cap
    if($value.sha256 -isnot [string] -or $value.sha256 -cnotmatch '^[0-9a-f]{64}$'){throw 'exact SHA256 pin'}
}
function Canonical([object]$value,[bool]$absolute=$false) {
    if($value -isnot [string] -or $value.Length -eq 0 -or $value.Length -gt 4096 -or $value -cmatch '[^\x20-\x7E]' -or $value.Contains('\')){throw 'canonical ASCII slash path'}
    $tail=$value
    if($absolute){if($value -cnotmatch '^[A-Z]:/'){throw 'local absolute drive path'};$tail=$value.Substring(3)}
    elseif($value.StartsWith('/') -or $value.Contains(':')){throw 'relative path required'}
    $parts=@($tail.Split('/'))
    if($parts.Count -gt 32){throw 'path depth bound'}
    foreach($part in $parts){
        if($part.Length -eq 0 -or $part.Length -gt 255 -or $part -in @('.','..') -or $part -cne $part.Trim() -or $part.EndsWith('.') -or $part -match '[<>:"|?*~]'){throw 'path alias segment'}
        if(($part.Split('.')[0]).ToUpperInvariant() -match '^(CON|PRN|AUX|NUL|CLOCK\$|CONIN\$|CONOUT\$|COM[1-9]|LPT[1-9])$'){throw 'reserved device path'}
    }
    return $value
}
function OrdinaryAncestry([string]$path,[bool]$includeLeaf=$false) {
    $directory=if($includeLeaf){[IO.DirectoryInfo]::new($path)}else{[IO.FileInfo]::new($path).Directory}
    while($null -ne $directory){
        $a=[IO.File]::GetAttributes($directory.FullName)
        if(($a -band [IO.FileAttributes]::ReparsePoint) -or ($a -band [IO.FileAttributes]::Device) -or -not ($a -band [IO.FileAttributes]::Directory)){throw 'ordinary directory ancestry required'}
        $directory=$directory.Parent
    }
}
function OrdinaryFile([string]$path,[bool]$allowSourceHardlink=$false) {
    OrdinaryAncestry $path
    $item=Get-Item -LiteralPath $path -Force -ErrorAction Stop
    if($item -isnot [IO.FileInfo] -or ($item.Attributes -band ([IO.FileAttributes]::ReparsePoint -bor [IO.FileAttributes]::Device -bor [IO.FileAttributes]::Directory))){throw 'ordinary regular file required'}
    if($null -ne $item.LinkType -and (-not $allowSourceHardlink -or $item.LinkType -cne 'HardLink')){throw 'unexpected file link type'}
    return $item
}
function HashOriginal([IO.FileStream]$stream,[long]$cap) {
    Check
    if($stream.Length -gt $cap){throw 'original input byte cap'}
    $length=$stream.Length;$stream.Position=0;$read=0L
    $hash=[Security.Cryptography.IncrementalHash]::CreateHash([Security.Cryptography.HashAlgorithmName]::SHA256)
    try {
        $buffer=[byte[]]::new(65536)
        do{Check;$n=$stream.Read($buffer,0,$buffer.Length);if($n){$read+=$n;if($read -gt $length){throw 'original stream grew'};$hash.AppendData($buffer,0,$n)}}while($n)
        if($read -ne $length -or $stream.Length -ne $length){throw 'original stream length changed'}
        $stream.Position=0
        return @{bytes=$length;sha256=[Convert]::ToHexString($hash.GetHashAndReset()).ToLowerInvariant()}
    } finally {$hash.Dispose()}
}
function SamePin($a,$b) {
    if($a.bytes -ne $b.bytes -or $a.sha256 -cne $b.sha256){throw 'original byte identity mismatch'}
}
function RetainControl([string]$path,$expected) {
    Check;[void](Canonical $path $true);PinShape $expected
    if($controlMap.ContainsKey($path)){SamePin $controlMap[$path].pin $expected;return $controlMap[$path]}
    [void](OrdinaryFile $path)
    $stream=[IO.FileStream]::new($path,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
    $inputs.Add($stream);$fileClosure.closed=$false
    [void](OrdinaryFile $path)
    $pin=HashOriginal $stream 8MB;SamePin $pin $expected
    $row=@{path=$path;stream=$stream;pin=$pin;identity=$null};$controlMap.Add($path,$row)
    if($nativeReady){$row.identity=[PNative.Owner]::FileIdentity($stream.SafeFileHandle)}
    return $row
}
function ReadOriginal($row,[long]$cap=8388608) {
    Check;if($row.stream.Length -gt $cap){throw 'bounded original read'}
    $raw=[byte[]]::new([int]$row.stream.Length);$row.stream.Position=0;$offset=0
    while($offset -lt $raw.Length){Check;$n=$row.stream.Read($raw,$offset,[Math]::Min(65536,$raw.Length-$offset));if($n -le 0){throw 'short original read'};$offset+=$n}
    $row.stream.Position=0;return ,$raw
}
function ReadJson($row) {
    $raw=ReadOriginal $row
    $options=[Text.Json.JsonDocumentOptions]::new();$options.MaxDepth=32
    $doc=[Text.Json.JsonDocument]::Parse([ReadOnlyMemory[byte]]::new($raw),$options)
    try {
        $pending=[Collections.Generic.Stack[object]]::new();$pending.Push($doc.RootElement);$nodes=0
        while($pending.Count){
            Check;$element=$pending.Pop();$nodes++;if($nodes -gt 200000){throw 'JSON node cap'}
            switch($element.ValueKind.ToString()){
                'Object' {$names=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal);foreach($property in $element.EnumerateObject()){if($property.Name.Length -gt 32768 -or -not $names.Add($property.Name)){throw 'JSON duplicate/long key'};$nodes++;if($nodes+$pending.Count -gt 200000){throw 'JSON scheduled node cap'};$pending.Push($property.Value)}}
                'Array' {foreach($item in $element.EnumerateArray()){if($nodes+$pending.Count -ge 200000){throw 'JSON scheduled node cap'};$pending.Push($item)}}
                'String' {if($element.GetString().Length -gt 32768){throw 'JSON string bound'}}
            }
        }
    } finally {$doc.Dispose()}
    return ([Text.Encoding]::UTF8.GetString($raw)|ConvertFrom-Json -AsHashtable -DateKind String)
}
function RefRecord($value,[string]$expectedPath) {
    Closed $value @('path','bytes','sha256');[void](Canonical $value.path)
    if($value.path -cne $expectedPath){throw 'exact retained control reference'}
    $row=RetainControl ($projectRoot+'/'+$value.path) @{bytes=$value.bytes;sha256=$value.sha256}
    return (ReadJson $row)
}
function UtcString($value) {
    if($value -isnot [string] -or $value.Length -gt 64 -or $value -cnotmatch '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,7})?(Z|\+00:00)$'){throw 'explicit UTC string required'}
    $parsed=[DateTimeOffset]::Parse($value,[Globalization.CultureInfo]::InvariantCulture,[Globalization.DateTimeStyles]::None)
    if($parsed.Offset -ne [TimeSpan]::Zero){throw 'explicit UTC string required'};return $parsed.UtcDateTime
}
function AcceptedReview($record,[string]$status) {
    if($record -isnot [Collections.IDictionary] -or $record.status -cne $status -or $record.authors -isnot [array] -or $record.authors.Count -lt 1 -or $record.authors.Count -gt 8 -or $record.reviewer -isnot [string] -or $record.reviewer.Length -eq 0){throw 'review typed identity'}
    foreach($author in $record.authors){if($author -isnot [string] -or $author.Length -eq 0 -or $author.Length -gt 128){throw 'review author scalar'}}
    if($record.authors -ccontains $record.reviewer -or $record.findings -isnot [array] -or $record.findings.Count -ne 0){throw 'independent accepted review'}
    [void](UtcString $record.created_utc)
}
function NativeControls($value) {
    $keys=@('emitted_pe_verified','original_output_identity_retained','loaded_same_pe_bytes','p_limits_query_verified','empty_job_closed')
    Closed $value ($keys+@('helper_identity'))
    foreach($key in $keys){if($value[$key] -isnot [bool] -or -not $value[$key]){throw 'native builder control'}}
    if($value.helper_identity -isnot [string] -or $value.helper_identity -cnotmatch '^[0-9a-f]{16}:[0-9a-f]{32}$'){throw 'native helper identity spelling'}
}
function NewOutput([string]$name) {
    Check
    if($name -cnotmatch '^(claim|origin|seal|caller-return)_[0-9a-f-]{36}\.json$'){throw 'metadata output namespace'}
    $path=$phase.Replace('\','/')+'/'+$name
    OrdinaryAncestry $path
    $stream=[IO.FileStream]::new($path,[IO.FileMode]::CreateNew,[IO.FileAccess]::ReadWrite,[IO.FileShare]::Read)
    $outputs.Add($stream);$fileClosure.closed=$false
    return @{path=$path;stream=$stream;pin=$null;identity=([PNative.Owner]::FileIdentity($stream.SafeFileHandle))}
}
function WriteRecord([string]$name,$value) {
    Check;$raw=[Text.Encoding]::UTF8.GetBytes(($value|ConvertTo-Json -Depth 30 -Compress)+[Environment]::NewLine)
    if($raw.Length -gt 1MB -or $script:metadataBytes+$raw.Length+$journal.bytes -gt 8MB){throw 'metadata output aggregate cap'}
    $row=NewOutput $name;$offset=0
    while($offset -lt $raw.Length){Check;$n=[Math]::Min(65536,$raw.Length-$offset);$row.stream.Write($raw,$offset,$n);$offset+=$n}
    $row.stream.Flush($true);$row.pin=HashOriginal $row.stream 1MB
    if($row.pin.bytes -ne $raw.Length -or $row.pin.sha256 -cne [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($raw)).ToLowerInvariant()){throw 'metadata same-handle readback'}
    $script:metadataBytes+=$raw.Length;$metadataRows.Add($row);return $row.pin
}
function CensusDestination {
    Check;OrdinaryAncestry $destination $true
    $pending=[Collections.Generic.Stack[string]]::new();$pending.Push($destination)
    $files=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
    $dirs=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase);[void]$dirs.Add($destination)
    while($pending.Count){
        Check;$directory=$pending.Pop()
        foreach($entry in [IO.Directory]::EnumerateFileSystemEntries($directory)){
            Check;$path=$entry.Replace('\','/');[void](Canonical $path $true)
            if(-not $path.StartsWith($destination+'/',[StringComparison]::Ordinal)){throw 'destination census escaped'}
            $attributes=[IO.File]::GetAttributes($path)
            if($attributes -band ([IO.FileAttributes]::ReparsePoint -bor [IO.FileAttributes]::Device)){throw 'destination census reparse/device'}
            if($attributes -band [IO.FileAttributes]::Directory){if(-not $dirs.Add($path) -or $dirs.Count -gt 256){throw 'destination directory cap/alias'};$pending.Push($path)}
            else{[void](OrdinaryFile $path);if(-not $files.Add($path) -or $files.Count -gt 256){throw 'destination file cap/alias'}}
        }
    }
    if($files.Count -ne $targetRows.Count -or $dirs.Count -ne $destinationDirectories.Count){throw 'destination census count'}
    foreach($row in $targetRows){if(-not $files.Contains($row.path)){throw 'destination file census missing'}}
    foreach($dir in $destinationDirectories){if(-not $dirs.Contains($dir)){throw 'destination directory census missing'}}
}
function VerifyOriginals {
    Check
    foreach($row in $controlMap.Values){[void](OrdinaryFile $row.path);SamePin (HashOriginal $row.stream 8MB) $row.pin;if([PNative.Owner]::FileIdentity($row.stream.SafeFileHandle) -cne $row.identity){throw 'control original identity drift'}}
    foreach($row in $sourceRows){[void](OrdinaryFile $row.path $true);SamePin (HashOriginal $row.stream 16MB) $row.pin;if([PNative.Owner]::FileIdentity($row.stream.SafeFileHandle) -cne $row.identity){throw 'opaque source identity drift'}}
    foreach($row in $targetRows){[void](OrdinaryFile $row.path);SamePin (HashOriginal $row.stream 16MB) $row.pin;if([PNative.Owner]::FileIdentity($row.stream.SafeFileHandle) -cne $row.identity){throw 'target original identity drift'}}
    foreach($row in $metadataRows){[void](OrdinaryFile $row.path);SamePin (HashOriginal $row.stream 1MB) $row.pin;if([PNative.Owner]::FileIdentity($row.stream.SafeFileHandle) -cne $row.identity){throw 'metadata original identity drift'}}
    CensusDestination
}

try {
    [void](Canonical $Admission.Replace('\','/') $true)
    if([IO.Path]::GetDirectoryName([IO.Path]::GetFullPath($Admission)) -cne [IO.Path]::GetFullPath($phase)){throw 'R admission namespace'}
    $stem=[IO.Path]::GetFileNameWithoutExtension($Admission)
    if($stem -cnotmatch '^admission_([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$'){throw 'R canonical operation filename'}
    $operation=$Matches[1]
    $journal.operation=$operation;$journal.caller_pid=$callerProcess.Id;$journal.creation_filetime=$callerProcess.StartTime.ToUniversalTime().ToFileTimeUtc()
    OrdinaryAncestry ($phase+'/bootstrap_'+$operation+'.jsonl')
    $journal.stream=[IO.FileStream]::new((Join-Path $phase ('bootstrap_'+$operation+'.jsonl')),[IO.FileMode]::CreateNew,[IO.FileAccess]::ReadWrite,[IO.FileShare]::Read)
    $fileClosure.closed=$false
    Journal $journal 'caller_entry'
    $guardRunspace=[Management.Automation.Runspaces.RunspaceFactory]::CreateRunspace();$guardRunspace.Open()
    $guardPowerShell=[Management.Automation.PowerShell]::Create();$guardPowerShell.Runspace=$guardRunspace
    [void]$guardPowerShell.AddScript($guardScript).AddArgument($callerProcess).AddArgument($killAction).AddArgument($originQpc).AddArgument($originUtc).AddArgument($frequency).AddArgument($stopPath).AddArgument($guardState).AddArgument($journal).AddArgument($faultDeadline)
    $guardInvocation=$guardPowerShell.BeginInvoke()
    while(-not $guardState.ready){
        if($guardState.done -or $guardInvocation.IsCompleted -or $null -ne $guardState.error -or (Elapsed) -ge 5){$killAction.Invoke();throw 'R independent guard startup refused'}
        [Threading.Thread]::Sleep(20)
    }
    if((Elapsed) -ge 5 -or $startupDeadline.IsCancellationRequested -or $guardState.second_sample.elapsed_seconds -ge 5){$killAction.Invoke();throw 'late R startup readiness'}
    $startupDeadline.CancelAfter([Threading.Timeout]::Infinite);$startupRegistration.Dispose();$startupDeadline.Dispose();$startupDisarmed=$true
    $samples=@($guardState.first_sample,$guardState.second_sample)
    if(($samples[1].qpc-$samples[0].qpc)/$frequency -lt 0.2){throw 'startup sample spacing'}
    Journal $journal 'startup_ready'
    Check
    if($AdmissionSha256 -cnotmatch '^[0-9a-f]{64}$'){throw 'admission SHA shape'}
    [void](OrdinaryFile $Admission)
    $admissionStream=[IO.FileStream]::new($Admission,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
    $inputs.Add($admissionStream)
    $admissionPin=HashOriginal $admissionStream 8MB
    if($admissionPin.sha256 -cne $AdmissionSha256){throw 'admission original pin'}
    $admissionRow=@{path=$Admission.Replace('\','/');stream=$admissionStream;pin=$admissionPin;identity=$null}
    $controlMap.Add($admissionRow.path,$admissionRow)
    $request=ReadJson $admissionRow
    Closed $request @('schema','stage','operation_id','created_utc','expires_utc','root','caller_runtime','sources','review','adoption','qualification','native_helper','copy_manifest','destination_parent','destination_prefix','limits','scientific_admission')
    if($request.schema -cne 'cho51_r_admission_v1' -or $request.stage -cne 'R' -or $request.root -cne $projectRoot -or $request.operation_id -cne $operation -or ([Guid]::ParseExact($operation,'D')).ToString('D') -cne $operation -or $request.scientific_admission -isnot [bool] -or $request.scientific_admission){throw 'R admission identity/authority'}
    $start=UtcString $request.created_utc;$end=UtcString $request.expires_utc
    if($start -gt $originUtc -or $end -lt $originUtc.AddSeconds(90) -or ($end-$start).TotalSeconds -lt 90 -or ($end-$start).TotalSeconds -gt 900){throw 'original R whole window'}
    Closed $request.limits @($expectedLimits.Keys)
    foreach($key in $expectedLimits.Keys){Integer $request.limits[$key] ([long]$expectedLimits[$key]) ([long]$expectedLimits[$key])}
    if($request.destination_parent -cne 'D:/Aenv/pro3/runs/local_runtimes' -or $request.destination_prefix -cne ('git_'+$operation+'_')){throw 'R exclusive destination scope'}
    [void](Canonical $request.destination_parent $true)
    Closed $request.caller_runtime @('path','bytes','sha256','version')
    [Threading.Monitor]::Enter($guardState.SyncRoot)
    try{$callerPath=$callerProcess.MainModule.FileName.Replace('\','/')}finally{[Threading.Monitor]::Exit($guardState.SyncRoot)}
    if($request.caller_runtime.path -cne $callerPath -or $request.caller_runtime.version -cne $PSVersionTable.PSVersion.ToString() -or -not $PSVersionTable.PSVersion.ToString().StartsWith('7.')){throw 'exact original PowerShell7 runtime'}
    [void](RetainControl $callerPath @{bytes=$request.caller_runtime.bytes;sha256=$request.caller_runtime.sha256})
    Closed $request.sources $requiredSources
    foreach($relative in $requiredSources){[void](Canonical $relative);[void](RetainControl ($projectRoot+'/'+$relative) $request.sources[$relative])}
    $review=RefRecord $request.review ($rPhase+'/source-review.json')
    $adoption=RefRecord $request.adoption ($rPhase+'/contract-adoption.json')
    $qualification=RefRecord $request.qualification ($qPhase+'/root-qualification.json')
    $manifest=RefRecord $request.copy_manifest ($rPhase+'/copy-manifest.json')
    AcceptedReview $review 'ACCEPTED_SOURCE_R1'
    Closed $review.sources $requiredSources
    foreach($relative in $requiredSources){PinShape $review.sources[$relative];SamePin $review.sources[$relative] $request.sources[$relative]}
    Closed $adoption @('schema','status','author','created_utc','source_review_sha256','contract_sha256','qualification_sha256','copy_manifest_sha256','launch_authorized','scientific_admission')
    if($adoption.schema -cne 'cho51_r_adoption_v1' -or $adoption.status -cne 'ADOPTED_R_ONLY' -or $adoption.author -cne 'project_root' -or $adoption.source_review_sha256 -cne $request.review.sha256 -or $adoption.contract_sha256 -cne $request.sources['docs/phase2/cho51_p3_git_materialization_contract_20261029.md'].sha256 -or $adoption.qualification_sha256 -cne $request.qualification.sha256 -or $adoption.copy_manifest_sha256 -cne $request.copy_manifest.sha256){throw 'R adoption exact joins'}
    foreach($key in @('launch_authorized','scientific_admission')){if($adoption[$key] -isnot [bool] -or $adoption[$key]){throw 'R adoption false authority'}}
    if((UtcString $review.created_utc) -gt (UtcString $adoption.created_utc) -or (UtcString $adoption.created_utc) -gt $start){throw 'R review/adoption order'}
    Closed $qualification (@('schema','status','author','created_utc','operation_id','source_review','actual_review','native_helper','test_count','timestamp_controls','native_fault_controls','native_builder_controls')+$falseFlags)
    if($qualification.schema -cne 'cho51_p2q_root_qualification_v1' -or $qualification.status -cne 'QUALIFIED_P2_Q_TESTED_SCOPE' -or $qualification.author -cne 'project_root' -or $qualification.operation_id -cne '9726e95c-1844-49aa-b43f-7dc688052766'){throw 'accepted exact Q qualification'}
    Integer $qualification.test_count 176 176;Integer $qualification.timestamp_controls 8 8;Integer $qualification.native_fault_controls 2 2
    foreach($key in $falseFlags){if($qualification[$key] -isnot [bool] -or $qualification[$key]){throw 'Q qualification no authority'}}
    NativeControls $qualification.native_builder_controls
    $qsource=RefRecord $qualification.source_review ($qPhase+'/source-review.json')
    $qactual=RefRecord $qualification.actual_review ($qPhase+'/actual-review.json')
    SamePin $request.sources[$qPhase+'/source-review.json'] @{bytes=$qualification.source_review.bytes;sha256=$qualification.source_review.sha256}
    SamePin $request.sources[$qPhase+'/actual-review.json'] @{bytes=$qualification.actual_review.bytes;sha256=$qualification.actual_review.sha256}
    SamePin $request.sources[$qPhase+'/root-qualification.json'] @{bytes=$request.qualification.bytes;sha256=$request.qualification.sha256}
    AcceptedReview $qsource 'ACCEPTED_SOURCE_P2Q';AcceptedReview $qactual 'ACCEPTED_P2Q_TESTED_SCOPE'
    if($qsource.reviewer -ceq $qactual.reviewer -or $qsource.authors -ccontains $qactual.reviewer -or $qactual.authors -ccontains $qsource.reviewer -or $qactual.operation_id -cne $qualification.operation_id -or $qactual.source_review_sha256 -cne $qualification.source_review.sha256){throw 'Q distinct actual/source review joins'}
    Integer $qactual.tests_run 176 176;Integer $qactual.timestamp_controls_passed 8 8;Integer $qactual.native_fault_controls_passed 2 2;Integer $qactual.actual_tool_exit_code 0 0
    if($qactual.new_operation_owned_lifecycle_closed -isnot [bool] -or -not $qactual.new_operation_owned_lifecycle_closed){throw 'Q actual owned closure'}
    NativeControls $qactual.native_builder_controls
    foreach($key in $qualification.native_builder_controls.Keys){if($qactual.native_builder_controls[$key] -cne $qualification.native_builder_controls[$key]){throw 'Q native controls join'}}
    if((UtcString $qsource.created_utc) -gt (UtcString $qactual.created_utc) -or (UtcString $qactual.created_utc) -gt (UtcString $qualification.created_utc) -or (UtcString $qualification.created_utc) -gt (UtcString $adoption.created_utc)){throw 'Q qualification time order'}
    foreach($ref in @($request.native_helper,$qualification.native_helper,$qactual.native_helper)){
        Closed $ref @('path','bytes','sha256');if($ref.path -cne $helperRelative){throw 'exact qualified native helper'};PinShape @{bytes=$ref.bytes;sha256=$ref.sha256}
        SamePin @{bytes=$ref.bytes;sha256=$ref.sha256} @{bytes=$request.native_helper.bytes;sha256=$request.native_helper.sha256}
    }
    $helperRow=RetainControl ($projectRoot+'/'+$helperRelative) @{bytes=$request.native_helper.bytes;sha256=$request.native_helper.sha256}
    $helperBytes=ReadOriginal $helperRow
    if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($helperBytes)).ToLowerInvariant() -cne $request.native_helper.sha256){throw 'native exact original load bytes'}
    if($null -ne ('PNative.Owner' -as [type])){throw 'preexisting native helper type refused'}
    [void][Reflection.Assembly]::Load($helperBytes);$nativeReady=$true
    foreach($row in $controlMap.Values){$row.identity=[PNative.Owner]::FileIdentity($row.stream.SafeFileHandle)}
    $journalIdentity=[PNative.Owner]::FileIdentity($journal.stream.SafeFileHandle)
    if($helperRow.identity -cne $qualification.native_builder_controls.helper_identity){throw 'qualified native original file identity'}
    Check
    try{$nativeProbe=[PNative.Owner]::new($originQpc,$originUtc.ToString('o'),$stopPath);if(-not $nativeProbe.LimitsVerified){throw 'qualified empty Job limits'}}
    finally{if($null -ne $nativeProbe){$nativeProbe.Dispose()}}
    $probeState=@{limits_query_verified=$nativeProbe.LimitsVerified;job_empty=$nativeProbe.JobEmpty;job_closed=$nativeProbe.JobClosed;watchdog_joined=$nativeProbe.WatchdogJoined;cleanup_error=$nativeProbe.CleanupError;fault=$nativeProbe.Fault;contains_caller=$false;child_created=$nativeProbe.CreationAttempted}
    if(-not($probeState.limits_query_verified -and $probeState.job_empty -and $probeState.job_closed -and $probeState.watchdog_joined) -or $null -ne $probeState.cleanup_error -or $null -ne $probeState.fault -or $probeState.child_created){throw 'empty Job original closure'}
    $prior=ReadJson $controlMap[$projectRoot+'/runs/coordination/cho51_p3_dependency_prepare_20261029_p1/root-disposition.json']
    $advice=ReadJson $controlMap[$projectRoot+'/'+$rPhase+'/design-advice.json']
    if($prior.status -cne 'FAILED_P2_P_CONSUMED_OWNED_CLOSED' -or $prior.observed_refusal -cne 'regular single-link entry' -or $prior.static_selected_hardlinks -ne 174 -or $advice.status -cne 'NO_DESIGN_BLOCKER_CONDITIONAL'){throw 'R exact predecessor/design context'}
    Closed $manifest @('schema','source_root','files','count','total_bytes','execution_authorized')
    if($manifest.schema -cne 'cho51_r_git_copy_manifest_v1' -or $manifest.source_root -cne $gitRoot -or $manifest.execution_authorized -isnot [bool] -or $manifest.execution_authorized){throw 'opaque materialization manifest identity'}
    Integer $manifest.count 243 243;Integer $manifest.total_bytes 189434327 189434327
    if($manifest.files -isnot [array] -or $manifest.files.Count -ne 243 -or $manifest.files.Count -gt 256){throw 'opaque source count'}
    $relativeNames=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase);$aggregate=0L
    foreach($file in $manifest.files){
        Check;Closed $file @('relative','source','bytes','sha256');[void](Canonical $file.relative);[void](Canonical $file.source $true)
        if($file.source -cne ($gitRoot+'/'+$file.relative) -or -not $relativeNames.Add($file.relative) -or $file.relative -cnotmatch '^(cmd/|mingw64/bin/|mingw64/libexec/git-core/|etc/)'){throw 'opaque source topology/alias'}
        PinShape @{bytes=$file.bytes;sha256=$file.sha256} 16777216
        $aggregate+=$file.bytes;if($aggregate -gt 201326592){throw 'opaque aggregate cap'}
        [void](OrdinaryFile $file.source $true)
        $stream=[IO.FileStream]::new($file.source,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read);$inputs.Add($stream)
        [void](OrdinaryFile $file.source $true)
        $pin=HashOriginal $stream 16MB;SamePin $pin $file
        $sourceRows.Add(@{relative=$file.relative;path=$file.source;stream=$stream;pin=$pin;identity=([PNative.Owner]::FileIdentity($stream.SafeFileHandle))})
    }
    if($aggregate -ne $manifest.total_bytes){throw 'opaque byte total join'}
    $journal.authority_pending=$false;Journal $journal 'R_authority_and_all_sources_verified'
    [void](WriteRecord ('claim_'+$operation+'.json') @{schema='cho51_r_claim_v1';operation_id=$operation;admission_sha256=$AdmissionSha256;origin_utc=$originUtc.ToString('o');origin_qpc=$originQpc;frequency=$frequency;source_count=$sourceRows.Count;source_total_bytes=$aggregate;launch_authorized=$false;scientific_admission=$false})
    $claimCreated=$true
    [void](WriteRecord ('origin_'+$operation+'.json') @{schema='cho51_r_origin_v1';operation_id=$operation;origin_utc=$originUtc.ToString('o');origin_qpc=$originQpc;frequency=$frequency;startup_samples=$samples;caller_version=$PSVersionTable.PSVersion.ToString();caller_pid=$PID;empty_job_probe=$probeState;empty_job_contains_caller=$false;caller_containment='independent_original_process_handle_deadline_and_512MiB_PDH_guard';tool_return_pending=$true;independent_actual_review_pending=$true;launch_authorized=$false;scientific_admission=$false})
    Check;OrdinaryAncestry $request.destination_parent $true
    if($null -eq ([IO.Directory].GetMethods()|Where-Object {$_.Name -ceq 'CreateTempSubdirectory' -and $_.GetParameters().Count -eq 1})){throw 'exclusive BCL temporary directory API unavailable'}
    $environmentChanged=$true
    [Environment]::SetEnvironmentVariable('TEMP',$request.destination_parent,'Process');[Environment]::SetEnvironmentVariable('TMP',$request.destination_parent,'Process')
    if([IO.Path]::GetTempPath().Replace('\','/').TrimEnd('/') -cne $request.destination_parent){throw 'BCL temp path differs from admitted ordinary parent'}
    $created=[IO.Directory]::CreateTempSubdirectory($request.destination_prefix);$destination=$created.FullName.Replace('\','/')
    [void](Canonical $destination $true)
    if($created.Parent.FullName.Replace('\','/') -cne $request.destination_parent -or -not $created.Name.StartsWith($request.destination_prefix,[StringComparison]::Ordinal) -or $created.Name.Length -le $request.destination_prefix.Length){throw 'exclusive destination result identity'}
    OrdinaryAncestry $destination $true
    [Environment]::SetEnvironmentVariable('TEMP',$oldTemp,'Process');[Environment]::SetEnvironmentVariable('TMP',$oldTmp,'Process');$environmentChanged=$false
    $directorySet=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase);[void]$directorySet.Add($destination)
    $destinationIdentities=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    foreach($row in $sourceRows){
        Check;$target=$destination+'/'+$row.relative;[void](Canonical $target $true)
        $parent=([IO.FileInfo]::new($target)).Directory
        $make=[Collections.Generic.Stack[string]]::new()
        while($parent.FullName.Replace('\','/') -cne $destination){
            $p=$parent.FullName.Replace('\','/');if(-not $p.StartsWith($destination+'/',[StringComparison]::Ordinal)){throw 'target parent escaped'}
            if(-not $directorySet.Contains($p)){$make.Push($p)};$parent=$parent.Parent
        }
        while($make.Count){Check;$p=$make.Pop();[void][IO.Directory]::CreateDirectory($p);OrdinaryAncestry $p $true;[void]$directorySet.Add($p)}
        OrdinaryAncestry $target
        $output=[IO.FileStream]::new($target,[IO.FileMode]::CreateNew,[IO.FileAccess]::ReadWrite,[IO.FileShare]::Read);$outputs.Add($output)
        [void](OrdinaryFile $target)
        $identity=[PNative.Owner]::FileIdentity($output.SafeFileHandle)
        if($identity -ceq $row.identity -or -not $destinationIdentities.Add($identity)){throw 'target must be fresh independent native identity'}
        $row.stream.Position=0;$remaining=$row.pin.bytes;$buffer=[byte[]]::new(65536)
        while($remaining -gt 0){Check;$n=$row.stream.Read($buffer,0,[int][Math]::Min(65536,$remaining));if($n -le 0){throw 'opaque source copy short read'};$output.Write($buffer,0,$n);$remaining-=$n}
        Check;if($row.stream.ReadByte() -ne -1){throw 'opaque source copy grew'}
        $row.stream.Position=0;Check;$output.Flush($true);$pin=HashOriginal $output 16MB;SamePin $pin $row.pin
        if([PNative.Owner]::FileIdentity($output.SafeFileHandle) -cne $identity){throw 'target identity changed during copy'}
        [void](OrdinaryFile $target)
        $targetRows.Add(@{path=$target;relative=$row.relative;stream=$output;pin=$pin;identity=$identity})
    }
    $destinationDirectories=@($directorySet)
    VerifyOriginals
    $sealed=@($targetRows|ForEach-Object {@{relative=$_.relative;path=$_.path;bytes=$_.pin.bytes;sha256=$_.pin.sha256;native_identity=$_.identity}})
    $sealPin=WriteRecord ('seal_'+$operation+'.json') @{schema='cho51_r_git_materialization_seal_v1';status='MATERIALIZATION_OBSERVED_REVIEW_PENDING';operation_id=$operation;destination_root=$destination;source_root=$gitRoot;source_manifest=$request.copy_manifest;files=$sealed;count=$targetRows.Count;total_bytes=$aggregate;directories=$destinationDirectories;original_target_handles_retained=$true;fresh_exclusive_root_api='System.IO.Directory.CreateTempSubdirectory';parent_directory_handle_retained=$false;directory_trust='reviewed_local_observer_ordinary_ancestry_checked_before_after_and_final_exact_census';empty_job_contains_caller=$false;input_output_closure_pending=$true;tool_return_pending=$true;independent_actual_review_pending=$true;complete_dependency_closure=$false;abi_qualified=$false;git_execution_qualified=$false;launch_authorized=$false;scientific_admission=$false}
    VerifyOriginals
    Check;$accepted=$true
} catch {
    $callerError=$_.Exception.GetType().Name+': '+$_.Exception.Message
    if($null -ne $journal.stream -and -not $journal.faulted){Journal $journal 'R_caller_error' $callerError}
} finally {
    if($environmentChanged){[Environment]::SetEnvironmentVariable('TEMP',$oldTemp,'Process');[Environment]::SetEnvironmentVariable('TMP',$oldTmp,'Process');$environmentChanged=$false}
    if($claimCreated){
        try {
            [void](WriteRecord ('caller-return_'+$operation+'.json') @{schema='cho51_r_caller_return_v1';operation_id=$operation;provisioning_observed_by_caller=$accepted;error=$callerError;destination_root=$destination;seal=$sealPin;origin_utc=$originUtc.ToString('o');origin_qpc=$originQpc;frequency=$frequency;elapsed_seconds=(Elapsed);input_handle_count=$inputs.Count;output_handle_count=$outputs.Count;native_probe=$probeState;bootstrap_guard=(GuardSnapshot);original_file_closure_pending=$true;tool_return_pending=$true;independent_actual_review_pending=$true;complete_dependency_closure=$false;abi_qualified=$false;git_execution_qualified=$false;launch_authorized=$false;scientific_admission=$false})
            if($accepted){VerifyOriginals}
        } catch {$accepted=$false;$callerError='return publication/final verify: '+$_.Exception.Message}
    }
    $closeErrors=[Collections.Generic.List[string]]::new()
    foreach($stream in $outputs){try{$stream.Dispose()}catch{$closeErrors.Add($_.Exception.Message)}}
    foreach($stream in $inputs){try{$stream.Dispose()}catch{$closeErrors.Add($_.Exception.Message)}}
    $fileClosure.closed=$closeErrors.Count -eq 0
    if(-not $fileClosure.closed){$accepted=$false;$killAction.Invoke();throw ('R original file close uncertainty: '+($closeErrors -join '; '))}
}
Journal $journal 'R_original_payload_handles_closed'
[Threading.Monitor]::Enter($journal.lock)
try {
    if($nativeReady -and [PNative.Owner]::FileIdentity($journal.stream.SafeFileHandle) -cne $journalIdentity){throw 'bootstrap original identity drift'}
    $journal.stream.Flush($true);$journal.stream.Dispose();$journal.closed=$true
} finally {[Threading.Monitor]::Exit($journal.lock)}
StopGuard
$finalGuard=GuardSnapshot
if(-not $finalGuard.joined -or -not $finalGuard.closed -or -not $finalGuard.done -or $null -ne $finalGuard.error -or (Elapsed) -ge 65 -or [DateTime]::UtcNow -ge $originUtc.AddSeconds(90)){$accepted=$false}
$return=@{schema='cho51_r_external_return_v1';operation_id=$operation;provisioning_observed_by_caller=$accepted;error=$callerError;destination_root=$destination;seal=$sealPin;bootstrap_guard=$finalGuard;original_file_handles_closed=($fileClosure.closed -and $journal.closed);bootstrap_journal_closed=$journal.closed;bootstrap_journal_bytes=$journal.bytes;bootstrap_journal_records=$journal.records;empty_job_probe=$probeState;empty_job_contains_caller=$false;child_processes_created=0;compiler_invoked=$false;elapsed_seconds=(Elapsed);tool_return_pending=$true;independent_actual_review_pending=$true;historical_custody_closed=$false;historical_operation_released=$false;historical_retry_allowed=$false;restart_qualified=$false;boundary_qualified=$false;complete_dependency_closure=$false;abi_qualified=$false;git_execution_qualified=$false;launch_authorized=$false;scientific_admission=$false}
$returnText=$return|ConvertTo-Json -Depth 12 -Compress
if([Text.Encoding]::UTF8.GetByteCount($returnText) -gt 1MB){throw 'R external receipt cap'}
$returnText
if(-not $accepted){throw ('R materialization not provisionally observed: '+$callerError)}
} finally {
    # Independent original-handle deadline remains armed through final return.
    if($environmentChanged){[Environment]::SetEnvironmentVariable('TEMP',$oldTemp,'Process');[Environment]::SetEnvironmentVariable('TMP',$oldTmp,'Process')}
    if(-not $fileClosure.closed){$killAction.Invoke();throw 'R original file closure uncertain'}
    if(-not $guardLifecycle.closed){StopGuard}
    if($null -ne $journal.stream -and -not $journal.closed){$journal.stream.Dispose();$journal.closed=$true}
    if(-not $startupDisarmed){$startupDeadline.CancelAfter([Threading.Timeout]::Infinite);$startupRegistration.Dispose();$startupDeadline.Dispose();$startupDisarmed=$true}
    $hardDeadline.CancelAfter([Threading.Timeout]::Infinite);$deadlineRegistration.Dispose();$hardDeadline.Dispose()
    $faultDeadline.CancelAfter([Threading.Timeout]::Infinite);$faultRegistration.Dispose();$faultDeadline.Dispose()
    $callerProcess.Dispose()
}

