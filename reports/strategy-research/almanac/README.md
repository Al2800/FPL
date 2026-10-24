# GW1 intro pack — 2026/27

Start here if you are a new model and need the live 15, the T-24h
expected-vs-actual record, and the owner stance. This pack is a
**record**. It is not a transfer recommendation and it does not
authorise account writes.

## Read in this order

1. This file.
2. `gw1-2026-27.html` — both 15s, our EP vs official `ep_next` vs actual.
3. `../2026-08-24-gw1-midweek-review.md` — calibration notes and stance.
4. `../packets/T-24h.json` — sealed T-24h packet. Do not rewrite.

Repo plan and rules still apply: `docs/plan.md`, `AGENTS.md`.

## Frozen facts

- Season: 2026/27. Bound packet: T-24h inner sha `879221d6…`.
  Published wrapper: `../packets/T-24h.json`.
- Snapshot on this page: official `event/1/live` at
  `2026-08-24T10:32:12Z` (provisional; bonus not locked).
- Account writes: **false**. No FPL login, no transfers, no chips.
- **Do not recapture T-24h or T-48h.**
- Do not retune live-faithful weights from this one Gameweek.
- Do not write event-live into T-24h.
- Do not confuse Harry Wilson (id **260**, Leeds MID) with Callum Wilson,
  or Bruno Fernandes (id **426**) with Bruno Guimarães.

## Live 15 (Haaland-in advisory)

Owner: Bruno Fernandes **(C)** / Haaland **(VC)**. Bank £0.5m. No GW1 chip.

| Slot | Player | id |
|---|---|---:|
| GKP | Verbruggen | 109 |
| DEF | Van Hecke | 112 |
| DEF | Mitchell | 204 |
| DEF | Shaw | 423 |
| MID | B.Fernandes (C) | 426 |
| MID | Gibbs-White | 480 |
| MID | E.Le Fée | 542 |
| MID | Wilson (Harry, LEE) | 260 |
| FWD | Haaland (VC) | 411 |
| FWD | João Pedro | 165 |
| FWD | Thiago | 106 |
| Bench | Dubravka, Xhaka, Diop, van Ewijk | 497, 544, 259, 175 |

XI+C at the Monday snapshot: **22** vs packet plan ~55. João Pedro still
to play in that snapshot.

## Robust comparator (not the live side)

T-24h optimiser 15. Bruno **(C)** / Semenyo **(VC)**. Bank £0.0.

IDs: `1, 109, 13, 165, 248, 388, 397, 4, 40, 423, 426, 441, 481, 498, 61`

XI+C at the Monday snapshot: **36** vs packet plan ~63. João Pedro and
Rogers still to play in that snapshot.

## Engine note (n=24 completed on these two 15s)

| Lens | Mean | Bias vs actual | MAE |
|---|---:|---:|---:|
| Our EP | 3.76 | −1.05 | 2.55 |
| Official EP | 2.37 | +0.34 | 1.63 |
| Actual | 2.71 | — | — |

Whole T-24h market was not hot (our 1.86 vs official 1.84 vs actual 2.00).
The heat is the premium tail. Minutes/starts first; shrink returns.

## Owner stance

No change to the live 15. Do not retune from GW1. Change the 15 only if
later pressers kill minutes, not because GW1 felt cold.

## Refresh the HTML

After a newer official `event/1/live` capture (never into T-24h):

```bash
./.venv/bin/python scripts/render_gw1_almanac.py \
  --event-live-dir data/live-shadow/fpl/event-live/<stamp>
```
