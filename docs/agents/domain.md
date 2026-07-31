# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring the codebase.

## Before exploring, read these

- **`AGENTS.md`** and **`docs/plan.md`** — project ground rules, architecture and sequencing (always).
- **`CONTEXT.md`** at the repo root if it exists (created lazily by `/domain-modeling`).
- **`CONTEXT-MAP.md`** at the repo root if it exists — points at one `CONTEXT.md` per context.
- **`docs/decisions/`** — architecture decision records for this lab (British English; equivalent role to a typical `docs/adr/` tree). Prefer ADRs that touch the area you're about to work in.

If `CONTEXT.md` / `CONTEXT-MAP.md` don't exist, **proceed silently**. Don't flag their absence; don't suggest creating them upfront. The `/domain-modeling` skill creates them lazily when terms or decisions actually get resolved.

## File structure

Single-context repo:

```
/
├── AGENTS.md
├── docs/plan.md
├── CONTEXT.md                 ← optional; created by domain-modeling
├── docs/decisions/            ← ADRs for this project
└── src/
```

## Use the glossary's vocabulary

When your output names a domain concept (in an issue title, a refactor proposal, a hypothesis, a test name), use the term as defined in `CONTEXT.md` when present, otherwise prefer terms from `docs/plan.md` Appendix A and existing ADRs. Don't drift to synonyms the glossary explicitly avoids.

## Flag ADR conflicts

If your output contradicts an existing ADR under `docs/decisions/`, surface it explicitly rather than silently overriding.
