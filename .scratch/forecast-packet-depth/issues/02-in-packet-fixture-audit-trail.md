# 02 — In-packet fixture context and per-week multiplier audit trail

**Blocked by:** None

**Status:** open

**Type:** task

**Category:** enhancement

## Handoff Brief

**Summary:** Fixture strength already changes EP inside the forecaster, but the
frozen packet collapses that to six floats. Agents and humans must be able to
reason primarily over an explicit per-player-week audit trail.

### Current behaviour

- Official fixtures are admitted (`fixture_count: 380`) and hash-bound.
- Forecaster builds per-GW `fixture_components` with `fixture_id`,
  `opponent_club_id`, `was_home`, `team_multiplier`, rate/event EP splits.
- Packet player rows expose only:
  `expected_points`, `start_probability`, `uncertainty`, club_id, flags, price.
- No opponent name/id, home/away, FDR, Elo, xG multipliers, or kickoff on the
  row. Strategy briefings cannot see “why GW3 dips” without leaving the packet.

### Desired behaviour

For each eligible player and each horizon Gameweek, the decision packet (or a
hash-bound companion artefact referenced by the packet) includes at least:

| Field | Purpose |
|---|---|
| `fixture_id` / blank|double markers | Identity + DGW/BGW |
| `opponent_club_id` (+ resolvable name in companion) | Human/agent readability |
| `was_home` | Home advantage reasoning |
| `kickoff_time` if known | Congestion / deadline context |
| Official FDR (team side) | Baseline difficulty signal |
| `attack_multiplier` / `defence_multiplier` / `team_multiplier` | Model audit |
| Elo / odds contribution flags or values when present | Provenance of tilt |
| `expected_minutes` | Minutes story beside EP |
| Component EP (rate vs event if weight>0) | Explainability |

Constraints:

1. Optimiser may keep consuming compact vectors; audit trail must not break
   `validate_initial_squad_packet` without a versioned schema bump.
2. Prefer a versioned `fixture_audit` (or `player_week_context`) block that is
   content-addressed and cited from `feature_state` / lineage.
3. Must be readable by strategy agents **and** humans in review markdown.
4. Point-in-time: only fixtures/multipliers available at decision cutoff.

### Acceptance criteria

- [ ] Schema + docs for the audit surface (British English).
- [ ] Checkpoint rebuild emits audit for GW1–GW6 eligible players.
- [ ] Haaland/Rogers-style examples show opponent + multipliers aligning with
      EP variation.
- [ ] Strategy research prompt / packet builder can attach a bounded view of
      this audit without dumping the full 509×6 table into the LLM context
      (shortlist or top-N by EP).
- [ ] Tests: hash stability; blank/double markers; cutoff-safe fields only.

### Out of scope

- Changing how multipliers are calculated (ticket 01).
- Availability-driven minutes (ticket 03).
