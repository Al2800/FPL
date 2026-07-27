# Season-transition and compounding-invariant ledger

**Purpose:** prevent small rule or state errors from compounding across a 38-Gameweek trajectory.

**Historical baseline:** `control/rules/2025-26.yaml` is immutable replay truth for Benchmark v0.

**Upcoming live target:** `control/rules/2026-27.yaml` is machine-activatable as `2026-27-v1.0`; advisory use remains pending explicit owner sign-off.

This ledger is a release control, not just background documentation. Every row must end in one of three states:

- **Executable:** enforced by a deterministic test against a content-addressed ruleset.
- **Observed-only:** official FPL output is retained as ground truth because the underlying adjudication cannot be reconstructed reliably.
- **Blocked:** the live engine cannot be activated until the rule and its value shape are confirmed.


## Activation update — 27 July 2026

The detailed register below preserves the gaps identified on 22 July. Those
rule/compiler gaps are now resolved: 39/39 rules are confirmed, the typed
preflight has zero blockers, AFCON `false` is normalised without a season
conditional, chip windows and GW39 terminal state are rules-driven, and the
full transfer/chip recurrence tests pass. The remaining unchecked release items
are operational live snapshot/finalisation/dry-run controls and owner approval.
## Why the small details matter

A one-transfer error in Gameweek 2 changes the legal transfer budget in Gameweek 3. That changes hits, bank, squad, purchase prices, selling prices, chip timing and every later comparison. The same is true of restoring the wrong squad after a Free Hit, resetting banked transfers after a Wildcard, expiring a chip one deadline late, or revealing corrected points too early. Longitudinal state therefore treats these as trajectory invariants rather than isolated validation messages.

## Compounding invariant register

