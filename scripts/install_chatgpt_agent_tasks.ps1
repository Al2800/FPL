[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string]$RepositoryRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$CodexPath,
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
$root = (Resolve-Path -LiteralPath $RepositoryRoot).Path
if (-not $CodexPath) {
    $command = Get-Command codex.cmd -ErrorAction SilentlyContinue
    if (-not $command) {
        $command = Get-Command codex -ErrorAction SilentlyContinue
    }
    if (-not $command) {
        throw 'The Codex CLI was not found on PATH.'
    }
    $CodexPath = $command.Source
}
$CodexPath = (Resolve-Path -LiteralPath $CodexPath).Path
$launcher = Join-Path $root 'scripts\run_chatgpt_agent_task.ps1'
$capturePrompt = Join-Path $root 'prompts\daily-news-research\v1.md'
$reviewPrompt = Join-Path $root 'prompts\daily-strategy-research\v1.md'
foreach ($path in @($launcher, $capturePrompt, $reviewPrompt)) {
    if (-not (Test-Path -LiteralPath $path)) {
        throw "Required path is missing: $path"
    }
}

$identity = if ($env:USERDOMAIN) { "$env:USERDOMAIN\$env:USERNAME" } else { $env:USERNAME }
function Register-AgentTask {
    param(
        [string]$TaskName,
        [string]$Time,
        [string]$TaskId,
        [string]$PromptPath
    )
    $taskCommand = 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "{0}" -RepositoryRoot "{1}" -CodexPath "{2}" -TaskId "{3}" -PromptPath "{4}"' -f $launcher, $root, $CodexPath, $TaskId, $PromptPath
    if ($taskCommand.Length -gt 261) {
        throw "Task Scheduler command is too long: $($taskCommand.Length) characters."
    }
    $arguments = @(
        '/Create', '/TN', $TaskName, '/TR', $taskCommand,
        '/SC', 'DAILY', '/ST', $Time, '/RU', $identity, '/IT', '/RL', 'LIMITED', '/F'
    )
    if ($PSCmdlet.ShouldProcess($TaskName, "Register daily Luna Max task at $Time local time")) {
        & schtasks.exe @arguments
        if ($LASTEXITCODE -ne 0) {
            throw "Task Scheduler could not register '$TaskName'."
        }
    }
    if (-not $WhatIfPreference) {
        & schtasks.exe /Query /TN $TaskName /FO LIST /V
        if ($LASTEXITCODE -ne 0) {
            throw "Task registration could not be verified: $TaskName"
        }
    }
}

Register-AgentTask -TaskName $CaptureTaskName -Time $CaptureTime -TaskId 'unstructured-capture' -PromptPath $capturePrompt
Register-AgentTask -TaskName $ReviewTaskName -Time $ReviewTime -TaskId 'strategy-review' -PromptPath $reviewPrompt
Write-Output "Installed $CaptureTaskName at $CaptureTime and $ReviewTaskName at $ReviewTime local time."
Write-Output 'Both tasks use the authenticated Codex CLI with GPT-5.6 Luna and maximum reasoning.'
