# 14 — Static dashboard and notification surface

Status: needs-triage
Type: task
Track: Phase 2 (reporting surface)
Blocked by: 02, 04

Activation gate: the static report is a Phase 2 deliverable. Do not implement
until the Phase 0/1 live GDR is stable and Phase 2 is authorised.

## Context

Phase 2 deliverables include a "dashboard or static report view"; today the closest artefact is the static HTML replay report (`scripts/render_replay_report.py`). A live engine needs one place showing the current recommendation, its confidence and evidence, and data freshness.

## Scope

- A static HTML render of the live GDR (no server): recommendation, candidate-plan comparison with distributions (ticket 05 output when available), evidence citations and conflicts, validation result, data-freshness/degraded status from ticket 04, price-risk annotations from ticket 07 when available.
- A season index page over `reports/gameweeks/` with outcome and retrospective once attached (ticket 03).
- Optional deadline reminder via the same pluggable notifier as ticket 04.

## Done when

- A fixture GDR renders to deterministic HTML with no network calls.
- The rendered page exposes the proposal ID, cutoff, rules/model versions,
  validation, freshness/degraded state and approval-journal reference.
- The season index links every available live GDR and its attached outcome;
  missing optional ticket-05/07 outputs render as explicitly unavailable.
- Accessibility checks cover headings, table labels and colour-independent
  status indicators.

## Boundaries

No hosted/cloud dashboard (Phase 9); no execution buttons — approval remains a journal entry, execution remains manual.
