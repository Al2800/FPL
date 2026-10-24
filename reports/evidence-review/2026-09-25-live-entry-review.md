# Live-entry evidence review — 2026-09-25

- observed_at: 2026-09-25T07:43:55Z
- next_deadline: 2026-10-10T10:00:00Z
- prior ledger tip: `1c0620f25f1b900933bd3aea56ca0e7580d5536d14a8d464e56c12fce130acb9`
- resulting ledger tip: `61779acc00e492604dc8da0818656b0090b1376719ec848bfaebdc8f6e751889`
- new availability claims admitted by model run: 1
- account writes: false

## Review outcome

There is one new ledger-admitted official claim and one material official bootstrap change.

1. Manchester City's 24 September international roundup confirms Haaland started for Norway and scored twice. The repository admitted this as an available/started-match claim.
2. Official FPL newly marks Semenyo 75% with an ankle injury, timestamped 2026-09-24T12:00:09Z. No dated club or Ghana original explaining severity or return was found, so this remains an official game-state observation rather than a new derived ledger claim.

## Current official state

- Entry 8522487: 292 points, current summary rank 5,200,330.
- Entry 7337262: 291 points, current summary rank 5,320,816.
- Sampled top-1,000 boundary: 414 points.
- GW6 deadline: 2026-10-10T10:00:00Z.
- No owned-player price, completed-GW score, chip-history or transfer-history change.
- No public endpoint exposes current free transfers, pending moves, purchase prices or selling prices.

## Accepted evidence

| player | source | published / added | accepted proposition |
|---|---|---|---|
| Haaland | Manchester City international roundup | 2026-09-24T21:00:00Z | started for Norway and scored twice; currently available |
| Semenyo | official FPL bootstrap | 2026-09-24T12:00:09Z | newly doubtful, ankle injury, 75% |
| other owned players | official FPL bootstrap | observed 2026-09-25T07:43:55Z | statuses and prices unchanged |

## Rejected or unresolved

| claim | disposition | reason |
|---|---|---|
| Semenyo will miss GW6 | unresolved | no duration, withdrawal or club assessment published |
| Kinsky, Cherki and Wissa are owned by entry 8522487 | rejected | contradicted by official completed-GW picks |
| either entry has exactly one current free transfer | rejected | private authenticated state |
| Palmer to Saka or João Pedro to Barry should be made now | rejected | community/model suggestion without resolved injuries or authenticated affordability |
| Wildcard popularity requires activation | rejected | sentiment does not establish structural necessity |
| Chelsea search hits settle Palmer or João Pedro return | rejected | publication date or current-window context unavailable |

## Decision implications

- No early transfer or chip.
- Haaland remains provisional captain for entry 8522487, Bruno vice-captain.
- Rogers remains risk-adjusted captain for entry 7337262 while Palmer is doubtful.
- Semenyo becomes a required daily monitor. If only Semenyo is unavailable, Shaw can cover.
- Four doubtful starters plus Obi make the no-Haaland squad materially closer to the Wildcard threshold. If the doubts persist close to the deadline, compare free-transfer repair, hits and Wildcard with authenticated prices.
- Continue monitoring Haaland after three remaining scheduled Norway matches; the brace proves current availability, not future fitness.

## Repository reconciliation

The companion live-entry report is authoritative for entries 8522487 and 7337262. The automated daily strategy report is useful for official discovery and the Haaland ledger claim, but its reconstructed squad and free-transfer assertion must not drive account actions.
