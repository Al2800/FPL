# 2026/27 set-piece role source

The primary source is the immutable official FPL `bootstrap-static` capture.
Each player row contains official player and team IDs plus published order fields
for penalties, direct free kicks, and corners/indirect free kicks. The official
Premier League/FPL Set-Piece Takers page is a manual corroboration source; this
implementation does not scrape its HTML.

## Snapshot and ledger semantics

`src/ingestion/set_piece_roles.py` converts one captured bootstrap into sixty
complete club-role groups: twenty clubs multiplied by three roles. A group
contains every ranked player in that official snapshot. Empty groups are
explicitly `unknown`, and duplicate ranks are explicitly `conflicted`.

The ledger is evaluated at an exact `as_of` time. Snapshots first available
after that time are excluded. For every club and role, the latest admissible
whole group replaces the earlier group. This means a player removed from the
new official list does not remain active through an old observation.

Role evidence expires after 192 hours unless a newer snapshot supersedes it.
Capture should therefore run at least daily and at the existing pre-deadline
checkpoints. Long breaks are safe because stale evidence expires and the
forecast falls back rather than assuming continuity.

## Confidence and forecasting boundary

The official order is retained directly. Rank confidence is preregistered from
0.95 for first choice down to 0.20 for ranks ten and beyond. These values express
how strongly the published order identifies the likely taker; they are not
goal probabilities or forecast weights.

The feature payload is shadow-only. It exposes active roles but deliberately
contains no effect weights. A conflicted, expired or absent ledger produces no
adjustments and declares `byte_identical_baseline`. Set-piece effects may be
promoted only after the preregistered point-in-time ablation demonstrates
forecast and decision value.

## Current launch assessment

The 27 July immutable launch snapshot has complete team coverage:

- 64 penalty candidates across 20 clubs.
- 60 direct-free-kick candidates across 20 clubs.
- 71 corner/indirect candidates across 20 clubs.
- Zero duplicate team/rank conflicts.

Every artifact carries exact observation, availability and expiry timestamps,
the official source hash, stable observation/group IDs and a derived content
hash. Raw official data remains local and is not redistributed. No browser,
authentication or FPL account write is involved.
