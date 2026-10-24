# Live-entry evidence review — 2026-09-28

- observed_at: 2026-09-28T07:38:53Z
- next_deadline: 2026-10-10T10:00:00Z
- prior ledger tip: `fdc175a82b61341900081a581a1a0b9962500a836960f459dfc4f38213c97a70`
- resulting ledger tip: `303520f85896d2d4d8ceae4ea9bc47b171f3dd55cf915ff01ba47f1f2ee2bdc9`
- new claims admitted by model run: 2
- account writes: false

## Review outcome

Isak is the material owned-player change. Liverpool confirms a minor injury, withdrawal from Sweden's remaining three matches and assessment by Liverpool medical staff. Official FPL now lists a thigh injury and 75% chance of playing.

The no-Haaland squad therefore has five doubtful players plus Obi unavailable. No early transfer is justified, but the repair-versus-Wildcard comparison is now mandatory if three or more doubts persist near the GW6 deadline.

## Current official state

- Entry 8522487: 292 points; current rank 5,200,151.
- Entry 7337262: 291 points; current rank 5,320,636.
- Sampled top-1,000 boundary: 414.
- Next deadline: 2026-10-10T10:00:00Z.
- Owned prices, public finances, chip histories and completed-GW scores are unchanged.
- Current free transfers, pending moves, purchase prices and selling prices remain private.

## Accepted evidence

| player | source | published_at | accepted proposition | relevance |
|---|---|---|---|---|
| Isak | Liverpool | 2026-09-27T09:38:00Z | returned early with minor injury; misses remaining Sweden fixtures; club assessment pending | owned; transfer, XI and captaincy risk |
| Isak | official FPL | news 2026-09-27T10:30:09Z | thigh injury; 75% chance of playing | owned; current official status |
| Havertz | Arsenal | 2026-09-25T07:50:35Z | started for Germany and was forced off after 30 minutes; no diagnosis | comparator only |
| owned squads | official FPL | observed 2026-09-28T07:38:53Z | completed picks, prices and statuses as recorded in companion report | live-entry authority |

## Rejected or unresolved

| claim | disposition | reason |
|---|---|---|
| Isak will miss GW6 | unresolved | Liverpool says minor injury and assessment pending, not ruled out |
| Isak is a Newcastle player facing Coventry in GW6 | rejected and corrected | official bootstrap assigns Isak to Liverpool; GW6 is Manchester City at Anfield |
| Isak should captain if Palmer remains doubtful | rejected | new injury flag, pending assessment and Manchester City fixture |
| Palmer, Rice, Semenyo or João Pedro has a confirmed GW6 return | unresolved | no current timed official club original |
| Kinsky, Cherki and Wissa are owned by entry 8522487 | rejected | official completed-GW picks and transfer history contradict reconstruction |
| either entry has exactly one current free transfer | rejected | authenticated private state is required |
| Wildcard-six popularity requires activation now | rejected | twelve days of injury information remain before the deadline |

## Changes since 27 September

- Isak: newly doubtful and removed from fallback captaincy consideration.
- No-Haaland doubt count: four to five; Wildcard pressure increased.
- Fallback captain: Rogers restored while Palmer is doubtful; Raya vice-captain.
- Prices, points, public finances and chips: unchanged.
- Transfer/chip action: unchanged; hold.

## Repository reconciliation

The companion live-entry report is authoritative for entries 8522487 and 7337262. The automated strategy report remains useful for discovery and ledger admission, but its reconstructed squad and free-transfer assertion must not drive account actions.

