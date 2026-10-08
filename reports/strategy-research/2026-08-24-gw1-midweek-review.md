# GW1 mid-week review — 2026-08-24

- observed_at: 2026-08-24T10:32:00Z
- status: **provisional** (bonus not locked; `finished=false` on played fixtures)
- remaining: Fulham vs Chelsea **Mon 20:00 UK** (`2026-08-24T19:00:00Z`)
- bound packet: T-24h `879221d6…` (do not rewrite)
- source: official `event/1/live` at `data/live-shadow/fpl/event-live/20260824T103200Z/`
- account_writes: false
- almanac: `reports/strategy-research/almanac/gw1-2026-27.html` (regenerate with `scripts/render_gw1_almanac.py`)

João Pedro (both 15s) and Rogers (robust only) have not played.

## Side totals so far (XI + captain; no autosub)

| Side | Captain | XI+C so far | Packet GW1 plan (full week) | Still to play |
|---|---|---:|---:|---|
| Haaland-in advisory | Bruno or Haaland (both scored 2) | **22** | 56.46 (host Haaland C) / ~56.2 Bruno C | João Pedro |
| Robust no-Haaland | Bruno C | **36** | 63.55 | João Pedro + Rogers |

Unused bench so far: advisory Xhaka **9**, Diop 2, van Ewijk 1, Dubravka 0. No GW1 chip, so Xhaka does not count.

## Player EP vs actual (completed only)

| Player | Side | min | EP | Act | Δ | Note |
|---|---|---:|---:|---:|---:|---|
| Xhaka | adv bench | 90 | 2.53 | 9 | +6.47 | Assist + BPS + DefCon 13 |
| Guéhi | robust XI | 90 | 3.84 | 10 | +6.16 | Goal + bonus |
| Verbruggen | both | 90 | 2.28 | 6 | +3.72 | CS vs Villa |
| Raya | robust XI | 90 | 5.16 | 6 | +0.84 | CS |
| Diop | adv bench | 90 | 1.40 | 2 | +0.60 | Started (not a dead enabler) |
| van Ewijk | adv bench | 90 | 0.92 | 1 | +0.08 | Started; −1 for 3 GC |
| Senesi | robust XI | 90 | 2.97 | 3 | +0.03 | |
| Gabriel | robust XI | 90 | 5.54 | 5 | −0.54 | CS |
| Le Fée | adv XI | 79 | 2.88 | 2 | −0.88 | |
| Van Hecke | adv XI | 90 | 2.36 | 1 | −1.36 | TOT 0-3 |
| Mitchell | adv XI | 90 | 2.56 | 1 | −1.56 | CRY 0-2 |
| Wilson | adv XI | 65 | 4.60 | 3 | −1.60 | Started; no return |
| Dubravka | adv bench | 0 | 1.57 | 0 | −1.57 | start_p 0.76; Kinsky played |
| Shaw | both | 90 | 2.81 | 1 | −1.81 | HUL 2-0 |
| Truffert | robust XI | 90 | 2.94 | 1 | −1.94 | |
| Gibbs-White | adv XI | 90 | 4.73 | 2 | −2.73 | |
| Rice | robust XI | 67 | 5.75 | 3 | −2.75 | |
| Anderson | robust XI | 62 | 5.21 | 2 | −3.21 | |
| Semenyo | robust XI | 90 | 6.22 | 2 | −4.22 | 90, no return |
| Bruno | both C | 90 | 7.20 | 2 | −5.20 | Hull away blank |
| Haaland | adv XI | 90 | 7.47 | 2 | −5.47 | 90, xG 0.74, no goal |
| Thiago | adv XI | 82 | 5.60 | 0 | −5.60 | Missed pen (−2) |

Union MAE on 24 completed players: **2.55**. Starts: high start_p players mostly did start. Failures: Dubravka 0.76→0 mins; Diop/van Ewijk low start_p but 90 mins.

