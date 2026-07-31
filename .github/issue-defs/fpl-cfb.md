## Parent / origin

Migrated from Bead `FPL-cfb` (was **open**, priority 0 / P0 bug).
Discovered from closed bead `FPL-1qi`.

## Status at migration

Open. Owner decision 2026-07-30: required CI is **Python 3.13 only**;
multi-version matrix compatibility is not a PR/main gate. Remaining scope is
clean-clone portable vs artifact-backed boundary repair.

## What

Fresh-clone GitHub Actions fails tests that require gitignored
`data/benchmark-v0/episodes/v1|v2` or raw Vaastav files, and some sealed
tree/hash assertions differ Linux vs Windows.

Restore an honest two-tier test boundary:

1. **Portable authoritative CI** constructs or consumes minimum
   repository-safe deterministic fixtures.
2. **Artifact-backed integration** tests are explicitly marked and run by a
   separately documented command.

Do not silently skip ordinary unit/contracts, do not commit raw/licence-restricted
or hidden-outcome payloads merely to make CI green, and do not weaken immutable
hash checks. Normalise artifact-relative paths and serialisation so sealed hashes
are OS-independent.

## Files

- `.github/workflows/ci.yml`
- `tests/conftest.py`
- agent-eval / historical-replay / orchestration tests listed in the former bead
- `evals/episodes/structured/benchmark-v0-index-v2.json`
- `docs/evaluation/ci-artifact-test-boundary.md` (to create/update)

## Acceptance criteria

- [ ] A clean checkout with no ignored `data/raw` or `data/benchmark-v0/episodes` tree passes the portable authoritative suite on Python 3.13.
- [ ] Every former failure is classified as portable-fixture, artifact-backed integration, or cross-platform hash defect; classification is committed.
- [ ] Portable tests use minimal synthetic/tracked-safe fixtures and still assert same-state bindings, chronology, immutability, legality and absence of hidden outcome leakage.
- [ ] Artifact-backed tests have one marker/command that fails clearly when requested without the approved artifact root; portable CI reports intentional skip count/reasons.
- [ ] Tree/artifact hashes are byte-identical on Windows and Linux (canonical repository-relative POSIX paths and serialisation).
- [ ] Required CI job(s) green on PR and main; local artifact-backed validation remains documented.
- [ ] No secret, credential, raw licensed dataset, or governed hidden-outcome payload is added to Git.

## Blocked by

None — can start immediately (subject to owner CI Python 3.13 policy above).

## Non-goals

Multi-version Python matrix as a merge gate; committing governed episode trees.
