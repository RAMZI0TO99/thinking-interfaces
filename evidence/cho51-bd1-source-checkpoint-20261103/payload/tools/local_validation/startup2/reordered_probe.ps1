param([Parameter(Mandatory=$true)][string]$OriginUtc,[Parameter(Mandatory=$true)][long]$OriginQpc,[Parameter(Mandatory=$true)][long]$Frequency)
$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false,$true)
if($Frequency -ne [Diagnostics.Stopwatch]::Frequency -or $OriginQpc -le 0){throw 'original fixture clock'}
$sequence=0
foreach($event in @('fixture_fast_end','fixture_fast_begin')){
 $tick=[Diagnostics.Stopwatch]::GetTimestamp();if(($tick-$OriginQpc)/$Frequency -ge 5){throw 'original fixture deadline'}
 [Console]::Out.WriteLine((@{schema='cho51_startup_probe_marker_v1';sequence=$sequence;event=$event;origin_utc=$OriginUtc;origin_qpc=$OriginQpc;frequency=$Frequency;qpc=$tick;elapsed_seconds=($tick-$OriginQpc)/$Frequency;detail='qualification reordered events'}|ConvertTo-Json -Compress));[Console]::Out.Flush();$sequence++
}
