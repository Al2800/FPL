# Live-entry decision input — 2026-09-16

**Status:** provisional advisory; no account changes executed  
**Observed at:** 2026-09-16T07:22:31Z  
**Next deadline:** 2026-09-18T17:30:00Z (18:30 UK)  
**Entries:** 8522487 and 7337262  
**Governing method:** `docs/plan.md`; official FPL state is authoritative for squad and history

## Material correction to the same-day strategy report

The report `reports/strategy-research/2026-09-16.md` is not safe to use as live manager state. It says entry 8522487 contains Kinsky, Cherki and Wissa and that Wilson plus Thiago became Cherki plus Wissa in GW4. Official entry history instead records one GW4 transfer, Wilson to Dewsbury-Hall. The current completed-GW4 squad still contains Dubravka and Thiago, and does not contain Cherki or Wissa.

This correction affects live-entry advice only. The official-source news evidence recovered by the daily pipeline remains useful, subject to its timestamps and scope. Do not promote the incorrect squad reconstruction into the evidence ledger.

## Official state

| Entry | GW4 | Total | Overall rank | Team value | Bank | GW4 transfers | Chips |
|---|---:|---:|---:|---:|---:|---:|---|
| 8522487 | 61 | 241 | about 5.54m | £99.4m | £0.3m | 1, no hit | none |
| 7337262 | 67 | 248 | about 4.91m | £99.6m | £0.0m | 3, no hit | none |

The current top-1,000 cut line is about 359 points, leaving gaps of 118 and 111 points respectively. This is descriptive, not a reason to chase variance in GW5.

Public endpoints do not expose pending transfers, exact current free-transfer counts, purchase prices or selling prices. Manager state is therefore **degraded** until the FPL transfer page confirms those fields. Based only on completed history and the transfer-banking rule, entry 8522487 is likely to have three free transfers and entry 7337262 one, provided no GW5 move has already been made. This is an inference, not an observed fact.

## Accepted availability claims

| Claim | Official field or source | Published/added | Decision use |
|---|---|---|---|
| Maatsen is at 25% with an ankle injury | official FPL player status | 2026-09-12 | immediate transfer candidate |
| Shaw is at 75% with an unspecified injury | official FPL player status | 2026-09-11 | avoid relying on him for the XI |
| Obi is unavailable after joining Willem II on loan | official FPL player status | 2026-09-14 | permanent dead third-bench slot |
| Gomez and Gakpo started the midweek cup match; Porro was available; Udogie started; Tonali was doubtful | official club reports cited in the daily evidence review | 2026-09-15/16 | peripheral to the two live squads |

No fresh, time-stamped official Manchester City, Manchester United, Chelsea or Aston Villa press-conference evidence was found in this run. Friday press conferences remain the main availability unlock.

## Rejected or quarantined claims

- The reconstructed Kinsky, Cherki and Wissa manager state is rejected because it conflicts with official entry history.
- Community injury, price and captain claims are discovery/challenge inputs only. None has been promoted to official evidence here.
- Unverified pending transfers, free transfers, purchase prices and selling prices are not inferred as facts.

## Provisional GW5 decisions

### Entry 8522487 — Haaland structure

If the transfer page confirms three free transfers and the prices are legal:

1. Thiago to Wissa
2. Shaw to Bogle
3. Dubravka to Kinsky

This removes a low-output forward, an injury doubt and a non-playing goalkeeper while preserving the strong midfield. The sequence should be rechecked after Friday press conferences. If only two transfers are available or new official news changes expected minutes, prioritise Thiago to Wissa, then Shaw to a confirmed starting defender.

**XI:** Kinsky; Van Hecke, Mitchell, Bogle; Bruno Fernandes, Gibbs-White, Dewsbury-Hall, Xhaka; Haaland, João Pedro, Wissa  
**Bench:** Verbruggen; Le Fée, Diop, van Ewijk  
**Captain:** Haaland  
**Vice-captain:** João Pedro

### Entry 7337262 — no-Haaland structure

If the transfer page confirms one free transfer and Maatsen can be sold for £4.5m:

1. Maatsen to Bogle

Do not take a hit solely to remove Obi. He is unavailable but can remain third outfield substitute for one week.

**XI:** Raya; Gabriel, Guéhi, Bogle; Rogers, Palmer, Semenyo, Rice, Anderson; João Pedro, Isak  
**Bench:** Verbruggen; Truffert, Shaw, Obi  
**Captain:** João Pedro  
**Vice-captain:** Palmer

The captaincy is provisional. João Pedro leads the current official next-match estimate, while Palmer retains penalties and a strong route to points. Reassess after Friday team news and independent projections.

## Rolling four-Gameweek plan

- **GW5:** maximise expected points; do not use a chip; do not chase the early top-1,000 gap.
- **GW6:** prefer rolling unless new availability evidence forces action. On the Haaland side, João Pedro at home to Bournemouth or Bruno at home to Spurs are captain alternatives. On the no-Haaland side, repair Obi only if no higher-value move emerges.
- **GW7:** Haaland at home to Ipswich is the likely captain anchor. Reassess a Haaland route for entry 7337262, but do not force it if the required multi-transfer restructure destroys more expected value than it creates.
- **GW8:** preserve flexibility around João Pedro, Bruno, Palmer and the fixture swing rather than pre-committing now.

## Friday hard checks

1. Confirm each account's exact free transfers, bank and selling prices in the authenticated transfer page.
2. Refresh official FPL status, chance-of-playing, price and news timestamps.
3. Review official club press conferences for City, United, Chelsea, Aston Villa, Brighton, Brentford and Leeds.
4. Rerun projected minutes and captaincy after the final official news.
5. Validate budget, club limits, formation and bench order deterministically before any human execution.

## Sources

- Official FPL: https://fantasy.premierleague.com/
- Entry 8522487 history: https://fantasy.premierleague.com/en/entry/8522487/history
- Entry 7337262 history: https://fantasy.premierleague.com/en/entry/7337262/history
- Daily evidence draft: https://github.com/Al2800/FPL/pull/89
- Previous X/community digest: https://github.com/Al2800/FPL/blob/main/reports/strategy-research/2026-09-15-x-community-digest.md
