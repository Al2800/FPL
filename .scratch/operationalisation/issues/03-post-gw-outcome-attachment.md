# 03 — Post-GW outcome attachment and live retrospectives

Status: resolved
Type: task
Track: A (close the live loop)
Blocked by: 02

## Context

`docs/handover-brief.md` step 3. The replay harness supports `attach_outcome_points`, but live GDRs have no automated path from the 09:00 final lock to outcome, realised-gain-versus-do-nothing and retrospective fields (plan §§15.4, 17.3).

## Scope

- A post-lock script that ingests final `event/{gw}/live` + bootstrap state, attaches outcomes to the live GDR, computes decision metrics (transfer gain vs. do-nothing, captaincy gain/loss, bench effectiveness, hit recovery) and appends the retrospective section.
- Preserve revisions: provisional results must not overwrite final ones (§7.5 discipline applies to outcomes too).

## Done when

- A completed live GDR gains an outcome and retrospective from recorded data alone, and the paired-metrics utilities in `src/evaluation/` accept live records identically to replayed ones.

## Answer

Implemented:

- `src/orchestration/live_outcome_attachment.py` — event live → hidden outcomes →
  `score_revealed_outcome`, decision metrics (transfer/captain/bench/hit), and
  provisional/final revision gates
- `scripts/attach_live_gameweek_outcome.py` — CLI over recorded live + bootstrap

Tests: `tests/orchestration/test_live_outcome_attachment.py` — **4 passed**,
including paired-metrics acceptance via `paired_summary` on live realised
outcomes and refusal to overwrite finals with provisional/conflicting bytes.
