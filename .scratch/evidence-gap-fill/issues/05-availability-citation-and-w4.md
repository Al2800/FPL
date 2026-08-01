# 05 — Availability citations + W4 persistence

**Blocked by:** None

**Status:** resolved

**Type:** task

## Summary

Keep official FPL availability automated; finish W4 persistent availability
behind the disabled V2 policy; accept high-impact club/role claims only via
manual citation until W12 rights clear automated club collection.

## Answer

**Availability and role evidence boundary verified; W4 challenger closed.**

- `fpl-official-endpoints` remains the automated availability source.
- Official club communications remain registry-disabled with unknown rights.
  High-impact club, tactical and role claims therefore enter only as
  metadata/manual citations; no club HTML scrape is enabled.
- `official-lineups-minutes` is restricted and enabled for manual citation
  capture only. Sportradar and other paid challengers remain off.
- `availability-persistence-v1` is implemented as a named challenger under
  `control/policies/evidence-adjustments-v2.yaml`, with `enabled: false`.
  It projects a copied solver input, persists cutoff-safe unavailable/doubtful
  claims until expiry or explicit recovery, requires exact identity and source
  hashes, and fails closed on conflicts or unapproved sources.
- The disabled path preserves the structured baseline byte-for-byte. No live
  production promotion or owner approval of evidence effects is implied.
- Focused coverage is in
  `tests/evidence/test_persistent_availability_challenger.py`,
  `tests/evidence/test_live_evidence_ledger.py` and
  `tests/integration/test_live_evidence_collection.py`.
- Automated club collection remains a W12 rights decision; this ticket does
  not reopen that gate.
