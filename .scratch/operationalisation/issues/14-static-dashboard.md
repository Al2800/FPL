# 14 — Static dashboard and notification surface

Status: resolved
Type: task
Track: Phase 2 (reporting surface)
Blocked by: 02, 04

Activation gate: Phase 2 authorised by owner on 4 August 2026 (tickets 06, 14).

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

## Answer

Implemented:

- `src/reporting/gdr_html.py` — deterministic self-contained HTML; season index
  scanner; colour-independent `[OK]`/`[DEGRADED]` status text; MC/price-risk
  sections explicitly unavailable when absent; no execution controls
- `scripts/render_gdr_report.py` — render one GDR or `--season-index`
- `scripts/send_deadline_reminder.py` — optional reminder via ticket-04 notifier
- Example render: `reports/gameweeks/schema-example/` + `reports/gameweeks/index.html`

Tests: `tests/reporting/test_gdr_html.py`.
