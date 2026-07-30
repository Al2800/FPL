# Deadline-aware local capture scheduler

The scheduler coordinates only the existing authorised, read-only capture commands. It does not open a browser, authenticate to FPL, submit a team, or make account changes. It runs every fifteen minutes while its registered user is signed in and stores operational state and reports below `data/live-shadow/scheduler/`.

The dispatcher reads the latest immutable official FPL bootstrap observation to find the event deadline. Its policy is in `config/data_sources/2026-27-capture-scheduler.json`:

- daily official observations at 07:00 and 10:00 Europe/London;
- checkpoint observations at T-48h, T-24h, T-8h, T-2h and 15 minutes before the deadline;
- odds snapshots for T-24h, T-8h, T-2h and final, followed by the matching official capture; and
- a missed window is recorded as a gap, never backfilled as if it had been timely.

An absent odds key produces `degraded_missing_secret_no_network`; the official capture continues. Scheduler reports redact the key and have explicit `account_writes: false` and `browser_actions: false` fields.

## Install and inspect

This checked-out launch worktree is `C:\Users\Alastair\FPL-pr-review`; its existing virtual environment is in `C:\Users\Alastair\FPL\.venv`. From a normal user PowerShell window, run:

```powershell
cd C:\Users\Alastair\FPL-pr-review
powershell -ExecutionPolicy Bypass -File .\scripts\install_deadline_capture_scheduler.ps1 `
  -RepositoryRoot 'C:\Users\Alastair\FPL-pr-review' `
  -PythonPath 'C:\Users\Alastair\FPL\.venv\Scripts\python.exe'

schtasks /Query /TN 'FPL Deadline-Aware Capture' /FO LIST /V
```

The installer first executes a local fixture dry-run and only then registers the per-user `FPL Deadline-Aware Capture` task. The task uses Windows `InteractiveToken`, so it runs only while you are signed in. It has no secret in the task definition. Installation itself does not fetch FPL or Odds API data.

Use this offline check at any time:

```powershell
& 'C:\Users\Alastair\FPL\.venv\Scripts\python.exe' .\scripts\run_deadline_capture_dispatch.py `
  --dry-run --bootstrap-fixture .\tests\fixtures\fpl-bootstrap-scheduler.json `
  --now 2026-08-20T17:30:00Z
```

## Store The Odds API key

Do not paste the key into chat, a Git file, or a command line. This command asks for it with masked input, stores it as a Windows **User** environment variable, and supplies it to the current shell without echoing it:

```powershell
cd C:\Users\Alastair\FPL-pr-review
$secure = Read-Host 'Paste The Odds API key' -AsSecureString
$pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
try {
  $plain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer)
  [Environment]::SetEnvironmentVariable('THE_ODDS_API_KEY', $plain, 'User')
  $env:THE_ODDS_API_KEY = $plain
} finally {
  [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer)
}
Remove-Variable plain, pointer, secure -ErrorAction SilentlyContinue
```

Then close and reopen Codex/PowerShell (or sign out and back in) before expecting a new scheduled-task process to see it. Verify only presence, never the value:

```powershell
if ([string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable('THE_ODDS_API_KEY', 'User'))) {
  'Odds key is not configured'
} else {
  'Odds key is configured for this Windows user'
}
```

## Review and recovery

Each invocation writes a timestamped report in `data/live-shadow/scheduler/reports/`. `state.json` records terminal checkpoint identities so repeated task invocations cannot duplicate an observation. A lock contention is refused instead of overlapping work. If a device is asleep or signed out, the next run records expired target windows as missed.

To remove the task without deleting any captured evidence or state:

```powershell
cd C:\Users\Alastair\FPL-pr-review
powershell -ExecutionPolicy Bypass -File .\scripts\uninstall_deadline_capture_scheduler.ps1
```