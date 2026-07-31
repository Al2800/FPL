---
name: github-issue-from-bead
description: Convert retired Beads work items into GitHub Issues for this repo. Use when migrating Beads, drafting backlog tickets from .beads/issues.jsonl or .github/issue-defs, or creating implementation issues with acceptance criteria.
---

# GitHub Issues from Beads (FPL lab)

Beads (`.beads/`) are an **archive only**. Do not claim, update or close Beads
for active work. Active tracking is **GitHub Issues**.

## When to use

- User asks to convert Beads into tickets/issues
- User asks to open backlog items from outstanding Beads or issue-defs
- Agent needs the template for a well-formed FPL lab GitHub Issue

## Hard constraints (from AGENTS.md)

1. Rules stay in versioned YAML under `control/rules/` — never hard-code into prompts.
2. No collector without a registry entry and confirmed licence / allowed use.
3. Point-in-time fields on temporal records; decisions filterable by `available_at <= deadline`.
4. Deterministic core: LLMs propose only.
5. No secrets in the repo or model context.
6. Phase 0/1 only — do not implement deferred Phase features.

## Create issues from committed defs

Preferred path for the seven migrated items:

```bash
python3 -m scripts.create_github_issues_from_defs
# or --dry-run first
```

Or run workflow **Create outstanding GitHub issues from defs**.

The Cursor cloud-agent `gh` token often lacks `createIssue`; prefer a
collaborator PAT or the workflow `GITHUB_TOKEN` with `issues: write`.

## Issue body template

```markdown
## Parent / origin

Migrated from Bead `FPL-…` (status, priority). Related issues: …

## Status at migration

…

## What

End-to-end behaviour / residual scope. Not a layer-by-layer rewrite.

## Acceptance criteria

- [ ] …
- [ ] Focused test command: `python -m pytest -q …`

## Blocked by

None — can start immediately
# or
- Blocked by #N (owner-gated registry / approval)

## Non-goals

…
```

## Labels

Ensure these exist (the create script upserts them): `p0`–`p3`, `epic`,
`owner-gated`, `migrated-from-beads`, plus standard `bug` / `enhancement`.

## After creating issues

1. Do not edit Beads status to “mirror” GitHub — ignore Beads.
2. Link ExecPlans under `docs/execplans/` to the GitHub issue number.
3. Update handoff docs if they still say Beads are authoritative.
