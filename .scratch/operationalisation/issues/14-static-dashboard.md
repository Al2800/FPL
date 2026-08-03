# 14 — Static dashboard and notification surface

Status: ready-for-agent
Type: task
Track: E (structure and surfaces)
Blocked by: 02

## Context

Phase 2 deliverables include a "dashboard or static report view"; today the closest artefact is the static HTML replay report (`scripts/render_replay_report.py`). A live engine needs one place showing the current recommendation, its confidence and evidence, and data freshness.

## Scope

- A static HTML render of the live GDR (no server): recommendation, candidate-plan comparison with distributions (ticket 05 output when available), evidence citations and conflicts, validation result, data-freshness/degraded status from ticket 04, price-risk annotations from ticket 07 when available.
- A season index page over `reports/gameweeks/` with outcome and retrospective once attached (ticket 03).
- Optional deadline reminder via the same pluggable notifier as ticket 04.

## Done when

- After `run_gameweek`, one command (or the orchestrator itself) emits the HTML view, and the owner can approve from the rendered record plus the signed journal entry (Phase-1 approval interface, plan §18).

## Boundaries

No hosted/cloud dashboard (Phase 9); no execution buttons — approval remains a journal entry, execution remains manual.
