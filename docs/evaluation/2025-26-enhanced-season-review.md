# 2025/26 enhanced replay review

## GW1-GW5 checkpoint

Status: `paused_for_review`

Checkpoint:
`reports/benchmarks/2025-26-enhanced/checkpoints/gw-01-gw-05.json`

Checkpoint SHA-256:
`21a8f0fc8e426b55466b58eeffbe8ec09a7056247b68a91ab829534b0ae172e0`

This is an exploratory, production-ineligible historical experiment. It does
not replace or alter the published canonical replay.

## Result

| GW | Scout seed | Scout cumulative | Optimized seed | Optimized cumulative | Optimized seed delta |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 56 | 56 | 48 | 48 | -8 |
| 2 | 59 | 115 | 47 | 95 | -20 |
| 3 | 59 | 174 | 64 | 159 | -15 |
| 4 | 57 | 231 | 64 | 223 | -8 |
| 5 | 46 | 277 | 56 | 279 | +2 |

The optimized seed did not win immediately. It lost eight points in GW1 and
fell 20 points behind after GW2, then recovered through a different transfer
path and finished GW5 two points ahead. This is exactly why the initial 15 must
be assessed longitudinally rather than by its opening-week score or terminal
score alone.

The structured and evidence arms were tied within each seed condition:

| Arm | GW1-GW5 points | Transfers | Hits | Chips | Applied evidence weeks |
| --- | ---: | ---: | ---: | ---: | ---: |
| Scout structured | 277 | 2 | 0 | 0 | 0 |
| Scout evidence | 277 | 2 | 0 | 0 | 0 |
| Optimized structured | 279 | 3 | 0 | 0 | 0 |
| Optimized evidence | 279 | 3 | 0 | 0 | 0 |

The terminal factorial effects are therefore:

- optimized seed without evidence: +2;
- optimized seed with evidence: +2;
- evidence effect with Scout seed: 0;
- evidence effect with optimized seed: 0; and
- seed/evidence interaction: 0.

These are descriptive results for five historical weeks, not evidence of
general skill.

## Decisions and state

The optimized structured policy made:

- GW2: Justin Kluivert to Antoine Semenyo;
- GW3: Yoane Wissa to João Pedro;
- GW4: Matheus Cunha to Cody Gakpo.

The Scout structured policy banked through GW3, then made two free transfers in
GW4:

- Cole Palmer to Cody Gakpo; and
- Elliot Anderson to Dominik Szoboszlai.

Neither path paid a hit or used a chip. Both selected Mohamed Salah as captain
from GW2 through GW5. Automatic substitutions are recorded in each realised
outcome and are not treated as manager transfers.

All four trajectories have independent, continuous state hashes. Each plan is
bound to its predecessor; each outcome is bound to the frozen plan; and each
transition is bound to the successor state. The same enhanced exogenous input
pack hash is attached to all four arms at every gameweek.

## Evidence outcome

No evidence adjustment reached the optimizer in GW2-GW5:

| GW | Result | Reason |
| ---: | --- | --- |
| 2 | abstained | evidence agent proposed no adjustment |
| 3 | deterministic fallback | Palmer adjustment required human review after challenger confidence downgrade |
| 4 | deterministic fallback | Palmer adjustment required human review after challenger confidence downgrade |
| 5 | abstained | evidence agent proposed no adjustment |

The GW3 and GW4 fallbacks are safe protocol behavior. They also show that the
current evidence policy is conservative: potentially actionable availability
signals can be identified but still contribute zero unless the challenger gate
allows automatic use. Before continuing, the review should decide whether this
is the desired live behavior or whether a deterministic downgrade rule should
turn selected human-review cases into bounded, pre-registered adjustments.

Because these cases were reconstructed retrospectively and were not
pre-registered, changing that rule now must not be used to rewrite this
checkpoint. Any alternative belongs in a separately identified counterfactual.

## Integrity and data review

- Canonical tree before:
  `aa1131c2c65c6f0199d7cc1537f8077b9a9f7e4290e81981ec7dfcf8d2732d02`
- Canonical tree after:
  `aa1131c2c65c6f0199d7cc1537f8077b9a9f7e4290e81981ec7dfcf8d2732d02`
- Canonical files checked: 3,065
- Enhanced integration tests: 6 passed through GW10
- Full repository suite: 622 passed in 457.30 seconds after GW10
- The runner refuses `--stop-gameweek 6` until the GW5 review is approved.

The enhanced input packs make gaps explicit, but not every available family is
yet an active projection feature:

