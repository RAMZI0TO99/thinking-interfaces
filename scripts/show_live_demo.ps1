param(
    [Parameter(Mandatory=$true)][string]$StatePath,
    [Parameter(Mandatory=$true)][string]$OutputDirectory,
    [switch]$HiddenPreview
)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
[System.Windows.Forms.Application]::EnableVisualStyles()
$initial = Get-Content -LiteralPath $StatePath -Raw | ConvertFrom-Json
$form = New-Object System.Windows.Forms.Form
$form.Text = $initial.interface.title
$form.ClientSize = New-Object System.Drawing.Size($initial.interface.width, $initial.interface.height)
$form.StartPosition = 'CenterScreen'
$form.FormBorderStyle = 'FixedSingle'
$form.MaximizeBox = $false
$form.BackColor = [System.Drawing.Color]::FromArgb(17, 24, 39)
$form.ForeColor = [System.Drawing.Color]::White
if ($HiddenPreview) { $form.Opacity = 0; $form.ShowInTaskbar = $false }

function Add-DisplayLabel([string]$Text, [int]$X, [int]$Y, [int]$Width, [int]$Height, [int]$FontSize) {
    $label = New-Object System.Windows.Forms.Label
    $label.Text = $Text
    $label.Location = New-Object System.Drawing.Point($X, $Y)
    $label.Size = New-Object System.Drawing.Size($Width, $Height)
    $label.Font = New-Object System.Drawing.Font('Segoe UI', $FontSize)
    $form.Controls.Add($label)
    return $label
}
$heading = Add-DisplayLabel 'THINKING INTERFACES' 32 24 930 46 24
$subtitle = Add-DisplayLabel "Live recording replay | $($initial.subject) | CPU EEGNet" 34 75 930 32 14
$framing = Add-DisplayLabel 'Training used other subjects only. These displayed trials were never used for fitting.' 34 111 930 45 11
$status = Add-DisplayLabel 'Waiting for the first complete EEG window...' 34 164 930 48 18
$target = Add-DisplayLabel 'Target: waiting for replay' 34 219 930 32 13
$grid = @{}
$index = 0
foreach ($className in $initial.class_labels) {
    $x = 34 + ($index % 2) * 470
    $y = 268 + [Math]::Floor($index / 2) * 82
    $cell = Add-DisplayLabel ($className -replace '_', ' ') $x $y 450 64 18
    $cell.TextAlign = 'MiddleCenter'
    $cell.BackColor = [System.Drawing.Color]::FromArgb(38, 49, 65)
    $grid[$className] = $cell
    $index++
}
$confidenceText = Add-DisplayLabel 'Gate confidence: waiting' 34 445 930 30 12
$confidenceBar = New-Object System.Windows.Forms.ProgressBar
$confidenceBar.Location = New-Object System.Drawing.Point(34, 480)
$confidenceBar.Size = New-Object System.Drawing.Size(930, 20)
$confidenceBar.Maximum = 1000
$form.Controls.Add($confidenceBar)
$command = Add-DisplayLabel 'Command: none | neutral is an intentional abstention' 34 519 930 38 14
$timing = Add-DisplayLabel 'Samples: 0 | completed windows: 0' 34 565 930 32 11
$footer = Add-DisplayLabel 'Exploratory replay, not live brain control. Gate A remains unsigned. Saved Profile A epochs.' 34 618 930 48 10
$footer.ForeColor = [System.Drawing.Color]::FromArgb(172, 185, 203)
$script:seen = New-Object System.Collections.Generic.List[int]
$script:updates = New-Object System.Collections.Generic.List[object]
$script:lastSequence = -999
$script:completionStarted = $null
$script:completed = $false
$script:failure = $null

function Save-WindowPreview([string]$Name) {
    $bitmap = New-Object System.Drawing.Bitmap($form.Width, $form.Height)
    try {
        $form.DrawToBitmap($bitmap, (New-Object System.Drawing.Rectangle(0, 0, $form.Width, $form.Height)))
        $bitmap.Save((Join-Path $OutputDirectory $Name), [System.Drawing.Imaging.ImageFormat]::Png)
    } finally { $bitmap.Dispose() }
}
$timer = New-Object System.Windows.Forms.Timer
$timer.Interval = [int]$initial.interface.poll_interval_ms
$timer.Add_Tick({
    try {
        $state = Get-Content -LiteralPath $StatePath -Raw | ConvertFrom-Json
        if ([int]$state.sequence -ne $script:lastSequence) {
            $script:lastSequence = [int]$state.sequence
            $status.Text = if ($state.frame.decision_state -eq 'neutral') { 'NEUTRAL | waiting for enough confidence' } else { 'DECISION | ' + ($state.frame.decision_state -replace '_', ' ') }
            $target.Text = 'Target: ' + $state.frame.target
            $confidenceText.Text = ('Gate confidence: {0:P1} | threshold: {1:P0}' -f [double]$state.frame.confidence, [double]$state.confidence_threshold)
            $confidenceBar.Value = [Math]::Max(0, [Math]::Min(1000, [int](1000 * $state.frame.confidence)))
            foreach ($key in $grid.Keys) {
                $grid[$key].BackColor = if ($key -eq $state.frame.decision_state) { [System.Drawing.Color]::FromArgb(24, 129, 115) } else { [System.Drawing.Color]::FromArgb(38, 49, 65) }
            }
            $emitted = if ($state.frame.emitted_command) { $state.frame.emitted_command } else { 'none' }
            $command.Text = "Command: $emitted | requires $($state.required_consecutive) consistent windows"
            $timing.Text = ('Samples: {0}/{1} | window: {2} | processing: {3:N2} ms' -f $state.received_samples, $state.total_samples, ($state.sequence + 1), $state.frame.latency_ms)
            $form.Refresh()
            if ($state.sequence -ge 0) {
                $script:seen.Add([int]$state.sequence)
                $script:updates.Add(@{sequence=[int]$state.sequence; displayed_at_utc=[DateTime]::UtcNow.ToString('o'); state=[string]$state.frame.decision_state})
            } else { Save-WindowPreview 'initial.png' }
        }
        if ($state.status -eq 'failed') { throw [string]$state.error }
        if ($state.status -eq 'complete' -and $null -eq $script:completionStarted) {
            $status.Text = 'REPLAY COMPLETE | all samples received'
            $form.Refresh()
            Save-WindowPreview 'final.png'
            $script:completed = $true
            $script:completionStarted = [DateTime]::UtcNow
        }
        if ($null -ne $script:completionStarted -and ([DateTime]::UtcNow - $script:completionStarted).TotalMilliseconds -ge $initial.interface.close_after_complete_ms) { $form.Close() }
    } catch {
        $script:failure = $_.Exception.Message
        $form.Close()
    }
})
$form.Add_Shown({ $timer.Start() })
[System.Windows.Forms.Application]::Run($form)
$timer.Stop()
$timer.Dispose()
$receipt = @{
    completed = $script:completed; error = $script:failure; sequences = @($script:seen.ToArray())
    updates = @($script:updates.ToArray()); renderer = 'Windows Forms'; hidden_preview = [bool]$HiddenPreview
}
$receiptPath = Join-Path $OutputDirectory 'interface_receipt.json'
$receipt | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath ($receiptPath + '.tmp') -Encoding UTF8
Move-Item -LiteralPath ($receiptPath + '.tmp') -Destination $receiptPath -Force
$form.Dispose()
if (-not $script:completed -or $script:failure) { exit 1 }
