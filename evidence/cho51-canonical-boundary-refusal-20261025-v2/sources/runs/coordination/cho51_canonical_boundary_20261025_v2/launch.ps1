param([Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$PinsSha256)
$ErrorActionPreference='Stop'
$root='D:\Aenv\pro3'
$run=$PSScriptRoot
function Get-Sha($path){(Get-FileHash -LiteralPath $path).Hash.ToLowerInvariant()}
function Write-New($path,$value){$raw=[Text.UTF8Encoding]::new($false).GetBytes(($value|ConvertTo-Json -Depth 25)+[char]10);$stream=[IO.File]::Open($path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read);try{$stream.Write($raw,0,$raw.Length);$stream.Flush($true)}finally{$stream.Dispose()}}
if((Get-Sha (Join-Path $run 'pins.json')) -cne $PinsSha256){throw 'Pins changed'}
$pins=Get-Content (Join-Path $run 'pins.json') -Raw|ConvertFrom-Json -DateKind String
$admission=Get-Content (Join-Path $run 'admission.json') -Raw|ConvertFrom-Json -DateKind String
if($admission.pins_sha256 -cne $PinsSha256 -or $admission.accepted -ne $true){throw 'Exact Root admission required'}
foreach($entry in $pins.reviewed_files.PSObject.Properties){if((Get-Sha (Join-Path $root $entry.Name)) -cne $entry.Value){throw 'Frozen reviewed source changed'}}
foreach($entry in $pins.runtime_files.PSObject.Properties){if((Get-Sha $entry.Name) -cne $entry.Value){throw 'Runtime changed'}}
if((Get-Sha $admission.peer_release_path) -cne $admission.peer_release_sha256){throw 'Peer release changed'}
$peer=Get-Content $admission.peer_release_path -Raw|ConvertFrom-Json -DateKind String
if($peer.scope -cne $pins.scope -or $peer.pins_sha256 -cne $PinsSha256 -or $peer.released -ne $true -or $peer.maximum_jobs -ne 1){throw 'Fresh exact peer release required'}
$start=[DateTimeOffset]::Parse($peer.window_start_utc).ToUniversalTime()
$end=[DateTimeOffset]::Parse($peer.window_end_utc).ToUniversalTime()
if([DateTimeOffset]::UtcNow -lt $start -or [DateTimeOffset]::UtcNow -gt $end.AddSeconds(-690)){throw 'Insufficient exact peer window'}
foreach($day in @('20261007','20261012','20261013','20261015','20261025')){if(Test-Path -LiteralPath ("D:\Aenv\pro2\WORK\resume-"+$day+"-001\coordination\PRO2_REQUEST_PRO3_PAUSE.json")){throw 'Genuine peer pause'}}
$command=@((Join-Path $root '.venv/Scripts/python.exe'),'-I','-S','-B',(Join-Path $run 'runner.py'),'--pins',(Join-Path $run 'pins.json'),'--expect-pins',$PinsSha256,'--output',(Join-Path $run 't1'))
$dispatch=[ordered]@{schema='cho51_canonical_boundary_dispatch_v1';observed_utc=[DateTimeOffset]::UtcNow.ToString('o');pins_sha256=$PinsSha256;root_admission_sha256=Get-Sha (Join-Path $run 'admission.json');command=$command;peer_release_sha256=$admission.peer_release_sha256;expected_numerical_budget=$pins.expected_numerical_budget;scientific_admission=$false}
Write-New (Join-Path $run 'dispatch_001.json') $dispatch
& (Join-Path $root '.venv/Scripts/python.exe') -I -S -B (Join-Path $run 'guard.py') --purpose $pins.scope --seconds 600 --process-mib 4096 --job-mib 5120 --pause-file 'D:\Aenv\pro2\WORK\resume-20261025-001\coordination\PRO2_REQUEST_PRO3_PAUSE.json' -- @command
$childExit=$LASTEXITCODE
Write-New (Join-Path $run 'dispatch-result_001.json') ([ordered]@{schema='cho51_canonical_boundary_dispatch_result_v1';completed_utc=[DateTimeOffset]::UtcNow.ToString('o');exit_code=$childExit;pins_sha256=$PinsSha256;scientific_admission=$false})
exit $childExit