- team-strength data is strictly available from GW2;
- reconstructed odds and unstructured evidence are exploratory only;
- player ratings and set-piece roles are unavailable in this tranche; and
- odds are intentionally not applied to the structured projection.

The checkpoint therefore tests the optimized seed, the upgraded stateful weekly
engine, and the reviewed evidence adapter. It does not yet establish the value
of odds, ratings, or set-piece features. Those require isolated, registered
ablations rather than being silently blended into this result.

## Review questions before GW6

1. Keep the challenger gate as-is, or define a separate pre-registered bounded
   downgrade counterfactual for human-review availability cases?
2. Is the optimized seed's recovery driven by robust weekly decisions or by
   one or two fragile transfer outcomes? Continue to GW10 before drawing a
   conclusion, while retaining the weekly decomposition.
3. Should team-strength inputs be included in an explicit ablation before the
   next tranche, or should this trajectory remain the frozen structured control?
4. Keep odds isolated until quote-level timestamps are available; do not admit
   reconstructed closing information into the primary historical trajectory.

## GW6-GW10 checkpoint

Status: `paused_for_review`

Checkpoint:
`reports/benchmarks/2025-26-enhanced/checkpoints/gw-06-gw-10.json`

Checkpoint SHA-256:
`58401799c19936939aff66caf5f332b29bb0c6bd339e353547f255ab08ea7846`

The checkpoint is cryptographically chained to the unchanged GW1-GW5
checkpoint. GW6 starts from each arm's sealed GW5 successor state.

| GW | Scout structured | Optimized structured | Scout evidence | Optimized evidence | Optimized seed delta |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 6 | 31 (308) | 40 (319) | 31 (308) | 40 (319) | +11 |
| 7 | 40 (348) | 54 (373) | 32 (340) | 54 (373) | +25 |
| 8 | 52 (400) | 49 (422) | 52 (392) | 49 (422) | +22 |
| 9 | 53 (453) | 57 (479) | 53 (445) | 57 (479) | +26 |
| 10 | 65 (518) | 74 (553) | 65 (510) | 74 (553) | +35 |

Parentheses contain season-to-date points. During GW6-GW10 the optimized
structured arm scored 274 against the Scout structured arm's 241. Across
GW1-GW10 the totals are 553 and 518 respectively.

The optimized structured transfers were:

- GW8: Jacob Murphy to Dominik Szoboszlai;
- GW10: Ola Aina to Gabriel and Jarrod Bowen to Danny Welbeck.

The Scout structured transfers were:

- GW7: Murillo to Gabriel;
- GW8: James Tarkowski to Jurriën Timber and Bruno Fernandes to Antoine Semenyo;
- GW10: Tijjani Reijnders to Bryan Mbeumo and Ollie Watkins to Nick Woltemade.

No arm paid a hit or used a chip.

## GW6-GW10 evidence review

| GW | Adapter result | Same-state result |
| ---: | --- | ---: |
| 6 | challenger-gated fallback | 0 |
| 7 | Gabriel start-probability reduction applied | optimized 0; Scout -8 |
| 8 | abstained | 0 |
| 9 | Gabriel start-probability reduction applied | 0 |
| 10 | abstained | 0 |

GW7 is the important causal case. The evidence adjustment reduced Gabriel's
start probability from 0.9227 to 0.7227. On the Scout state, that caused the
engine not to make Murillo to Gabriel; the unchanged same-state control scored
40 and the evidence plan scored 32. On the optimized state, the same adjustment
did not alter the selected plan and both scored 54. This is genuine
seed/evidence interaction: identical exogenous evidence can matter differently
because the inherited squads and available transfer choices differ.

By GW10, evidence remained neutral for the optimized seed and was -8 for the
Scout seed. The headline optimized-versus-Scout structured delta was +35; the
optimized-versus-Scout evidence delta was +43. The latter must not be described
as additional optimized-seed skill: eight points are the negative Scout GW7
evidence counterfactual.

## Review questions before GW11

1. Keep this trajectory frozen. Do not tune the Gabriel threshold using its
   known outcome; any alternative threshold belongs in a registered fork.
2. GW11 can reuse the early-season evidence regime, but GW12 is a regime
   boundary. The optimized structured and optimized evidence states must be
   advanced with the real episode adapter rather than borrowing canonical or
   the existing seed branch, which currently ends at GW11.
3. Continue reporting same-state evidence effects separately from inherited
   trajectory effects.
