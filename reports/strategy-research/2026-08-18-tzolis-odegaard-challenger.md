# Tzolis-in / Ødegaard-in challenger host-score — 2026-08-18

- observed_at: 2026-08-18
- role: scoped challenger research (not a new daily strategy run)
- bound_packet_sha256: `65eba1feb8c6f6f9707789e0cbf6533baf9fdffa57ac872e10b8bc6badcd3651`
- packet_binding_status: **hash identified; packet body missing**
- bound packet summary: `reports/strategy-research/packets/weekly-2026-08-11.json`
- live checkpoint: `reports/live/2026-27/initial-squad/weekly-2026-08-11/` (gitignored; absent on this clone)
- host API: `score_declared_initial_squad` (`src/optimisation/initial_squad.py`)
- policy: `control/policies/initial-squad-2026-27.json`
- rules: `control/rules/2026-27.yaml`
- helper: `scripts/compare_tzolis_odegaard_challenger.py` (fails closed until the live packet is restored)
- account_writes: false
- owner approval: still required

This is a same-packet challenger rescore of the held 18 August Haaland-in advisory 15. It does not re-open Haaland-in, Bruno captaincy, Kinsky, Timber-starts-GW1, Gómez-as-template, or chip timing.

## Blocker

The committed packet summary **binds** SHA `65eba1fe…` on `recommendation.input_packet_sha256`, but it is a derived decision surface only. `scripts/publish_decision_packet_summary.py` and ADR-0027 exclude raw EP vectors and fixture audits. The summary `note` states that the full input packet remains local-only.

This clone has no `reports/live/` checkpoint and no `input-packet.json`. The summary cannot be reconstructed into a legal `validate_initial_squad_packet` object without inventing six-GW `expected_points` / `start_probability` / `uncertainty` vectors. Per the freeze rule, **no host score was computed and no EP was invented**.

`checkpoint.input_packet_sha256` in the same summary file is the older midday seal `c37b904f…`. Later briefings, the 12 August Haaland-in comparison, and the 12 August declared-15 host-score all bind `65eba1fe…`. That later body is what this run must use.

**Do not treat current official `ep_next` as packet EP.**

## Resolved identities

### From the bound packet summary (no EP vectors)

The summary lists 43 selected / alternative players from the robust and deterministic arms. Tzolis, Ødegaard, Xhaka and Haaland are **not** among those 43 — they were outside the no-Haaland arm 15s and their one-for-one screens. That is not proof they are absent from the full packet.

| player | packet summary player_id | packet summary now_cost | packet summary GW1 EP / start_p |
|---|---|---:|---|
| Wilson (Harry, Leeds MID) | `260` | £6.5m | not in summary body |
| E.Le Fée | `542` | £6.0m | not in summary body |
| Xhaka | **not in summary** | — | — |
| Tzolis | **not in summary** | — | — |
| Ødegaard | **not in summary** | — | — |

Previously quoted packet GW1 figures from bound-packet briefings (not re-read from the packet body today):

| player | quoted GW1 EP | quoted GW1 start_p | quote source |
|---|---:|---:|---|
| Wilson | `3.67` | `0.7342` | `reports/strategy-research/2026-08-18.md` |
| E.Le Fée | `3.88` | `0.7615` | `reports/strategy-research/2026-08-17.md` |
| Xhaka | not quoted | `0.7406` | `reports/strategy-research/2026-08-18.md` |
| Tzolis | unknown | unknown | — |
| Ødegaard | unknown | unknown | — |

### Current official bootstrap (identity / price only; not packet)

Fetched 2026-08-18 from the registered endpoint `https://fantasy.premierleague.com/api/bootstrap-static/` (source `fpl-official-endpoints`). Body SHA-256 `f7001dc5a4bd36cd936e4b3227de9111fd44dd55f98bc92d5379addf5cb55b5b` (not committed). Used only to confirm names, FPL ids and **current** prices. Current `ep_next` is ignored for scoring.