## Engine read (not a team change)

- Minutes/start was the better half. Points/returns were too high on premiums (Haaland, Bruno, Semenyo, Thiago) and too low on DefCon/set-piece variance (Xhaka, Guéhi).
- Thiago 0 is a penalty-miss, not a minutes miss (82, xG 1.00).
- Treating Diop/van Ewijk as non-playing BB blockers was wrong on minutes, right on points.
- Xhaka 9 on the bench is the advisory’s main structural leak this week.
- Robust lead (36 vs 22) is mostly Guéhi 10 + Raya/Gabriel CS, not “Haaland-out was right on Haaland” — Haaland and Bruno both scored 2.

Do not promote GW1 actuals raw into GW2 EP (live-faithful shrinkage policy).

## Calibration note (do not retune from this week)

On the **two 15s** (n=24 completed): our mean GW1 EP was **3.76**, official `ep_next` on 20 Aug was **2.37**, actual **2.71**. We ran **+1.39** hotter than official on the assets we picked. Official was slightly *low* vs actual.

On the **whole T-24h market** (n=426 completed): our mean 1.86 vs official 1.84 vs actual 2.00. Bias and MAE are essentially the same as FPL’s own EP. This is not a global “turn EP down” result.

The heat is in the **premium tail**: Haaland 7.47 vs official 4.00 (actual 2, xG 0.74); Bruno 7.20 vs 4.00 (actual 2, xGI 0.34); Semenyo 6.22 vs 2.90 (actual 2, xGI 0.08). Thiago 5.60 vs 2.50 with xGI 1.08 and a missed pen is unkind, not a miss on minutes.

Do not change live-faithful weights from n=1. For GW2, let existing shrinkage run, then compare the new packet’s premium EP to official `ep_next` as a diagnostic only.

## Owner stance (2026-08-24T16:27Z)

Logged from the GW2 process / weighting discussion. **No change to the live 15.** Do not retune model weights from this week. Results were mixed luck and some hot premiums — not a reason to haircut the whole engine.

### What GW2 processing already does

Live-faithful shrinks GW1 points toward last season’s prior. A 2-point Haaland does not become 2 next week; Xhaka’s 9 does not become 9. Minutes and starts update faster than returns. That is the intended GW2 move: let the existing process run, then **rescore this same 15** on the new packet.

### Are EPs too high?

- Whole market: no. n=426 completed T-24h players: our mean 1.86, official `ep_next` 1.84, actual 2.00.
- Selected two 15s: yes at the **top of the list**. Mean our EP 3.76 vs official 2.37 vs actual 2.71 (~+1.4 vs official).
- That heat is the ClubElo+Understat premium tail (same lift as T-48h 238 → T-24h 261). Relative ranks can still be useful. Treat 7-point premiums as optimistic until the GW2 packet is compared to official `ep_next` again.

### What to weight into GW2 — judgement, not a code change

1. **Minutes / starts first.** Dubravka 0.76→0 mins and Diop/van Ewijk actually starting are the clean process misses. Those should move GW2 EP via the existing start-shrink.
2. **Returns second, and shrink them.** Do not sell Haaland or Bruno because they scored 2. Do not promote Xhaka because he scored 9.
3. **Official EP as a sense-check**, not a new model. If the next packet still has Haaland at 7 vs official 4, that is a later calibration question, not a Monday knob.
4. **No new source weights** (ClubElo, DefCon, odds) from one Gameweek.

### Review process this week

1. Tonight + bonus lock → final official `event/1/live`. Never write it into T-24h.
2. New GW2 live-faithful packet with GW1 shrunk in.
3. Host rescores this same 15 (and the robust comparator).
4. Strategy briefing may argue transfers; owner approves. No account writes.

Change the 15 only if Friday pressers kill minutes, not because GW1 felt cold. If after the new packet the side is still legal and premiums have come back toward official, hold.
