# Browser feasibility summary

**Status:** Documentary record only · browser execution remains **disabled**  
**Bead:** `FPL-bsw.6`  
**Related:** [browser-dry-run.md](browser-dry-run.md) · [ADR-0015](../../decisions/0015-browser-dry-run-stability.md)

## Purpose

Concisely record the feasibility conclusions from the already completed
authenticated FPL squad-selection dry run. This note does **not** authorise a
repeat browser session, production selectors, or any account write.

## Session boundary

| Claim | Status |
|---|---|
| Enter Squad was selected | **No** — Enter Squad was not selected |
| Account mutation / squad submission committed | **No** — no account mutation was committed |
| Browser execution enabled in this repository | **No** — remains disabled |

## Observed versus inferred

### Observed in the recorded dry-run session

- Authenticated squad state was readable.
- Player search worked.
- Add and remove of players was reversible within the staging UI.
- Pitch / list view toggle worked.
- Auto Pick could stage a squad proposal.
- Submission control state was visible (including that Enter Squad remained unselected).
- A successful reset returned the session to a clean staging state.

### Inferred (not independently re-verified here)

- The same selectors would remain stable across future FPL UI releases.
- Authentication cookies or sessions would survive long enough for an unattended
  multi-step write.
- A future write path would receive a reliable submission acknowledgement from
  the FPL UI under load.

### Untested

- Selecting Enter Squad.
- Any irreversible account write.
- Post-submission read-back of a mutated squad.
- Recovery after an ambiguous write (timeout, partial UI update, or conflicting
  read-back).
- Unattended multi-Gameweek operation.

## Feasibility conclusion

Read-only and reversible staging flows appear workable for a **future,
separately approved** execution bead. Submission and account mutation were
deliberately not exercised. Selector volatility, authentication lifetime,
screenshot evidence and ambiguous-write handling remain open risks before any
write path is enabled.

## Prerequisites for a future execution bead

Any later bead that proposes real writes must include all of the following
before activation:

1. Explicit owner approval for account writes.
2. Isolated test account or season state where possible.
3. Versioned selector map plus screenshot evidence for each critical step.
4. Pre-action read of current squad / bank / transfers.
5. Staged diff of the intended mutation.
6. Single write with **no-retry** on uncertainty.
7. Submission acknowledgement capture.
8. Post-action read-back verifying the intended state.
9. Ambiguous-write halt with rollback or escalation procedure.
10. Continued adherence to ADR-0015 live-stability thresholds before expanding
    beyond the isolated test.

Until those prerequisites are met under a separate approved bead, browser
execution stays disabled and empty `src/execution/` remains intentional.
