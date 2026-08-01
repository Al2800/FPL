# 2026/27 launch context

**Status:** prospective shadow input, observed 27 July 2026
**Control artifact:** `control/identities/2026-27-launch-context.json`
**World Cup ledger:** `control/identities/world-cup-2026-priors.csv`

The 27 July artifact remains immutable. A 31 July successor was generated
locally after the official universe changed; it is not a mutation of the
reviewed artifact.

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

## Immutable successor re-derivation

When the official bootstrap hash changes, do not edit this reviewed 27 July
artifact. Use `scripts/build_launch_context.py` with immutable local inputs. The
prior-roster CSV is deliberately narrow and must be UTF-8 with exactly the
identity fields needed for deterministic derivation:

```text
code,team_code
59735,12
67089,78
```

`code` is the stable FPL player code and `team_code` is the stable FPL team code
from the completed 2025/26 roster. Both values are required integers; duplicate
or blank codes fail the build. Display names, club names and fuzzy matching are
not accepted.

The builder requires source `observed_at` and `available_at` timestamps for the
official bootstrap, prior roster and World Cup CSV, plus timestamps for the
produced context and an intended decision cutoff. Every timestamp must be
strictly before the cutoff; an input may not be observed before it was
available; the derived context may not precede one of its inputs. This preserves
point-in-time validity rather than merely recording a file date.

```powershell
C:\Users\Alastair\FPL\.venv\Scripts\python.exe scripts\build_launch_context.py `
  --bootstrap-file C:\data\bootstrap-static.json `
  --bootstrap-observed-at 2026-08-03T12:00:00Z `
  --bootstrap-available-at 2026-08-03T12:00:00Z `
  --prior-roster-file C:\data\2025-26-prior-roster.csv `
  --prior-roster-observed-at 2026-05-25T12:00:00Z `
  --prior-roster-available-at 2026-05-25T12:00:00Z `
  --world-cup-observed-at 2026-07-21T17:21:28Z `
  --world-cup-available-at 2026-07-21T17:21:28Z `
  --context-observed-at 2026-08-03T12:05:00Z `
  --context-available-at 2026-08-03T12:05:00Z `
  --decision-cutoff 2026-08-21T17:30:00Z
```

The command is offline. It copies the exact inputs, `context.json`, and a
self-hashed manifest beneath
`data/snapshots/2026-27/launch-context/<context-content-sha256>/`. That
operational evidence is ignored by Git. It reports the input hashes and a
`universe_delta`: player codes added versus the prior roster, prior codes now
removed, stable-code team changes, and promoted current team codes. A second
run with identical inputs verifies and returns the same bytes. Changed inputs
create another content-addressed directory; they never overwrite an earlier
context.

Pass the resulting `context_path` and copied World Cup CSV path explicitly to
`scripts/capture_preseason_snapshot.py`. FPL-756 will admit them only when the
checkpoint has identical raw bootstrap bytes; a different universe is recorded
as `official_bootstrap_hash_mismatch` and exposes no context bytes downstream.

## 31 July successor

Using the registered local 2025/26 roster and the official bootstrap captured at
`2026-07-31T19:22:08Z`, the successor context was built with:

- context SHA-256: `6d9dad02e85b3b3f428638105b28e9b453f60d149955417879a2b4d0c62a2dea`;
- manifest SHA-256: `ea6324eb0f3249184e69b90c7fc93c909e090755dcbb47346b5ded65d8bde4b0`;
- current official players: 564; prior roster rows: 841;
- class counts: 86 promoted, 27 new to FPL, 26 transferred and 425 established;
- World Cup coverage: 141 current-code matches out of 176 rows, 32 non-current
  codes and three blank codes;
- return-to-training dates: zero.

The successor is available under the gitignored content-addressed snapshot
directory and should be passed explicitly to the next checkpoint capture. Its
missing return dates remain a named degradation; no neutral dates were
invented.
