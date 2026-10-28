param(
 [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$RequestSha256,
 [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$AdmissionSha256
)
$ErrorActionPreference='Stop'
$entry=[DateTimeOffset]::UtcNow
$watch=[Diagnostics.Stopwatch]::StartNew()
$root='D:\Aenv\pro3'
$run=Join-Path $root 'runs\coordination\cho51_p3_contracts_20261027_v1'
$scope='cho51_p3_contracts_native_preparation_001'
$testScope='cho51_p3_contracts_20261027_v1_tests'
$runtimeRoot='C:\Users\aladdin-alyanai\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell'
$executable=Join-Path $runtimeRoot 'pwsh.exe'
$sourceReviewSha='ab2df55aa4d36c66ce7f7d238f71683eddcb7dd773543c01da08dac4790df65a'
$prepareSha='c6817bd7dd7840509da6973a4cfdfd375134e6550200f359750448de510275ed'
$nativeSha='f885c47e997bfa9902790bdf5f7fd3502b5b153229719475bf34934102e061bb'
$sourceScopePath='D:\Aenv\pro2\WORK\resume-20261027-002\coordination\ROOT_PRO3_NEW_FINITE_SOURCE_ONLY_COEXISTENCE_SCOPE_009_001.json'
$sourceScopeSha='b04507102cc00306e99ce9992cd0a526da03101e7d972e79eed6d20aab354739'
$sourceAdoptionPath='D:\Aenv\pro2\WORK\resume-20261027-002\coordination\ROOT_PRO3_SOURCE_ONLY_COEXISTENCE009_DIFFERENT_REVIEW_ADOPTION_001.json'
$sourceAdoptionSha='29dce6bd6b7767449b0bc28d8daeed1023581748d82be41d4eb82cabcf8804ab'
$pauses=@('20261007','20261012','20261013','20261015','20261025')|ForEach-Object{"D:\Aenv\pro2\WORK\resume-$_-001\coordination\PRO2_REQUEST_PRO3_PAUSE.json"}
$stopAt=$entry.AddSeconds(225)
$cleanupEnd=$entry.AddSeconds(270)
$finalEnd=$entry.AddSeconds(285)
$hardEnd=$entry.AddSeconds(300)
$script:preflightDeadline=$stopAt
$bootstrap=[Collections.Generic.List[object]]::new()
$held=[Collections.Generic.List[object]]::new()
$startup=[Collections.Generic.List[object]]::new()
$errors=[Collections.Generic.List[string]]::new()
$process=$null;$tree=$null;$outDrain=$null;$errDrain=$null
$started=$false;$attemptWritten=$false;$nativeLoaded=$false;$reaped=$false
$stdoutEof=$false;$stderrEof=$false;$discoveryComplete=$true;$exitCode=$null
$pinsSha=$null;$minimumRam=[uint64]::MaxValue;$minimumDisk=[uint64]::MaxValue
$oldTemp=$env:TEMP;$oldTmp=$env:TMP
function Need($condition,[string]$message){if(-not $condition){throw $message}}
function Check-Time([double]$seconds=225){Need ($watch.Elapsed.TotalSeconds -lt $seconds -and [DateTimeOffset]::UtcNow -lt $entry.AddSeconds($seconds)) 'Preparation UTC/monotonic deadline reached'}
function Check-Pauses{foreach($path in $pauses){Need (-not (Test-Path -LiteralPath $path)) 'Genuine peer pause requested'}}
function Direct-Path([string]$path){
 Need ([IO.Path]::IsPathFullyQualified($path) -and [IO.Path]::GetFullPath($path) -ieq $path -and -not $path.StartsWith('\\') -and -not $path.Substring(2).Contains(':')) 'Direct local absolute bootstrap path required'
 foreach($part in $path.Substring(3).Split('\')){Need ($part -ne '' -and -not $part.EndsWith('.') -and -not $part.EndsWith(' ') -and $part -notmatch '[~<>|?*]' -and $part -notmatch '^(?i:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(\.|$)') 'Bootstrap path alias refused'}
 $current=$path
 while($current){$item=Get-Item -LiteralPath $current -Force;Need (-not ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -and -not $item.LinkType) 'Bootstrap reparse/link path refused';$current=[IO.Path]::GetDirectoryName($current)}
}
function Resource-Sample{
 Check-Time;Check-Pauses
 $memory=CimCmdlets\Get-CimInstance -ClassName Win32_OperatingSystem -OperationTimeoutSec 3
 Need ($null -ne $memory -and $memory.FreePhysicalMemory -gt 0) 'Available physical memory observation required'
 $ram=[uint64]$memory.FreePhysicalMemory*1024
 $disk=[uint64]([IO.DriveInfo]::new('D:\').AvailableFreeSpace)
 $script:minimumRam=[math]::Min($script:minimumRam,$ram);$script:minimumDisk=[math]::Min($script:minimumDisk,$disk)
 Need ($ram -ge 4GB -and $disk -ge 20GB) 'Preparation startup/active4GiB or disk20GiB floor refused'
 return [ordered]@{observed_utc=[DateTimeOffset]::UtcNow.ToString('o');available_ram_bytes=$ram;free_disk_bytes=$disk;method='local built-in CIM FreePhysicalMemory KiB and DriveInfo; before Add-Type'}
}
function Json-Scalar($element,[int]$depth=0){
 Check-Time
 $script:controlJsonNodes++
 Need ($depth -le 32 -and $script:controlJsonNodes -le 100000) 'Preparation metadata depth/aggregate node bound exceeded'
 switch($element.ValueKind.ToString()){
  'Object' {$result=[Collections.Generic.Dictionary[string,object]]::new([StringComparer]::Ordinal);foreach($property in $element.EnumerateObject()){Need ($result.Count -lt 30000 -and -not $result.ContainsKey($property.Name)) 'Duplicate/excessive metadata object';$result.Add($property.Name,(Json-Scalar $property.Value ($depth+1)))};return ,$result}
  'Array' {$result=[Collections.Generic.List[object]]::new();foreach($member in $element.EnumerateArray()){Need ($result.Count -lt 30000) 'Excessive metadata array';$result.Add((Json-Scalar $member ($depth+1)))};return ,($result.ToArray())}
  'String' {$result=$element.GetString();Need ($result.Length -le 32768) 'Preparation metadata string bound';return $result}
  'Number' {$integer=0L;Need ($element.TryGetInt64([ref]$integer)) 'Only exact Int64 preparation metadata numbers admitted';return $integer}
  'True' {return $true}
  'False' {return $false}
  'Null' {return $null}
  default {throw 'Unsupported preparation metadata'}
 }
}
function Parse-Control([byte[]]$raw){Need ($raw.Length -gt 0 -and $raw.Length -le 8388608) 'Preparation metadata8MiB bound exceeded';$script:controlJsonNodes=0;$options=[Text.Json.JsonDocumentOptions]::new();$options.MaxDepth=32;$document=[Text.Json.JsonDocument]::Parse([ReadOnlyMemory[byte]]::new($raw),$options);try{return ,(Json-Scalar $document.RootElement)}finally{$document.Dispose()}}
function Text($value,[string]$name,[string]$expected){Need ($value.ContainsKey($name) -and $value[$name] -is [string] -and $value[$name] -ceq $expected) ('Exact preparation text required: '+$name)}
function Integer($value,[string]$name,[long]$expected){Need ($value.ContainsKey($name) -and $value[$name] -is [long] -and $value[$name] -eq $expected) ('Exact preparation integer required: '+$name)}
function Boolean($value,[string]$name,[bool]$expected){Need ($value.ContainsKey($name) -and $value[$name] -is [bool] -and $value[$name] -eq $expected) ('Exact preparation Boolean required: '+$name)}
function Hash($value,[string]$name){Need ($value.ContainsKey($name) -and $value[$name] -is [string] -and $value[$name] -cmatch '^[0-9a-f]{64}$') ('Exact preparation SHA-256 required: '+$name)}
function Utc($value,[string]$name){Need ($value[$name] -is [string] -and $value[$name] -cmatch '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,7})?(Z|\+00:00)$') 'Explicit preparation UTC string required';return [DateTimeOffset]::Parse($value[$name],[Globalization.CultureInfo]::InvariantCulture)}
function Zero($value){$names=@('source_updates','restore_count','support_updates','gradient_updates','target_inference_calls','query_count','model_constructions','measured_cells');Need ($value -is [Collections.Generic.Dictionary[string,object]] -and $value.Count -eq 8) 'Exact preparation zero ledger required';foreach($name in $names){Integer $value $name 0}}
function Retain-Bootstrap([string]$path,[string]$expected,[int]$maximum=1048576,[bool]$floors=$false,[bool]$retain=$true){
 Check-Time;Check-Pauses;Direct-Path $path
 Need ($expected -cmatch '^[0-9a-f]{64}$') 'Independent bootstrap byte pin required'
 $stream=[IO.File]::Open($path,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
 try{
  Need (($stream.Length -gt 0 -or -not $retain) -and $stream.Length -le $maximum) 'Bootstrap file bound exceeded'
  $buffer=[byte[]]::new(1048576);$bytes=$null;if($retain){$bytes=[IO.MemoryStream]::new()};$counted=0L;$digest=[Security.Cryptography.IncrementalHash]::CreateHash([Security.Cryptography.HashAlgorithmName]::SHA256)
  try{while($true){Check-Time;Check-Pauses;if($floors){[void](Resource-Sample)};$count=$stream.Read($buffer,0,$buffer.Length);if($count -eq 0){break};$digest.AppendData($buffer,0,$count);$counted+=$count;if($retain){$bytes.Write($buffer,0,$count)};Need ($counted -le $maximum) 'Bootstrap file grew beyond bound'};$actual=[Convert]::ToHexString($digest.GetHashAndReset()).ToLowerInvariant();Need ($actual -ceq $expected -and $stream.Length -eq $counted) 'Retained bootstrap bytes changed';$record=[pscustomobject]@{path=$path;sha256=$actual;stream=$stream;length=$counted;raw=$(if($retain){$bytes.ToArray()}else{$null})};$bootstrap.Add($record);return $record}finally{$digest.Dispose();if($bytes){$bytes.Dispose()}}
 }catch{$stream.Dispose();throw}
}
function Read-Control([string]$path,[string]$expected){$pin=Retain-Bootstrap $path $expected;return ,(Parse-Control $pin.raw)}
function Write-New([string]$path,$value){Check-Time 285;$raw=[Text.UTF8Encoding]::new($false).GetBytes(($value|ConvertTo-Json -Depth 32 -Compress)+[char]10);Need ($raw.Length -le 8388608) 'Preparation output bound exceeded';$stream=[IO.File]::Open($path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read);try{$stream.Write($raw,0,$raw.Length);$stream.Flush($true)}finally{$stream.Dispose()}}
function Policy($value){
 Text $value 'scope' $scope
 foreach($name in @('maximum_total_seconds')){Integer $value $name 300}
 Integer $value 'maximum_owned_prepare_children' 1;Integer $value 'maximum_owned_tree_processes' 64
 Integer $value 'maximum_python_invocations' 0;Integer $value 'maximum_jobs' 0;Integer $value 'maximum_test_invocations' 0
 Integer $value 'maximum_wrapper_helper_loads' 1;Integer $value 'maximum_child_helper_loads' 1
 Integer $value 'startup_ram_gib' 4;Integer $value 'active_ram_gib' 4;Integer $value 'disk_gib' 20
 Boolean $value 'automatic_retry_permitted' $false;Boolean $value 'test_execution_admitted' $false;Boolean $value 'scientific_admission' $false
 Zero $value.expected_numerical_budget
}
function Hold-Native([string]$path,[string]$expected,[long]$maximum=8388608,[bool]$retain=$true){$pin=[ChoP3Native]::Pin($path,$maximum,$retain);$held.Add($pin);Need ($pin.Sha256 -ceq $expected) ('Native preparation pin changed: '+$path);return $pin}
function Floors{Check-Time;foreach($path in $pauses){Need (-not [ChoP3Native]::Exists($path)) 'Genuine peer pause during preparation'};$ram=[ChoP3Native]::AvailableMemory();$disk=[ChoP3Native]::AvailableDisk();$script:minimumRam=[math]::Min($script:minimumRam,$ram);$script:minimumDisk=[math]::Min($script:minimumDisk,$disk);Need ($ram -ge 4GB -and $disk -ge 20GB) 'Native preparation active floor refused'}
function Remaining-Milliseconds([int]$maximum){$remaining=[math]::Min(($cleanupEnd-[DateTimeOffset]::UtcNow).TotalMilliseconds,(270-$watch.Elapsed.TotalSeconds)*1000);return [int][math]::Max(0,[math]::Min($maximum,[math]::Floor($remaining)))}
function Check-Temporary{
 if(-not $script:temporary){return}
 $count=0;$total=0L
 Get-ChildItem -LiteralPath $script:temporary -Recurse -Force -File|ForEach-Object{Check-Time 285;$count++;Need ($count -le 128 -and -not ($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -and -not $_.LinkType) 'Preparation temporary inventory bound/alias refused';$total+=$_.Length;Need ($total -le 33554432) 'Preparation temporary bytes exceeded32MiB'}
}
try{
 Need ($PSScriptRoot -ceq $run -and [Environment]::ProcessPath -ieq $executable) 'Exact preparation wrapper and PowerShell executable required'
 $request=Read-Control (Join-Path $run 'preparation-request_001.json') $RequestSha256
 $admission=Read-Control (Join-Path $run 'preparation-admission_001.json') $AdmissionSha256
 Text $request 'schema' 'cho51_p3_contracts_native_preparation_request_v1';Policy $request
 Text $admission 'schema' 'cho51_p3_contracts_native_preparation_admission_v1';Policy $admission;Boolean $admission 'accepted' $true
 Text $admission 'request_sha256' $RequestSha256;Text $request 'source_review_sha256' $sourceReviewSha
 foreach($name in @('preparation_source_review_sha256','owner_resource_amendment_sha256','wrapper_sha256','protocol_sha256')){Hash $request $name;Text $admission $name $request[$name]}
 Text $admission 'source_review_sha256' $sourceReviewSha
 Text $request 'original_prepare_source_sha256' $prepareSha;Hash $request 'prepare_source_sha256';Text $request 'native_helper_sha256' $nativeSha
 Hash $admission 'peer_grant_sha256'
 $peer=Read-Control $admission.peer_grant_path $admission.peer_grant_sha256
 Text $peer 'schema' 'pro2_pro3_native_preparation_release_v1';Policy $peer;Boolean $peer 'released' $true
 Text $peer 'request_sha256' $RequestSha256;Text $peer 'source_review_sha256' $sourceReviewSha
 foreach($name in @('preparation_source_review_sha256','owner_resource_amendment_sha256','wrapper_sha256','protocol_sha256')){Text $peer $name $request[$name]}
 foreach($record in @($admission,$peer)){foreach($name in @('window_start_utc','window_end_utc')){Text $record $name $request[$name]};Need ((Utc $record 'observed_utc') -le $entry) 'Fresh actual preparation disposition required'}
 $windowStart=Utc $request 'window_start_utc';$windowEnd=Utc $request 'window_end_utc'
 Need ($windowStart -le $entry -and $entry.AddSeconds(300) -le $windowEnd) 'Whole300-second preparation/caller/release grant must fit before start'
 $source=Read-Control $sourceScopePath $sourceScopeSha;$adoption=Read-Control $sourceAdoptionPath $sourceAdoptionSha
 Text $request 'source_scope_sha256' $sourceScopeSha;Text $request 'source_adoption_sha256' $sourceAdoptionSha
 Boolean $adoption 'Source_only_coexistence_adopted' $true;Text $adoption.Source_only_scope 'sha256' $sourceScopeSha
 Integer $source 'Pro3_max_including_Root_and_reviewer' 2;Integer $source 'Pro2_max_including_Root' 3;Integer $source 'shared_max_including_both_roots_and_overlap' 5
 Need ((Utc $source 'interval_start') -le $entry -and $entry.AddSeconds(300) -le (Utc $source 'interval_end').AddSeconds(-60)) 'Source009finiteend and60-second reserve refuse preparation start'
 $original=Read-Control (Join-Path $run 'source-review.json') $sourceReviewSha
 Boolean $original 'source_only' $true;Need ($original.remaining_actionable_findings -is [object[]] -and $original.remaining_actionable_findings.Count -eq 0 -and $original.files.Count -eq 14) 'Settled original14-source review required'
 Integer $original 'expected_tests' 117;Integer $original 'expected_stdlib_controls' 34
 Text $original.files 'runs/coordination/cho51_p3_contracts_20261027_v1/prepare.ps1' $prepareSha
 Text $original.files 'runs/coordination/cho51_p3_contracts_20261027_v1/native.ps1' $nativeSha
 $review=Read-Control (Join-Path $run 'preparation-source-review_001.json') $request.preparation_source_review_sha256
 Text $review 'schema' 'cho51_p3_contracts_preparation_source_review_v1';Boolean $review 'source_only' $true;Boolean $review 'independent_review' $true;Boolean $review 'passed' $true
 Text $review 'original_source_review_sha256' $sourceReviewSha
 Need ($review.remaining_actionable_findings -is [object[]] -and $review.remaining_actionable_findings.Count -eq 0 -and $review.files.Count -eq 3) 'Different-reviewer wrapper/protocol/prepare successor source review required'
 $wrapperRelative='runs/coordination/cho51_p3_contracts_20261027_v1/preparation-supervise_001.ps1'
 $protocolRelative='runs/coordination/cho51_p3_contracts_20261027_v1/preparation-protocol_001.md'
 $prepareRelative='runs/coordination/cho51_p3_contracts_20261027_v1/prepare_002.ps1'
 Text $review.files $wrapperRelative $request.wrapper_sha256;Text $review.files $protocolRelative $request.protocol_sha256
 Text $review.files $prepareRelative $request.prepare_source_sha256
 $amendment=Read-Control (Join-Path $run 'owner-resource-amendment.json') $request.owner_resource_amendment_sha256
 Text $amendment 'scope' $testScope;Text $amendment 'applies_to' 'metadata_profile_mapping_and_telemetry_contract_tests_only'
 Text $amendment 'owner_answer_exact' 'work with what you ahve!!!!'
 Integer $amendment 'startup_ram_gib' 4;Integer $amendment 'active_ram_gib' 4;Integer $amendment 'disk_gib' 20
 Boolean $amendment 'canonical_guard_modified' $false;Boolean $amendment 'scientific_admission' $false
 Need ($request.runtime_files -is [Collections.Generic.Dictionary[string,object]] -and $request.runtime_files.Count -ge 6 -and $request.runtime_files.Count -le 2500) 'Bounded exact PowerShell runtime inventory required'
 foreach($name in @('pwsh.exe','pwsh.dll','coreclr.dll','System.Management.Automation.dll','Microsoft.Management.Infrastructure.CimCmdlets.dll','Microsoft.Management.Infrastructure.dll')){Hash $request.runtime_files (Join-Path $runtimeRoot $name)}
 $outputs=@('preparation-attempt_001.json','preparation-supervision_001.json','preparation-stdout_001.json','preparation-stderr_001.json','preparation-caller-completion_001.json','preparation-custody-release_001.json','preparation-tmp_001','pins.json','pin-review.json','admission.json','guard-attempt_001.json','dispatch_001.json','t1')
 foreach($name in $outputs){Need (-not (Test-Path -LiteralPath (Join-Path $run $name))) 'Preparation identity/output or unit execution identity already consumed'}
 Check-Time;Check-Pauses
 Write-New (Join-Path $run 'preparation-attempt_001.json') ([ordered]@{schema='cho51_p3_contracts_preparation_attempt_v1';observed_utc=[DateTimeOffset]::UtcNow.ToString('o');request_sha256=$RequestSha256;admission_sha256=$AdmissionSha256;peer_grant_sha256=$admission.peer_grant_sha256;maximum_owned_prepare_children=1;maximum_python_invocations=0;maximum_jobs=0;automatic_retry_permitted=$false;scientific_admission=$false})
 $attemptWritten=$true
 for($sampleIndex=0;$sampleIndex -lt 2;$sampleIndex++){$startup.Add((Resource-Sample));if($sampleIndex -eq 0){Start-Sleep -Milliseconds 200}}
 foreach($relative in $original.files.Keys){[void](Retain-Bootstrap (Join-Path $root $relative) $original.files[$relative] 262144 $true)}
 [void](Retain-Bootstrap $PSCommandPath $request.wrapper_sha256 262144 $true)
 [void](Retain-Bootstrap (Join-Path $root $protocolRelative) $request.protocol_sha256 262144 $true)
 [void](Retain-Bootstrap (Join-Path $root $prepareRelative) $request.prepare_source_sha256 262144 $true)
 $runtimeBytes=0L
 foreach($path in $request.runtime_files.Keys){Need ($path.StartsWith($runtimeRoot+'\',[StringComparison]::OrdinalIgnoreCase)) 'Only exact declared PowerShell runtime files admitted';$pin=Retain-Bootstrap $path $request.runtime_files[$path] 67108864 $true $false;$runtimeBytes+=$pin.length;Need ($runtimeBytes -le 1073741824) 'Bootstrap runtime aggregate bound exceeded'}
 Check-Time;Check-Pauses;[void](Resource-Sample)
 $temporary=Join-Path $run 'preparation-tmp_001';[void][IO.Directory]::CreateDirectory($temporary);$env:TEMP=$temporary;$env:TMP=$temporary
 $nativeRecord=@($bootstrap|Where-Object{$_.path -ceq (Join-Path $run 'native.ps1')})
 Need ($nativeRecord.Count -eq 1) 'One exact retained native helper required'
 . ([scriptblock]::Create([Text.UTF8Encoding]::new($false,$true).GetString($nativeRecord[0].raw)))
 $nativeLoaded=$true
 Check-Temporary
 [ChoP3Native]::ConfigurePinChecks($stopAt.UtcDateTime,[string[]]$pauses,(225-$watch.Elapsed.TotalSeconds))
 foreach($pin in $bootstrap){[void](Hold-Native $pin.path $pin.sha256 ([math]::Max(1,$pin.length)) $false)}
 Floors
 Need ($watch.Elapsed.TotalSeconds -le 165 -and ($stopAt-[DateTimeOffset]::UtcNow).TotalSeconds -ge 60) 'Insufficient preparation work/cleanup/caller reserve after compilation and bootstrap'
 foreach($pin in $held){$pin.Recheck()}
 $command=@('-NoLogo','-NoProfile','-NonInteractive','-File',(Join-Path $run 'prepare_002.ps1'),'-ReviewSha256',$sourceReviewSha,'-PreparationReviewSha256',$request.preparation_source_review_sha256)
 $info=[Diagnostics.ProcessStartInfo]::new($executable);$info.UseShellExecute=$false;$info.CreateNoWindow=$true;$info.WindowStyle=[Diagnostics.ProcessWindowStyle]::Hidden;$info.WorkingDirectory=$root;$info.RedirectStandardOutput=$true;$info.RedirectStandardError=$true
 foreach($argument in $command){[void]$info.ArgumentList.Add($argument)}
 $info.Environment['TEMP']=$temporary;$info.Environment['TMP']=$temporary
 $process=[Diagnostics.Process]::new();$process.StartInfo=$info;$tree=[ChoP3Native+OwnedTree]::new()
 Floors
 Need ($watch.Elapsed.TotalSeconds -le 165 -and [DateTimeOffset]::UtcNow -lt $stopAt) 'Immediate owned preparation launch refused'
 Need ($process.Start()) 'Owned preparation child start failed'
 $started=$true;$tree.Root([uint32]$process.Id,$process.Handle)
 $outDrain=[ChoP3Native+BoundedDrain]::new($process.StandardOutput.BaseStream);$errDrain=[ChoP3Native+BoundedDrain]::new($process.StandardError.BaseStream)
 try{$tree.Discover()}catch{$discoveryComplete=$false;throw}
 while($true){Floors;Check-Temporary;Need (-not $outDrain.Overflow -and -not $errDrain.Overflow -and -not $outDrain.Error -and -not $errDrain.Error) 'Preparation bounded stream overflow/drain failure';if($process.WaitForExit(100)){$exitCode=$process.ExitCode;break};try{$tree.Discover()}catch{$discoveryComplete=$false;throw}}
 Need ($exitCode -eq 0) 'Owned preparation child returned nonzero'
 $pinsPin=[ChoP3Native]::Pin((Join-Path $run 'pins.json'),8388608,$true);$held.Add($pinsPin);$pinsSha=$pinsPin.Sha256
 $pins=Parse-Control $pinsPin.Raw
 Text $pins 'schema' 'cho51_p3_contracts_pins_v1';Text $pins 'scope' $testScope;Text $pins 'source_review_sha256' $sourceReviewSha
 Text $pins 'owner_resource_amendment_sha256' $request.owner_resource_amendment_sha256
 Text $pins 'preparation_source_review_sha256' $request.preparation_source_review_sha256
 Integer $pins 'startup_ram_gib' 4;Integer $pins 'active_ram_gib' 4;Integer $pins 'disk_gib' 20;Integer $pins 'expected_tests' 117;Integer $pins 'expected_stdlib_controls' 34
 Boolean $pins 'scientific_admission' $false;Zero $pins.expected_numerical_budget
 Need ($pins.reviewed_files.Count -eq 14) 'Prepared exact14-source inventory required'
 foreach($relative in $original.files.Keys){Text $pins.reviewed_files $relative $original.files[$relative]}
}catch{$errors.Add($_.Exception.Message)}finally{
 if($started){
  if($tree.Records.Count -eq 0){$discoveryComplete=$false;try{[void][ChoP3Native]::StopRetainedRoot($process.Handle,(Remaining-Milliseconds 1000))}catch{$errors.Add('retained root cleanup: '+$_.Exception.Message)}}
  for($round=0;$round -lt 4 -and $watch.Elapsed.TotalSeconds -lt 270 -and [DateTimeOffset]::UtcNow -lt $cleanupEnd;$round++){
   try{$tree.Discover()}catch{$discoveryComplete=$false;$errors.Add('owned discovery: '+$_.Exception.Message)}
   foreach($member in @($tree.Records)){try{$tree.Terminate($member)}catch{$errors.Add('owned termination: '+$_.Exception.Message)}}
   foreach($member in @($tree.Records)){try{[void]$tree.Reap($member,(Remaining-Milliseconds 500))}catch{$errors.Add('owned reap: '+$_.Exception.Message)}}
   $alive=$false;foreach($member in @($tree.Records)){try{if(-not $tree.Exited($member)){$alive=$true}}catch{$alive=$true;$errors.Add('owned liveness: '+$_.Exception.Message)}}
   if(-not $alive -and $round -ge 1){break}
  }
  $reaped=$discoveryComplete -and $tree.Records.Count -gt 0
  foreach($member in @($tree.Records)){try{if(-not $tree.Exited($member)){$reaped=$false}}catch{$reaped=$false;$errors.Add('final reap: '+$_.Exception.Message)}}
  try{if($process.HasExited){$exitCode=$process.ExitCode}else{$errors.Add('owned root remains alive')}}catch{$errors.Add('root exit: '+$_.Exception.Message)}
 }
 foreach($drain in @($outDrain,$errDrain)){if($null -ne $drain){try{[void]$drain.Wait((Remaining-Milliseconds 1000));$drain.Dispose();[void]$drain.Wait((Remaining-Milliseconds 500))}catch{$errors.Add('bounded stream close: '+$_.Exception.Message)}}}
 if($outDrain){$stdoutEof=$outDrain.Eof -and -not $outDrain.Overflow -and -not $outDrain.Error}
 if($errDrain){$stderrEof=$errDrain.Eof -and -not $errDrain.Overflow -and -not $errDrain.Error}
 $identities=@();$snapshots=0
 if($tree){$snapshots=$tree.Snapshots;$identities=@($tree.Records|ForEach-Object{[ordered]@{pid=$_.Pid;parent_pid=$_.ParentPid;creation_filetime=$_.Created.ToString();snapshot_cutoff_filetime=$_.SnapshotCutoff.ToString()}})}
 foreach($pin in $held){try{$pin.Recheck()}catch{$errors.Add('final retained native identity: '+$_.Exception.Message)}}
 foreach($pin in $held){try{$pin.Dispose()}catch{$errors.Add('native pin disposal: '+$_.Exception.Message)}}
 foreach($pin in $bootstrap){try{$pin.stream.Dispose()}catch{$errors.Add('bootstrap stream disposal: '+$_.Exception.Message)}}
 if($process){try{$process.Dispose()}catch{$errors.Add('owned process disposal: '+$_.Exception.Message)}}
 if($tree){try{$tree.Dispose()}catch{$errors.Add('owned handle disposal: '+$_.Exception.Message)}}
 $env:TEMP=$oldTemp;$env:TMP=$oldTmp
 if($attemptWritten){
  foreach($row in @(@('preparation-stdout_001.json',$outDrain),@('preparation-stderr_001.json',$errDrain))){if($null -ne $row[1]){try{$raw=$row[1].Bytes();Write-New (Join-Path $run $row[0]) ([ordered]@{bytes=$raw.Length;text=[Text.UTF8Encoding]::new($false).GetString($raw);eof=$row[1].Eof;overflow=$row[1].Overflow;error=$row[1].Error})}catch{$errors.Add('stream evidence: '+$_.Exception.Message)}}}
  if($watch.Elapsed.TotalSeconds -ge 285 -or [DateTimeOffset]::UtcNow -ge $finalEnd){$errors.Add('Preparation final evidence/caller reserve exceeded')}
  $internalPassed=$started -and $exitCode -eq 0 -and $reaped -and $stdoutEof -and $stderrEof -and $errors.Count -eq 0 -and $null -ne $pinsSha
  $result=[ordered]@{schema='cho51_p3_contracts_preparation_supervision_v1';started_utc=$entry.ToString('o');observed_before_final_supervision_write_utc=[DateTimeOffset]::UtcNow.ToString('o');elapsed_before_final_supervision_write_seconds=$watch.Elapsed.TotalSeconds;internal_checks_passed=$internalPassed;full_caller_completion_and_custody_release_status='pending_separate_Root_actual_record';request_sha256=$RequestSha256;admission_sha256=$AdmissionSha256;source_review_sha256=$sourceReviewSha;prepared_pins_sha256=$pinsSha;native_helper_loaded=$nativeLoaded;owned_prepare_child_started=$started;exit_code=$exitCode;owned_tree_reaped=$reaped;owned_tree_discovery_complete=$discoveryComplete;owned_identities=$identities;descendant_snapshots=$snapshots;stdout_eof=$stdoutEof;stderr_eof=$stderrEof;stream_limit_bytes=1048576;startup_samples=@($startup);minimum_available_ram_bytes=$minimumRam;minimum_free_disk_bytes=$minimumDisk;maximum_total_seconds=300;work_stop_seconds=225;cleanup_end_seconds=270;final_evidence_end_seconds=285;full_caller_and_release_deadline_utc=$hardEnd.ToString('o');source_publication_reserve_seconds=60;errors=@($errors);maximum_owned_prepare_children=1;maximum_python_invocations=0;maximum_jobs=0;maximum_test_invocations=0;automatic_retry_permitted=$false;test_execution_admitted=$false;scientific_admission=$false}
  try{Write-New (Join-Path $run 'preparation-supervision_001.json') $result;$result|ConvertTo-Json -Depth 14}catch{$errors.Add('final supervision output: '+$_.Exception.Message)}
 }
}
if(-not $attemptWritten -or $errors.Count -ne 0 -or -not $internalPassed -or $watch.Elapsed.TotalSeconds -ge 285 -or [DateTimeOffset]::UtcNow -ge $finalEnd){exit 1}
exit 0
