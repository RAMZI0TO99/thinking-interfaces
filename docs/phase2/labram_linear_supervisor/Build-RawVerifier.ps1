[CmdletBinding()]
param(
    [string]$ProjectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..')),
    [Parameter(Mandatory = $true)][ValidatePattern('^[0-9a-f]{64}$')][string]$SourceSha256,
    [Parameter(Mandatory = $true)][string]$OutputDirectory
)

# Prepare fresh code bytes only. This script never reads EEG or runs Python.
$ErrorActionPreference = 'Stop'
$taskRoot = [IO.Path]::GetFullPath($ProjectRoot).TrimEnd('\')
$taskBase = Join-Path $taskRoot 'runs/phase2/freeze_readiness'
$taskOutput = [IO.Path]::GetFullPath($OutputDirectory).TrimEnd('\')
if ([IO.Path]::GetDirectoryName($taskOutput) -ine $taskBase -or
    (Test-Path -LiteralPath $taskOutput)) {
    throw 'A fresh direct output directory under runs/phase2/freeze_readiness is required'
}
function Assert-TaskOrdinaryAncestors([string]$Path) {
    $taskCursor = [IO.Path]::GetFullPath($Path)
    while ($taskCursor) {
        if (Test-Path -LiteralPath $taskCursor) {
            $taskItem = Get-Item -LiteralPath $taskCursor -Force
            if (($taskItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw "Reparse path refused: $taskCursor"
            }
        }
        $taskParent = [IO.Path]::GetDirectoryName($taskCursor)
        if ($taskParent -eq $taskCursor) { break }
        $taskCursor = $taskParent
    }
}
function Get-TaskBytesSha([byte[]]$Bytes) {
    $taskHasher = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($taskHasher.ComputeHash($Bytes))).Replace('-', '').ToLowerInvariant() }
    finally { $taskHasher.Dispose() }
}
$taskSource = Join-Path $taskBase '20261004_62536382_raw_source_readonly/verify_raw_sources.py'
Assert-TaskOrdinaryAncestors $taskSource
Assert-TaskOrdinaryAncestors $taskOutput
$taskExpected = '0bafb8fa8ea35e0b924e9434f7861a32684a1fc5c7bedcb5a5939e613e709548'
$taskOriginal = [IO.File]::ReadAllBytes($taskSource)
if ((Get-TaskBytesSha $taskOriginal) -cne $taskExpected) { throw 'Frozen raw verifier bytes differ' }
if ($SourceSha256 -ceq '62536382eb85a7626d6d45b110b688dbb374281d136733e75cf77301a4c77cf0') {
    throw 'Successor must bind a new source, not relabel the historical attempt'
}
$taskEncoding = [Text.Encoding]::GetEncoding(28591)
$taskText = $taskEncoding.GetString($taskOriginal)
$taskChanges = @(
    [pscustomobject]@{old='62536382eb85a7626d6d45b110b688dbb374281d136733e75cf77301a4c77cf0';new=$SourceSha256},
    [pscustomobject]@{old='source differs from exact 62536382 review target';new=('source differs from exact '+$SourceSha256.Substring(0,8)+' review target')},
    [pscustomobject]@{old='Rehash the declared 52 Cho raw sources without decoding or fitting EEG.';new='Verify 52 Cho raw sources and decode Profile A; no model fitting.'}
)
foreach ($taskChange in $taskChanges) {
    if ([regex]::Matches($taskText,[regex]::Escape($taskChange.old)).Count -ne 1) {
        throw 'Expected substitution must occur exactly once'
    }
    $taskText = $taskText.Replace($taskChange.old,$taskChange.new)
}
$taskReverse = $taskText
for ($taskIndex=$taskChanges.Count-1; $taskIndex -ge 0; $taskIndex--) {
    $taskChange = $taskChanges[$taskIndex]
    if ([regex]::Matches($taskReverse,[regex]::Escape($taskChange.new)).Count -ne 1) {
        throw 'Reverse substitution must occur exactly once'
    }
    $taskReverse = $taskReverse.Replace($taskChange.new,$taskChange.old)
}
if ((Get-TaskBytesSha ($taskEncoding.GetBytes($taskReverse))) -cne $taskExpected) {
    throw 'Reverse proof does not reconstruct frozen verifier'
}
if ((Get-TaskBytesSha ([IO.File]::ReadAllBytes($taskSource))) -cne $taskExpected) {
    throw 'Frozen source changed during preparation'
}
$taskNewBytes = $taskEncoding.GetBytes($taskText)
New-Item -ItemType Directory -Path $taskOutput -ErrorAction Stop | Out-Null
$taskFile = [IO.File]::Open((Join-Path $taskOutput 'verify_raw_sources.py'),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
try { $taskFile.Write($taskNewBytes,0,$taskNewBytes.Length); $taskFile.Flush($true) }
finally { $taskFile.Dispose() }
$taskRecord = [ordered]@{
    schema='pro3_raw_verifier_prospective_repin_v1';created_utc=[datetime]::UtcNow.ToString('o')
    state='code_prepared_only_no_raw_verification_or_admission'
    builder_sha256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant()
    source_file=$taskSource.Substring($taskRoot.Length+1).Replace('\','/');source_file_sha256=$taskExpected
    prospective_source_sha256=$SourceSha256;new_file_sha256=Get-TaskBytesSha $taskNewBytes
    replacements=$taskChanges;reverse_substitution_reproduces_original_bytes=$true
    raw_or_weights_read=$false;python_or_training_invoked=$false;scientific_admission=$false
    runtime_scope='Execution imports scientific modules, hashes raw EEG and decodes Profile A; separately guarded compute required'
    unchanged_floors='Verifier6GiB RAM/8GiB disk; external finite watchdog and fresh peer admission still required'
}
$taskBytes=[Text.UTF8Encoding]::new($false).GetBytes(($taskRecord | ConvertTo-Json -Depth 8)+[Environment]::NewLine)
$taskFile=[IO.File]::Open((Join-Path $taskOutput 'repin_provenance.json'),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
try { $taskFile.Write($taskBytes,0,$taskBytes.Length); $taskFile.Flush($true) }
finally { $taskFile.Dispose() }
[pscustomobject]@{state=$taskRecord.state;output_directory=$taskOutput;new_file_sha256=$taskRecord.new_file_sha256;reverse_proof=$true} | ConvertTo-Json
