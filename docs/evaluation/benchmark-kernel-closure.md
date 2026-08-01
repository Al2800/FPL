# Benchmark Kernel programme closure

**Status:** Verified; residual ticket resolved  
**Date:** 31 July 2026  
**Contract:** Benchmark Kernel v1.0 (`docs/decisions/0017-benchmark-kernel.md`)

## Scope

This is an evidence-led closure of the Benchmark Kernel programme residual. It
does not add policy arms, datasets, metrics or execution capability.

Ticket 06 records owner ratification of the prospective initial-squad policy
gate. It does **not** approve a specific 2026/27 starting squad:
`ready_for_manual_entry` remains false while the live six-Gameweek packet is
degraded.

## Contract audit

| Contract | Evidence | Result |
|---|---|---|
| Immutable point-in-time episode identity | Episode manifest schema, historical/live builders and immutable-write tests | Pass |
| Information parity | Observed episode SHA-256 excludes hidden outcomes and policy outputs; equal hashes are the only pairing key | Pass |
| Run reproducibility | Policy-result schema retains episode/run/arm identity, code/rules/policy/tool versions, trace, proposal/GDR hashes and frozen validation | Pass |
| Resource accounting | Episode budgets and policy-result limit/used records retain wall-clock, tool calls, tokens, currency and cost | Pass |
| Freeze/reveal isolation | Replay requires every fixed arm to provide a passed, hashed, frozen plan before loading the hidden outcome; state transitions reject early reveal | Pass |
| Source governance | Disabled sources fail the collectability gate before collection; enabled official-lineup use remains manual citation only | Pass |
| Advisory boundary | Live episode, shadow, readiness and deferred-interface contracts keep browser actions and account writes disabled | Pass |

The benchmark protocol reports uncertainty, paired sub-decision metrics,
degraded runs, cost and latency. It also records the historical/live evidence
asymmetry rather than treating incomplete historical news as agent evidence.

## Verification

The portable acceptance slice was run without governed historical artefacts:

```text
python3 -m pytest -q -m "not artifact_backed" \
  tests/contracts/test_benchmark_schemas.py \
  tests/historical-replay/test_genuine_replay.py \
  tests/unit/test_registry.py
18 passed, 13 deselected
```

The governed replay file currently contains 13 artifact-backed tests:

```text
python3 -m pytest --collect-only -q -m artifact_backed \
  tests/historical-replay/test_genuine_replay.py
13 tests collected
```

The episode tree is intentionally not committed. Running those replay tests
requires an approved local `data/benchmark-v0/episodes` tree or
`FPL_ARTIFACT_ROOT`. The absence of that private artefact is an explicit
provisioning limitation, not a waived contract failure. Ticket 01 owns the
portable/artifact-backed test boundary.

The archived `.beads/` data was not modified. Active work remains tracked by
local Markdown tickets under `.scratch/`.
