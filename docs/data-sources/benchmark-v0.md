# Benchmark v0 dataset

Benchmark v0 is frozen to the complete 2025/26 Premier League season: all 38
Gameweeks, not a representative sample. It supports structured-data historical
replay and is not evidence that the historical injury/news environment is
recoverable.

## Frozen identity

- Dataset ID: benchmark-v0-2025-26
- Dataset hash: fac1f0711ffd403e0cd68b7e7a75ef4cce0540ff0d42da970212efd2da54c6b0
- Acquisition time: 2026-07-22T12:57:20Z
- Registry version: 0.3.0
- Manifest: control/manifests/datasets/benchmark-v0.json
- Raw private location: data/benchmark-v0/2025-26/20260722T125720Z

Raw source payloads and endpoint manifests remain gitignored. Only the frozen
manifest, validation code, tests and this report are committed.

## Coverage

| Measure | Result |
|---|---:|
| Gameweeks | 38 of 38 |
| De-duplicated player/Gameweek/fixture rows | 29,747 |
| Players in season catalogue | 841 |
| Teams | 20 |
| FPL fixtures | 380 |
| football-data.co.uk EPL matches | 380 |
| Unresolved player identities | 0 |
| Unresolved team identities | 0 |
| Conflicting duplicate keys | 0 |

Every Gameweek has a distinct partition hash in the frozen manifest.

## Duplicate decision

The upstream merged Gameweek file contains ten repeated rows across ten natural
keys. All columns are identical within each repeated key, so the seed process
counts and collapses only the extra exact rows before partition hashing:

- Junior Kroupi, Gameweeks 1 through 9: nine extra exact rows.
- Ben Gannon-Doak, Gameweek 1: one extra exact row.

Any duplicate natural key with differing columns fails closed. Fixtures and match
results also fail on duplicate IDs or match keys; they are not automatically
collapsed.

## Point-in-time boundary

Allowed observed features are lagged prior-Gameweek player outcomes, fixture
structure demonstrably available by the episode cutoff, and match results strictly
earlier than that cutoff.

The following are excluded from observed historical features:

- unshifted vaastav xP, because the upstream project warns it may contain
  post-match information;
- same-Gameweek outcomes such as total points and minutes;
- football-data.co.uk odds without a timestamp strictly before the FPL deadline;
- reconstructed injury, press-conference or news evidence.

The latter fields can remain in hidden outcomes or be labelled unavailable. They
must not be reconstructed from hindsight.

## Sources and rights

The FPL-derived season files come from vaastav/Fantasy-Premier-League. The match
results file comes from football-data.co.uk. Both are enabled only for private
local analysis under the source registry and ADR-0001, ADR-0002, ADR-0007 and
ADR-0018. Do not redistribute their payloads.

## Reproduction

Run the dependency-complete environment from the repository root:

    .venv/Scripts/python.exe -m scripts.seed_benchmark_v0

The command acquires all five registered files through the common immutable
acquisition boundary, validates them, and refuses to replace a different frozen
manifest. Tests use local HTTP fixtures and require no network.
