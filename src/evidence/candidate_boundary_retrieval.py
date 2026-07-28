"""Deterministic attention routing from engine candidates to evidence claims."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from datetime import datetime, timezone
import math
from typing import Any

from src.evidence.live_evidence_ledger import (
    live_evidence_hash,
)
from src.forecasting.live_faithful import artifact_hash
from src.optimisation.io import fingerprint


class CandidateBoundaryRetrievalError(ValueError):
    """Raised when candidate discovery or evidence retrieval is unsafe."""


def _seal(value: Mapping[str, Any]) -> dict[str, Any]:
    result = deepcopy(dict(value))
    result["content_sha256"] = artifact_hash(result)
    return result


def _number(value: Any, field: str, *, minimum: float | None = None) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
        or (minimum is not None and float(value) < minimum)
    ):
        raise CandidateBoundaryRetrievalError(
            f"{field} must be a finite number"
        )
    return float(value)


def _timestamp(value: Any, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise CandidateBoundaryRetrievalError(
            f"{field} must be an ISO-8601 timestamp"
        ) from exc
    if parsed.tzinfo is None:
        raise CandidateBoundaryRetrievalError(
            f"{field} must include a timezone"
        )
    return parsed.astimezone(timezone.utc)


def _reject_outcome_fields(
    value: Any,
    *,
    forbidden: set[str],
    path: str = "$",
) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            name = str(key)
            if name.lower() in forbidden:
                raise CandidateBoundaryRetrievalError(
                    f"Forbidden outcome field at {path}.{name}"
                )
            _reject_outcome_fields(
                item, forbidden=forbidden, path=f"{path}.{name}"
            )
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _reject_outcome_fields(
                item, forbidden=forbidden, path=f"{path}[{index}]"
            )


def _player_index(solver_input: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    rows = solver_input.get("players")
    if not isinstance(rows, list) or not rows:
        raise CandidateBoundaryRetrievalError(
            "solver input requires a non-empty player market"
        )
    result: dict[str, dict[str, Any]] = {}
    for source in rows:
        row = deepcopy(dict(source))
        player_id = str(row.get("player_id", ""))
        if not player_id or player_id in result:
            raise CandidateBoundaryRetrievalError(
                "market player IDs must be unique and non-empty"
            )
        for field in ("position", "club_id", "now_cost"):
            if field not in row:
                raise CandidateBoundaryRetrievalError(
                    f"market player {player_id} is missing {field}"
                )
        row["player_id"] = player_id
        row["club_id"] = str(row["club_id"])
        row["position"] = str(row["position"])
        row["now_cost"] = _number(row["now_cost"], "now_cost", minimum=0)
        row["expected_points"] = _number(
            row.get("expected_points", 0.0),
            "expected_points",
        )
        result[player_id] = row
    return result


def _planning_points(
    player: Mapping[str, Any],
    discount_factors: Sequence[Any],
) -> float:
    if player.get("expected_points_by_gameweek") is not None:
        values = player["expected_points_by_gameweek"]
        if not isinstance(values, list) or not values:
            raise CandidateBoundaryRetrievalError(
                "expected_points_by_gameweek must be a non-empty list"
            )
        factors = [
            _number(value, "discount_factor", minimum=0)
            for value in discount_factors
        ]
        if len(values) < len(factors):
            raise CandidateBoundaryRetrievalError(
                "expected_points_by_gameweek does not cover the horizon"
            )
        return round(
            sum(
                _number(value, "expected_points_by_gameweek") * factor
                for value, factor in zip(values, factors, strict=False)
            ),
            6,
        )
    if player.get("planning_expected_points") is not None:
        return _number(
            player["planning_expected_points"], "planning_expected_points"
        )
    return _number(player.get("expected_points", 0.0), "expected_points")


def _candidate_objective(candidate: Mapping[str, Any]) -> float:
    return _number(candidate.get("objective"), "candidate objective")


def _entities_for_players(
    player_ids: Sequence[str],
    market: Mapping[str, Mapping[str, Any]],
) -> dict[str, list[str]]:
    clubs: set[str] = set()
    fixtures: set[str] = set()
    for player_id in player_ids:
        row = market[player_id]
        clubs.add(str(row["club_id"]))
        fixtures.update(str(value) for value in row.get("fixture_ids", []))
    return {
        "player_ids": sorted(set(player_ids)),
        "club_ids": sorted(clubs),
        "fixture_ids": sorted(fixtures),
    }


def _boundary(
    *,
    boundary_id: str,
    decision_type: str,
    incumbent_id: str,
    alternative_id: str,
    margin_points: float,
    max_swing_points: float,
    market: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    players = sorted(set((incumbent_id, alternative_id)))
    entities = _entities_for_players(players, market)
    return {
        "boundary_id": boundary_id,
        "decision_type": decision_type,
        "incumbent_id": incumbent_id,
        "alternative_id": alternative_id,
        "margin_points": round(max(0.0, margin_points), 6),
        "max_swing_points": round(max(0.0, max_swing_points), 6),
        "entities": entities,
    }


def discover_candidate_boundaries(
    *,
    solver_input: Mapping[str, Any],
    solver_output: Mapping[str, Any],
    config: Mapping[str, Any],
    identity_aliases: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Project the engine's evaluated candidates into a bounded attention set."""

    if str(solver_input.get("season", "")) != str(config.get("season", "")):
        raise CandidateBoundaryRetrievalError(
            "Solver input season does not match evidence coverage policy"
        )
    forbidden = {
        str(value).lower()
        for value in config.get("forbidden_outcome_fields", [])
    }
    _reject_outcome_fields(solver_input, forbidden=forbidden)
    _reject_outcome_fields(solver_output, forbidden=forbidden)
    expected_fingerprint = fingerprint(dict(solver_input))
    if str(solver_output.get("input_fingerprint", "")) != expected_fingerprint:
        raise CandidateBoundaryRetrievalError(
            "Solver output input fingerprint does not match solver input"
        )

    market = _player_index(solver_input)
    owned_ids = [str(value) for value in solver_input.get("squad_player_ids", [])]
    if not owned_ids or len(owned_ids) != len(set(owned_ids)):
        raise CandidateBoundaryRetrievalError(
            "squad_player_ids must be unique and non-empty"
        )
    missing = sorted(set(owned_ids) - set(market))
    if missing:
        raise CandidateBoundaryRetrievalError(
            f"Owned players missing from market: {missing}"
        )
    selected = solver_output.get("selected")
    candidates = solver_output.get("all_candidates")
    if not isinstance(selected, Mapping) or not isinstance(candidates, list):
        raise CandidateBoundaryRetrievalError(
            "solver output requires selected and all_candidates"
        )
    selected_objective = _candidate_objective(selected)
    factors = list(solver_input.get("discount_factors", [1.0]))

    pair_rows: dict[tuple[str, str], dict[str, Any]] = {}
    for candidate in candidates:
        if not isinstance(candidate, Mapping):
            raise CandidateBoundaryRetrievalError(
                "solver candidates must be objects"
            )
        objective = _candidate_objective(candidate)
        if objective > selected_objective + 1e-6:
            raise CandidateBoundaryRetrievalError(
                "An evaluated candidate exceeds the selected objective"
            )
        for move in candidate.get("transfers", []):
            out_id = str(move.get("player_out_id", ""))
            in_id = str(move.get("player_in_id", ""))
            if (
                out_id not in owned_ids
                or in_id not in market
                or in_id in owned_ids
            ):
                raise CandidateBoundaryRetrievalError(
                    "Engine candidate contains an invalid transfer identity"
                )
            outgoing = market[out_id]
            incoming = market[in_id]
            if outgoing["position"] != incoming["position"]:
                raise CandidateBoundaryRetrievalError(
                    "Engine candidate transfer changes position"
                )
            gain = _planning_points(incoming, factors) - _planning_points(
                outgoing, factors
            )
            row = {
                "candidate_id": f"replacement:{out_id}:{in_id}",
                "player_id": in_id,
                "player_out_id": out_id,
                "position": incoming["position"],
                "club_id": incoming["club_id"],
                "now_cost": incoming["now_cost"],
                "expected_points": incoming["expected_points"],
                "planning_expected_points": _planning_points(
                    incoming, factors
                ),
                "replacement_gain_points": round(gain, 6),
                "candidate_objective": objective,
                "objective_margin_points": round(
                    selected_objective - objective, 6
                ),
                "status": str(incoming.get("status", "a")),
                "start_probability": (
                    float(incoming["start_probability"])
                    if incoming.get("start_probability") is not None
                    else None
                ),
                "fixture_ids": sorted(
                    str(value) for value in incoming.get("fixture_ids", [])
                ),
                "source": "evaluated_solver_candidate",
            }
            key = (out_id, in_id)
            prior = pair_rows.get(key)
            if prior is None or (
                row["objective_margin_points"],
                -row["replacement_gain_points"],
                row["candidate_id"],
            ) < (
                prior["objective_margin_points"],
                -prior["replacement_gain_points"],
                prior["candidate_id"],
            ):
                pair_rows[key] = row

    policy = config["candidate_discovery"]
    per_position = int(policy["maximum_external_per_position"])
    maximum_external = int(policy["maximum_external_candidates"])
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in pair_rows.values():
        grouped.setdefault(str(row["position"]), []).append(row)
    retained_pairs: list[dict[str, Any]] = []
    omitted_pairs: list[str] = []
    for position in sorted(grouped):
        ranked = sorted(
            grouped[position],
            key=lambda row: (
                row["objective_margin_points"],
                -row["planning_expected_points"],
                row["now_cost"],
                row["player_id"],
                row["player_out_id"],
            ),
        )
        retained_pairs.extend(ranked[:per_position])
        omitted_pairs.extend(
            row["candidate_id"] for row in ranked[per_position:]
        )
    retained_pairs.sort(
        key=lambda row: (
            row["objective_margin_points"],
            -row["planning_expected_points"],
            row["position"],
            row["player_id"],
            row["player_out_id"],
        )
    )
    omitted_pairs.extend(
        row["candidate_id"] for row in retained_pairs[maximum_external:]
    )
    retained_pairs = retained_pairs[:maximum_external]

    boundaries: list[dict[str, Any]] = []
    for row in retained_pairs[: int(policy["maximum_transfer_boundaries"])]:
        out_id = str(row["player_out_id"])
        in_id = str(row["player_id"])
        boundaries.append(
            _boundary(
                boundary_id=f"transfer:{out_id}:{in_id}",
                decision_type="transfer",
                incumbent_id=out_id,
                alternative_id=in_id,
                margin_points=float(row["objective_margin_points"]),
                max_swing_points=max(
                    abs(float(row["replacement_gain_points"])),
                    float(row["objective_margin_points"]),
                ),
                market=market,
            )
        )

    lineup = selected.get("lineup", {})
    starting = [
        str(value) for value in lineup.get("starting_xi_ids", [])
        if str(value) in market
    ]
    bench = [
        str(value) for value in lineup.get("bench_ids", [])
        if str(value) in market
    ]
    if starting and bench:
        weakest = min(
            starting,
            key=lambda player_id: (
                _planning_points(market[player_id], factors),
                player_id,
            ),
        )
        strongest_bench = min(
            bench,
            key=lambda player_id: (
                -_planning_points(market[player_id], factors),
                player_id,
            ),
        )
        margin = abs(
            _planning_points(market[weakest], factors)
            - _planning_points(market[strongest_bench], factors)
        )
        boundaries.append(
            _boundary(
                boundary_id=f"lineup:{weakest}:{strongest_bench}",
                decision_type="lineup",
                incumbent_id=weakest,
                alternative_id=strongest_bench,
                margin_points=margin,
                max_swing_points=max(margin, 0.1),
                market=market,
            )
        )
    captain = str(lineup.get("captain_id", ""))
    vice = str(lineup.get("vice_captain_id", ""))
    if captain in market and vice in market and captain != vice:
        margin = abs(
            _planning_points(market[captain], factors)
            - _planning_points(market[vice], factors)
        )
        boundaries.append(
            _boundary(
                boundary_id=f"captaincy:{captain}:{vice}",
                decision_type="captaincy",
                incumbent_id=captain,
                alternative_id=vice,
                margin_points=margin,
                max_swing_points=max(margin, 0.1),
                market=market,
            )
        )

    selected_out = {
        str(move["player_out_id"])
        for move in selected.get("transfers", [])
    }
    by_out: dict[str, list[dict[str, Any]]] = {}
    for row in retained_pairs:
        by_out.setdefault(str(row["player_out_id"]), []).append(row)
    risk_statuses = set(policy["availability_risk_statuses"])
    risk_below = float(policy["start_probability_risk_below"])
    gain_threshold = float(
        policy["underperformance_replacement_gain_points"]
    )
    watchlist: list[dict[str, Any]] = []
    for player_id in owned_ids:
        player = market[player_id]
        reasons: list[str] = []
        if str(player.get("status", "a")) in risk_statuses:
            reasons.append("availability_risk")
        probability = player.get("start_probability")
        if probability is not None and float(probability) < risk_below:
            reasons.append("low_start_probability")
        if player_id in selected_out:
            reasons.append("selected_transfer_out")
        replacements = sorted(
            by_out.get(player_id, []),
            key=lambda row: (
                row["objective_margin_points"],
                -row["replacement_gain_points"],
                row["player_id"],
            ),
        )
        if replacements and float(
            replacements[0]["replacement_gain_points"]
        ) >= gain_threshold:
            reasons.append("structured_underperformance")
            reasons.append("strong_legal_replacement")
        if reasons:
            watchlist.append(
                {
                    "player_id": player_id,
                    "web_name": str(player.get("web_name", player_id)),
                    "position": player["position"],
                    "club_id": player["club_id"],
                    "expected_points": player["expected_points"],
                    "planning_expected_points": _planning_points(
                        player, factors
                    ),
                    "status": str(player.get("status", "a")),
                    "start_probability": (
                        float(probability) if probability is not None else None
                    ),
                    "reasons": sorted(set(reasons)),
                    "best_replacement_candidate_id": (
                        replacements[0]["candidate_id"]
                        if replacements
                        else None
                    ),
                }
            )
    watchlist.sort(
        key=lambda row: (
            "availability_risk" not in row["reasons"],
            "selected_transfer_out" not in row["reasons"],
            row["planning_expected_points"],
            row["player_id"],
        )
    )
    watchlist = watchlist[: int(policy["maximum_owned_watchlist"])]

    all_entities = {"player_ids": set(), "club_ids": set(), "fixture_ids": set()}
    for boundary in boundaries:
        for key in all_entities:
            all_entities[key].update(boundary["entities"][key])
    aliases = {
        str(source): str(target)
        for source, target in (identity_aliases or {}).items()
    }
    for source, target in aliases.items():
        if target in all_entities["player_ids"]:
            all_entities["player_ids"].add(source)

    return _seal(
        {
            "schema_version": "1.0",
            "season": str(solver_input.get("season", "")),
            "gameweek": int(solver_input.get("gameweek", 0)),
            "engine_input_fingerprint": expected_fingerprint,
            "engine_output_sha256": artifact_hash(solver_output),
            "selected_candidate_sha256": artifact_hash(selected),
            "owned_watchlist": watchlist,
            "external_candidates": retained_pairs,
            "boundaries": sorted(
                boundaries, key=lambda row: str(row["boundary_id"])
            ),
            "expanded_entities": {
                key: sorted(values) for key, values in all_entities.items()
            },
            "identity_aliases": aliases,
            "omitted": {
                "external_candidate_ids": sorted(set(omitted_pairs))
            },
            "information_policy": {
                "outcome_blind": True,
                "legal_candidate_source": "evaluated_solver_candidates",
                "silence_interpretation": "unknown_not_available",
            },
        }
    )


