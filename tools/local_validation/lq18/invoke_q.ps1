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
$phase=Join-Path $projectRoot 'runs/coordination/cho51_p3_startup_timing_20261101_qd1'
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
# QD has one clock and no Q dispatch. Early caller records stay bounded until
# C08 makes the reviewed native directory API available (implementation amendment).
$qdWatermark=45;$timingJournal=$null;$supervisorTiming=$null
$timingState=@{rows=[Collections.Generic.List[byte[]]]::new();bytes=0L;next=0;normal=0;final=0;failed=$false;terminal=$false;verified=$false;lastq=$originQpc;lastu=$originUtc.Ticks;stack=[Collections.Generic.List[string]]::new();done=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)}
function NewTimingValidator {
    $expected=[Collections.Generic.List[string]]::new()
    foreach($i in 1..11){$s='C'+$i.ToString('00',[Globalization.CultureInfo]::InvariantCulture);$expected.Add($s+'/begin');$expected.Add($s+'/end')}
    $expected.Add('C12/begin')
    foreach($i in 13..21){$s='C'+$i.ToString('00',[Globalization.CultureInfo]::InvariantCulture);$expected.Add($s+'/begin');$expected.Add($s+'/end')}
    $expected.Add('C12/end')
    foreach($i in 22..28){$s='C'+$i.ToString('00',[Globalization.CultureInfo]::InvariantCulture);$expected.Add($s+'/begin');$expected.Add($s+'/end')}
    return @{expected=$expected;position=0;count=0;bytes=0L;normal=0;final=0;lastq=$originQpc;lastu=$originUtc.Ticks;lastgs=0L;verified=$false;failed=$false;secondary=$false;ready=$false;terminal=$false;poisoned=$false}
}
function TimingDecimal($value,[bool]$positive=$false) {
    if($value -isnot [string] -or $value -cnotmatch '^(0|[1-9][0-9]*)$'){throw 'QD canonical decimal string'}
    $n=[long]::Parse($value,[Globalization.NumberStyles]::None,[Globalization.CultureInfo]::InvariantCulture)
    if($positive -and $n -le 0){throw 'QD positive native integer'}
    return $n
}
function ValidateTimingLine([byte[]]$raw,$v) {
    if($v.poisoned){throw 'QD timing validator already refused'}
    try {
        if($raw.Length -lt 3 -or $raw.Length -gt 512 -or $raw[$raw.Length-1] -ne 10 -or $v.terminal -or $v.count -ge 128 -or $v.bytes+$raw.Length -gt 65536){throw 'QD exact line/capacity/terminal'}
        for($i=0;$i -lt $raw.Length;$i++){if($raw[$i] -gt 127 -or $raw[$i] -eq 0 -or $raw[$i] -eq 13 -or ($raw[$i] -eq 10 -and $i -ne $raw.Length-1)){throw 'QD ASCII single LF'}}
        $row=StrictJson ([Text.Encoding]::ASCII.GetString($raw))
        if(($row.v -isnot [int] -and $row.v -isnot [long]) -or $row.v -ne 1){throw 'QD event version'}
        if($row.k -isnot [string]){throw 'QD scalar event kind'}
        $final=$false
        if($v.count -eq 0){
            ClosedRecord $row @('v','k','op','r','n','oq','fq','ou','pp','ah')
            foreach($key in @('k','op','r','n','oq','fq','ou','pp','ah')){if($row[$key] -isnot [string]){throw 'QD scalar header field'}}
            if($row.k -cne 'H' -or $row.op -cne $journal.operation -or $row.r -cne 'C' -or $row.n -cne '0' -or $row.n -isnot [string] -or $row.ah -cne $AdmissionSha256 -or (TimingDecimal $row.oq $true) -ne $originQpc -or (TimingDecimal $row.fq $true) -ne $frequency -or (TimingDecimal $row.ou $true) -ne $originUtc.Ticks -or (TimingDecimal $row.pp $true) -ne $callerProcess.Id){throw 'QD exact original header'}
        } else {
            if((TimingDecimal $row.n) -ne $v.count){throw 'QD contiguous sequence'}
            $q=TimingDecimal $row.q $true;$u=TimingDecimal $row.u $true
            if($q -lt $v.lastq -or $u -lt $v.lastu){throw 'QD backwards native clock'}
            $v.lastq=$q;$v.lastu=$u
            if($row.k -ceq 'T'){
                ClosedRecord $row @('v','k','n','q','u','c','lv')
                foreach($key in @('k','n','q','u','c','lv')){if($row[$key] -isnot [string]){throw 'QD scalar terminal field'}}
                if($row.c -cnotin @('ready_for_original_close','incomplete','journal_fault') -or $row.lv -cnotin @('complete','incomplete','unknown') -or -not $v.ready){throw 'QD terminal tokens/readiness'}
                if($row.c -ceq 'ready_for_original_close'){if($v.failed -or $row.lv -cne 'complete' -or $v.position -ne $v.expected.Count){throw 'QD complete terminal without complete graph'}}
                elseif(-not $v.failed -or $row.lv -ceq 'complete'){throw 'QD incomplete terminal without failure'}
                $final=$true;$v.terminal=$true
            } elseif($row.k -ceq 'E') {
                ClosedRecord $row @('v','k','n','s','e','q','u','a','c','nf','nb','gs')
                foreach($key in @('k','n','s','e','q','u','a','c')){if($row[$key] -isnot [string]){throw 'QD scalar event field'}}
                if($row.s -isnot [string] -or $row.s -cnotmatch '^C(0[1-9]|1[0-9]|2[0-9])$' -or $row.e -cnotin @('begin','end','fail','mark') -or $row.a -cnotin @('pending','verified') -or $row.c -cnotin @('ok','prefix_stop','input','authority','clock','resource','stop','capacity','io','identity','custody','deadline','unknown') -or $null -ne $row.nf -or $null -ne $row.nb){throw 'QD closed caller event fields'}
                if($null -ne $row.gs){$gs=TimingDecimal $row.gs;if($gs -lt $v.lastgs){throw 'QD guard counter regression'};$v.lastgs=$gs}
                $ready=($row.s -ceq 'C29' -and $row.e -ceq 'mark');$final=($ready -or $row.e -ceq 'fail')
                if($v.failed){
                    if($v.ready -or -not $final -or (-not $ready -and ($row.e -cne 'fail' -or $row.c -cne 'io' -or $v.secondary))){throw 'QD failure suffix'}
                    if($ready){$v.ready=$true}else{$v.secondary=$true}
                } elseif($row.e -ceq 'fail') {
                    if($row.c -cin @('ok','prefix_stop')){throw 'QD first failure code'};$v.failed=$true
                } elseif($ready) {
                    if($v.ready -or $row.c -cne 'ok' -or $v.position -ne $v.expected.Count){throw 'QD premature ready mark'};$v.ready=$true
                } else {
                    if($row.c -cne 'ok' -or $v.position -ge $v.expected.Count -or ($row.s+'/'+$row.e) -cne $v.expected[$v.position]){throw 'QD fixed graph order/nesting'}
                    $v.position++
                }
                $verified=($v.verified -or ($row.s -ceq 'C05' -and $row.e -ceq 'end'))
                if($row.a -cne $(if($verified){'verified'}else{'pending'})){throw 'QD authority transition'};$v.verified=$verified
            }else{throw 'QD closed event kind'}
        }
        if($final){if($v.final -ge 6){throw 'QD final capacity'};$v.final++}else{if($v.final -gt 0 -or $v.normal -ge 122){throw 'QD normal capacity/suffix'};$v.normal++}
        $v.count++;$v.bytes+=$raw.Length
    }catch{$v.poisoned=$true;throw}
}
function ValidateTimingReadback([byte[]]$raw) {
    if($raw.Length -lt 1 -or $raw.Length -gt 65536 -or $raw[$raw.Length-1] -ne 10){throw 'QD original readback bound/torn suffix'}
    $v=NewTimingValidator;$begin=0
    for($i=0;$i -lt $raw.Length;$i++){
        if($raw[$i] -eq 10){Check;$length=$i-$begin+1;if($length -gt 512){throw 'QD original record capacity'};$line=[byte[]]::new($length);[Array]::Copy($raw,$begin,$line,0,$length);ValidateTimingLine $line $v;$begin=$i+1}
    }
    if($begin -ne $raw.Length -or -not $v.terminal -or $v.count -ne $timingState.next -or $v.bytes -ne $timingState.bytes){throw 'QD full original event replay'}
    Check
}
$timingValidation=NewTimingValidator
function TimingPut($row,[bool]$final=$false) {
    if($timingState.terminal -or $timingState.next -ge 128 -or ($final -and $timingState.final -ge 6) -or (-not $final -and ($timingState.final -gt 0 -or $timingState.normal -ge 122))){throw 'QD timing capacity/terminal'}
    $row.n=$timingState.next.ToString([Globalization.CultureInfo]::InvariantCulture)
    $raw=[Text.Encoding]::ASCII.GetBytes(($row|ConvertTo-Json -Depth 4 -Compress)+"`n")
    if($raw.Length -gt 512 -or $timingState.bytes+$raw.Length -gt 65536){throw 'QD timing bytes'}
    if($null -eq $timingJournal){if($timingState.next -ge 32 -or $timingState.bytes+$raw.Length -gt 16384){throw 'QD early caller buffer capacity'}}
    ValidateTimingLine $raw $timingValidation
    $timingState.next++;$timingState.bytes+=$raw.Length
    if($final){$timingState.final++}else{$timingState.normal++}
    if($null -eq $timingJournal){$timingState.rows.Add($raw)}else{$timingJournal.Append($raw,$final,$true)}
}
function TimingHeader {
    if($AdmissionSha256 -cnotmatch '^[0-9a-f]{64}$' -or $timingState.next -ne 0){throw 'QD header identity'}
    TimingPut ([ordered]@{v=1;k='H';op=$journal.operation;r='C';n='0';oq=$originQpc.ToString([Globalization.CultureInfo]::InvariantCulture);fq=$frequency.ToString([Globalization.CultureInfo]::InvariantCulture);ou=$originUtc.Ticks.ToString([Globalization.CultureInfo]::InvariantCulture);pp=$callerProcess.Id.ToString([Globalization.CultureInfo]::InvariantCulture);ah=$AdmissionSha256})
}
function TimingStage([string]$stage,[string]$edge,[string]$code='ok') {
    if($timingState.failed -and $edge -cnotin @('fail','mark')){return}
    if($stage -cnotmatch '^C(0[1-9]|1[0-9]|2[0-9])$' -or $edge -cnotin @('begin','end','fail','mark') -or $code -cnotin @('ok','prefix_stop','input','authority','clock','resource','stop','capacity','io','identity','custody','deadline','unknown')){throw 'QD closed timing token'}
    $final=($edge -ceq 'fail' -or $stage -ceq 'C29')
    if($edge -ceq 'begin'){
        if($timingState.done.Contains($stage) -or $timingState.stack.Contains($stage) -or ($timingState.stack.Count -gt 0 -and -not($timingState.stack.Count -eq 1 -and $timingState.stack[0] -ceq 'C12' -and $stage -cmatch '^C(1[3-9]|2[01])$'))){throw 'QD stage nesting/repeat'}
        $timingState.stack.Add($stage)
    } elseif($edge -ceq 'end') {
        if($timingState.stack.Count -eq 0 -or $timingState.stack[$timingState.stack.Count-1] -cne $stage){throw 'QD unmatched stage end'}
        $timingState.stack.RemoveAt($timingState.stack.Count-1);[void]$timingState.done.Add($stage)
        if($stage -ceq 'C05'){$timingState.verified=$true}
    } elseif($edge -ceq 'fail') {$timingState.failed=$true}
    elseif($stage -cne 'C29'){throw 'QD caller mark scope'}
    $q=[Diagnostics.Stopwatch]::GetTimestamp();$u=[DateTime]::UtcNow.Ticks
    if($q -lt $timingState.lastq -or $u -lt $timingState.lastu){throw 'QD timing clock moved backwards'}
    $timingState.lastq=$q;$timingState.lastu=$u
    $authority=if($timingState.verified){'verified'}else{'pending'}
    $gs=if($guardState.samples -gt 0){([long]$guardState.samples).ToString([Globalization.CultureInfo]::InvariantCulture)}else{$null}
    TimingPut ([ordered]@{v=1;k='E';n='0';s=$stage;e=$edge;q=$q.ToString([Globalization.CultureInfo]::InvariantCulture);u=$u.ToString([Globalization.CultureInfo]::InvariantCulture);a=$authority;c=$code;nf=$null;nb=$null;gs=$gs}) $final
}
function TimingOpen {
    $name='timing-caller_'+$journal.operation+'.jsonl';$full=$phase.Replace('\','/')+'/'+$name
    ReserveCallerOutput $full 65536
    $script:timingJournal=[QNative.TimingJournal]::new()
    $timingJournal.Open($full,[Action]{Check},[Action[byte[]]]{param([byte[]]$bytes) ValidateTimingReadback $bytes})
    foreach($raw in $timingState.rows){$timingJournal.Append($raw,$false,$true)}
    $timingState.rows.Clear()
}
function TimingFinish {
    if($null -eq $timingJournal -or $timingJournal.Faulted){return}
    $complete=($accepted -and $finalInputVerified -and $lFinalVerified -and $fileClosure.closed -and -not $timingState.failed -and $timingState.done.Count -eq 28 -and $timingState.stack.Count -eq 0)
    if(-not $complete){$script:accepted=$false}
    if(-not $complete -and -not $timingValidation.failed){TimingStage 'C29' 'fail' 'unknown'}
    $code=if($complete){'ok'}else{'unknown'}
    TimingStage 'C29' 'mark' $code
    $q=[Diagnostics.Stopwatch]::GetTimestamp();$u=[DateTime]::UtcNow.Ticks
    if($q -lt $timingState.lastq -or $u -lt $timingState.lastu){throw 'QD terminal clock'}
    $code=if($complete){'ready_for_original_close'}else{'incomplete'};$lv=if($complete){'complete'}else{'incomplete'}
    TimingPut ([ordered]@{v=1;k='T';n='0';q=$q.ToString([Globalization.CultureInfo]::InvariantCulture);u=$u.ToString([Globalization.CultureInfo]::InvariantCulture);c=$code;lv=$lv}) $true
    $timingState.terminal=$true;$timingJournal.Seal()
}
function TimingReference {
    if($null -eq $timingJournal -or -not $timingJournal.Sealed){return $null}
    return @{path='D:/Aenv/pro3/runs/coordination/cho51_p3_startup_timing_20261101_qd1/timing-caller_'+$journal.operation+'.jsonl';bytes=$timingJournal.Bytes;sha256=$timingJournal.Sha256;native_identity=$timingJournal.Identity;records=$timingJournal.Records;sealed=$timingJournal.Sealed;original_file_closed=$timingJournal.FileClosed;original_ancestry_closed=$timingJournal.AncestorsClosed}
}
function ValidateSupervisorTiming($value) {
    ClosedRecord $value @('path','bytes','sha256','native_identity','records','sealed','original_file_closed','original_ancestry_closed')
    if($value.path -isnot [string]){throw 'QD scalar supervisor journal path'}
    if($value.path -cne ('D:/Aenv/pro3/runs/coordination/cho51_p3_startup_timing_20261101_qd1/timing-supervisor_'+$operation+'.jsonl') -or $value.sha256 -isnot [string] -or $value.sha256 -cnotmatch '^[0-9a-f]{64}$'){throw 'QD supervisor journal pin'}
    foreach($key in @('bytes','records')){if(($value[$key] -isnot [int] -and $value[$key] -isnot [long]) -or $value[$key] -lt 1){throw 'QD supervisor journal integer'}}
    if($value.bytes -gt 65536 -or $value.records -ne 42){throw 'QD supervisor journal capacity/complete sequence'}
    foreach($key in @('sealed','original_file_closed','original_ancestry_closed')){if($value[$key] -isnot [bool] -or -not $value[$key]){throw 'QD supervisor journal final closure'}}
    ClosedRecord $value.native_identity @('schema','volume_serial','file_id','volume_kind','filesystem')
    $id=$value.native_identity
    foreach($key in @('schema','volume_kind','filesystem','volume_serial','file_id')){if($id[$key] -isnot [string]){throw 'QD scalar native identity field'}}
    if($id.schema -cne 'cho51_lv_native_identity_v1' -or $id.volume_kind -cne 'local_fixed' -or $id.filesystem -cne 'NTFS' -or $id.volume_serial -isnot [string] -or $id.volume_serial -cnotmatch '^[0-9a-f]{16}$' -or $id.volume_serial -ceq '0000000000000000' -or $id.file_id -isnot [string] -or $id.file_id -cnotmatch '^[0-9a-f]{32}$' -or $id.file_id -ceq '00000000000000000000000000000000'){throw 'QD supervisor native journal identity'}
}
function FinalPublicationClock {
    $q=[Diagnostics.Stopwatch]::GetTimestamp();$u=[DateTime]::UtcNow
    return ($q -ge $originQpc -and ($q-$originQpc) -lt (55L*$frequency) -and $u -ge $originUtc -and $u -lt $originUtc.AddSeconds(55))
}
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


function ValidateQDRequest($request) {
    ClosedRecord $request @('schema','stage','operation_id','created_utc','expires_utc','root','python','runtime','caller_runtime','sources','review','adoption','predecessor','limits','modes','expected_tests','forbidden','scientific_admission','compiler','native_compiler','bootstrap_qualification','bootstrap_controls','purpose','stop_point','timing')
    foreach($key in @('schema','stage','purpose','stop_point','root')){if($request[$key] -isnot [string]){throw 'QD scalar authority identity'}}
    if($request.schema -cne 'cho51_startup_timing_admission_v1' -or $request.stage -cne 'QD' -or $request.purpose -cne 'QD_STARTUP_PREFIX_ONLY' -or $request.stop_point -cne 'BEFORE_MODE_LOOP' -or $request.scientific_admission -isnot [bool] -or $request.scientific_admission){throw 'closed QD-only authority'}
    if($request.operation_id -isnot [string] -or $request.operation_id -cnotmatch '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'){throw 'canonical QD operation'}
    $timing=$request.timing
    ClosedRecord $timing @('design_sha256','format_sha256','stages_sha256','caller_name','supervisor_name','records','record_bytes','journal_bytes','prefix_seconds','verification_seconds','publication_seconds')
    $expected=@{design_sha256='948eb50a0bc4176f9f07adc70e033304131ab3311f59487b9d84ce78425a7d68';format_sha256='4c46130c2d52395e6fd17a01ba8d8fa7c0e7a025dd10cc89cff4fa9161dcfd76';stages_sha256='ac449ef41d3c3537a4ebd3265262199d093be2f40454618525c9050651e38c38';caller_name='timing-caller_'+$request.operation_id+'.jsonl';supervisor_name='timing-supervisor_'+$request.operation_id+'.jsonl'}
    foreach($key in $expected.Keys){if($timing[$key] -isnot [string] -or $timing[$key] -cne $expected[$key]){throw 'QD timing identity'}}
    $numbers=@{records=128;record_bytes=512;journal_bytes=65536;prefix_seconds=45;verification_seconds=53;publication_seconds=55}
    foreach($key in $numbers.Keys){if(($timing[$key] -isnot [int] -and $timing[$key] -isnot [long]) -or $timing[$key] -ne $numbers[$key]){throw 'QD fixed timing cap'}}
    $names=@('fixed_supplied_case','closed_schema_and_types','fixed_selection','raw_pin_before_parse','historical_descriptor','full_page_and_index','strict_json','origin_is_not_custody','full_field_traversal','parent_identity','bom_crlf_null_spans','extra_node_changes_count','comparison_has_six_fields','distinct_observation_identities','semantics_stay_unresolved','conservation','forbidden_products','report_schema_is_not_state','safe_parser_refusal','source_and_node_bounds','encoder_bound','report_is_bounded','raw_assets_counted','guard_refusal','deterministic_immutable','self_certified_pin_refused','refusal_has_no_report','no_custody_grant','no_progress_state','exact_probe_roster','original_kernel_limit','all_authority_false')
    if($request.expected_tests -isnot [array] -or $request.expected_tests.Count -ne 32){throw 'QD retained exact probe roster'}
    for($i=0;$i -lt 32;$i++){$name='tools.local_validation.lplan15.test_compiler.SourceProbeTests.test_rs'+($i+1).ToString('00',[Globalization.CultureInfo]::InvariantCulture)+'_'+$names[$i];if($request.expected_tests[$i] -isnot [string] -or $request.expected_tests[$i] -cne $name){throw 'QD held probe identity'}}
    $arrays=@{modes=@('suite','native-transient','native-overflow','native-badreason','native-badutf16','native-pathbound','badframe','stall');forbidden=@('candidate_imports','third_party_imports','numerical_work','data_or_weights','network','git','unowned_processes','historical_launcher_replay');bootstrap_controls=@('accepted','bad_identity')}
    foreach($key in $arrays.Keys){$actual=$request[$key];$expected=$arrays[$key];if($actual -isnot [array] -or $actual.Count -ne $expected.Count){throw 'QD closed obligation/effect array'};for($i=0;$i -lt $expected.Count;$i++){if($actual[$i] -isnot [string] -or $actual[$i] -cne $expected[$i]){throw 'QD exact obligation/effect identity'}}}
    $limits=@{whole_seconds=90;work_seconds=60;cleanup_seconds=5;process_mib=512;job_mib=768;parent_mib=512;startup_ram_gib=4;active_ram_gib=4;disk_gib=20;frame_bytes=1048576;stream_bytes=1048576;threads=1;gpu_visible=$false}
    ClosedRecord $request.limits ([string[]]@($limits.Keys))
    foreach($key in $limits.Keys){$value=$request.limits[$key];if($key -ceq 'gpu_visible'){if($value -isnot [bool] -or $value){throw 'QD hidden GPU'}}elseif(($value -isnot [int] -and $value -isnot [long]) -or $value -ne $limits[$key]){throw 'QD exact unchanged resource scalar'}}
}
# This file is textually embedded in both reviewed callers, not independently
# executed from a pathname. Kept as the reviewed source comparison reference.
function LoadReviewedNativeBootstrap([string]$Role,[string]$Case='accepted') {
    $pin=PinBytes $Admission
    if($pin.sha256 -cne $AdmissionSha256 -or $pin.bytes -gt 1MB){throw 'bootstrap admission pin'}
    $request=ReadPinnedJson @{path=[IO.Path]::GetFullPath($Admission).Replace('\','/');bytes=$pin.bytes;sha256=$pin.sha256}
    if($Role -cnotin @('QD','P_Q_CONTROL')){throw 'QD-only bootstrap role; P disabled'}
    ValidateQDRequest $request
    $stage='QD'
    if($request.operation_id -cne $journal.operation -or $request.root -cne $projectRoot){throw 'bootstrap current stage authority'}
    AdmissionWindow $request.created_utc $request.expires_utc $originUtc
    $controls=@{}
    foreach($key in @('review','adoption')){
        $r=$request[$key];ClosedRecord $r @('path','bytes','sha256')
        $leaf=if($key -ceq 'review'){'source-review.json'}else{'contract-adoption.json'}
        $expected=if($stage -ceq 'P'){$phase.Replace('\','/')+'/'+$leaf}else{$leaf}
        $relative=if($stage -ceq 'P'){'runs/coordination/cho51_p3_startup_timing_20261101_p_disabled/'+$leaf}else{$leaf}
        if($r.path -cne $relative){throw 'bootstrap current review namespace'}
        $controls[$key]=ReadPinnedJson @{path=$phase.Replace('\','/')+'/'+$leaf;bytes=$r.bytes;sha256=$r.sha256}
    }
    $review=$controls.review;$adoption=$controls.adoption
    $status='ACCEPTED_SOURCE_QD1'
    if($review.status -cne $status -or $review.reviewer -isnot [string] -or $review.reviewer -cnotmatch '^[a-z][a-z0-9_-]{0,63}$' -or $review.authors -isnot [array] -or $review.authors.Count -lt 1 -or $review.authors -ccontains $review.reviewer -or $review.findings -isnot [array] -or $review.findings.Count -ne 0 -or $review.sources.Count -ne $request.sources.Count){throw 'bootstrap current independent source review'}
    foreach($row in $request.sources.GetEnumerator()){
        if(-not $review.sources.ContainsKey($row.Key) -or $review.sources[$row.Key].bytes -ne $row.Value.bytes -or $review.sources[$row.Key].sha256 -cne $row.Value.sha256){throw 'bootstrap current reviewed sources'}
    }
    $contract='docs/phase2/cho51_p3_qd_contract_20261101.md'
    if($adoption.author -cne 'project_root' -or $adoption.status -cne ('ADOPTED_'+$stage+'_ONLY') -or $adoption.source_review_sha256 -cne $request.review.sha256 -or $adoption.supplement_sha256 -cne $request.sources[$contract].sha256 -or $adoption.bootstrap_qualification_sha256 -cne $request.bootstrap_qualification.sha256){throw 'bootstrap current scoped adoption'}
    if((UtcString $review.created_utc) -gt (UtcString $adoption.created_utc) -or (UtcString $adoption.created_utc) -gt (UtcString $request.created_utc)){throw 'bootstrap current review/adoption order'}
    foreach($key in @('historical_custody_closed','historical_operation_released','historical_retry_allowed','restart_qualified','boundary_qualified','complete_dependency_closure','launch_authorized','scientific_admission')){if($adoption[$key] -isnot [bool] -or $adoption[$key]){throw 'bootstrap current scope expansion'}}
    $relative='tools/local_validation/lp18/native_bootstrap.ps1';$modulePin=$request.sources[$relative]
    $rawRef=@{path=$projectRoot+'/'+$relative;bytes=$modulePin.bytes;sha256=$modulePin.sha256}
    $pinned=PinBytes $rawRef.path
    if($pinned.bytes -ne $rawRef.bytes -or $pinned.sha256 -cne $rawRef.sha256 -or $pinned.bytes -gt 1MB){throw 'shared bootstrap exact reviewed module'}
    $stream=$inputs[$inputs.Count-1];$reader=[IO.StreamReader]::new($stream,[Text.UTF8Encoding]::new($false,$true),$false,65536,$true)
    try{$source=$reader.ReadToEnd()}finally{$reader.Dispose();$stream.Position=0}
    # The current independent review and Root adoption were checked before this
    # execution. Source strings are never accepted solely on an admission pin.
    . ([scriptblock]::Create($source))
    if($Role -cnotin @('QD','P_Q_CONTROL')){throw 'bootstrap role drift before native initialization'}
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
    if(([Diagnostics.Stopwatch]::GetTimestamp()-$originQpc) -ge ([long]$qdWatermark*$frequency) -or [DateTime]::UtcNow -ge $originUtc.AddSeconds($qdWatermark)){throw 'QD original-clock watermark'}
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
    return @{reference=@{path='runs/coordination/cho51_p3_startup_timing_20261101_qd1/'+$name;bytes=$raw.Length;sha256=$sha};native_identity=$identity;stream=$stream}
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
    TimingHeader
    TimingStage 'C01' 'begin'
    $bootstrapOwner=LoadReviewedNativeBootstrap 'QD';
    TimingStage 'C01' 'end'
    TimingStage 'C02' 'begin'
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
    TimingStage 'C02' 'end'
    TimingStage 'C03' 'begin'
    $initialPrivate=$samples[0].caller_private_bytes
    if(($samples[1].qpc-$samples[0].qpc)/$frequency -lt 0.2){throw 'independent startup sample spacing'}
    Check
    if([IO.Path]::GetDirectoryName([IO.Path]::GetFullPath($Admission)) -ne [IO.Path]::GetFullPath($phase)){throw 'admission location'}
    $pin=PinBytes $Admission
    if($pin.sha256 -cne $AdmissionSha256 -or $pin.bytes -gt 8MB){throw 'admission caller hash'}
    $request=[IO.File]::ReadAllText($Admission)|ConvertFrom-Json -AsHashtable -DateKind String;$operation=$request.operation_id
    ValidateQDRequest $request
    $windowOperands=@{created_literal=$request.created_utc;expires_literal=$request.expires_utc;created_utc=(UtcString $request.created_utc).ToString('o');expires_utc=(UtcString $request.expires_utc).ToString('o');original_utc=$originUtc.ToString('o');original_deadline_utc=$originUtc.AddSeconds(90).ToString('o')}
    Journal $journal 'window_operands' ($windowOperands|ConvertTo-Json -Compress)
    AdmissionWindow $request.created_utc $request.expires_utc $originUtc
    TimingStage 'C03' 'end'
    TimingStage 'C04' 'begin'
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
    TimingStage 'C04' 'end'
    TimingStage 'C05' 'begin'
    foreach($key in @('review','adoption')){
        $ref=$request[$key];$expected=if($key -eq 'review'){'source-review.json'}else{'contract-adoption.json'}
        if($ref.path -cne $expected){throw 'review path'}
        $a=PinBytes (Join-Path $phase $ref.path)
        if($a.bytes -ne $ref.bytes -or $a.sha256 -cne $ref.sha256){throw 'review/adoption pin'}
    }
    $review=[IO.File]::ReadAllText((Join-Path $phase 'source-review.json'))|ConvertFrom-Json -AsHashtable -DateKind String
    $adoption=[IO.File]::ReadAllText((Join-Path $phase 'contract-adoption.json'))|ConvertFrom-Json -AsHashtable -DateKind String
    if($review.status -cne 'ACCEPTED_SOURCE_QD1' -or $review.authors -contains $review.reviewer -or $adoption.status -cne 'ADOPTED_QD_ONLY' -or $adoption.source_review_sha256 -cne $request.review.sha256 -or $review.sources.Count -ne $request.sources.Count){throw 'independent review/adoption'}
    foreach($row in $request.sources.GetEnumerator()){
        if(-not $review.sources.ContainsKey($row.Key) -or $review.sources[$row.Key].bytes -ne $row.Value.bytes -or $review.sources[$row.Key].sha256 -cne $row.Value.sha256){throw 'reviewed source mismatch'}
    }
    if($adoption.contract_sha256 -cne $request.sources['docs/phase2/cho51_p3_local_validation_contract_20261029.md'].sha256 -or $adoption.design_review_sha256 -cne $request.sources['runs/coordination/cho51_p3_local_validation_design_20261029_v1/design-review.json'].sha256 -or [DateTimeOffset]::Parse($adoption.created_utc) -gt [DateTimeOffset]::Parse($request.created_utc)){throw 'adoption joins/order'}
    if($adoption.schema -cne 'cho51_q_contract_adoption_v2' -or $adoption.supplement_sha256 -cne $request.sources['docs/phase2/cho51_p3_qd_contract_20261101.md'].sha256){throw 'LQ1 supplement adoption'}
    foreach($key in @('historical_custody_closed','historical_operation_released','historical_retry_allowed','restart_qualified','boundary_qualified','complete_dependency_closure','launch_authorized','scientific_admission')){
        if($adoption[$key] -isnot [bool] -or $adoption[$key]){throw 'adoption authority'}
    }
    $journal.authority_pending=$false;Journal $journal 'authority_verified'
    TimingStage 'C05' 'end'
    # Admitted Q effect: compile exact verified C# bytes in memory through the
    # pinned PowerShell/.NET compiler. No OutputAssembly or compiler subprocess.
    WriteRecord ('claim_'+$operation+'.json') @{schema='cho51_startup_timing_external_claim_v1';diagnostic_outcome='incomplete';diagnostic_prefix_complete=$false;timing=@{caller=$null;supervisor=$null};required_q_obligations_complete=$false;qualification_accepted=$false;operation_id=$operation;admission_sha256=$AdmissionSha256;origin_utc=$originUtc.ToString('o');origin_qpc=$originQpc;frequency=$frequency}
    $claimCreated=$true
    TimingStage 'C06' 'begin'
    $timestampControls=TimestampControls
    if($timestampControls.Count -ne 8 -or @($timestampControls.Values|Where-Object {$_ -isnot [bool] -or -not $_}).Count -ne 0){throw 'timestamp control outcomes'}
    WriteRecord ('timestamp-controls_'+$operation+'.json') @{schema='cho51_q_timestamp_controls_v1';operation_id=$operation;controls=$timestampControls;culture_exercised='ar-SA';actual_window_operands=$windowOperands;historical_custody_closed=$false;historical_operation_released=$false;historical_retry_allowed=$false;restart_qualified=$false;boundary_qualified=$false;complete_dependency_closure=$false;launch_authorized=$false;scientific_admission=$false}
    TimingStage 'C06' 'end'
    TimingStage 'C07' 'begin'
    $helper=[IO.File]::ReadAllBytes((Join-Path $projectRoot 'tools/local_validation/lq18/caller_native.cs'))
    if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($helper)).ToLowerInvariant() -cne $request.sources['tools/local_validation/lq18/caller_native.cs'].sha256){throw 'helper same-byte pin'}
    Check

    foreach($row in $request.compiler.files.GetEnumerator()){
        $a=PinBytes $row.Key
        if($a.bytes -ne $row.Value.bytes -or $a.sha256 -cne $row.Value.sha256){throw 'compiler pin'}
    }
    $expectedCompiler=@(Get-ChildItem -LiteralPath (Join-Path $PSHOME 'ref') -File -Filter '*.dll'|ForEach-Object {$_.FullName.Replace('\','/')})+@(($PSHOME.Replace('\','/')+'/Microsoft.CodeAnalysis.dll'),($PSHOME.Replace('\','/')+'/Microsoft.CodeAnalysis.CSharp.dll'))
    if($request.compiler.root -cne $PSHOME.Replace('\','/') -or @($expectedCompiler|Where-Object {-not $request.compiler.files.ContainsKey($_)}).Count -ne 0 -or $expectedCompiler.Count -ne $request.compiler.files.Count){throw 'exact compiler recipe'}

    TimingStage 'C07' 'end'
    TimingStage 'C08' 'begin'
    Journal $journal 'compiler_begin'
    Add-Type -TypeDefinition ([Text.Encoding]::UTF8.GetString($helper)) -Language CSharp -ErrorAction Stop
    Check
    Journal $journal 'compiler_return'
    TimingStage 'C08' 'end'
    TimingOpen
    TimingStage 'C09' 'begin'

    $builderPath=Join-Path $projectRoot 'tools/local_validation/lp18/build_native.ps1'
    $builderBytes=[IO.File]::ReadAllBytes($builderPath)
    if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($builderBytes)).ToLowerInvariant() -cne $request.sources['tools/local_validation/lp18/build_native.ps1'].sha256){throw 'builder same-byte pin'}
    . ([scriptblock]::Create([Text.Encoding]::UTF8.GetString($builderBytes)))
    $pSource=[IO.File]::ReadAllBytes((Join-Path $projectRoot 'tools/local_validation/lp18/caller_native.cs'))
    if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($pSource)).ToLowerInvariant() -cne $request.sources['tools/local_validation/lp18/caller_native.cs'].sha256){throw 'P helper same-byte pin'}
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
    $nativeArtifact=@{path='runs/coordination/cho51_p3_startup_timing_20261101_qd1/native-helper_'+$operation+'.dll';bytes=$pe.Length;sha256=$peSha}
    $callerArtifacts.Add(@{role='helper';reference=$nativeArtifact;native_identity=$peIdentity;stream=$peStream})
    $builderControls=@{emitted_pe_verified=$true;original_output_identity_retained=$true;loaded_same_pe_bytes=$true;p_limits_query_verified=$true;empty_job_closed=$true;l_two_process_limits_query_verified=$true;l_empty_job_closed=$true;l_invalid_process_count_refused=$invalidProcessCount;helper_identity=$peIdentity}
    WriteRecord ('native-build_'+$operation+'.json') @{schema='cho51_p2_native_build_v1';operation_id=$operation;native_helper=$nativeArtifact;controls=$builderControls;source_sha256=$request.sources['tools/local_validation/lp18/caller_native.cs'].sha256;compiler=$request.compiler;launch_authorized=$false;scientific_admission=$false}
    Journal $journal 'native_builder_return'
    TimingStage 'C09' 'end'
    TimingStage 'C10' 'begin'

    # Exact Q-only running-schema query; no returned target host is loaded.
    Check
    $planRelative='tools/local_validation/lp18/api_query_plan.json'
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
    TimingStage 'C10' 'end'
    TimingStage 'C11' 'begin'
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

    TimingStage 'C11' 'end'
    TimingStage 'C12' 'begin'
    $lBuilderPath=Join-Path $projectRoot 'tools/local_validation/lq18/build_l_native.ps1'
    $lBuilderBytes=[IO.File]::ReadAllBytes($lBuilderPath)
    if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($lBuilderBytes)).ToLowerInvariant() -cne $request.sources['tools/local_validation/lq18/build_l_native.ps1'].sha256){throw 'L native builder pin'}
    . ([scriptblock]::Create([Text.Encoding]::UTF8.GetString($lBuilderBytes)))
    $lBundle=BuildLNative
    TimingStage 'C12' 'end'
    TimingStage 'C22' 'begin'
    # Both controls keep the original Q clock and precede the main supervisor.
    $controlPath=$projectRoot+'/tools/local_validation/lq18/bootstrap_controls.ps1'
    $controlPin=PinBytes $controlPath
    if($controlPin.bytes -ne $request.sources['tools/local_validation/lq18/bootstrap_controls.ps1'].bytes -or $controlPin.sha256 -cne $request.sources['tools/local_validation/lq18/bootstrap_controls.ps1'].sha256){throw 'bootstrap controls reviewed source pin'}
    $controlStream=$inputs[$inputs.Count-1];$controlReader=[IO.StreamReader]::new($controlStream,[Text.UTF8Encoding]::new($false,$true),$false,65536,$true)
    try{$controlText=$controlReader.ReadToEnd()}finally{$controlReader.Dispose();$controlStream.Position=0}
    . ([scriptblock]::Create($controlText))
    $bootstrapControls=RunBootstrapControls
    TimingStage 'C22' 'end'
    TimingStage 'C23' 'begin'
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
    TimingStage 'C23' 'end'
    TimingStage 'C24' 'begin'
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
    $command=@('-I','-S','-B','-X',('pycache_prefix='+$cache),'-c',$bootstrap,(Join-Path $projectRoot 'tools/local_validation/lq18/supervisor.py'),$request.sources['tools/local_validation/lq18/supervisor.py'].sha256,$Admission,$AdmissionSha256,$originUtc.ToString('o'),$originQpc.ToString(),$frequency.ToString(),$apiSha,$apiIdentity,$apiMapping.bytes.ToString(),$lBundle.reference.sha256,$lBundle.native_identity,$lBundle.reference.bytes.ToString())
    Check;if((Elapsed) -ge 45){throw 'insufficient remaining work'}
    TimingStage 'C24' 'end'
    TimingStage 'C25' 'begin'
    Journal $journal 'supervisor_dispatch'
    # Supervisor enforces45 before prefix-stop. Caller waits for its final53/55 closure.
    $qdWatermark=53
    $owner.Start($request.python,[string[]]$command,$projectRoot)
    while(-not $owner.Poll()){Start-Sleep -Milliseconds 50}
    $supervisorExit=$owner.ExitCode()
    $owner.Dispose()
    $outText=$owner.StdoutText();$errText=$owner.StderrText()
    if($supervisorExit -ne 0){throw 'supervisor exit refused'}
    $ret=StrictJson $outText
    ClosedRecord $ret @('schema','operation_id','accepted_by_supervisor','error','handle_closure','api_mapping','api_mapping_native_identity','native_diagnostic','native_diagnostic_native_identity','caller_artifact_capabilities','resources','output_allocation','diagnostic_outcome','diagnostic_prefix_complete','timing','required_q_obligations_complete','qualification_accepted','historical_custody_closed','historical_operation_released','historical_retry_allowed','restart_qualified','boundary_qualified','complete_dependency_closure','launch_authorized','scientific_admission')
    foreach($key in @('schema','operation_id','diagnostic_outcome','api_mapping_native_identity','native_diagnostic_native_identity')){if($ret[$key] -isnot [string]){throw 'QD scalar return identity'}}
    ClosedRecord $ret.handle_closure @('inputs','outputs','output_state')
    if($ret.handle_closure.output_state -isnot [string] -or $ret.handle_closure.output_state -cne 'closed'){throw 'QD scalar original output closure state'}
    foreach($key in @('api_mapping','native_diagnostic')){
        $ref=$ret[$key];ClosedRecord $ref @('path','bytes','sha256')
        if($ref.path -isnot [string] -or $ref.sha256 -isnot [string] -or $ref.sha256 -cnotmatch '^[0-9a-f]{64}$' -or ($ref.bytes -isnot [int] -and $ref.bytes -isnot [long]) -or $ref.bytes -lt 1 -or $ref.bytes -gt 1MB){throw 'QD scalar artifact reference'}
    }
    if($ret.caller_artifact_capabilities -isnot [array] -or $ret.caller_artifact_capabilities.Count -ne 3){throw 'QD exact capability array'}
    foreach($cap in $ret.caller_artifact_capabilities){
        ClosedRecord $cap @('role','path','bytes','sha256','native_identity','read_share')
        foreach($key in @('role','path','sha256','native_identity')){if($cap[$key] -isnot [string]){throw 'QD scalar capability identity'}}
        foreach($key in @('bytes','read_share')){if($cap[$key] -isnot [int] -and $cap[$key] -isnot [long]){throw 'QD exact capability integer'}}
    }
    foreach($flag in @('historical_custody_closed','historical_operation_released','historical_retry_allowed','restart_qualified','boundary_qualified','complete_dependency_closure','launch_authorized','scientific_admission')){if($ret[$flag] -isnot [bool] -or $ret[$flag]){throw 'QD cannot expand authority'}}
    if($null -ne $ret.error){throw 'QD supervisor error'}
    if($ret.api_mapping.path -cne $apiMapping.path -or $ret.api_mapping.bytes -ne $apiMapping.bytes -or $ret.api_mapping.sha256 -cne $apiMapping.sha256 -or $ret.api_mapping_native_identity -cne $apiIdentity){throw 'Q accepted mapping original receipt join'}
    if($ret.native_diagnostic.path -cne $nativeDiagnostic.path -or $ret.native_diagnostic.bytes -ne $nativeDiagnostic.bytes -or $ret.native_diagnostic.sha256 -cne $nativeDiagnostic.sha256 -or $ret.native_diagnostic_native_identity -cne $diagnosticIdentity){throw 'Q accepted diagnostic original receipt join'}
    if($ret.caller_artifact_capabilities.Count -ne 3){throw 'three returned caller artifact capabilities'}
    foreach($item in $callerArtifacts){
        $cap=@($ret.caller_artifact_capabilities|Where-Object {$_.role -ceq $item.role})
        if($cap.Count -ne 1 -or $cap[0].path -cne ($projectRoot+'/'+$item.reference.path) -or $cap[0].bytes -ne $item.reference.bytes -or $cap[0].sha256 -cne $item.reference.sha256 -or $cap[0].native_identity -cne $item.native_identity -or $cap[0].read_share -ne 3){throw 'caller artifact exact capability join'}
    }
    if($ret.schema -cne 'cho51_startup_timing_supervisor_return_v1' -or $ret.operation_id -cne $operation -or $ret.accepted_by_supervisor -isnot [bool] -or $ret.accepted_by_supervisor -or $ret.diagnostic_prefix_complete -isnot [bool] -or -not $ret.diagnostic_prefix_complete -or $ret.diagnostic_outcome -cne 'prefix_pending_review' -or $ret.required_q_obligations_complete -isnot [bool] -or $ret.required_q_obligations_complete -or $ret.qualification_accepted -isnot [bool] -or $ret.qualification_accepted -or $ret.handle_closure.inputs -isnot [bool] -or -not $ret.handle_closure.inputs -or $ret.handle_closure.outputs -isnot [bool] -or -not $ret.handle_closure.outputs){throw 'QD prefix return/closure; never Q acceptance'}
    ClosedRecord $ret.timing @('caller','supervisor')
    if($null -ne $ret.timing.caller){throw 'supervisor cannot witness caller timing close'}
    ValidateSupervisorTiming $ret.timing.supervisor
    $supervisorTiming=$ret.timing.supervisor
    ClosedRecord $ret.output_allocation @('supervisor_files','supervisor_bytes','supervisor_file_cap','supervisor_byte_cap','fixture_files','fixture_bytes','fixture_largest')
    foreach($key in $ret.output_allocation.Keys){$number=$ret.output_allocation[$key];if(($number -isnot [int] -and $number -isnot [long]) -or $number -lt 0){throw 'exact output allocation integer'}}
    $allocation=$ret.output_allocation
    if($allocation.supervisor_files -ne 3 -or $allocation.supervisor_bytes -ne 1118208 -or $allocation.fixture_files -ne 0 -or $allocation.fixture_bytes -ne 0 -or $allocation.fixture_largest -ne 0){throw 'QD exact three-output reservation; no suite fixtures'}
    if($allocation.supervisor_file_cap -ne 40 -or $allocation.supervisor_byte_cap -ne 8MB -or $allocation.supervisor_files -gt 40 -or $allocation.supervisor_bytes -gt 8MB -or $allocation.fixture_files -gt 160 -or $allocation.fixture_bytes -gt 32MB -or $allocation.fixture_largest -gt 8MB -or $allocation.fixture_largest -gt $allocation.fixture_bytes){throw 'whole operation allocation'}
    TimingStage 'C25' 'end'
    TimingStage 'C26' 'begin'
    VerifyCallerInputs
    TimingStage 'C26' 'end'
    $accepted=$true
}catch{try{if(-not $timingState.failed -and $timingState.next -gt 0){$failureStage=if($timingState.stack.Count){$timingState.stack[$timingState.stack.Count-1]}else{'C29'};TimingStage $failureStage 'fail' 'unknown'}}catch{$timingState.failed=$true};$callerError=$_.Exception.GetType().Name+': '+$_.Exception.Message;if($null -ne $journal.stream -and -not $journal.faulted){Journal $journal 'caller_error' $callerError}}
finally {
    try {
        if($null -ne $owner){
            $owner.Dispose()
            $state=@{creation_attempted=$owner.CreationAttempted;pid=$owner.Pid;creation_filetime=$owner.CreationFileTime;limits_verified=$owner.LimitsVerified;atomic_membership=$owner.AtomicMembership;resumed=$owner.Resumed;job_empty=$owner.JobEmpty;job_closed=$owner.JobClosed;process_closed=$owner.ProcessClosed;thread_closed=$owner.ThreadClosed;reaped=$owner.Reaped;fault=$owner.Fault;cleanup_error=$owner.CleanupError;samples=$owner.Samples;minimum_ram=$owner.MinimumRam;minimum_disk=$owner.MinimumDisk;peak_caller_private=$owner.PeakCallerPrivate;peak_process=$owner.PeakProcessBytes;peak_job=$owner.PeakJobBytes;watchdog_joined=$owner.WatchdogJoined;owned_nul_closed=$owner.InputClosed;stdout_eof=$owner.StdoutEof;stderr_eof=$owner.StderrEof;stdout_overflow=$owner.StdoutOverflow;stderr_overflow=$owner.StderrOverflow;stdout_reader_closed=$owner.StdoutReaderClosed;stderr_reader_closed=$owner.StderrReaderClosed;stdout_writer_closed=$owner.StdoutWriterClosed;stderr_writer_closed=$owner.StderrWriterClosed;stdout_reader_thread_handle_closed=$owner.StdoutThreadClosed;stderr_reader_thread_handle_closed=$owner.StderrThreadClosed;stdout_reader_joined=$owner.StdoutJoined;stderr_reader_joined=$owner.StderrJoined;stdout_cancel_attempted=$owner.StdoutCancelled;stderr_cancel_attempted=$owner.StderrCancelled;stdout_retained_bytes=$owner.StdoutBytes;stderr_retained_bytes=$owner.StderrBytes;stdout_observed_bytes=$owner.StdoutObserved;stderr_observed_bytes=$owner.StderrObserved;stdout_error=$owner.StdoutError;stderr_error=$owner.StderrError}
            if(-not($owner.JobEmpty -and $owner.JobClosed -and $owner.ProcessClosed -and $owner.ThreadClosed -and $owner.Reaped -and $owner.WatchdogJoined -and $owner.InputClosed -and $owner.StdoutEof -and $owner.StderrEof -and $owner.StdoutReaderClosed -and $owner.StderrReaderClosed -and $owner.StdoutWriterClosed -and $owner.StderrWriterClosed -and $owner.StdoutThreadClosed -and $owner.StderrThreadClosed -and $owner.StdoutJoined -and $owner.StderrJoined) -or $owner.StdoutOverflow -or $owner.StderrOverflow -or $null -ne $owner.CleanupError -or $null -ne $owner.Fault){$accepted=$false}
            if($owner.StdoutJoined -and $owner.StdoutEof -and -not $owner.StdoutOverflow -and $null -eq $owner.StdoutError){$outText=$owner.StdoutText()}
            if($owner.StderrJoined -and $owner.StderrEof -and -not $owner.StderrOverflow -and $null -eq $owner.StderrError){$errText=$owner.StderrText()}
        }
        TimingStage 'C27' 'begin'
        $noConsumers=($null -eq $owner -or -not $owner.CreationAttempted)
        $artifactHandoff.consumers_reaped=(-not $noConsumers -and $owner.Reaped -and $owner.JobEmpty -and $owner.JobClosed -and $owner.ProcessClosed)
        if($noConsumers -or $artifactHandoff.consumers_reaped){
            try{VerifyCallerArtifacts;foreach($item in $lNativeArtifacts){VerifyLNativeItem $item};foreach($item in $lToolInputs){VerifyLNativeItem $item};$lFinalVerified=($null -ne $lBundle);$artifactHandoff.final_original_recheck=$true;$artifactHandoff.original_writers_held_through_consumers=($artifactHandoff.consumers_reaped -and $callerArtifacts.Count -eq 3)}
            catch{$accepted=$false;$callerError='caller artifact final recheck: '+$_.Exception.Message;try{TimingStage 'C27' 'fail' 'input'}catch{$timingState.failed=$true}}
        }else{$accepted=$false}
        $artifactHandoff.artifacts=@($callerArtifacts|ForEach-Object {@{role=$_.role;reference=$_.reference;native_identity=$_.native_identity;writer_share=1}})
        if($accepted -and ($callerArtifacts.Count -ne 3 -or -not $artifactHandoff.final_original_recheck -or -not $artifactHandoff.original_writers_held_through_consumers)){$accepted=$false}
        TimingStage 'C27' 'end'
        $qdWatermark=55
        if($claimCreated){WriteRecord ('caller-return_'+$operation+'.json') @{schema='cho51_startup_timing_caller_return_v1';operation_id=$operation;accepted_by_caller=$false;diagnostic_outcome='incomplete';diagnostic_prefix_complete=$false;timing=@{caller=$null;supervisor=$supervisorTiming};required_q_obligations_complete=$false;qualification_accepted=$false;error=$callerError;origin_utc=$originUtc.ToString('o');origin_qpc=$originQpc;frequency=$frequency;return_utc=[DateTime]::UtcNow.ToString('o');return_qpc=[Diagnostics.Stopwatch]::GetTimestamp();elapsed_seconds=(Elapsed);outer_custody=$state;bootstrap_native_custody=$bootstrapCustody;bootstrap_controls=$bootstrapControls;final_input_verification=$finalInputVerified;stdout=$outText;stderr=$errText;stdio_capture_kind='owned_anonymous_pipes_strict_EOF_1MiB_retained_each';bootstrap_hard_deadline_seconds=65;bootstrap_original_process_handle_retained=$true;bootstrap_guard=(GuardSnapshot);guard_shutdown_pending=$true;startup_samples=$samples;initial_caller_private_bytes=$initialPrivate;supervisor_exit=$supervisorExit;api_mapping=$apiMapping;api_mapping_native_identity=$apiIdentity;native_diagnostic=$nativeDiagnostic;native_diagnostic_native_identity=$diagnosticIdentity;l_native_build=@{bundle=$lBundle;operations=$lBuildOperations.ToArray();final_original_recheck=$lFinalVerified;tool_inputs=$lToolInputs.Count};artifact_handoff=$artifactHandoff;caller_output_allocation=@{file_cap=40;byte_cap=20MB;reserved_files=$callerOutputReservations.Count;reserved_bytes=$script:callerOutputReservedBytes;reservations=$callerOutputReservations};input_handle_count=$inputs.Count;tool_return_pending=$true;independent_actual_review_pending=$true;historical_custody_closed=$false;historical_operation_released=$false;historical_retry_allowed=$false;restart_qualified=$false;boundary_qualified=$false;complete_dependency_closure=$false;launch_authorized=$false;scientific_admission=$false}}
    }finally{
        try{TimingStage 'C28' 'begin'}catch{$accepted=$false;$timingState.failed=$true}
        $closeErrors=[Collections.Generic.List[string]]::new()
        foreach($s in $outputs){try{$s.Dispose()}catch{$closeErrors.Add($_.Exception.Message)}}
        foreach($s in $inputs){try{$s.Dispose()}catch{$closeErrors.Add($_.Exception.Message)}}
        foreach($handle in $lDirectoryHandles.Values){try{$handle.Dispose();if(-not $handle.IsClosed){throw 'L compiler directory handle close'}}catch{$closeErrors.Add($_.Exception.Message)}}
        $fileClosure.closed=$closeErrors.Count -eq 0
        if($null -ne $bootstrapOwner){$bootstrapOwner.Dispose()}
    if(-not $fileClosure.closed){throw ('original input/output close failure: '+($closeErrors -join '; '))}
        try{TimingStage 'C28' 'end'}catch{$accepted=$false;$timingState.failed=$true}
    }
}
try{TimingFinish}catch{$accepted=$false;$callerError='QD journal seal failed'}finally{if($null -ne $timingJournal){$timingJournal.Dispose()}}
$callerTiming=TimingReference
if($null -eq $callerTiming -or -not $callerTiming.original_file_closed -or -not $callerTiming.original_ancestry_closed -or $null -ne $timingJournal.CleanupError){$accepted=$false}
Journal $journal 'caller_ready_to_close'
$journal.stream.Dispose();$journal.closed=$true
StopGuard
if($null -ne $bootstrapOwner){$bootstrapOwner.Dispose();$bootstrapCustody=OwnerState $bootstrapOwner;if($bootstrapCustody.creation_attempted -or -not $bootstrapCustody.job_closed -or -not $bootstrapCustody.job_empty -or -not $bootstrapCustody.watchdog_joined -or $null -ne $bootstrapCustody.cleanup_error -or $null -ne $bootstrapCustody.fault){$accepted=$false}}
$finalGuard=GuardSnapshot
if(-not $finalGuard.joined -or -not $finalGuard.closed -or -not $finalGuard.done -or $null -ne $finalGuard.error){$accepted=$false}
if(-not (FinalPublicationClock)){$accepted=$false;$callerError='QD publication deadline after guard shutdown'}
$externalReturn=@{schema='cho51_startup_timing_external_return_v1';operation_id=$operation;accepted_by_caller=$false;diagnostic_outcome=$(if($accepted){'prefix_pending_review'}elseif(-not $fileClosure.closed -or $null -eq $callerTiming -or -not $callerTiming.original_file_closed -or -not $callerTiming.original_ancestry_closed){'custody_unknown'}else{'incomplete'});diagnostic_prefix_complete=$accepted;timing=@{caller=$callerTiming;supervisor=$supervisorTiming};required_q_obligations_complete=$false;qualification_accepted=$false;error=$callerError;outer_custody=$state;bootstrap_native_custody=$bootstrapCustody;bootstrap_controls=$bootstrapControls;final_input_verification=$finalInputVerified;api_mapping=$apiMapping;api_mapping_native_identity=$apiIdentity;native_diagnostic=$nativeDiagnostic;native_diagnostic_native_identity=$diagnosticIdentity;l_native_build=@{bundle=$lBundle;operations=$lBuildOperations.ToArray();final_original_recheck=$lFinalVerified;tool_inputs=$lToolInputs.Count};artifact_handoff=$artifactHandoff;caller_output_allocation=@{file_cap=40;byte_cap=20MB;reserved_files=$callerOutputReservations.Count;reserved_bytes=$script:callerOutputReservedBytes;reservations=$callerOutputReservations};bootstrap_guard=$finalGuard;original_file_handles_closed=($fileClosure.closed -and $journal.closed);bootstrap_journal_closed=$journal.closed;bootstrap_journal_bytes=$journal.bytes;bootstrap_journal_records=$journal.records;elapsed_seconds=(Elapsed);historical_custody_closed=$false;historical_operation_released=$false;historical_retry_allowed=$false;restart_qualified=$false;boundary_qualified=$false;complete_dependency_closure=$false;launch_authorized=$false;scientific_admission=$false}
$encoded=$externalReturn|ConvertTo-Json -Depth 8 -Compress
if(-not (FinalPublicationClock)){
    $accepted=$false;$callerError='QD publication deadline immediately before output'
    $externalReturn.diagnostic_prefix_complete=$false
    if($externalReturn.diagnostic_outcome -cne 'custody_unknown'){$externalReturn.diagnostic_outcome='incomplete'}
    $externalReturn.error=$callerError;$encoded=$externalReturn|ConvertTo-Json -Depth 8 -Compress
}
$encoded
if(-not (FinalPublicationClock)){$accepted=$false;$callerError='QD publication boundary crossed; emitted frame cannot be accepted'}
if(-not $accepted){throw ('QD prefix incomplete; Q remains held: '+$callerError)}
} finally {
    if($null -ne $timingJournal){$timingJournal.Dispose();if(-not $timingJournal.FileClosed -or -not $timingJournal.AncestorsClosed){$killAction.Invoke();throw 'QD timing custody unknown'}}
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
















