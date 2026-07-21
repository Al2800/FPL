# Architecture decision records

Decisions with trade-offs are recorded here (see `AGENTS.md`). Statuses: **Proposed**, **Accepted**, **Superseded**. New records take the next number and follow the same structure: Status, Date, Decides, Context, Decision, Consequences.

| ADR | Decision | Status |
|---|---|---|
| [0001](0001-private-non-commercial.md) | The project is private and non-commercial | Accepted |
| [0002](0002-local-retention-of-raw-snapshots.md) | Local retention of raw snapshots | Accepted |
| [0003](0003-weekly-effort-budget.md) | Weekly operating-effort budget: 2h → 1h per Gameweek | Accepted |
| [0004](0004-minimum-meaningful-effect-size.md) | Minimum meaningful effect size: 0.5 points per Gameweek | Accepted |
| [0005](0005-manual-manager-state-entry.md) | Manager state entered manually at first | Accepted |
| [0006](0006-balanced-risk-preference.md) | Balanced risk preference with weekly aggressive override | Accepted |
| [0007](0007-download-historical-datasets-locally.md) | Historical datasets downloaded locally | Accepted |
| [0008](0008-duckdb-parquet-season-one.md) | DuckDB plus Parquet for season one | Accepted |
| [0009](0009-multi-manager-cohort.md) | Multi-manager live cohort of about five managers | Accepted |
| [0010](0010-plain-python-orchestration.md) | Plain Python as the initial orchestration substrate | Accepted |
| [0011](0011-transparent-internal-optimiser.md) | Smaller transparent internal optimiser (Open Decision 7) | Proposed |
| [0012](0012-single-gameweek-horizon.md) | Single-Gameweek optimiser horizon for Phase 1 (Open Decision 14) | Proposed |
| [0013](0013-evidence-adjustment-threshold.md) | Minimum evidence threshold for proposed adjustments (Open Decision 10) | Proposed |
