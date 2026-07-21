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

Re-run verification against live FPL rules pages and API schemas when 2026/27 launches; promote inherited → confirmed or revise. Residual log: `docs/data-sources/launch-reverification.md`. Golden runner: `python3 -m scripts.run_rules_golden`.