| player | full name | web_name | player_id | pos | club | current now_cost | status |
|---|---|---|---:|---|---|---:|---|
| Tzolis | Christos Tzolis | Tzolis | 557 | MID | Arsenal | £6.5m | `a` |
| Ødegaard | Martin Ødegaard | Ødegaard | 15 | MID | Arsenal | £6.5m | `a` |
| Wilson | Harry Wilson | Wilson | 260 | MID | Leeds | £6.5m | `a` |
| E.Le Fée | Enzo Le Fée | E.Le Fée | 542 | MID | Sunderland | £6.0m | `a` |
| Xhaka | Granit Xhaka | Xhaka | 544 | MID | Sunderland | £5.5m | `a` |

Wilson is unambiguous in the packet summary as id `260`. Current bootstrap also has Callum Wilson (108, FWD, Brentford) and Ben Wilson (172, GKP, Coventry) — those are not the advisory midfielder.

Tzolis and Ødegaard identities are unambiguous on the current official list (one MID each at Arsenal). **Packet presence, packet price and packet GW1 EP / start_p remain unconfirmed.** If the restored packet omits either name, that challenger stops.

Community £4.5m Tzolis talk is not used. Current official price is £6.5m.

## Official citations used (Lane A)

Community / X chatter is why these names were checked. It is not ledger evidence and was not written into the availability ledger.

| URL | what it shows | published_at |
|---|---|---|
| https://www.arsenal.com/news/team-news-guimaraes-and-tzolis-start-community-shield-aGP3h9S4sdjJ | Official CS team news: Tzolis and skipper Martin Odegaard both start. XI includes Tzolis (left wing) and Odegaard. Saka / Rice / Zubimendi on the bench ahead of Friday vs Coventry. | `2026-08-16T12:45:22Z` (already-admitted discovery / ledger metadata; same URL as 18 Aug news-discovery, not the `aGP3hS4sdjJ` typo variant) |
| https://www.arsenal.com/news/report-arsenal-3-0-manchester-city-axOZ78a0LKZm | Official CS match report: Tzolis two assists; Odegaard scored the third (2' after restart), 55/58 passes, 3/3 dribbles, 9 possessions won. GW1 vs Coventry next. | unknown from this fetch |
| https://www.arsenal.com/feature/arsenal-analysed-how-the-community-shield-was-secured-aGfVG9A3KhDB | Official club analysis: Odegaard “looking very sharp ahead of Friday’s big kick-off”; Tzolis “looks almost certain to be in our starting XI against Coventry City on Friday night.” | unknown from this fetch |
| https://www.arsenal.com/news/arteta-delighted-with-our-flying-start-to-the-season-a3A0K7F66PiJ | Arteta on Tzolis / Guimaraes debuts; Odegaard lifted the Shield; recover for Coventry Friday. | unknown from this fetch |
| https://www.arsenal.com/news/every-word-artetas-post-community-shield-presser-aATrq4Y4fosW | Arteta: Tzolis “decisive” in the last 20–30m; Odegaard missed five or six months last year, “if we can maintain him fit… a very different Martin.” | unknown from this fetch |
| https://fantasy.premierleague.com/api/bootstrap-static/ | Current official identities / prices / `status=a` for the five names above. No GW1 XI. | observed 2026-08-18 |

No current official Arsenal GW1 team sheet or Friday press-conference XI was found. CS start plus Arteta / club-analysis language is minutes *context*, not a packet start_p edit and not a host-score input.

No ledger ingest was run. No account writes.

## Current advisory 15 (baseline)

Held 18 August 15 from `reports/strategy-research/2026-08-18.md`:

Verbruggen, Dubravka; Van Hecke, Mitchell, Shaw, Diop, van Ewijk; B.Fernandes, Gibbs-White, E.Le Fée, Wilson, Xhaka; Haaland, João Pedro, Thiago.

Declared advisory usage: 3-4-3; Bruno (C), Haaland (VC); bench Dubravka / Xhaka / Diop / van Ewijk; £99.5m / bank £0.5m (bootstrap).

### Host scores on this run

