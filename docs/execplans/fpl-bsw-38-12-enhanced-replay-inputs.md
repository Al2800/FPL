# FPL-bsw.38.12 — enhanced 2025/26 replay inputs

## Purpose

Build the input boundary for the non-canonical enhanced replay before running
it. The boundary must maximise honest historical coverage while preventing
retrospective research, final exports, or inferred timestamps from being
mistaken for live-captured pre-deadline evidence.

## Pre-flight findings

1. The canonical v2 episode corpus covers all 38 Gameweeks and has immutable
   observed and identity hashes, but its deadlines are reconstructed as first
   kickoff minus 90 minutes and its fixture schedule is a final export.
2. Lagged player outcomes and prior match results are usable after a
   conservative event-completion bound. Historical prices remain post-Gameweek
   quotes rather than exact deadline prices.
3. The GW1 Scout seed is a valid shared historical reference, but it is not a
   complete launch market for a dedicated initial-15 optimiser.
4. Football-Data pre-closing odds are licensed and useful for exploratory
   comparison, but their Friday/Tuesday schedule is not a quote-level
   availability timestamp. They cannot enter the strict pack.
5. No verified 2025/26 point-in-time player-rating or official set-piece
   snapshot exists. Those families must be explicit gaps.
6. GW1-GW38 unstructured evidence was recovered after the historical
   decisions. Publication predates the relevant deadlines, but project
   observation/availability does not. It is exploratory only and never strict
   replay evidence.
7. Canonical source-artifact `available_at` values at the cutoff are synthetic
   episode boundaries, not proof of historical acquisition. The enhanced
   builder must derive or reject availability independently.

## Contract

Each enhanced Gameweek pack will:

- bind the canonical manifest, observed partition, and identity map by hash;
- never read or reference the hidden outcome payload;
- enumerate official state, promoted/transfer context, team strength, player
  ratings, set-piece roles, odds, and unstructured evidence;
- classify each family as strict, degraded, exploratory-only, or unavailable;
- give every included observation a source, source hash, `observed_at`, and
  `available_at`;
- retain publication precision separately from project observation time;
- emit an explicit gap and fallback for absent families;
- remain exploratory and production-ineligible;
- write immutably and reproduce byte-for-byte.

## Work

- [x] Audit canonical episodes and every intended feature family.
- [x] Record pre-replay failure modes and admission policy.
- [x] Implement the deterministic enhanced-pack builder.
- [x] Add immutable CLI materialisation for GW1-GW38.
- [x] Add leakage, hash, gap, canonical-mutation, and reproducibility tests.
- [x] Generate and inspect the complete availability matrix.
- [x] Run focused and full regression suites.
- [x] Record results, close the Bead, commit, and push `main`.

## Validation log

- Canonical v2 local corpus: 38/38 Gameweek directories present.
- Early evidence: 12/12 candidates published before their target cutoff, but
  0/12 observed before it and 0/12 production eligible.
- GW12-GW38 evidence bundles likewise carry post-season `captured_at` values
  and retrospective case selection.
- Existing complete-suite baseline before this bead: 609 passing tests.

- Focused enhanced-input contract: 7 passed in 0.11 seconds.
- Related evaluation/historical replay suite: 117 passed in 198.94 seconds.
- Complete repository suite: 616 passed in 443.82 seconds.
- Final materialisation: 38 packs; index f7f834691b803d161414bbc7b7baab9ca4dc1c96512a1e12eb09d5af0544f5f2; immediate rerun unchanged.
- Canonical allowlisted tree before/after: a6c1bb9bb42ea2ac42af2d3d7045e4fae8fd661bea7ffb2bc7caaea1f029033e (114 files).

- Bead FPL-bsw.38.12 closed after acceptance evidence was recorded.
