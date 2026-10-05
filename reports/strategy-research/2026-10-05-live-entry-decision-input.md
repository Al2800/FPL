# Live-entry decision input — 2026-10-05

- observed_at: 2026-10-05T07:15:00Z
- next_deadline: 2026-10-10T10:00:00Z (11:00 BST)
- scope: public entries 8522487 and 7337262
- governing method: `docs/plan.md`; official FPL entry data is authoritative for completed squads, picks, transfers and scoring; dated club and association sources are authoritative for availability evidence
- account writes: false
- decision state: live_faithful_degraded
- companion advisory: `reports/strategy-research/2026-10-05.md` (reconstructed 15 is **not** either owned squad)

## Executive decision

There is **no material decision change** and no transfer or chip action today. Official FPL shows no overnight owned-player price or availability change versus the 4 Oct live-entry surface. Lane A run `composer-2.5:2026-10-05T071500Z` admitted **0** claims; tip remains `fdc0e882…`.

**Haaland arm (8522487):** keep **Haaland (C) / Bruno Fernandes (VC)**. City 4 Oct original confirms Haaland played **67'** for Norway vs Portugal — workload observed, not a reason to flip captaincy away from Haaland on this owned arm. Van Hecke remains foot-doubtful — provisional **Diop start / Van Hecke bench**. Do not buy Bogle into ARS (A). João Pedro only enters the XI after a Chelsea normal-minutes clearance.

**No-Haaland arm (7337262):** still carries five 75%-flagged players — Palmer, Semenyo, Rice, Isak and João Pedro — plus Obi unavailable. Keep **Rogers (C) / Raya (VC)** until Palmer receives a normal-minutes clearance. Wildcard / multi-transfer repair remains a final-presser comparison only if ≥3 genuine XI holes persist.

Note: the advisory reconstructed 15 still prefers **Bruno (C) / Haaland (VC)** inside *that* Kinsky/Cherki/Wissa structure; that is **not** an instruction to flip the Haaland arm’s leadership away from Haaland (C).

## Official entry state

GW5 is finished and data checked. Sampled top-1,000 boundary remains **414** from overall standings page-20 (re-polled this morning).

| entry | arm | GW5 | total | current OR | gap to 414 (pts) |
|---|---|---:|---:|---:|---:|
| 8522487 | Haaland | 51 | 292 | ~5.20m | ~122 |
| 7337262 | no Haaland | 43 | 291 | ~5.32m | ~123 |

| entry | last-deadline value | bank | chips used |
|---|---:|---:|---|
| 8522487 | £99.6m | £0.2m | none |
| 7337262 | £99.8m | £0.0m | none |

Completed transfer history remains:

- 8522487: Wilson to Dewsbury-Hall in GW4; Shaw to Castagne in GW5.
- 7337262: Beto to Isak, B.Fernandes to Palmer and Senesi to Maatsen in GW4; Maatsen to Castagne in GW5.

Public endpoints do not expose current free transfers, pending transfers, purchase prices or selling prices. Those fields must not be inferred; manager state remains degraded.

## Authoritative squads, prices and flags

### Entry 8522487

- GKP: Verbruggen £4.5m; Dubravka £4.0m
- DEF: Van Hecke £4.9m (`d`, foot, 75%; FPL `news_added` 2026-09-30T16:00:09Z); Mitchell £4.5m; Castagne £4.5m; Diop £4.0m; van Ewijk £4.0m (`d`, hamstring, 75%)
- MID: B.Fernandes £11.9m; Gibbs-White £8.0m; E.Le Fée £5.7m; Dewsbury-Hall £6.6m; Xhaka £5.5m
- FWD: Thiago £7.8m; Haaland £15.6m; João Pedro £7.7m (`d`, knee, 75%)

### Entry 7337262

- GKP: Raya £6.1m; Verbruggen £4.5m
- DEF: Gabriel £8.0m; Guéhi £6.0m; Castagne £4.5m; Truffert £5.4m; Shaw £4.3m
- MID: Palmer £9.7m (`d`, muscular, 75%); Rogers £7.7m; Semenyo £8.4m (`d`, ankle, 75%); Rice £7.4m (`d`, unspecified, 75%); Anderson £6.3m
- FWD: Isak £9.1m (`d`, thigh, 75%); João Pedro £7.7m (`d`, knee, 75%); Obi £4.5m (`u`, loan, 0%)

## Evidence and freshness

| input | latest usable observation | implication |
|---|---|---|
| official FPL bootstrap / entry endpoints | 2026-10-05T07:15:00Z | no owned price/status change; deadline and public entry state current |
| City Haaland Norway minutes | mancity.com, 2026-10-04T22:00:00Z | Haaland 67' vs Portugal; tip retained; not re-admitted; supports keep Haaland (C) on owned arm |
| Man Utd Portugal victory | manutd.com, 2026-10-02T10:00:00Z | Bruno international corroboration only |
| CPFC Mitchell friendly XI | cpfc.co.uk, 2026-10-03T10:18:46Z | minutes corroboration; already available |
| Spurs Van Hecke | bootstrap foot `d`/75% only; 1 Oct no-travel aged out of 72h gate | keep Diop over Van Hecke |
| governed evidence ledger | tip `fdc0e882…` | 0 admits today |
| decision packet | 2026-08-11 checkpoint | stale for live squads; methodology context only |
| X / community | Pilot Bruno-lean; Copilot Bruno/Saka/Haaland; Bogle projection conflict; Pedro specialist timelines | challenge input only; no claim promoted |

No dated official club publication after the prior cutoff resolves Palmer, Semenyo, Rice, Isak, João Pedro, Van Hecke or van Ewijk. Silence is not a clearance. Unregistered Pedro specialist / Van Hecke toe reports stay briefing-only.

Official FPL’s mutable GW6 estimates include Haaland 8.0, Mitchell 7.7, Van Hecke 5.5, Semenyo 6.5, Guéhi 6.0, Isak 3.8, Bogle 11.3 and Bruno 2.0. Treat these as directional game estimates, not medical evidence.

## Community challenge review

- Palmer KEEP and João Pedro ownership discussion: **defer**; neither resolves expected minutes.
- WC6 drafts: **reject as default**; compare only if ≥3 owned holes survive final pressers.
- Bruno-versus-Haaland captain debate: **retain Haaland (C)** on entry 8522487; Bruno remains vice. Advisory reconstructed-15 Bruno (C) does not override the owned Haaland-arm leadership rule.
- Bogle into ARS (A): **reject** as the GW6 FT despite ep/xPts conflict.
