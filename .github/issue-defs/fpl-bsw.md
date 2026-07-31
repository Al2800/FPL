## Parent / origin

Migrated from Bead `FPL-bsw` (was **open**, priority 0 epic).

## Status at migration

Epic still open while child `FPL-bsw.38` remains unfinished at epic level.
**37 of 38 child beads are closed.** This ticket is residual closure of the
Benchmark Kernel programme, not a restart of the kernel build.

## What

Turn Phase 1 scaffolding into a reproducible benchmark kernel for comparing
deterministic analytics, optimisation, evidence agents and human decisions under
identical point-in-time information.

Kernel contract: immutable episode manifest → arm runner → deterministic
validation → frozen proposal/GDR → hidden-outcome reveal → longitudinal
transition → paired and clustered evaluation.

## Remaining work

- [ ] Close or explicitly re-scope child epic **Early-season evidence / live squad** (migrated from `FPL-bsw.38`) — all 14 of its children are already closed; residual is prospective policy + human approval.
- [ ] Confirm kernel acceptance: no arm observes hidden outcomes before proposal freeze; comparisons are paired; collection remains registry-gated; browser execution remains deferred.
- [ ] Update evaluation docs / handoff so GitHub Issues (not Beads) are authoritative for residual kernel work.

## Acceptance criteria

- [ ] Child work for the benchmark kernel is either closed or tracked as focused GitHub Issues with clear residual scope.
- [ ] No arm can observe hidden outcomes before its proposal is frozen.
- [ ] Every comparison is paired on the same observed episode and reports uncertainty plus resource use.
- [ ] Collection remains source-registry gated and browser execution remains deferred.

## Blocked by

Residual closure of the early-season / live-squad epic ticket.

## References

- `docs/evaluation/benchmark-protocol.md`
- `docs/decisions/0017-benchmark-kernel.md`
- `control/schemas/benchmark/**`, `src/orchestration/**`, `src/evaluation/**`
