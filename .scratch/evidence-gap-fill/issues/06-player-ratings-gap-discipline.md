# 06 — Player-ratings gap discipline

**Blocked by:** None

**Status:** resolved

**Type:** research

## Summary

Leave ratings degraded until a rights-cleared local 2026/27 PL envelope exists.
Record the gap explicitly; do not scrape FotMob/Sofascore/FBref. Survey only
registered local-transform options (e.g. StatsBomb open if coverage appears).

## Answer

**Player-ratings gap recorded and safely contained.**

- `statsbomb-open` is the only selected zero-cost local-transform source. The
  adapter consumes a caller-supplied, source-bound local envelope and makes no
  network request.
- The repository manifest records current 2026/27 Premier League coverage as
  `unavailable_not_verified`; therefore the ratings family remains degraded.
- Missing, expired, future, ambiguous or invalid rows are quarantined, and
  explicit source-player identity mappings are required. No name-based
  matching is allowed.
- The feature payload remains
  `shadow_only_pending_point_in_time_ablation` with `effect_weights: null`.
  Empty or unusable input falls back to the byte-identical baseline.
- FotMob, Sofascore and FBref are not collected. A commercial event-data
  source requires a separate terms, cost and owner-approval decision.
- Focused coverage is in `tests/data/test_player_ratings.py` and the
  point-in-time optional-family tests in
  `tests/data/test_preseason_snapshot_capture.py`.
