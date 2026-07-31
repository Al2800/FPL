# 05 — Rehearse official lineup capture or approve a low-cost challenger

**Blocked by:** None — can start immediately.

**Status:** resolved

**Category:** enhancement

**Former bead:** `FPL-eah`

## Human Handoff

**Summary:** Select and complete one governed path for pre-match lineup
evidence: an official citation-capture rehearsal or an approved low-cost
challenger trial.

### Current behaviour

The ingestion/configuration boundary already degrades safely with
`selected_provider: null`. Official Premier League/club team sheets are the
canonical primary truth; official FPL event-live/element-summary data are the
post-match minutes oracle.

Sportradar was probed once for endpoint reachability, then disabled because its
ongoing cost was not justified. That probe admitted no fixtures:
`fixtures_measured: 0`, `matchdays_measured: 0`. The family is in
`degraded_official_capture_pending_rehearsal`, the registry entry remains
disabled, and null-provider safety tests pass.

### Desired behaviour

The owner chooses one branch and the chosen branch is actually completed—not
merely selected:

1. **Official citation path:** rehearse a complete, immutable capture of an
   official published XI/substitution record, including citation, publication
   and observation times, identity mapping, correction history and
   reconciliation to the official FPL minutes oracle.
2. **Low-cost challenger path:** approve a named provider only after its exact
   source/rights/retention terms are registered, then run the controlled
   admission trial over at least 10 Premier League fixtures across at least
   three matchdays.

Official sheets remain the adjudication truth. Disagreements are quarantined
and adjudicated; feeds are never averaged.

### Key interfaces

- Lineup configuration: `selected_provider`, `primary_truth_provider`,
  `collection_status`, provider approval/rights flags and trial status.
- Registry source: exact endpoints, licence status, allowed use, retention,
  enabled flag and owner approval.
- Provider-neutral snapshot: publication/observation/availability times,
  fixture and player identities, starting XI, substitutions, corrections,
  source/hash and failure mode.
- Admission gates for a challenger: at least 95% lineup coverage, 99% final
  minutes within ±1 minute of the FPL oracle, 100% identity coverage and 20%
  quota headroom.
- Degraded contract: missing credential, timeout, rate limit or outage must
  return safe no-network/degraded behaviour without changing the shared
  structured forecast.

### Acceptance criteria

- [x] The owner records the chosen branch, cost/rights rationale and whether any provider may be evaluated; Sportradar remains off unless a new explicit decision reverses the cost ruling.
- [x] Before either rehearsal/trial, the exact official or challenger source has a registry entry with confirmed licence status and allowed use.
- [x] Until that decision and registry gate are complete, `selected_provider` stays null, registry collection stays disabled and no capture runs.
- [x] **Official branch:** at least one complete rehearsal artifact demonstrates XI/substitution citation capture, temporal/provenance fields, identity mapping, correction handling and reconciliation to official FPL minutes.
- [x] **Challenger branch:** N/A — official citation path selected.
- [x] **Challenger branch:** N/A — official citation path selected.
- [x] Any disagreement is quarantined and adjudicated against the official team sheet; no averaging is introduced.
- [x] `python3 -m pytest -q tests/data/test_lineups_minutes.py tests/unit/test_registry.py` passes (19 tests at handoff).
- [x] No API keys, raw provider payloads or browser sessions are committed.

### Out of scope

- Re-enabling Sportradar on the basis of its historical reachability probe.
- Selecting or purchasing a feed without owner and registry approval.
- Treating API-Football, football-data.org or TheSportsDB as canonical truth.
- Implementing the later broad live shadow/ablation programme.
- Updating the archived Bead to mirror this ticket.

## Answer

**Branch chosen: official citation path (enabled).**

- Decision: `docs/data-sources/2026-27-lineups-citation-decision.md`
- Registry 0.6.2: `official-lineups-minutes` `enabled: true`, manual citation only
- Config: `selected_provider: official-team-sheets`; Sportradar still off
- Builder: `build_official_team_sheet_citation` / `rehearse_official_team_sheet_capture` in `src/ingestion/lineups_minutes.py`
- Rehearsal artifact: `evals/golden-cases/evidence/official-team-sheet-citation-rehearsal.json`
- HTTP capture helper returns `manual_citation_required` rather than inventing a scrape
