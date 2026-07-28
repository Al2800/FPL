# Claim-value reports

The versioned `*-v1.json` files are the canonical W6 outputs. They verify
player assertions against manifest-bound, all-player hidden outcomes and bind
every source artifact by content hash.

The unversioned JSON files are immutable implementation diagnostics generated
before the all-player outcome join was enabled. They use scored-squad realised
outcomes only, so some verification rows are unavailable. Do not use the
unversioned files for calibration.

All paired score deltas have Gameweek-arm scope. Claim rows record
participation in an application group; they never receive or duplicate a
claim-level share of the weekly delta.
