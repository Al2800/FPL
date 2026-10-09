# Live-entry decision input — 2026-10-09

- observed_at: 2026-10-09T08:02:10Z
- official FPL snapshot observed_at: 2026-10-09T07:01:05Z
- next_deadline: 2026-10-10T10:00:00Z (11:00 BST)
- entries: 8522487 (Haaland arm), 7337262 (no-Haaland arm)
- method: `docs/plan.md`; point-in-time official FPL and dated club evidence first; community sources are challenge inputs only
- account writes: false
- manager state: live_faithful_degraded

## Decision

There is **no material transfer, chip or captaincy change this morning**. Do not make an early transfer on either entry. The two most decision-relevant press conferences remain after this cutoff: Liverpool's pre-Manchester City briefing is scheduled for 13:30 BST today, and Manchester City's briefing is also today. A post-presser pass is mandatory before the deadline.

The 09 October official-news run admitted three Leeds claims (Harry Wilson doubtful after returning to training, Daniel James unavailable and Jean-Mattéo Bahoya doubtful). None of those players is owned. The owned Isak doubtful claim and Haaland available claim remain active.

## Public official state

GW5 is final and data checked. No chip has been used by either entry.

| entry | arm | GW5 | total | current OR | sampled top-1k gap | last-deadline value | last-deadline bank |
|---|---|---:|---:|---:|---:|---:|---:|
| 8522487 | Haaland | 51 | 292 | ~5.20m | 122 | £99.6m | £0.2m |
| 7337262 | no Haaland | 43 | 291 | ~5.32m | 123 | £99.8m | £0.0m |

The sampled overall top-1,000 boundary remains 414 points. Public endpoints expose completed picks, transfers, chips, total points, rank and last-deadline value/bank, but not current free transfers, pending transfers, purchase prices or selling prices. Do not infer those private fields.

Completed transfer history:

- 8522487: Wilson to Dewsbury-Hall in GW4; Shaw to Castagne in GW5.
- 7337262: Beto to Isak, Bruno Fernandes to Palmer and Senesi to Maatsen in GW4; Maatsen to Castagne in GW5.

## Current official FPL flags and prices

No owned price or flag change was captured between the 08 and 09 October morning snapshots.

### 8522487

| player | price | status | current implication |
|---|---:|---|---|
| Verbruggen | £4.5m | available | start |
| Dubravka | £4.0m | available | reserve GK |
| Van Hecke | £4.9m | 75%, foot | bench pending Spurs update |
| Mitchell | £4.5m | available | start |
| Castagne | £4.5m | available | start |
| Diop | £4.0m | available | start |
| van Ewijk | £4.0m | 75%, hamstring | third outfield substitute |
| Bruno Fernandes | £11.9m | available | start, vice-captain |
| Gibbs-White | £8.0m | available | start |
| Le Fée | £5.7m | available | start |
| Dewsbury-Hall | £6.6m | available | start |
| Xhaka | £5.5m | available | start unless João Pedro is cleared |
| Thiago | £7.8m | available | start |
| Haaland | £15.6m | available | start, captain |
| João Pedro | £7.7m | 75%, knee | first substitute; start for Xhaka only after normal-minutes clearance |

### 7337262

| player | price | status | current implication |
|---|---:|---|---|
| Raya | £6.1m | available | start, vice-captain |
| Verbruggen | £4.5m | available | reserve GK |
| Gabriel | £8.0m | available | start |
| Guéhi | £6.0m | available | start |
| Castagne | £4.5m | available | start |
| Shaw | £4.3m | available | first substitute |
| Truffert | £5.4m | available | second substitute |
| Palmer | £9.7m | 75%, muscular | start if cleared; captain only with normal-minutes clearance |
| Rogers | £7.8m | available | start, provisional captain |
| Semenyo | £8.4m | 75%, ankle | start if cleared |
| Rice | £7.4m | 75%, unspecified | start if cleared |
| Anderson | £6.3m | available | start |
| Isak | £9.1m | 75%, thigh | high blank/cameo risk; 13:30 Liverpool update is mandatory |
| João Pedro | £7.7m | 75%, knee | start only with clearance |
| Obi | £4.5m | unavailable, loan | third substitute; not a hit-worthy repair alone |

## Provisional GW6 teams

### 8522487 — Haaland arm

