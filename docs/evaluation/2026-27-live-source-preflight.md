# 2026/27 live-source preflight

## Purpose

`scripts/preflight_live_sources.py` is the no-network operational readiness
check for currently approved live input families. It verifies only whether a
configured environment-variable value is non-blank in the process that will
run the capture scheduler. It does not validate a key with a provider, create
an HTTP client, make a network request, write an account, or print, persist or
hash a credential value.

A missing credential is a successful **degraded** result, not a reason to
retry or to manufacture an input. The decision pipeline must retain the shared
structured forecast and expose the affected family in its decision record.

## Current source families

| Family | Structural readiness rule | Absent-key result |
| --- | --- | --- |
| Odds | `THE_ODDS_API_KEY` is non-blank | `missing_credential_no_network` |
| Line-ups/minutes | A provider is explicitly selected first; only that provider's key is inspected | `no_provider_selected`, or `missing_credential_no_network` after valid selection |

The current line-ups/minutes configuration deliberately has
`selected_provider: null`. Candidate provider keys are neither read nor named
in the preflight report until an owner-approved provider selection is made.
Selection still requires registry enablement, rights approval, owner approval
and the representative-fixture trial described in
`config/data_sources/2026-27-lineups-minutes.json`.

## Operator procedure

1. Store the Odds key as the **user-level** environment variable
   `THE_ODDS_API_KEY`. Do not put it in a command, source file, JSON, `.env`
   file committed to Git, or agent prompt. The masked PowerShell setup and
   restart instructions are maintained in
   `docs/data-sources/deadline-capture-scheduler.md`.
2. Close and reopen Codex or PowerShell after setting the user environment
   variable so the scheduler process inherits it.
3. From the repository root, run:

   ```powershell
   & 'C:\Users\Alastair\FPL\.venv\Scripts\python.exe' scripts\preflight_live_sources.py
   ```

4. Confirm `families.odds.credential_present` is `true` and
   `families.odds.status` is `ready_structural`. This proves only process-local
   presence. Provider validity, quota and response shape remain the scheduled
   capture's responsibility.
5. Treat any degraded family as unavailable. Do not compensate by retrying
   this preflight or by treating missing evidence as positive availability.

## Safe report contract

The JSON output contains the provider ID, environment-variable *name*, boolean
presence, degradation reason, `network_actions: false` and
`account_writes: false`. It intentionally contains no secret value, length,
prefix, digest, request URL or manifest. The command exits successfully for a
valid configuration even when sources are degraded, allowing the scheduler to
record readiness without creating a retry loop. Invalid configuration fails
closed with a non-zero exit instead.

## Test coverage

`tests/data/test_live_source_preflight.py` proves the following:

- no Odds key produces an explicit safe degraded result;
- a present test key changes readiness structurally and never appears in the
  report;
- no candidate line-ups key is inspected while provider selection is null;
- the selected provider key is inspected only after explicit selection and
  approval gates pass; and
- an unregistered selected provider remains degraded with no network action.
