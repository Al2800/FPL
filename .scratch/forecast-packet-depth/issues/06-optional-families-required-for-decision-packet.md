# 06 — Optional families required for a decision-grade packet

**Blocked by:** None

**Status:** open

**Type:** task

**Category:** enhancement

## Handoff Brief

**Summary:** Odds, ratings, transfers/signings, promoted priors and availability
blend are not optional for decision quality even when collectors must degrade.
Track the host integration work that makes each family either numerically
present or explicitly reasoned-over as a gap.

### Family checklist (checkpoint `weekly-2026-08-02`)

| Family | State now | Required outcome |
|---|---|---|
| Licensed odds (`the-odds-api`) | unavailable at checkpoint; markets beginning to open | Cutoff-safe snapshots → team prior + packet lineage; still degrade if slot missing |
| Player ratings | unavailable; no 2026/27 envelope | Keep degraded; expose gap in strategy packet; no scrape |
| Transfers & signings | unavailable artifact; launch_context partial | Dedicated transfer context or explicit residual gap for new/loan players |
| Promoted team priors | unavailable artifact; cold-start flags present | Stronger promoted attack/defence priors or documented reliance on Understat fallback |
| Availability / role evidence | admitted (small ledger) | Must blend (ticket 03); model-run admission continues to grow claims |
| Set pieces | admitted, shadow effects | Visibility (ticket 04); effects gated |
| Launch context / WC fatigue | admitted | Keep; weight caution in ticket 05 |

### Desired behaviour

1. Strategy/decision packet builder emits a single `source_families` / gap
   panel that agents are required to read before recommending.
2. Odds: reuse evidence-gap ticket 04 capture path; wire admitted odds into
   Understat/ClubElo team prior (`odds_weight`) and audit trail (tickets 01+02).
3. Ratings: remain shadow/degraded; strategy prompt states the gap; do not
   invent proxies from unregistered sites.
4. Transfers: either bind a transfers artefact when available or mark
   `new_signing` players with an explicit prior-quality flag beyond the boolean.
5. No family may fail closed on the official bootstrap/fixtures path.

### Acceptance criteria

- [ ] Gap panel present on rebuilt checkpoint artefacts consumed by strategy.
- [ ] Odds→team-prior path implemented or explicitly blocked on “no admitted
      snapshot yet” with runbook pointer.
- [ ] Ratings/transfers residual gaps documented in packet limitations, not
      only in narrative docs.
- [ ] Cross-links to tickets 01–05; no duplicate collectors.
- [ ] Tests for degrade-clean behaviour when each optional family is absent.

### Notes

Related resolved/human-gated work lives under
`.scratch/evidence-gap-fill/issues/04` (odds runbook), `05` (availability),
`06` (ratings discipline). This ticket is the **packet integration** umbrella,
not a reopening of rights decisions.
