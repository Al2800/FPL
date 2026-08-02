[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string]$RepositoryRoot,
    [ValidatePattern('^\d{2}:\d{2}$')]
    [string]$CaptureTime = '06:00',
    [ValidatePattern('^\d{2}:\d{2}$')]
    [string]$ReviewTime = '08:00',
    [ValidatePattern('^FPL ChatGPT Unstructured Capture$')]
    [string]$CaptureTaskName = 'FPL ChatGPT Unstructured Capture',
    [ValidatePattern('^FPL ChatGPT Strategy Review$')]
    [string]$ReviewTaskName = 'FPL ChatGPT Strategy Review'
)

$ErrorActionPreference = 'Stop'
if (-not $RepositoryRoot) { $RepositoryRoot = Split-Path -Parent $PSCommandPath }
$root = (Resolve-Path -LiteralPath $RepositoryRoot).Path
$captureLauncher = Join-Path $root 'scripts\run_chatgpt_unstructured_capture_task.ps1'
$reviewLauncher = Join-Path $root 'scripts\run_chatgpt_strategy_review_task.ps1'
foreach ($path in @($captureLauncher, $reviewLauncher)) {
    if (-not (Test-Path -LiteralPath $path)) { throw "Required path is missing: $path" }
}
$identity = if ($env:USERDOMAIN) { "$env:USERDOMAIN\$env:USERNAME" } else { $env:USERNAME }
function Register-AgentTask {
    param([string]$TaskName, [string]$Time, [string]$Launcher)
    $taskCommand = 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "{0}"' -f $Launcher
    $arguments = @('/Create', '/TN', $TaskName, '/TR', $taskCommand, '/SC', 'DAILY', '/ST', $Time, '/RU', $identity, '/IT', '/RL', 'LIMITED', '/F')
    if ($PSCmdlet.ShouldProcess($TaskName, "Register daily Luna Max task at $Time local time")) {
        & schtasks.exe @arguments
        if ($LASTEXITCODE -ne 0) { throw "Task Scheduler could not register '$TaskName'." }
        & schtasks.exe /Query /TN $TaskName /FO LIST /V
        if ($LASTEXITCODE -ne 0) { throw "Task registration could not be verified: $TaskName" }
    }
}
Register-AgentTask -TaskName $CaptureTaskName -Time $CaptureTime -Launcher $captureLauncher
Register-AgentTask -TaskName $ReviewTaskName -Time $ReviewTime -Launcher $reviewLauncher
Write-Output "Installed $CaptureTaskName at $CaptureTime and $ReviewTaskName at $ReviewTime local time."
