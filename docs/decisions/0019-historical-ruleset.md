# ADR-0019: Use a source-backed 2025/26 ruleset for Benchmark v0

- Status: Accepted
- Date: 2026-07-22
- Owner: Alastair
- Implementation bead: `FPL-mcp`

## Context

Benchmark v0 replays all 38 Gameweeks of the 2025/26 season. Its first episode build isolated observed data from hidden outcomes correctly, but labelled every episode with a synthetic “historical rules not yet executable” record. Reusing `control/rules/2026-27.yaml` would be incorrect: 2026/27 changes the Bonus Points System and the time at which Gameweek scores become final, and it removes the exceptional Africa Cup of Nations transfer top-up.

Rules affect two different layers. Decision rules determine legal squads, formations, transfers, prices, chips and deadlines and must be executable before a proposal is frozen. Outcome rules determine official points. Benchmark v0 stores official historical FPL outcomes; it does not attempt to recreate subjective Opta or FPL adjudications from incomplete event data.

## Decision

Use `control/rules/2025-26.yaml` as the only valid catalogue for 2025/26 replay. Every rule is marked `confirmed` and cites a dated official Premier League source. The episode builder rejects a catalogue for another season, a catalogue without `replay_status: validated`, or any rule that is not confirmed.

Each v2 episode embeds an exact copy named `ruleset.yaml`. `episode-manifest.json` and the public episode index store the lower-case SHA-256 digest of those exact YAML bytes. This content address is intentionally byte-sensitive: even a metadata or formatting change creates a new ruleset identity and therefore a new episode hash.

The executable engines receive the parsed historical mapping explicitly. Historical tests do not rely on the default loader, which currently points to 2026/27.

## Official evidence

The evidence ledger is encoded per rule in the YAML catalogue. The principal official sources are:

- [Picking a squad, 1 July 2025](https://www.premierleague.com/en/news/2174419): £100.0m budget, 15-player composition and three-per-club limit.
- [Managing your team, 1 July 2025](https://www.premierleague.com/en/news/2174899/1000): deadline, formation, captaincy, bench order and automatic substitutions.
- [Making transfers, 1 July 2025](https://www.premierleague.com/en/news/2174907): free transfers, five-transfer bank, four-point hits and selling prices.
- [Using chips, 1 July 2025](https://www.premierleague.com/en/news/2174900): effects, boundary restrictions and retention of banked transfers.
- [Scoring points, 1 July 2025](https://www.premierleague.com/en/news/2174909): the complete point table and defensive-contribution summary.
- [Defensive contributions, 18 July 2025](https://www.premierleague.com/en/news/4361991/whats-new-in-202526-fantasy-defensive-contributions): CBIT/CBIRT definitions, thresholds and two-point cap.
- [Two sets of chips, 18 July 2025](https://www.premierleague.com/en/news/4362027): eight chips, Gameweek 19 expiry and no carry-over.
- [Assist changes, 18 July 2025](https://www.premierleague.com/en/news/4362187): deflection, defensive error and handball criteria.
- [2025/26 changes, 19 July 2025](https://www.premierleague.com/en/news/4362211/all-you-need-to-know-about-changes-to-fantasy-for-202526): consolidated changes and removal of Assistant Manager.
- [2025/26 BPS changes, 19 July 2025](https://www.premierleague.com/en/news/4362127/whats-new-in-202526-fantasy-changes-to-bonus-points-system): save location, goal-line clearance, penalty-goal and tackle metrics.
- [AFCON transfers, 18 October 2025](https://www.premierleague.com/en/news/4362102/whats-new-in-202526-fantasy-extra-transfers-for-afcon): Gameweek 16 top-up to five.
- [Gameweek 38 finalisation notice, 22 May 2026](https://www.premierleague.com/en/news/4659732/gameweek-38-scores-to-remain-provisional-until-post-match-reviews-completed): normal one-hour finalisation and the explicit GW38 exception.

## Material differences from 2026/27

- 2025/26 topped every manager up to five free transfers at Gameweek 16 for AFCON; 2026/27 has no top-up.
- 2025/26 normally locked scores approximately one hour after the final whistle of the Gameweek. The announced 2026/27 rule moves finalisation to 09:00 UK time the next day. Gameweek 38 in 2025/26 was an official exception and remains represented by the official observed outcome.
- 2025/26 BPS awarded three points for an inside-box goalkeeper save, two for an outside-box save, eight base points for a penalty save, nine for a goal-line clearance, twelve for any penalty goal and two per tackle won. The 2026/27 catalogue records a different goalkeeper/CBI/tackled-player scheme.
- Defensive contributions and two sets of the standard four chips began in 2025/26 and continue into 2026/27. Assistant Manager was not available in 2025/26.

## Consequences

Season-accurate decision validation can now proceed into longitudinal manager-state work and genuine replay. The rules limitation is removed from v2 observed partitions. Historical news, actual pre-deadline manager state and archived fixture revisions remain separate evidence limitations; this ADR does not reconstruct them.

Full re-scoring of assists and BPS from raw events is out of scope because Benchmark v0 does not hold complete adjudication inputs. Official FPL totals remain the outcome ground truth, while deterministic golden cases prove the parts of the catalogue that the current engine executes.
