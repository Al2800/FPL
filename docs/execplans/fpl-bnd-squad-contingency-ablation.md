# FPL-bnd squad-contingency component ablation

This ExecPlan is a living record of the implementation and validation of FPL-bnd.

## Purpose

Determine which separable parts of `probabilistic_v1` explain its W10 results without fitting policy on historical outcomes or mutating production defaults.

## Progress

- [x] Implement independent bench-order and captain/vice arms.
- [x] Establish that XI/formation is structurally unidentified because v1 has no independent XI probability term.
- [x] Bind every locked and descriptive row one-to-one to W10 episode, state, outcome, rules, control plan and control outcome hashes.
- [x] Regenerate the 38-week locked and 37-week descriptive report from approved local artifacts.
- [x] Add portable regression tests and prospective-only v2 protocol.
- [ ] Publish the reviewed branch, pass remote checks and merge.

## Decisions

- Do not use the proposed `start_probability × expected_points` XI heuristic: it is a new policy, not an isomorphic ablation of v1.
- Report XI as unidentified and preserve an exact policy-off no-op diagnostic.
- Attribute only identified marginal terms; label the remainder joint interaction plus structurally unidentified contribution.
- Treat 2024/25 and 2025/26 as exploratory and production-ineligible. Freeze any v2 before the 2026/27 first deadline and require owner approval.
- Defer optional peak-memory profiling; the full replay completes successfully and performance work is not a correctness gate for this bead.

## Outcomes

The regenerated report hash is `2d866b4fad5ea679aa81d1c52d68cee7af6f321524b5e6bbe54bff3658882cba`.

Locked 2024/25: joint v1 −10; identified bench −3; identified captain/vice 0; residual −7.

Descriptive 2025/26: joint v1 +22; identified bench +3; identified captain/vice +18; residual +1.

Focused tests: 9 passed and 3 expected skips. Repository suite: 736 passed, 22 skipped, and the same 27 known environment/artifact failures as current main; no FPL-bnd-specific failure.
