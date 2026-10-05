[CmdletBinding()]
param(
    [string]$ProjectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..')),
    [Parameter(Mandatory = $true)][ValidateNotNullOrEmpty()][string]$PackageDirectory,
    [Parameter(Mandatory = $true)][ValidateNotNullOrEmpty()][string]$OutputPath
)

# This runner evaluates only a byte-bound AST rejection expression with inert
# JSON objects. It does not invoke/dot-source the launcher or Python parent.
# Running even these small fixtures requires the root's separate scoped slot.
$ErrorActionPreference = 'Stop'
$taskRoot = [IO.Path]::GetFullPath($ProjectRoot)
$taskCoordination = [IO.Path]::GetFullPath((Join-Path $taskRoot 'runs/coordination'))
$taskPackage = [IO.Path]::GetFullPath($PackageDirectory)
$taskOutput = [IO.Path]::GetFullPath($OutputPath)
$taskChecks = [Collections.Generic.List[object]]::new()
$taskExpectedCaseId = 'af0f24764e577f2223db4759582852aacc2b1b2b0b0a549f1d4b43f8f14998b5'
$taskExpectedFiles = @('Invoke-FirstCaseSupervisorV1.ps1', 'Prepare-FirstCaseRuntimeV1.ps1',
    'parent.py', 'child.py', 'design.json')
$taskFrozenSha = @{
    'Invoke-FirstCaseSupervisorV1.ps1' = '72e03974ac7140e0d823d1c9165dd0d81928b456efbdaed5ea48615fcd06dd8b'
    'Prepare-FirstCaseRuntimeV1.ps1' = 'b7f95393740186d3db1a79a7af4445fd877b6ae8e5c6772a084b6572539cf3a7'
    'parent.py' = '67889194aa04b7f83aaf9dcea3ff3532be701098931d41cc93f0bb69ae62b430'
    'child.py' = '80fa45115ba3809db5b4eda8bef3b400e214656050eb38612ae8d909941444eb'
    'design.json' = '79dc609e7bc111376ea69dbb3cd715fc91c35779620e0ae4424be88eeab648ec'
}

function Get-TaskShaBytes([byte[]]$Bytes) {
    $taskHash = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($taskHash.ComputeHash($Bytes))).Replace('-', '').ToLowerInvariant() }
    finally { $taskHash.Dispose() }
}

