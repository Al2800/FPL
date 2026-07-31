# 2026/27 evidence coverage audit

**Audit date:** 31 July 2026  
**Mode:** local private analysis; advisory only  
**Conclusion:** coverage has improved, but the initial-squad packet is not
decision-grade yet.

This audit separates evidence that exists locally from evidence that is
permitted, current and usable at a decision cutoff. A source being registered
does not make a late, stale or unobserved value point-in-time safe.

## Structured coverage obtained

| Family | Current evidence | Lineage / status |
|---|---|---|
| Official player/team/fixture state | 2026/27 bootstrap and fixtures captured for the 31 July checkpoint; the live availability run also returned HTTP 200 | Bootstrap `e3b41b91…49431c`; live availability acquisition `31362739…83ebd9`; mandatory structured spine is present |
| Historical player events | Registered Vaastav history restored locally, including 2025/26 `merged_gw` with 29,757 rows | Private, gitignored source; do not redistribute |
| Historical results and odds | Registered football-data.co.uk E0 files restored for 2015/16–2024/25 | Historical comparator only; upload timing is not exact pre-deadline evidence |
| 2025/26 player prior | 841-player prior envelope generated from 29,747 used rows | Hash `4be6801f…e7e1d16`; 10 exact duplicate player-fixture keys were verified and deduplicated; conflicting duplicates would fail closed |
| Launch context | Successor context generated from the 31 July bootstrap and the cutoff-safe 2025/26 roster | Context hash `6d9dad02…c62a2dea`; manifest hash `ea6324eb…d8bde4b0`; old 31 July checkpoint remains immutable and is not rewritten |
| Official FPL availability/news | 55 hash-bound claims captured at 21:30 UTC with no gaps | Local ledger hash `38f6a5e7…d53d856`; official structured fields and derived summaries only |

The restored historical data is useful for calibration and priors, but it does
not recreate the 2026/27 pre-deadline information environment. It must not be
used to claim that an evidence-dependent strategy has been fairly replayed.

## Remaining structured gaps

1. **Complete 2026/27 cadence:** only a small number of preseason snapshots
   exist. Bootstrap, fixtures and availability must be captured at
   T-48h/T-24h/T-8h/T-2h/final, with missed checkpoints recorded rather than
   backfilled.
2. **Manager state:** bank, selling prices, free transfers, chips and the
   current 15-player squad still require the owner's manual entry at each
   decision cutoff.
3. **Live odds:** zero 2026/27 slots exist. The adapter is ready, but the
   environment key and a valid market window are required before capture.
4. **Player ratings:** zero verified 2026/27 Premier League rows exist.
   StatsBomb Open remains a local-transform option; the forecast stays
   shadow-only with zero effect weights.
5. **World Cup return dates:** 141 of 176 World Cup rows match the current
   official code universe, but no return-to-training dates are present. The
   missing-date policy is explicit degradation, not neutral imputation.
6. **Outcome and rank state:** post-Gameweek outcomes and prospective overall
   standings are downstream captures. They must not enter the pre-deadline
   observed partition.

## Remaining unstructured gaps

- Official FPL `news` text is available as structured endpoint evidence and is
  now captured in the availability ledger.
- Club communications, press conferences, tactical comments, role changes and
  official team-sheet evidence are not bulk-collected. They require a
  metadata/manual citation containing URL, source hash, publication,
  observation, availability and expiry timestamps.
- No current candidate-specific manual citation set has been admitted for a
  starting-squad proposal. This is appropriate while no proposal is approved.
- Predicted line-up feeds and automated club HTML collection remain disabled.
  Sportradar remains off; no unregistered analyst/blog source may fill the
  gap.

## Action order

1. Keep the official endpoint and availability ledger on the deadline-relative
   cadence; bind the refreshed launch context and 2025/26 prior to the next
   immutable checkpoint.
2. Enter manager state manually before any solver or starting-squad review.
3. Obtain the owner-managed Odds API environment key and capture every slot;
   do not open the W15 ablation until four Gameweeks are complete.
4. Admit only specific manual citations for high-impact availability or role
   questions; retain no raw club page text.
5. Leave ratings, World Cup return dates and unavailable sources explicitly
   degraded until governed evidence exists.

No missing family is converted into a neutral value or silently omitted from
the decision record.
