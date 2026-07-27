# Live 2026/27 initial-squad selection policy

The season-start squad is a distinct decision problem. It must not be produced
by pretending that the weekly transfer optimiser already owns a squad and can
replace all 15 players.

The lab consumes one immutable, point-in-time player packet frozen before the
selection deadline. That packet binds the ruleset, feature state, forecast
model, capture time, decision cutoff and six-Gameweek forecast horizon. Every
player record supplies launch price, position, club, expected points,
start probability, uncertainty and the declared context features used for
promoted-team/new-signing shrinkage, World Cup fatigue, transfer optionality
and early-Wildcard risk. A record first available after the cutoff is rejected.

## Arms and equal inputs

The deterministic and robust arms search the same bounded player pool. The
deterministic arm uses the point forecast; the robust arm applies the
preregistered uncertainty penalty. Both include the same structured context,
captaincy, bench/autosub and transfer-optionality terms.

The evidence-agent and challenger arms may either:

1. submit bounded per-player expected-points adjustments with evidence IDs,
   rationale and pre-cutoff availability time, then invoke the same optimiser;
   or
2. submit a complete 15-player proposal.

The human/reference arm submits a declared 15. Every external arm must bind its
completion metadata to the base packet hash. Every proposed squad is rescored
and rules-validated by deterministic code. An invalid or incomplete arm remains
visible as rejected or not run; it cannot silently become the robust arm.

This design permits a more capable model to add value through better use of
unstructured information while preventing it from seeing different structured
engine outputs or enforcing FPL rules.

## Objective

For each of the six declared Gameweeks, the lab selects a legal XI, captain,
vice-captain and ordered bench. The objective reports:

- discounted starting-XI and captain value;
- bench and formation-preserving autosub value;
- uncertainty penalty;
- promoted-team and new-signing shrinkage;
- World Cup fatigue adjustment;
- transfer-optionality bonus;
- early-Wildcard-risk penalty.

The search is a deterministic bounded beam, not a claim of global optimality.
Its shortlist sizes, beam width, state counts and pruning counts are included
in every output. Alternatives and one-factor uncertainty sensitivity are
reported alongside the selected proposal.

## Approval and execution boundary

Generation is always advisory-only. The output contains
`account_writes: false` and has no authenticated FPL or browser interface.

A proposal is `ready_for_manual_entry` only when:

- the deterministic and robust arms completed;
- the selected arm completed and is bound to the frozen packet;
- the separately maintained 2026/27 rules activation artifact is active and
  matches the ruleset hash;
- the owner approval names the selected arm and binds the exact proposal and
  packet hashes;
- approval occurred no later than the decision cutoff.

Otherwise the output is still inspectable, but its approval gate is `blocked`
with explicit reasons. `FPL-bsw.38.11` owns rules verification and sign-off;
this Bead consumes that result rather than weakening it.

## Historical use

The same code may be used in the enhanced 2025/26 replay with a historical
rules mapping and a genuinely point-in-time reconstructed packet. Such runs
remain exploratory and production-ineligible. Their purpose is to find state,
forecast and process failures before the live season, not to tune the 2026/27
policy on known outcomes.
