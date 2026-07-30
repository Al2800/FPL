[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string]$RepositoryRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$PythonPath,
    [ValidatePattern('^FPL Deadline-Aware Capture$')]
    [string]$TaskName = 'FPL Deadline-Aware Capture'
)

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path -LiteralPath $RepositoryRoot).Path
if (-not $PythonPath) {
    $PythonPath = Join-Path $root '.venv\Scripts\python.exe'
}
$PythonPath = (Resolve-Path -LiteralPath $PythonPath).Path
$dispatcher = Join-Path $root 'scripts\run_deadline_capture_dispatch.py'
$taskLauncher = Join-Path $root 'scripts\run_deadline_capture_task.ps1'
$config = Join-Path $root 'config\data_sources\2026-27-capture-scheduler.json'
$fixture = Join-Path $root 'tests\fixtures\fpl-bootstrap-scheduler.json'
foreach ($path in @($PythonPath, $dispatcher, $taskLauncher, $config, $fixture)) {
    if (-not (Test-Path -LiteralPath $path)) {
        throw "Required scheduler path is missing: $path"
    }
}

# Installation must remain offline: prove planner wiring against a static fixture first.
& $PythonPath $dispatcher --config $config --dry-run --bootstrap-fixture $fixture --now '2026-08-20T17:30:00Z' | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw 'Scheduler dry-run failed; task was not registered.'
}

$identity = if ($env:USERDOMAIN) { "$env:USERDOMAIN\$env:USERNAME" } else { $env:USERNAME }
$taskCommand = 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "{0}" -PythonPath "{1}"' -f $taskLauncher, $PythonPath
if ($taskCommand.Length -gt 261) {
    throw "Task Scheduler command is too long: $($taskCommand.Length) characters."
}
$arguments = @(
    '/Create', '/TN', $TaskName, '/TR', $taskCommand,
    '/SC', 'MINUTE', '/MO', '15', '/RU', $identity, '/IT', '/RL', 'LIMITED', '/F'
)
if ($PSCmdlet.ShouldProcess($TaskName, 'Register signed-in 15-minute local scheduler')) {
    & schtasks.exe @arguments
    if ($LASTEXITCODE -ne 0) {
        throw "schtasks.exe could not register '$TaskName'."
    }
}

& schtasks.exe /Query /TN $TaskName /FO LIST /V
if ($LASTEXITCODE -ne 0) {
    throw "Task registration could not be verified: $TaskName"
}
Write-Output "Installed $TaskName. It runs only while $identity is signed in; it contains no API key."