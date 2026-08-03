$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$codexPath = Join-Path $env:APPDATA 'npm\codex.cmd'
if (-not (Test-Path -LiteralPath $codexPath)) { $codexPath = (Get-Command codex.cmd -ErrorAction Stop).Source }
& (Join-Path $PSScriptRoot 'run_chatgpt_agent_task.ps1') `
    -RepositoryRoot $root `
    -CodexPath $codexPath `
    -TaskId 'strategy-review' `
    -PromptPath (Join-Path $root 'prompts\daily-strategy-research\v2-broad-signal-review.md')
exit $LASTEXITCODE
