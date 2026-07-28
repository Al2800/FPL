# FPL-xht — Transactional evidence checkpoint runner

## Purpose

Operate one reproducible evidence checkpoint from the real FPL deadline through
collection, ledger admission, boundary-aware retrieval, and coverage reporting.
The runner must never mutate the frozen structured control and must not allow
concurrent processes to fork the evidence ledger.

## Existing contracts reused

- `src/ingestion/evidence_source_orchestrator.py` decides which source families
  may run and records missing or degraded coverage.
- `src/ingestion/live_evidence_collector.py` captures approved public FPL
  endpoints into immutable acquisition manifests and a governed claim ledger.
- `src/evidence/live_evidence_ledger.py` validates claims, projects a
  decision-time view, and records expiry, quarantine, conflicts, and
  supersession.
- `src/evidence/candidate_boundary_retrieval.py` derives the deterministic
  attention set from solver candidates and builds the bounded evidence packet.
- `src/evaluation/evidence_coverage.py` audits acquisition, ledger, retrieval,
  and adjustment coverage as distinct planes.

## Transaction design

1. Derive T-48h, T-24h, T-8h, T-2h, and final-pre-deadline timestamps from the
   exact `deadline_time` in the official FPL event payload.
2. Acquire an exclusive cross-platform file lock beside the checkpoint head.
   The lock file persists; no cleanup race or file deletion is required.
3. Validate the hash-sealed head and compare its generation/hash with the
   caller's expected head. A stale writer is refused before collectors run.
4. Build and execute the existing rights-aware acquisition plan. Adapter
   exceptions and incomplete captures become visible gaps; successful
   acquisitions and claims remain usable.
5. Require every manual observation to carry a document ID, HTTP(S) citation,
   SHA-256 source hash, and observation timestamp. Manual claims must match one
   of those citation artifacts exactly.
6. Merge newly captured claims into the current ledger in availability order.
   Identical claim IDs are idempotent. A newer claim from the same source for
   the same stable subject and claim type automatically supersedes the latest
   prior claim unless an explicit valid supersession is supplied.
7. Project the decision-time ledger, derive candidate boundaries, build the
   evidence packet, and produce the coverage audit.
8. Write one immutable, content-addressed checkpoint artifact binding the
   acquisition plan/funnel, acquisition manifest IDs, added claim IDs, ledger
   before/after hashes, evidence view, discovery, packet, and audit hashes.
9. Advance the hash-sealed head under the same lock. Re-running the identical
   request returns the existing checkpoint without calling collectors or
   advancing the generation.

## Safety and recovery

- All source access remains read-only and rights-gated.
- The structured control is explicitly preserved in the funnel and checkpoint.
- The head is a small mutable coordination pointer; checkpoint artifacts and
  acquisition manifests are immutable.
- A crash before head advancement leaves an unreferenced but valid immutable
  artifact. Re-running the request verifies and reuses it.
- A crash during head writing is detected by the head hash and fails closed.
- No failed evidence arm blocks execution of the structured control.

## Verification

- Unit/integration assertions for exact deadline offsets.
- Stale expected-head conflict before any adapter call.
- Identical restart makes zero adapter calls and reproduces all hashes.
- Same-source claim update supersedes the prior claim.
- Missing or mismatched manual citations fail closed.
- Degraded adapter results retain successful manifest and claim bindings.
- Packet and audit hashes recompute with repository hash functions.
- Focused integration tests followed by the full repository suite.

## Progress

- [x] Existing contracts and ownership mapped.
- [x] Red integration tests.
- [x] Runner and CLI implementation.
- [x] Runbook and genesis head.
- [x] Focused and split full regression verification.