4. Odds, ratings, set pieces, and explicit team-strength ablations remain
   outside this primary trajectory and should not be silently introduced
   mid-season.

## GW11-GW15 checkpoint

Status: `paused_for_review`

Checkpoint:
`reports/benchmarks/2025-26-enhanced/checkpoints/gw-11-gw-15.json`

Checkpoint SHA-256:
`be2e5d45d4f7db41e5f7b71e077b57334f9406b066eff98849f359033f9e2d16`

The checkpoint is cryptographically chained to GW6-GW10. GW11 uses the final
precomputed early-season controls. From GW12 onward all four arms are solved,
validated, scored, and transitioned from their own sealed manager state; no arm
borrows the canonical or old optimized trajectory.

| GW | Scout structured | Optimized structured | Scout evidence | Optimized evidence |
| ---: | ---: | ---: | ---: | ---: |
| 11 | 35 (553) | 38 (591) | 36 (546) | 38 (591) |
| 12 | 29 (582) | 66 (657) | 41 (587) | 65 (656) |
| 13 | 36 (618) | 20 (677) | 38 (625) | 31 (687) |
| 14 | 63 (681) | 46 (723) | 53 (678) | 71 (758) |
| 15 | 55 (736) | 45 (768) | 55 (733) | 45 (803) |

Parentheses contain season-to-date points. Across GW11-GW15 the arms scored
218, 215, 223, and 250 respectively in table order. Through GW15 the optimized
structured arm leads Scout structured by 32 points. Optimized evidence leads
Scout evidence by 70 points, but that headline is not an estimate of LLM value:
38 points are the measured seed/evidence interaction at the terminal state.

No arm paid a hit or used a chip. Through GW15, the structured arms have each
made 11 transfers and the evidence arms have each made 10.

## GW11-GW15 evidence review

| GW | Scout evidence | Optimized evidence | Paired same-state result |
| ---: | --- | --- | ---: |
| 11 | abstained | abstained | 0 / 0 |
| 12 | applied | applied | -1 / -1 |
| 13 | challenger-gated fallback | challenger-gated fallback | 0 / 0 |
| 14 | applied | applied | 0 / 0 |
| 15 | abstained | abstained | 0 / 0 |

GW12 applied the frozen Gabriel and Semenyo availability adjustments to both
arm-owned states. The immediate paired effect was minus one point in each arm.
On the Scout evidence state, the structured control rolled while evidence sold
Reijnders and Gabriel for Declan Rice and Maxence Lacroix. On the optimized
evidence state, the structured control proposed Gakpo to Rice while evidence
instead sold Gabriel for Jurriën Timber. Captains were unchanged. Those decisions
then changed the carried trajectories, so by GW15 the evidence arms differ
materially from their structured controls. That downstream spread is a
legitimate longitudinal effect of an earlier decision, but this single
retrospectively selected case cannot establish evidence skill. The Timber path
also reinforces the separate review finding that minutes/start calibration can
dominate a nominal evidence result.

GW13 failed closed at the challenger gate. GW14 adjustments passed but did not
change either selected plan, producing zero same-state effect. This separates
three concepts that must remain distinct in later reporting:

- whether an evidence interpretation was accepted;
- whether it changed the current decision and realised score; and
- whether a changed decision altered future squad state and later opportunity.

The hosted GW12-GW15 interpretations were originally sampled against one frozen
request candidate. For this factorial replay they are reused as
projection-level proposals only after exact target-player baseline equality.
Each application artifact records the source host-bundle hash, owned starting
state, and the limitation that its application candidate may differ. This is
exploratory and production-ineligible; live 2026/27 evaluation must sample each
agent against its actual current candidate and retain a continuously frozen
no-evidence shadow.

## Integrity at GW15

- Checkpoint is paused with `next_gameweek: 16`; no GW16 comparison exists.
- Canonical tree before and after:
  `aa1131c2c65c6f0199d7cc1537f8077b9a9f7e4290e81981ec7dfcf8d2732d02`.
- Canonical files checked: 3,065.
- Focused enhanced and fork-adapter regressions: 27 passed.
- Full repository suite: 624 passed in 430.51 seconds, with empty stderr and
  retained JUnit output.
- All four arms have continuous, independently referenced successor hashes
  through GW15.
- All GW12-GW15 plans passed deterministic validation before outcome reveal.

## Review questions before GW16

1. Keep the GW12 downstream trajectory frozen; do not tune its evidence
   thresholds using the now-known results.
2. Inspect which GW12 plan differences generated the later optimized-evidence
   advantage, separating transfer, captaincy, bench, and automatic-substitution
   contributions.
