param([Parameter(Mandatory=$true)][string]$OriginUtc,[Parameter(Mandatory=$true)][long]$OriginQpc,[Parameter(Mandatory=$true)][long]$Frequency)
$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false,$true)
if($Frequency -ne [Diagnostics.Stopwatch]::Frequency -or $OriginQpc -le 0){throw 'original fixture clock'}
$tick=[Diagnostics.Stopwatch]::GetTimestamp();if(($tick-$OriginQpc)/$Frequency -ge 5){throw 'original fixture deadline'}
[Console]::Out.WriteLine((@{schema='cho51_startup_probe_marker_v1';sequence=0;event='fixture_fast_begin';origin_utc=$OriginUtc;origin_qpc=$OriginQpc;frequency=$Frequency;qpc=$tick;elapsed_seconds=($tick-$OriginQpc)/$Frequency;detail='qualification malformed suffix'}|ConvertTo-Json -Compress));[Console]::Out.Flush()
[Console]::Out.WriteLine('{"schema":');[Console]::Out.Flush()
