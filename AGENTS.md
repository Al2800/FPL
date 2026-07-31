# Agent instructions

This repository is the FPL Agentic Decision Laboratory. Read `docs/plan.md` before doing any work — it is the source of truth for scope, architecture and sequencing.

## Ground rules

1. **Rules are data.** FPL rules live in versioned YAML under `control/rules/` (see plan §5). Never hard-code budget, formation, transfer or chip rules into prompts, models or optimiser code.
2. **No collection without registration.** Do not write or enable a data collector unless its source has an entry in `control/sources/source-registry.yaml` with a confirmed `licence_status` and `allowed_use` (plan §6.2). Collectors for unresolved sources stay disabled by default.
3. **Point-in-time discipline.** Every temporal record carries `published_at`, `observed_at`, `effective_at` and `finalised_at` where applicable. Anything used in a decision must be filterable by `available_at <= deadline` (plan §7.2, §11.4).
4. **Deterministic core.** Rules validation, scoring and optimisation are deterministic code with tests. LLM components propose; they never enforce, approve or execute (plan §4.3, §13.3).
5. **No secrets in the repo or in model context.** Credentials, browser sessions, raw data dumps and screenshots stay out of Git (plan §22.3). Respect `.gitignore`.
6. **Phase discipline.** The current phase is Phase 0/1 (governance, then advisory MVP). Do not implement deferred features (vector retrieval, rival analysis, live-match agents, computer-use execution, cloud infrastructure) — anticipate their interfaces only (plan §18, §19).

## Work packages

Work is organised into non-overlapping packages WP-01 to WP-10 (plan §24). When asked to work on a package, stay within its boundary and record open questions rather than expanding scope. Key sequencing: WP-01 (rules audit) and WP-02 (source governance) gate all automated collection; the rules validator (WP-06) precedes any LLM recommendation workflow.

## Work tracking

**GitHub Issues are authoritative.** Beads under `.beads/` are a historical archive only — do not claim, update, close or sync Beads for active work. Outstanding Beads were converted into issue definitions under `.github/issue-defs/`; materialise them with `python3 -m scripts.create_github_issues_from_defs` or the workflow in `.github/workflows/create-outstanding-issues.yml`. See `docs/operations/tracker-migration-beads-to-github.md` and the skill `.agents/skills/github-issue-from-bead/SKILL.md`.

## Conventions

- Python for pipeline code; Parquet + DuckDB for analytical data; SQLite/PostgreSQL for operational state (plan §8.2).
- British English in documentation, matching the plan.
- Every derived record retains source references and the transformation, rules, model and prompt versions used (plan §9.5).
- Decisions with trade-offs get an architecture decision record in `docs/decisions/`.