3. Decide whether the current later evidence cases remain the fixed historical
   smoke-test set through GW38 or whether any new evidence regime is registered
   as a separate fork rather than silently changing this trajectory.
4. Continue to keep odds, ratings, set pieces, and team-strength ablations out
   of this frozen primary path; evaluate each as a named paired ablation.
## GW16-GW20 checkpoint

Status: `paused_for_review`

Checkpoint:
`reports/benchmarks/2025-26-enhanced/checkpoints/gw-16-gw-20.json`

Checkpoint SHA-256:
`f69e3890193899634c74051706b3e4baf94bdf95c1eeb15ffd576387bc6ce5a7`

The checkpoint resumes each arm from its own sealed GW15 successor. It keeps
the later evidence regime frozen and binds GW20 to the repaired, complete
`sol-v3` host artifact rather than the degraded `sol-v1` or partial diagnostic
`sol-v2` attempts.

| GW | Scout structured | Optimized structured | Scout evidence | Optimized evidence |
| ---: | ---: | ---: | ---: | ---: |
| 16 | 59 (795) | 57 (825) | 49 (782) | 61 (864) |
| 17 | 88 (883) | 78 (903) | 97 (879) | 86 (950) |
| 18 | 33 (916) | 43 (946) | 38 (917) | 41 (991) |
| 19 | 36 (952) | 48 (994) | 41 (958) | 40 (1031) |
| 20 | 65 (1017) | 68 (1062) | 45 (1003) | 63 (1094) |

Parentheses contain season-to-date points. Through GW20, optimized structured
leads Scout structured by 45 points and optimized evidence leads Scout evidence
by 91. The terminal evidence effect is +32 on the optimized seed and -14 on the
Scout seed, producing a +46 seed/evidence interaction. These longitudinal
totals include inherited squad-state differences and are not estimates of
same-week LLM value.

No arm paid a hit or used a chip. The structured arms have made 16 transfers
each; the evidence arms have made 15 each. GW16 also confirms the exceptional
free-transfer top-up: each arm made one transfer and correctly retained five
for GW17.

## GW16-GW20 evidence review

| GW | Adapter result | Scout same-state result | Optimized same-state result |
| ---: | --- | ---: | ---: |
| 16 | applied | 0 | 0 |
| 17 | applied | +2 | +3 |
| 18 | applied | -1 | +9 |
| 19 | abstained | 0 | 0 |
| 20 | applied | 0 | 0 |

GW17 is the first week in this tranche where accepted evidence improved both
same-state decisions. GW18 is more revealing: evidence cost one point on the
Scout state but added nine on the optimized state. The optimized evidence arm
still scored two fewer points than optimized structured that week because the
two arms entered with different inherited squads. The paired same-state result
therefore captures the current evidence decision; the arm-to-arm weekly score
captures the entire longitudinal policy path.

GW16 and GW20 show that accepted evidence is not automatically causally useful:
the adjustments passed protocol but did not change realised same-state points.
GW19 abstained. This reinforces the need for the separate live evidence
acquisition and retrieval work in `FPL-bsw.38.14`: success must be measured by
coverage of decision boundaries, candidate recall, decision changes, and
paired outcome impact rather than by document or claim volume.

## Integrity at GW20

- Checkpoint is paused with `next_gameweek: 21`; no GW21 comparison exists.
- Canonical tree remains unchanged and the checkpoint reports
  `canonical_artifacts.unchanged: true`.
- GW20 uses the complete `sol-v3` source-host bundle with SHA-256
  `fd642ab2712cbe6e46ee7501c3c5cdc25d99f4a732911c3372e34b1369a7825c`.
- Focused enhanced replay and agent-fork regressions: 34 passed.
- Full repository suite: 627 passed in 414.70 seconds, with empty stderr and retained JUnit output.
- All four arms have continuous independently owned states through GW20.
- All plans passed deterministic validation before outcome reveal.

## Review questions before GW21

1. Preserve this path as the frozen primary replay; any alternative evidence
   threshold or retrieval policy must be a separately named fork.
2. Review GW17 and GW18 as the most informative causal cases, including which
   candidate, transfer, captain, and lineup changes produced their paired
   effects.
3. Continue the historical smoke-test evidence set through GW38, while keeping
   the broader live acquisition/retrieval system in `FPL-bsw.38.14` separate
   from this retrospective trajectory.
4. Keep chips and data-family ablations out of the path unless introduced as
   preregistered comparison arms.
