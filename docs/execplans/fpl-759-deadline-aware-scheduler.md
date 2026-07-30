# Install a deadline-aware local capture scheduler

This ExecPlan is a living document. It follows `C:\Users\Alastair\.codex\.agent\PLANS.md`; contributors must keep the Progress, Surprises & Discoveries, Decision Log and Outcomes & Retrospective sections current.

## Purpose / Big Picture

The laboratory already has immutable FPL and odds capture commands, but an operator must invoke them manually. After this work, one Windows Scheduled Task will run a read-only dispatcher at a fixed interval. The dispatcher reads the current official FPL deadline, determines which daily or deadline-relative captures are due, and writes an auditable local result for each attempt. It cannot submit an FPL team, use a browser, expose a secret, backfill a missed checkpoint, or retry a failed market request blindly.

An operator will be able to run the dispatcher in dry-run mode, inspect the due jobs, install the user-scoped task, and query the task to confirm it is active. The first installed task remains safe while `THE_ODDS_API_KEY` is absent: it records a degraded odds slot without contacting the Odds API.

## Progress

- [x] (2026-07-30 11:56Z) Read `AGENTS.md`, the complete `docs/plan.md`, the ExecPlan requirements, source registry, capture runbooks and existing capture commands.
- [x] (2026-07-30 11:56Z) Created and claimed Bead `FPL-759`.
- [x] (2026-07-30 11:56Z) Added the pure schedule/config/state contract and offline tests.
- [x] (2026-07-30 12:16Z) Added the dependency-free dispatcher CLI and Windows install/uninstall/task-launcher scripts.
- [x] (2026-07-30 12:17Z) Passed 20 focused tests, ran the offline fixture dry-run, live bootstrap and registered/query-verified the local task (last result 0).
- [ ] Commit, push, document the outcome and close the Bead.

## Surprises & Discoveries

- Observation: `docs/data-sources/snapshot-cadence.md` defines the intended cadence but explicitly says captures remain manual until a scheduler is installed.
  Evidence: the runbook gives a cron example and no existing scheduler source or Bead was found.

- Observation: `scripts/capture_live_odds.py` is already credential-safe and refuses a missing key before a provider request.
  Evidence: its provider contract reads only `THE_ODDS_API_KEY`; the current process and user environments both report it absent.

- Observation: the transactional evidence checkpoint runner requires current solver input/output and therefore is not a general unattended data-capture entry point.
  Evidence: `scripts/run_evidence_checkpoint.py` requires `--solver-input` and `--solver-output`.

- Observation: the existing virtual environment has no `filelock` package, and Task Scheduler caps a `/TR` command at 261 characters.
  Evidence: the first focused run raised `ModuleNotFoundError: filelock`; the first registration attempt failed with the documented `/TR` limit.
  Resolution: the dispatcher uses a standard-library create-only lock and the task calls a short PowerShell launcher.

## Decision Log

- Decision: use one fixed-interval dispatcher rather than a separate Windows task per Gameweek checkpoint.
  Rationale: official deadlines and fixtures can change. The dispatcher derives current deadlines from a registered official bootstrap observation at runtime and retains the exact observation used to plan jobs.
  Date/Author: 2026-07-30 / Codex.

- Decision: run the Windows task every fifteen minutes while Alastair is signed in, with the final checkpoint targeted fifteen minutes before the FPL deadline.
  Rationale: this stays inside the Odds API final slot (0–30 minutes remaining), avoids a persistent credential in task XML, and retains a manual fallback if the computer is asleep or signed out.
  Date/Author: 2026-07-30 / Codex.

- Decision: source data remains in the existing immutable capture commands; the dispatcher coordinates rather than reimplements parsing, source permission checks, odds admission or manifest writing.
  Rationale: a thin coordinator has fewer independent data semantics and preserves existing tests and provenance contracts.
  Date/Author: 2026-07-30 / Codex.

