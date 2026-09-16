# Live-entry decision input — 2026-09-16

**Status:** provisional advisory; hold transfers pending midweek matches and Friday press conferences; no account changes executed  
**Observed at:** 2026-09-16T07:22:31Z  
**Next deadline:** 2026-09-18T17:30:00Z (18:30 UK)  
**Entries:** 8522487 and 7337262  
**Governing method:** `docs/plan.md`; official FPL state is authoritative for squad and history

## Material correction to the same-day strategy report

The report `reports/strategy-research/2026-09-16.md` is not safe to use as live manager state. It says entry 8522487 contains Kinsky, Cherki and Wissa and that Wilson plus Thiago became Cherki plus Wissa in GW4. Official entry history instead records one GW4 transfer, Wilson to Dewsbury-Hall. The completed-GW4 squad still contains Dubravka and Thiago, and does not contain Kinsky, Cherki or Wissa. The report also omits entry 7337262.

The same-day report is bound to `weekly-2026-08-11`, so its deterministic and robust comparisons are not current GW5 comparisons. Its phrase “midweek cups largely complete” is also false at the observation time: important matches remain before the deadline. Do not promote its squad reconstruction or derived recommendation into the evidence ledger.

## Official state

| Entry | GW4 | Total | Overall rank | Team value | Bank | GW4 transfers | Chips |
|---|---:|---:|---:|---:|---:|---:|---|
| 8522487 | 61 | 241 | about 5.54m | £99.4m | £0.3m | 1, no hit | none |
| 7337262 | 67 | 248 | about 4.91m | £99.6m | £0.0m | 3, no hit | none |

The current top-1,000 cut line is about 359 points, leaving gaps of 118 and 111 points respectively. This is descriptive, not a reason to chase variance in GW5.

Public endpoints do not expose pending transfers, exact current free-transfer counts, purchase prices or selling prices. Manager state is therefore **degraded** until the authenticated transfer pages confirm those fields. Based only on completed history and the transfer-banking rule, entry 8522487 is likely to have three free transfers and entry 7337262 one, provided no GW5 move has already been made. This is an inference, not an observed fact.

## Accepted availability claims

| Claim | Official field or source | Published/added | Decision use |
|---|---|---|---|
| Maatsen is at 25% with an ankle injury | official FPL player status | 2026-09-12 | wait for Friday club update; transfer if ruled out |
| Shaw is at 75% with an unspecified injury | official FPL player status | 2026-09-11 | do not rely on him for the provisional XI |
| Obi is unavailable after joining Willem II on loan | official FPL player status | 2026-09-14 | permanent dead third-bench slot |
| Gomez and Gakpo started the midweek cup match; Porro was available; Udogie started; Tonali was doubtful | official club reports cited in the daily evidence review | 2026-09-15/16 | peripheral to the two live squads |

No fresh, time-stamped official Manchester City, Manchester United, Chelsea or Aston Villa press-conference evidence was found in this run. Thursday match minutes and Friday press conferences remain the main availability unlocks.

## Rejected or quarantined claims

- The reconstructed Kinsky, Cherki and Wissa manager state is rejected because it conflicts with official entry history.
- “Catalogue coverage 21/21” describes attempted searches, not evidence coverage. The discovery output had time-bounded official leads for only three clubs.
- Community injury, price, projection and captain claims are discovery or challenge inputs only. None has been promoted to official evidence here.
- Unverified pending transfers, free transfers, purchase prices and selling prices are not stated as facts.

## Provisional GW5 decisions

### Entry 8522487 — Haaland structure

**Current action: make no early transfer.** Wait through the remaining cup matches and Friday press conferences. If no adverse news emerges, rolling all likely three free transfers is preferred. Thiago has only five FPL points but strong underlying involvement and reliable minutes, so Thiago to Wissa is a comparison candidate, not an automatic move. Keep Dewsbury-Hall for Ipswich at home.

The main Friday contingency is an injured-defender correction. If Shaw is ruled out, compare Shaw to Bogle and Shaw to Ola Aina using fresh GW5–GW8 minutes and projections, then confirm the authenticated selling price. If Shaw is fit and likely to start, roll.

**Provisional XI:** Verbruggen; Van Hecke, Mitchell, Diop; Bruno Fernandes, Gibbs-White, Dewsbury-Hall, Le Fée; Haaland, João Pedro, Thiago  
**Bench:** Dubravka; Xhaka, van Ewijk, Shaw  
**Captain:** Haaland  
**Vice-captain:** Bruno Fernandes

### Entry 7337262 — no-Haaland structure

**Current action: make no early transfer.** Wait for official Maatsen news and the remaining cup minutes.

- If Maatsen is ruled out or remains a serious minutes doubt, Maatsen to Bogle is the clean one-free-transfer priority, subject to authenticated sale-price confirmation.
- If Maatsen is explicitly fit and expected to start, rolling is defensible.
- Do not take a hit solely to remove Obi. He is unavailable but can remain third outfield substitute for one week.

**Provisional XI if Maatsen becomes Bogle:** Raya; Gabriel, Guéhi, Bogle; Rogers, Palmer, Semenyo, Rice, Anderson; João Pedro, Isak  
**Bench:** Verbruggen; Truffert, Shaw, Obi  
**Captain:** João Pedro  
**Vice-captain:** Palmer

João Pedro leads the current official next-match estimate, while Palmer retains penalties and a strong route to points. Reassess after Friday team news and independent projections.

## Rolling four-Gameweek plan

- **GW5:** maximise expected points; do not use a chip; do not chase the early top-1,000 gap.
- **GW6:** the international break increases the value of banked transfers. Prefer rolling unless new availability evidence forces action. On the Haaland side, João Pedro at home to Bournemouth or Bruno at home to Spurs are captain alternatives. On the no-Haaland side, repair Obi only if no higher-value move emerges.
- **GW7:** Haaland at home to Ipswich is the likely captain anchor. Reassess a Haaland route for entry 7337262, but do not force a multi-transfer restructure unless fresh expected-value work supports it.
- **GW8:** preserve flexibility around João Pedro, Bruno, Palmer and the fixture swing rather than pre-committing now.

## Friday hard checks

1. Confirm each account's exact free transfers, bank and selling prices in the authenticated transfer page.
2. Refresh official FPL status, chance-of-playing, price and news timestamps.
3. Capture remaining cup minutes and official post-match updates, especially City and Palace assets.
4. Review official club press conferences for City, United, Chelsea, Aston Villa, Brighton, Brentford, Leeds, Palace and Forest.
5. Rerun GW5–GW8 expected minutes, transfers, XI, bench and captaincy from the actual squads.
6. Validate budget, club limits, formation and bench order deterministically before any human execution.

## Sources

- Official FPL: https://fantasy.premierleague.com/
- Entry 8522487 history: https://fantasy.premierleague.com/en/entry/8522487/history
- Entry 7337262 history: https://fantasy.premierleague.com/en/entry/7337262/history
- Daily evidence draft: https://github.com/Al2800/FPL/pull/89
- Previous X/community digest: https://github.com/Al2800/FPL/blob/main/reports/strategy-research/2026-09-15-x-community-digest.md