| Invariant | If wrong | 2025/26 replay truth | 2026/27 status at 22 Jul audit | Proof / gap at that audit | Required live action |
|---|---|---|---|---|---|
| Free-transfer recurrence order | An off-by-one changes hits and all later squads. Example: one available, two used must produce one next Gameweek, not zero. | `min(cap, max(0, available - used) + 1)` for ordinary transfers. | Inherited: one award and four-point hit require launch confirmation; cap five is confirmed. | `test_ordinary_transfer_uses_purchase_history_hits_and_correct_next_free_transfer` proves historical behavior. `src.scoring.validator.banked_transfers` uses a search-oriented operation order and must not drive season state. | Differential tests must exercise zero through five available transfers and zero through six moves for both catalogues. |
| Transfer hit accounting | Gross points accidentally stored as net, or a hit applied twice, shifts cumulative rank permanently. | Four points per transfer beyond the available allowance; Wildcard and Free Hit have zero hit. | Hit cost inherited and not live-approved. | Historical transition tests assert gross, hit and net separately. | Activation gate blocks until `transfers.hit_cost` is confirmed; transition output keeps all three fields. |
| Bank cap and award timing | Banking above the cap or awarding before spending changes later options. | Maximum five; ordinary unused transfers roll after the current decision. | Cap five confirmed; award timing inherited. | Historical cap and recurrence are tested. | Add a cross-season recurrence truth table; never infer “five banked” from an API field without translating its semantics. |
| Wildcard transfer state | Treating it like a temporary squad discards permanent transfers and purchase history. | New squad, bank and purchase prices persist; no hit. | Chip sets confirmed; exact detailed behavior inherited. | Historical Wildcard persistence test exists. | Keep Wildcard and Free Hit as separate transition branches and launch-block until detailed chip behavior is confirmed. |
| Wildcard/Free Hit banked transfers | Resetting, spending or incrementing the count creates an immediate off-by-one. | Exact pre-chip free-transfer count is retained; no extra award for the transition. | Inherited; launch verification required. | Historical Wildcard and Free Hit tests assert exact retention. | Cross-season contract must consume `transfers.wildcard_free_hit_retain_banked`, not assume `true`. |
| Free Hit permanent state | Persisting the temporary team or temporary finances corrupts every later Gameweek. | Temporary squad is validated for the scoring Gameweek; prior permanent squad, bank and purchase history return afterward, refreshed only by later market prices. | Detailed behavior inherited. | Historical Free Hit reversion test covers squad, bank, transfer count and purchase price. | Add round-trip tests with price rises/falls and a transfer immediately after restoration. |
| Purchase and selling price history | Using current price or another arm's purchase price invents cash and changes affordability. | Half of profit is retained, rounded down to £0.1m; losses use current price. Each arm owns its history. | Inherited; launch verification required. | Historical tests cover independent arms, retained purchase price, later price rises and semantic £0.1m steps. | Confirm the sell-price rule and API units; test rises, falls, odd tenths and Free Hit restoration. |
| Decision-price versus next-price snapshots | Using post-deadline prices leaks future data or buys/sells at the wrong value. | Transfers use the frozen decision market; successor state refreshes from the next point-in-time snapshot. | Required regardless of season. | Transition rejects stale owned-player prices and missing next-market players. | Live episode builder must bind both snapshots by timestamp and content hash. |
| Chip inventory and expiry | A chip can be reused, lost early, or survive into the wrong half. | Two sets of four; first set expires at the GW19 deadline and cannot carry into GW20. | Two sets and GW19 expiry confirmed. | Historical inventory and expiry tests exist; chip names and boundary `20` are currently encoded in policy-state code. | Move inventory, windows and expiry boundaries into typed rules before live activation. |
| Chip boundary restrictions | A Wildcard or Free Hit can be made illegally available by one Gameweek. | Wildcard and Free Hit unavailable in GW1; Free Hit cannot be played in both GW19 and GW20. | Provisional: exact boundary wording pending launch. | Historical GW19/20 adjacency is tested; boundaries are hard-coded. | Block live activation until confirmed, then test every boundary Gameweek on both sides. |
| Exceptional transfer awards | Applying a historical exception in a new season changes all subsequent transfer counts. | Every manager was topped up to five entering GW16 for AFCON. | Confirmed absent in 2026/27. | Historical GW16 top-up is tested. **Known incompatibility:** policy state expects an object with `gameweek`/`top_up_to`, while the 2026/27 catalogue value is `false`. | Normalize exceptional events as typed optional rules; prove 2025/26 applies the event and 2026/27 does not. This is a live-engine blocker. |
| Deadline, freeze and reveal order | Post-deadline knowledge leaks into a proposal or provisional points are frozen as final. | Proposal freezes before outcome reveal; normal finalisation was about one hour after the final match, with an official GW38 exception. | Deadline rule inherited; score lock at 09:00 UK next morning confirmed. | Transition enforces reveal strictly after freeze, but does not yet derive the season-specific finalisation instant. | Episode/outcome services must calculate cutoff and finalisation from the active ruleset and retain correction revisions. |
| Blank, Double and revised fixtures | Assigning an event to the wrong Gameweek changes opportunity count, captaincy and chip value. | Revisioned fixtures are part of point-in-time evidence. | Support inherited and launch verification required. | Catalogue acknowledges blanks/doubles; longitudinal state does not itself schedule fixtures. | Episode builder must pin fixture revision/hash and never replace the historical view with the latest schedule. |
| Captain, bench and automatic substitutions | Incorrect fallback alters official outcome and can bias policy comparisons. | Formation-preserving ordered substitutions; vice-captain only when captain records zero minutes. | Inherited. | Validator covers legality; Benchmark v0 uses official FPL totals rather than reconstructing all adjudication. | Keep official totals as observed outcome; confirm live rules and add deterministic golden cases for engine-produced projections. |
| Scoring, BPS and corrections | A small per-player scoring delta accumulates through total points and training labels. | 2025/26 scoring and BPS catalogue is frozen; official totals are outcome truth. | 2026/27 BPS changes and next-morning lock confirmed; many base values inherited. | Historical rules tests protect replay catalogue identity. | Never rescore historical episodes with the default/current catalogue. Promote live rules only after official confirmation. |
| Ruleset identity and value shape | A matching rule name with a different type can crash or, worse, be misread silently. | Every episode embeds and hashes the exact validated 2025/26 YAML bytes. | Catalogue is `2026-27-v0.1`, with mixed confirmed/inherited/provisional states. | State rejects ruleset ID/hash mismatch; no preflight schema currently validates every consumed rule's type/status. | Add a typed ruleset contract and activation command that fails before a season run starts. |
| Initial state and state ownership | An invalid £100m seed or shared mutable state contaminates every arm. | Purchase prices plus bank equal initial budget; all five arms start from the same seed hash but own distinct state hashes. | Initial budget and squad limits inherited. | Isolation and seed-finance tests exist. | Confirm launch budget/composition, then capture the real manager state explicitly; never fabricate missing account history. |
| Season boundary and migrations | Hard-coding 38 Gameweeks or silently changing schemas makes hashes and terminal state wrong. | GW39 is a terminal marker after GW38 in Benchmark v0. | Calendar/terminal assumptions need live confirmation; schema migrations remain explicit. | Terminal historical test exists; boundary is currently hard-coded. | Put season length/terminal semantics in the activation contract and version any state-schema migration. |

