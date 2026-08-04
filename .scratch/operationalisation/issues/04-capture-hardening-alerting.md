# 04 — Capture hardening and freshness alerting

Status: resolved
Type: task
Track: Phase 2 (operational hardening)
Blocked by: 02

Activation gate: Phase 2 authorised by owner on 4 August 2026 (tickets 04–05).

## Context

Capture scheduling is a single Windows machine via `scripts/install_deadline_capture_scheduler.ps1` (Task Scheduler, 15-minute polling). A missed T-2h capture silently yields a stale recommendation. Plan §22.1 defines degraded-operation reporting but nothing notifies a human.

## Scope

- A portable scheduler path (cron/systemd unit or equivalent) alongside the existing PowerShell installer, reusing `src/orchestration/deadline_capture_scheduler.py` unchanged.
- A freshness monitor: given the capture plan and the snapshot ledger, report missed jobs, stale sources (against `max_staleness` in the source registry) and affected features; exit non-zero / emit a notification (email or webhook — keep the transport pluggable and secret-free in Git).
- Wire the freshness result into the GDR's data-quality section so a degraded record is visibly degraded.

## Done when

- The portable scheduler installs, runs the dispatcher against an offline
  fixture, records its operational state and can be uninstalled without
  deleting captured evidence.
- A simulated missed T-2h capture produces an alert and a GDR flagged degraded
  rather than a silent stale recommendation.
- Tests cover missed, stale, duplicate and recovered checkpoints without
  performing network access.

## Answer

Implemented:

- `src/orchestration/freshness_monitor.py` — missed jobs via `plan_due_jobs`,
  registry `max_staleness` parsing (`6h`/`7d`/non-enforceable markers),
  recovered/duplicate handling, pluggable `NullNotifier`/`WebhookNotifier`
  (URL from `FPL_FRESHNESS_WEBHOOK_URL` only)
- `scripts/check_capture_freshness.py` — offline CLI; exit 1 when degraded
- Portable install/uninstall: `scripts/install_deadline_capture_scheduler.sh`,
  `scripts/uninstall_deadline_capture_scheduler.sh`, plus systemd examples under
  `config/operations/` (Windows PowerShell installers unchanged)
- `run_gameweek(..., freshness_report=...)` / `--freshness-report` merges
  capture freshness into GDR `data_quality` / `degraded_reasons`

Tests: `tests/orchestration/test_freshness_monitor.py`,
`tests/orchestration/test_portable_capture_scheduler.py`, and the missed-T-2h
integration case in `tests/integration/test_run_gameweek.py`.
