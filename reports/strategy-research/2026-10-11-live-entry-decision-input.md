# Live-entry decision input — 2026-10-11

- observed_at: 2026-10-11T07:02:58Z
- next_deadline: 2026-10-17T10:00:00Z (GW7) — GW6 scoring still open
- scope: public entries 8522487 and 7337262
- governing method: `docs/plan.md`; official FPL entry data is authoritative for completed squads, picks, transfers and scoring; dated club sources are authoritative for availability evidence
- account writes: false
- decision state: live_faithful_degraded
- companion advisory: `reports/strategy-research/2026-10-11.md` (reconstructed 15 is **not** either owned squad)

## Executive decision

**Haaland arm (8522487):** GW6 deadline locked with **Haaland (C) / Bruno (VC)** and Van Hecke started — keep that leadership for remaining fixtures (Mitchell, Gibbs-White, Dewsbury-Hall, Haaland still live). **No chip**. Into GW7: prefer **roll until after Anfield**, then consider **1 FT** toward Groß (fund from Dewsbury-Hall or E.Le Fée) only if Cherki-equivalent blank pressure appears; **reject Schade** (`model:e63a6717…` doubtful). Keep **Haaland (C)** vs IPS (H). Do not treat advisory Bruno (C) as an owned correction — ownership already chose Haaland (C).

**No-Haaland arm (7337262):** Isak remains ledger **unavailable** (`model:abd411a7…`) / bootstrap `i` for City — expect blank; **João Pedro** (already played) is the autosub cover. Palmer (C) / Rogers (VC) locked. Semenyo still `d`/75% into Anfield. Obi is **loan unavailable** (`u`) — dead bench slot. Into GW7: **priority FT Isak → active FWD** (not Schade while doubtful); second structural problem is Obi — WC pressure rises if Semenyo also fails clearance. Reject default WC only if owner can repair Isak+Obi with ≤2 FTs without wrecking Arsenal/Chelsea spine.

## Official entry state

GW6 is current (`is_current`); Saturday fixtures started/scored; Sunday/Monday remain. Sampled this morning:

| entry | arm | GW6 pts (live) | total | current OR |
|---|---|---:|---:|---:|
| 8522487 | Haaland | 31 | 323 | ~5.56m |
| 7337262 | no Haaland | 49 | 340 | ~4.33m |

| entry | bank (event hist) | chips used | GW6 transfers |
|---|---:|---|---:|
| 8522487 | £0.2m | none | 0 |
| 7337262 | £0.0m | none | 0 |

Public endpoints do not expose current free transfers, pending transfers, purchase prices or selling prices. Manager state remains degraded.

## Authoritative squads, prices and flags (morning bootstrap)

### 8522487 — Haaland arm (GW6 picks)

| role | player | club | price | status | note |
|---|---|---|---:|---|---|
| GK | Verbruggen | BHA | 4.5 | a | XI |
| DEF | Van Hecke | TOT | 4.9 | a 100% | XI — tip retained |
| DEF | Mitchell | CRY | 4.5 | a | XI — still to play Forest (H) |
| DEF | Castagne | FUL | 4.5 | a | XI — played Sat |
| MID | B.Fernandes | MUN | 11.9 | a | **VC** — played Sat |
| MID | Gibbs-White | NFO | 8.0 | a | XI — still to play Palace (A) |
| MID | E.Le Fée | SUN | 5.7 | a | XI — played Sat |
| MID | Dewsbury-Hall | EVE | 6.6 | a | XI — still to play Hull (A) Sun |
| FWD | João Pedro | CHE | 7.7 | a 100% | XI — played Sat |
| FWD | Thiago | BRE | 7.8 | a | XI — played Sat |
| FWD | Haaland | MCI | 15.6 | a | **(C)** — still to play LIV (A) |
| BEN | Dubravka | TOT | 4.0 | a | |
| BEN | Xhaka | SUN | 5.4 | a | |
| BEN | Diop | IPS | 4.0 | a | |
| BEN | van Ewijk | COV | 4.0 | d 75% | hamstring |

### 7337262 — no-Haaland arm (GW6 picks)

| role | player | club | price | status | note |
|---|---|---|---:|---|---|
| GK | Raya | ARS | 6.1 | a | XI — played Sat |
| DEF | Gabriel | ARS | 7.9 | a | XI — played Sat |
| DEF | Castagne | FUL | 4.5 | a | XI — played Sat |
| DEF | Guéhi | MCI | 6.0 | a | XI — still to play LIV (A) |
| MID | Rogers | CHE | 7.8 | a | **VC** — played Sat |
| MID | Palmer | CHE | 9.7 | a 100% | **(C)** — played Sat |
| MID | Semenyo | MCI | 8.4 | d 75% | ankle — still to play LIV (A) |
| MID | Rice | ARS | 7.3 | a 100% | XI — played Sat (bootstrap cleared vs prior `d`) |
| MID | Anderson | MCI | 6.3 | a | XI — still to play LIV (A) |
| FWD | João Pedro | CHE | 7.7 | a 100% | XI/autosub cover — played Sat |
| FWD | Isak | LIV | 9.0 | i 0% | **unavailable** tip — expect blank |
| BEN | Verbruggen | BHA | 4.5 | a | |
| BEN | Truffert | BOU | 5.4 | a | |
| BEN | Shaw | MUN | 4.3 | a | |
| BEN | Obi | MUN | 4.5 | u 0% | loan — dead slot |

## Recommended owned actions (advisory only)

### Remaining GW6 (no transfers possible)

- **8522487:** leave locked XI/C/VC; watch Haaland minutes at Anfield; Mitchell/MGW/DH still to play.
- **7337262:** leave locked Palmer (C); accept Isak blank → Pedro cover; Semenyo/Guéhi/Anderson Anfield minutes risk.

### Toward GW7 (after GW6 finalises)

- **8522487:** Haaland (C) vs IPS (H); FT shortlist Dewsbury-Hall/E.Le Fée → Groß; reject Schade; reject Semenyo; TC only if Anfield confirms full Haaland go.
- **7337262:** FT1 Isak → active FWD (Pedro already owned — prefer non-Schade); plan Obi repair (FT2 or WC); do not buy Schade while `model:e63a6717…` doubtful; Semenyo hold only if cleared.

## Falsifiers

- Haaland rested/limited at Anfield or for Ipswich
- Schade cleared + nailed before Groß FT
- Isak surprise return into City (unlikely given tip + bootstrap `i`)
- Owner already used WC/TC overnight (public chip field still null this morning)

## Host handoff

- Account writes: false
- Owner approval still required
- Companion review: `reports/evidence-review/2026-10-11-live-entry-review.md`
