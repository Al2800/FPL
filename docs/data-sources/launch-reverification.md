# FPL launch re-verification log

**Last pass:** 2026-07-21 (Phase 1 residual)  
**Bootstrap sample used:** local snapshot `data/raw/fpl/20260721T171247Z` (HTTP 200, 841 elements)  
**Live check at residual pass:** `bootstrap-static` → HTTP **403**; `fixtures` → HTTP **200** (transient / edge protection — keep retrying)

## Schema (decision-relevant fields)

Confirmed present on sample elements in the 171247Z snapshot (also documented in `fpl-endpoint-schema-notes.md`):

- availability: `status`, `chance_of_playing_*`, `news`, `news_added`
- projections: `ep_this`, `ep_next`
- DC: `defensive_contribution`, `defensive_contribution_per_90`, `clearances_blocks_interceptions`, `recoveries`
- ownership/price: `selected_by_percent`, `now_cost*`, `cost_change_*`

## Rules cross-check vs bootstrap `game_settings`

| Topic | Catalogue (`2026-27.yaml`) | API observation | Action |
|---|---|---|---|
| Max banked free transfers | `transfers.max_banked` = 5 | `max_extra_free_transfers` = 4 (⇒ 1 + 4 = 5 available) | Consistent — keep confirmed |
| Selling price | half-profit | `element_sell_at_purchase_price` = false | Consistent with half-profit model |
| Season path in static URL | 2026/27 target | `static_content_url` still references `2025_26` | **Do not promote** season-label-dependent inherited rules yet |

## Promotion status

Inherited / provisional rules remain **not promoted** until:

1. `bootstrap-static` is stably HTTP 200 through a full rules-page review, and  
2. official 2026/27 rules pages confirm budget, formations, hit cost, and scoring values unchanged.

Snapshot cadence and failed-response retention continue as designed (403 snapshots are still operational evidence).

## Next verification trigger

Re-run when FPL announces 2026/27 launch / when bootstrap returns 200 consistently; then promote eligible `inherited` → `confirmed` in `control/rules/2026-27.yaml` with a new `verified_at`.
