# Early-season evidence reconstruction: GW1-GW11

The sealed manifest at
`evals/evidence-forks/2025-26/early-season-manifest.json` inventories the
historical evidence recovered for the part of the 2025/26 replay that precedes
the existing GW12 evidence experiment.

Every source was first observed by this project in July 2026, after the
relevant deadline. Publication before a deadline establishes only that the
information existed publicly; it does not prove that the historical policy
observed it. Every entry is therefore exploratory, production-ineligible and
promotion-ineligible.

## Coverage

| GW | Decision boundary | Recovered evidence | Primary use |
|---:|---|---|---|
| 1 | Initial 15 and captain | Official FPL opening advice | Separate seed reference, never an ordinary transfer bundle |
| 2 | Palmer lineup; Salah alternatives | Official Scout GW2 squad | Negative case: Palmer was favoured before an unforeseeable warm-up injury |
| 3 | Palmer transfer and lineup | Official Scout fitness doubt | Availability-sensitive decision |
| 4 | Palmer transfer | Chelsea pre-match training test | Partial availability, not a confirmed absence |
| 5 | Salah captain; Chelsea attackers | Official captain analysis | Reference-policy evidence |
| 6 | Transfer and lineup | Timestamped expected-lineup report | Palmer absence and Porro rotation risk |
| 7 | Murillo-to-Gabriel transfer | Gabriel fitness report | Evidence against an attractive defender purchase |
| 8 | Semenyo purchase and captaincy | Official captain analysis | Overlaps with structured form and fixtures |
| 9 | Gabriel lineup | Deadline-day team news | Renewed availability uncertainty |
| 10 | Mbeumo and Woltemade purchases | Official Scout selection | Direct support for the canonical move |
| 11 | Gabriel hold and lineup | Official Scout selection | Positive continuation signal |

The scope is decision-boundary targeted, not an attempt to reproduce every
article published each week. Official Premier League advice and club
communications are preferred. Three secondary sources are retained as manual
metadata-and-short-excerpt citations only; automated crawling remains
disabled, and their unregistered status is explicit in the manifest.

## Quality interpretation

The manifest contains 12 admitted candidates across 11 weeks. Only one source
has a second-level publication timestamp; eleven have a dated page or an
explicit pre-deadline context with coarser precision. All 12 were observed
after the deadline. Those facts prevent a high coverage count from masquerading
as production-quality evidence.

Admission means only that the source is attributable, published before the
episode cutoff, hash-intact, relevant to a declared boundary and explicit
about its limitations. It does not mean the claim is correct, independent of
structured data or safe to convert directly into a forecast adjustment.

GW2 demonstrates the distinction. The recovered source favoured Palmer, but
his injury occurred in the warm-up after the deadline. More pre-deadline prose
could not have solved that event. GW8 and GW10, meanwhile, largely restate form
and fixture signals already available to deterministic code; an agent must not
receive double credit for them.

## Replay boundary

GW2-GW11 now proceed in two modes. Isolated runs start from each canonical
weekly state. A longitudinal run starts from the canonical post-GW1 state and
carries its own squad, bank, purchase prices and free transfers. Its resulting
GW12 state is compared with, not substituted for, the accepted canonical GW12
state.

GW1 follows a different path. The official Scout squad remains the canonical
control. Any evidence-assisted initial 15 becomes a separate seed branch.

Run the validator and builder from the repository root:

    .venv\Scripts\python.exe -m pytest tests/evaluation/test_early_season_evidence_manifest.py -q
    .venv\Scripts\python.exe -m scripts.build_early_season_evidence_manifest

An identical rerun is accepted. A conflicting generated artifact, changed
excerpt, duplicate claim, cutoff mismatch or episode-hash mismatch fails
closed.
