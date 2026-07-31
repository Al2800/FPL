# 01 — Restore fresh-clone CI artifact boundary

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

**Category:** bug

**Former bead:** `FPL-cfb`

## Agent Brief

**Summary:** Make the authoritative Python 3.13 CI suite honest and portable
without weakening governed historical-integration coverage.

### Current behaviour

CI runs the undifferentiated `python3 -m pytest` suite. A clean Linux checkout
reviewed on 31 July 2026 produced **30 failures and 22 skips**: some tests fail
when gitignored Benchmark v0 episode bundles or raw Vaastav files are absent,
while other tests silently skip for the same reason. The historical Bead
recorded 27 failures, so the inventory has already drifted and must be refreshed
when this ticket is claimed.

No strict pytest marker currently defines the artifact-backed tier, and the
test documentation still describes a broader Python matrix even though the
owner has made Python 3.13 the only required PR/main gate.

### Desired behaviour

A fresh clone on Python 3.13 has a documented portable command that exits zero
without raw or governed episode data. Tests that genuinely require those
artifacts are selected by a separately documented artifact-backed command.
Requesting that tier without its approved artifact root fails clearly rather
than silently passing or fabricating fixtures.

Portable replacements must retain the behavioural contracts that matter:
same-state bindings, chronology, immutability, legality and absence of hidden
outcome leakage. Sealed-tree hashes must be byte-identical across Windows and
Linux.

### Key interfaces

- The pytest selection contract: registered marker(s) compatible with the
  repository's strict-marker configuration and two documented entry points
  (portable and artifact-backed).
- The artifact-root input contract: one explicit way to provide approved
  episode/raw roots, with an actionable missing-root error.
- The sealed hash contract: repository-relative POSIX paths plus canonical
  serialisation; never host-absolute paths.
- The CI/test-documentation contract: CI, the test README and the boundary
  document all name the same portable command and explain excluded tests.

### Acceptance criteria

- [ ] At claim time, all clean-clone failures **and artifact-related skips** are inventoried and committed as portable-fixture, artifact-backed integration, or cross-platform hash defects; no test disappears without an explicit reason.
- [ ] The documented portable command exits zero on a clean Python 3.13 checkout with no ignored raw or Benchmark v0 episode tree.
- [ ] Portable synthetic/tracked-safe fixtures continue to assert same-state binding, chronology, immutability, legality and no hidden-outcome leakage.
- [ ] Artifact-backed tests use registered marker(s) and one documented command; without the approved artifact root that command exits non-zero with a clear provisioning message.
- [ ] With approved local artifacts, the artifact-backed command remains runnable and verifies the original historical contracts.
- [ ] CI runs the portable command and reports the number and reason for intentionally excluded artifact-backed tests.
- [ ] Test documentation records the two tiers and makes clear that the historical downloader restores registered raw history only, not governed episode bundles.
- [ ] Sealed tree/artifact hashes are byte-identical on Windows and Linux using canonical repository-relative POSIX paths and serialisation.
- [ ] No secret, credential, raw licensed dataset, or governed hidden-outcome payload is added to Git.

### Suggested execution order

1. Commit the refreshed inventory and classification.
2. Introduce the marker/entry-point boundary and align CI/documentation.
3. Replace only genuinely portable dependencies with minimal safe fixtures.
4. Canonicalise cross-platform hashes and verify both tiers.

### Out of scope

- Restoring Python 3.11, 3.12 or 3.14 as required merge gates.
- Committing ignored historical episode trees or raw licensed datasets.
- Treating the historical downloader as provisioning governed episode bundles.
- Weakening immutable hash assertions or skipping ordinary unit/contract tests.
- Re-opening already completed core-performance-oracle work.
