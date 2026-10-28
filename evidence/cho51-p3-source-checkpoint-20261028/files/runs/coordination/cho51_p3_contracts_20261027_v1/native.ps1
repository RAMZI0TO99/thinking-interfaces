Add-Type -TypeDefinition @'
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;
using System.Threading.Tasks;
using Microsoft.Win32.SafeHandles;

public static class ChoP3Native {
    [StructLayout(LayoutKind.Sequential)] public struct FileTime { public uint Low, High; public ulong Value { get { return ((ulong)High << 32) | Low; } } }
    [StructLayout(LayoutKind.Sequential)] public struct FileInfo { public uint Attributes; public FileTime Created, Accessed, Written; public uint Volume, SizeHigh, SizeLow, Links, IndexHigh, IndexLow; public ulong Size { get { return ((ulong)SizeHigh << 32) | SizeLow; } } }
    [StructLayout(LayoutKind.Sequential)] public struct MemoryStatus { public uint Length, Load; public ulong TotalPhysical, AvailablePhysical, TotalPageFile, AvailablePageFile, TotalVirtual, AvailableVirtual, AvailableExtendedVirtual; }
    [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)] public struct ProcessEntry { public uint Size, Usage, Pid; public UIntPtr Heap; public uint Module, Threads, ParentPid; public int Priority; public uint Flags; [MarshalAs(UnmanagedType.ByValTStr, SizeConst=260)] public string Exe; }
    [StructLayout(LayoutKind.Sequential)] public struct ProcessBasicInformation { public IntPtr Reserved, Peb, Reserved2, Reserved3; public UIntPtr Pid, ParentPid; }
    public struct ProcessIdentity { public uint Pid, ParentPid; public ulong Created, Exited; }
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)] static extern SafeFileHandle CreateFileW(string path, uint access, uint share, IntPtr security, uint mode, uint flags, IntPtr template);
    [DllImport("kernel32.dll", SetLastError=true)] static extern bool GetFileInformationByHandle(SafeFileHandle handle, out FileInfo info);
    [DllImport("kernel32.dll", SetLastError=true)] static extern uint GetFileType(SafeFileHandle handle);
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)] static extern uint GetFinalPathNameByHandleW(SafeFileHandle handle, StringBuilder path, uint capacity, uint flags);
    [DllImport("kernel32.dll", SetLastError=true)] static extern bool ReadFile(SafeFileHandle handle, [Out] byte[] buffer, uint count, out uint read, IntPtr overlapped);
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)] static extern uint GetFileAttributesW(string path);
    [DllImport("kernel32.dll", SetLastError=true)] static extern bool GlobalMemoryStatusEx(ref MemoryStatus status);
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)] static extern bool GetDiskFreeSpaceExW(string directory, out ulong available, out ulong total, out ulong free);
    [DllImport("kernel32.dll", SetLastError=true)] static extern SafeFileHandle CreateToolhelp32Snapshot(uint flags, uint pid);
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)] static extern bool Process32FirstW(SafeFileHandle snapshot, ref ProcessEntry entry);
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)] static extern bool Process32NextW(SafeFileHandle snapshot, ref ProcessEntry entry);
    [DllImport("kernel32.dll", SetLastError=true)] static extern SafeFileHandle OpenProcess(uint access, bool inherit, uint pid);
    [DllImport("kernel32.dll", SetLastError=true)] static extern bool GetProcessTimes(SafeFileHandle process, out FileTime created, out FileTime exited, out FileTime kernel, out FileTime user);
    [DllImport("kernel32.dll", SetLastError=true)] static extern uint GetProcessId(SafeFileHandle process);
    [DllImport("kernel32.dll")] static extern void GetSystemTimePreciseAsFileTime(out FileTime time);
    [DllImport("ntdll.dll")] static extern int NtQueryInformationProcess(SafeFileHandle process, int informationClass, out ProcessBasicInformation information, uint length, out uint returned);
    [DllImport("kernel32.dll", SetLastError=true)] static extern bool TerminateProcess(SafeFileHandle process, uint code);
    [DllImport("kernel32.dll", SetLastError=true)] static extern uint WaitForSingleObject(SafeFileHandle handle, uint milliseconds);
    [DllImport("kernel32.dll", SetLastError=true)] static extern bool DuplicateHandle(IntPtr sourceProcess, IntPtr source, IntPtr targetProcess, out SafeFileHandle target, uint access, bool inherit, uint options);
    [DllImport("kernel32.dll")] static extern IntPtr GetCurrentProcess();
    static Exception Failure(string operation) { return new Win32Exception(Marshal.GetLastWin32Error(), operation); }
    static DateTime pinDeadlineUtc;
    static long pinDeadlineTicks;
    static string[] pinPauses;
    public static void ConfigurePinChecks(DateTime deadlineUtc, string[] pausePaths, double maximumRemainingSeconds) {
        if(deadlineUtc.Kind!=DateTimeKind.Utc || deadlineUtc<=DateTime.UtcNow || pausePaths==null || pausePaths.Length!=5 || Double.IsNaN(maximumRemainingSeconds) || maximumRemainingSeconds<=0 || maximumRemainingSeconds>300) throw new IOException("finite fresh pin deadline and five pauses required");
        double remaining=Math.Min(maximumRemainingSeconds,(deadlineUtc-DateTime.UtcNow).TotalSeconds);
        long deadlineTicks=Stopwatch.GetTimestamp()+(long)Math.Floor(remaining*Stopwatch.Frequency);
        pinDeadlineTicks=pinDeadlineTicks==0 ? deadlineTicks : Math.Min(pinDeadlineTicks,deadlineTicks);
        pinDeadlineUtc=deadlineUtc; pinPauses=(string[])pausePaths.Clone();
    }
    static void CheckPinBudget() {
        if(pinPauses==null || DateTime.UtcNow>=pinDeadlineUtc || Stopwatch.GetTimestamp()>=pinDeadlineTicks) throw new IOException("native physical pin deadline reached");
        if(AvailableMemory()<4294967296UL || AvailableDisk()<21474836480UL) throw new IOException("native physical pin active floor refused");
        foreach(string pause in pinPauses) if(Exists(pause)) throw new IOException("genuine peer pause during physical pin");
    }
    static void DirectHandlePath(SafeFileHandle handle,string expected) {
        var actual=new StringBuilder(4096);
        uint length=GetFinalPathNameByHandleW(handle,actual,(uint)actual.Capacity,0);
        if(length==0) throw Failure("normalized final physical path");
        if(length>=actual.Capacity || !actual.ToString().StartsWith(@"\\?\",StringComparison.Ordinal) || !String.Equals(actual.ToString().Substring(4),expected,StringComparison.OrdinalIgnoreCase)) throw new IOException("short-name, device or trailing-component alias refused");
    }
    static FileInfo Info(SafeFileHandle handle) { FileInfo value; if(!GetFileInformationByHandle(handle,out value)) throw Failure("physical file identity"); if(GetFileType(handle)!=1) throw new IOException("non-disk metadata refused"); return value; }
    static SafeFileHandle Open(string path, bool directory, bool contents) {
        var handle=CreateFileW(path,contents ? 0x80000000u : 0x80u,1,IntPtr.Zero,3,0x00200000u | (directory ? 0x02000000u : 0x08000000u),IntPtr.Zero);
        if(handle.IsInvalid) { handle.Dispose(); throw Failure("direct retained physical open"); }
        try { DirectHandlePath(handle,path); var info=Info(handle); if((info.Attributes & 0x400)!=0 || ((info.Attributes & 0x10)!=0)!=directory || (!directory && info.Links!=1 && !(info.Links==2 && info.Size==46480 && String.Equals(path,@"C:\Users\aladdin-alyanai\AppData\Local\Programs\Git\cmd\git.exe",StringComparison.OrdinalIgnoreCase)))) throw new IOException("reparse/nonregular/multilink file refused"); return handle; }
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
        CheckPinBudget();
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
                    CheckPinBudget();
                    uint count; if(!ReadFile(file,buffer,(uint)buffer.Length,out count,IntPtr.Zero)) throw Failure("bounded physical read");
                    if(count==0) break;
                    total+=count; if(total>(ulong)maximum) throw new IOException("physical byte bound exceeded");
                    digest.AppendData(buffer,0,(int)count); if(retain) bytes.Write(buffer,0,(int)count);
                }
                pin.Sha256=BitConverter.ToString(digest.GetHashAndReset()).Replace("-","").ToLowerInvariant(); pin.Raw=retain ? bytes.ToArray() : null;
            }
            if(total!=before.Size) throw new IOException("physical read length changed"); if(before.Links==2 && pin.Sha256!="da240fe9bc24895b3e04150a4990b8a6ff329ecabcd8f19684c2cc310da5ef3f") throw new IOException("exact admitted Git binary exception changed"); pin.Length=total; pin.Recheck(); CheckPinBudget(); return pin;
        } catch { pin.Dispose(); throw; }
    }
    public static bool Exists(string path) { uint value=GetFileAttributesW(path); if(value!=0xffffffff) return true; int error=Marshal.GetLastWin32Error(); if(error==2 || error==3) return false; throw new Win32Exception(error,"bounded local existence check"); }
    public static ulong AvailableMemory() { var status=new MemoryStatus(); status.Length=(uint)Marshal.SizeOf(typeof(MemoryStatus)); if(!GlobalMemoryStatusEx(ref status)) throw Failure("physical memory query"); return status.AvailablePhysical; }
    public static ulong AvailableDisk() { ulong available,total,free; if(!GetDiskFreeSpaceExW(@"D:\",out available,out total,out free)) throw Failure("local disk query"); return available; }
    static ProcessBasicInformation BasicIdentity(SafeFileHandle handle) {
        ProcessBasicInformation information; uint returned; uint length=(uint)Marshal.SizeOf(typeof(ProcessBasicInformation));
        int status=NtQueryInformationProcess(handle,0,out information,length,out returned);
        if(status!=0 || returned!=length || information.Pid.ToUInt64()==0 || information.Pid.ToUInt64()>UInt32.MaxValue || information.ParentPid.ToUInt64()>UInt32.MaxValue) throw new IOException("native retained PID/parent query refused: "+status.ToString("X8"));
        return information;
    }
    static ProcessIdentity ExactProcessIdentity(SafeFileHandle handle,uint expectedPid) {
        FileTime createdBefore,exitedBefore,kernel,user,createdAfter,exitedAfter;
        if(!GetProcessTimes(handle,out createdBefore,out exitedBefore,out kernel,out user)) throw Failure("owned creation identity before query");
        var before=BasicIdentity(handle); uint actualPid=GetProcessId(handle); if(actualPid==0) throw Failure("native retained PID query");
        if(!GetProcessTimes(handle,out createdAfter,out exitedAfter,out kernel,out user)) throw Failure("owned creation identity after query");
        var after=BasicIdentity(handle);
        if(actualPid!=expectedPid || before.Pid.ToUInt64()!=expectedPid || after.Pid.ToUInt64()!=expectedPid || before.ParentPid!=after.ParentPid || createdBefore.Value==0 || createdBefore.Value!=createdAfter.Value || exitedBefore.Value!=0 && exitedBefore.Value!=exitedAfter.Value) throw new IOException("retained process PID/parent/creation identity changed");
        return new ProcessIdentity { Pid=expectedPid,ParentPid=(uint)after.ParentPid.ToUInt64(),Created=createdAfter.Value,Exited=exitedAfter.Value };
    }
    static ulong PreciseTime() { FileTime time; GetSystemTimePreciseAsFileTime(out time); if(time.Value==0) throw new IOException("native snapshot clock unavailable"); return time.Value; }
    static void SnapshotClock(ulong started,long beforeTicks,long afterTicks) {
        long before=Stopwatch.GetTimestamp(); ulong observed=PreciseTime(); long after=Stopwatch.GetTimestamp();
        double minimum=(before-afterTicks)*10000000.0/Stopwatch.Frequency, maximum=(after-beforeTicks)*10000000.0/Stopwatch.Frequency;
        if(observed<started || observed-started<minimum-10000.0 || observed-started>maximum+10000.0) throw new IOException("snapshot UTC/monotonic clock discontinuity");
    }
    public sealed class OwnedProcess { public uint Pid; public uint ParentPid; public ulong Created; public ulong SnapshotCutoff; internal SafeFileHandle Handle; }
    public sealed class OwnedTree : IDisposable {
        public readonly List<OwnedProcess> Records=new List<OwnedProcess>();
        public int Snapshots { get; private set; }
        static ProcessIdentity RetainedIdentity(OwnedProcess process) { var actual=ExactProcessIdentity(process.Handle,process.Pid); if(actual.Created!=process.Created || actual.ParentPid!=process.ParentPid) throw new IOException("retained owner generation/parent changed"); return actual; }
        public void Root(uint pid,IntPtr handle) { SafeFileHandle copy; if(!DuplicateHandle(GetCurrentProcess(),handle,GetCurrentProcess(),out copy,0,false,2)) throw Failure("retain exact root process"); try { var actual=ExactProcessIdentity(copy,pid); Records.Add(new OwnedProcess { Pid=pid,ParentPid=actual.ParentPid,Created=actual.Created,Handle=copy }); } catch { copy.Dispose(); throw; } }
        public void Discover() {
            var rows=new List<ProcessEntry>(); var watch=Stopwatch.StartNew();
            foreach(var member in Records) RetainedIdentity(member);
            long snapshotTicks=Stopwatch.GetTimestamp(); ulong snapshotStarted=PreciseTime(); long snapshotTicksAfter=Stopwatch.GetTimestamp();
            using(var snapshot=CreateToolhelp32Snapshot(2,0)) {
                if(snapshot.IsInvalid) throw Failure("bounded owned process snapshot");
                var entry=new ProcessEntry(); entry.Size=(uint)Marshal.SizeOf(typeof(ProcessEntry));
                bool more=Process32FirstW(snapshot,ref entry); if(!more && Marshal.GetLastWin32Error()!=18) throw Failure("first process snapshot entry");
                while(more) { rows.Add(entry); if(rows.Count>8192 || watch.ElapsedMilliseconds>250) throw new IOException("process snapshot bound exceeded"); entry.Size=(uint)Marshal.SizeOf(typeof(ProcessEntry)); more=Process32NextW(snapshot,ref entry); }
                if(Marshal.GetLastWin32Error()!=18) throw Failure("process snapshot enumeration");
            }
            SnapshotClock(snapshotStarted,snapshotTicks,snapshotTicksAfter);
            foreach(var member in Records) RetainedIdentity(member);
            Snapshots++;
            for(int round=0;round<64;round++) {
                bool changed=false;
                foreach(var row in rows) {
                    if(watch.ElapsedMilliseconds>750) throw new IOException("owned discovery time bound exceeded");
                    bool known=false; foreach(var member in Records) if(member.Pid==row.Pid) { known=true; break; }
                    if(known || row.Pid==0) continue;
                    OwnedProcess parent=null; foreach(var member in Records) if(member.Pid==row.ParentPid) { parent=member; break; }
                    if(parent==null) continue;
                    var handle=OpenProcess(0x00101401,false,row.Pid);
                    if(handle.IsInvalid) { int error=Marshal.GetLastWin32Error(); handle.Dispose(); throw new Win32Exception(error,"snapshot descendant cannot be authenticated"); }
                    try {
                        SnapshotClock(snapshotStarted,snapshotTicks,snapshotTicksAfter);
                        var actual=ExactProcessIdentity(handle,row.Pid); var owner=RetainedIdentity(parent);
                        if(actual.ParentPid!=row.ParentPid || actual.ParentPid!=owner.Pid || actual.Created<=owner.Created || actual.Created>snapshotStarted || owner.Exited!=0 && actual.Created>owner.Exited) throw new IOException("snapshot row/actual handle/retained parent generation is uncertain");
                        var confirmed=ExactProcessIdentity(handle,row.Pid); var confirmedOwner=RetainedIdentity(parent);
                        if(confirmed.ParentPid!=actual.ParentPid || confirmed.Created!=actual.Created || confirmedOwner.Exited!=0 && actual.Created>confirmedOwner.Exited) throw new IOException("opened descendant ownership changed before adoption");
                        SnapshotClock(snapshotStarted,snapshotTicks,snapshotTicksAfter);
                        if(Records.Count>=64) throw new IOException("owned descendant bound exceeded");
                        Records.Add(new OwnedProcess { Pid=actual.Pid,ParentPid=actual.ParentPid,Created=actual.Created,SnapshotCutoff=snapshotStarted,Handle=handle }); changed=true;
                    } catch { handle.Dispose(); throw; }
                }
                if(!changed) return;
            }
            throw new IOException("owned process closure rounds exceeded");
        }
        public bool Exited(OwnedProcess process) { RetainedIdentity(process); uint result=WaitForSingleObject(process.Handle,0); if(result==0xffffffff) throw Failure("owned liveness query"); RetainedIdentity(process); return result==0; }
        public void Terminate(OwnedProcess process) { RetainedIdentity(process); if(!Exited(process) && !TerminateProcess(process.Handle,1) && !Exited(process)) throw Failure("exact owned termination"); RetainedIdentity(process); }
        public bool Reap(OwnedProcess process,int milliseconds) { RetainedIdentity(process); uint result=WaitForSingleObject(process.Handle,(uint)Math.Max(0,milliseconds)); if(result==0xffffffff) throw Failure("bounded exact owned reap"); RetainedIdentity(process); return result==0; }
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