## Historical code boundaries as of 2026-07-22 (resolved by activation compiler)

`src/orchestration/policy_state.py` is deliberately proven against `control/rules/2025-26.yaml`. It is **not yet approved as a generic 2026/27 live engine**. In particular:

1. the AFCON rule path assumes the 2025/26 object value and is incompatible with the 2026/27 `false` value;
2. chip half boundaries, GW1 restrictions, GW19/GW20 adjacency and terminal GW39 are currently encoded in Python;
3. exact chip inventory is encoded as eight fixed identifiers;
4. proposal/reveal chronology is enforced, but season-specific deadline and finalisation time are not yet calculated by this module;
5. ruleset identity is enforced after loading, but there is no typed preflight that proves all consumed values are confirmed and structurally compatible before the first live episode.

These are tracked as implementation work rather than accepted as harmless technical debt.

## Live-season activation gate

The 2026/27 engine remains disabled until all of the following are true:

- [x] Every rule consumed by squad, line-up, transfer, price, chip, deadline and scoring paths is `confirmed`, or an explicit reviewed compatibility policy names the allowed exception.
- [x] A typed ruleset validator checks required IDs, value shapes, units, effective dates and cross-rule consistency.
- [ ] A machine-generated 2025/26 → 2026/27 semantic diff has been reviewed; metadata-only changes are separated from behavioral changes.
- [x] Cross-season golden tests prove shared invariants and intentional differences, especially AFCON top-up/no-top-up and score-finalisation timing.
- [x] Boundary tests cover GW1, GW18–20, every exceptional-event boundary and the terminal transition.
- [x] Transfer recurrence tests cover the full bank/hit matrix and both unlimited-transfer chips.
- [x] Free Hit round-trip tests prove squad, bank, purchase history and free transfers restore exactly.
- [ ] Live snapshot/API monetary units, manager fields and deadline timestamps have been verified and content-addressed.
- [ ] Outcome reveal uses the active season's finalisation rule and stores later official corrections as revisions rather than overwrites.
- [ ] A dry-run season can replay deterministically twice with identical state/transition hashes and no unclassified degraded behavior.
- [ ] The activated ruleset ID and SHA-256 are pinned in every episode, proposal, transition and report.
- [ ] Activation is an explicit reviewed configuration change; the engine never selects a season merely because it is the default loader.

## Change protocol

When a new discrepancy is found:

1. add or amend a row here with the failure path and season scope;
2. cite the exact official source in the relevant rules catalogue;
3. add a failing golden/unit test before changing transition behavior;
4. update the machine-readable rule instead of adding a season conditional where possible;
5. run historical replay regressions to prove the old season did not drift;
6. record the discovery and implementation in Beads;
7. create a new ruleset ID/hash when any catalogue bytes change.

## Source records

- `docs/decisions/0019-historical-ruleset.md` — source-backed 2025/26 replay decision and material 2026/27 differences.
- `docs/data-sources/launch-reverification.md` — live API/rules-page launch checks and unresolved promotions.
- `docs/rules/wp01-status.md` — current 2026/27 catalogue status.
- `docs/execplans/fpl-bsw-12-policy-state.md` — implementation decisions and executable longitudinal evidence.
- `control/rules/2025-26.yaml` and `control/rules/2026-27.yaml` — authoritative machine-readable catalogues.