**XI (3-5-2):** Verbruggen; Mitchell, Castagne, Diop; Bruno Fernandes, Gibbs-White, Le Fée, Dewsbury-Hall, Xhaka; Thiago, Haaland.

- Captain: **Haaland**
- Vice-captain: **Bruno Fernandes**
- Bench: Dubravka; **1 João Pedro, 2 Van Hecke, 3 van Ewijk**
- If Chelsea clears João Pedro for normal minutes, start him and bench Xhaka.
- If Spurs clears Van Hecke for a normal start, compare him with Diop; do not automatically prefer the flagged defender.
- Transfer/chip: **zero now; no chip**. The public data does not verify the free-transfer count, so record this as “hold” rather than “roll one”.

### 7337262 — no-Haaland arm

Conditional on the five doubtful attackers/midfielders receiving adequate clearance:

**XI (3-5-2):** Raya; Gabriel, Guéhi, Castagne; Rogers, Palmer, Semenyo, Rice, Anderson; João Pedro, Isak.

- Captain: **Rogers** while Palmer remains flagged
- Vice-captain: **Raya**
- Bench: Verbruggen; **1 Shaw, 2 Truffert, 3 Obi**
- If Palmer receives a normal-minutes clearance, switch to **Palmer captain, Rogers vice-captain**.
- If exactly one of João Pedro or Isak is unavailable, start Shaw and use a 4-5-1.
- If both João Pedro and Isak are ruled out, a forward transfer becomes the priority because the squad otherwise cannot field a credible playing forward.
- If at least three genuine XI holes remain after the pressers, rerun free-transfers-versus-Wildcard. Do not activate Wildcard from flags alone.
- Transfer/chip: **zero now; no chip**.

## Evidence and freshness

| evidence | published_at | observed_at | treatment |
|---|---|---|---|
| Official FPL bootstrap, entry, history, picks and standings | mutable | 2026-10-09T07:01:05Z | authoritative structured state |
| Liverpool: Isak and Gakpo injured, recovery for City uncertain | 2026-10-07T14:59:00Z | 2026-10-09T08:02:10Z | accepted, retained; Friday presser can falsify |
| Liverpool: pre-City presser scheduled 13:30 BST | 2026-10-09 | 2026-10-09T08:02:10Z | schedule only; no fitness conclusion yet |
| Chelsea: João Pedro was expected back after the international break | before the break | 2026-10-09T08:02:10Z | supportive but stale; not a current clearance |
| Chelsea: 08 October training gallery | 2026-10-08T15:53:45Z | 2026-10-09T08:02:10Z | names other players, not Pedro/Palmer; not clearance |
| Manchester City: Haaland returned after three goals in four Norway matches and discussed Liverpool | 2026-10-08T15:00:00Z | 2026-10-09T08:02:10Z | soft available corroboration, not minutes guarantee |
| Leeds Farke update: Wilson/James/Bahoya | 2026-10-08T13:30:00Z | 2026-10-09T07:01:05Z | accepted; no owned effect |
| 08 October X community digest | 2026-10-08T08:05:00Z | 2026-10-09T08:02:10Z | challenge input only |

Rejected as decision evidence: an unsourced fan claim that João Pedro trained; a misattributed community claim that Isak and Gakpo needed late tests; price-change trackers as proof of official price movement; Wildcard drafts without verified manager state; and community captain polls without a current minutes model.

## Rolling four-Gameweek direction

- **GW6:** no early move or chip; make the final decision only after Chelsea, Liverpool, Manchester City, Arsenal, Spurs and Manchester United updates. The no-Haaland entry's forward availability is the main transfer trigger.
- **GW7:** Manchester City versus Ipswich is the planned Haaland captain anchor. Triple Captain remains a comparison, not a commitment. On 7337262, price the route to Haaland only after authenticated free transfers and selling prices are known.
- **GW8–GW9:** preserve transfer flexibility around Palmer, Bruno, João Pedro and the premium-forward structure. Avoid spending transfers on healthy bench depth while the two-forward availability problem is unresolved.
- Wildcard threshold: at least three persistent structural holes or a clearly superior four-Gameweek rebuild after exact private manager state is supplied. Free Hit and Bench Boost have no current case.

## Required private confirmation before final moves

Open each authenticated transfer page and record: current free transfers, bank, pending transfers, every proposed sale price and the post-transfer bank. Without those fields, manager state remains degraded and no transfer plan should be described as executable.
