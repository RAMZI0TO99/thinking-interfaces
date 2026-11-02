function ValidateQDRequest($request) {
    ClosedRecord $request @('schema','stage','operation_id','created_utc','expires_utc','root','python','runtime','caller_runtime','sources','review','adoption','predecessor','limits','modes','expected_tests','forbidden','scientific_admission','compiler','native_compiler','bootstrap_qualification','bootstrap_controls','purpose','stop_point','timing')
    foreach($key in @('schema','stage','purpose','stop_point','root')){if($request[$key] -isnot [string]){throw 'QD scalar authority identity'}}
    if($request.schema -cne 'cho51_startup_timing_admission_v1' -or $request.stage -cne 'QD' -or $request.purpose -cne 'QD_STARTUP_PREFIX_ONLY' -or $request.stop_point -cne 'BEFORE_MODE_LOOP' -or $request.scientific_admission -isnot [bool] -or $request.scientific_admission){throw 'closed QD-only authority'}
    if($request.operation_id -isnot [string] -or $request.operation_id -cnotmatch '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'){throw 'canonical QD operation'}
    $timing=$request.timing
    ClosedRecord $timing @('design_sha256','format_sha256','stages_sha256','caller_name','supervisor_name','records','record_bytes','journal_bytes','prefix_seconds','verification_seconds','publication_seconds')
    $expected=@{design_sha256='948eb50a0bc4176f9f07adc70e033304131ab3311f59487b9d84ce78425a7d68';format_sha256='4c46130c2d52395e6fd17a01ba8d8fa7c0e7a025dd10cc89cff4fa9161dcfd76';stages_sha256='ac449ef41d3c3537a4ebd3265262199d093be2f40454618525c9050651e38c38';caller_name='timing-caller_'+$request.operation_id+'.jsonl';supervisor_name='timing-supervisor_'+$request.operation_id+'.jsonl'}
    foreach($key in $expected.Keys){if($timing[$key] -isnot [string] -or $timing[$key] -cne $expected[$key]){throw 'QD timing identity'}}
    $numbers=@{records=128;record_bytes=512;journal_bytes=65536;prefix_seconds=45;verification_seconds=53;publication_seconds=55}
    foreach($key in $numbers.Keys){if(($timing[$key] -isnot [int] -and $timing[$key] -isnot [long]) -or $timing[$key] -ne $numbers[$key]){throw 'QD fixed timing cap'}}
    $names=@('fixed_supplied_case','closed_schema_and_types','fixed_selection','raw_pin_before_parse','historical_descriptor','full_page_and_index','strict_json','origin_is_not_custody','full_field_traversal','parent_identity','bom_crlf_null_spans','extra_node_changes_count','comparison_has_six_fields','distinct_observation_identities','semantics_stay_unresolved','conservation','forbidden_products','report_schema_is_not_state','safe_parser_refusal','source_and_node_bounds','encoder_bound','report_is_bounded','raw_assets_counted','guard_refusal','deterministic_immutable','self_certified_pin_refused','refusal_has_no_report','no_custody_grant','no_progress_state','exact_probe_roster','original_kernel_limit','all_authority_false')
    if($request.expected_tests -isnot [array] -or $request.expected_tests.Count -ne 32){throw 'QD retained exact probe roster'}
    for($i=0;$i -lt 32;$i++){$name='tools.local_validation.lplan15.test_compiler.SourceProbeTests.test_rs'+($i+1).ToString('00',[Globalization.CultureInfo]::InvariantCulture)+'_'+$names[$i];if($request.expected_tests[$i] -isnot [string] -or $request.expected_tests[$i] -cne $name){throw 'QD held probe identity'}}
    $arrays=@{modes=@('suite','native-transient','native-overflow','native-badreason','native-badutf16','native-pathbound','badframe','stall');forbidden=@('candidate_imports','third_party_imports','numerical_work','data_or_weights','network','git','unowned_processes','historical_launcher_replay');bootstrap_controls=@('accepted','bad_identity')}
    foreach($key in $arrays.Keys){$actual=$request[$key];$expected=$arrays[$key];if($actual -isnot [array] -or $actual.Count -ne $expected.Count){throw 'QD closed obligation/effect array'};for($i=0;$i -lt $expected.Count;$i++){if($actual[$i] -isnot [string] -or $actual[$i] -cne $expected[$i]){throw 'QD exact obligation/effect identity'}}}
    $limits=@{whole_seconds=90;work_seconds=60;cleanup_seconds=5;process_mib=512;job_mib=768;parent_mib=512;startup_ram_gib=4;active_ram_gib=4;disk_gib=20;frame_bytes=1048576;stream_bytes=1048576;threads=1;gpu_visible=$false}
    ClosedRecord $request.limits ([string[]]@($limits.Keys))
    foreach($key in $limits.Keys){$value=$request.limits[$key];if($key -ceq 'gpu_visible'){if($value -isnot [bool] -or $value){throw 'QD hidden GPU'}}elseif(($value -isnot [int] -and $value -isnot [long]) -or $value -ne $limits[$key]){throw 'QD exact unchanged resource scalar'}}
}
# This file is textually embedded in both reviewed callers, not independently
# executed from a pathname. Kept as the reviewed source comparison reference.
function LoadReviewedNativeBootstrap([string]$Role,[string]$Case='accepted') {
    $pin=PinBytes $Admission
    if($pin.sha256 -cne $AdmissionSha256 -or $pin.bytes -gt 1MB){throw 'bootstrap admission pin'}
    $request=ReadPinnedJson @{path=[IO.Path]::GetFullPath($Admission).Replace('\','/');bytes=$pin.bytes;sha256=$pin.sha256}
    if($Role -cnotin @('QD','P_Q_CONTROL')){throw 'QD-only bootstrap role; P disabled'}
    ValidateQDRequest $request
    $stage='QD'
    if($request.operation_id -cne $journal.operation -or $request.root -cne $projectRoot){throw 'bootstrap current stage authority'}
    AdmissionWindow $request.created_utc $request.expires_utc $originUtc
    $controls=@{}
    foreach($key in @('review','adoption')){
        $r=$request[$key];ClosedRecord $r @('path','bytes','sha256')
        $leaf=if($key -ceq 'review'){'source-review.json'}else{'contract-adoption.json'}
        $expected=if($stage -ceq 'P'){$phase.Replace('\','/')+'/'+$leaf}else{$leaf}
        $relative=if($stage -ceq 'P'){'runs/coordination/cho51_p3_startup_timing_20261101_p_disabled/'+$leaf}else{$leaf}
        if($r.path -cne $relative){throw 'bootstrap current review namespace'}
        $controls[$key]=ReadPinnedJson @{path=$phase.Replace('\','/')+'/'+$leaf;bytes=$r.bytes;sha256=$r.sha256}
    }
    $review=$controls.review;$adoption=$controls.adoption
    $status='ACCEPTED_SOURCE_QD1'
    if($review.status -cne $status -or $review.reviewer -isnot [string] -or $review.reviewer -cnotmatch '^[a-z][a-z0-9_-]{0,63}$' -or $review.authors -isnot [array] -or $review.authors.Count -lt 1 -or $review.authors -ccontains $review.reviewer -or $review.findings -isnot [array] -or $review.findings.Count -ne 0 -or $review.sources.Count -ne $request.sources.Count){throw 'bootstrap current independent source review'}
    foreach($row in $request.sources.GetEnumerator()){
        if(-not $review.sources.ContainsKey($row.Key) -or $review.sources[$row.Key].bytes -ne $row.Value.bytes -or $review.sources[$row.Key].sha256 -cne $row.Value.sha256){throw 'bootstrap current reviewed sources'}
    }
    $contract='docs/phase2/cho51_p3_qd_contract_20261101.md'
    if($adoption.author -cne 'project_root' -or $adoption.status -cne ('ADOPTED_'+$stage+'_ONLY') -or $adoption.source_review_sha256 -cne $request.review.sha256 -or $adoption.supplement_sha256 -cne $request.sources[$contract].sha256 -or $adoption.bootstrap_qualification_sha256 -cne $request.bootstrap_qualification.sha256){throw 'bootstrap current scoped adoption'}
    if((UtcString $review.created_utc) -gt (UtcString $adoption.created_utc) -or (UtcString $adoption.created_utc) -gt (UtcString $request.created_utc)){throw 'bootstrap current review/adoption order'}
    foreach($key in @('historical_custody_closed','historical_operation_released','historical_retry_allowed','restart_qualified','boundary_qualified','complete_dependency_closure','launch_authorized','scientific_admission')){if($adoption[$key] -isnot [bool] -or $adoption[$key]){throw 'bootstrap current scope expansion'}}
    $relative='tools/local_validation/lp18/native_bootstrap.ps1';$modulePin=$request.sources[$relative]
    $rawRef=@{path=$projectRoot+'/'+$relative;bytes=$modulePin.bytes;sha256=$modulePin.sha256}
    $pinned=PinBytes $rawRef.path
    if($pinned.bytes -ne $rawRef.bytes -or $pinned.sha256 -cne $rawRef.sha256 -or $pinned.bytes -gt 1MB){throw 'shared bootstrap exact reviewed module'}
    $stream=$inputs[$inputs.Count-1];$reader=[IO.StreamReader]::new($stream,[Text.UTF8Encoding]::new($false,$true),$false,65536,$true)
    try{$source=$reader.ReadToEnd()}finally{$reader.Dispose();$stream.Position=0}
    # The current independent review and Root adoption were checked before this
    # execution. Source strings are never accepted solely on an admission pin.
    . ([scriptblock]::Create($source))
    if($Role -cnotin @('QD','P_Q_CONTROL')){throw 'bootstrap role drift before native initialization'}
    $sampler=InitializeNativeBootstrap $request $Role $Case
    $script:NativeBootstrapGuardScript=$NativeBootstrapGuardScript
    return $sampler
}