def _claim_entities(
    claim: Mapping[str, Any],
    aliases: Mapping[str, str],
) -> set[str]:
    result: set[str] = set()
    for binding in claim.get("identity_bindings", []):
        stable_id = str(binding.get("stable_id", ""))
        if stable_id:
            result.add(stable_id)
            if stable_id in aliases:
                result.add(str(aliases[stable_id]))
    return result


def build_candidate_boundary_packet(
    *,
    discovery: Mapping[str, Any],
    evidence_view: Mapping[str, Any],
    config: Mapping[str, Any],
) -> dict[str, Any]:
    """Retrieve a bounded cited packet for the deterministic attention set."""

    if discovery.get("content_sha256") != artifact_hash(discovery):
        raise CandidateBoundaryRetrievalError("Discovery hash mismatch")
    if evidence_view.get("content_sha256") != live_evidence_hash(evidence_view):
        raise CandidateBoundaryRetrievalError("Evidence view hash mismatch")
    retrieval = config["retrieval"]
    decision_at = _timestamp(evidence_view["decision_at"], "decision_at")
    type_rank = {
        str(key): int(value)
        for key, value in retrieval["decision_type_rank"].items()
    }
    authority_rank = {
        str(key): int(value)
        for key, value in retrieval["authority_rank"].items()
    }
    boundary_by_id = {
        str(row["boundary_id"]): row for row in discovery["boundaries"]
    }
    aliases = discovery.get("identity_aliases", {})
    ranked: list[dict[str, Any]] = []
    irrelevant: list[str] = []
    for claim in evidence_view.get("accepted", []):
        claim_id = str(claim["claim_id"])
        explicit_ids = sorted(
            boundary_id
            for boundary_id in claim.get("decision_boundary_ids", [])
            if boundary_id in boundary_by_id
        )
        entities = _claim_entities(claim, aliases)
        entity_ids = sorted(
            boundary_id
            for boundary_id, boundary in boundary_by_id.items()
            if entities.intersection(
                set(boundary["entities"]["player_ids"])
                | set(boundary["entities"]["club_ids"])
                | set(boundary["entities"]["fixture_ids"])
            )
        )
        matched_ids = sorted(set(explicit_ids) | set(entity_ids))
        if not matched_ids:
            irrelevant.append(claim_id)
            continue
        matches = [boundary_by_id[value] for value in matched_ids]
        matches.sort(
            key=lambda row: (
                type_rank.get(str(row["decision_type"]), 999),
                float(row["margin_points"]),
                str(row["boundary_id"]),
            )
        )
        best = matches[0]
        impact = round(
            float(claim.get("estimated_impact_points", 0.0))
            * float(claim["confidence"]),
            6,
        )
        available = _timestamp(claim["available_at"], "available_at")
        age_hours = max(
            0.0, (decision_at - available).total_seconds() / 3600.0
        )
        authority = str(
            claim.get("source_rights", {}).get("authority", "unknown")
        )
        ranked.append(
            {
                "claim": deepcopy(dict(claim)),
                "matched_boundary_ids": matched_ids,
                "match_basis": sorted(
                    (
                        (["explicit_boundary"] if explicit_ids else [])
                        + (["stable_entity"] if entity_ids else [])
                    )
                ),
                "best_decision_type": str(best["decision_type"]),
                "best_margin_points": float(best["margin_points"]),
                "confidence_weighted_impact_points": impact,
                "can_flip": impact >= float(best["margin_points"]),
                "age_hours": round(age_hours, 6),
                "fresh": age_hours
                <= float(retrieval["maximum_staleness_hours"]),
                "authority": authority,
                "authority_rank": authority_rank.get(authority, 999),
            }
        )
    ranked.sort(
        key=lambda row: (
            not row["can_flip"],
            type_rank.get(row["best_decision_type"], 999),
            row["best_margin_points"],
            -row["confidence_weighted_impact_points"],
            not row["fresh"],
            row["age_hours"],
            row["authority_rank"],
            -float(row["claim"]["confidence"]),
            str(row["claim"]["claim_id"]),
        )
    )

    maximum_claims = int(retrieval["maximum_claims"])
    maximum_characters = int(retrieval["maximum_claim_characters"])
    selected: list[dict[str, Any]] = []
    count_omitted: list[str] = []
    character_omitted: list[str] = []
    characters = 0
    for row in ranked:
        claim_id = str(row["claim"]["claim_id"])
        text_length = len(str(row["claim"]["claim_text"]))
        if len(selected) >= maximum_claims:
            count_omitted.append(claim_id)
        elif characters + text_length > maximum_characters:
            character_omitted.append(claim_id)
        else:
            selected.append(row)
            characters += text_length

    expanded = discovery["expanded_entities"]
    relevant_identity_tokens = {
        f"{entity_type}:{stable_id}"
        for entity_type, values in (
            ("player_uid", expanded.get("player_ids", [])),
            ("club_uid", expanded.get("club_ids", [])),
            ("fixture_uid", expanded.get("fixture_ids", [])),
        )
        for stable_id in values
    }
    relevant_conflicts = [
        deepcopy(dict(conflict))
        for conflict in evidence_view.get("conflicts", [])
        if any(
            token in str(conflict.get("subject_key", "")).split("|", 1)[-1]
            for token in relevant_identity_tokens
        )
    ]

    return _seal(
        {
            "schema_version": "1.0",
            "packet_id": (
                f"candidate-boundary:{discovery['season']}:"
                f"gw{int(discovery['gameweek']):02d}:"
                f"{evidence_view['decision_at']}"
            ),
            "status": "complete" if selected else "degraded",
            "degraded_reasons": (
                [] if selected else ["no_retrieved_active_evidence"]
            ),
            "decision_at": evidence_view["decision_at"],
            "engine_output_sha256": discovery["engine_output_sha256"],
            "discovery_sha256": discovery["content_sha256"],
            "evidence_view_sha256": evidence_view["content_sha256"],
            "boundaries": deepcopy(discovery["boundaries"]),
            "evidence": selected,
            "conflicts": relevant_conflicts,
            "exclusion_counts": {
                key: len(value)
                for key, value in evidence_view.get("excluded", {}).items()
            },
            "omitted": {
                "irrelevant_claim_ids": sorted(irrelevant),
                "claim_budget_claim_ids": sorted(count_omitted),
                "character_budget_claim_ids": sorted(character_omitted),
            },
            "limits": {
                "maximum_claims": maximum_claims,
                "maximum_claim_characters": maximum_characters,
                "selected_claims": len(selected),
                "selected_claim_characters": characters,
                "candidate_claims": len(ranked),
            },
            "context_contract": {
                "agent_visible_fields": [
                    "schema_version",
                    "packet_id",
                    "status",
                    "degraded_reasons",
                    "decision_at",
                    "engine_output_sha256",
                    "discovery_sha256",
                    "evidence_view_sha256",
                    "boundaries",
                    "evidence",
                    "conflicts",
                    "limits",
                    "identical_packet_required_for_all_agent_arms",
                    "frozen_no_evidence_control_required",
                ],
                "host_audit_only_fields": [
                    "exclusion_counts",
                    "omitted",
                ],
                "prompt_must_exclude_host_audit_fields": True,
            },
            "identical_packet_required_for_all_agent_arms": True,
            "frozen_no_evidence_control_required": True,
        }
    )
