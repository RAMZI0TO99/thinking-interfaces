param([Parameter(Mandatory=$true)][string]$OriginUtc,[Parameter(Mandatory=$true)][long]$OriginQpc,[Parameter(Mandatory=$true)][long]$Frequency)
$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false,$true)
$sequence=0;$counter=$null;$failed=$false;$errorDetail=''
if($Frequency -ne [Diagnostics.Stopwatch]::Frequency -or $OriginQpc -le 0){throw 'original probe clock'}
function Marker([string]$Event,[string]$Detail='') {
 $tick=[Diagnostics.Stopwatch]::GetTimestamp()
 if($Detail.Length -gt 1024){$Detail=$Detail.Substring(0,1024)}
 $row=@{schema='cho51_startup_probe_marker_v1';sequence=$script:sequence;event=$Event;origin_utc=$OriginUtc;origin_qpc=$OriginQpc;frequency=$Frequency;qpc=$tick;elapsed_seconds=($tick-$OriginQpc)/$Frequency;detail=$Detail}
 $script:sequence++;[Console]::Out.WriteLine(($row|ConvertTo-Json -Compress));[Console]::Out.Flush()
}
function BeforeEffect {if(([Diagnostics.Stopwatch]::GetTimestamp()-$OriginQpc)/$Frequency -ge 5){throw 'original probe deadline'}}
try {
 BeforeEffect;Marker 'assembly_load_begin'
 [void][Reflection.Assembly]::Load('System.Diagnostics.PerformanceCounter');Marker 'assembly_load_end'
 BeforeEffect;Marker 'counter_ctor_begin'
 $counter=[Diagnostics.PerformanceCounter]::new('Memory','Available Bytes');Marker 'counter_ctor_end'
 BeforeEffect;Marker 'first_sample_begin'
 $sample=$counter.NextSample()
 if($sample.CounterType.ToString() -cne 'NumberOfItems64'){throw 'PDH sample type'}
 Marker 'first_sample_end' ('raw_available_bytes='+[string]$sample.RawValue)
}catch{$failed=$true;$errorDetail=$_.Exception.GetType().Name+': '+$_.Exception.Message}
finally {
 if($null -ne $counter){Marker 'counter_dispose_begin';$counter.Dispose();Marker 'counter_dispose_end'}
}
if($failed){Marker 'probe_error' $errorDetail;exit 1}
