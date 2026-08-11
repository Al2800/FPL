[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$PythonPath
)

# Daily supplementary source captures (ClubElo, Understat when installed).
# Idempotent per UTC day: a source already captured today is skipped.
# Writes one JSON report per run under data/live-shadow/scheduler/supplementary/.

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$PythonPath = (Resolve-Path -LiteralPath $PythonPath).Path

# Native commands write progress to stderr; only exit codes decide status.
$ErrorActionPreference = 'Continue'

$today = (Get-Date).ToUniversalTime().ToString('yyyy-MM-dd')
$stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$reportDir = Join-Path $root 'data\live-shadow\scheduler\supplementary'
New-Item -ItemType Directory -Path $reportDir -Force | Out-Null

$jobs = @()

# --- ClubElo: one ranking capture per UTC day ---
$clubeloDay = Join-Path $root "data\live-shadow\clubelo\$today"
if (Test-Path -LiteralPath $clubeloDay) {
    $jobs += @{ source = 'clubelo'; status = 'skipped'; detail = 'already_captured_today' }
} else {
    & $PythonPath (Join-Path $root 'scripts\capture_clubelo_ratings.py') 2>&1 | Out-Null
    $status = if ($LASTEXITCODE -eq 0) { 'complete' } else { 'degraded' }
    $jobs += @{ source = 'clubelo'; status = $status; detail = "exit_$LASTEXITCODE" }
}

# --- Understat: requires the understatapi package (owner-approved install) ---
& $PythonPath -c 'import understatapi' 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    $jobs += @{ source = 'understat'; status = 'skipped'; detail = 'understatapi_not_installed' }
} else {
    # Current-season table once matches exist; otherwise ensure the prior-season
    # table has been captured at least once for priors.
    $currentSeason = '2026'
    $priorSeason = '2025'
    $currentRoot = Join-Path $root "data\live-shadow\understat\EPL\$currentSeason"
    $priorRoot = Join-Path $root "data\live-shadow\understat\EPL\$priorSeason"
    $capturedToday = $false
    if (Test-Path -LiteralPath $currentRoot) {
        $capturedToday = @(Get-ChildItem -LiteralPath $currentRoot -Directory |
            Where-Object { $_.Name -like ($today.Replace('-', '') + '*') }).Count -gt 0
    }
    if ($capturedToday) {
        $jobs += @{ source = 'understat'; status = 'skipped'; detail = 'already_captured_today' }
    } else {
        & $PythonPath (Join-Path $root 'scripts\capture_understat_epl.py') --season $currentSeason --include-matches 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            $jobs += @{ source = 'understat'; status = 'complete'; detail = "season_$currentSeason" }
        } elseif (-not (Test-Path -LiteralPath $priorRoot)) {
            & $PythonPath (Join-Path $root 'scripts\capture_understat_epl.py') --season $priorSeason --include-matches 2>&1 | Out-Null
            $status = if ($LASTEXITCODE -eq 0) { 'complete' } else { 'degraded' }
            $jobs += @{ source = 'understat'; status = $status; detail = "prior_season_$priorSeason" }
        } else {
            $jobs += @{ source = 'understat'; status = 'skipped'; detail = 'current_season_empty_prior_present' }
        }
    }
}

# --- News triage: shortlist the newest news capture for Lane A verification ---
# The committed shortlist must land on origin/main before the 07:00 UTC cloud
# strategy run so its Lane A can verify leads and admit ledger claims.
$newsRoot = Join-Path $root 'data\live-shadow\news-discovery'
$latestCapture = $null
if (Test-Path -LiteralPath $newsRoot) {
    $latestCapture = Get-ChildItem -LiteralPath $newsRoot -Directory |
        Sort-Object Name | Select-Object -Last 1
}
if ($null -eq $latestCapture) {
    $jobs += @{ source = 'news_triage'; status = 'skipped'; detail = 'no_news_capture' }
} else {
    $captureFile = Join-Path $latestCapture.FullName 'news-capture.json'
    $triageOut = Join-Path $root "reports\news-triage\$($latestCapture.Name).json"
    if (-not (Test-Path -LiteralPath $captureFile)) {
        $jobs += @{ source = 'news_triage'; status = 'skipped'; detail = 'capture_missing_news_capture_json' }
    } elseif (Test-Path -LiteralPath $triageOut) {
        $jobs += @{ source = 'news_triage'; status = 'skipped'; detail = 'already_triaged' }
    } else {
        & $PythonPath (Join-Path $root 'scripts\run_news_capture_triage.py') --capture $captureFile --out $triageOut 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            # Publish the shortlist for the cloud Lane A run; scoped add only.
            Push-Location $root
            git pull --ff-only origin main 2>&1 | Out-Null
            git add "reports/news-triage/$($latestCapture.Name).json" "reports/news-triage/$($latestCapture.Name)-impact.json" "reports/news-triage/$($latestCapture.Name).md" 2>&1 | Out-Null
            git commit -m "Publish news triage shortlist $($latestCapture.Name) for Lane A verification." 2>&1 | Out-Null
            git push origin HEAD:main 2>&1 | Out-Null
            $pushOk = ($LASTEXITCODE -eq 0)
            Pop-Location
            $jobs += @{ source = 'news_triage'; status = $(if ($pushOk) { 'complete' } else { 'degraded' }); detail = $(if ($pushOk) { 'triaged_and_published' } else { 'triaged_push_failed' }) }
        } else {
            $jobs += @{ source = 'news_triage'; status = 'degraded'; detail = "triage_exit_$LASTEXITCODE" }
        }
    }
}

$report = @{
    schema_version = '1.0'
    task = 'supplementary_source_capture'
    observed_at = $stamp
    jobs = $jobs
}
$reportPath = Join-Path $reportDir "$stamp.json"
$report | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $reportPath -Encoding UTF8

$degraded = @($jobs | Where-Object { $_.status -eq 'degraded' }).Count
exit $(if ($degraded -gt 0) { 1 } else { 0 })
