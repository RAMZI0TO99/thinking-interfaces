// Q-only trusted bootstrap helper. Compiled in memory only after fresh admission.
// Owns an outer Job before native creation; no PID lookup, reopen or tree sweep.
using System;
using System.ComponentModel;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;
using System.Diagnostics;

namespace QNative {
public sealed class Owner : IDisposable {
    [StructLayout(LayoutKind.Sequential)] struct Basic {
        public long ProcessTime, JobTime; public uint Flags;
        public UIntPtr Minimum, Maximum; public uint ActiveLimit;
        public UIntPtr Affinity; public uint Priority, Scheduling;
    }
    [StructLayout(LayoutKind.Sequential)] struct IO {public ulong a,b,c,d,e,f;}
    [StructLayout(LayoutKind.Sequential)] struct Extended {
        public Basic Basic; public IO IO; public UIntPtr ProcessMemory, JobMemory, PeakProcess, PeakJob;
    }
    [StructLayout(LayoutKind.Sequential)] struct Accounting {
        public long a,b,c,d; public uint Faults, Total, Active, Terminated;
    }
    [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)] struct Startup {
        public uint cb; public IntPtr Reserved, Desktop, Title;
        public uint x,y,w,h,cx,cy,Fill,Flags; public ushort Show, ReservedSize;
        public IntPtr ReservedBytes, Input, Output, Error;
    }
    [StructLayout(LayoutKind.Sequential)] struct StartupEx {public Startup Startup;public IntPtr Attributes;}
    [StructLayout(LayoutKind.Sequential)] struct Info {public IntPtr Process,Thread;public uint Pid,Tid;}
    [StructLayout(LayoutKind.Sequential)] struct Memory {
        public uint Length,Load;public ulong Total,Available,PageTotal,PageAvailable,VirtualTotal,VirtualAvailable,Extended;
    }
    [StructLayout(LayoutKind.Sequential)] struct ProcessMemory {
        public uint Length, Faults;public UIntPtr PeakWorking,Working,PeakPaged,Paged,PeakNonpaged,Nonpaged,Pagefile,PeakPagefile,Private;
    }
    [StructLayout(LayoutKind.Sequential)] struct FileID {public ulong Volume,Low,High;}

    [DllImport("kernel32.dll",SetLastError=true,CharSet=CharSet.Unicode)] static extern IntPtr CreateJobObjectW(IntPtr security,string name);
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool SetInformationJobObject(IntPtr job,int cls,ref Extended info,int length);
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool QueryInformationJobObject(IntPtr job,int cls,ref Extended info,int length,IntPtr result);
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool QueryInformationJobObject(IntPtr job,int cls,ref Accounting info,int length,IntPtr result);
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool InitializeProcThreadAttributeList(IntPtr list,int count,int flags,ref UIntPtr size);
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool UpdateProcThreadAttribute(IntPtr list,uint flags,IntPtr key,IntPtr value,UIntPtr size,IntPtr previous,IntPtr returned);
    [DllImport("kernel32.dll")] static extern void DeleteProcThreadAttributeList(IntPtr list);
    [DllImport("kernel32.dll",SetLastError=true,CharSet=CharSet.Unicode)] static extern bool CreateProcessW(string app,StringBuilder command,IntPtr ps,IntPtr ts,bool inherit,uint flags,IntPtr environment,string cwd,ref StartupEx startup,ref Info info);
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool IsProcessInJob(IntPtr process,IntPtr job,out bool present);
    [DllImport("kernel32.dll",SetLastError=true)] static extern uint ResumeThread(IntPtr thread);
    [DllImport("kernel32.dll",SetLastError=true)] static extern uint WaitForSingleObject(IntPtr obj,uint milliseconds);
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool GetExitCodeProcess(IntPtr process,out uint code);
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool GetProcessTimes(IntPtr process,out long creation,out long exit,out long kernel,out long user);
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool SetHandleInformation(IntPtr handle,uint mask,uint flags);
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool TerminateJobObject(IntPtr job,uint code);
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool TerminateProcess(IntPtr process,uint code);
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool CloseHandle(IntPtr handle);
    [DllImport("kernel32.dll")] static extern IntPtr GetCurrentProcess();
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool GlobalMemoryStatusEx(ref Memory status);
    [DllImport("kernel32.dll",SetLastError=true,CharSet=CharSet.Unicode)] static extern bool GetDiskFreeSpaceExW(string root,out ulong available,out ulong total,out ulong free);
    [DllImport("psapi.dll",SetLastError=true)] static extern bool GetProcessMemoryInfo(IntPtr process,ref ProcessMemory counters,int length);
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool GetFileInformationByHandleEx(IntPtr file,int cls,out FileID id,int length);
    [DllImport("kernel32.dll",SetLastError=true,CharSet=CharSet.Unicode)] static extern IntPtr CreateFileW(string name,uint access,uint sharing,IntPtr security,uint creation,uint flags,IntPtr template);
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool CreatePipe(out IntPtr read,out IntPtr write,IntPtr security,uint bytes);
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool ReadFile(IntPtr file,byte[] buffer,uint bytes,out uint read,IntPtr overlapped);
    [DllImport("kernel32.dll")] static extern IntPtr GetCurrentThread();
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool DuplicateHandle(IntPtr sourceProcess,IntPtr source,IntPtr targetProcess,out IntPtr target,uint access,bool inherit,uint options);
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool CancelSynchronousIo(IntPtr thread);

