# Challenger matrix and live-shadow promotion

The challenger matrix is a governance boundary, not a leaderboard. Every row
binds the same sealed GW2–GW38 episode manifests, observed inputs, hidden
outcomes, configuration, and evidence report. Rejected and exploratory
challengers remain in the report so a positive final-season result cannot
erase a failed held-out gate or a provenance limitation.

## Predeclared rule

A policy may be nominated for **observation-only** live shadow only when all of
these gates pass:

1. configuration and episode integrity;
2. no known temporal leakage;
3. the locked held-out gate;
4. legal replay through the unchanged validator and scorer;
5. deterministic reproduction;
6. bounded degradation; and
7. a control fallback.

A failed locked gate, retrospective case selection, historical schedule
provenance gap, or missing full legal replay disqualifies a candidate. Final
2025/26 points are a diagnostic and tie-break input; they cannot override a
failed gate.

## Nomination

`robust-selection-v2` is the live-shadow nominee. It is the only current
challenger that passed its locked 2024/25 calibration/decision gate and can be
run across the full legal sealed episode set without depending on reconstructed
future schedules or retrospectively selected evidence.

The nomination is deliberately cautious. Locked selected-player MAE and ranking
regret improved, and final 2025/26 selected-player MAE also improved, but final
unconstrained top-15 regret worsened. In the full isolated legal replay, robust
selection changed 17 transfer decisions and 30 lineups, never changed the
captain, and scored 1,935 versus the control's 1,954 across GW2–GW38: a
19-point loss. That negative result prevents any claim that the policy is
better. It does not make an observation-only shadow unsafe or uninformative:
live shadow is the appropriate place to test whether the locked calibration
benefit generalises prospectively without placing the FPL team at risk.

The executable policy remains `live-faithful-v1`. The shadow config cannot
submit actions to FPL, cannot delay the control deadline, and falls back to the
control on timeout, missing inputs, or validation failure.

## Matrix interpretation

- Event and team-context models remain rejected after their declared gates.
- Captain v1 remains rejected despite finishing +7 in 2025/26 because it lost
  nine points on locked 2024/25.
- Squad contingency has useful held-out appearance calibration but awaits a
  full paired realised-decision replay.
- Transfer horizon and chip policies remain exploratory until genuinely
  captured deadline fixture schedules exist.
- The weekly evidence programme remains exploratory for historical GW12 because
  the case was recovered and selected retrospectively. Its isolated +14 and
  longitudinal +4 are both retained.

Resource evidence comes from the committed core and optimiser-scale profiles.
No challenger makes network calls or incurs model cost in this historical
matrix. Performance remains a weekly-operability diagnostic, not a reason to
change deterministic outputs.

## Reproduction

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m scripts.run_challenger_matrix
.\.venv\Scripts\python.exe -m scripts.run_challenger_matrix --recompute-robust
.\.venv\Scripts\python.exe -m pytest tests/evaluation/test_challenger_matrix.py -q
```

The default command reuses a compatible sealed robust report. The explicit
`--recompute-robust` command reruns all 37 legal solves and must reproduce it
byte-for-byte. The runner refuses to overwrite a differing sealed report. It
writes only the matrix report, its robust legal replay evidence, and the
observation-only candidate policy; the canonical 2025/26 replay tree is hashed
before and after and must remain unchanged.
