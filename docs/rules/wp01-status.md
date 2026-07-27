# WP-01 Rules audit — status

**Package:** WP-01
**Status:** Launch re-verification complete; owner advisory sign-off pending
**Ruleset:** `control/rules/2026-27.yaml` (`2026-27-v1.0`)
**Golden cases:** `evals/golden-cases/rules-2026-27.yaml`

## Done-when checklist

| Criterion | Status |
|---|---|
| Every Section 5.3 category has versioned 2026/27 entries | Met — see categories in the YAML |
| Each rule has status, source_url and verified_at | Met — enforced by `tests/rules/test_rules_catalogue.py` |
| Every rule has dated official launch evidence | Met — 39/39 confirmed |
| Golden cases cover each rule family | Met |

## Verification result

- **Confirmed:** all 39 rules, including budget, squad/formation, transfers,
  pricing, chips, scoring, BPS, substitutions, captain fallback, fixture support,
  correction timing and deadlines.
- **Activation:** zero machine blockers; `2026-27-v1.0` compiles to a
  38-Gameweek transition profile.
- **Owner gate:** pending for advisory use at the exact ruleset SHA. Browser
  execution and account writes remain unapproved.

## Next

## Longitudinal activation warning

The catalogue being present does not make the longitudinal engine live-ready. `docs/rules/season-transition-ledger.md` records every known stateful rule that can compound across Gameweeks and the activation evidence required for 2026/27.

The typed, ruleset-driven preflight and cross-season differential suite now normalise the historical AFCON object and live `false` value, derive chip boundaries and terminal state from rules, and preserve historical hashes.

Historical replay must continue to inject and hash `2025-26.yaml`; live execution must never switch merely because `2026-27.yaml` is the default loader.

Review packet: `docs/rules/2026-27-owner-signoff.md`. Residual log: `docs/data-sources/launch-reverification.md`. Golden runner: `python -m scripts.run_rules_golden`.
