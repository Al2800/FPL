$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$codexPath = Join-Path $env:APPDATA 'npm\codex.cmd'
if (-not (Test-Path -LiteralPath $codexPath)) { $codexPath = (Get-Command codex.cmd -ErrorAction Stop).Source }
& (Join-Path $PSScriptRoot 'run_chatgpt_agent_task.ps1') `
    -RepositoryRoot $root `
    -CodexPath $codexPath `
    -TaskId 'strategy-review' `
    -PromptPath (Join-Path $root 'prompts\daily-strategy-research\v2-broad-signal-review.md')
$agentExit = $LASTEXITCODE

# Deterministic post-run steps. The agent never commits; this wrapper
# publishes scoped artefacts only (briefing, verification, evidence review,
# ledger chain, team diff). Native stderr must not abort the wrapper.
$ErrorActionPreference = 'Continue'
$python = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) { $python = 'python' }

# Day-over-day team diff from the two latest date-named briefings.
& $python (Join-Path $root 'scripts\diff_strategy_teams.py') 2>&1 | Out-Null

Push-Location $root
git pull --ff-only origin main 2>&1 | Out-Null
git add `
    'reports/strategy-research/*.md' `
    'reports/strategy-research/diffs/*.md' `
    'reports/news-triage/*-verifications-input.json' `
    'reports/news-triage/*-verified.json' `
    'reports/news-triage/*-verified-discovery.json' `
    'reports/news-triage/*-discovery-for-ingest.json' `
    'reports/evidence-review/*.md' `
    'reports/evidence-review/ledgers/*.json' `
    'reports/news-discovery/*.md' 2>&1 | Out-Null
git diff --cached --quiet 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    $day = (Get-Date).ToUniversalTime().ToString('yyyy-MM-dd')
    git commit -m "Daily strategy run ${day}: briefing, verification, ledger chain and team diff." 2>&1 | Out-Null
    git push origin HEAD:main 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Warning 'Scoped publish push failed; artefacts remain committed locally.'
    }
}
Pop-Location

exit $agentExit
