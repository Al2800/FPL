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
| [0014](0014-historical-seasons-event-data.md) | Historical seasons with reliable event-level data (Open Decision 6) | Proposed |
| [0015](0015-browser-dry-run-stability.md) | Stability threshold before browser dry-run (Open Decision 11) | Proposed |
| [0016](0016-agent-runtime-budgets.md) | Per-Gameweek agent cost and latency budgets (Open Decision 13) | Proposed |
| [0017](0017-benchmark-kernel.md) | Fixed observed-episode benchmark contract | Accepted |
| [0018](0018-benchmark-datasets.md) | Full 2025/26 benchmark seed and live snapshots | Accepted |
| [0019](0019-historical-ruleset.md) | Historical 2025/26 ruleset activation | Accepted |
| [0020](0020-transfer-option-value-bridge.md) | Transfer option-value bridge | Accepted for replay review |
| [0021](0021-sol-subscription-evidence-agent.md) | GPT-5.6 Sol subscription-hosted evidence arm (Open Decision 8) | Accepted |
| [0023](0023-model-run-evidence-admission-and-rationale.md) | Engine-model evidence admission with visible rationale trace | Accepted |
