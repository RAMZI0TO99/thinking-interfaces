# Definitions loaded only after current Q authority and the exact source pin.
function RunBootstrapControls {
    $result=[Collections.Generic.List[object]]::new()
    foreach($case in @('accepted','bad_identity')){
        Check;if((Elapsed) -ge 55){throw 'insufficient enclosing Q work for bootstrap control'}
        $root=$phase.Replace('\','/')+'/bootstrap-controls/'+$operation+'/'+$case
        if([IO.Directory]::Exists($root) -or [IO.File]::Exists($root)){throw 'consumed bootstrap control directory'}
        [void][IO.Directory]::CreateDirectory($root)
        $cache=@('AppData','AppData/Local','AppData/Local/Microsoft','AppData/Local/Microsoft/PowerShell')
        foreach($relative in $cache){[void][IO.Directory]::CreateDirectory($root+'/'+$relative)}
        foreach($path in @($root)+@($cache|ForEach-Object {$root+'/'+$_})){
            $directory=[IO.DirectoryInfo]::new($path)
            while($null -ne $directory){$attributes=[IO.File]::GetAttributes($directory.FullName);if(($attributes -band [IO.FileAttributes]::ReparsePoint) -or -not($attributes -band [IO.FileAttributes]::Directory)){throw 'bootstrap control plain ancestry'};$directory=$directory.Parent}
        }
        $environment=@{SystemRoot='C:/Windows';WINDIR='C:/Windows';PATH=$PSHOME.Replace('\','/')+';C:/Windows/System32';HOME=$root;USERPROFILE=$root;TEMP=$root;TMP=$root;OMP_NUM_THREADS='1';MKL_NUM_THREADS='1';OPENBLAS_NUM_THREADS='1';CUDA_VISIBLE_DEVICES='-1';PYTEST_DISABLE_PLUGIN_AUTOLOAD='1';DOTNET_MultiCoreJitNoProfileGather='1'}
        $probe=[QNative.Owner]::new($originQpc,$originUtc.ToString('o'),$stopPath)
        $exit=$null;$stdout='';$stderr='';$state=$null
        try {
            $arguments=@('-NoLogo','-NoProfile','-NonInteractive','-File',($projectRoot+'/tools/local_validation/lq6/bootstrap_probe.ps1'),'-Admission',$Admission,'-AdmissionSha256',$AdmissionSha256,'-Case',$case,'-EnclosingUtc',$originUtc.ToString('o'),'-EnclosingQpc',[string]$originQpc,'-EnclosingFrequency',[string]$frequency)
            $saved=[Environment]::GetEnvironmentVariables('Process')
            try {
                foreach($key in $saved.Keys){[Environment]::SetEnvironmentVariable([string]$key,$null,'Process')}
                foreach($key in $environment.Keys){[Environment]::SetEnvironmentVariable($key,$environment[$key],'Process')}
                Check;$probe.Start($callerProcess.MainModule.FileName,[string[]]$arguments,$projectRoot)
            }finally{
                foreach($key in [Environment]::GetEnvironmentVariables('Process').Keys){[Environment]::SetEnvironmentVariable([string]$key,$null,'Process')}
                foreach($key in $saved.Keys){[Environment]::SetEnvironmentVariable([string]$key,[string]$saved[$key],'Process')}
            }
            while(-not $probe.Poll()){Check;[Threading.Thread]::Sleep(25)}
            $exit=$probe.ExitCode()
        }finally {
            $probe.Dispose();$state=OwnerState $probe
            if($probe.StdoutJoined -and $probe.StdoutEof){$stdout=$probe.StdoutText()}
            if($probe.StderrJoined -and $probe.StderrEof){$stderr=$probe.StderrText()}
            $result.Add(@{case=$case;exit_code=$exit;stdout=$stdout;stderr=$stderr;outer_custody=$state;validated=$false})
            $script:bootstrapControls=$result.ToArray()
        }
        foreach($key in @('limits_verified','atomic_membership','resumed','job_empty','job_closed','process_closed','thread_closed','reaped','watchdog_joined','owned_nul_closed','stdout_eof','stderr_eof','stdout_reader_closed','stderr_reader_closed','stdout_writer_closed','stderr_writer_closed','stdout_reader_thread_handle_closed','stderr_reader_thread_handle_closed','stdout_reader_joined','stderr_reader_joined')){if($state[$key] -isnot [bool] -or -not $state[$key]){throw ('bootstrap control outer custody '+$key)}}
        if($exit -ne 0 -or $stderr -or $state.stdout_overflow -or $state.stderr_overflow -or $null -ne $state.fault -or $null -ne $state.cleanup_error){throw 'bootstrap control external failure'}
        $receipt=StrictJson $stdout
        if($receipt.schema -cne 'cho51_lp4_bootstrap_control_v1' -or $receipt.operation_id -cne $operation -or $receipt.case -cne $case -or $receipt.role -cne 'P_BOOTSTRAP_Q_CONTROL' -or $receipt.expected_outcome_observed -isnot [bool] -or -not $receipt.expected_outcome_observed -or $receipt.original_streams_closed -isnot [bool] -or -not $receipt.original_streams_closed -or $receipt.journal_closed -isnot [bool] -or -not $receipt.journal_closed -or $receipt.source_bootstrap_sha256 -cne $request.sources['tools/local_validation/lp6/native_bootstrap.ps1'].sha256 -or $receipt.enclosing_utc -cne $originUtc.ToString('o') -or $receipt.enclosing_qpc -ne $originQpc -or $receipt.enclosing_frequency -ne $frequency -or $receipt.elapsed_seconds -ge 5){throw 'bootstrap control exact receipt'}
        if($case -ceq 'accepted'){
            if(-not $receipt.accepted -or -not $receipt.helper_loaded -or -not $receipt.final_input_verification -or $null -ne $receipt.error -or -not $receipt.guard.ready -or -not $receipt.guard.done -or -not $receipt.guard.joined -or -not $receipt.guard.closed -or -not $receipt.guard.completion_wait_closed -or $null -ne $receipt.guard.error -or $receipt.sampler_custody.creation_attempted -or -not $receipt.sampler_custody.job_empty -or -not $receipt.sampler_custody.job_closed -or -not $receipt.sampler_custody.watchdog_joined -or $null -ne $receipt.sampler_custody.fault -or $null -ne $receipt.sampler_custody.cleanup_error){throw 'positive shared P bootstrap evidence'}
        }else{
            if($receipt.accepted -or $receipt.helper_loaded -or -not $receipt.refused_before_load -or $null -ne $receipt.sampler_custody -or $receipt.guard.ready -or $receipt.error -notlike '*bootstrap expected native identity mismatch*'){throw 'bad identity did not refuse before helper load'}
        }
        # Exact finite plain cache layout; no shared profile/caches are reused.
        $expectedFiles=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal);[void]$expectedFiles.Add('bootstrap.jsonl')
        $expectedDirs=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal);foreach($relative in $cache){[void]$expectedDirs.Add($relative)}
        $pending=[Collections.Generic.Stack[string]]::new();$pending.Push($root);$count=0
        while($pending.Count){foreach($entry in [IO.Directory]::EnumerateFileSystemEntries($pending.Pop())){Check;$count++;if($count -gt 5){throw 'bootstrap control census cap'};$full=$entry.Replace('\','/');$relative=$full.Substring($root.Length+1);$attributes=[IO.File]::GetAttributes($entry);if($attributes -band [IO.FileAttributes]::ReparsePoint){throw 'bootstrap control reparse'};if($attributes -band [IO.FileAttributes]::Directory){if(-not $expectedDirs.Remove($relative)){throw 'bootstrap control unknown directory'};$pending.Push($full)}elseif(-not $expectedFiles.Remove($relative)){throw 'bootstrap control unknown file'}}}
        if($expectedDirs.Count -or $expectedFiles.Count -or $receipt.journal_path -cne $root+'/bootstrap.jsonl'){throw 'bootstrap control output census'}
        $journalPin=PinBytes ($root+'/bootstrap.jsonl');$result[$result.Count-1].journal=@{path=$root+'/bootstrap.jsonl';bytes=$journalPin.bytes;sha256=$journalPin.sha256;native_identity=[PNative.Owner]::FileIdentity($inputs[$inputs.Count-1].SafeFileHandle)}
        $result[$result.Count-1].receipt=$receipt;$result[$result.Count-1].validated=$true
        $script:bootstrapControls=$result.ToArray()
    }
    return ,$result.ToArray()
}