## Outcomes & Retrospective

Installed `FPL Deadline-Aware Capture` for the signed-in `DESKTOP-8EKEQMT\\Alastair` account on 2026-07-30. Its next run is 12:30 Europe/London and it invokes the task launcher in this worktree using the existing `C:\\Users\\Alastair\\FPL\\.venv\\Scripts\\python.exe`. Validation passed: 20 focused scheduler/Odds-provider tests and an offline fixture dry-run (`network_calls: 0`). `THE_ODDS_API_KEY` is configured as a user-level secret (never written to the repository or task), and the verified first official bootstrap at `2026-07-30T12:08:35Z` succeeded. A manual Windows Scheduled Task invocation then exited 0 and wrote a second local report. No odds checkpoint was due, so no Odds API request was made.

## Context and Orientation

The repository root is `C:\Users\Alastair\FPL-pr-review`. Sources are authorised in `control/sources/source-registry.yaml`. The public FPL endpoint collector is enabled, and The Odds API is authorised for private local analysis. Raw capture output is Git-ignored and must remain local.

`scripts/capture_fpl_live_shadow.py` performs registered, unauthenticated official bootstrap/fixtures capture and builds a hash-bound local forecast-input artifact. `scripts/capture_live_odds.py` captures one `T-24h`, `T-8h`, `T-2h` or `final` Odds API slot, provided its environment key is available. `src/orchestration/evidence_checkpoint_runner.py` is not called by this scheduler because it requires a later decision-stage solver state.

A checkpoint is an observation intended for a particular window before the current FPL deadline. A missed checkpoint is not recreated later: the dispatcher writes a local `missed` outcome and the downstream forecast sees an explicit gap. A scheduler state file records which uniquely named checkpoint attempts have already happened. It is operational state, not a source artifact.

## Plan of Work

Create `config/data_sources/2026-27-capture-scheduler.json` as the complete schedule policy. It will declare the season, `Europe/London` daily capture time, a 15-minute dispatch interval, a bounded lateness window, named offsets for T-48h/T-24h/T-8h/T-2h/final, source command policies and the local state/report roots. The final target is deadline minus 15 minutes; it remains strictly before the deadline and inside the approved Odds API final window.

Create `src/orchestration/deadline_capture_scheduler.py`. Its pure functions parse an official bootstrap, select the next unfinished FPL event, calculate UTC target times, and return a deterministic list of due jobs. They will reject naive timestamps, unknown checkpoint names, unknown time zones, late/malformed bootstrap events, an observation after the deadline, and duplicate state entries. The state reducer will mark every selected job `complete`, `degraded`, `missed` or `refused`; it will never treat a later run as timely for a missed slot.

Create `scripts/run_deadline_capture_dispatch.py`. In `--dry-run` mode it accepts a supplied bootstrap fixture and prints the exact planned jobs without network or writes. In normal mode it captures a registered bootstrap scheduling probe, derives jobs, takes a local single-writer lock, and invokes only existing command-line capture interfaces. It calls official capture for due official jobs. For odds it first tests only for environment-variable presence; an absent key writes a degraded slot and makes no network request. With a key, it calls `capture_live_odds.py` for the exact slot and then passes the resulting artifact to the accompanying official capture. Every run writes a hashable local report, stdout summary and state update. Subprocess output is redacted and bounded.

Create `scripts/install_deadline_capture_scheduler.ps1` and `scripts/uninstall_deadline_capture_scheduler.ps1`. The install script checks the repository Python executable and dispatcher dry-run, then registers `FPL Deadline-Aware Capture` as a per-user InteractiveToken task every 15 minutes. It uses an absolute repository path, no secret, no browser profile and no FPL credentials. The uninstall script removes only that named task after confirming its identity. Neither script begins a source capture while being installed.

