param(
 [Parameter(Mandatory=$true)][string]$Request,
 [Parameter(Mandatory=$true)][long]$RequestBytes,
 [Parameter(Mandatory=$true)][string]$RequestSha256,
 [Parameter(Mandatory=$true)][string]$Admission,
 [Parameter(Mandatory=$true)][long]$AdmissionBytes,
 [Parameter(Mandatory=$true)][string]$AdmissionSha256
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$originUtc=[DateTime]::UtcNow
$originQpc=[Diagnostics.Stopwatch]::GetTimestamp()
$frequency=[Diagnostics.Stopwatch]::Frequency
$originalProcess=[Diagnostics.Process]::GetCurrentProcess()
$originalHandle=$originalProcess.SafeHandle
$callerPid=$originalProcess.Id
$callerCreation=$originalProcess.StartTime.ToUniversalTime().ToFileTimeUtc()
$killAction=[Delegate]::CreateDelegate([Action],$originalProcess,'Kill')
$hard=[Threading.CancellationTokenSource]::new()
$hardRegistration=$hard.Token.Register($killAction)
$hard.CancelAfter(245000)
$startup=[Threading.CancellationTokenSource]::new()
$startupRegistration=$startup.Token.Register($killAction)
$startup.CancelAfter(5000)
$inputHandles=[Collections.Generic.List[IO.FileStream]]::new()
$outputHandles=[Collections.Generic.List[IO.FileStream]]::new()
$inputPins=[Collections.Generic.List[object]]::new()
$outputPins=[Collections.Generic.List[object]]::new()
$owner=$null;$failure=$null;$successful=$false;$originRecord=$null;$returnPath=$null;$requestValue=$null;$admissionValue=$null
$preGuard=$null;$preRunspace=$null;$preInvocation=$null
$preState=[hashtable]::Synchronized(@{ready=$false;stop=$false;done=$false;error=$null;samples=0;first=$null;second=$null;last=0L;minimum_ram=[long]::MaxValue;minimum_disk=[long]::MaxValue;peak_private=0L;joined=$false;closed=$false})
$utf8=[Text.UTF8Encoding]::new($false,$true)
function Elapsed {([Diagnostics.Stopwatch]::GetTimestamp()-$originQpc)/$frequency}
function Check {
 if((Elapsed) -ge 240 -or [DateTime]::UtcNow -ge $originUtc.AddSeconds(240)){throw 'original L caller work deadline'}
 if(-not $preState.ready -or $preState.done -or $null -ne $preState.error -or $preInvocation.IsCompleted -or
    ([Diagnostics.Stopwatch]::GetTimestamp()-$preState.last)/$frequency -gt 0.25){$killAction.Invoke();throw 'independent original-caller guard stale/faulted'}
 if($null -ne $owner){$owner.Check()}
}
function StartPreGuard {
 $script=@'
param($process,$kill,$origin,$utcOrigin,$frequency,$shared)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$counter=$null
try {
 [void][Reflection.Assembly]::Load('System.Diagnostics.PerformanceCounter')
 $counter=[Diagnostics.PerformanceCounter]::new('Memory','Available Bytes')
 while(-not $shared.stop){
  $tick=[Diagnostics.Stopwatch]::GetTimestamp()
  if(($tick-$origin)/$frequency -lt 0 -or ($tick-$origin)/$frequency -ge 240 -or [DateTime]::UtcNow -ge $utcOrigin.AddSeconds(240)){throw 'independent caller deadline'}
  if($shared.last -ne 0 -and ($tick-$shared.last)/$frequency -gt 0.25){throw 'independent caller sample interval'}
  $stopFile='D:/Aenv/pro3/runs/coordination/PROJECT_STOP.json'
  $directory=[IO.FileInfo]::new($stopFile).Directory
  while($null -ne $directory){$attributes=[IO.File]::GetAttributes($directory.FullName);if(($attributes -band [IO.FileAttributes]::ReparsePoint) -or -not($attributes -band [IO.FileAttributes]::Directory)){throw 'independent stop ancestry'};$directory=$directory.Parent}
  try{[void][IO.File]::GetAttributes($stopFile);throw 'independent project stop present'}catch [IO.FileNotFoundException]{}
  $sample=$counter.NextSample()
  if($sample.CounterType.ToString() -cne 'NumberOfItems64'){throw 'independent RAM sensor type'}
  $available=[long]$sample.RawValue;$disk=[IO.DriveInfo]::new('D').AvailableFreeSpace
  [Threading.Monitor]::Enter($shared.SyncRoot)
  try{$process.Refresh();$private=$process.PrivateMemorySize64}finally{[Threading.Monitor]::Exit($shared.SyncRoot)}
  if(([Diagnostics.Stopwatch]::GetTimestamp()-$tick)/$frequency -gt 0.25){throw 'independent sample duration'}
  if($available -lt 4GB -or $disk -lt 20GB -or $private -gt 4096MB){throw 'independent caller memory/disk floor/cap'}
  $row=@{qpc=$tick;available_ram_bytes=$available;free_disk_bytes=$disk;caller_private_bytes=$private}
  $shared.samples++;$shared.minimum_ram=[Math]::Min([long]$shared.minimum_ram,$available);$shared.minimum_disk=[Math]::Min([long]$shared.minimum_disk,[long]$disk);$shared.peak_private=[Math]::Max([long]$shared.peak_private,[long]$private);$shared.last=$tick
  if($null -eq $shared.first){$shared.first=$row}
  if(-not $shared.ready -and ($tick-$shared.first.qpc)/$frequency -ge 0.2){$shared.second=$row;$shared.ready=$true}
  [Threading.Thread]::Sleep(100)
 }
}catch{$shared.error=$_.Exception.GetType().Name+': '+$_.Exception.Message;$kill.Invoke()}
finally{if($null -ne $counter){$counter.Dispose()};$shared.done=$true}
'@
 $script:preRunspace=[Management.Automation.Runspaces.RunspaceFactory]::CreateRunspace();$preRunspace.Open()
 $script:preGuard=[Management.Automation.PowerShell]::Create();$preGuard.Runspace=$preRunspace
 [void]$preGuard.AddScript($script).AddArgument($originalProcess).AddArgument($killAction).AddArgument($originQpc).AddArgument($originUtc).AddArgument($frequency).AddArgument($preState)
 $script:preInvocation=$preGuard.BeginInvoke()
 while(-not $preState.ready){if($preInvocation.IsCompleted -or $null -ne $preState.error){throw 'independent caller guard startup'};[Threading.Thread]::Sleep(10)}
}
function StopPreGuard {
 if($null -eq $preInvocation){return}
 $timer=[Threading.CancellationTokenSource]::new();$registration=$timer.Token.Register($killAction);$timer.CancelAfter(1000)
 try {
  $preState.stop=$true;$completion=$preInvocation.AsyncWaitHandle
  if(-not $completion.WaitOne(1000)){$killAction.Invoke();throw 'independent caller guard join timeout'}
  [void]$preGuard.EndInvoke($preInvocation)
  if($preGuard.HadErrors -or -not $preState.done -or $null -ne $preState.error){$killAction.Invoke();throw 'independent caller guard completion'}
  $preState.joined=$true;$completion.Dispose();$preGuard.Dispose();$preRunspace.Dispose();$preState.closed=$true
 }finally{$timer.CancelAfter([Threading.Timeout]::Infinite);$registration.Dispose();$timer.Dispose()}
}
function Pin([string]$Path,[long]$Bytes,[string]$Digest) {
 Check
 if($Digest -cnotmatch '^[0-9a-f]{64}$' -or $Bytes -lt 0 -or $Bytes -gt 64MB){throw 'caller pin shape/cap'}
 $full=[IO.Path]::GetFullPath($Path)
 if($full.Replace('\','/') -cne $Path.Replace('\','/') -or $Path.Contains('..')){throw 'caller canonical path'}
 $ancestor=[IO.FileInfo]::new($full).Directory
 while($null -ne $ancestor){if([IO.File]::GetAttributes($ancestor.FullName) -band [IO.FileAttributes]::ReparsePoint){throw 'caller pin reparse ancestry'};$ancestor=$ancestor.Parent}
 if([IO.File]::GetAttributes($full) -band [IO.FileAttributes]::ReparsePoint){throw 'caller pin reparse leaf'}
 $stream=[IO.FileStream]::new($full,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
 $inputHandles.Add($stream)
 if($stream.Length -ne $Bytes){throw 'caller pin length'}
 $hash=[Security.Cryptography.IncrementalHash]::CreateHash([Security.Cryptography.HashAlgorithmName]::SHA256)
 $memory=[IO.MemoryStream]::new()
 try {
  $buffer=[byte[]]::new(65536)
  do {Check;$count=$stream.Read($buffer,0,$buffer.Length);if($count){$hash.AppendData($buffer,0,$count);$memory.Write($buffer,0,$count)}}while($count)
  if([Convert]::ToHexString($hash.GetHashAndReset()).ToLowerInvariant() -cne $Digest){throw 'caller pin digest'}
  $stream.Position=0
  $inputPins.Add(@{stream=$stream;bytes=$Bytes;sha256=$Digest;identity=$null})
  return ,$memory.ToArray()
 } finally {$hash.Dispose();$memory.Dispose()}
}
function Parse([byte[]]$Raw) {
 if($Raw.Length -gt 8MB){throw 'caller JSON cap'}
 $document=[Text.Json.JsonDocument]::Parse($utf8.GetString($Raw))
 $budget=@{nodes=0}
 function Visit($Node,[int]$Depth,$Budget) {
  $Budget.nodes++
  if($Depth -gt 32 -or $Budget.nodes -gt 200000){throw 'caller JSON structure cap'}
  if($Node.ValueKind -eq [Text.Json.JsonValueKind]::Object){
   $seen=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
   foreach($property in $Node.EnumerateObject()){if(-not $seen.Add($property.Name)){throw 'duplicate JSON key'};Visit $property.Value ($Depth+1) $Budget}
  } elseif($Node.ValueKind -eq [Text.Json.JsonValueKind]::Array){foreach($item in $Node.EnumerateArray()){Visit $item ($Depth+1) $Budget}}
 }
 try {Visit $document.RootElement 0 $budget;return ($utf8.GetString($Raw)|ConvertFrom-Json -AsHashtable -Depth 32 -DateKind String)}finally{$document.Dispose()}
}
function EvidencePath($Reference) {
 $path=$Reference.path
 if(-not [IO.Path]::IsPathRooted($path)){$path='D:/Aenv/pro3/'+$path}
 if([IO.Path]::GetFullPath($path).Replace('\','/') -cne $path -or $Reference.sha256 -cnotmatch '^[0-9a-f]{64}$'){throw 'canonical evidence reference'}
 return $path
}
function SameReference($Left,$Right) {
 return (EvidencePath $Left) -ceq (EvidencePath $Right) -and $Left.bytes -eq $Right.bytes -and $Left.sha256 -ceq $Right.sha256
}
function ReviewedSources($Review) {
 $pins=@{}
 foreach($path in $Review.sources.Keys){
  $absolute=if([IO.Path]::IsPathRooted($path)){$path}else{'D:/Aenv/pro3/'+$path}
  if(-not $absolute.StartsWith('D:/Aenv/pro3/',[StringComparison]::Ordinal) -or [IO.Path]::GetFullPath($absolute).Replace('\','/') -cne $absolute -or $pins.ContainsKey($absolute)){throw 'review source scope/alias'}
  $pins[$absolute]=$Review.sources[$path]
 }
 if($pins.Count -lt 1 -or $pins.Count -gt 2000){throw 'bounded review source set'}
 return $pins
}
function Publish([string]$Path,$Value) {
 Check
 $raw=$utf8.GetBytes(($Value|ConvertTo-Json -Compress -Depth 32))
 if($raw.Length -gt 8MB -or $outputHandles.Count -ge 16){throw 'caller output cap'}
 $stream=[IO.FileStream]::new($Path,[IO.FileMode]::CreateNew,[IO.FileAccess]::ReadWrite,[IO.FileShare]::Read)
 $outputHandles.Add($stream)
 $stream.Write($raw,0,$raw.Length);$stream.Flush($true);$stream.Position=0
 $copy=[byte[]]::new($raw.Length);$offset=0
 while($offset -lt $copy.Length){Check;$count=$stream.Read($copy,$offset,$copy.Length-$offset);if($count -le 0){throw 'caller output short readback'};$offset+=$count}
 $digest=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($raw)).ToLowerInvariant()
 if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($copy)).ToLowerInvariant() -cne $digest){throw 'caller output original readback'}
 $outputPins.Add(@{stream=$stream;bytes=$raw.Length;sha256=$digest;identity=[PNative.Owner]::FileIdentity($stream.SafeFileHandle)})
 return @{path=$Path.Replace('\','/');bytes=$raw.Length;sha256=$digest}
}
function VerifyOriginals {
 foreach($pin in @($inputPins.ToArray())+@($outputPins.ToArray())){
  Check
  $stream=$pin.stream
  if($stream.Length -ne $pin.bytes -or [PNative.Owner]::FileIdentity($stream.SafeFileHandle) -cne $pin.identity){throw 'caller final original identity/length'}
  $hash=[Security.Cryptography.IncrementalHash]::CreateHash([Security.Cryptography.HashAlgorithmName]::SHA256)
  try {
   $stream.Position=0;$buffer=[byte[]]::new(65536)
   do{Check;$count=$stream.Read($buffer,0,$buffer.Length);if($count){$hash.AppendData($buffer,0,$count)}}while($count)
   if([Convert]::ToHexString($hash.GetHashAndReset()).ToLowerInvariant() -cne $pin.sha256){throw 'caller final original bytes'}
  }finally{$hash.Dispose()}
 }
}
try {
 StartPreGuard
 $requestRaw=Pin $Request $RequestBytes $RequestSha256
 $admissionRaw=Pin $Admission $AdmissionBytes $AdmissionSha256
 $requestValue=Parse $requestRaw;$admissionValue=Parse $admissionRaw
 if($requestValue.stop_path -cne 'D:/Aenv/pro3/runs/coordination/PROJECT_STOP.json'){throw 'exact project-local stop path'}
 if($requestValue.schema -cne 'cho51_l_request_v1' -or $admissionValue.schema -cne 'cho51_l_admission_v1' -or
    $requestValue.stage -cne 'L' -or $admissionValue.stage -cne 'L' -or $admissionValue.issuer -cne 'project_root' -or
    $admissionValue.authorized_new_l_only -isnot [bool] -or -not $admissionValue.authorized_new_l_only -or
    $requestValue.operation_id -cne $admissionValue.operation_id){throw 'Root L request/admission boundary'}
 if($admissionValue.request.path -cne $Request -or $admissionValue.request.bytes -ne $RequestBytes -or $admissionValue.request.sha256 -cne $RequestSha256){throw 'request/admission exact pin'}
 $source=$requestValue.source_manifest
 $manifest=Parse (Pin $source.path $source.bytes $source.sha256)
 if($manifest.schema -cne 'cho51_l_source_manifest_v1' -or $manifest.project_root -cne 'D:/Aenv/pro3' -or $manifest.files.Count -lt 1 -or $manifest.files.Count -gt 2000){throw 'fixed source manifest root/schema/count'}
 $sourcePins=@{}
 foreach($reference in $manifest.files){if($sourcePins.ContainsKey($reference.path)){throw 'duplicate source path'};$sourcePins[$reference.path]=$reference}
 $root=$manifest.project_root
 $implementationRef=$admissionValue.implementation_review
 $implementation=Parse (Pin (EvidencePath $implementationRef) $implementationRef.bytes $implementationRef.sha256)
 if($implementation.status -cne 'ACCEPTED_SOURCE_L1' -or $implementation.authors -ccontains $implementation.reviewer -or -not $implementation.reviewer -or $implementation.findings.Count -ne 0){throw 'independent exact L source review'}
 $reviewPins=ReviewedSources $implementation
 if($reviewPins.Count -ne $sourcePins.Count){throw 'source review/manifest cardinality'}
 foreach($path in $sourcePins.Keys){
  if(-not $reviewPins.ContainsKey($path) -or $reviewPins[$path].bytes -ne $sourcePins[$path].bytes -or $reviewPins[$path].sha256 -cne $sourcePins[$path].sha256){throw 'unreviewed source bytes before bootstrap'}
 }
 if(-not $sourcePins.ContainsKey($root+'/tools/local_validation/lhost1/bootstrap.py') -or -not $sourcePins.ContainsKey($root+'/tools/local_validation/lhost1/invoke_l.ps1') -or [IO.Path]::GetFullPath($PSCommandPath).Replace('\','/') -cne $root+'/tools/local_validation/lhost1/invoke_l.ps1'){throw 'reviewed fixed bootstrap/caller'}
 if(-not (SameReference $implementation.runtime_manifest $requestValue.runtime_manifest)){throw 'unreviewed runtime manifest before native/bootstrap effects'}
 # L never compiles a helper. Consume exactly the separately accepted fresh
 # Q artifact and its original native identity.
 $adoptionRef=$requestValue.adoption
 $adoption=Parse (Pin $adoptionRef.path $adoptionRef.bytes $adoptionRef.sha256)
 if(-not (SameReference $adoption.implementation_review $implementationRef) -or -not (SameReference $admissionValue.adoption $adoptionRef)){throw 'implementation adoption reference mismatch'}
 $qualificationRef=$adoption.qualification_q
 $qualification=Parse (Pin $qualificationRef.path $qualificationRef.bytes $qualificationRef.sha256)
 $qActualRef=$qualification.actual_review
 $qActualPath=if([IO.Path]::IsPathRooted($qActualRef.path)){$qActualRef.path}else{$root+'/'+$qActualRef.path}
 $qActual=Parse (Pin $qActualPath $qActualRef.bytes $qActualRef.sha256)
 $qSourceRef=$qualification.source_review
 $qSource=Parse (Pin (EvidencePath $qSourceRef) $qSourceRef.bytes $qSourceRef.sha256)
 if($qSource.status -cne 'ACCEPTED_SOURCE_LQ1' -or $qSource.authors -ccontains $qSource.reviewer -or $qActual.authors -ccontains $qActual.reviewer -or $qActual.reviewer -ceq $qSource.reviewer -or $qActual.source_review_sha256 -cne $qSourceRef.sha256 -or $qSource.findings.Count -ne 0 -or $qActual.findings.Count -ne 0){throw 'Q exact independent source/actual chain'}
 $qPins=ReviewedSources $qSource
 foreach($path in $sourcePins.Keys){if(-not $qPins.ContainsKey($path) -or $qPins[$path].bytes -ne $sourcePins[$path].bytes -or $qPins[$path].sha256 -cne $sourcePins[$path].sha256){throw 'fresh Q does not cover bootstrap sources'}}
 if($qualification.author -cne 'project_root' -or $qualification.status -cne 'QUALIFIED_LQ1_MECHANISMS_ONLY' -or
    $qActual.status -cne 'ACCEPTED_LQ1_TESTED_SCOPE' -or $qActual.operation_id -cne $qualification.operation_id -or
    $qActual.actual_tool_exit_code -ne 0 -or $qActual.new_operation_owned_lifecycle_closed -isnot [bool] -or -not $qActual.new_operation_owned_lifecycle_closed){throw 'fresh accepted Q helper authority'}
 $nativePin=$qualification.native_helper
 if($nativePin.path -cne $qActual.native_helper.path -or $nativePin.bytes -ne $qActual.native_helper.bytes -or $nativePin.sha256 -cne $qActual.native_helper.sha256 -or $nativePin.bytes -gt 1MB){throw 'exact Q managed helper artifact'}
 $nativePath=if([IO.Path]::IsPathRooted($nativePin.path)){$nativePin.path}else{$root+'/'+$nativePin.path}
 $nativeRaw=Pin $nativePath $nativePin.bytes $nativePin.sha256
 $nativeStream=$inputHandles[$inputHandles.Count-1]
 [void][Reflection.Assembly]::Load($nativeRaw)
 $nativeIdentity=[PNative.Owner]::FileIdentity($nativeStream.SafeFileHandle)
 if($nativeIdentity -cne $qualification.native_builder_controls.helper_identity -or $nativeIdentity -cne $qActual.native_builder_controls.helper_identity){throw 'Q managed helper native identity'}
 foreach($key in @('l_two_process_limits_query_verified','l_empty_job_closed')){
  if($qualification.native_builder_controls[$key] -isnot [bool] -or -not $qualification.native_builder_controls[$key] -or
     $qActual.native_builder_controls[$key] -isnot [bool] -or -not $qActual.native_builder_controls[$key]){throw 'Q-qualified finite L two-process custody required'}
 }
 $owner=[PNative.Owner]::new($originQpc,$originUtc.ToString('o'),$requestValue.stop_path,[uint32]2)
 $owner.Check();$first=$owner.Sample();[Threading.Thread]::Sleep(210);$owner.Check();$second=$owner.Sample()
 $startup.CancelAfter([Threading.Timeout]::Infinite)
 foreach($reference in $manifest.files){[void](Pin $reference.path $reference.bytes $reference.sha256)}
 $runtimeRef=$requestValue.runtime_manifest
 $runtime=Parse (Pin $runtimeRef.path $runtimeRef.bytes $runtimeRef.sha256)
 if($runtime.schema -cne 'cho51_l_runtime_manifest_v1' -or $runtime.root -cne $requestValue.roots.runtime -or $runtime.executable -cne ($runtime.root+'/python.exe') -or $requestValue.roots.project -cne $root -or $requestValue.roots.site -cne ($root+'/.venv/Lib/site-packages') -or $requestValue.cwd -cne $root){throw 'exact runtime/executable/cwd/roots'}
 $pythonPin=@($runtime.files|Where-Object {$_.path -ceq $runtime.executable})
 if($pythonPin.Count -ne 1){throw 'one exact interpreter pin'}
 if($runtime.files.Count -lt 1 -or $runtime.files.Count -gt 2000){throw 'bounded runtime closure'}
 $runtimePaths=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
 foreach($runtimePin in $runtime.files){
  if(-not $runtimePin.path.StartsWith($runtime.root+'/',[StringComparison]::Ordinal) -or -not $runtimePaths.Add($runtimePin.path)){throw 'runtime closure scope/alias'}
  [void](Pin $runtimePin.path $runtimePin.bytes $runtimePin.sha256)
 }
 foreach($pin in $inputPins){$pin.identity=[PNative.Owner]::FileIdentity($pin.stream.SafeFileHandle)}
 $attempt=[IO.Path]::GetFullPath($requestValue.attempt_root)
 if($attempt.Replace('\','/') -cne $requestValue.attempt_root -or [IO.Path]::GetFileName($attempt) -cne $requestValue.operation_id -or $requestValue.operation_id -cnotmatch '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'){throw 'caller UUID attempt namespace'}
 $attemptParent=[IO.DirectoryInfo]::new([IO.Path]::GetDirectoryName($attempt))
 $ancestor=$attemptParent
 while($null -ne $ancestor){$attributes=[IO.File]::GetAttributes($ancestor.FullName);if(($attributes -band [IO.FileAttributes]::ReparsePoint) -or -not($attributes -band [IO.FileAttributes]::Directory)){throw 'caller claim ancestry'};$ancestor=$ancestor.Parent}
 [void](Publish ($attemptParent.FullName+'/external-claim_'+$requestValue.operation_id+'.json') @{schema='cho51_l_external_claim_v1';operation_id=$requestValue.operation_id;request_sha256=$RequestSha256;admission_sha256=$AdmissionSha256;original_utc=$originUtc.ToString('o');original_qpc=$originQpc;caller_pid=$callerPid;caller_creation_filetime=$callerCreation;attempt_root=$requestValue.attempt_root})
 $bootstrap=$root+'/tools/local_validation/lhost1/bootstrap.py'
 if(-not $sourcePins.ContainsKey($bootstrap)){throw 'one pinned bootstrap'}
 $lPhase=$root+'/runs/coordination/cho51_p3_loader_collection_l1'
 if($requestValue.attempt_root -cne ($lPhase+'/attempts/'+$requestValue.operation_id) -or $requestValue.environment.PYTHONPYCACHEPREFIX -cne ($lPhase+'/disabled-bytecode/'+$requestValue.operation_id)){throw 'fixed attempt/cache namespace'}
 $expectedChild=@($runtime.executable,'-I','-S','-B','-X',('pycache_prefix='+$requestValue.environment.PYTHONPYCACHEPREFIX),$bootstrap,'child',
  '{request_path}','{request_bytes}','{request_sha256}','{admission_path}','{admission_bytes}','{admission_sha256}','{origin_utc}','{origin_ticks}','{result_handle}')
 if($requestValue.command.Count -ne $expectedChild.Count -or $admissionValue.permitted_command.Count -ne $expectedChild.Count){throw 'exact child command length'}
 for($i=0;$i -lt $expectedChild.Count;$i++){if($requestValue.command[$i] -cne $expectedChild[$i] -or $admissionValue.permitted_command[$i] -cne $expectedChild[$i]){throw 'fixed reviewed child vector'}}
 $environment=$requestValue.environment
 if($environment -isnot [hashtable] -or $environment.Count -eq 0 -or $environment.Count -gt 128){throw 'explicit bounded environment'}
 $environmentNames=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
 foreach($key in $environment.Keys){
  if($key -isnot [string] -or $environment[$key] -isnot [string] -or -not $key -or $key.Contains('=') -or $key.Contains([char]0) -or $environment[$key].Contains([char]0) -or -not $environmentNames.Add($key)){throw 'environment shape/alias'}
 }
 foreach($key in @('SystemRoot','WINDIR','TEMP','TMP','HOME','USERPROFILE','PATH','XDG_CONFIG_HOME','XDG_CACHE_HOME','MPLCONFIGDIR','PYTHONPYCACHEPREFIX')){if(-not $environment.ContainsKey($key) -or -not $environment[$key]){throw 'required Windows/isolated environment'}}
 $allowedEnvironment=@('SystemRoot','WINDIR','TEMP','TMP','HOME','USERPROFILE','PATH','XDG_CONFIG_HOME','XDG_CACHE_HOME','MPLCONFIGDIR','PYTHONPYCACHEPREFIX','PYTEST_DISABLE_PLUGIN_AUTOLOAD','OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS','CUDA_VISIBLE_DEVICES','PYTHONDONTWRITEBYTECODE','PYTHONNOUSERSITE','COMSPEC','PATHEXT','SystemDrive','LOCALAPPDATA','APPDATA','LANG','LC_ALL','TZ')
 foreach($key in $environment.Keys){if($allowedEnvironment -cnotcontains $key){throw 'environment outside exact allowlist'}}
 foreach($key in @('PYTHONPATH','PYTHONHOME','PYTHONSTARTUP','PYTEST_ADDOPTS','PYTEST_PLUGINS','GIT_CONFIG','GIT_DIR','GIT_WORK_TREE')){if($environmentNames.Contains($key)){throw 'ambient environment override'}}
 $fixedEnvironment=@{PYTEST_DISABLE_PLUGIN_AUTOLOAD='1';OMP_NUM_THREADS='1';MKL_NUM_THREADS='1';OPENBLAS_NUM_THREADS='1';NUMEXPR_NUM_THREADS='1';CUDA_VISIBLE_DEVICES='-1';PYTHONDONTWRITEBYTECODE='1';PYTHONNOUSERSITE='1'}
 foreach($key in $fixedEnvironment.Keys){if($environment[$key] -cne $fixedEnvironment[$key]){throw 'fixed environment boundary'}}
 $ticks=([string]$originQpc)+':'+([string]$frequency)+':'+([string]$callerPid)+':'+([string]$callerCreation)
 $arguments=@('-I','-S','-B','-X',('pycache_prefix='+$requestValue.environment.PYTHONPYCACHEPREFIX),$bootstrap,'parent',
              $Request,[string]$RequestBytes,$RequestSha256,$Admission,[string]$AdmissionBytes,$AdmissionSha256,$originUtc.ToString('o'),$ticks)
 # PNative's Q-qualified three-argument interface inherits this process's
 # environment. Restrict only this owned caller, restore it even on refusal.
 $savedEnvironment=[Environment]::GetEnvironmentVariables('Process')
 try {
  foreach($key in $savedEnvironment.Keys){[Environment]::SetEnvironmentVariable([string]$key,$null,'Process')}
  foreach($key in $environment.Keys){[Environment]::SetEnvironmentVariable($key,$environment[$key],'Process')}
  Check
  $owner.Start($runtime.executable,[string[]]$arguments,$requestValue.cwd)
 } finally {
  foreach($key in [Environment]::GetEnvironmentVariables('Process').Keys){[Environment]::SetEnvironmentVariable([string]$key,$null,'Process')}
  foreach($key in $savedEnvironment.Keys){[Environment]::SetEnvironmentVariable([string]$key,[string]$savedEnvironment[$key],'Process')}
 }
 while(-not $owner.Poll()){Check;[Threading.Thread]::Sleep(100)}
 $supervisorExit=$owner.ExitCode()
 $owner.Dispose()
 $stdout=$owner.StdoutText();$stderr=$owner.StderrText()
 if($supervisorExit -ne 0){throw 'L parent returned refusal'}
 $parentReceipt=Parse $utf8.GetBytes($stdout)
 if($parentReceipt.schema -cne 'cho51_l_parent_return_v1' -or $parentReceipt.status -cne 'provisional-complete'){throw 'incomplete L parent receipt'}
 VerifyOriginals
 $successful=$true
} catch {$failure=$_.Exception.GetType().Name+': '+$_.Exception.Message}
finally {
 if($null -ne $owner){$owner.Dispose()}
 foreach($stream in $inputHandles){$stream.Dispose()}
 foreach($stream in $outputHandles){$stream.Dispose()}
 StopPreGuard
}
$closed=$null -ne $owner -and $owner.Reaped -and $owner.JobEmpty -and $owner.JobClosed -and $owner.ProcessClosed -and $owner.ThreadClosed -and $owner.InputClosed -and $owner.StdoutEof -and $owner.StderrEof -and $owner.StdoutReaderClosed -and $owner.StderrReaderClosed -and $owner.StdoutWriterClosed -and $owner.StderrWriterClosed -and $owner.StdoutThreadClosed -and $owner.StderrThreadClosed -and $owner.StdoutJoined -and $owner.StderrJoined -and -not $owner.StdoutOverflow -and -not $owner.StderrOverflow -and $owner.WatchdogJoined -and $null -eq $owner.CleanupError
$receipt=@{schema='cho51_l_external_caller_return_v1';operation_id=$null;origin=@{utc=$originUtc.ToString('o');qpc=$originQpc;qpc_frequency=$frequency};
 caller_identity=@{process_id=$callerPid;creation_filetime=$callerCreation};status='refused';failure=$failure;owned_lifecycle_closed=$closed;
 elapsed_seconds=(Elapsed);independent_caller_guard=$preState;actual_tool_return_pending=$true;historical_custody_closed=$false;historical_operation_released=$false;historical_retry_allowed=$false;
 restart_qualified=$false;scientific_admission=$false;candidate_tests_executed=0;successor_controls_executed=0}
if($null -ne $requestValue){$receipt.operation_id=$requestValue.operation_id}
if($successful -and $closed -and (Elapsed) -lt 245){$receipt.status='provisional-complete'}
$hard.CancelAfter([Threading.Timeout]::Infinite)
$startupRegistration.Dispose();$startup.Dispose();$hardRegistration.Dispose();$hard.Dispose()
$receipt|ConvertTo-Json -Depth 16 -Compress
if($receipt.status -cne 'provisional-complete'){exit 1}
