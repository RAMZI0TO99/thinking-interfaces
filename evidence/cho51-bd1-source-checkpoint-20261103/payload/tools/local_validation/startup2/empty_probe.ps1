param([Parameter(Mandatory=$true)][string]$OriginUtc,[Parameter(Mandatory=$true)][long]$OriginQpc,[Parameter(Mandatory=$true)][long]$Frequency)
$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
# Q-only fixed negative: normal process exit with no marker evidence.
if($Frequency -ne [Diagnostics.Stopwatch]::Frequency -or $OriginQpc -le 0 -or ([Diagnostics.Stopwatch]::GetTimestamp()-$OriginQpc)/$Frequency -ge 5){throw 'original fixture clock/deadline'}
