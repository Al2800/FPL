$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$codexPath = Join-Path $env:APPDATA 'npm\codex.cmd'
if (-not (Test-Path -LiteralPath $codexPath)) { $codexPath = (Get-Command codex.cmd -ErrorAction Stop).Source }
& (Join-Path $PSScriptRoot 'run_chatgpt_agent_task.ps1') `
    -RepositoryRoot $root `
    -CodexPath $codexPath `
    -TaskId 'unstructured-capture' `
    -PromptPath (Join-Path $root 'prompts\daily-news-research\v1.md')
exit $LASTEXITCODE