Add unit tests in `tests/orchestration/test_deadline_capture_scheduler.py` for deadline movement, daily selection, all relative windows, final-window correctness, duplicate suppression, missed-window refusal, UTC/DST conversion, malformed bootstrap and no-backfill behavior. Add integration tests in `tests/integration/test_deadline_capture_dispatch.py` using injected command runners: they prove a dry-run invokes nothing, a missing key makes no Odds API call, official/odds command order is correct, lock contention records refusal, and reports have no account or browser action fields.

Document exact operator use, the signed-in limitation, the task name, the user environment-variable setup, task query, log/report locations and the manual recovery procedure in `docs/data-sources/deadline-capture-scheduler.md`.

## Concrete Steps

From `C:\Users\Alastair\FPL-pr-review`, run the focused suite:

    .venv\Scripts\python.exe -m pytest -q tests/orchestration/test_deadline_capture_scheduler.py tests/integration/test_deadline_capture_dispatch.py tests/data/test_live_odds_provider.py

Run a fixture dry-run:

    .venv\Scripts\python.exe scripts/run_deadline_capture_dispatch.py --dry-run --bootstrap-fixture tests/fixtures/fpl-bootstrap-scheduler.json --now 2026-08-20T17:30:00Z

Expected output is JSON containing a UTC deadline, a deterministic due-job list and `network_calls: 0`.

Install only after the dry-run and tests pass:

    powershell -ExecutionPolicy Bypass -File scripts\install_deadline_capture_scheduler.ps1
    Get-ScheduledTask -TaskName 'FPL Deadline-Aware Capture' | Format-List TaskName,State

Expected output names the task and shows Ready or Running. Installation must not create a raw FPL capture or contact The Odds API.

## Validation and Acceptance

The focused suite must pass. The fixture dry-run must select only jobs whose configured window contains `--now`, and must report no network calls. A same-input second run must produce byte-identical planned jobs. A late `T-2h` or final window must yield a `missed` record, not a capture attempt. An absent `THE_ODDS_API_KEY` must yield `degraded_missing_secret` and no mocked Odds request.

The installation verification is a Task Scheduler query plus the dispatcher dry-run. A real live capture is not part of scheduler installation; it will occur only when the task reaches a configured time window.

## Idempotence and Recovery

The install script updates only the named per-user task and can be rerun. The uninstall script removes only that task. Dispatcher state uses a job identity of season, Gameweek, checkpoint and target UTC time; repeated dispatcher invocations do not duplicate a completed, degraded, missed or refused job. A crash before state finalisation leaves a `started` entry that becomes a visible refusal for manual review, not an automatic repeat.

If a computer is asleep or the user is not signed in, Windows will not run this InteractiveToken task. On the next manual dispatch, the system records expired slots as missed. The operator may run the ordinary capture command manually, but it remains a later observation and must not be labelled as the missed checkpoint.

## Artifacts and Notes

All runtime state and reports remain below `data/live-shadow/scheduler/` and are Git-ignored. The report contains only job identities, UTC times, command result classification, public artifact paths/hashes and redacted error messages. It contains no API key, request URL with a key, cookie, browser state, manager state or account action.

## Interfaces and Dependencies

In `src/orchestration/deadline_capture_scheduler.py`, define a stable pure planner:

    def plan_due_jobs(*, bootstrap: Mapping[str, Any], now: datetime, policy: Mapping[str, Any], completed_job_ids: Collection[str]) -> list[dict[str, Any]]

It returns job dictionaries with `job_id`, `gameweek`, `checkpoint`, `target_at`, `deadline_at`, `kind` (`official` or `odds`) and `late_by_seconds`. It must not access the network, environment or filesystem.

The dispatcher accepts injectable `bootstrap_loader`, `command_runner`, `environment` and `clock` functions so all important behavior has offline tests. Production wiring uses only the existing scripts listed above and enforces the source registry through those scripts.

Revision note (2026-07-30): initial plan created after confirming the previous cadence was manual-only and the Odds API key was absent.
