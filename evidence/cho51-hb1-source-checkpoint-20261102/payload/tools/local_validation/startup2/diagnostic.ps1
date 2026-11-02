param([Parameter(Mandatory=$true)][string]$Capsule,[Parameter(Mandatory=$true)][long]$CapsuleBytes,[Parameter(Mandatory=$true)][string]$CapsuleSha256)
$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
$originUtc=[DateTime]::UtcNow;$originQpc=[Diagnostics.Stopwatch]::GetTimestamp();$frequency=[Diagnostics.Stopwatch]::Frequency
$process=[Diagnostics.Process]::GetCurrentProcess();$originalHandle=$process.SafeHandle;$creation=$process.StartTime.ToUniversalTime().ToFileTimeUtc();$callerPid=$process.Id
$kill=[Delegate]::CreateDelegate([Action],$process,'Kill')
$hard=[Threading.CancellationTokenSource]::new();$hardRegistration=$hard.Token.Register($kill)
$hard.CancelAfter([Math]::Max(1,[int](15000-([Diagnostics.Stopwatch]::GetTimestamp()-$originQpc)*1000/$frequency)))
$startup=[Threading.CancellationTokenSource]::new();$startupRegistration=$startup.Token.Register($kill)
$startup.CancelAfter([Math]::Max(1,[int](5000-([Diagnostics.Stopwatch]::GetTimestamp()-$originQpc)*1000/$frequency)))
$cleanupDeadline=[Threading.CancellationTokenSource]::new();$cleanupRegistration=$cleanupDeadline.Token.Register($kill)
$inputs=[Collections.Generic.Dictionary[string,object]]::new([StringComparer]::Ordinal);$outputs=[Collections.Generic.List[object]]::new()
$utf8=[Text.UTF8Encoding]::new($false,$true);$value=$null;$owner=$null;$guard=$null;$runspace=$null;$invocation=$null
$disposeSource=$null;$disposeRegistration=$null;$disposeJoined=$false;$disposeArmed=$false;$disposeScheduledQpc=$null;$cancelObservedQpc=$null
$authority=$false;$failure=$null;$closed=$false;$claim=$null;$report=$null;$stdout='';$stderr='';$markers=@();$markerError=$null;$nativeIdsBound=$false
$guardState=[hashtable]::Synchronized(@{ready=$false;stop=$false;done=$false;error=$null;last=0L;samples=0;first=$null;second=$null;joined=$false;closed=$false;completion_wait_closed=$false})
$events=[Collections.Generic.List[object]]::new();$outputBytes=0L;$filesClosed=$false
$finalInputsVerified=$false;$finalOutputsVerified=$false;$custody=$null
$loadedHelper=$null;$runtimeSet=$null;$runtimeDirectory=$null;$managedBefore=@();$managedAfter=@()
$cacheDirectories=@('AppData','AppData/Local','AppData/Local/Microsoft','AppData/Local/Microsoft/PowerShell')
function Elapsed {([Diagnostics.Stopwatch]::GetTimestamp()-$originQpc)/$frequency}
function Need($Condition,[string]$Message){if(-not $Condition){throw $Message}}
function Fields($Object,[string]$Names){
 Need ($Object -is [System.Collections.IDictionary]) 'closed object type'
 $keys=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
 foreach($name in $Names.Split(' ')){[void]$keys.Add($name)}
 foreach($name in $Object.Keys){Need ($keys.Remove([string]$name)) ('unknown/alias field '+$name)}
 Need ($keys.Count -eq 0) ('missing fields '+($keys -join ','))
}
function IntValue($Number,[long]$Low,[long]$High){Need (($Number -is [int] -or $Number -is [long]) -and $Number -ge $Low -and $Number -le $High) 'bounded exact integer'}
function IndependentIdentity($Record,[string]$Role){
 Need ($Record.reviewer -is [string] -and $Record.reviewer -cmatch '^[a-z][a-z0-9_-]{0,63}$') ($Role+' reviewer identity')
 Need ($Record.authors -is [array] -and $Record.authors.Count -ge 1 -and $Record.authors.Count -le 16) ($Role+' author identities')
 $identities=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
 foreach($identity in $Record.authors){Need ($identity -is [string] -and $identity -cmatch '^[a-z][a-z0-9_-]{0,63}$' -and $identities.Add($identity)) ($Role+' author identity/duplicate')}
 Need (-not $identities.Contains($Record.reviewer)) ($Role+' reviewer is an author')
}
function Canonical([string]$Path){
 Need ($Path -cmatch '^[A-Z]:/' -and -not $Path.Contains('\') -and -not $Path.Contains([char]0) -and $Path.Substring(3) -cnotmatch '[:*?"<>|]') 'canonical absolute path'
 foreach($part in $Path.Substring(3).Split('/')){Need ($part -and $part -cne '.' -and $part -cne '..' -and -not $part.EndsWith('.') -and -not $part.EndsWith(' ')) 'canonical path component'}
 Need ([IO.Path]::GetFullPath($Path).Replace('\','/') -ceq $Path) 'canonical full path';return $Path
}
function Ancestors([string]$Path){
 $dir=[IO.FileInfo]::new($Path).Directory
 while($null -ne $dir){$attr=[IO.File]::GetAttributes($dir.FullName);Need (($attr -band [IO.FileAttributes]::Directory) -and -not($attr -band [IO.FileAttributes]::ReparsePoint)) 'ordinary ancestry';$dir=$dir.Parent}
}
function StopCheck {
 $stopFile='D:/Aenv/pro3/runs/coordination/PROJECT_STOP.json';Ancestors $stopFile
 try{[void][IO.File]::GetAttributes($stopFile);throw 'project stop present'}catch [IO.FileNotFoundException]{}
}
function Check([switch]$Work){
 Need ((Elapsed) -lt 15 -and [DateTime]::UtcNow -lt $originUtc.AddSeconds(15)) 'original whole deadline'
 if($Work){Need ((Elapsed) -lt 5 -and [DateTime]::UtcNow -lt $originUtc.AddSeconds(5) -and -not $startup.IsCancellationRequested) 'original work deadline'}
 if($null -ne $invocation){Need ($guardState.ready -and -not $guardState.done -and $null -eq $guardState.error -and -not $invocation.IsCompleted -and ([Diagnostics.Stopwatch]::GetTimestamp()-$guardState.last)/$frequency -le .25) 'independent guard unhealthy/stale'}
 else {
  StopCheck
  $process.Refresh();Need ($process.PrivateMemorySize64 -le 4096MB -and [IO.DriveInfo]::new('D').AvailableFreeSpace -ge 20GB) 'bootstrap private/disk'
 }
}
function Event([string]$Name){Need ($events.Count -lt 32) 'journal count';$events.Add(@{sequence=$events.Count;event=$Name;qpc=[Diagnostics.Stopwatch]::GetTimestamp();elapsed_seconds=(Elapsed)})}
function Parse([byte[]]$Raw){
 Need ($Raw.Length -le 1MB) 'JSON cap';$text=$utf8.GetString($Raw);$document=[Text.Json.JsonDocument]::Parse($text,[Text.Json.JsonDocumentOptions]@{MaxDepth=16})
 $budget=@{count=0}
 function Visit($Node,[int]$Depth,$Budget){
  $Budget.count++;Need ($Budget.count -le 20000 -and $Depth -le 16) 'JSON structure'
  if($Node.ValueKind -eq [Text.Json.JsonValueKind]::Object){
   $seen=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
   foreach($item in $Node.EnumerateObject()){Need ($seen.Add($item.Name) -and -not $item.Name.Contains([char]0)) 'duplicate/invalid JSON key';Visit $item.Value ($Depth+1) $Budget}
  }elseif($Node.ValueKind -eq [Text.Json.JsonValueKind]::Array){foreach($item in $Node.EnumerateArray()){Visit $item ($Depth+1) $Budget}}
  elseif($Node.ValueKind -eq [Text.Json.JsonValueKind]::String){$item=$Node.GetString();Need (-not $item.Contains([char]0)) 'invalid JSON string';[void]$utf8.GetBytes($item)}
  elseif($Node.ValueKind -eq [Text.Json.JsonValueKind]::Number){Need ([double]::IsFinite($Node.GetDouble())) 'nonfinite JSON number'}
 }
 try{Visit $document.RootElement 0 $budget;return ($text|ConvertFrom-Json -AsHashtable -Depth 16 -DateKind String)}finally{$document.Dispose()}
}
function Ref($Reference){Fields $Reference 'path bytes sha256';[void](Canonical $Reference.path);IntValue $Reference.bytes 0 64MB;Need ($Reference.sha256 -is [string] -and $Reference.sha256 -cmatch '^[0-9a-f]{64}$') 'pin digest'}
function SameRef($Left,$Right){return $Left.path -ceq $Right.path -and $Left.bytes -eq $Right.bytes -and $Left.sha256 -ceq $Right.sha256}
function AbsoluteRef($Reference){
 $path=$Reference.path;if($path -cnotmatch '^[A-Z]:/'){$path='D:/Aenv/pro3/'+$path}
 return @{path=$path;bytes=$Reference.bytes;sha256=$Reference.sha256}
}
function Pin($Reference,[switch]$Collect){
 Ref $Reference;Check -Work
 if($Collect){Need ($Reference.bytes -le 1MB) 'collected input cap'}
 if($inputs.ContainsKey($Reference.path)){$row=$inputs[$Reference.path];Need (SameRef $row.pin $Reference) 'conflicting retained pins';if($Collect){$row.stream.Position=0;$bytes=[byte[]]::new($row.pin.bytes);$offset=0;while($offset -lt $bytes.Length){Check -Work;$count=$row.stream.Read($bytes,$offset,$bytes.Length-$offset);Need ($count -gt 0) 'retained short read';$offset+=$count};return ,$bytes};return}
 Need ($inputs.Count -lt 1100) 'input file cap';Ancestors $Reference.path
 Need (-not([IO.File]::GetAttributes($Reference.path) -band ([IO.FileAttributes]::ReparsePoint -bor [IO.FileAttributes]::Directory))) 'ordinary input leaf'
 $stream=[IO.FileStream]::new($Reference.path,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
 $row=@{stream=$stream;pin=$Reference;identity=$null};$inputs.Add($Reference.path,$row)
 if($nativeIdsBound){$row.identity=[PNative.Owner]::FileIdentity($stream.SafeFileHandle)}
 Need ($stream.Length -eq $Reference.bytes) 'input length'
 $hash=[Security.Cryptography.IncrementalHash]::CreateHash([Security.Cryptography.HashAlgorithmName]::SHA256)
 $memory=if($Collect){[IO.MemoryStream]::new()}else{$null}
 try{$buffer=[byte[]]::new(65536);do{Check -Work;$count=$stream.Read($buffer,0,$buffer.Length);if($count){$hash.AppendData($buffer,0,$count);if($Collect){Need ($memory.Length+$count -le 1MB) 'collected input cap';$memory.Write($buffer,0,$count)}}}while($count)
  Need ([Convert]::ToHexString($hash.GetHashAndReset()).ToLowerInvariant() -ceq $Reference.sha256) 'input digest'
  if($Collect){return ,$memory.ToArray()}
 }finally{$hash.Dispose();if($null -ne $memory){$memory.Dispose()};$stream.Position=0}
}
function Record($Reference){return (Parse (Pin $Reference -Collect))}
function Utc($Literal){Need ($Literal -is [string] -and $Literal -cmatch '^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(\.\d{1,7})?(Z|\+00:00)$') 'explicit UTC';return [DateTimeOffset]::Parse($Literal,[Globalization.CultureInfo]::InvariantCulture).UtcDateTime}
function Safety($Record){Fields $Record 'historical_custody_closed historical_operation_released historical_retry_allowed restart_qualified scientific_admission candidate_tests_executed successor_controls_executed';foreach($name in @('historical_custody_closed','historical_operation_released','historical_retry_allowed','restart_qualified','scientific_admission')){Need ($Record[$name] -is [bool] -and -not $Record[$name]) 'historical/scientific scope'};IntValue $Record.candidate_tests_executed 0 0;IntValue $Record.successor_controls_executed 0 0}
function SourcesMatch($Left,$Right){
 Need ($Left.Count -eq $Right.Count) 'source set count'
 foreach($name in $Left.Keys){Need ($Right.Contains($name) -or $Right.ContainsKey($name)) 'source membership';Fields $Left[$name] 'bytes sha256';Fields $Right[$name] 'bytes sha256';IntValue $Left[$name].bytes 0 1MB;IntValue $Right[$name].bytes 0 1MB;Need ($Left[$name].bytes -eq $Right[$name].bytes -and $Left[$name].sha256 -ceq $Right[$name].sha256) 'reviewed source bytes'}
}
function Publish([string]$Name,[byte[]]$Raw){
 Check;Need ($outputs.Count -lt 16 -and $outputBytes+$Raw.Length -le 64MB -and $Raw.Length -le 8MB) 'output budget'
 Need ($Name -cmatch '^[a-z0-9-]+\.(json|bin)$') 'owned output name'
 $path=$value.output_root+'/'+$Name;Ancestors $path
 $stream=[IO.FileStream]::new($path,[IO.FileMode]::CreateNew,[IO.FileAccess]::ReadWrite,[IO.FileShare]::Read)
 $pin=@{path=$path;bytes=$Raw.Length;sha256=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($Raw)).ToLowerInvariant()}
 $row=@{stream=$stream;pin=$pin;identity=$null};$outputs.Add($row);$script:outputBytes+=$Raw.Length
 $row.identity=[PNative.Owner]::FileIdentity($stream.SafeFileHandle)
 $stream.Write($Raw,0,$Raw.Length);$stream.Flush($true);return @{path=$pin.path;bytes=$pin.bytes;sha256=$pin.sha256;native_identity=$row.identity}
}
function Verify($Row){
 Check;$stream=$Row.stream;Need ($stream.Length -eq $Row.pin.bytes -and [PNative.Owner]::FileIdentity($stream.SafeFileHandle) -ceq $Row.identity) 'final original identity/length'
 $hash=[Security.Cryptography.IncrementalHash]::CreateHash([Security.Cryptography.HashAlgorithmName]::SHA256)
 try{$stream.Position=0;$buffer=[byte[]]::new(65536);do{Check;$count=$stream.Read($buffer,0,$buffer.Length);if($count){$hash.AppendData($buffer,0,$count)}}while($count);Need ([Convert]::ToHexString($hash.GetHashAndReset()).ToLowerInvariant() -ceq $Row.pin.sha256) 'final original bytes'}finally{$hash.Dispose()}
}
function StartGuard {
 $script=@'
param($owner,$process,$kill,$origin,$utc,$frequency,$privateCap,$shared)
$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
try {
 while(-not $shared.stop){
  $before=[Diagnostics.Stopwatch]::GetTimestamp()
  if(($before-$origin)/$frequency -lt 0 -or ($before-$origin)/$frequency -ge 15 -or [DateTime]::UtcNow -ge $utc.AddSeconds(15)){throw 'original guard deadline'}
  if($shared.last -ne 0 -and ($before-$shared.last)/$frequency -gt .25){throw 'guard sample stale'}
  $stopFile='D:/Aenv/pro3/runs/coordination/PROJECT_STOP.json';$dir=[IO.FileInfo]::new($stopFile).Directory
  while($null -ne $dir){$attr=[IO.File]::GetAttributes($dir.FullName);if(($attr -band [IO.FileAttributes]::ReparsePoint) -or -not($attr -band [IO.FileAttributes]::Directory)){throw 'guard stop ancestry'};$dir=$dir.Parent}
  try{[void][IO.File]::GetAttributes($stopFile);throw 'guard stop present'}catch [IO.FileNotFoundException]{}
  $ram=$owner.Sample() # public current-process APIs; safe after owned Job/stdio Dispose
  $process.Refresh();$private=$process.PrivateMemorySize64
  if($private -gt $privateCap){throw 'role-specific caller cap'}
  $after=[Diagnostics.Stopwatch]::GetTimestamp()
  if(($after-$before)/$frequency -gt .25){throw 'guard sample duration'}
  if($shared.last -ne 0 -and ($after-$shared.last)/$frequency -gt .25){throw 'guard completed-sample interval'}
  $sample=@{qpc_begin=$before;qpc_end=$after;ram_sample_bytes=$ram;minimum_disk_bytes_so_far=$owner.MinimumDisk;peak_caller_private_bytes_so_far=$owner.PeakCallerPrivate;managed_current_private_bytes=$private;native_predicates_passed=$true}
  $shared.samples++;$shared.last=$after
  if($null -eq $shared.first){$shared.first=$sample}
  if(-not $shared.ready -and ($before-$shared.first.qpc_end)/$frequency -ge .2){$shared.second=$sample;$shared.ready=$true}
  [Threading.Thread]::Sleep(75)
 }
}catch{$shared.error=$_.Exception.GetType().Name+': '+$_.Exception.Message;$kill.Invoke()}
finally{$shared.done=$true}
'@
 $script:runspace=[Management.Automation.Runspaces.RunspaceFactory]::CreateRunspace();$runspace.Open()
 $script:guard=[Management.Automation.PowerShell]::Create();$guard.Runspace=$runspace
 $cap=if($value.role -ceq 'Q_STARTUP_CONTROL'){512MB}else{4096MB}
 [void]$guard.AddScript($script).AddArgument($owner).AddArgument($process).AddArgument($kill).AddArgument($originQpc).AddArgument($originUtc).AddArgument($frequency).AddArgument($cap).AddArgument($guardState)
 $script:invocation=$guard.BeginInvoke()
 while(-not $guardState.ready){Need (-not $invocation.IsCompleted -and -not $guardState.done -and $null -eq $guardState.error -and (Elapsed) -lt 5) 'native guard startup';[Threading.Thread]::Sleep(5)}
}
function JoinGuard {
 if($null -eq $invocation){if($null -ne $guard){$guard.Dispose()};if($null -ne $runspace){$runspace.Dispose()};return}
 $guardState.stop=$true;$wait=$invocation.AsyncWaitHandle
 Need ($wait.WaitOne(500)) 'guard join deadline';[void]$guard.EndInvoke($invocation)
 Need ($guardState.done -and $null -eq $guardState.error -and -not $guard.HadErrors) 'guard completion'
 $guardState.joined=$true;$wait.Dispose();$guardState.completion_wait_closed=$true;$guard.Dispose();$runspace.Dispose();$guardState.closed=$true
}
function RuntimeCensus {
 $current=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
 foreach($name in [IO.Directory]::EnumerateFiles($runtimeDirectory)){
  if([IO.Path]::GetExtension($name).ToLowerInvariant() -cin @('.dll','.exe','.json')){[void]$current.Add($name.Replace('\','/'))}
 }
 Need ($current.SetEquals($runtimeSet)) 'exact runtime top-level DLL/EXE/JSON census'
 foreach($dir in [IO.Directory]::EnumerateDirectories($runtimeDirectory)){
  if([IO.Path]::GetFileName($dir) -cmatch '^[a-z]{2}(-[A-Za-z0-9]{2,8})*$'){
   Need (-not([IO.File]::GetAttributes($dir) -band [IO.FileAttributes]::ReparsePoint)) 'runtime culture reparse'
   foreach($file in [IO.Directory]::EnumerateFiles($dir)){Need ([IO.Path]::GetExtension($file).ToLowerInvariant() -cne '.dll') 'unreviewed culture DLL census'}
  }
 }
 foreach($leaf in @('pwsh.exe.config','powershell.exe.config')){
  try{[void][IO.File]::GetAttributes($runtimeDirectory+'/'+$leaf);throw 'unexpected runtime config alias'}catch [IO.FileNotFoundException]{}
 }
}
function ManagedCoverage {
 $rows=[Collections.Generic.List[object]]::new()
 foreach($assembly in [AppDomain]::CurrentDomain.GetAssemblies()){
  if($assembly.IsDynamic){$rows.Add(@{name=$assembly.FullName;path=$null;scope='local_runtime_dynamic_platform_trust'});continue}
  if($null -ne $loadedHelper -and [object]::ReferenceEquals($assembly,$loadedHelper)){$rows.Add(@{name=$assembly.FullName;path=$null;scope='exact_retained_helper_bytes'});continue}
  $location=$assembly.Location.Replace('\','/');Need ($location -and $runtimeSet.Contains($location)) 'loaded managed assembly outside finite runtime closure'
  $rows.Add(@{name=$assembly.FullName;path=$location;scope='disk_pin_and_resident_platform_trust_not_loaded_code_attestation'})
 }
 return ,$rows.ToArray()
}
function CreateCacheDirectories {
 foreach($relative in $cacheDirectories){
  Check -Work;$path=$value.output_root+'/'+$relative;Ancestors $path
  try{[void][IO.File]::GetAttributes($path);throw 'occupied cache directory'}catch [IO.FileNotFoundException]{}
  [void][IO.Directory]::CreateDirectory($path)
  $attributes=[IO.File]::GetAttributes($path)
  Need (($attributes -band [IO.FileAttributes]::Directory) -and -not($attributes -band [IO.FileAttributes]::ReparsePoint)) 'plain cache directory'
  foreach($entry in [IO.Directory]::EnumerateFileSystemEntries($path)){throw 'cache directory not fresh empty'}
 }
}
function OutputCensus {
 # Exact bounded tree: four plain directories and only currently retained files.
 # Before observation publication that is three files; at final verification five.
 $files=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
 foreach($row in $outputs){Need ($files.Add($row.pin.path.Substring($value.output_root.Length+1))) 'duplicate owned output'}
 $directories=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
 foreach($relative in $cacheDirectories){[void]$directories.Add($relative)}
 $pending=[Collections.Generic.Stack[object]]::new();$pending.Push(@{path=$value.output_root;depth=0});$count=0
 while($pending.Count){
  Check;$current=$pending.Pop();Need ($current.depth -le 4) 'output census depth';Ancestors ($current.path+'/witness')
  foreach($entry in [IO.Directory]::EnumerateFileSystemEntries($current.path)){
   Check;$count++;Need ($count -le 9) 'output census entries'
   $full=$entry.Replace('\','/');[void](Canonical $full)
   Need ($full.StartsWith($value.output_root+'/',[StringComparison]::Ordinal)) 'output census ancestry'
   $relative=$full.Substring($value.output_root.Length+1);$attributes=[IO.File]::GetAttributes($entry)
   Need (-not($attributes -band [IO.FileAttributes]::ReparsePoint)) 'output census reparse'
   if($attributes -band [IO.FileAttributes]::Directory){
    Need ($directories.Remove($relative)) 'unknown/aliased output directory'
    $pending.Push(@{path=$full;depth=$current.depth+1})
   }else{Need ($files.Remove($relative)) 'unknown/aliased attempt file'}
  }
 }
 Need ($files.Count -eq 0 -and $directories.Count -eq 0) 'missing output file/directory'
}
try {
 Event 'entry';$value=Parse (Pin @{path=$Capsule;bytes=$CapsuleBytes;sha256=$CapsuleSha256} -Collect)
 Fields $value 'schema issuer operation_id role probe created_utc expires_utc project_root stop_path output_root helper q2_qualification q2_actual_review source_review adoption qualification sources caller_runtime environment limits safety enclosing_q'
 Need ($value.schema -ceq 'cho51_startup_capsule_v1' -and $value.issuer -ceq 'project_root') 'capsule authority'
 Need ($value.operation_id -is [string] -and $value.operation_id -ceq ([guid]$value.operation_id).ToString() -and $value.operation_id -cmatch '^[0-9a-f-]{36}$') 'canonical UUID'
 Need ($value.project_root -ceq 'D:/Aenv/pro3' -and $value.stop_path -ceq 'D:/Aenv/pro3/runs/coordination/PROJECT_STOP.json') 'project scope'
 Need ($value.role -ceq 'D' -or $value.role -ceq 'Q_STARTUP_CONTROL') 'closed role'
 Need (($value.role -ceq 'D' -and $value.probe -ceq 'pdh') -or ($value.role -ceq 'Q_STARTUP_CONTROL' -and $value.probe -cin @('fast','stall','empty','malformed','reordered','partial'))) 'closed probe/role'
 [void](Canonical $value.output_root);Need ([IO.Path]::GetFileName($value.output_root) -ceq $value.operation_id -and $value.output_root.StartsWith('D:/Aenv/pro3/runs/coordination/',[StringComparison]::Ordinal)) 'output namespace'
 Need ((Utc $value.created_utc) -le $originUtc -and (Utc $value.expires_utc) -ge $originUtc.AddSeconds(15)) 'whole original admission interval'
 Safety $value.safety
 Fields $value.limits 'startup_seconds cleanup_deadline_seconds whole_seconds startup_ram_bytes active_ram_bytes disk_bytes process_mib job_mib sample_interval_ms'
 $limits=@{startup_seconds=5;cleanup_deadline_seconds=10;whole_seconds=15;startup_ram_bytes=4GB;active_ram_bytes=4GB;disk_bytes=20GB;process_mib=4096;job_mib=5120;sample_interval_ms=250}
 foreach($key in $limits.Keys){IntValue $value.limits[$key] $limits[$key] $limits[$key]}
 if($value.role -ceq 'D'){Ref $value.qualification;Need ($null -eq $value.enclosing_q) 'D Q separation'}else{
  Need ($null -eq $value.qualification) 'no self qualification';Fields $value.enclosing_q 'operation_id admission limits';Ref $value.enclosing_q.admission;[void](Pin $value.enclosing_q.admission);Fields $value.enclosing_q.limits 'process_mib job_mib';IntValue $value.enclosing_q.limits.process_mib 512 512;IntValue $value.enclosing_q.limits.job_mib 768 768;Need ($value.enclosing_q.operation_id -cne $value.operation_id) 'outer Q operation'
 }
 $leaves=@('__init__.py','contract.py','diagnostic.ps1','pdh_probe.ps1','fast_probe.ps1','stall_probe.ps1','empty_probe.ps1','malformed_probe.ps1','reordered_probe.ps1','partial_probe.ps1','test_diagnostic.py','README.md')
 Need ($value.sources.Count -eq $leaves.Count) 'exact startup source count'
 foreach($leaf in $leaves){$path='D:/Aenv/pro3/tools/local_validation/startup2/'+$leaf;Need ($value.sources.Contains($path) -or $value.sources.ContainsKey($path)) 'exact startup source membership';Fields $value.sources[$path] 'bytes sha256';[void](Pin @{path=$path;bytes=$value.sources[$path].bytes;sha256=$value.sources[$path].sha256})}
 Need ($PSCommandPath.Replace('\','/') -ceq 'D:/Aenv/pro3/tools/local_validation/startup2/diagnostic.ps1') 'exact running source'
 Fields $value.caller_runtime 'executable version files';$runtime=$value.caller_runtime
 Need ($runtime.files -is [array] -and $runtime.files.Count -ge 1 -and $runtime.files.Count -le 1024) 'runtime count'
 Need ($runtime.version -ceq $PSVersionTable.PSVersion.ToString() -and $runtime.executable.path -ceq $process.MainModule.FileName.Replace('\','/')) 'caller runtime'
 $runtimeSet=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal);$total=0L
 foreach($reference in $runtime.files){Ref $reference;Need ($runtimeSet.Add($reference.path)) 'runtime aliases';$total+=$reference.bytes;Need ($total -le 512MB) 'runtime aggregate'}
 Need ($runtimeSet.Contains($runtime.executable.path)) 'runtime executable closure';Ref $runtime.executable;[void](Pin $runtime.executable)
 $runtimeDirectory=[IO.Path]::GetDirectoryName($runtime.executable.path).Replace('\','/');RuntimeCensus;$managedBefore=ManagedCoverage
 $review=Record $value.source_review;Fields $review 'schema status reviewer authors created_utc sources design design_acceptance findings checks limitations'
 foreach($key in @('findings','checks','limitations')){Need ($review[$key] -is [array] -and $review[$key].Count -le 256) 'review bounded arrays'}
 Need ($review.schema -ceq 'cho51_startup_source_review_v1' -and $review.status -ceq 'ACCEPTED_SOURCE_STARTUP2') 'startup source review schema/status'
 IndependentIdentity $review 'startup source review'
 Need ($review.findings.Count -eq 0) 'unresolved startup source review findings'
 foreach($key in @('checks','limitations')){foreach($item in $review[$key]){Need ($item -is [string] -and $item.Length -le 4096) 'review detail string'}}
 SourcesMatch $value.sources $review.sources
 $adoption=Record $value.adoption;Fields $adoption 'schema status author created_utc source_review design design_acceptance q2_qualification q2_actual_review helper limits bootstrap_effects safety'
 Need ($adoption.schema -ceq 'cho51_startup_adoption_v1' -and $adoption.status -ceq 'ADOPTED_STARTUP_DIAGNOSTIC_ONLY' -and $adoption.author -ceq 'project_root') 'Root scoped adoption';Safety $adoption.safety
 foreach($key in @('source_review','q2_qualification','q2_actual_review')){Need (SameRef $adoption[$key] $value[$key]) ('adoption '+$key)}
 Need ((SameRef $review.design $adoption.design) -and (SameRef $review.design_acceptance $adoption.design_acceptance)) 'design joins'
 Need ((Utc $review.created_utc) -le (Utc $adoption.created_utc) -and (Utc $adoption.created_utc) -le (Utc $value.created_utc)) 'source adoption order'
 Fields $adoption.limits 'startup_seconds cleanup_deadline_seconds whole_seconds startup_ram_bytes active_ram_bytes disk_bytes process_mib job_mib sample_interval_ms'
 foreach($key in $limits.Keys){IntValue $adoption.limits[$key] $limits[$key] $limits[$key]}
 Need (($adoption.bootstrap_effects -join ',') -ceq 'retained_helper_load,empty_job_and_native_guard,one_fixed_probe') 'finite bootstrap effects'
 [void](Pin $adoption.design);$accepted=Record $adoption.design_acceptance
 Need ($accepted.schema -ceq 'cho51_startup_diagnostic_root_design_acceptance_v1' -and $accepted.status -ceq 'ACCEPTED_DESIGN_ONLY' -and $accepted.author -ceq 'project_root' -and (SameRef (AbsoluteRef $accepted.source) $adoption.design)) 'accepted design'
 $designReview=Record (AbsoluteRef $accepted.independent_review)
 IndependentIdentity $designReview 'design review'
 Fields $designReview.design 'path sha256'
 $reviewedDesignPath=$designReview.design.path;if($reviewedDesignPath -cnotmatch '^[A-Z]:/'){$reviewedDesignPath='D:/Aenv/pro3/'+$reviewedDesignPath}
 Need ($designReview.schema -ceq 'cho51_startup_diagnostic_design_review_v1' -and $designReview.status -ceq 'ACCEPTED_DESIGN_ONLY' -and $designReview.authors -cnotcontains $designReview.reviewer -and $designReview.design.sha256 -ceq $adoption.design.sha256 -and $reviewedDesignPath -ceq $adoption.design.path) 'independent design review'
 $q2=Record $value.q2_qualification;$actual=Record $value.q2_actual_review
 Need ($q2.author -ceq 'project_root' -and $q2.status -ceq 'QUALIFIED_LQ1_MECHANISMS_ONLY' -and (SameRef (AbsoluteRef $q2.actual_review) $value.q2_actual_review) -and $actual.status -ceq 'ACCEPTED_LQ1_TESTED_SCOPE' -and $actual.operation_id -ceq $q2.operation_id -and $actual.actual_tool_exit_code -eq 0 -and $actual.new_operation_owned_lifecycle_closed -is [bool] -and $actual.new_operation_owned_lifecycle_closed) 'qualified existing helper authority'
 $q2Source=Record (AbsoluteRef $q2.source_review)
 IndependentIdentity $q2Source 'existing helper source review';IndependentIdentity $actual 'existing helper actual review'
 Need ($q2Source.status -ceq 'ACCEPTED_SOURCE_LQ1' -and $q2Source.authors -cnotcontains $q2Source.reviewer -and $actual.reviewer -cne $q2Source.reviewer -and $actual.authors -cnotcontains $actual.reviewer -and $actual.source_review_sha256 -ceq $q2.source_review.sha256) 'existing helper independent reviews'
 foreach($key in @('emitted_pe_verified','original_output_identity_retained','loaded_same_pe_bytes','p_limits_query_verified','empty_job_closed','l_two_process_limits_query_verified','l_empty_job_closed','l_invalid_process_count_refused')){Need ($q2.native_builder_controls[$key] -is [bool] -and $q2.native_builder_controls[$key] -and $actual.native_builder_controls[$key] -is [bool] -and $actual.native_builder_controls[$key]) 'existing helper qualified controls'}
 Fields $value.helper 'path bytes sha256 native_identity';$helper=@{path=$value.helper.path;bytes=$value.helper.bytes;sha256=$value.helper.sha256}
 Fields $adoption.helper 'path bytes sha256 native_identity';Ref @{path=$adoption.helper.path;bytes=$adoption.helper.bytes;sha256=$adoption.helper.sha256}
 Need ((SameRef (AbsoluteRef $q2.native_helper) $helper) -and (SameRef (AbsoluteRef $actual.native_helper) $helper) -and (SameRef $adoption.helper $helper) -and $value.helper.native_identity -ceq $adoption.helper.native_identity -and $value.helper.native_identity -ceq $q2.native_builder_controls.helper_identity -and $value.helper.native_identity -ceq $actual.native_builder_controls.helper_identity) 'exact qualified helper bytes/identity'
 Need ($helper.bytes -le 1MB -and $value.helper.native_identity -cmatch '^[0-9a-f]{16}:[0-9a-f]{32}$') 'helper bounds'
 if($value.role -ceq 'D'){
  $qualification=Record $value.qualification;Fields $qualification 'schema status author created_utc source_review actual_review operation_id accepted_controller_sources controls owned_lifecycle_closed safety'
  Need ($qualification.schema -ceq 'cho51_startup_qualification_v1' -and $qualification.status -ceq 'QUALIFIED_STARTUP2_MECHANISMS_ONLY' -and $qualification.author -ceq 'project_root' -and (SameRef $qualification.source_review $value.source_review) -and $qualification.owned_lifecycle_closed -is [bool] -and $qualification.owned_lifecycle_closed -and ($qualification.controls -join ',') -ceq 'fast,stall' -and $qualification.operation_id -cne $value.operation_id) 'fresh startup qualification'
  Safety $qualification.safety;SourcesMatch $value.sources $qualification.accepted_controller_sources
  $qualifiedActual=Record $qualification.actual_review;IndependentIdentity $qualifiedActual 'startup actual review';Need ($qualifiedActual.status -ceq 'ACCEPTED_STARTUP2_TESTED_SCOPE' -and $qualifiedActual.operation_id -ceq $qualification.operation_id -and $qualifiedActual.reviewer -cne $review.reviewer -and $qualifiedActual.authors -cnotcontains $qualifiedActual.reviewer) 'independent startup actual review'
  SourcesMatch $value.sources $qualifiedActual.accepted_controller_sources
  Need ($qualifiedActual.startup_source_review_sha256 -ceq $value.source_review.sha256 -and ($qualifiedActual.controls -join ',') -ceq 'fast,stall' -and $qualifiedActual.owned_lifecycle_closed -is [bool] -and $qualifiedActual.owned_lifecycle_closed -and $qualifiedActual.findings -is [array] -and $qualifiedActual.findings.Count -eq 0) 'actual startup source/outcome joins';IntValue $qualifiedActual.actual_tool_exit_code 0 0
  Need ((Utc $review.created_utc) -le (Utc $qualifiedActual.created_utc) -and (Utc $qualifiedActual.created_utc) -le (Utc $qualification.created_utc) -and (Utc $qualification.created_utc) -le (Utc $value.created_utc)) 'review actual qualification admission order'
 }
 Fields $value.environment 'SystemRoot WINDIR PATH HOME USERPROFILE TEMP TMP OMP_NUM_THREADS MKL_NUM_THREADS OPENBLAS_NUM_THREADS CUDA_VISIBLE_DEVICES PYTEST_DISABLE_PLUGIN_AUTOLOAD DOTNET_MultiCoreJitNoProfileGather'
 foreach($key in $value.environment.Keys){Need ($value.environment[$key] -is [string] -and $value.environment[$key] -and -not $value.environment[$key].Contains([char]0) -and $value.environment[$key].Length -le 32768) 'environment entry'}
 foreach($key in @('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','PYTEST_DISABLE_PLUGIN_AUTOLOAD')){Need ($value.environment[$key] -ceq '1') 'one-thread/autoload environment'};Need ($value.environment.CUDA_VISIBLE_DEVICES -ceq '-1') 'hidden GPU'
 Need ($value.environment.DOTNET_MultiCoreJitNoProfileGather -ceq '1') 'fixed probe profile gathering setting'
 Need ($value.environment.SystemRoot -ceq 'C:/Windows' -and $value.environment.WINDIR -ceq 'C:/Windows' -and $value.environment.PATH -ceq ([IO.Path]::GetDirectoryName($runtime.executable.path).Replace('\','/')+';C:/Windows/System32')) 'exact Windows runtime environment'
 foreach($key in @('HOME','USERPROFILE','TEMP','TMP')){Need ($value.environment[$key] -ceq $value.output_root) 'attempt-only environment'}
 $helperBytes=Pin $helper -Collect;Event 'bootstrap_authority_verified';$authority=$true
 # Initial Assembly.Load is explicit exact-byte bootstrap trust, not pre-load native-ID attestation.
 $loadedHelper=[Reflection.Assembly]::Load($helperBytes)
 foreach($row in $inputs.Values){$row.identity=[PNative.Owner]::FileIdentity($row.stream.SafeFileHandle)};$nativeIdsBound=$true
 Need ($inputs[$helper.path].identity -ceq $value.helper.native_identity) 'retained helper native identity';Event 'qualified_helper_loaded'
 $owner=[PNative.Owner]::new($originQpc,$originUtc.ToString('o'),'D:/Aenv/pro3/runs/coordination/PROJECT_STOP.json')
 StartGuard;Check -Work;Event 'native_guard_ready'
 foreach($reference in $runtime.files){[void](Pin $reference)}
 RuntimeCensus;[void](ManagedCoverage);Check -Work
 Need ((Elapsed) -lt 3.5) 'insufficient shared interval for dispatch'
 Ancestors $value.output_root;Need (-not [IO.Directory]::Exists($value.output_root) -and -not [IO.File]::Exists($value.output_root)) 'occupied operation'
 [void][IO.Directory]::CreateDirectory($value.output_root)
 CreateCacheDirectories
 $claim=Publish 'claim.json' ($utf8.GetBytes((@{schema='cho51_startup_claim_v1';operation_id=$value.operation_id;capsule_sha256=$CapsuleSha256;origin_utc=$originUtc.ToString('o');origin_qpc=$originQpc;caller_pid=$callerPid;caller_creation_filetime=$creation}|ConvertTo-Json -Compress)))
 $probePath='D:/Aenv/pro3/tools/local_validation/startup2/'+@{pdh='pdh_probe.ps1';fast='fast_probe.ps1';stall='stall_probe.ps1';empty='empty_probe.ps1';malformed='malformed_probe.ps1';reordered='reordered_probe.ps1';partial='partial_probe.ps1'}[$value.probe]
 $probeArguments=@('-NoLogo','-NoProfile','-NonInteractive','-File',$probePath,$originUtc.ToString('o'),[string]$originQpc,[string]$frequency)
 $savedEnvironment=[Environment]::GetEnvironmentVariables('Process')
 try{
  foreach($key in $savedEnvironment.Keys){[Environment]::SetEnvironmentVariable([string]$key,$null,'Process')}
  foreach($key in $value.environment.Keys){[Environment]::SetEnvironmentVariable($key,$value.environment[$key],'Process')}
  Check -Work;$owner.Start($runtime.executable.path,[string[]]$probeArguments,'D:/Aenv/pro3')
 }finally{
  foreach($key in [Environment]::GetEnvironmentVariables('Process').Keys){[Environment]::SetEnvironmentVariable([string]$key,$null,'Process')}
  foreach($key in $savedEnvironment.Keys){[Environment]::SetEnvironmentVariable([string]$key,[string]$savedEnvironment[$key],'Process')}
 }
 Check -Work
 # From here through registration join there is no Poll/ExitCode/Check/second Dispose on Owner.
 $dispose=[Delegate]::CreateDelegate([Action],$owner,'Dispose');$disposeSource=[Threading.CancellationTokenSource]::new();$disposeRegistration=$disposeSource.Token.Register($dispose);$disposeArmed=$true
 $disposeScheduledQpc=$originQpc+5*$frequency;$disposeSource.CancelAfter([Math]::Max(1,[int][Math]::Ceiling(($disposeScheduledQpc-[Diagnostics.Stopwatch]::GetTimestamp())*1000/$frequency)))
 $cleanupDeadline.CancelAfter([Math]::Max(1,[int](10000-(Elapsed)*1000)))
 $startup.CancelAfter([Threading.Timeout]::Infinite)
 while(-not $disposeSource.IsCancellationRequested){Check;[Threading.Thread]::Sleep(5)}
 $cancelObservedQpc=[Diagnostics.Stopwatch]::GetTimestamp();$disposeRegistration.Dispose();$disposeJoined=$true
 Need ($cancelObservedQpc -ge $disposeScheduledQpc -and ($cancelObservedQpc-$disposeScheduledQpc)/$frequency -le .25) 'late/early cancellation observation'
 Need ((Elapsed) -lt 10) 'original cleanup deadline';$cleanupDeadline.CancelAfter([Threading.Timeout]::Infinite);Event 'dispose_registration_joined'
 $closed=$owner.LimitsVerified -and $owner.AtomicMembership -and $owner.Resumed -and $owner.Reaped -and $owner.JobEmpty -and $owner.JobClosed -and $owner.ProcessClosed -and $owner.ThreadClosed -and $owner.InputClosed -and $owner.StdoutEof -and $owner.StderrEof -and $owner.StdoutReaderClosed -and $owner.StderrReaderClosed -and $owner.StdoutWriterClosed -and $owner.StderrWriterClosed -and $owner.StdoutThreadClosed -and $owner.StderrThreadClosed -and $owner.StdoutJoined -and $owner.StderrJoined -and $owner.WatchdogJoined -and -not $owner.StdoutOverflow -and -not $owner.StderrOverflow -and $null -eq $owner.Fault -and $null -eq $owner.CleanupError -and $null -eq $owner.StdoutError -and $null -eq $owner.StderrError
 Need $closed 'owned diagnostic closure incomplete'
 $stdout=$owner.StdoutText();$stderr=$owner.StderrText();Check
 $stdoutRef=Publish 'stdout.bin' ($utf8.GetBytes($stdout));$stderrRef=Publish 'stderr.bin' ($utf8.GetBytes($stderr))
 $list=[Collections.Generic.List[object]]::new()
 try{
  $previousQpc=$originQpc;$prefix=0
  $markerProtocol=if($value.probe -cin @('empty','malformed','reordered','partial')){'fast'}else{$value.probe}
  $allowed=@{pdh=@('assembly_load_begin','assembly_load_end','counter_ctor_begin','counter_ctor_end','first_sample_begin','first_sample_end','counter_dispose_begin','counter_dispose_end');fast=@('fixture_fast_begin','fixture_fast_end');stall=@('fixture_stall_begin')}[$markerProtocol]
  foreach($line in $stdout.Split([char]10)){
   if(-not $line.Trim()){continue};Need ($list.Count -lt 16 -and $utf8.GetByteCount($line) -le 4096) 'bounded marker stream';$marker=Parse ($utf8.GetBytes($line.TrimEnd([char]13)))
   Fields $marker 'schema sequence event origin_utc origin_qpc frequency qpc elapsed_seconds detail'
   IntValue $marker.sequence $list.Count $list.Count;Need ($marker.schema -ceq 'cho51_startup_probe_marker_v1' -and $marker.origin_utc -ceq $originUtc.ToString('o') -and $marker.origin_qpc -eq $originQpc -and $marker.frequency -eq $frequency) 'marker origin/schema'
   IntValue $marker.origin_qpc $originQpc $originQpc;IntValue $marker.frequency $frequency $frequency;IntValue $marker.qpc $previousQpc ($originQpc+5*$frequency)
   Need (($marker.elapsed_seconds -is [double] -or $marker.elapsed_seconds -is [long] -or $marker.elapsed_seconds -is [int]) -and [double]::IsFinite($marker.elapsed_seconds) -and $marker.elapsed_seconds -ge 0 -and $marker.elapsed_seconds -le 5 -and [Math]::Abs($marker.elapsed_seconds-($marker.qpc-$originQpc)/$frequency) -le .000001) 'marker elapsed type/clock'
   Need ($marker.event -cne 'probe_error') 'probe reported error marker'
   Need ($prefix -lt $allowed.Count -and $marker.event -ceq $allowed[$prefix]) 'ordered marker prefix';$prefix++
   $previousQpc=$marker.qpc
   Need ($marker.detail -is [string] -and $marker.detail.Length -le 1024) 'marker detail';$list.Add($marker)
  }
  Need ($list.Count -gt 0) 'nonempty marker evidence required'
  if($markerProtocol -ceq 'fast'){Need ($prefix -eq 2) 'complete fast markers required'}
  elseif($markerProtocol -ceq 'stall'){Need ($prefix -eq 1) 'exact stall marker required'}
  else{Need ($prefix -ge 1) 'nonempty PDH prefix required'}
 }catch{$markerError=$_.Exception.Message}
 $markers=$list.ToArray()
 if($null -ne $markerError -and $null -eq $failure){$failure='marker evidence refused: '+$markerError}
 Event 'inputs_outputs_verification'
 foreach($row in $inputs.Values){Verify $row};foreach($row in $outputs){Verify $row}
 RuntimeCensus;$managedAfter=ManagedCoverage;OutputCensus
 $reportValue=@{schema='cho51_startup_observation_v1';operation_id=$value.operation_id;role=$value.role;probe=$value.probe;origin=@{utc=$originUtc.ToString('o');qpc=$originQpc;frequency=$frequency};status=$(if($null -eq $markerError){'provisional_diagnostic_only'}else{'refused_marker_evidence'});markers=$markers;marker_error=$markerError;stdout=$stdoutRef;stderr=$stderrRef;claim=$claim;managed_runtime=@{before=$managedBefore;after=$managedAfter;top_level_census_count=$runtimeSet.Count};output_directories=$cacheDirectories;profile_gathering_setting=@{key='DOTNET_MultiCoreJitNoProfileGather';value='1';scope='probe_environment_only_not_runtime_attestation'};exit_code=$null;exit_code_status='unavailable_original_handle_closed_by_dispose';termination_cause='unobserved';deadline=@{target_qpc=$disposeScheduledQpc;cancel_observed_qpc=$cancelObservedQpc;registration_joined=$disposeJoined};owned_lifecycle_closed=$closed;guard_shutdown_pending=$true;safety=$value.safety}
 $report=Publish 'observation.json' ($utf8.GetBytes(($reportValue|ConvertTo-Json -Compress -Depth 16)))
 $journalRaw=$utf8.GetBytes((@{schema='cho51_startup_journal_v1';operation_id=$value.operation_id;events=$events.ToArray()}|ConvertTo-Json -Compress -Depth 8));Need ($journalRaw.Length -le 65536) 'journal bytes';[void](Publish 'journal.json' $journalRaw)
 foreach($row in $inputs.Values){Verify $row};$finalInputsVerified=$true;foreach($row in $outputs){Verify $row}
 OutputCensus
 $finalOutputsVerified=$true;Check
}catch{if($null -eq $failure){$failure=$_.Exception.GetType().Name+': '+$_.Exception.Message}}
finally {
 # Join the registered callback before reading state or touching Owner cleanup.
 if($disposeArmed -and -not $disposeJoined){
  try{$disposeSource.Cancel();$disposeRegistration.Dispose();$disposeJoined=$true}catch{$failure='dispose registration join: '+$_.Exception.Message;$kill.Invoke()}
 }elseif($null -ne $owner -and -not $disposeArmed){
  $cleanupDeadline.CancelAfter([Math]::Max(1,[int](10000-(Elapsed)*1000)))
  try{$owner.Dispose()}catch{$failure='exclusive owner cleanup: '+$_.Exception.Message}
 }
 $filesClosed=$true
 foreach($row in $inputs.Values){try{$row.stream.Dispose()}catch{$filesClosed=$false;if($null -eq $failure){$failure='original input closure: '+$_.Exception.Message}}}
 foreach($row in $outputs){try{$row.stream.Dispose()}catch{$filesClosed=$false;if($null -eq $failure){$failure='original output closure: '+$_.Exception.Message}}}
 try{JoinGuard}catch{$failure='guard closure: '+$_.Exception.Message;$kill.Invoke()}
}
if($null -ne $owner -and ($disposeJoined -or -not $disposeArmed)){
 $custody=@{};foreach($name in @('LimitsVerified','AtomicMembership','Resumed','Reaped','JobEmpty','JobClosed','ProcessClosed','ThreadClosed','InputClosed','StdoutEof','StderrEof','StdoutReaderClosed','StderrReaderClosed','StdoutWriterClosed','StderrWriterClosed','StdoutThreadClosed','StderrThreadClosed','StdoutJoined','StderrJoined','WatchdogJoined','StdoutOverflow','StderrOverflow','Fault','CleanupError','StdoutError','StderrError','CreationFileTime','Pid')){$custody[$name]=$owner.$name}
}
if($null -ne $report){foreach($row in $outputs){if($row.pin.path -ceq $report.path){$report.native_identity=$row.identity}}}
$manifest=@($outputs|ForEach-Object {@{path=$_.pin.path;bytes=$_.pin.bytes;sha256=$_.pin.sha256;native_identity=$_.identity}})
$result=@{schema='cho51_startup_external_return_v1';operation_id=$(if($null -ne $value){$value['operation_id']}else{$null});role=$(if($null -ne $value){$value['role']}else{$null});probe=$(if($null -ne $value){$value['probe']}else{$null});status='refused';failure=$failure;origin=@{utc=$originUtc.ToString('o');qpc=$originQpc;frequency=$frequency};caller=@{pid=$callerPid;creation_filetime=$creation};elapsed_seconds=(Elapsed);authority_verified=$authority;native_ids_bound=$nativeIdsBound;dispose_registration_joined=$disposeJoined;owned_lifecycle_closed=$closed;custody=$custody;original_streams_closed=$filesClosed;final_input_verification=$finalInputsVerified;final_output_verification=$finalOutputsVerified;guard=$guardState;observation=$report;outputs=$manifest;actual_tool_return_pending=$true;exit_code=$null;termination_cause='unobserved';historical_custody_closed=$false;historical_operation_released=$false;historical_retry_allowed=$false;restart_qualified=$false;scientific_admission=$false;candidate_tests_executed=0;successor_controls_executed=0}
if($null -eq $failure -and $null -eq $markerError -and $markers.Count -gt 0 -and $closed -and $disposeJoined -and $filesClosed -and $guardState.closed -and $finalInputsVerified -and $finalOutputsVerified -and (Elapsed) -lt 15){$result.status='observed_diagnostic_only'}
$raw=$utf8.GetBytes(($result|ConvertTo-Json -Compress -Depth 12));Need ($raw.Length -le 1MB) 'return bound';[Console]::Out.WriteLine($utf8.GetString($raw));[Console]::Out.Flush()
$startup.CancelAfter([Threading.Timeout]::Infinite);$hard.CancelAfter([Threading.Timeout]::Infinite);$cleanupDeadline.CancelAfter([Threading.Timeout]::Infinite)
$startupRegistration.Dispose();$startup.Dispose();$cleanupRegistration.Dispose();$cleanupDeadline.Dispose();$hardRegistration.Dispose();$hard.Dispose()
if($null -ne $disposeSource){$disposeSource.Dispose()}
if($result.status -cne 'observed_diagnostic_only'){exit 1}
