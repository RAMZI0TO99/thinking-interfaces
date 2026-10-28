param(
 [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$ProofsSha256,
 [Parameter(Mandatory)][ValidatePattern('^[0-9a-f]{64}$')][string]$AdmissionSha256
)
$ErrorActionPreference='Stop'
$entry=[DateTimeOffset]::UtcNow
$script:preflightDeadline=$entry.AddSeconds(300)
$watch=[Diagnostics.Stopwatch]::StartNew()
$root='D:\Aenv\pro3'
$run=Join-Path $root 'runs\coordination\cho51_canonical_boundary_20261025_v5_aggregate'
$source=Join-Path $run 'aggregate.py'
$sourceSha='eb85e2bb7b682a4215c373ee080bda9a4638708e54190bda3170474c09c3fab8'
$planSha='d1467ae85739115f2f65ab1ca23a8f6624b1a09d1a6b40384f64c07eab62497f'
$aPins=Join-Path $root 'runs\coordination\cho51_canonical_boundary_20261025_v5_a\pins.json'
$aPinsSha='82b820ab809370465c6589124b182106ad3467a2cf61e1d063003479b711b291'
$scope='cho51_canonical_boundary_20261025_v5_aggregate'
if($PSScriptRoot -cne $run -or $PSCommandPath -cne (Join-Path $run 'supervise.ps1')){throw 'Exact supplemental supervisor path required'}
Add-Type -TypeDefinition @'
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Threading.Tasks;
using Microsoft.Win32.SafeHandles;

public static class ChoAggregateNative {
    [StructLayout(LayoutKind.Sequential)] public struct FileTime { public uint Low, High; public ulong Value { get { return ((ulong)High << 32) | Low; } } }
    [StructLayout(LayoutKind.Sequential)] public struct FileInfo { public uint Attributes; public FileTime Created, Accessed, Written; public uint Volume, SizeHigh, SizeLow, Links, IndexHigh, IndexLow; public ulong Size { get { return ((ulong)SizeHigh << 32) | SizeLow; } } }
    [StructLayout(LayoutKind.Sequential)] public struct MemoryStatus { public uint Length, Load; public ulong TotalPhysical, AvailablePhysical, TotalPageFile, AvailablePageFile, TotalVirtual, AvailableVirtual, AvailableExtendedVirtual; }
    [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)] public struct ProcessEntry { public uint Size, Usage, Pid; public UIntPtr Heap; public uint Module, Threads, ParentPid; public int Priority; public uint Flags; [MarshalAs(UnmanagedType.ByValTStr, SizeConst=260)] public string Exe; }
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)] static extern SafeFileHandle CreateFileW(string path, uint access, uint share, IntPtr security, uint mode, uint flags, IntPtr template);
    [DllImport("kernel32.dll", SetLastError=true)] static extern bool GetFileInformationByHandle(SafeFileHandle handle, out FileInfo info);
    [DllImport("kernel32.dll", SetLastError=true)] static extern uint GetFileType(SafeFileHandle handle);
    [DllImport("kernel32.dll", SetLastError=true)] static extern bool ReadFile(SafeFileHandle handle, [Out] byte[] buffer, uint count, out uint read, IntPtr overlapped);
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)] static extern uint GetFileAttributesW(string path);
    [DllImport("kernel32.dll", SetLastError=true)] static extern bool GlobalMemoryStatusEx(ref MemoryStatus status);
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)] static extern bool GetDiskFreeSpaceExW(string directory, out ulong available, out ulong total, out ulong free);
    [DllImport("kernel32.dll", SetLastError=true)] static extern SafeFileHandle CreateToolhelp32Snapshot(uint flags, uint pid);
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)] static extern bool Process32FirstW(SafeFileHandle snapshot, ref ProcessEntry entry);
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)] static extern bool Process32NextW(SafeFileHandle snapshot, ref ProcessEntry entry);
    [DllImport("kernel32.dll", SetLastError=true)] static extern SafeFileHandle OpenProcess(uint access, bool inherit, uint pid);
    [DllImport("kernel32.dll", SetLastError=true)] static extern bool GetProcessTimes(SafeFileHandle process, out FileTime created, out FileTime exited, out FileTime kernel, out FileTime user);
    [DllImport("kernel32.dll", SetLastError=true)] static extern bool TerminateProcess(SafeFileHandle process, uint code);
    [DllImport("kernel32.dll", SetLastError=true)] static extern uint WaitForSingleObject(SafeFileHandle handle, uint milliseconds);
    [DllImport("kernel32.dll", SetLastError=true)] static extern bool DuplicateHandle(IntPtr sourceProcess, IntPtr source, IntPtr targetProcess, out SafeFileHandle target, uint access, bool inherit, uint options);
    [DllImport("kernel32.dll")] static extern IntPtr GetCurrentProcess();
    static Exception Failure(string operation) { return new Win32Exception(Marshal.GetLastWin32Error(), operation); }
    static FileInfo Info(SafeFileHandle handle) { FileInfo value; if(!GetFileInformationByHandle(handle,out value)) throw Failure("physical file identity"); if(GetFileType(handle)!=1) throw new IOException("non-disk metadata refused"); return value; }
    static SafeFileHandle Open(string path, bool directory, bool contents) {
        var handle=CreateFileW(path,contents ? 0x80000000u : 0x80u,1,IntPtr.Zero,3,0x00200000u | (directory ? 0x02000000u : 0x08000000u),IntPtr.Zero);
        if(handle.IsInvalid) { handle.Dispose(); throw Failure("direct retained physical open"); }
        try { var info=Info(handle); if((info.Attributes & 0x400)!=0 || ((info.Attributes & 0x10)!=0)!=directory || (!directory && info.Links!=1)) throw new IOException("reparse/nonregular/multilink file refused"); return handle; }
        catch { handle.Dispose(); throw; }
    }
    static bool Same(FileInfo first, FileInfo second, bool directory) {
        return first.Volume==second.Volume && first.IndexHigh==second.IndexHigh && first.IndexLow==second.IndexLow && first.Created.Value==second.Created.Value && first.Attributes==second.Attributes && (directory || first.Links==second.Links && first.Size==second.Size && first.Written.Value==second.Written.Value);
    }
    public sealed class PhysicalPin : IDisposable {
        internal readonly List<SafeFileHandle> Handles=new List<SafeFileHandle>();
        internal readonly List<string> Paths=new List<string>();
        internal readonly List<FileInfo> Identities=new List<FileInfo>();
        public byte[] Raw { get; internal set; }
        public string Sha256 { get; internal set; }
        public ulong Length { get; internal set; }
        public void Recheck() {
            for(int index=0;index<Handles.Count;index++) {
                bool directory=index<Handles.Count-1;
                if(!Same(Identities[index],Info(Handles[index]),directory)) throw new IOException("retained identity changed");
                using(var current=Open(Paths[index],directory,false)) if(!Same(Identities[index],Info(current),directory)) throw new IOException("reopened path/ancestor identity changed");
            }
        }
        public void Dispose() { for(int index=Handles.Count-1;index>=0;index--) Handles[index].Dispose(); Handles.Clear(); }
    }
    public static PhysicalPin Pin(string path, long maximum, bool retain) {
        if(maximum<1 || !Path.IsPathFullyQualified(path) || !String.Equals(Path.GetFullPath(path),path,StringComparison.OrdinalIgnoreCase) || path.StartsWith(@"\\",StringComparison.Ordinal) || path.Substring(2).Contains(":")) throw new IOException("direct local absolute path required");
        var pin=new PhysicalPin();
        try {
            var ancestors=new List<string>(); var parent=Path.GetDirectoryName(path);
            while(!String.IsNullOrEmpty(parent)) { ancestors.Add(parent); parent=Path.GetDirectoryName(parent); }
            ancestors.Reverse();
            foreach(var ancestor in ancestors) { var handle=Open(ancestor,true,false); pin.Handles.Add(handle); pin.Paths.Add(ancestor); pin.Identities.Add(Info(handle)); }
            var file=Open(path,false,true); pin.Handles.Add(file); pin.Paths.Add(path); var before=Info(file); pin.Identities.Add(before);
            if(before.Size>(ulong)maximum) throw new IOException("physical byte bound exceeded");
            var buffer=new byte[65536]; ulong total=0;
            using(var digest=IncrementalHash.CreateHash(HashAlgorithmName.SHA256)) using(var bytes=retain ? new MemoryStream() : null) {
                while(true) {
                    uint count; if(!ReadFile(file,buffer,(uint)buffer.Length,out count,IntPtr.Zero)) throw Failure("bounded physical read");
                    if(count==0) break;
                    total+=count; if(total>(ulong)maximum) throw new IOException("physical byte bound exceeded");
                    digest.AppendData(buffer,0,(int)count); if(retain) bytes.Write(buffer,0,(int)count);
                }
                pin.Sha256=BitConverter.ToString(digest.GetHashAndReset()).Replace("-","").ToLowerInvariant(); pin.Raw=retain ? bytes.ToArray() : null;
            }
            if(total!=before.Size) throw new IOException("physical read length changed"); pin.Length=total; pin.Recheck(); return pin;
        } catch { pin.Dispose(); throw; }
    }
    public static bool Exists(string path) { uint value=GetFileAttributesW(path); if(value!=0xffffffff) return true; int error=Marshal.GetLastWin32Error(); if(error==2 || error==3) return false; throw new Win32Exception(error,"bounded local existence check"); }
    public static ulong AvailableMemory() { var status=new MemoryStatus(); status.Length=(uint)Marshal.SizeOf(typeof(MemoryStatus)); if(!GlobalMemoryStatusEx(ref status)) throw Failure("physical memory query"); return status.AvailablePhysical; }
    public static ulong AvailableDisk() { ulong available,total,free; if(!GetDiskFreeSpaceExW(@"D:\",out available,out total,out free)) throw Failure("local disk query"); return available; }
    public sealed class OwnedProcess { public uint Pid; public uint ParentPid; public ulong Created; internal SafeFileHandle Handle; }
    public sealed class OwnedTree : IDisposable {
        public readonly List<OwnedProcess> Records=new List<OwnedProcess>();
        public int Snapshots { get; private set; }
        static ulong Times(SafeFileHandle handle,out ulong exited) { FileTime created,ended,kernel,user; if(!GetProcessTimes(handle,out created,out ended,out kernel,out user)) throw Failure("owned process identity"); exited=ended.Value; return created.Value; }
        public void Root(uint pid,IntPtr handle) { SafeFileHandle copy; if(!DuplicateHandle(GetCurrentProcess(),handle,GetCurrentProcess(),out copy,0,false,2)) throw Failure("retain exact root process"); try { ulong exited; Records.Add(new OwnedProcess { Pid=pid,Created=Times(copy,out exited),Handle=copy }); } catch { copy.Dispose(); throw; } }
        public void Discover() {
            var rows=new List<ProcessEntry>(); var watch=Stopwatch.StartNew();
            using(var snapshot=CreateToolhelp32Snapshot(2,0)) {
                if(snapshot.IsInvalid) throw Failure("bounded owned process snapshot");
                var entry=new ProcessEntry(); entry.Size=(uint)Marshal.SizeOf(typeof(ProcessEntry));
                bool more=Process32FirstW(snapshot,ref entry); if(!more && Marshal.GetLastWin32Error()!=18) throw Failure("first process snapshot entry");
                while(more) { rows.Add(entry); if(rows.Count>8192 || watch.ElapsedMilliseconds>250) throw new IOException("process snapshot bound exceeded"); entry.Size=(uint)Marshal.SizeOf(typeof(ProcessEntry)); more=Process32NextW(snapshot,ref entry); }
                if(Marshal.GetLastWin32Error()!=18) throw Failure("process snapshot enumeration");
            }
            Snapshots++;
            for(int round=0;round<64;round++) {
                bool changed=false;
                foreach(var row in rows) {
                    if(watch.ElapsedMilliseconds>750) throw new IOException("owned discovery time bound exceeded");
                    bool known=false; foreach(var member in Records) if(member.Pid==row.Pid) { known=true; break; }
                    if(known || row.Pid==0) continue;
                    OwnedProcess parent=null; foreach(var member in Records) if(member.Pid==row.ParentPid) { parent=member; break; }
                    if(parent==null) continue;
                    var handle=OpenProcess(0x00101001,false,row.Pid);
                    if(handle.IsInvalid) { int error=Marshal.GetLastWin32Error(); handle.Dispose(); if(error==87) continue; throw new Win32Exception(error,"exact owned descendant open"); }
                    try {
                        ulong childExit,parentExit; ulong created=Times(handle,out childExit); Times(parent.Handle,out parentExit);
                        if(created<parent.Created || parentExit!=0 && created>parentExit) { handle.Dispose(); continue; }
                        if(Records.Count>=64) throw new IOException("owned descendant bound exceeded");
                        Records.Add(new OwnedProcess { Pid=row.Pid,ParentPid=row.ParentPid,Created=created,Handle=handle }); changed=true;
                    } catch { handle.Dispose(); throw; }
                }
                if(!changed) return;
            }
            throw new IOException("owned process closure rounds exceeded");
        }
        public bool Exited(OwnedProcess process) { uint result=WaitForSingleObject(process.Handle,0); if(result==0xffffffff) throw Failure("owned liveness query"); return result==0; }
        public void Terminate(OwnedProcess process) { if(!Exited(process) && !TerminateProcess(process.Handle,1) && !Exited(process)) throw Failure("exact owned termination"); }
        public bool Reap(OwnedProcess process,int milliseconds) { uint result=WaitForSingleObject(process.Handle,(uint)Math.Max(0,milliseconds)); if(result==0xffffffff) throw Failure("bounded exact owned reap"); return result==0; }
        public void Dispose() { foreach(var member in Records) member.Handle.Dispose(); }
    }
    public static bool StopRetainedRoot(IntPtr handle,int milliseconds) { using(var current=new SafeFileHandle(handle,false)) { uint state=WaitForSingleObject(current,0); if(state==0xffffffff) throw Failure("retained root liveness"); if(state!=0 && !TerminateProcess(current,1)) throw Failure("retained root termination"); state=WaitForSingleObject(current,(uint)Math.Max(0,milliseconds)); if(state==0xffffffff) throw Failure("retained root reap"); return state==0; } }
    public sealed class BoundedDrain : IDisposable {
        readonly Stream stream; readonly MemoryStream bytes=new MemoryStream(); readonly Task task;
        public volatile bool Overflow, Eof;
        public volatile string Error;
        public BoundedDrain(Stream value) {
            stream=value;
            task=Task.Run(async () => { var buffer=new byte[4096]; try { while(true) { int count=await stream.ReadAsync(buffer,0,buffer.Length).ConfigureAwait(false); if(count==0) { Eof=true; return; } lock(bytes) { if(bytes.Length+count>1048576) { Overflow=true; return; } bytes.Write(buffer,0,count); } } } catch(Exception error) { Error=error.GetType().Name+": "+error.Message.Substring(0,Math.Min(512,error.Message.Length)); } });
        }
        public bool Wait(int milliseconds) { return task.Wait(Math.Max(0,milliseconds)); }
        public byte[] Bytes() { lock(bytes) return bytes.ToArray(); }
        public void Dispose() { stream.Dispose(); }
    }
}
'@
function Require($condition,[string]$message){if(-not $condition){throw $message}}
function Exact-Keys($value,[string[]]$names){Require ($value -is [Collections.Generic.Dictionary[string,object]] -and $value.Count -eq $names.Count -and @($names|Where-Object{-not $value.ContainsKey($_)}).Count -eq 0) 'Exact metadata object keys required'}
function Json-Value($element,[int]$depth=0){
 Require ([DateTimeOffset]::UtcNow -lt $script:preflightDeadline) 'Metadata parsing deadline exceeded'
 Require ($depth -le 32) 'JSON depth exceeded'
 switch($element.ValueKind.ToString()){
  'Object' {$value=[Collections.Generic.Dictionary[string,object]]::new([StringComparer]::Ordinal);foreach($property in $element.EnumerateObject()){Require ($value.Count -lt 30000 -and -not $value.ContainsKey($property.Name)) 'Duplicate or excessive JSON object';$value.Add($property.Name,(Json-Value $property.Value ($depth+1)))};return ,$value}
  'Array' {$value=[Collections.Generic.List[object]]::new();foreach($member in $element.EnumerateArray()){Require ($value.Count -lt 30000) 'Excessive JSON array';$value.Add((Json-Value $member ($depth+1)))};return ,($value.ToArray())}
  'String' {$value=$element.GetString();Require ($value.Length -le 32768) 'JSON string bound exceeded';return $value}
  'Number' {$integer=0L;if($element.TryGetInt64([ref]$integer)){return $integer};$number=$element.GetDouble();Require (-not [double]::IsNaN($number) -and -not [double]::IsInfinity($number)) 'Nonfinite JSON number';return $number}
  'True' {return $true}
  'False' {return $false}
  'Null' {return $null}
  default {throw 'Unsupported JSON value'}
 }
}
function Parse-Bytes([byte[]]$raw){$options=[Text.Json.JsonDocumentOptions]::new();$options.MaxDepth=32;$document=[Text.Json.JsonDocument]::Parse([ReadOnlyMemory[byte]]::new($raw),$options);try{return ,(Json-Value $document.RootElement)}finally{$document.Dispose()}}
function Require-Text($value,[string]$name,[string]$expected){Require ($value.ContainsKey($name) -and $value[$name] -is [string] -and $value[$name] -ceq $expected) ('Exact text required: '+$name)}
function Require-Hash($value,[string]$name){Require ($value.ContainsKey($name) -and $value[$name] -is [string] -and $value[$name] -cmatch '^[0-9a-f]{64}$') ('Exact hash required: '+$name)}
function Require-Integer($value,[string]$name,[long]$expected){Require ($value.ContainsKey($name) -and $value[$name] -is [long] -and $value[$name] -eq $expected) ('Exact integer required: '+$name)}
function Require-Boolean($value,[string]$name,[bool]$expected){Require ($value.ContainsKey($name) -and $value[$name] -is [bool] -and $value[$name] -eq $expected) ('Exact Boolean required: '+$name)}
function Require-Zero($value){$names=@('source_updates','restore_count','support_updates','gradient_updates','target_inference_calls','query_count','model_constructions','measured_cells');Exact-Keys $value $names;foreach($name in $names){Require-Integer $value $name 0}}
function Utc-Time($value,[string]$name){Require ($value.ContainsKey($name) -and $value[$name] -is [string] -and $value[$name] -cmatch '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,7})?(Z|\+00:00)$') ('Explicit UTC time required: '+$name);$time=[DateTimeOffset]::MinValue;Require ([DateTimeOffset]::TryParse($value[$name],[Globalization.CultureInfo]::InvariantCulture,[Globalization.DateTimeStyles]::None,[ref]$time) -and $time.Offset -eq [TimeSpan]::Zero) 'Invalid UTC time refused';return $time}
$pinsHeld=[Collections.Generic.List[object]]::new()
function Hold-File([string]$path,[string]$expected,[long]$maximum=8388608,[bool]$retain=$true){$pin=[ChoAggregateNative]::Pin($path,$maximum,$retain);$pinsHeld.Add($pin);if($expected){Require ($pin.Sha256 -ceq $expected) ('Retained physical hash changed: '+$path)};return $pin}
function Write-New([string]$path,$value){$raw=[Text.UTF8Encoding]::new($false).GetBytes(($value|ConvertTo-Json -Depth 24 -Compress)+[char]10);Require ($raw.Length -le 8388608) 'Output metadata bound exceeded';$stream=[IO.File]::Open($path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read);try{$stream.Write($raw,0,$raw.Length);$stream.Flush($true)}finally{$stream.Dispose()}}
$pauses=@('20261007','20261012','20261013','20261015','20261025')|ForEach-Object{"D:\Aenv\pro2\WORK\resume-$_-001\coordination\PRO2_REQUEST_PRO3_PAUSE.json"}
$script:minRam=[uint64]::MaxValue;$script:minDisk=[uint64]::MaxValue
function Floors {$availableRam=[ChoAggregateNative]::AvailableMemory();$availableDisk=[ChoAggregateNative]::AvailableDisk();$script:minRam=[math]::Min($script:minRam,$availableRam);$script:minDisk=[math]::Min($script:minDisk,$availableDisk);Require ($availableRam -ge 4GB) 'Active RAM floor';Require ($availableDisk -ge 20GB) 'Disk floor';foreach($path in $pauses){Require (-not [ChoAggregateNative]::Exists($path)) 'Genuine peer pause'}}
$unused=@('attempt_001.json','result.json','supervision_001.json','supervisor-attempt_001.json','stdout_001.json','stderr_001.json')
function Unused([bool]$attemptWritten=$false){foreach($name in $unused){if($attemptWritten -and $name -ceq 'supervisor-attempt_001.json'){continue};Require (-not [ChoAggregateNative]::Exists((Join-Path $run $name))) 'Aggregate scope already used'}}
$process=$null;$tree=$null;$outDrain=$null;$errDrain=$null
try{
 $self=Hold-File $PSCommandPath '' 262144
 $supervisorSha=$self.Sha256
 [void](Hold-File $source $sourceSha 262144)
 $admissionPin=Hold-File (Join-Path $run 'admission.json') $AdmissionSha256
 $proofPin=Hold-File (Join-Path $run 'proofs.json') $ProofsSha256
 $approved=Parse-Bytes $admissionPin.Raw
 $request=Parse-Bytes $proofPin.Raw
 Require ($approved -is [Collections.Generic.Dictionary[string,object]]) 'Root admission object required'
 Require-Text $approved 'schema' 'cho51_canonical_boundary_aggregate_admission_v1'
 Require-Boolean $approved 'accepted' $true
 Require-Hash $approved 'peer_release_sha256'
 Require ($approved.ContainsKey('peer_release_path') -and $approved.peer_release_path -is [string]) 'Exact peer path required'
 $peerPin=Hold-File $approved.peer_release_path $approved.peer_release_sha256
 $peer=Parse-Bytes $peerPin.Raw
 Require ($peer -is [Collections.Generic.Dictionary[string,object]]) 'Peer grant object required'
 Require-Text $peer 'schema' 'pro2_pro3_compute_release_v1'
 Require-Boolean $peer 'released' $true
 Require-Hash $approved 'supervisor_review_sha256'
 Require-Text $peer 'supervisor_review_sha256' $approved.supervisor_review_sha256
 $reviewPin=Hold-File (Join-Path $run 'supervisor-review.json') $approved.supervisor_review_sha256 262144
 $review=Parse-Bytes $reviewPin.Raw
 Require ($review -is [Collections.Generic.Dictionary[string,object]]) 'Independent source-only supervisor review object required'
 Require-Text $review 'schema' 'cho51_canonical_boundary_aggregate_supervisor_review_v1'
 Require-Boolean $review 'accepted' $true
 Require-Boolean $review 'source_only' $true
 Require ($review.ContainsKey('remaining_actionable_findings') -and $review.remaining_actionable_findings -is [object[]] -and $review.remaining_actionable_findings.Count -eq 0) 'Supervisor review has unresolved findings'
 $reviewSource='runs/coordination/cho51_canonical_boundary_20261025_v5_aggregate/aggregate.py'
 $reviewSelf='runs/coordination/cho51_canonical_boundary_20261025_v5_aggregate/supervise.ps1'
 Exact-Keys $review.files @($reviewSource,$reviewSelf)
 Require-Text $review.files $reviewSource $sourceSha
 Require-Text $review.files $reviewSelf $supervisorSha
 foreach($record in @($approved,$peer)){
  foreach($row in @(@('scope',$scope),@('proofs_sha256',$ProofsSha256),@('batch_plan_sha256',$planSha),@('aggregate_source_sha256',$sourceSha),@('supervisor_sha256',$supervisorSha))){Require-Text $record $row[0] $row[1]}
  foreach($row in @(@('maximum_jobs',0),@('maximum_interpreter_invocations',1),@('maximum_seconds',300),@('expected_historical_metadata_tests',133),@('expected_batches',3),@('expected_controls_per_batch',34),@('startup_ram_gib',4),@('active_ram_gib',4),@('disk_gib',20))){Require-Integer $record $row[0] $row[1]}
  Require-Boolean $record 'automatic_retry_permitted' $false
  Require-Boolean $record 'scientific_admission' $false
  Require ($record.ContainsKey('expected_numerical_budget')) 'Explicit zero budget required'
  Require-Zero $record.expected_numerical_budget
 }
 $windowStart=Utc-Time $approved 'window_start_utc';$windowEnd=Utc-Time $approved 'window_end_utc'
 Require-Text $peer 'window_start_utc' $approved.window_start_utc
 Require-Text $peer 'window_end_utc' $approved.window_end_utc
 [void](Utc-Time $peer 'window_start_utc');[void](Utc-Time $peer 'window_end_utc')
 $deadline=Utc-Time $approved 'deadline_utc';$admissionObserved=Utc-Time $approved 'observed_utc'
 Require ($admissionObserved -le $entry -and $windowStart -le $entry -and $entry -lt $windowEnd) 'Fresh observed Root admission and exact live peer window required'
 $now=[DateTimeOffset]::UtcNow
 Require ($deadline -gt $now -and $deadline -le $now.AddSeconds(300) -and $deadline -le $windowEnd) 'Exact bounded aggregate deadline required'
 $hardEnd=$entry.AddSeconds(300);if($deadline -lt $hardEnd){$hardEnd=$deadline};if($windowEnd -lt $hardEnd){$hardEnd=$windowEnd}
 $script:preflightDeadline=$hardEnd
 $cleanupEnd=$hardEnd.AddSeconds(-2)
 $stopAt=$hardEnd.AddSeconds(-45)
 Require (($stopAt-$now).TotalSeconds -ge 60) 'Insufficient runtime and reserved cleanup window'
 Exact-Keys $request @('schema','batch_plan_sha256','batches')
 Require-Text $request 'schema' 'cho51_canonical_boundary_aggregate_proofs_v1'
 Require-Text $request 'batch_plan_sha256' $planSha
 Exact-Keys $request.batches @('a','b','c')
 $proofNames=@('pins','result','closeout','lease','junit','native_receipt','native_admission','native_deadline','root_admission','peer_grant','external_supervision','archive_manifest')
 foreach($batch in @('a','b','c')){Exact-Keys $request.batches[$batch] $proofNames;foreach($name in $proofNames){$reference=$request.batches[$batch][$name];Exact-Keys $reference @('path','sha256');Require ($reference.path -is [string] -and [IO.Path]::IsPathFullyQualified($reference.path)) 'Direct proof path required';Require-Hash $reference 'sha256'}}
 Require-Text $request.batches.a.pins 'path' $aPins
 Require-Text $request.batches.a.pins 'sha256' $aPinsSha
 $aPin=Hold-File $aPins $aPinsSha
 $authenticatedPins=Parse-Bytes $aPin.Raw
 Require ($authenticatedPins.runtime_files -is [Collections.Generic.Dictionary[string,object]]) 'Authenticated runtime pin inventory required'
 $runtime=@('D:\Aenv\pro3\.venv\Scripts\python.exe','C:\Users\aladdin-alyanai\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python3.dll','C:\Users\aladdin-alyanai\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python312.dll')
 foreach($path in $runtime){Require-Hash $authenticatedPins.runtime_files $path;[void](Hold-File $path $authenticatedPins.runtime_files[$path] 67108864 $false)}
 Floors;Unused
 foreach($pin in $pinsHeld){$pin.Recheck()}
 $info=[Diagnostics.ProcessStartInfo]::new($runtime[0]);$info.UseShellExecute=$false;$info.CreateNoWindow=$true;$info.WindowStyle=[Diagnostics.ProcessWindowStyle]::Hidden;$info.WorkingDirectory=$root;$info.RedirectStandardOutput=$true;$info.RedirectStandardError=$true
 foreach($argument in @('-I','-S','-B',$source,'--expect-proofs',$ProofsSha256,'--expect-admission',$AdmissionSha256)){[void]$info.ArgumentList.Add($argument)}
 foreach($name in @('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS')){$info.Environment[$name]='1'}
 $info.Environment['CUDA_VISIBLE_DEVICES']='';$info.Environment['PYTHONDONTWRITEBYTECODE']='1'
 $process=[Diagnostics.Process]::new();$process.StartInfo=$info;$tree=[ChoAggregateNative+OwnedTree]::new()
 $rootPid=$null;$started=$false;$exitCode=$null;$timedOut=$false;$stopReason=$null;$stdoutEof=$false;$stderrEof=$false;$reaped=$false;$launchTime=$null;$discoveryComplete=$true
 $errors=[Collections.Generic.List[string]]::new()
 Write-New (Join-Path $run 'supervisor-attempt_001.json') ([ordered]@{schema='cho51_canonical_boundary_aggregate_supervisor_attempt_v1';observed_utc=[DateTimeOffset]::UtcNow.ToString('o');proofs_sha256=$ProofsSha256;admission_sha256=$AdmissionSha256;supervisor_sha256=$supervisorSha;supervisor_review_sha256=$approved.supervisor_review_sha256;a_pins_sha256=$aPinsSha;maximum_interpreter_invocations=1;maximum_jobs=0;automatic_retry_permitted=$false;scientific_admission=$false})
 function Remaining-Milliseconds([int]$maximum){$remaining=[math]::Floor(($cleanupEnd-[DateTimeOffset]::UtcNow).TotalMilliseconds);return [int][math]::Max(0,[math]::Min($maximum,$remaining))}
 try{
  Floors;Unused $true
  foreach($pin in $pinsHeld){$pin.Recheck()}
  Require ([DateTimeOffset]::UtcNow -ge $windowStart -and ([DateTimeOffset]::UtcNow-$entry).TotalSeconds -lt 255 -and ($stopAt-[DateTimeOffset]::UtcNow).TotalSeconds -ge 60) 'Immediate deadline/window check refused interpreter start'
  $launchTime=[DateTimeOffset]::UtcNow
  if(-not $process.Start()){throw 'Owned interpreter start failed'}
  $started=$true;$rootPid=$process.Id;$tree.Root([uint32]$rootPid,$process.Handle)
  $outDrain=[ChoAggregateNative+BoundedDrain]::new($process.StandardOutput.BaseStream);$errDrain=[ChoAggregateNative+BoundedDrain]::new($process.StandardError.BaseStream)
  try{$tree.Discover()}catch{$discoveryComplete=$false;throw}
  while($true){
   if($outDrain.Overflow -or $errDrain.Overflow){throw 'Bounded output overflow'}
   if($outDrain.Error -or $errDrain.Error){throw 'Bounded pipe drain failed'}
   Floors
   if([DateTimeOffset]::UtcNow -ge $stopAt){$timedOut=$true;throw 'Aggregate stop trigger with cleanup reserve'}
   $wait=[int][math]::Max(0,[math]::Min(100,[math]::Floor(($stopAt-[DateTimeOffset]::UtcNow).TotalMilliseconds)))
   if($process.WaitForExit($wait)){$exitCode=$process.ExitCode;break}
   try{$tree.Discover()}catch{$discoveryComplete=$false;throw}
  }
 }catch{$stopReason=$_.Exception.Message;$errors.Add('execution: '+$_.Exception.Message)}finally{
  if($started){
   if($tree.Records.Count -eq 0){$discoveryComplete=$false;try{[void][ChoAggregateNative]::StopRetainedRoot($process.Handle,(Remaining-Milliseconds 1000))}catch{$errors.Add('retained root fallback cleanup: '+$_.Exception.Message)}}
   for($round=0;$round -lt 4 -and [DateTimeOffset]::UtcNow -lt $cleanupEnd;$round++){
    try{$tree.Discover()}catch{$discoveryComplete=$false;$errors.Add('final descendant discovery: '+$_.Exception.Message)}
    foreach($member in @($tree.Records)){try{$tree.Terminate($member)}catch{$errors.Add('exact owned termination: '+$_.Exception.Message)}}
    foreach($member in @($tree.Records)){try{[void]$tree.Reap($member,(Remaining-Milliseconds 500))}catch{$errors.Add('bounded owned reap: '+$_.Exception.Message)}}
    $alive=$false;foreach($member in @($tree.Records)){try{if(-not $tree.Exited($member)){$alive=$true}}catch{$alive=$true;$errors.Add('owned final liveness: '+$_.Exception.Message)}}
    if(-not $alive -and $round -ge 1){break}
   }
   try{if($process.HasExited){$exitCode=$process.ExitCode}else{$errors.Add('root process remains alive')}}catch{$errors.Add('root exit query: '+$_.Exception.Message)}
   $reaped=$discoveryComplete -and $tree.Records.Count -gt 0
   foreach($member in @($tree.Records)){try{if(-not $tree.Exited($member)){$reaped=$false}}catch{$reaped=$false;$errors.Add('final owned identity reap: '+$_.Exception.Message)}}
  }
  foreach($drain in @($outDrain,$errDrain)){if($null -ne $drain){try{[void]$drain.Wait((Remaining-Milliseconds 1000))}catch{$errors.Add('bounded pipe wait: '+$_.Exception.Message)};try{$drain.Dispose()}catch{$errors.Add('pipe disposal: '+$_.Exception.Message)};try{[void]$drain.Wait((Remaining-Milliseconds 500))}catch{$errors.Add('bounded post-disposal pipe wait: '+$_.Exception.Message)}}}
  if($null -ne $outDrain){$stdoutEof=$outDrain.Eof -and -not $outDrain.Overflow -and -not $outDrain.Error;if($outDrain.Overflow){$errors.Add('stdout exceeded 1 MiB')};if($outDrain.Error){$errors.Add('stdout drain: '+$outDrain.Error)}}
  if($null -ne $errDrain){$stderrEof=$errDrain.Eof -and -not $errDrain.Overflow -and -not $errDrain.Error;if($errDrain.Overflow){$errors.Add('stderr exceeded 1 MiB')};if($errDrain.Error){$errors.Add('stderr drain: '+$errDrain.Error)}}
  foreach($row in @(@('stdout_001.json',$outDrain),@('stderr_001.json',$errDrain))){if($null -ne $row[1]){try{$bytes=$row[1].Bytes();Write-New (Join-Path $run $row[0]) ([ordered]@{bytes=$bytes.Length;text=[Text.UTF8Encoding]::new($false).GetString($bytes);overflow=$row[1].Overflow;eof=$row[1].Eof;error=$row[1].Error})}catch{$errors.Add('bounded output evidence: '+$_.Exception.Message)}}}
  foreach($pin in $pinsHeld){try{$pin.Recheck()}catch{$errors.Add('final retained source/input identity: '+$_.Exception.Message)}}
  if($null -ne $process){try{$process.Dispose()}catch{$errors.Add('root handle disposal: '+$_.Exception.Message)}}
  if($null -ne $tree){try{$tree.Dispose()}catch{$errors.Add('owned handle disposal: '+$_.Exception.Message)}}
  $observedEnd=[DateTimeOffset]::UtcNow;$watch.Stop()
  if($observedEnd -ge $hardEnd -or $watch.Elapsed.TotalSeconds -gt 300){$timedOut=$true;$errors.Add('absolute external deadline exceeded')}
  if($errors.Count -gt 0 -and -not $stopReason){$stopReason='Supervision or cleanup failure'}
  $identities=@($tree.Records|ForEach-Object{[ordered]@{pid=$_.Pid;parent_pid=$_.ParentPid;creation_filetime=$_.Created.ToString()}})
  $super=[ordered]@{schema='cho51_canonical_boundary_aggregate_supervision_v1';started_utc=$entry.ToString('o');interpreter_started_utc=$(if($launchTime){$launchTime.ToString('o')}else{$null});ended_utc=$observedEnd.ToString('o');elapsed_seconds=$watch.Elapsed.TotalSeconds;owned_pid=$rootPid;observed_owned_pids=@($tree.Records|ForEach-Object{$_.Pid}|Sort-Object);observed_owned_identities=$identities;descendant_snapshots=$tree.Snapshots;owned_tree_discovery_complete=$discoveryComplete;limit_seconds=300;absolute_deadline_utc=$deadline.ToString('o');absolute_window_end_utc=$windowEnd.ToString('o');cleanup_reserve_seconds=45;stop_trigger_utc=$stopAt.ToString('o');timed_out=$timedOut;stop_reason=$stopReason;errors=@($errors);exit_code=$exitCode;interpreter_started=$started;owned_tree_reaped=$reaped;stdout_eof=$stdoutEof;stderr_eof=$stderrEof;stdout_maximum_bytes=1048576;stderr_maximum_bytes=1048576;minimum_available_ram_bytes=$script:minRam;minimum_available_disk_bytes=$script:minDisk;aggregate_source_sha256=$sourceSha;supervisor_sha256=$supervisorSha;supervisor_review_sha256=$approved.supervisor_review_sha256;proofs_sha256=$ProofsSha256;admission_sha256=$AdmissionSha256;a_pins_sha256=$aPinsSha;candidate_imported=$false;job_created=$false;maximum_interpreter_invocations=1;scientific_admission=$false}
  Write-New (Join-Path $run 'supervision_001.json') $super
  $super|ConvertTo-Json -Depth 12
 }
 if(-not $started -or $exitCode -ne 0 -or -not $reaped -or -not $stdoutEof -or -not $stderrEof -or $stopReason -or $errors.Count -ne 0 -or $timedOut -or $observedEnd -gt $hardEnd){exit 1}
}finally{
 foreach($pin in $pinsHeld){$pin.Dispose()}
}
