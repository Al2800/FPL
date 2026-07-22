# WP-01 Rules audit — status

**Package:** WP-01  
**Status:** Draft complete pending FPL 2026/27 launch re-verification  
**Ruleset:** `control/rules/2026-27.yaml` (`2026-27-v0.1`)  
**Golden cases:** `evals/golden-cases/rules-2026-27.yaml`

## Done-when checklist

| Criterion | Status |
|---|---|
| Every Section 5.3 category has versioned 2026/27 entries | Met — see categories in the YAML |
| Each rule has status, source_url and verified_at | Met — enforced by `tests/rules/test_rules_catalogue.py` |
| Unresolved rules listed as inherited/provisional | Met — not omitted; launch checklist in the YAML |
| Golden cases cover each rule family | Met |

## Confirmed vs unresolved

- **Confirmed:** chip sets and GW19 expiry, max five banked transfers, no AFCON top-up, defensive contributions retained, BPS 2026/27 metric changes, 09:00 UK Gameweek lock, live ranks / projected bonus from ~20 minutes.
- **Inherited / provisional (launch verification required):** budget, squad composition, formation bounds, hit cost, selling-price half-profit, GW1/boundary chip restrictions, deadline = KO−90m, and most scoring point values (sourced from current scoring page; confirm unchanged at launch).

## Next

## Longitudinal activation warning

The catalogue being present does not make the longitudinal engine live-ready. `docs/rules/season-transition-ledger.md` records every known stateful rule that can compound across Gameweeks and the activation evidence required for 2026/27.

Current blocker: the historical policy-state transition reads `transfers.afcon_exceptional_topup` as a 2025/26 `{gameweek, top_up_to}` object, while the confirmed 2026/27 value is `false`. Chip boundaries and the terminal Gameweek are also still encoded in Python. A typed, ruleset-driven preflight and cross-season differential suite must land before activation.

Historical replay must continue to inject and hash `2025-26.yaml`; live execution must never switch merely because `2026-27.yaml` is the default loader.

Re-run verification against live FPL rules pages and API schemas when 2026/27 launches; promote inherited → confirmed or revise. Residual log: `docs/data-sources/launch-reverification.md`. Golden runner: `python3 -m scripts.run_rules_golden`.
