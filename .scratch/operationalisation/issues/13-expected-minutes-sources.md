# 13 — Owner decision: external expected-minutes sources

Status: ready-for-human
Type: task
Track: Owner/source gate

## Context

Expected minutes is the acknowledged weakest point (plan §7.1). The official
team-sheet citation path is already registered, enabled and rehearsed for
manual use (`official-lineups-minutes`; decision dated 31 July 2026). It is not
an automated predicted-line-up feed.

Fantasy Football Scout, Rotowire, Sofascore and Fotmob are candidates named in
the plan but do **not** have individual registry entries. Understat/FBref and
ClubElo remain disabled. No collector may be implemented until a named source
has a confirmed registry entry.

## Decision required from the owner

1. Decide whether the manual official citation path is sufficient for the first
   live season.
2. If not, select a **named** predicted-line-up or confirmed-line-up challenger
   for terms, cost and retention review.
3. Add or update its exact registry entry with `licence_status`, `allowed_use`,
   collection method, retention, attribution and owner approval. A prohibited
   or unresolved source stays disabled.
4. Separately decide whether Understat/FBref or ClubElo warrants review; these
   are not implicitly approved by selecting a line-up source.

## Done when

- The owner records either “official manual path only” or a named external
  source trial with a complete registry decision.
- Ticket 19 is updated to identify only the approved source, collection method,
  admission thresholds and fallback before implementation starts.

## Boundaries

This ticket makes the source decision only. Collection and benchmarking are
separate in ticket 19.
