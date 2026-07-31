# 01 — Restore fresh-clone CI artifact boundary

**What to build:** A clean clone of the repo passes the portable authoritative
test suite on the required CI Python without needing gitignored historical
episode trees or raw licensed dumps. Tests that truly need governed artifacts
are explicitly marked and run via a separate artifact-backed command that fails
clearly when those artifacts are absent. Sealed hashes are OS-independent.

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

**Category:** bug

**Former bead:** `FPL-cfb`

- [ ] Portable suite is green on a clean checkout under the owner-required CI Python (3.13).
- [ ] Every former fresh-clone failure is classified as portable-fixture, artifact-backed integration, or cross-platform hash defect, with the classification committed.
- [ ] Artifact-backed tests have one marker/command and do not silently skip ordinary contracts in portable CI.
- [ ] Sealed hashes match across Windows and Linux via canonical repository-relative paths and serialisation.
- [ ] No secret, credential, raw licensed dataset, or hidden-outcome payload is added to Git.