function Assert-TaskOrdinaryPath([string]$Path, [string]$Under, [bool]$MustExist) {
    $taskAbsolute = [IO.Path]::GetFullPath($Path)
    if ($Under -and -not $taskAbsolute.StartsWith($Under.TrimEnd('\') + '\',
            [StringComparison]::OrdinalIgnoreCase)) { throw 'Path is outside the specified ordinary directory' }
    if ($MustExist -and -not (Test-Path -LiteralPath $taskAbsolute)) { throw "Missing required path: $taskAbsolute" }
    $taskCursor = $taskAbsolute
    while ($taskCursor) {
        if (Test-Path -LiteralPath $taskCursor) {
            $taskItem = Get-Item -LiteralPath $taskCursor -Force
            if ($taskItem.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Linked paths are refused' }
        }
        $taskNext = [IO.Path]::GetDirectoryName($taskCursor)
        if ($taskNext -eq $taskCursor) { break }
        $taskCursor = $taskNext
    }
    return $taskAbsolute
}

function Read-TaskRegularBytes([string]$Path, [long]$Maximum = 2097152) {
    [void](Assert-TaskOrdinaryPath $Path $taskRoot $true)
    $taskBefore = Get-Item -LiteralPath $Path -Force
    if ($taskBefore.PSIsContainer -or $taskBefore.Length -le 0 -or $taskBefore.Length -gt $Maximum) {
        throw "Bounded nonempty regular file required: $Path"
    }
    $taskStream = [IO.File]::Open($Path, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::Read)
    try {
        if ($taskStream.Length -ne $taskBefore.Length) { throw 'File length changed before read' }
        $taskBytes = [byte[]]::new([int]$taskBefore.Length)
        $taskOffset = 0
        while ($taskOffset -lt $taskBytes.Length) {
            $taskRead = $taskStream.Read($taskBytes, $taskOffset, $taskBytes.Length - $taskOffset)
            if ($taskRead -eq 0) { throw 'File truncated during read' }
            $taskOffset += $taskRead
        }
        if ($taskStream.ReadByte() -ne -1) { throw 'File grew during read' }
    } finally { $taskStream.Dispose() }
    $taskAfter = Get-Item -LiteralPath $Path -Force
    if ($taskAfter.Length -ne $taskBefore.Length -or
        $taskAfter.LastWriteTimeUtc.Ticks -ne $taskBefore.LastWriteTimeUtc.Ticks) { throw 'File changed during read' }
    return ,$taskBytes
}

function Add-TaskCheck([string]$Id, [string]$Scope, [bool]$Passed, $Details) {
    $taskChecks.Add([pscustomobject]@{ id = $Id; scope = $Scope; passed = $Passed; details = $Details })
}

function Assert-TaskText([string]$Text, [string]$Needle, [string]$Id, [int]$Count = 1) {
    # Literal snippets may be authored with LF; the full forward/reverse proof
    # above separately binds every original line-ending byte.
    $taskFound = [regex]::Matches($Text.Replace("`r`n", "`n"), [regex]::Escape($Needle.Replace("`r`n", "`n"))).Count
    Add-TaskCheck $Id 'byte_bound_source_consistency' ($taskFound -eq $Count) @{ expected_count = $Count; actual_count = $taskFound }
}

function Get-TaskNativeAst([string]$Path) {
    $taskTokens = $null; $taskErrors = $null
    $taskAst = [Management.Automation.Language.Parser]::ParseFile($Path, [ref]$taskTokens, [ref]$taskErrors)
    if ($taskErrors.Count -ne 0) { throw "PowerShell parse errors: $Path" }
    return $taskAst
}

function Get-TaskFunctionText($Ast, [string]$Name) {
    $taskMatches = @($Ast.FindAll({
        param($taskNode)
        $taskNode -is [Management.Automation.Language.FunctionDefinitionAst] -and $taskNode.Name -ceq $Name
    }, $true))
    if ($taskMatches.Count -ne 1) { throw "Expected exactly one native function: $Name" }
    return $taskMatches[0].Extent.Text
}

function Get-TaskPythonRegion([string]$Text, [string]$Name) {
    $taskPattern = '(?ms)^def ' + [regex]::Escape($Name) + '\(.*?(?=^def |^class |\z)'
    $taskMatches = [regex]::Matches($Text, $taskPattern)
    if ($taskMatches.Count -ne 1) { throw "Expected one top-level source region: $Name" }
    return $taskMatches[0].Value
}

[void](Assert-TaskOrdinaryPath $taskRoot $null $true)
if (-not (Get-Item -LiteralPath $taskRoot -Force).PSIsContainer) { throw 'ProjectRoot must be an ordinary directory' }
[void](Assert-TaskOrdinaryPath $taskPackage $taskCoordination $true)
if (-not (Get-Item -LiteralPath $taskPackage -Force).PSIsContainer -or
    [IO.Path]::GetDirectoryName($taskPackage.TrimEnd('\')) -ine $taskCoordination -or
    [IO.Path]::GetFileName($taskPackage.TrimEnd('\')) -cnotmatch '^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$') {
    throw 'PackageDirectory must be a direct ordinary child of runs/coordination'
}
[void](Assert-TaskOrdinaryPath $taskOutput $taskCoordination $false)
if (Test-Path -LiteralPath $taskOutput) { throw 'OutputPath already exists; preserve spent fixtures' }
$taskOutputParent = [IO.Path]::GetDirectoryName($taskOutput)
[void](Assert-TaskOrdinaryPath $taskOutputParent $taskRoot $true)
if (-not (Get-Item -LiteralPath $taskOutputParent -Force).PSIsContainer -or
    [IO.Path]::GetFileName($taskOutput) -cnotmatch '^[A-Za-z0-9][A-Za-z0-9_.-]{0,119}\.json$') {
    throw 'Existing ordinary parent and fresh ASCII .json output basename required'
}
$taskUtf8 = [Text.UTF8Encoding]::new($false, $true)
$taskLatin1 = [Text.Encoding]::GetEncoding(28591)
$taskIgnoreText = $taskUtf8.GetString((Read-TaskRegularBytes (Join-Path $taskRoot '.gitignore') 65536))
if ($taskIgnoreText -cnotmatch '(?m)^runs/\r?$' -or $taskIgnoreText -cmatch '(?m)^!runs(?:/|$)') {
    throw 'Root Git ignore contract for runs/ is absent or explicitly negated'
}

$taskProvenancePath = Join-Path $taskPackage 'package_build_provenance.json'
$taskProvenanceBytes = Read-TaskRegularBytes $taskProvenancePath
$taskProvenanceSha = Get-TaskShaBytes $taskProvenanceBytes
$taskBuild = $taskUtf8.GetString($taskProvenanceBytes) | ConvertFrom-Json
if ($taskBuild.schema -cne 'pro3_labram_linear_package_build_v1' -or
    $taskBuild.state -cne 'prospective_labram_linear_package_only_no_execution_release' -or
    $taskBuild.release_created -isnot [bool] -or $taskBuild.release_created -or
    $taskBuild.launcher_invoked -isnot [bool] -or $taskBuild.launcher_invoked -or
    $taskBuild.python_invoked -isnot [bool] -or $taskBuild.python_invoked -or
    $taskBuild.training_invoked -isnot [bool] -or $taskBuild.training_invoked -or
    $taskBuild.live_source_verified -isnot [bool] -or $taskBuild.live_source_verified -or
    $taskBuild.runtime_record_copied -isnot [bool] -or $taskBuild.runtime_record_copied -or
    $taskBuild.runtime_measured -isnot [bool] -or $taskBuild.runtime_measured -or
    $taskBuild.environment_measured -isnot [bool] -or $taskBuild.environment_measured -or
    $taskBuild.checkpoint_pretraining_cohort_verified -isnot [bool] -or $taskBuild.checkpoint_pretraining_cohort_verified -or
    $taskBuild.gate_a_signed -isnot [bool] -or $taskBuild.gate_a_signed -or
    $taskBuild.scientific_freeze_ratified -isnot [bool] -or $taskBuild.scientific_freeze_ratified -or
    $taskBuild.scientific_claims_made -ne 0 -or
    $taskBuild.source_package -cne 'runs/coordination/first_case_supervision_20261004_v10') {
    throw 'Expected unadmitted prospective package with preserved V10 input provenance'
}
$taskFiles = @($taskBuild.artifacts | ForEach-Object { $_.file })
if ($taskFiles.Count -ne 5 -or @($taskFiles | Select-Object -Unique).Count -ne 5 -or
    @($taskExpectedFiles | Where-Object { $_ -cnotin $taskFiles }).Count -ne 0) { throw 'Exactly the five named operational artifacts are required' }
$taskSource = Join-Path $taskRoot $taskBuild.source_package
$taskSourceImages = @{}; $taskPackageImages = @{}
foreach ($taskArtifact in $taskBuild.artifacts) {
    if ($taskArtifact.before_sha256 -cne $taskFrozenSha[$taskArtifact.file] -or
        $taskArtifact.after_sha256 -cnotmatch '^[0-9a-f]{64}$') { throw 'Explicit lower-case artifact hashes required' }
    $taskBeforeBytes = Read-TaskRegularBytes (Join-Path $taskSource $taskArtifact.file)
    $taskAfterBytes = Read-TaskRegularBytes (Join-Path $taskPackage $taskArtifact.file)
    if ((Get-TaskShaBytes $taskBeforeBytes) -cne $taskArtifact.before_sha256 -or
        (Get-TaskShaBytes $taskAfterBytes) -cne $taskArtifact.after_sha256 -or
        $taskBeforeBytes.Length -ne $taskArtifact.before_bytes -or $taskAfterBytes.Length -ne $taskArtifact.after_bytes) {
        throw "Byte-bound artifact differs: $($taskArtifact.file)"
    }
    $taskSourceImages[$taskArtifact.file] = $taskLatin1.GetString($taskBeforeBytes)
    $taskPackageImages[$taskArtifact.file] = $taskLatin1.GetString($taskAfterBytes)
    $taskForward = $taskSourceImages[$taskArtifact.file]
    $taskChanges = @($taskBuild.replacements | Where-Object { $_.file -ceq $taskArtifact.file })
    foreach ($taskChange in $taskChanges) {
        if ([string]::IsNullOrEmpty($taskChange.old) -or [string]::IsNullOrEmpty($taskChange.new) -or
            $taskChange.old -ceq $taskChange.new -or $taskChange.expected_count -lt 1 -or
            $taskChange.actual_count -ne $taskChange.expected_count -or
            [regex]::Matches($taskForward, [regex]::Escape($taskChange.old)).Count -ne $taskChange.expected_count) {
            throw 'Malformed or unreproducible declared replacement'
        }
        $taskForward = $taskForward.Replace($taskChange.old, $taskChange.new)
    }
    if ($taskForward -cne $taskPackageImages[$taskArtifact.file]) { throw 'Declared replacements do not reconstruct generated bytes' }
    $taskReverse = $taskPackageImages[$taskArtifact.file]
    for ($taskIndex = $taskChanges.Count - 1; $taskIndex -ge 0; $taskIndex--) {
        $taskChange = $taskChanges[$taskIndex]
        if ([regex]::Matches($taskReverse, [regex]::Escape($taskChange.new)).Count -ne $taskChange.expected_count) {
            throw 'Declared reverse replacement count differs'
        }
        $taskReverse = $taskReverse.Replace($taskChange.new, $taskChange.old)
    }
    if ($taskReverse -cne $taskSourceImages[$taskArtifact.file] -or
        $taskChanges.Count -ne $taskArtifact.replacement_count -or
        $taskArtifact.reverse_substitution_reproduces_original_bytes -isnot [bool] -or
        -not $taskArtifact.reverse_substitution_reproduces_original_bytes) { throw 'Inverse byte proof differs' }
    Add-TaskCheck "reversible_bytes_$($taskArtifact.file)" 'byte_bound_source_consistency' $true @{ replacements = $taskChanges.Count }
}

$taskBinding = $taskBuild.binding
if ($taskBinding.source_sha256 -cnotmatch '^[0-9a-f]{64}$' -or
    $taskBinding.source_sha256 -ceq '62536382eb85a7626d6d45b110b688dbb374281d136733e75cf77301a4c77cf0' -or
    ($taskBinding.source_file_count -isnot [int] -and $taskBinding.source_file_count -isnot [long]) -or
    $taskBinding.source_file_count -le 0 -or $taskBinding.deadline_utc -cnotmatch '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$' -or
    $taskBinding.peer_thread -cnotmatch '^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}$' -or
    $taskBinding.peer_thread -ceq '01a0f844-b0d8-79a0-89d7-a823ce1b8962' -or
    $taskBinding.case_id -cne $taskExpectedCaseId -or $taskBinding.worker -cne 'cho-labram-linear-20261005-v1') {
    throw 'Explicit source, count, UTC deadline, peer and fresh worker binding required'
}
$taskDeadline = [DateTimeOffset]::ParseExact($taskBinding.deadline_utc, "yyyy-MM-dd'T'HH:mm:ss'Z'",
    [Globalization.CultureInfo]::InvariantCulture, [Globalization.DateTimeStyles]::AssumeUniversal)
# Independent native reconstruction of config_digest(asdict(CasePlan)): sorted
# ASCII keys, compact JSON, UTF-8 without BOM or newline. No Python is invoked.
$taskSortedCase = [ordered]@{ dataset = 'cho2017'; method = 'labram_linear'; model_seed = 11;
    repetition = 1; shots_per_class = 5; target_subject = 'subject_01' }
$taskCanonicalCaseJson = $taskSortedCase | ConvertTo-Json -Compress
$taskNativeCaseId = Get-TaskShaBytes ($taskUtf8.GetBytes($taskCanonicalCaseJson))
Add-TaskCheck 'native_caseplan_id' 'executed_native_json_and_hash' ($taskNativeCaseId -ceq $taskExpectedCaseId) @{
    canonical_json = $taskCanonicalCaseJson; actual_sha256 = $taskNativeCaseId; expected_sha256 = $taskExpectedCaseId
}
if (@($taskBinding.case.PSObject.Properties).Count -ne 6) { throw 'Binding case must have exactly six CasePlan fields' }
foreach ($taskField in $taskSortedCase.Keys) {
    $taskActualField = $taskBinding.case.$taskField
    $taskTypeMatches = if ($taskSortedCase[$taskField] -is [string]) { $taskActualField -is [string] }
        else { $taskActualField -is [int] -or $taskActualField -is [long] }
    if (-not $taskTypeMatches -or $taskActualField -cne $taskSortedCase[$taskField]) { throw "Case binding differs: $taskField" }
}
$taskDesign = $taskPackageImages['design.json'] | ConvertFrom-Json
foreach ($taskField in $taskSortedCase.Keys) {
    Add-TaskCheck "design_case_$taskField" 'byte_bound_source_consistency' ($taskDesign.first_case.$taskField -ceq $taskSortedCase[$taskField]) $taskDesign.first_case.$taskField
}
Add-TaskCheck 'design_source_count_deadline' 'byte_bound_source_consistency' (
    $taskDesign.source_sha256 -ceq $taskBinding.source_sha256 -and
    $taskDesign.source_file_count -eq $taskBinding.source_file_count -and
    $taskDesign.global_deadline_utc -ceq $taskBinding.deadline_utc -and
    $taskDesign.first_case.case_id -ceq $taskExpectedCaseId) $null
Add-TaskCheck 'design_runtime_measurements_pending' 'byte_bound_source_consistency' (
    $null -eq $taskDesign.runtime_schema.file_count_native_observed -and
    $null -eq $taskDesign.runtime_schema.selected_native_digest -and
    $taskDesign.runtime_and_environment_measured_for_this_package -is [bool] -and
    -not $taskDesign.runtime_and_environment_measured_for_this_package -and
    $taskDesign.execution_release_created -is [bool] -and -not $taskDesign.execution_release_created -and
    $taskDesign.checkpoint_pretraining_cohort_verified -is [bool] -and -not $taskDesign.checkpoint_pretraining_cohort_verified) $null
$taskParent = $taskPackageImages['parent.py']; $taskChild = $taskPackageImages['child.py']
$taskLauncher = $taskPackageImages['Invoke-FirstCaseSupervisorV1.ps1']
$taskDeadlinePython = 'GLOBAL_DEADLINE = datetime(' + (@($taskDeadline.Year, $taskDeadline.Month,
    $taskDeadline.Day, $taskDeadline.Hour, $taskDeadline.Minute, $taskDeadline.Second) -join ', ') + ', tzinfo=UTC)'
Assert-TaskText $taskParent ('EXPECTED_SOURCE = "' + $taskBinding.source_sha256 + '"') 'parent_source'
Assert-TaskText $taskParent ('EXPECTED_SOURCE_FILE_COUNT = ' + $taskBinding.source_file_count) 'parent_source_count'
Assert-TaskText $taskParent ('CASE_ID = "' + $taskExpectedCaseId + '"') 'parent_case_id'
Assert-TaskText $taskParent '"method": "labram_linear"' 'parent_canonical_method'
Assert-TaskText $taskParent $taskDeadlinePython 'parent_deadline'
Assert-TaskText $taskParent ('"peer_thread": "' + $taskBinding.peer_thread + '"') 'parent_fresh_peer'
Assert-TaskText $taskLauncher ('$taskExpectedSource = ''' + $taskBinding.source_sha256 + '''') 'launcher_source'
Assert-TaskText $taskLauncher ('$taskExpectedSourceCount = ' + $taskBinding.source_file_count) 'launcher_source_count'
Assert-TaskText $taskLauncher ('$taskGlobalEnd = [DateTimeOffset]::Parse(''' + $taskBinding.deadline_utc + ''')') 'launcher_deadline'
Assert-TaskText $taskLauncher ('$taskRelease.peer_thread -cne ''' + $taskBinding.peer_thread + '''') 'launcher_fresh_peer'
Assert-TaskText $taskChild 'plan = CasePlan("cho2017", "subject_01", "labram_linear", 5, 11, 1)' 'child_caseplan'
Assert-TaskText $taskChild '"""Fixed no-fit environment probe or LaBraM linear CLI inside verified outer Job."""' 'child_accurate_method_docstring'
Add-TaskCheck 'child_no_stale_eegnet_docstring' 'byte_bound_source_consistency' (
    -not $taskChild.Contains('Fixed no-fit environment probe or first EEGNet CLI inside verified outer Job.')) $null
Assert-TaskText $taskChild ('"--method",' + "`n" + '                            "labram_linear",') 'child_cli_method'
Assert-TaskText $taskChild ('"--worker",' + "`n" + '                            "' + $taskBinding.worker + '",') 'child_fresh_worker'
Assert-TaskText $taskChild 'len(provenance.source_files(ROOT)) != ops.EXPECTED_SOURCE_FILE_COUNT' 'child_source_file_count_measurement'
$taskDesignPeer = @($taskDesign.release_schema.required_equalities | Where-Object { $_ -clike 'peer_thread=*' })
Add-TaskCheck 'design_fresh_peer' 'byte_bound_source_consistency' (
    $taskDesignPeer.Count -eq 1 -and $taskDesignPeer[0] -ceq ('peer_thread=' + $taskBinding.peer_thread)) $taskDesignPeer

# Adapter and native helper regions must remain byte-identical to frozen V10.
# These checks inspect source regions; they do not measure native Job behavior.
foreach ($taskName in @('install_job_adapter', 'runtime_pin')) {
    Add-TaskCheck "preserved_python_region_$taskName" 'byte_bound_source_consistency' (
        (Get-TaskPythonRegion $taskParent $taskName) -ceq
        (Get-TaskPythonRegion $taskSourceImages['parent.py'] $taskName)) $null
}
$taskAst = Get-TaskNativeAst (Join-Path $taskPackage 'Invoke-FirstCaseSupervisorV1.ps1')
$taskOldAst = Get-TaskNativeAst (Join-Path $taskSource 'Invoke-FirstCaseSupervisorV1.ps1')
foreach ($taskName in @('Get-TaskDirectPath', 'Read-TaskPinnedJson', 'Write-TaskOnce',
        'ConvertTo-TaskWin32Argument', 'Get-TaskResourceSample')) {
    Add-TaskCheck "preserved_native_function_$taskName" 'byte_bound_ast_consistency' (
        (Get-TaskFunctionText $taskAst $taskName) -ceq (Get-TaskFunctionText $taskOldAst $taskName)) $null
}
foreach ($taskText in @('$taskProcessLimit = 6442450944L', '$taskAggregateLimit = 8053063680L',
        '$taskStartupRam = 10737418240L', '$taskActiveRam = 4294967296L', '$taskDiskFloor = 21474836480L',
        '$taskOuterSeconds = if ($Mode -ceq ''execute'') { 600 } else { 120 }', '$taskCleanupReserve = 5',
        '$taskProcess.Kill() # Exact owned parent only; its noninherited Job closes with it.',
        '$taskInfo.RedirectStandardOutput = $true', '$taskInfo.RedirectStandardError = $true')) {
    Assert-TaskText $taskLauncher $taskText ('preserved_launcher_guard_' + $taskChecks.Count)
}
foreach ($taskText in @('MEMORY_LIMIT_BYTES = 6 * GIB', 'AGGREGATE_LIMIT_BYTES = 15 * GIB // 2',
        'CLEANUP_RESERVE_SECONDS = 20', 'deadline = min(started_utc + timedelta(seconds=cap), options.window_end, GLOBAL_DEADLINE)',
        'floor=primitive.ResourceFloor(disk_bytes=20 * GIB, ram_bytes=4 * GIB)',
        'process_memory_limit_bytes=MEMORY_LIMIT_BYTES')) {
    Assert-TaskText $taskParent $taskText ('preserved_parent_guard_' + $taskChecks.Count)
}
$taskExpectedPreparer = $taskSourceImages['Prepare-FirstCaseRuntimeV1.ps1'].Replace(
    '62536382eb85a7626d6d45b110b688dbb374281d136733e75cf77301a4c77cf0', $taskBinding.source_sha256)
$taskDeclaredPreparerSource = 'source_sha256 = ''' + $taskBinding.source_sha256 + ''''
$taskExpectedPreparer = $taskExpectedPreparer.Replace($taskDeclaredPreparerSource,
    $taskDeclaredPreparerSource + "`n" + '    source_file_count = ' + $taskBinding.source_file_count + "`n" +
    '    source_binding_is_declared_not_measured = $true')
Add-TaskCheck 'runtime_preparer_only_declared_source_binding_changes' 'byte_bound_source_consistency' (
    $taskPackageImages['Prepare-FirstCaseRuntimeV1.ps1'] -ceq $taskExpectedPreparer) $null
Add-TaskCheck 'no_copied_historical_runtime_acceptance' 'byte_bound_package_inventory' (
    @((Get-ChildItem -LiteralPath $taskPackage -File -Force) | Where-Object {
        $_.Name -cmatch '(?i)^(runtime_preparation_|release|environment_preparation|completion|receipt|child_result)'
    }).Count -eq 0) $null

# Locate the final rejection statement in the generated launcher, not a replica
# of it. A direct one-statement throw body distinguishes it from enclosing ifs.
$taskMatches = @($taskAst.FindAll({
    param($taskNode)
    if ($taskNode -isnot [Management.Automation.Language.IfStatementAst] -or
        $taskNode.Clauses.Count -ne 1 -or $null -ne $taskNode.ElseClause) { return $false }
    $taskBody = $taskNode.Clauses[0].Item2.Statements
    return ($taskBody.Count -eq 1 -and $taskBody[0] -is [Management.Automation.Language.ThrowStatementAst] -and
        $taskBody[0].Extent.Text -ceq "throw 'Fixed first-case result differs'")
}, $true))
if ($taskMatches.Count -ne 1) { throw 'Exactly one actual fixed-case rejection predicate is required' }
$taskConditionAst = $taskMatches[0].Clauses[0].Item1
$taskCondition = $taskConditionAst.Extent.Text
if ($taskCondition.Length -gt 12288 -or -not $taskCondition.Contains('$taskChildResult.result.case')) { throw 'Bounded final-case expression required' }
$taskUnsafe = @($taskConditionAst.FindAll({
    param($taskNode)
    return ($taskNode -is [Management.Automation.Language.CommandAst] -or
        $taskNode -is [Management.Automation.Language.InvokeMemberExpressionAst] -or
        $taskNode -is [Management.Automation.Language.AssignmentStatementAst] -or
        $taskNode -is [Management.Automation.Language.ScriptBlockExpressionAst] -or
        $taskNode -is [Management.Automation.Language.SubExpressionAst] -or
        ($taskNode -is [Management.Automation.Language.VariableExpressionAst] -and
            $taskNode.VariablePath.UserPath -cnotin @('taskChildResult', 'null', 'true', 'false')))
}, $true))
if ($taskUnsafe.Count -ne 0) { throw 'Predicate contains a command, call, assignment, scriptblock or external variable' }
$taskPredicate = [scriptblock]::Create($taskCondition)
$taskBaseJson = '{"schema":"pro3_first_case_child_v1","mode":"execute","engineering_cell_count":1,"result":{"case":{"dataset":"cho2017","target_subject":"subject_01","method":"labram_linear","shots_per_class":5,"model_seed":11,"repetition":1},"completion":{"measured":1}}}'
$taskFixtures = [Collections.Generic.List[object]]::new()
$taskFixtures.Add([pscustomobject]@{ id = 'exact_labram_case_integer_one'; json = $taskBaseJson; expected = $true })
foreach ($taskField in @('dataset', 'target_subject', 'method')) {
    $taskOldValue = [string]$taskSortedCase[$taskField]
    $taskWrong = if ($taskField -ceq 'method') { 'eegnet' } else { 'incorrect' }
    $taskFixtures.Add([pscustomobject]@{ id = "wrong_$taskField";
        json = $taskBaseJson.Replace(('"' + $taskField + '":"' + $taskOldValue + '"'), ('"' + $taskField + '":"' + $taskWrong + '"')); expected = $false })
    $taskFixtures.Add([pscustomobject]@{ id = "array_$taskField";
        json = $taskBaseJson.Replace(('"' + $taskField + '":"' + $taskOldValue + '"'), ('"' + $taskField + '":["' + $taskOldValue + '"]')); expected = $false })
}
foreach ($taskField in @('model_seed', 'shots_per_class', 'repetition', 'measured')) {
    $taskExpectedNumber = if ($taskField -ceq 'measured') { 1 } else { $taskSortedCase[$taskField] }
    foreach ($taskValue in @('0', '2', '999', 'null', '"1"', 'true', '1.0', '"malformed"', '[1]', '{}')) {
        # Repetition/measured 2 rejects; shots/seed 2 also rejects. The string1,
        # Boolean and float fixtures must preserve JSON types through parsing.
        $taskFixtures.Add([pscustomobject]@{ id = "${taskField}_$taskValue";
            json = $taskBaseJson.Replace(('"' + $taskField + '":' + $taskExpectedNumber), ('"' + $taskField + '":' + $taskValue)); expected = $false })
    }
    if ($taskExpectedNumber -ne 1) {
        $taskFixtures.Add([pscustomobject]@{ id = "${taskField}_numeric_string_expected";
            json = $taskBaseJson.Replace(('"' + $taskField + '":' + $taskExpectedNumber), ('"' + $taskField + '":"' + $taskExpectedNumber + '"')); expected = $false })
        $taskFixtures.Add([pscustomobject]@{ id = "${taskField}_float_expected_value";
            json = $taskBaseJson.Replace(('"' + $taskField + '":' + $taskExpectedNumber), ('"' + $taskField + '":' + $taskExpectedNumber + '.0')); expected = $false })
    }
}
foreach ($taskField in $taskSortedCase.Keys) {
    $taskPayload = $taskBaseJson | ConvertFrom-Json
    $taskPayload.result.case.PSObject.Properties.Remove($taskField)
    $taskFixtures.Add([pscustomobject]@{ id = "missing_case_$taskField";
        json = ($taskPayload | ConvertTo-Json -Depth 12 -Compress); expected = $false })
}
$taskFixtures.Add([pscustomobject]@{ id = 'missing_measured'; json = $taskBaseJson.Replace('"measured":1', '"other":1'); expected = $false })
$taskFixtures.Add([pscustomobject]@{ id = 'legacy_measured_cases_only'; json = $taskBaseJson.Replace('"measured":1', '"measured_cases":1'); expected = $false })
$taskFixtures.Add([pscustomobject]@{ id = 'extra_case_field'; json = $taskBaseJson.Replace('"dataset":"cho2017"', '"extra":1,"dataset":"cho2017"'); expected = $false })
foreach ($taskShape in @('null', '"malformed"', '[]', 'true')) {
    foreach ($taskField in @('result', 'case', 'completion')) {
        $taskPayload = $taskBaseJson | ConvertFrom-Json
        $taskOriginalValue = if ($taskField -ceq 'result') { $taskPayload.result }
            else { $taskPayload.result.$taskField }
        $taskOriginalJson = $taskOriginalValue | ConvertTo-Json -Depth 12 -Compress
        $taskOriginalField = '"' + $taskField + '":' + $taskOriginalJson
        if ([regex]::Matches($taskBaseJson, [regex]::Escape($taskOriginalField)).Count -ne 1) {
            throw 'Malformed-container fixture must replace exactly one JSON field'
        }
        # Replace serialized text before parsing, so [] remains an actual empty
        # JSON array rather than being unrolled to null by a PowerShell pipeline.
        $taskFixtures.Add([pscustomobject]@{ id = "malformed_${taskField}_$taskShape";
            json = $taskBaseJson.Replace($taskOriginalField, ('"' + $taskField + '":' + $taskShape)); expected = $false })
    }
}
foreach ($taskFixture in $taskFixtures) {
    $taskChildResult = $taskFixture.json | ConvertFrom-Json
    $taskFixtureError = $null; $taskActual = $false
    try {
        $taskReturn = @(& $taskPredicate)
        if ($taskReturn.Count -ne 1 -or $taskReturn[0] -isnot [bool]) { throw 'Rejection predicate must emit exactly one Boolean' }
        $taskActual = -not $taskReturn[0]
    } catch { $taskFixtureError = $_.Exception.Message }
    Add-TaskCheck $taskFixture.id 'executed_ast_predicate_native_json_fixture' (
        $taskActual -eq $taskFixture.expected -and $null -eq $taskFixtureError) @{
        expected_acceptance = $taskFixture.expected; actual_acceptance = $taskActual;
        exception = $taskFixtureError; fixture_json_sha256 = Get-TaskShaBytes ($taskUtf8.GetBytes($taskFixture.json))
    }
}

# The real parent writes nonempty status/completion JSON on success. Preserve
# its producer and the launcher's capture. This is a byte check, not Python or
# whole-launcher interoperability execution; that prospective test is deferred.
$taskSuccessPrint = 'print(json.dumps({"status": completion["status"], "completion": str(out / "completion.json")}))'
Assert-TaskText $taskParent $taskSuccessPrint 'parent_actual_nonempty_success_stdout_producer'
Assert-TaskText $taskSourceImages['parent.py'] $taskSuccessPrint 'historical_success_stdout_producer'
Assert-TaskText $taskLauncher '[IO.File]::WriteAllText((Join-Path $taskLaunchPath ''parent_stdout.log''),$taskStdout.Result,(New-Object Text.UTF8Encoding($false)))' 'launcher_actual_stdout_capture'

foreach ($taskArtifact in $taskBuild.artifacts) {
    if ((Get-TaskShaBytes (Read-TaskRegularBytes (Join-Path $taskSource $taskArtifact.file))) -cne $taskArtifact.before_sha256 -or
        (Get-TaskShaBytes (Read-TaskRegularBytes (Join-Path $taskPackage $taskArtifact.file))) -cne $taskArtifact.after_sha256) {
        throw 'Frozen input or generated artifact changed during fixtures'
    }
}
if ((Get-TaskShaBytes (Read-TaskRegularBytes $taskProvenancePath)) -cne $taskProvenanceSha) { throw 'Build provenance changed during fixtures' }
$taskFailures = @($taskChecks | Where-Object { -not $_.passed })
$taskDecision = if ($taskFailures.Count -eq 0) { 'PASS_PACKAGE_BYTES_AST_AND_EXTRACTED_PREDICATE_ONLY' } else { 'FAIL_PACKAGE_CONTRACT' }
$taskResult = [ordered]@{
    schema = 'pro3_labram_linear_package_contract_regression_v1'; utc = [DateTimeOffset]::UtcNow.ToString('o')
    decision = $taskDecision; validator_sha256 = Get-TaskShaBytes (Read-TaskRegularBytes $PSCommandPath)
    package_directory = $taskPackage; build_provenance_sha256 = $taskProvenanceSha; binding = $taskBinding
    native_caseplan_id = $taskNativeCaseId; canonical_case_json = $taskCanonicalCaseJson
    actual_launcher_predicate = [ordered]@{ line = $taskMatches[0].Extent.StartLineNumber; condition = $taskCondition }
    checks = @($taskChecks.ToArray()); checks_passed = $taskChecks.Count - $taskFailures.Count; checks_failed = $taskFailures.Count
    executed_predicate_fixture_count = $taskFixtures.Count
    byte_ast_checks_do_not_prove_runtime_behavior = $true; historical_inputs_unchanged = $true; package_unchanged = $true
    live_source_verified = $false; fresh_environment_or_controls_verified = $false; release_created = $false
    parent_success_stdout_producer_checked_by_source_only = $true; whole_launcher_stdout_interop_executed = $false
    deferred = @('Whole parent/native launcher success and failure interoperability, including real nonempty stdout',
        'Fresh current source, quality, controls, raw and measured environment prerequisites',
        'One-use execution release, resource admission, actual LaBraM engineering case and physical cleanup')
    launcher_invoked = $false; python_invoked = $false; job_created = $false; training_invoked = $false
    gate_a_signed = $false; scientific_freeze_ratified = $false; scientific_claims_made = 0
}
[void](Assert-TaskOrdinaryPath $taskOutput $taskCoordination $false)
$taskResultBytes = $taskUtf8.GetBytes(($taskResult | ConvertTo-Json -Depth 24) + "`n")
$taskFile = [IO.File]::Open($taskOutput, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::Read)
try { $taskFile.Write($taskResultBytes, 0, $taskResultBytes.Length); $taskFile.Flush($true) }
finally { $taskFile.Dispose() }
[pscustomobject]@{ decision = $taskDecision; checks_passed = $taskResult.checks_passed;
    checks_failed = $taskResult.checks_failed; executed_predicate_fixtures = $taskFixtures.Count; output_path = $taskOutput } | ConvertTo-Json
if ($taskFailures.Count -ne 0) { throw 'Package contract regression failed; fresh failure receipt preserved' }