    // Original anonymous-pipe readers and reader-thread handles are owned here.
    // At most 1MiB retained plus one 4KiB chunk per channel; overflow stops the
    // owned Job immediately. Neither an output file nor a sampled file-size cap
    // is used. Anonymous-pipe kernel buffers are requested at 4KiB (OS sizing is
    // trusted platform behavior, not a claimed byte-exact kernel allocation).
    sealed class Capture {
        readonly Owner owner;
        readonly byte[] retained=new byte[1024*1024];
        readonly ManualResetEvent ready=new ManualResetEvent(false);
        IntPtr read,write,threadHandle;
        Thread reader;
        int length;
        public bool Eof,Overflow,ReaderClosed,WriterClosed,ThreadHandleClosed,Joined,CancelAttempted;
        public long ObservedBytes;
        public string ErrorText;
        public Capture(Owner parent){owner=parent;}
        public IntPtr Writer {get{return write;}}
        public int RetainedBytes {get{return length;}}
        public void Open() {
            if(!CreatePipe(out read,out write,IntPtr.Zero,4096))throw Error("owned stdio pipe creation");
            if(!SetHandleInformation(read,1,0) || !SetHandleInformation(write,1,1))throw Error("owned pipe inheritance");
        }
        public void Start() {
            reader=new Thread(ReadLoop);reader.IsBackground=true;reader.Start();
            if(!ready.WaitOne(500))throw new IOException("stdio reader startup");
            if(ErrorText!=null)throw new IOException(ErrorText);
        }
        void ReadLoop() {
            try {
                // Duplicate our own pseudo-handle once, without OpenThread/PID.
                if(!DuplicateHandle(GetCurrentProcess(),GetCurrentThread(),GetCurrentProcess(),out threadHandle,0,false,2))throw Error("original reader thread handle");
                ready.Set();
                byte[] chunk=new byte[4096];
                while(true) {
                    uint got;
                    if(!ReadFile(read,chunk,(uint)chunk.Length,out got,IntPtr.Zero)) {
                        int error=Marshal.GetLastWin32Error();
                        if(error==109){Eof=true;break;}
                        throw new Win32Exception(error,"owned stdio pipe read");
                    }
                    if(got==0){Eof=true;break;}
                    if(got>chunk.Length)throw new IOException("stdio native chunk bound");
                    ObservedBytes+=got;
                    int keep=Math.Min((int)got,retained.Length-length);
                    if(keep>0){Buffer.BlockCopy(chunk,0,retained,length,keep);length+=keep;}
                    if(keep!=(int)got){Overflow=true;owner.SetFault("stdio retained-byte overflow");break;}
                }
            }catch(Exception e){ErrorText=e.GetType().Name+": "+e.Message;owner.SetFault(ErrorText);}
            finally{ready.Set();}
        }
        public void CloseWriter() {
            if(write!=IntPtr.Zero){WriterClosed=CloseHandle(write);write=IntPtr.Zero;if(!WriterClosed)owner.SetFault("original pipe writer close");}
        }
        public void Finish(double until) {
            CloseWriter();
            if(reader==null){Joined=true;return;}
            Joined=reader.Join(owner.Remaining(until,250));
            if(!Joined) {
                CancelAttempted=true;
                if(threadHandle!=IntPtr.Zero && !CancelSynchronousIo(threadHandle) && Marshal.GetLastWin32Error()!=1168)
                    owner.CleanupFailure("stdio synchronous cancellation failed");
                Joined=reader.Join(owner.Remaining(until,100));
            }
            if(!Joined)owner.CleanupFailure("original stdio reader did not join");
            if(!Eof || Overflow || ErrorText!=null)owner.CleanupFailure("stdio did not reach strict bounded EOF");
        }
        public void CloseOriginals() {
            if(!Joined)throw new IOException("cannot close active original reader");
            if(read!=IntPtr.Zero){ReaderClosed=CloseHandle(read);read=IntPtr.Zero;if(!ReaderClosed)owner.CleanupFailure("original pipe reader close");}
            if(threadHandle!=IntPtr.Zero){ThreadHandleClosed=CloseHandle(threadHandle);threadHandle=IntPtr.Zero;if(!ThreadHandleClosed)owner.CleanupFailure("original reader thread handle close");}
            ready.Dispose();
        }
        public string Text() {
            if(!Joined || !Eof || Overflow || ErrorText!=null)throw new IOException("stdio incomplete/overflowed");
            return new UTF8Encoding(false,true).GetString(retained,0,length);
        }
    }

