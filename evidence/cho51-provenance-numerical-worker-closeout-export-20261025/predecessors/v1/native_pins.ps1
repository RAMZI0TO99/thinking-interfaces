param()
$ErrorActionPreference = 'Stop'
if (-not (Get-Command ConvertFrom-Json).Parameters.ContainsKey('DateKind')) { throw 'Native pin preparation requires ConvertFrom-Json -DateKind String to preserve JSON timestamps' }
$FactoryRoot = 'D:\Aenv\pro3'
$FactoryPrevious = Join-Path $FactoryRoot 'runs\coordination\cho51_provenance_restore_20261025_v2\pins.json'
$FactoryPreviousSha = '4ba8504b7ff1f91f26cdfc721813de8f643c245ab738b04927ca1ee0be0c12dc'
if ((Get-FileHash -LiteralPath $FactoryPrevious -Algorithm SHA256).Hash.ToLowerInvariant() -ne $FactoryPreviousSha) { throw 'Historical pin inventory changed' }
$FactoryPreviousValue = Get-Content -LiteralPath $FactoryPrevious -Raw | ConvertFrom-Json -DateKind String
$FactoryGroups = [ordered]@{}
$FactoryChanges = @()
foreach ($FactoryGroup in @('runtime', 'runtime_modules', 'supporting_runtime_sources')) {
    $FactoryValues = [ordered]@{}
    foreach ($FactoryProperty in $FactoryPreviousValue.$FactoryGroup.PSObject.Properties) {
        $FactoryPath = $FactoryProperty.Name
        $FactoryBefore = Get-Item -LiteralPath $FactoryPath
        if ($FactoryBefore.PSIsContainer -or $FactoryBefore.FullName -ne $FactoryPath -or $FactoryBefore.Length -gt 536870912) { throw 'Direct bounded runtime file required' }
        $FactoryAncestor = $FactoryBefore
        while ($null -ne $FactoryAncestor) {
            if (($FactoryAncestor.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'Runtime reparse path refused' }
            $FactoryAncestor = if ($FactoryAncestor -is [System.IO.FileInfo]) { $FactoryAncestor.Directory } else { $FactoryAncestor.Parent }
        }
        $FactorySha = (Get-FileHash -LiteralPath $FactoryPath -Algorithm SHA256).Hash.ToLowerInvariant()
        $FactoryAfter = Get-Item -LiteralPath $FactoryPath
        if ($FactoryBefore.Length -ne $FactoryAfter.Length -or $FactoryBefore.LastWriteTimeUtc -ne $FactoryAfter.LastWriteTimeUtc -or $FactoryBefore.CreationTimeUtc -ne $FactoryAfter.CreationTimeUtc) { throw 'Runtime identity changed during native pinning' }
        $FactoryValues[$FactoryPath] = $FactorySha
        $FactoryChanges += [ordered]@{path=$FactoryPath; group=$FactoryGroup; historical_sha256=$FactoryProperty.Value; current_sha256=$FactorySha; changed=($FactorySha -ne $FactoryProperty.Value); bytes=$FactoryAfter.Length; product_version=$FactoryAfter.VersionInfo.ProductVersion}
    }
    $FactoryGroups[$FactoryGroup] = $FactoryValues
}
if ($FactoryGroups.runtime.Count -ne 5 -or $FactoryGroups.runtime_modules.Count -ne 18 -or $FactoryGroups.supporting_runtime_sources.Count -ne 4) { throw 'Exact fresh 5/18/4 runtime inventory required' }
$FactoryValue = [ordered]@{schema='cho51_provenance_numerical_worker_native_runtime_v1'; observed_utc=[DateTime]::UtcNow.ToString('o'); historical_pins_sha256=$FactoryPreviousSha; runtime=$FactoryGroups.runtime; runtime_modules=$FactoryGroups.runtime_modules; supporting_runtime_sources=$FactoryGroups.supporting_runtime_sources; transitions=$FactoryChanges; python_executed=$false; scientific_admission=$false}
$FactoryOutput = Join-Path $PSScriptRoot 'native-runtime.json'
$FactoryStream = [System.IO.File]::Open($FactoryOutput, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write, [System.IO.FileShare]::Read)
try {
    $FactoryWriter = [System.IO.StreamWriter]::new($FactoryStream, [System.Text.UTF8Encoding]::new($false))
    try { $FactoryWriter.WriteLine(($FactoryValue | ConvertTo-Json -Depth 12)); $FactoryWriter.Flush(); $FactoryStream.Flush($true) } finally { $FactoryWriter.Dispose() }
} finally { $FactoryStream.Dispose() }
[pscustomobject]@{path=$FactoryOutput; sha256=(Get-FileHash -LiteralPath $FactoryOutput -Algorithm SHA256).Hash.ToLowerInvariant(); changed_files=@($FactoryChanges | Where-Object changed).Count; python_executed=$false} | ConvertTo-Json
