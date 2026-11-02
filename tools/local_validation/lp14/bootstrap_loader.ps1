# This file is textually embedded in both reviewed callers, not independently
# executed from a pathname. Kept as the reviewed source comparison reference.
function LoadReviewedNativeBootstrap([string]$Role,[string]$Case='accepted') {
    $pin=PinBytes $Admission
    if($pin.sha256 -cne $AdmissionSha256 -or $pin.bytes -gt 1MB){throw 'bootstrap admission pin'}
    $request=ReadPinnedJson @{path=[IO.Path]::GetFullPath($Admission).Replace('\','/');bytes=$pin.bytes;sha256=$pin.sha256}
    $keys=if($Role -ceq 'P'){@('schema','stage','operation_id','created_utc','expires_utc','root','python','runtime','caller_runtime','sources','review','adoption','qualification','native_helper','map_index','coverage_review','extra_paths','limits','forbidden','scientific_admission','api_mapping','native_diagnostic','l_native_bundle','plan_spec','bootstrap_qualification','qualification_aggregate')}else{@('schema','stage','operation_id','created_utc','expires_utc','root','python','runtime','caller_runtime','sources','review','adoption','predecessor','limits','modes','expected_tests','forbidden','scientific_admission','compiler','native_compiler','bootstrap_qualification','bootstrap_controls')}
    ClosedRecord $request $keys
    $stage=if($Role -ceq 'P'){'P'}else{'Q'}
    if($request.schema -cne $(if($stage -ceq 'P'){'cho51_resolver_p_admission_v1'}else{'cho51_q_admission_v1'}) -or $request.stage -cne $stage -or $request.operation_id -cne $journal.operation -or $request.root -cne $projectRoot -or $request.scientific_admission -isnot [bool] -or $request.scientific_admission){throw 'bootstrap current stage authority'}
    AdmissionWindow $request.created_utc $request.expires_utc $originUtc
    $controls=@{}
    foreach($key in @('review','adoption')){
        $r=$request[$key];ClosedRecord $r @('path','bytes','sha256')
        $leaf=if($key -ceq 'review'){'source-review.json'}else{'contract-adoption.json'}
        $expected=if($stage -ceq 'P'){$phase.Replace('\','/')+'/'+$leaf}else{$leaf}
        $relative=if($stage -ceq 'P'){'runs/coordination/cho51_p3_probe_20261101_p1/'+$leaf}else{$leaf}
        if($r.path -cne $relative){throw 'bootstrap current review namespace'}
        $controls[$key]=ReadPinnedJson @{path=$phase.Replace('\','/')+'/'+$leaf;bytes=$r.bytes;sha256=$r.sha256}
    }
    $review=$controls.review;$adoption=$controls.adoption
    $status=if($stage -ceq 'P'){'ACCEPTED_SOURCE_LP1'}else{'ACCEPTED_SOURCE_LQ1'}
    if($review.status -cne $status -or $review.reviewer -isnot [string] -or $review.reviewer -cnotmatch '^[a-z][a-z0-9_-]{0,63}$' -or $review.authors -isnot [array] -or $review.authors.Count -lt 1 -or $review.authors -ccontains $review.reviewer -or $review.findings -isnot [array] -or $review.findings.Count -ne 0 -or $review.sources.Count -ne $request.sources.Count){throw 'bootstrap current independent source review'}
    foreach($row in $request.sources.GetEnumerator()){
        if(-not $review.sources.ContainsKey($row.Key) -or $review.sources[$row.Key].bytes -ne $row.Value.bytes -or $review.sources[$row.Key].sha256 -cne $row.Value.sha256){throw 'bootstrap current reviewed sources'}
    }
    $contract='docs/phase2/cho51_p3_probe_contract_20261101.md'
    if($adoption.author -cne 'project_root' -or $adoption.status -cne ('ADOPTED_'+$stage+'_ONLY') -or $adoption.source_review_sha256 -cne $request.review.sha256 -or $adoption.supplement_sha256 -cne $request.sources[$contract].sha256 -or $adoption.bootstrap_qualification_sha256 -cne $request.bootstrap_qualification.sha256){throw 'bootstrap current scoped adoption'}
    if((UtcString $review.created_utc) -gt (UtcString $adoption.created_utc) -or (UtcString $adoption.created_utc) -gt (UtcString $request.created_utc)){throw 'bootstrap current review/adoption order'}
    foreach($key in @('historical_custody_closed','historical_operation_released','historical_retry_allowed','restart_qualified','boundary_qualified','complete_dependency_closure','launch_authorized','scientific_admission')){if($adoption[$key] -isnot [bool] -or $adoption[$key]){throw 'bootstrap current scope expansion'}}
    if($stage -ceq 'P'){
        # Both accepted Q cohorts are prerequisites even for the P native bootstrap.
        function EqualTree($a,$b){
            if($a -is [Collections.IDictionary]){
                if($b -isnot [Collections.IDictionary] -or $a.Count -ne $b.Count){return $false}
                foreach($k in $a.Keys){if(-not(@($b.Keys) -ccontains $k) -or -not(EqualTree $a[$k] $b[$k])){return $false}}
                return $true
            }
            if($a -is [array]){
                if($b -isnot [array] -or $a.Count -ne $b.Count){return $false}
                for($i=0;$i -lt $a.Count;$i++){if(-not(EqualTree $a[$i] $b[$i])){return $false}}
                return $true
            }
            if($null -eq $a){return ($null -eq $b)}
            if($a -is [bool]){return ($b -is [bool] -and $a -eq $b)}
            if($a -is [string]){return ($b -is [string] -and $a -ceq $b)}
            return ($b -isnot [bool] -and $a -eq $b)
        }
        $qPhase='runs/coordination/cho51_p3_probe_20261101_q1/'
        $ar=$request.qualification_aggregate
        ClosedRecord $ar @('path','bytes','sha256')
        if($ar.path -cne ($qPhase+'qualification-aggregate.json') -or $adoption.qualification_aggregate_sha256 -cne $ar.sha256){throw 'both Q aggregate adoption'}
        $aggregate=ReadPinnedJson @{path=$projectRoot+'/'+$ar.path;bytes=$ar.bytes;sha256=$ar.sha256}
        $refs=@('source_review','primary_qualification','primary_admission','primary_actual','secondary_qualification','secondary_admission','secondary_actual')
        ClosedRecord $aggregate (@('schema','status','author','created_utc','expected_counts','launch_authorized','scientific_admission')+$refs)
        if($aggregate.schema -cne 'cho51_resolver_q_aggregate_v1' -or $aggregate.status -cne 'ACCEPTED_BOTH_Q_COHORTS' -or $aggregate.author -cne 'project_root' -or -not(EqualTree $aggregate.expected_counts @{inherited=384;resolver=40})){throw 'both Q aggregate status/counts'}
        foreach($flag in @('launch_authorized','scientific_admission')){if($aggregate[$flag] -isnot [bool] -or $aggregate[$flag]){throw 'aggregate scope'}}
        $fixed=@{source_review='source-review.json';primary_qualification='root-qualification.json';primary_actual='actual-review.json';secondary_qualification='resolver-qualification.json';secondary_actual='resolver-actual-review.json'}
        $docs=@{}
        foreach($key in $refs){
            $r=$aggregate[$key];ClosedRecord $r @('path','bytes','sha256')
            if($fixed.ContainsKey($key)){if($r.path -cne ($qPhase+$fixed[$key])){throw 'aggregate fixed reference'}}
            elseif($r.path -cnotmatch ('^'+[regex]::Escape($qPhase)+'admission_[0-9a-f-]{36}\.json$')){throw 'aggregate admission namespace'}
            $docs[$key]=ReadPinnedJson @{path=$projectRoot+'/'+$r.path;bytes=$r.bytes;sha256=$r.sha256}
        }
        if(-not(EqualTree $aggregate.primary_qualification $request.qualification) -or -not(EqualTree $docs.source_review.sources $request.sources) -or $docs.source_review.status -cne 'ACCEPTED_SOURCE_LQ1'){throw 'aggregate primary/current source join'}
        $operations=@()
        foreach($cohortRole in @('primary','secondary')){
            $count=if($cohortRole -ceq 'primary'){384}else{40}
            $q=$docs[$cohortRole+'_qualification'];$a=$docs[$cohortRole+'_actual'];$qa=$docs[$cohortRole+'_admission']
            $operations+=,$q.operation_id
            if($q.status -cne 'QUALIFIED_LQ1_MECHANISMS_ONLY' -or $q.author -cne 'project_root' -or $a.status -cne 'ACCEPTED_LQ1_TESTED_SCOPE' -or $a.reviewer -ceq $docs.source_review.reviewer -or $a.authors -ccontains $a.reviewer -or $docs.source_review.authors -ccontains $a.reviewer -or $a.findings.Count -ne 0 -or $docs.source_review.findings.Count -ne 0){throw 'aggregate independent accepted reviews'}
            if($qa.operation_id -cne $q.operation_id -or $a.operation_id -cne $q.operation_id -or $qa.stage -cne 'Q' -or $qa.schema -cne 'cho51_q_admission_v1' -or $aggregate[$cohortRole+'_admission'].path -cne ($qPhase+'admission_'+$q.operation_id+'.json')){throw 'aggregate distinct admitted cohort'}
            if(-not(EqualTree $q.source_review $aggregate.source_review) -or -not(EqualTree $q.actual_review $aggregate[$cohortRole+'_actual']) -or -not(EqualTree $a.admission $aggregate[$cohortRole+'_admission']) -or $a.source_review_sha256 -cne $aggregate.source_review.sha256){throw 'aggregate review reference join'}
            foreach($field in @('sources','runtime','caller_runtime','python','root')){if(-not(EqualTree $qa[$field] $request[$field])){throw 'aggregate current source/runtime identity'}}
            $seen=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
            if($qa.expected_tests -isnot [array] -or $qa.expected_tests.Count -ne $count){throw 'aggregate complete cohort count'}
            foreach($name in $qa.expected_tests){if($name -isnot [string] -or -not $seen.Add($name) -or $name.StartsWith('tools.local_validation.lplan11.test_compiler.ResolverTests.',[StringComparison]::Ordinal) -ne ($cohortRole -ceq 'secondary')){throw 'aggregate cohort partition'}}
            $rosterBytes=[Text.Encoding]::UTF8.GetBytes((ConvertTo-Json -InputObject $qa.expected_tests -Compress -Depth 5))
            if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($rosterBytes)).ToLowerInvariant() -cne $a.test_roster_sha256 -or $q.test_count -ne $count -or $a.tests_run -ne $count -or $a.actual_tool_exit_code -ne 0){throw 'aggregate actual exact tests'}
            foreach($field in @('new_operation_owned_lifecycle_closed','final_input_verification')){if($a[$field] -isnot [bool] -or -not $a[$field]){throw 'aggregate verified cleanup'}}
            foreach($field in @('historical_custody_closed','historical_operation_released','historical_retry_allowed','restart_qualified','boundary_qualified','complete_dependency_closure','launch_authorized','scientific_admission')){if($q[$field] -isnot [bool] -or $q[$field] -or $a[$field] -isnot [bool] -or $a[$field]){throw 'aggregate no authority expansion'}}
            if($q.timestamp_controls -ne 8 -or $q.native_fault_controls -ne 2 -or $a.timestamp_controls_passed -ne 8 -or $a.native_fault_controls_passed -ne 2){throw 'aggregate all controls'}
            foreach($field in @('native_helper','native_builder_controls','api_mapping','api_mapping_native_identity','native_diagnostic','native_diagnostic_native_identity','artifact_handoff','sharing_controls','l_native_bundle','l_native_bundle_identity','l_native_cases','bootstrap_controls')){if(-not(EqualTree $q[$field] $a[$field])){throw 'aggregate native actual join'}}
            if((UtcString $docs.source_review.created_utc) -gt (UtcString $qa.created_utc) -or (UtcString $qa.created_utc) -gt (UtcString $a.created_utc) -or (UtcString $a.created_utc) -gt (UtcString $q.created_utc) -or (UtcString $q.created_utc) -gt (UtcString $aggregate.created_utc) -or (UtcString $aggregate.created_utc) -gt (UtcString $request.created_utc)){throw 'aggregate authority order'}
        }
        if($operations[0] -ceq $operations[1]){throw 'aggregate repeated operation'}
        foreach($field in @('compiler','native_compiler')){if(-not(EqualTree $docs.primary_admission[$field] $docs.secondary_admission[$field])){throw 'aggregate compiler roles'}}
    }
    $relative='tools/local_validation/lp14/native_bootstrap.ps1';$modulePin=$request.sources[$relative]
    $rawRef=@{path=$projectRoot+'/'+$relative;bytes=$modulePin.bytes;sha256=$modulePin.sha256}
    $pinned=PinBytes $rawRef.path
    if($pinned.bytes -ne $rawRef.bytes -or $pinned.sha256 -cne $rawRef.sha256 -or $pinned.bytes -gt 1MB){throw 'shared bootstrap exact reviewed module'}
    $stream=$inputs[$inputs.Count-1];$reader=[IO.StreamReader]::new($stream,[Text.UTF8Encoding]::new($false,$true),$false,65536,$true)
    try{$source=$reader.ReadToEnd()}finally{$reader.Dispose();$stream.Position=0}
    # The current independent review and Root adoption were checked before this
    # execution. Source strings are never accepted solely on an admission pin.
    . ([scriptblock]::Create($source))
    if($Role -cne $stage){throw 'bootstrap role drift before native initialization'}
    $sampler=InitializeNativeBootstrap $request $Role $Case
    $script:NativeBootstrapGuardScript=$NativeBootstrapGuardScript
    return $sampler
}