    IntPtr job;
    Info info; // Native output is retained even if managed creation bookkeeping fails.
    readonly long origin;
    readonly DateTime utcOrigin;
    readonly string stop;
    readonly ManualResetEvent done=new ManualResetEvent(false);
    Thread watchdog;
    Capture stdout,stderr;
    bool disposed;
    volatile bool cleaning;
    double cleanupUntil;
    long faultAt;
    public string Fault;
    public string CleanupError;
    public bool LimitsVerified, CreationAttempted, AtomicMembership, Resumed, JobEmpty, JobClosed, ProcessClosed, ThreadClosed, Reaped;
    public long CreationFileTime;
    public uint Pid {get{return info.Pid;}}
    public long MinimumRam=long.MaxValue, MinimumDisk=long.MaxValue, PeakCallerPrivate, PeakJobBytes, PeakProcessBytes;
    public int Samples;
    public bool InputClosed;
    public bool StdoutEof {get{return stdout!=null && stdout.Eof;}}
    public bool StderrEof {get{return stderr!=null && stderr.Eof;}}
    public bool StdoutOverflow {get{return stdout!=null && stdout.Overflow;}}
    public bool StderrOverflow {get{return stderr!=null && stderr.Overflow;}}
    public bool StdoutReaderClosed {get{return stdout!=null && stdout.ReaderClosed;}}
    public bool StderrReaderClosed {get{return stderr!=null && stderr.ReaderClosed;}}
    public bool StdoutWriterClosed {get{return stdout!=null && stdout.WriterClosed;}}
    public bool StderrWriterClosed {get{return stderr!=null && stderr.WriterClosed;}}
    public bool StdoutThreadClosed {get{return stdout!=null && stdout.ThreadHandleClosed;}}
    public bool StderrThreadClosed {get{return stderr!=null && stderr.ThreadHandleClosed;}}
    public bool StdoutJoined {get{return stdout!=null && stdout.Joined;}}
    public bool StderrJoined {get{return stderr!=null && stderr.Joined;}}
    public bool StdoutCancelled {get{return stdout!=null && stdout.CancelAttempted;}}
    public bool StderrCancelled {get{return stderr!=null && stderr.CancelAttempted;}}
    public int StdoutBytes {get{return stdout==null?0:stdout.RetainedBytes;}}
    public int StderrBytes {get{return stderr==null?0:stderr.RetainedBytes;}}
    public long StdoutObserved {get{return stdout==null?0:stdout.ObservedBytes;}}
    public long StderrObserved {get{return stderr==null?0:stderr.ObservedBytes;}}
    public string StdoutError {get{return stdout==null?null:stdout.ErrorText;}}
    public string StderrError {get{return stderr==null?null:stderr.ErrorText;}}
    public bool WatchdogJoined;
    public string StdoutText(){return stdout==null?"":stdout.Text();}
    public string StderrText(){return stderr==null?"":stderr.Text();}
    public bool Started {get{return info.Process!=IntPtr.Zero;}}
    const ulong ProcessCap=512UL*1024*1024, JobCap=768UL*1024*1024;
    static Exception Error(string text){return new Win32Exception(Marshal.GetLastWin32Error(),text);}
    public double Elapsed {get{return (Stopwatch.GetTimestamp()-origin)/(double)Stopwatch.Frequency;}}
    int Remaining(double until,int reserve=0){return (int)Math.Max(0,Math.Min(5000,(until-Elapsed)*1000-reserve));}
    void CleanupFailure(string text){CleanupError=CleanupError==null?text:CleanupError+"; "+text;}
    public Owner(long originQpc,string originalUtc,string stopFile) {
        origin=originQpc;utcOrigin=DateTime.Parse(originalUtc,null,System.Globalization.DateTimeStyles.RoundtripKind).ToUniversalTime();stop=stopFile;
        if(IntPtr.Size!=8 || origin<=0 || Elapsed<0 || Elapsed>=45)throw new InvalidOperationException("Q caller bootstrap window/architecture");
        job=CreateJobObjectW(IntPtr.Zero,null);
        if(job==IntPtr.Zero)throw Error("outer Job creation");
        try {
            Extended limits=new Extended();
            limits.Basic.Flags=0x2000|0x100|0x200|0x8;
            limits.Basic.ActiveLimit=2;limits.ProcessMemory=(UIntPtr)ProcessCap;limits.JobMemory=(UIntPtr)JobCap;
            if(!SetInformationJobObject(job,9,ref limits,Marshal.SizeOf<Extended>()))throw Error("outer Job limits");
            Extended observed=new Extended();
            if(!QueryInformationJobObject(job,9,ref observed,Marshal.SizeOf<Extended>(),IntPtr.Zero) ||
               observed.Basic.Flags!=limits.Basic.Flags || observed.Basic.ActiveLimit!=2 ||
               observed.ProcessMemory.ToUInt64()!=ProcessCap || observed.JobMemory.ToUInt64()!=JobCap)throw new InvalidOperationException("outer limits query");
            LimitsVerified=true;
            watchdog=new Thread(Watch);watchdog.IsBackground=true;watchdog.Start();
        }catch{CloseHandle(job);job=IntPtr.Zero;throw;}
    }
    static void Minimum(ref long target,long value){long old;do{old=Interlocked.Read(ref target);if(value>=old)return;}while(Interlocked.CompareExchange(ref target,value,old)!=old);}
    static void Maximum(ref long target,long value){long old;do{old=Interlocked.Read(ref target);if(value<=old)return;}while(Interlocked.CompareExchange(ref target,value,old)!=old);}
    public long Sample() {
        Memory memory=new Memory();memory.Length=(uint)Marshal.SizeOf<Memory>();
        if(!GlobalMemoryStatusEx(ref memory))throw Error("RAM sensor");
        ulong available,total,free;
        if(!GetDiskFreeSpaceExW("D:\\",out available,out total,out free))throw Error("disk sensor");
        ProcessMemory self=new ProcessMemory();self.Length=(uint)Marshal.SizeOf<ProcessMemory>();
        if(!GetProcessMemoryInfo(GetCurrentProcess(),ref self,Marshal.SizeOf<ProcessMemory>()))throw Error("caller memory sensor");
        Minimum(ref MinimumRam,(long)memory.Available);Minimum(ref MinimumDisk,(long)available);
        Maximum(ref PeakCallerPrivate,(long)self.Private.ToUInt64());Interlocked.Increment(ref Samples);
        if(memory.Available<4UL*1024*1024*1024 || available<20UL*1024*1024*1024 || self.Private.ToUInt64()>ProcessCap)throw new InvalidOperationException("Q resource floor/caller cap");
        return (long)memory.Available;
    }
    void StopCheck() {
        DirectoryInfo dir=new FileInfo(stop).Directory;
        while(dir!=null){FileAttributes attr=File.GetAttributes(dir.FullName);if((attr&FileAttributes.ReparsePoint)!=0 || (attr&FileAttributes.Directory)==0)throw new IOException("stop ancestry");dir=dir.Parent;}
        try{File.GetAttributes(stop);throw new IOException("project stop present");}catch(FileNotFoundException){}
    }
    void SetFault(string error) {
        if(Interlocked.CompareExchange(ref Fault,error,null)==null)Interlocked.Exchange(ref faultAt,Stopwatch.GetTimestamp());
        if(job!=IntPtr.Zero)TerminateJobObject(job,125);
    }
    void Watch() {
        while(!done.WaitOne(100)){
            try{
                if(Elapsed>=65 || (cleaning && Elapsed>=Volatile.Read(ref cleanupUntil)) || (Fault!=null && (Stopwatch.GetTimestamp()-Interlocked.Read(ref faultAt))/(double)Stopwatch.Frequency>=5))
                    TerminateProcess(GetCurrentProcess(),125);
                if(Elapsed>=60 || DateTime.UtcNow>=utcOrigin.AddSeconds(60))SetFault("original Q work deadline");
                StopCheck();Sample();
                if(Fault!=null && (Stopwatch.GetTimestamp()-Interlocked.Read(ref faultAt))/(double)Stopwatch.Frequency>=5)
                    TerminateProcess(GetCurrentProcess(),125);
                if(Elapsed>=65)TerminateProcess(GetCurrentProcess(),124);
            }catch(Exception e){SetFault(e.GetType().Name+": "+e.Message);}
        }
    }
    public void Check() {
        if(Fault!=null)throw new InvalidOperationException(Fault);
        if(Elapsed>=60 || DateTime.UtcNow>=utcOrigin.AddSeconds(60))throw new InvalidOperationException("original work deadline");
        StopCheck();Sample();
    }
    static string Quote(string arg) {
        if(arg==null || arg.IndexOf('\0')>=0)throw new ArgumentException("command argument");
        StringBuilder result=new StringBuilder("\"");int slashes=0;
        foreach(char c in arg){if(c=='\\'){slashes++;continue;}result.Append('\\',c=='"'?slashes*2+1:slashes);result.Append(c);slashes=0;}
        result.Append('\\',slashes*2);result.Append('"');return result.ToString();
    }
    public void Start(string executable,string[] args,string cwd) {
        Check();if(CreationAttempted)throw new InvalidOperationException("once-only creation");
        IntPtr attributes=IntPtr.Zero,jobs=IntPtr.Zero,handles=IntPtr.Zero,input=IntPtr.Zero;bool initialized=false;
        try {
            stdout=new Capture(this);stdout.Open();
            stderr=new Capture(this);stderr.Open();
            stdout.Start();stderr.Start();Check();
            UIntPtr size=UIntPtr.Zero;
            if(InitializeProcThreadAttributeList(IntPtr.Zero,2,0,ref size) || Marshal.GetLastWin32Error()!=122 || size.ToUInt64()==0 || size.ToUInt64()>65536)throw Error("attribute size");
            attributes=Marshal.AllocHGlobal((int)size.ToUInt64());
            if(!InitializeProcThreadAttributeList(attributes,2,0,ref size))throw Error("attributes");
            initialized=true;
            jobs=Marshal.AllocHGlobal(IntPtr.Size);Marshal.WriteIntPtr(jobs,job);
            input=CreateFileW("NUL",0x80000000,3,IntPtr.Zero,3,0,IntPtr.Zero);
            if(input==IntPtr.Zero || input==new IntPtr(-1))throw Error("owned NUL input");
            handles=Marshal.AllocHGlobal(3*IntPtr.Size);Marshal.WriteIntPtr(handles,0,stdout.Writer);Marshal.WriteIntPtr(handles,IntPtr.Size,stderr.Writer);Marshal.WriteIntPtr(handles,2*IntPtr.Size,input);
            if(!UpdateProcThreadAttribute(attributes,0,(IntPtr)0x2000D,jobs,(UIntPtr)IntPtr.Size,IntPtr.Zero,IntPtr.Zero) ||
               !UpdateProcThreadAttribute(attributes,0,(IntPtr)0x20002,handles,(UIntPtr)(3*IntPtr.Size),IntPtr.Zero,IntPtr.Zero))throw Error("atomic Job/stdio attributes");
            StartupEx startup=new StartupEx();startup.Startup.cb=(uint)Marshal.SizeOf<StartupEx>();
            startup.Startup.Flags=0x100;startup.Startup.Input=input;startup.Startup.Output=stdout.Writer;startup.Startup.Error=stderr.Writer;startup.Attributes=attributes;
            StringBuilder command=new StringBuilder(Quote(executable));foreach(string arg in args)command.Append(" ").Append(Quote(arg));
            if(command.Length>=30000)throw new ArgumentException("bounded native command");
            if(!SetHandleInformation(input,1,1))throw Error("NUL inheritance");
            CreationAttempted=true;
            if(!CreateProcessW(executable,command,IntPtr.Zero,IntPtr.Zero,true,0x4|0x08000000|0x00080000,IntPtr.Zero,cwd,ref startup,ref info))throw Error("atomic suspended supervisor");
            long exit,kernel,user;
            if(!GetProcessTimes(info.Process,out CreationFileTime,out exit,out kernel,out user))throw Error("original process generation");
            bool member;
            if(!IsProcessInJob(info.Process,job,out member)||!member)throw Error("outer atomic membership");
            AtomicMembership=true;Check();
            if(ResumeThread(info.Thread)==0xffffffff)throw Error("resume supervisor");
            Resumed=true;
        } finally {
            if(stdout!=null)stdout.CloseWriter();
            if(stderr!=null)stderr.CloseWriter();
            if(initialized)DeleteProcThreadAttributeList(attributes);
            if(attributes!=IntPtr.Zero)Marshal.FreeHGlobal(attributes);
            if(jobs!=IntPtr.Zero)Marshal.FreeHGlobal(jobs);
            if(handles!=IntPtr.Zero)Marshal.FreeHGlobal(handles);
            if(input!=IntPtr.Zero && input!=new IntPtr(-1)){InputClosed=CloseHandle(input);if(!InputClosed)SetFault("owned input close");}
        }
    }
    uint Active() {
        Accounting count=new Accounting();
        if(!QueryInformationJobObject(job,1,ref count,Marshal.SizeOf<Accounting>(),IntPtr.Zero))throw Error("outer Job accounting");
        Extended peaks=new Extended();
        if(!QueryInformationJobObject(job,9,ref peaks,Marshal.SizeOf<Extended>(),IntPtr.Zero))throw Error("outer Job peaks");
        Maximum(ref PeakJobBytes,(long)peaks.PeakJob.ToUInt64());Maximum(ref PeakProcessBytes,(long)peaks.PeakProcess.ToUInt64());
        return count.Active;
    }
    public bool Poll() {
        Check();uint active=Active();
        if(info.Process==IntPtr.Zero)throw new InvalidOperationException("no original process");
        uint waited=WaitForSingleObject(info.Process,0);
        if(waited!=0 && waited!=258)throw Error("supervisor wait");
        Reaped=waited==0;
        return Reaped && active==0;
    }
    public uint ExitCode() {uint code;if(!Reaped || !GetExitCodeProcess(info.Process,out code))throw Error("supervisor exit");return code;}
    public void Dispose() {
        if(disposed)return;disposed=true;
        double until=Math.Min(65,Elapsed+5);
        if(Fault!=null)until=Math.Min(until,(Interlocked.Read(ref faultAt)-origin)/(double)Stopwatch.Frequency+5);
        Volatile.Write(ref cleanupUntil,until);cleaning=true;
        try {
            if(job!=IntPtr.Zero){
                if(Active()!=0 && !TerminateJobObject(job,125))throw Error("owned outer Job termination");
                while(Active()!=0 && Elapsed<until)Thread.Sleep(20);
                JobEmpty=Active()==0;
                if(!JobEmpty)throw new IOException("outer Job not empty");
            }
            if(info.Process!=IntPtr.Zero){Reaped=WaitForSingleObject(info.Process,(uint)Remaining(until,250))==0;if(!Reaped)throw new IOException("supervisor not reaped");}
        }catch(Exception e){CleanupFailure(e.GetType().Name+": "+e.Message);}
        finally {
            // Keep the watchdog running during accounting, termination, reap,
            // EOF drain and cancellation. All waits share the same deadline.
            try{if(stdout!=null)stdout.Finish(until);}catch(Exception e){CleanupFailure(e.Message);}
            try{if(stderr!=null)stderr.Finish(until);}catch(Exception e){CleanupFailure(e.Message);}
            done.Set();
            WatchdogJoined=watchdog==null || watchdog.Join(Remaining(until));
            if(!WatchdogJoined || (stdout!=null && !stdout.Joined) || (stderr!=null && !stderr.Joined)){
                CleanupFailure("owned watchdog/stdio thread not joined");
                TerminateProcess(GetCurrentProcess(),125);
                throw new IOException("self termination failed with original handles retained");
            }
            try{if(stdout!=null)stdout.CloseOriginals();}catch(Exception e){CleanupFailure(e.Message);}
            try{if(stderr!=null)stderr.CloseOriginals();}catch(Exception e){CleanupFailure(e.Message);}
            if(job!=IntPtr.Zero){JobClosed=CloseHandle(job);job=IntPtr.Zero;}
            if(info.Thread!=IntPtr.Zero){ThreadClosed=CloseHandle(info.Thread);info.Thread=IntPtr.Zero;}
            if(info.Process!=IntPtr.Zero){ProcessClosed=CloseHandle(info.Process);info.Process=IntPtr.Zero;}
            done.Dispose();
        }
    }
}
}

