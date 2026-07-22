# Benchmark v0 historical episodes

`benchmark-v0-index-v2.json` is the Git-safe index for 38 deterministic episodes
built from the frozen 2025/26 dataset. It contains only identifiers, hashes,
counts, cutoffs and declared limitations. Player-level observed and outcome rows
remain private and gitignored below:

    data/benchmark-v0/episodes/v2/2025-26/

Generate or verify the complete set from the repository root:

    python -m scripts.build_historical_episodes

A second identical run reuses every immutable artefact and leaves the index
byte-for-byte unchanged.

## Episode boundary

For Gameweek N, the observed partition contains:

- the stripped Gameweek N fixture schedule, without scores, match statistics or
  post-kickoff state;
- Gameweek N-1 player outcomes whose kickoff is strictly before the cutoff;
- football-data.co.uk match results strictly before the cutoff;
- season-specific player and team identity mappings; and
- explicit evidence limitations.

The hidden partition contains Gameweek N player points/minutes, final fixture
scores/statistics and matching league results. Its content hash appears in the
episode manifest, but the payload is unavailable to policy arms until their
proposal is frozen.

Gameweek 1 is an honest cold start with no lagged player outcomes. It does not
load final-season player aggregates as a substitute.

## Current limitations

Historical news, injury context and manager state are not reconstructed. The
fixture slate comes from a final season export because archived pre-deadline
fixture revisions are unavailable; every episode records that limitation. The
deadline is deterministically derived as 90 minutes before the earliest fixture
kickoff.

Every v2 episode embeds the validated `2025-26-v1.0` catalogue and references
the SHA-256 of its exact YAML bytes. Squad, transfer, price, chip, scoring,
defensive-contribution, bonus and deadline rules are source-backed and tested.
The original v1 artefacts remain immutable evidence of the earlier rules
limitation.

Manager state is represented by an explicit unavailable placeholder owned by
`FPL-bsw.12`. That bead will create independent evolving state for each policy
arm before the genuine replay harness runs.

## Reproducibility evidence

The v2 build produced 38 distinct observed episode hashes. Repeating the full
command reused every immutable artefact and preserved the safe index SHA-256:

    726A0A4183D13BEC7036016AF65DBF8D400E66033DC03E4D08E90772482CE9FB

The embedded ruleset SHA-256 is:

    376E6A7982B54BCE8562A73CFD749F30C2D869C50BFA036A531B96C90BB5A809

Representative observed hashes:

- GW1: `388be60abd0473edead3ee350b32a6b4aaf22cb4ac556d1c46a02fd81ebda311`
- GW2: `cc87c37663393d5f0347dfc05068fefa1b0704f29d651d67acfa39e31b67a2ef`
- GW20: `d4d14d5b5dba5f41bc01d8029fac618d42679cbe90b2575c4a5f85c43c00656e`
- GW38: `0f5774b7d7cdbb02ee8cc18dfd5a162070ab60b8fc6166d91eb704a300d7013c`
