# 2026/27 FPL ruleset owner review

**Ruleset:** `2026-27-v1.0`
**SHA-256:** `3439006e5ad21d0e497732273ff9b674e599010df98f0104272c53cea6be0c5a`
**Activation blockers:** 0
**Owner status:** approved
**Approved by:** Alastair
**Approved at:** 27 July 2026, 19:01:48 UTC
**Requested scope:** advisory engine use only

Browser execution and FPL account writes remain unapproved regardless of this
decision.

## What was verified

All 39 catalogue rules are now `confirmed`, carry an official Premier League
source, a source publication date and a 27 July 2026 verification date. The
machine activation profile is:

- £100.0m initial budget; 15 players split 2 GKP / 5 DEF / 5 MID / 3 FWD;
  maximum three from one club;
- one free transfer per Gameweek, maximum five banked, four points per excess
  transfer;
- banked transfers retained when Wildcard or Free Hit is used;
- half of a price rise retained on sale, rounded down to £0.1m;
- two sets of Wildcard, Free Hit, Triple Captain and Bench Boost;
- first set expires at the GW19 deadline on 2 January 2027;
- only one chip per Gameweek;
- Wildcard and Free Hit unavailable in GW1; Free Hit cannot be used in both
  GW19 and GW20;
- 38 regular Gameweeks, with the terminal manager state at GW39.

The malformed provisional chip string has been replaced by that structured
boundary. The expiry timestamp year was corrected from 2026 to 2027.

## Official evidence

The current season sources are:

- [FPL Help, 24 July 2026](https://www.premierleague.com/en/news/4681092/fpl-help-copilot):
  current 15-player/£100m overview, starting XI, captaincy, transfers, maximum
  five banked, four-point hits, one chip per Gameweek and two chip sets.
- [FPL live for 2026/27, 23 July 2026](https://www.premierleague.com/en/news/4680722/fpl-is-live-pick-your-202627-squad-now/):
  season launch, £100m budget, five-transfer rollover and no AFCON top-up.
- [2026/27 chips, 20 July 2026](https://www.premierleague.com/en/news/4679879/whats-happening-with-fpl-chips-in-202627):
  two sets, GW19 expiry, one-chip limit, Free Hit boundary and chip effects.
- [Current FPL FAQ, 18 May 2026](https://www.premierleague.com/en/news/4661030):
  selling-price rounding, retained saved transfers, Wildcard/Free Hit transfer
  treatment and current price-change behaviour.
- [2026/27 BPS changes, 20 July 2026](https://www.premierleague.com/en/news/4679946/whats-new-in-202627-fantasy-changes-to-bonus-points-system):
  bonus allocation/ties and the season-specific BPS changes.

The dated 2026/27 Help page links to these maintained official FPL Basics pages,
which were published on 1 July 2025 and remain the detailed rule definitions:

- [How to pick a squad](https://www.premierleague.com/en/news/2174419/fpl-basics-how-to-pick-a-squad)
- [Managing your team](https://www.premierleague.com/en/news/2174899/fpl-basics-managing-your-team)
- [Making transfers](https://www.premierleague.com/en/news/2174907/fpl-basics-making-transfers)
- [Scoring points](https://www.premierleague.com/en/news/2174909/fpl-basics-scoring)

## Semantic comparison with 2025/26

The typed transition profile has two behavioural catalogue differences:

1. The 2025/26 GW16 AFCON top-up to five free transfers is absent in 2026/27.
2. The first-half chip deadline moves from 30 December 2025 to
   2 January 2027. Both seasons still use GW19 as the boundary.

Budget, squad composition, transfer recurrence/hit cost, price-sale semantics,
chip inventory, GW1/GW19–20 restrictions, season length and terminal-state
semantics are unchanged.

The broader scoring catalogue also records the announced 2026/27 BPS revisions:
the tackled penalty is removed, CBI earns one BPS per three actions, and
goalkeeper save/BPS values are revised. These affect scoring interpretation, not
manager-state transfer recurrence.

## Tests and controls

The owner packet is self-hashed. Tests recompute it from the exact two YAML
files, require zero activation blockers, require all 39 rules to have dated
official evidence, exercise GW1 and GW19–20 chip boundaries, preserve historical
2025/26 state hashes, and prove live state can initialise.

Approval changes only:

`advisory_use: blocked_pending_owner_signoff` → `advisory_use: approved`

It does not change:

- `browser_execution_authorized: false`
- `fpl_account_writes_authorized: false`

## Owner decision

Approved by Alastair on 27 July 2026 at 19:01:48 UTC:

> I approve ruleset `2026-27-v1.0` at SHA-256
> `3439006e5ad21d0e497732273ff9b674e599010df98f0104272c53cea6be0c5a`
> for advisory FPL engine use. This does not authorise browser execution or FPL
> account writes.