| mode | objective | bank | proposal SHA-256 | validation.ok | GW1 XI / C / VC / bench |
|---|---:|---:|---|---|---|
| human_reference | **blocked** | — | — | — | — |
| robust | **blocked** | — | — | — | — |
| deterministic | **blocked** | — | — | — | — |

### Prior same-packet host score (12 Aug; not re-run)

`reports/strategy-research/2026-08-12-declared-15-host-score.md` already scored **this same 15** on packet `65eba1fe…`:

| mode | objective | bank | host-optimal GW1 |
|---|---:|---:|---|
| robust | `215.705381` | `0.5` | C/VC B.Fernandes / Gibbs-White; XI Verbruggen, Shaw, Van Hecke, Mitchell, B.Fernandes, Gibbs-White, E.Le Fée, Wilson, Haaland, João Pedro, Thiago; bench Dubravka, Xhaka, Diop, van Ewijk; 3-4-3 |
| deterministic | `220.007893` | `0.5` | not separately listed |
| human_reference | not recorded | — | — |

Those figures are a prior artefact, not this run’s rescore. They cannot be used as a substitute delta for the challengers.

## Challenger 15s

Funding constraint: drop only from {Wilson, E.Le Fée, Xhaka}. Keep Haaland, Bruno and the playing DEFs. Keep 2 GKP / 5 DEF / 5 MID / 3 FWD, ≤ £100m, max 3 per club. One extra cheap like-for-like MID bench enabler only if budget/position legality requires it.

Current official prices (not packet): Tzolis £6.5m, Ødegaard £6.5m. Wilson £6.5m is cost-neutral; E.Le Fée £6.0m plus the £0.5m bank is exact; Xhaka-only (£5.5m) is £1.0m short at current prices and would need a second funding drop plus a cheap MID filler. The advisory 15 has zero Arsenal players, so one or two Arsenal MIDs stay inside the club-3 cap.

**Neither 15 was declared to the host scorer.** Construction below is the intended legal shape once the packet body is restored; packet prices may forbid it.

### Tzolis-in

- Intended 15 (current-price sketch): drop Wilson (`260`); add Tzolis (`557`); keep the other 14 including Haaland and Bruno.
- XI / C / VC / bench: not host-chosen.
- Bank / validation / proposal SHA: blocked.
- Host scores and delta vs baseline: blocked.
- Stop condition if restored packet: missing/ambiguous `Tzolis`, or no legal funding path from {Wilson, E.Le Fée, Xhaka}.

### Optional Ødegaard-in

- Intended 15 (current-price sketch): drop Wilson (`260`); add Ødegaard (`15`); keep the other 14 including Haaland and Bruno.
- XI / C / VC / bench: not host-chosen.
- Bank / validation / proposal SHA: blocked.
- Host scores and delta vs baseline: blocked.
- Stop condition if restored packet: missing/ambiguous `Ødegaard`, or no legal funding path from the same pool.

A combined Tzolis **and** Ødegaard 15 was not requested.

## Host-score table

| side | human_reference | robust | deterministic | bank | notes |
|---|---:|---:|---:|---:|---|
| Current advisory 15 (this run) | blocked | blocked | blocked | — | packet body missing |
| Tzolis-in | blocked | blocked | blocked | — | not scored |
| Ødegaard-in | blocked | blocked | blocked | — | not scored |
| Current advisory 15 (12 Aug prior, same SHA) | n/a | 215.705381 | 220.007893 | 0.5 | prior artefact only |

## Verdict

Neither challenger can be shown to beat the current advisory 15 on `human_reference` or `robust`. Official CS evidence supports availability for both Arsenal mids, but that is not a host delta.

## Recommendation

**Keep the current 15.** Wait for the GW1 presser / official Arsenal XI, and restore the live `weekly-2026-08-11` input-packet (SHA `65eba1fe…`) before any adopt/reject call. Do not change the live advisory briefing on CS buzz or current `ep_next`.

Re-run: `python3 scripts/compare_tzolis_odegaard_challenger.py` once `reports/live/2026-27/initial-squad/weekly-2026-08-11/input-packet.json` is present and hashes to `65eba1fe…`.

- account_writes: false
