# Tracker migration: Beads → GitHub Issues

**Date:** 31 July 2026  
**Status:** Definitions committed; create issues via script or workflow.

## Decision

Active work tracking moves from Beads (`.beads/issues.jsonl`) to **GitHub
Issues**. Beads remain in the repository as a historical archive only.

Agents and humans should:

- **Ignore** Beads status (`open` / `in_progress` / `closed`) for planning.
- **Not** run `bd create|update|close|sync` for new work.
- Open and manage GitHub Issues (see `.github/issue-defs/`).

## Outstanding Beads converted

| Former bead | Former status | Issue def | Notes |
|---|---|---|---|
| `FPL-cfb` | open | `fpl-cfb.md` | P0 CI artifact boundary |
| `FPL-bsw` | open | `fpl-bsw.md` | Epic residual; 37/38 children already closed |
| `FPL-bsw.38` | in_progress | `fpl-bsw-38.md` | All 14 children closed; residual policy/approval |
| `FPL-eah` | in_progress | `fpl-eah.md` | Lineup capture / low-cost challenger |
| `FPL-761` | open | `fpl-761.md` | Owner-gated historical rank source |
| `FPL-762` | open | `fpl-762.md` | Prospective 2026/27 standings capture |
| `FPL-2xu` | in_progress | `fpl-2xu.md` | Contract implemented; blocked on source |

## How to materialise the Issues

```bash
python3 -m scripts.create_github_issues_from_defs --dry-run
python3 -m scripts.create_github_issues_from_defs
```

Or Actions → **Create outstanding GitHub issues from defs** → Run workflow.

Creation is idempotent by issue title.

## Skill

Project skill: `.agents/skills/github-issue-from-bead/SKILL.md` — use when
drafting or migrating further backlog items into GitHub Issues.
