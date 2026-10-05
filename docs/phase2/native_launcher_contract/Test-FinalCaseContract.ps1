[CmdletBinding()]
param(
    [string]$ProjectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..')),
    [string]$PackageDirectory,
    [string]$ReceiptPath
)

# Evaluate only the actual source predicate. Never dot-source or invoke a
# complete launcher, numerical process, recorder or Job.
$ErrorActionPreference = 'Stop'
$taskRoot = [IO.Path]::GetFullPath($ProjectRoot)
if (-not $PackageDirectory) {
    $PackageDirectory = Join-Path $taskRoot 'runs/coordination/first_case_supervision_20261005_v11'
}
$taskPackage = [IO.Path]::GetFullPath($PackageDirectory)
if (-not $ReceiptPath) { $ReceiptPath = Join-Path $taskPackage 'final_case_contract_test_001.json' }
$taskReceipt = [IO.Path]::GetFullPath($ReceiptPath)
if (-not $taskReceipt.StartsWith($taskPackage.TrimEnd('\') + '\', [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Receipt must be inside the successor package'
}
if (Test-Path -LiteralPath $taskReceipt) { throw 'Receipt already exists; no overwrite allowed' }
function Get-TaskSha([string]$Path) { return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() }
$taskBuildPath = Join-Path $taskPackage 'v11_build_provenance.json'
$taskBuild = [IO.File]::ReadAllText($taskBuildPath) | ConvertFrom-Json
if ($taskBuild.schema -cne 'pro3_first_case_v11_template_build_v1' -or $taskBuild.artifacts.Count -ne 6 -or
    $taskBuild.release_created -ne $false -or $taskBuild.live_source_verified -ne $false) {
    throw 'Expected an unadmitted six-file historical-baseline template'
}
$taskSource = Join-Path $taskRoot $taskBuild.source_package
foreach ($taskArtifact in $taskBuild.artifacts) {
    if ((Get-TaskSha (Join-Path $taskSource $taskArtifact.file)) -cne $taskArtifact.before_sha256 -or
        (Get-TaskSha (Join-Path $taskPackage $taskArtifact.file)) -cne $taskArtifact.after_sha256) {
        throw "Frozen input or generated package differs: $($taskArtifact.file)"
    }
}
function Get-TaskActualPredicate([string]$Path) {
    $taskTokens = $null; $taskErrors = $null
    $taskAst = [Management.Automation.Language.Parser]::ParseFile($Path, [ref]$taskTokens, [ref]$taskErrors)
    if ($taskErrors.Count -ne 0) { throw "PowerShell parse errors: $Path" }
    $taskMatches = @($taskAst.FindAll({
        param($taskNode)
        $taskNode -is [Management.Automation.Language.IfStatementAst] -and
        $taskNode.Extent.Text.StartsWith('if ($taskChildResult.result.case.dataset', [StringComparison]::Ordinal) -and
        $taskNode.Extent.Text.Contains("throw 'Fixed first-case result differs'")
    }, $true))
    if ($taskMatches.Count -ne 1 -or $taskMatches[0].Clauses.Count -ne 1 -or $null -ne $taskMatches[0].ElseClause) {
        throw 'Expected exactly the single fixed-case check with no else clause'
    }
    # Evaluate the AST's condition alone, rather than any branch or surrounding
    # statement. Its source is bound to the byte-verified package above.
    $taskCondition = $taskMatches[0].Clauses[0].Item1.Extent.Text
    return [pscustomobject]@{
        line = $taskMatches[0].Extent.StartLineNumber
        condition = $taskCondition
        block = [scriptblock]::Create($taskCondition)
    }
}
$taskOldLauncher = Join-Path $taskSource 'Invoke-FirstCaseSupervisorV1.ps1'
$taskNewLauncher = Join-Path $taskPackage 'Invoke-FirstCaseSupervisorV1.ps1'
$taskOld = Get-TaskActualPredicate $taskOldLauncher
$taskNew = Get-TaskActualPredicate $taskNewLauncher
if (-not $taskOld.condition.Contains('.completion.measured_cases') -or
    -not $taskNew.condition.Contains('.completion.measured') -or $taskNew.condition.Contains('measured_cases')) {
    throw 'Expected exact recorded field-name correction'
}
if ($taskOld.condition.Replace('.completion.measured_cases', '.completion.measured') -cne $taskNew.condition) {
    throw 'Case-check condition contains an undocumented semantic change'
}
$taskFixturePath = Join-Path $taskRoot 'runs/phase2/first_case_supervision/execcase62536382c003/child_result.json'
$taskFixtureSha = Get-TaskSha $taskFixturePath
if ($taskFixtureSha -cne 'bf949893c2605afec9a68e05b3052429f369323b377d1a807e881ea0b88b4311') {
    throw 'Accepted historical c003 fixture bytes differ'
}
$taskFixtureRaw = [IO.File]::ReadAllText($taskFixturePath)
function Get-TaskFreshFixture { return ($taskFixtureRaw | ConvertFrom-Json) }
function Invoke-TaskCheck($Predicate, $Payload) {
    $taskChildResult = $Payload
    return (-not [bool](& $Predicate.block))
}
$taskCases = @()
$taskCases += [pscustomobject]@{ id = 'historical_c003_success'; payload = Get-TaskFreshFixture; expected = $true }
$taskCases += [pscustomobject]@{ id = 'malformed_null_result'; payload = Get-TaskFreshFixture; expected = $false }
$taskCases[-1].payload.result = $null
$taskCases += [pscustomobject]@{ id = 'malformed_string_result'; payload = Get-TaskFreshFixture; expected = $false }
$taskCases[-1].payload.result = 'malformed'
$taskCases += [pscustomobject]@{ id = 'missing_measured'; payload = Get-TaskFreshFixture; expected = $false }
$taskCases[-1].payload.result.completion.PSObject.Properties.Remove('measured')
foreach ($taskValue in @(0, 2, 'malformed')) {
    $taskPayload = Get-TaskFreshFixture
    $taskPayload.result.completion.measured = $taskValue
    $taskCases += [pscustomobject]@{ id = "measured_$taskValue"; payload = $taskPayload; expected = $false }
}
$taskPayload = Get-TaskFreshFixture
$taskPayload.result.completion.PSObject.Properties.Remove('measured')
$taskPayload.result.completion | Add-Member -NotePropertyName measured_cases -NotePropertyValue 1
$taskCases += [pscustomobject]@{ id = 'legacy_field_only'; payload = $taskPayload; expected = $false }
foreach ($taskField in @('dataset', 'method', 'target_subject', 'model_seed', 'shots_per_class', 'repetition')) {
    $taskPayload = Get-TaskFreshFixture
    $taskPayload.result.case.$taskField = if ($taskField -in @('model_seed', 'shots_per_class', 'repetition')) { 999 } else { 'incorrect' }
    $taskCases += [pscustomobject]@{ id = "incorrect_$taskField"; payload = $taskPayload; expected = $false }
}
$taskChecks = @()
$taskOldActual = Invoke-TaskCheck $taskOld (Get-TaskFreshFixture)
$taskChecks += [pscustomobject]@{ id = 'historical_v10_reproduces_rejection'; expected_acceptance = $false; actual_acceptance = $taskOldActual; passed = ($taskOldActual -eq $false) }
foreach ($taskCase in $taskCases) {
    $taskActual = Invoke-TaskCheck $taskNew $taskCase.payload
    $taskChecks += [pscustomobject]@{ id = $taskCase.id; expected_acceptance = $taskCase.expected; actual_acceptance = $taskActual; passed = ($taskActual -eq $taskCase.expected) }
}
if (@($taskChecks | Where-Object { -not $_.passed }).Count -ne 0) { throw 'Extracted predicate contract regression failed' }
foreach ($taskArtifact in $taskBuild.artifacts) {
    if ((Get-TaskSha (Join-Path $taskSource $taskArtifact.file)) -cne $taskArtifact.before_sha256 -or
        (Get-TaskSha (Join-Path $taskPackage $taskArtifact.file)) -cne $taskArtifact.after_sha256) {
        throw "Input/package changed during checks: $($taskArtifact.file)"
    }
}
if ((Get-TaskSha $taskFixturePath) -cne $taskFixtureSha) { throw 'Historical fixture changed during checks' }
$taskResult = [ordered]@{
    schema = 'pro3_native_final_case_contract_regression_v1'
    utc = [DateTimeOffset]::UtcNow.ToString('o')
    decision = 'PASS_EXTRACTED_PREDICATE_ONLY'
    scope = 'AST-extracted actual rejection conditions; no whole-launcher or live-case acceptance'
    validator_sha256 = Get-TaskSha $PSCommandPath
    build_provenance_sha256 = Get-TaskSha $taskBuildPath
    fixture_sha256 = $taskFixtureSha
    old_launcher_sha256 = Get-TaskSha $taskOldLauncher
    new_launcher_sha256 = Get-TaskSha $taskNewLauncher
    old_predicate = [ordered]@{ line = $taskOld.line; condition = $taskOld.condition }
    new_predicate = [ordered]@{ line = $taskNew.line; condition = $taskNew.condition }
    checks = $taskChecks; checks_passed = $taskChecks.Count
    frozen_artifacts_unchanged = $true; historical_fixture_unchanged = $true
    whole_launcher_invoked = $false; python_invoked = $false; job_created = $false
    training_invoked = $false; recorder_modified = $false; release_created = $false
    live_source_verified = $false; scientific_claims_made = 0
    gate_a_signed = $false; scientific_freeze_ratified = $false
}
[IO.File]::WriteAllText($taskReceipt, ($taskResult | ConvertTo-Json -Depth 16) + "`n", [Text.UTF8Encoding]::new($false))
[pscustomobject]@{ decision = $taskResult.decision; checks_passed = $taskChecks.Count; receipt_path = $taskReceipt } | ConvertTo-Json
