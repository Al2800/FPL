# World Cup 2026 priors — provenance

**Status:** Populated from manual/citation-based assembly  
**Brief:** [`docs/handover-world-cup-priors.md`](../handover-world-cup-priors.md)  
**Output path:** `control/identities/world-cup-2026-priors.csv`  
**Template:** `control/identities/world-cup-2026-priors-template.csv`  
**Observed at:** 2026-07-21T17:21:28Z

## Tournament window

- Start: 11 June 2026  
- Final: 19 July 2026  

## Assembly checklist (agent)

- [x] Stage 0 — PL universe from FPL bootstrap  
- [x] Stage 1 — nation elimination map  
- [x] Stage 2 — squad ∩ PL players  
- [x] Stage 3 — minutes / appearances  
- [x] Stage 4 — return-to-training (optional; no club-specific return dates captured)  
- [x] Stage 5 — `fatigue_prior` + commit CSV + this note updated  

## Counts

| fatigue_prior | n |
|---|---:|
| none | 18 |
| moderate | 105 |
| high | 21 |
| extreme | 32 |

- Rows: 176 current FPL-universe World Cup squad members.
- `wc_minutes` filled: 161 / 176 (91.5%).
- FPL-code join rate: 173 / 176 rows (98.3%).
- `return_to_training_date`: left blank for all rows; no first club return-to-training date was captured with a club/source citation.

## Club coverage

Every current 2026/27 FPL club has at least one World Cup squad member in the CSV.

| club_short_name | rows |
|---|---:|
| ARS | 15 |
| AVL | 9 |
| BHA | 8 |
| BOU | 7 |
| BRE | 4 |
| BUR | 5 |
| CHE | 12 |
| CRY | 13 |
| EVE | 4 |
| FUL | 7 |
| LEE | 4 |
| LIV | 10 |
| MCI | 19 |
| MUN | 13 |
| NEW | 7 |
| NFO | 6 |
| SUN | 12 |
| TOT | 9 |
| WHU | 5 |
| WOL | 7 |

## Join misses

These three rows are retained because the Premier League squad list names them as PL-linked World Cup squad members, but they did not resolve to an `elements[].code` in the 20260721T171247Z FPL bootstrap:

| display_name | club_short_name | national_team | note |
|---|---|---|---|
| Owen Goodman | CRY | Canada | `join_missing;minutes_unconfirmed` |
| Luc de Fougerolles | FUL | Canada | `join_missing` |
| Tyler Bindon | NFO | New Zealand | `join_missing` |

## Remaining minute gaps

Fifteen rows retain blank `wc_minutes` with `minutes_unconfirmed`. The fatigue prior for those rows is reached-round based, as allowed by the brief, and should be revisited if official player-minute files become available:

Zubimendi (ARS, Spain), Wieffer (BHA, Netherlands), Paulsen (BOU, New Zealand), Ekdal (BUR, Sweden), Penders (CHE, Belgium), Chalobah (CHE, England), M.Sarr (CHE, Senegal), Owen Goodman (CRY, Canada), Fletcher (MUN, Scotland), Bayindir (MUN, Turkey), Burn (NEW, England), Geertruida (SUN, Netherlands), Roefs (SUN, Netherlands), Jose Sa (WOL, Portugal), Hee Chan (WOL, South Korea).

## Sources used

- FPL bootstrap snapshot captured at `data/raw/fpl/20260721T171247Z/api_bootstrap-static.json` for `fpl_code`, current club and display-name joins.
- Premier League squad list: <https://www.premierleague.com/en/news/4676821/updated-premier-league-players-appearing-at-fifa-world-cup-2026-by-nation>.
- FIFA final tournament standings: <https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/articles/final-tournament-standings>.
- FotMob World Cup 2026 minutes leaderboard: <https://www.fotmob.com/leagues/77/stats/season/24254/players/mins_played/world-cup>.
- Premier League finalist appearance notes: <https://www.premierleague.com/en/news/4679876/which-premier-league-players-will-win-the-2026-world-cup>.
- Targeted checks for otherwise blank England/Uruguay rows:
  - <https://www.givemesport.com/england-2026-world-cup-players-ranked-worst-best-football-soccer/>
  - <https://www.newsandstar.co.uk/news/26292262.dean-henderson-handed-first-world-cup-appearance-england/>
  - <https://last5games.com/players/kobbie-mainoo-37540234/>
  - <https://terrikon.com/en/football/players/33283>
- openfootball cross-check JSON: <https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.json>.

`control/sources/source-registry.yaml` remains unchanged: `world-cup-2026` automated collection is still disabled.
