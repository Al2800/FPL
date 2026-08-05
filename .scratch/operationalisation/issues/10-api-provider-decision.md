# 10 — Owner decision: API-backed model provider arm for scheduled agent runs

Status: resolved
Type: task
Track: D (automate the AI overlay)

## Context

Open Decision 8 resolved the first arm as `gpt-5.6-sol` via the ChatGPT-subscription Codex host — no API key, human-in-the-loop. That constraint makes the evidence/challenger arms unschedulable: nothing can run unattended at T-48h/T-8h/T-2h. ADR-0016 (Proposed) already notes that a hard currency cap requires a future API-backed provider.

## Decision required from the owner

1. Authorise (or decline) an API-backed provider arm for scheduled evidence/challenger runs, with per-Gameweek token/cost caps per §13.5.
2. If authorised: which provider(s), the cap values, and secret handling (environment/secret store — never Git or model context, §22.3).
3. Ratify or revise ADR-0016 accordingly.

The subscription-hosted Sol arm remains a valid experimental condition either way; this decision only adds an automatable arm alongside it.

## Done when

- An ADR records the decision. If declined, ticket 11 is re-scoped to "scheduled deterministic evidence checkpoint with manual agent hand-off" and this is noted there.

## Answer

Owner decision 5 August 2026: **decline** an API-backed arm. The always-on
local host schedules the existing ChatGPT-subscription Codex path
(ADR-0024 amending ADR-0016; ADR-0021 unchanged). Currency remains unavailable.
Ticket 11 re-scoped to subscription/deterministic scheduling.
