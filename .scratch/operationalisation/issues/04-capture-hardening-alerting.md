# 04 — Capture hardening and freshness alerting

Status: ready-for-agent
Type: task
Track: A (close the live loop)

## Context

Capture scheduling is a single Windows machine via `scripts/install_deadline_capture_scheduler.ps1` (Task Scheduler, 15-minute polling). A missed T-2h capture silently yields a stale recommendation. Plan §22.1 defines degraded-operation reporting but nothing notifies a human.

## Scope

- A portable scheduler path (cron/systemd unit or equivalent) alongside the existing PowerShell installer, reusing `src/orchestration/deadline_capture_scheduler.py` unchanged.
- A freshness monitor: given the capture plan and the snapshot ledger, report missed jobs, stale sources (against `max_staleness` in the source registry) and affected features; exit non-zero / emit a notification (email or webhook — keep the transport pluggable and secret-free in Git).
- Wire the freshness result into the GDR's data-quality section so a degraded record is visibly degraded.

## Done when

- A simulated missed T-2h capture produces an alert and a GDR flagged degraded rather than a silent stale recommendation.
