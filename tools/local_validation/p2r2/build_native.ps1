# Dot-sourced only by the separately admitted Q caller from verified bytes.
# Emits a bounded managed PE in memory; caller owns create-new publication.
function Build-PNative([byte[]]$source, $compiler, [scriptblock]$checkpoint) {
    & $checkpoint
    if($source.Length -gt 1MB){throw 'native source cap'}
    $trees=[Microsoft.CodeAnalysis.SyntaxTree[]]@(
        [Microsoft.CodeAnalysis.CSharp.CSharpSyntaxTree]::ParseText(
            [Text.Encoding]::UTF8.GetString($source),
            [Microsoft.CodeAnalysis.CSharp.CSharpParseOptions]::Default,
            'retained-p-native.cs',[Text.Encoding]::UTF8,[Threading.CancellationToken]::None))
    $refs=[Collections.Generic.List[Microsoft.CodeAnalysis.MetadataReference]]::new()
    foreach($path in @($compiler.files.Keys|Sort-Object)) {
        & $checkpoint
        if($path.StartsWith($compiler.root+'/ref/',[StringComparison]::Ordinal)) {
            $refs.Add([Microsoft.CodeAnalysis.MetadataReference]::CreateFromFile(
                $path,[Microsoft.CodeAnalysis.MetadataReferenceProperties]::Assembly,$null))
        }
    }
    if($refs.Count -lt 1 -or $refs.Count -gt 256){throw 'compiler reference bound'}
    $constructor=@([Microsoft.CodeAnalysis.CSharp.CSharpCompilationOptions].GetConstructors()|
        Where-Object {$p=$_.GetParameters();$p.Count -ge 1 -and $p[0].ParameterType -eq [Microsoft.CodeAnalysis.OutputKind] -and @($p|Select-Object -Skip 1|Where-Object {-not $_.IsOptional}).Count -eq 0}|
        Sort-Object {$_.GetParameters().Count})[0]
    if($null -eq $constructor){throw 'explicit optional compilation-options API unavailable'}
    $parameters=$constructor.GetParameters();$optionArgs=[object[]]::new($parameters.Count)
    $optionArgs[0]=[Microsoft.CodeAnalysis.OutputKind]::DynamicallyLinkedLibrary
    for($i=1;$i -lt $optionArgs.Length;$i++){$optionArgs[$i]=$parameters[$i].DefaultValue}
    $options=$constructor.Invoke($optionArgs)
    $compilation=[Microsoft.CodeAnalysis.CSharp.CSharpCompilation]::Create(
        'Cho51P2Native',$trees,$refs.ToArray(),$options)
    $emit=@($compilation.GetType().GetMethods()|Where-Object {
        $p=$_.GetParameters();$_.Name -eq 'Emit' -and $p.Count -ge 1 -and
        $p[0].ParameterType -eq [IO.Stream] -and
        @($p|Select-Object -Skip 1|Where-Object {-not $_.IsOptional}).Count -eq 0
    }|Sort-Object {$_.GetParameters().Count})[0]
    if($null -eq $emit){throw 'explicit optional Emit API unavailable'}
    $stream=[IO.MemoryStream]::new()
    try {
        $parameters=$emit.GetParameters();$emitArgs=[object[]]::new($parameters.Count);$emitArgs[0]=$stream
        for($i=1;$i -lt $emitArgs.Length;$i++){$emitArgs[$i]=$parameters[$i].DefaultValue}
        & $checkpoint
        $result=$emit.Invoke($compilation,$emitArgs)
        & $checkpoint
        if(-not $result.Success){$text=($result.Diagnostics|ForEach-Object {$_.ToString()}) -join '; ';throw ('native emit: '+$text.Substring(0,[Math]::Min(2048,$text.Length)))}
        if($stream.Length -lt 512 -or $stream.Length -gt 1MB){throw 'native PE output bound'}
        return ,$stream.ToArray()
    } finally {$stream.Dispose()}
}
