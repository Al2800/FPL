# 2026/27 initial-squad checkpoint operation

## Purpose

`FPL-guz` runs the dedicated season-start optimiser against a particular
immutable preseason capture. Its purpose is operational rehearsal: each run
shows what a prospective initial-15 process can see at that exact time,
whether it is complete enough for a real decision, and how the proposal changes
as new pre-deadline information is admitted.

It is always advisory-only. The runner has no browser or account-write path.
A legal squad in an artifact is not permission to enter it in FPL.

## Current live checkpoint

The first current-season checkpoint is `weekly-2026-07-30`.

| Field | Value |
|---|---|
| Observation time | `2026-07-30T08:02:14Z` |
| GW1 deadline | `2026-08-21T17:30:00Z` |
| Capture manifest | `eca9b64aa0c57be08480b0183fd00ca1738e0ed7e59fedcc2bd71d35443ddb30` |
| Official market | 558 players, public FPL bootstrap and fixtures |
| Run status | `degraded`, `approval_status=blocked` |
| Account writes | `false` |

The run is intentionally an **operational baseline**, not a tactical
recommendation. It uses the official one-GW `ep_next` field repeated across
the fixed six-GW planning horizon. That exercises the complete candidate,
legality, bench, captaincy, alternative, artifact and diff path while making
the forecast limitation impossible to miss.

The baseline cannot clear approval because the prospective six-GW
`live-faithful` forecast packet has not yet been materialised and hash-bound.
It must not be compared with a future decision-grade squad as though both had
the same information quality.

## Current coverage gaps

The checkpoint preserves these unavailable families individually rather than
turning them into observed zero-valued inputs:

- availability/role evidence;
- transfers and signings;
- set-piece roles;
- promoted-team priors;
- World Cup return/fatigue context;
- timestamped licensed odds; and
- player ratings.

The engine still receives the official current status and chance-of-playing
fields. It does not claim this is equivalent to cited club availability,
minutes, set-piece or rating data.

## Daily rhythm

The Composer 2.5 strategy agent is the **primary advisory decision**
(`docs/evaluation/2026-27-daily-agent-strategy-loop.md`): recommended 15, chip
path and captains after web search + packet reasoning. This checkpoint freezes
the statistical base and publishes deterministic/robust **comparators**; the
host rescores the strategy agent’s declared 15 against the same packet. The
agent cannot clear owner approval or write to FPL.

## Run and inspect

From the repository root:

```powershell
C:\Users\Alastair\FPL\.venv\Scripts\python.exe `
  scripts\run_initial_squad_checkpoint.py `
  --manifest data\snapshots\2026-27\preseason\weekly-2026-07-30\manifest.json `
  --output-root reports\live\2026-27\initial-squad
```

Each run writes a create-or-identical directory:

```text
reports/live/2026-27/initial-squad/<checkpoint-id>/
  input-packet.json       # candidate universe, exclusions, source states
  recommendation.json     # arms, legal squad, XI, captain, bench, risks
  diff.json / diff.md     # checkpoint-to-checkpoint comparison
  checkpoint.json         # sealed index and all output hashes
```

Rerunning an identical capture must retain byte-identical artifacts. A
different policy, ruleset, source byte, or report at the same checkpoint path
fails closed rather than overwriting the prior decision record.

## Before a manual-entry review

The approval gate must remain blocked until all of the following are true:

1. a decision-grade six-GW forecast packet is materialised from the immutable
   checkpoint rather than the temporary official-EP baseline;
2. required source coverage and every remaining degradation have an explicit
   acceptance decision;
3. deterministic and robust arms complete from the same packet;
4. the active 2026/27 rules activation matches the packet rules hash; and
5. an owner approves a named arm, proposal hash and packet hash before the
   official deadline.

For later checkpoints, pass the immediately preceding manifest hash during
capture. The runner then finds its corresponding prior output and produces a
sealed machine- and human-readable diff; it never compares with an unbound
"latest" directory.
