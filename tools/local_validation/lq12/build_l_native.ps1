# Dot-sourced only from the fresh pinned LQ1 caller after admission/source review.
# The original Q clock, independent guard and 512/768 MiB process/Job caps apply
# to every sequential compiler child. Binary outputs arrive on original pipes.
function RetainLAncestry([string]$path) {
    $chain=[Collections.Generic.List[string]]::new();$dir=[IO.FileInfo]::new($path).Directory
    while($null -ne $dir){$chain.Add($dir.FullName);$dir=$dir.Parent}
    for($index=$chain.Count-1;$index -ge 0;$index--){
        Check;$name=$chain[$index]
        if(-not $lDirectoryHandles.ContainsKey($name)){$lDirectoryHandles[$name]=[QNative.Owner]::RetainDirectory($name)}
    }
}
function NativeToolPin($path,$expected) {
    Check
    RetainLAncestry $path
    $cursor=[IO.FileInfo]::new($path)
    while($null -ne $cursor){if([IO.File]::GetAttributes($cursor.FullName) -band [IO.FileAttributes]::ReparsePoint){throw 'native tool reparse ancestry'};$cursor=if($cursor -is [IO.FileInfo]){$cursor.Directory}else{$cursor.Parent}}
    if($expected.bytes -isnot [long] -and $expected.bytes -isnot [int]){throw 'native tool byte type'}
    if($expected.bytes -lt 0 -or $expected.bytes -gt 256MB){throw 'native tool file bound'}
    $stream=[IO.FileStream]::new($path,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
    $inputs.Add($stream)
    $identity=[PNative3.Owner]::FileIdentity($stream.SafeFileHandle)
    $item=@{path=$path;stream=$stream;native_identity=$identity;reference=$expected}
    VerifyLNativeItem $item
    $lToolInputs.Add($item)
}
function VerifyLNativeItem($item) {
    Check;$stream=$item.stream
    [QNative.Owner]::StrictFile($stream.SafeFileHandle)
    if($stream.SafeFileHandle.IsClosed -or $stream.Length -ne $item.reference.bytes -or [PNative3.Owner]::FileIdentity($stream.SafeFileHandle) -cne $item.native_identity){throw 'L native retained identity/length'}
    $stream.Position=0;$hash=[Security.Cryptography.IncrementalHash]::CreateHash([Security.Cryptography.HashAlgorithmName]::SHA256)
    try{$buffer=[byte[]]::new(65536);$total=0L
        do{Check;$n=$stream.Read($buffer,0,$buffer.Length);if($n){$total+=$n;if($total -gt $item.reference.bytes){throw 'L native grew'};$hash.AppendData($buffer,0,$n)}}while($n)
        $digest=[Convert]::ToHexString($hash.GetHashAndReset()).ToLowerInvariant()
    }finally{$hash.Dispose();$stream.Position=0}
    if($total -ne $item.reference.bytes -or $digest -cne $item.reference.sha256 -or [PNative3.Owner]::FileIdentity($stream.SafeFileHandle) -cne $item.native_identity){throw 'L native retained hash/identity'}
}
function PublishLNative([string]$name,[byte[]]$bytes,[string]$role) {
    Check
    if($name -cnotmatch '^l-(observer|injection|target|observer-object|injection-object|target-object|callback|bundle)_[0-9a-f-]{36}\.(dll|obj|txt|json)$' -or $bytes.Length -eq 0 -or $bytes.Length -gt 1MB){throw 'L native output bound/name'}
    $path=Join-Path $phase $name
    RetainLAncestry $path
    $writer=$null;$anchor=$null;$strict=$null
    try{
        $writer=[IO.FileStream]::new($path,[IO.FileMode]::CreateNew,[IO.FileAccess]::ReadWrite,[IO.FileShare]::Read)
        $outputs.Add($writer);$writer.Write($bytes,0,$bytes.Length);$writer.Flush($true)
        $identity=[PNative3.Owner]::FileIdentity($writer.SafeFileHandle)
        $reference=@{path=$path.Replace('\','/');bytes=$bytes.Length;sha256=([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)).ToLowerInvariant());role=$role}
        VerifyLNativeItem @{stream=$writer;native_identity=$identity;reference=$reference}
        # Continuous file identity anchor across the writer-to-read transition.
        # Strict read sharing is incompatible with a live writer. The bridge
        # denies deletion; final strict acquisition+rehash refuses ordinary drift.
        # This is a local custody protocol, not a malicious same-user sandbox.
        $anchor=[IO.FileStream]::new($path,[IO.FileMode]::Open,[IO.FileAccess]::Read,([IO.FileShare]::ReadWrite))
        if([PNative3.Owner]::FileIdentity($anchor.SafeFileHandle) -cne $identity){throw 'L native bridge identity'}
        $writer.Dispose();$writer=$null
        $strict=[IO.FileStream]::new($path,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
        $inputs.Add($strict)
        $item=@{stream=$strict;native_identity=$identity;reference=$reference;role=$role}
        VerifyLNativeItem $item
        $anchor.Dispose();$anchor=$null
        $lNativeArtifacts.Add($item)
        return @{reference=$reference;native_identity=$identity;owner='q_original_strict_receiver';sharing=@{read=$true;write=$false;delete=$false}}
    }finally{if($null -ne $writer){$writer.Dispose()};if($null -ne $anchor){$anchor.Dispose()}}
}
function RunLTool([string]$executable,[string[]]$arguments,[string]$purpose) {
    Check
    if(-not $request.native_compiler.files.ContainsKey($executable)){throw 'unadmitted compiler executable'}
    $processOwner=$null;$exitCode=$null;$output=$null;$failure=$null;$stderr=''
    try{
        $processOwner=[QNative.Owner]::new($originQpc,$originUtc.ToString('o'),$stopPath)
        $processOwner.Start($executable,$arguments,$projectRoot)
        while(-not $processOwner.Poll()){Check;Start-Sleep -Milliseconds 20}
        $exitCode=$processOwner.ExitCode()
    }catch{$failure=$_.Exception.Message}
    finally{
        if($null -ne $processOwner){
            $processOwner.Dispose()
            $fact=@{purpose=$purpose;executable=$executable;arguments=$arguments;exit_code=$exitCode;error=$failure;
                pid=$processOwner.Pid;creation_filetime=$processOwner.CreationFileTime;limits_verified=$processOwner.LimitsVerified;
                atomic_membership=$processOwner.AtomicMembership;resumed=$processOwner.Resumed;reaped=$processOwner.Reaped;
                job_empty=$processOwner.JobEmpty;job_closed=$processOwner.JobClosed;process_closed=$processOwner.ProcessClosed;
                thread_closed=$processOwner.ThreadClosed;watchdog_joined=$processOwner.WatchdogJoined;owned_nul_closed=$processOwner.InputClosed;
                stdout_eof=$processOwner.StdoutEof;stderr_eof=$processOwner.StderrEof;stdout_joined=$processOwner.StdoutJoined;stderr_joined=$processOwner.StderrJoined;
                stdout_reader_closed=$processOwner.StdoutReaderClosed;stderr_reader_closed=$processOwner.StderrReaderClosed;
                stdout_writer_closed=$processOwner.StdoutWriterClosed;stderr_writer_closed=$processOwner.StderrWriterClosed;
                stdout_thread_closed=$processOwner.StdoutThreadClosed;stderr_thread_closed=$processOwner.StderrThreadClosed;
                stdout_overflow=$processOwner.StdoutOverflow;stderr_overflow=$processOwner.StderrOverflow;
                stdout_error=$processOwner.StdoutError;stderr_error=$processOwner.StderrError;fault=$processOwner.Fault;cleanup_error=$processOwner.CleanupError;
                peak_process=$processOwner.PeakProcessBytes;peak_job=$processOwner.PeakJobBytes;elapsed_seconds=(Elapsed)}
            $lBuildOperations.Add($fact)
            $closed=$true
            foreach($key in @('limits_verified','atomic_membership','resumed','reaped','job_empty','job_closed','process_closed','thread_closed','watchdog_joined','owned_nul_closed','stdout_eof','stderr_eof','stdout_joined','stderr_joined','stdout_reader_closed','stderr_reader_closed','stdout_writer_closed','stderr_writer_closed','stdout_thread_closed','stderr_thread_closed')){if($fact[$key] -isnot [bool] -or -not $fact[$key]){$closed=$false}}
            foreach($key in @('stdout_error','stderr_error','fault','cleanup_error')){if($null -ne $fact[$key]){$closed=$false}}
            if($fact.stdout_overflow -or $fact.stderr_overflow){$closed=$false}
            if(-not $closed){throw 'native compiler owned closure incomplete'}
            $output=$processOwner.StdoutBinary();$stderr=$processOwner.StderrText();$fact.stderr=$stderr
        }
    }
    if($null -ne $failure -or $exitCode -ne 0 -or $null -eq $output -or $output.Length -eq 0){throw ('native compiler failed: '+$purpose+'; '+$failure+'; '+$stderr)}
    return ,$output
}
function BuildLNative {
    $spec=$request.native_compiler
    if((($spec.Keys|Sort-Object) -join ',') -cne 'files,import_library,recipe,root' -or $spec.recipe -cne 'clang-cc1-closed-header-lld-stdout-v1'){throw 'native compiler closed recipe'}
    $bin=$spec.root
    RetainLAncestry ($projectRoot+'/tools/local_validation/l1/native_observer.c')
    $expected=@(Get-ChildItem -LiteralPath $bin -File -Filter '*.dll'|ForEach-Object {$_.FullName.Replace('\','/')})+@(($bin+'/clang.exe'),($bin+'/lld-link.exe'),($bin+'/llvm-objdump.exe'),$spec.import_library)
    if($expected.Count -gt 128 -or $expected.Count -ne $spec.files.Count -or @($expected|Where-Object {-not $spec.files.ContainsKey($_)}).Count){throw 'native toolchain exact files'}
    if(@(Get-ChildItem -LiteralPath $bin -File | Where-Object {$_.Name -match '^(clang|lld).*(\.cfg|\.json|\.manifest)$'}).Count){throw 'unexpected compiler configuration'}
    $total=0L
    foreach($row in $spec.files.GetEnumerator()){$total+=$row.Value.bytes;if($total -gt 2GB){throw 'native toolchain aggregate cap'};NativeToolPin $row.Key $row.Value}
    $oldEnvironment=@{}
    foreach($key in @('CL','_CL_','INCLUDE','LIB','LIBPATH','LLVM_PROFILE_FILE','CCC_OVERRIDE_OPTIONS','CLANG_CONFIG_FILE_SYSTEM_DIR','CLANG_CONFIG_FILE_USER_DIR','PATH')){$oldEnvironment[$key]=[Environment]::GetEnvironmentVariable($key);[Environment]::SetEnvironmentVariable($key,$null)}
    [Environment]::SetEnvironmentVariable('PATH','C:\Windows\System32')
    try{
        $result=@{}
        foreach($kind in @('observer','injection','target')){
            $source=if($kind -eq 'target'){'native_fixture.c'}else{'native_observer.c'}
            $args=@('-cc1','-triple','x86_64-pc-windows-msvc','-emit-obj','-O2','-fms-extensions','-fms-compatibility','-ffreestanding','-fno-builtin','-fno-autolink','-nostdsysteminc','-nobuiltininc','-o','-','-x','c')
            if($kind -eq 'injection'){$args+=@('-D','L1_FIXTURE=1')}
            $args+=($projectRoot+'/tools/local_validation/l1/'+$source)
            $object=RunLTool ($bin+'/clang.exe') $args ('compile-'+$kind)
            $objectRef=PublishLNative ('l-'+$kind+'-object_'+$operation+'.obj') $object ('l-'+$kind+'-object')
            $link=@('/dll','/entry:DllMain','/nodefaultlib','/machine:x64','/out:-','/noimplib','/dynamicbase','/nxcompat','/brepro','/opt:ref','/opt:icf','/threads:1',$objectRef.reference.path,$spec.import_library)
            $binary=RunLTool ($bin+'/lld-link.exe') $link ('link-'+$kind)
            if($binary.Length -lt 512 -or $binary[0] -ne 0x4d -or $binary[1] -ne 0x5a){throw 'native linker binary stdout PE'}
            $result[$kind]=PublishLNative ('l-'+$kind+'_'+$operation+'.dll') $binary ('l-'+$kind)
            if($kind -eq 'observer'){
                $assembly=RunLTool ($bin+'/llvm-objdump.exe') @('--disassemble','--disassemble-symbols=l1_notification','--reloc','--no-show-raw-insn',$objectRef.reference.path) 'inspect-callback'
                $text=[Text.UTF8Encoding]::new($false,$true).GetString($assembly)
                if($text -cnotmatch '<l1_notification>:' -or $text -match '(?im)\bcall[q]?\s|\b(memcpy|memmove|memset|__chkstk|__security_check_cookie)\b'){throw 'generated callback contains external call or missing body'}
                foreach($line in ($text -split "`n"|Where-Object {$_ -match 'IMAGE_REL_'})){
                    if($line -cnotmatch 'IMAGE_REL_AMD64_REL32\s+(\.bss|\.data|\.rdata|active_callbacks|started|stopped|fault_bits|produced|events|observer_generation)([-+].*)?\s*$'){throw 'callback unknown relocation target'}
                }
                $result.callback=PublishLNative ('l-callback_'+$operation+'.txt') $assembly 'l-callback-disassembly'
            }
        }
        foreach($item in $lToolInputs){VerifyLNativeItem $item}
        foreach($item in $lNativeArtifacts){VerifyLNativeItem $item}
        $bundle=@{schema='cho51_l_native_bundle_v1';operation_id=$operation;artifacts=$result;operations=$lBuildOperations.ToArray();production_exports=@('l1_start','l1_drain','l1_snapshot','l1_stop','l1_state');qualification_pending=$true;scientific_admission=$false}
        $raw=[Text.Encoding]::UTF8.GetBytes(($bundle|ConvertTo-Json -Depth 16 -Compress)+[Environment]::NewLine)
        return PublishLNative ('l-bundle_'+$operation+'.json') $raw 'l-native-bundle'
    }finally{foreach($key in $oldEnvironment.Keys){[Environment]::SetEnvironmentVariable($key,$oldEnvironment[$key])}}
}
