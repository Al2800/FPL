# 2026/27 launch context

**Status:** prospective shadow input, observed 27 July 2026
**Control artifact:** `control/identities/2026-27-launch-context.json`
**World Cup ledger:** `control/identities/world-cup-2026-priors.csv`

## What this provides

The launch context makes the initial-squad cold start reproducible. It binds an
official FPL bootstrap snapshot, the completed 2025/26 player catalogue and the
World Cup prior ledger by SHA-256. Stable FPL `code` is the only automatic player
join. Display names are retained for review but never resolve an identity.

The official universe contains 558 players. The registered precedence gives each
player exactly one primary class:

| Primary class | Players | Forecast treatment |
|---|---:|---|
| Promoted team | 83 | Position/price prior plus 0.10 promoted-team risk |
| Other new to FPL | 26 | Position/price prior plus 0.08 new-signing risk |
| Changed current club | 25 | Stable-code performance prior plus 0.08 new-club minutes risk |
| Established | 424 | Stable-code prior, then the normal position/price fallback |

The precedence is deliberate. A player at Coventry City, Hull City or Ipswich
Town is primarily a promoted-team cold start even if absent from the prior
Premier League catalogue. Orthogonal `is_new_to_fpl` and `changed_club` flags are
still retained, so information is not discarded or double charged.

## Derivation

- Promoted teams are the official 2026/27 teams whose stable team codes are
  absent from the 2025/26 Premier League.
- A new player is an official current stable player code absent from the
  completed 2025/26 player catalogue.
- A transferred player has the same stable code in both catalogues but a
  different stable team code.
- The derivation is frozen to the official snapshot observed at
  `2026-07-27T10:05:27Z`. A later official snapshot must produce a new,
  reviewed artifact and new expected counts; it must not mutate this evidence.

These classes describe uncertainty, not player quality. They do not use 2026/27
outcomes.

## World Cup prior

The 176-row ledger currently joins 140 rows to the latest official player
universe. Thirty-three stable codes no longer appear in that universe and three
rows have no stable code. Those 36 rows are excluded visibly; no name-only
fallback is attempted.

Fatigue is an orthogonal expected-minutes input:

| Tier | Score |
|---|---:|
| none | 0.00 |
| moderate | 0.35 |
| high | 0.70 |
| extreme | 1.00 |

The score fades by Gameweek as `1.0, 1.0, 0.5, 0.5, 0.25, 0.0` for GW1–GW6.
The initial-squad policy applies its separately registered World Cup weight to
the effective score. This preserves the named prior for attribution instead of
baking it invisibly into expected points.

No cited club-specific return-to-training date has yet been admitted. Blank
dates therefore degrade visibly but do not block use of tournament minutes,
elimination dates or fatigue tier. A future return date is admitted only if its
evidence was available before the relevant decision cutoff.

## Failure and update policy

Unknown promoted teams, unknown new/transferred player codes, duplicate stable
codes, source-hash mismatches and official context observed at or after the
decision cutoff fail closed. A late World Cup row, blank World Cup identity or
stable code no longer in the current universe is excluded and reported as a
degradation.

Run the adapter for each decision boundary with the exact official bootstrap
body, its source hash, the World Cup rows and their source hash. The output is
self-hashed and reports class counts, World Cup coverage and every degraded row.
The live forecast capture understands the same four-class precedence.

Before GW1, repeat the derivation after each material official squad update.
Review and commit a new artifact rather than overwriting the snapshot history.
