"""Append-only, cutoff-safe player availability evidence state."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from copy import deepcopy
from typing import Any

from src.evidence.lifecycle import (
    _parse_timestamp,
    assess_claim_for_decision,
    validate_availability_claim_semantics,
)
from src.forecasting.live_faithful import artifact_hash


class AvailabilityLedgerError(ValueError):
    """Raised when availability history is invalid or has been altered."""


def _seal(value: Mapping[str, Any]) -> dict[str, Any]:
    result = deepcopy(dict(value))
    result["content_sha256"] = artifact_hash(result)
    return result


def new_availability_ledger(
    *, season: str, created_at: str
) -> dict[str, Any]:
    """Create an empty immutable-history ledger."""

    if not isinstance(season, str) or not season:
        raise AvailabilityLedgerError("season must be a non-empty string")
    _parse_timestamp(created_at, field="created_at")
    return _seal(
        {
            "schema_version": "1.0",
            "ledger_id": f"availability-ledger:{season}",
            "season": season,
            "created_at": created_at,
            "claims": [],
        }
    )


def _known_by(claim: Mapping[str, Any], decision_at: str) -> bool:
    cutoff = _parse_timestamp(decision_at, field="decision_at")
    return all(
        _parse_timestamp(str(claim[field]), field=field) <= cutoff
        for field in ("published_at", "observed_at", "available_at")
    )


def validate_availability_ledger(ledger: Mapping[str, Any]) -> None:
    """Verify identity, integrity, ordering, and supersession references."""

    if ledger.get("schema_version") != "1.0":
        raise AvailabilityLedgerError("unsupported availability ledger schema")
    season = ledger.get("season")
    if not isinstance(season, str) or not season:
        raise AvailabilityLedgerError("ledger season must be a non-empty string")
    if ledger.get("ledger_id") != f"availability-ledger:{season}":
        raise AvailabilityLedgerError("availability ledger_id mismatch")
    _parse_timestamp(str(ledger.get("created_at", "")), field="created_at")
    if ledger.get("content_sha256") != artifact_hash(ledger):
        raise AvailabilityLedgerError("availability ledger content hash mismatch")
    claims = ledger.get("claims")
    if not isinstance(claims, list):
        raise AvailabilityLedgerError("availability ledger claims must be a list")
    seen: dict[str, Mapping[str, Any]] = {}
    previous_available = None
    for claim in claims:
        if not isinstance(claim, dict):
            raise AvailabilityLedgerError("availability claims must be objects")
        try:
            validate_availability_claim_semantics(claim)
        except ValueError as exc:
            raise AvailabilityLedgerError(str(exc)) from exc
        claim_id = str(claim["claim_id"])
        if claim_id in seen:
            raise AvailabilityLedgerError(
                f"duplicate availability claim_id: {claim_id}"
            )
        available = _parse_timestamp(
            str(claim["available_at"]), field="available_at"
        )
        if previous_available is not None and available < previous_available:
            raise AvailabilityLedgerError(
                "availability claims must be appended in available_at order"
            )
        for superseded_id in claim.get("supersedes_claim_ids", []):
            superseded = seen.get(str(superseded_id))
            if superseded is None:
                raise AvailabilityLedgerError(
                    f"superseded claim does not precede claim: {superseded_id}"
                )
            if superseded["player_uid"] != claim["player_uid"]:
                raise AvailabilityLedgerError(
                    "availability claims may only supersede the same player"
                )
        seen[claim_id] = claim
        previous_available = available


def _previous_unsuperseded_negative_claims(
    claims: list[Mapping[str, Any]],
    player_uid: str,
    *,
    at_time: str,
) -> list[str]:
    cutoff = _parse_timestamp(at_time, field="available_at")
    superseded = {
        str(value)
        for claim in claims
        for value in claim.get("supersedes_claim_ids", [])
    }
    return [
        str(claim["claim_id"])
        for claim in claims
        if claim["player_uid"] == player_uid
        and claim["status"] in {"unavailable", "doubtful"}
        and claim["claim_id"] not in superseded
        and _parse_timestamp(str(claim["expires_at"]), field="expires_at")
        > cutoff
    ]


def append_availability_claim(
    ledger: Mapping[str, Any], claim: Mapping[str, Any]
) -> dict[str, Any]:
    """Return a new ledger with one validated claim appended."""

    validate_availability_ledger(ledger)
    candidate = deepcopy(dict(claim))
    try:
        validate_availability_claim_semantics(candidate)
    except ValueError as exc:
        raise AvailabilityLedgerError(str(exc)) from exc
    claims = deepcopy(list(ledger["claims"]))
    claim_id = str(candidate["claim_id"])
    existing = next(
        (
            row
            for row in claims
            if str(row["claim_id"]) == claim_id
        ),
        None,
    )
    if existing is not None:
        if artifact_hash(existing) != artifact_hash(candidate):
            raise AvailabilityLedgerError(
                f"conflicting duplicate availability claim_id: {claim_id}"
            )
        return deepcopy(dict(ledger))

    if claims:
        latest = _parse_timestamp(
            str(claims[-1]["available_at"]), field="available_at"
        )
        incoming = _parse_timestamp(
            str(candidate["available_at"]), field="available_at"
        )
        if incoming < latest:
            raise AvailabilityLedgerError(
                "availability claims must be appended in available_at order"
            )
    references = set(candidate.get("supersedes_claim_ids", []))
    indexed = {str(existing["claim_id"]): existing for existing in claims}
    for superseded_id in references:
        prior = indexed.get(str(superseded_id))
        if prior is None:
            raise AvailabilityLedgerError(
                f"superseded claim does not precede claim: {superseded_id}"
            )
        if prior["player_uid"] != candidate["player_uid"]:
            raise AvailabilityLedgerError(
                "availability claims may only supersede the same player"
            )
    prior_negative = _previous_unsuperseded_negative_claims(
        claims,
        str(candidate["player_uid"]),
        at_time=str(candidate["available_at"]),
    )
    if candidate["status"] == "available" and prior_negative:
        if not set(prior_negative) <= references:
            raise AvailabilityLedgerError(
                "recovery must supersede every unresolved absence or doubt"
            )
        if "recovery" not in candidate:
            raise AvailabilityLedgerError(
                "recovery requires an explicit observed recovery condition"
            )
    claims.append(candidate)
    result = deepcopy(dict(ledger))
    result["claims"] = claims
    return _seal(result)


def project_availability(
    ledger: Mapping[str, Any],
    *,
    decision_at: str,
    player_uids: Iterable[str] = (),
) -> dict[str, Any]:
    """Project the append-only history into an auditable decision-time view."""

    validate_availability_ledger(ledger)
    _parse_timestamp(decision_at, field="decision_at")
    claims = deepcopy(list(ledger["claims"]))
    known = [claim for claim in claims if _known_by(claim, decision_at)]
    effective_superseders = [
        claim
        for claim in known
        if assess_claim_for_decision(
            claim, str(claim["available_at"])
        ).eligible
    ]
    superseded_ids = {
        str(value)
        for claim in effective_superseders
        for value in claim.get("supersedes_claim_ids", [])
    }
    active: list[dict[str, Any]] = []
    stale: list[dict[str, Any]] = []
    superseded: list[dict[str, Any]] = []
    future: list[dict[str, Any]] = []
    for claim in claims:
        claim_id = str(claim["claim_id"])
        if not _known_by(claim, decision_at):
            future.append(claim)
        elif claim_id in superseded_ids:
            superseded.append(claim)
        else:
            eligibility = assess_claim_for_decision(claim, decision_at)
            decorated = {
                **claim,
                "eligibility": {
                    "eligible": eligibility.eligible,
                    "reasons": list(eligibility.reasons),
                    "warnings": list(eligibility.warnings),
                },
            }
            if eligibility.eligible:
                active.append(decorated)
            else:
                stale.append(decorated)

    by_player: dict[str, list[dict[str, Any]]] = {}
    for claim in active:
        by_player.setdefault(str(claim["player_uid"]), []).append(claim)
    conflicts: list[dict[str, Any]] = []
    accepted: list[dict[str, Any]] = []
    for player_uid, player_claims in sorted(by_player.items()):
        statuses = sorted({str(claim["status"]) for claim in player_claims})
        if len(statuses) > 1:
            conflicts.append(
                {
                    "player_uid": player_uid,
                    "claim_ids": sorted(
                        str(claim["claim_id"]) for claim in player_claims
                    ),
                    "statuses": statuses,
                    "resolution": "abstain_pending_explicit_supersession",
                }
            )
        else:
            ordered = sorted(
                player_claims,
                key=lambda item: (
                    float(item["confidence"]),
                    str(item["available_at"]),
                    str(item["claim_id"]),
                ),
                reverse=True,
            )
            canonical = deepcopy(ordered[0])
            canonical["corroborating_claim_ids"] = sorted(
                str(item["claim_id"]) for item in ordered[1:]
            )
            accepted.append(canonical)
    conflicted_players = {
        str(conflict["player_uid"]) for conflict in conflicts
    }
    requested = sorted({str(value) for value in player_uids})
    abstentions = []
    for player_uid in requested:
        if player_uid in conflicted_players:
            reason = "unresolved_conflict"
        elif player_uid not in by_player:
            reason = "no_active_evidence"
        else:
            continue
        abstentions.append({"player_uid": player_uid, "reason": reason})
    return _seal(
        {
            "schema_version": "1.0",
            "ledger_id": ledger["ledger_id"],
            "ledger_sha256": ledger["content_sha256"],
            "decision_at": decision_at,
            "accepted": accepted,
            "conflicts": conflicts,
            "abstentions": abstentions,
            "history": {
                "stale": sorted(
                    stale, key=lambda item: str(item["claim_id"])
                ),
                "superseded": sorted(
                    superseded, key=lambda item: str(item["claim_id"])
                ),
                "future": sorted(
                    future, key=lambda item: str(item["claim_id"])
                ),
            },
        }
    )


def _availability_challenger_policy(
    policy: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate the additive, default-disabled availability challenger policy."""

    persistent = policy.get("persistent_availability")
    if not isinstance(persistent, Mapping):
        raise AvailabilityLedgerError("persistent availability policy is missing")
    required = {
        "schema_version",
        "challenger_id",
        "enabled",
        "scope",
        "require_registry_approved_source",
        "require_exact_identity",
        "require_source_hash",
        "effects",
    }
    missing = sorted(required - set(persistent))
    if missing:
        raise AvailabilityLedgerError(
            "persistent availability policy missing: " + ", ".join(missing)
        )
    if persistent["schema_version"] != "1.0":
        raise AvailabilityLedgerError("unsupported persistent availability policy")
    if persistent["challenger_id"] != "availability-persistence-v1":
        raise AvailabilityLedgerError("unknown persistent availability challenger")
    if not isinstance(persistent["enabled"], bool):
        raise AvailabilityLedgerError(
            "persistent availability enabled must be boolean"
        )
    if persistent["scope"] != "named_challenger_only":
        raise AvailabilityLedgerError(
            "persistent availability scope must be named challenger only"
        )
    effects = persistent["effects"]
    if not isinstance(effects, Mapping):
        raise AvailabilityLedgerError("persistent availability effects must be an object")
    unavailable = effects.get("unavailable")
    doubtful = effects.get("doubtful")
    available = effects.get("available")
    if (
        not isinstance(unavailable, Mapping)
        or unavailable.get("mode") != "zero_projection"
        or not isinstance(doubtful, Mapping)
        or doubtful.get("mode") != "bounded_reduction"
        or not isinstance(available, Mapping)
        or available.get("mode") != "restore_structured_baseline"
    ):
        raise AvailabilityLedgerError("persistent availability effects are invalid")
    maximum = doubtful.get("max_start_probability_delta")
    if (
        isinstance(maximum, bool)
        or not isinstance(maximum, (int, float))
        or not 0 <= float(maximum) <= 1
    ):
        raise AvailabilityLedgerError(
            "persistent availability doubtful cap must be between zero and one"
        )
    return deepcopy(dict(persistent))


def _approved_availability_sources(
    source_registry: Mapping[str, Any],
    evidence_config: Mapping[str, Any],
) -> set[str]:
    """Return sources admitted by both the registry and evidence config."""

    registry_rows = source_registry.get("sources")
    configured_rows = evidence_config.get("sources")
    if not isinstance(registry_rows, list) or not isinstance(configured_rows, list):
        raise AvailabilityLedgerError(
            "source registry and evidence config need sources"
        )
    registry: dict[str, Mapping[str, Any]] = {}
    for row in registry_rows:
        if not isinstance(row, Mapping) or not isinstance(
            row.get("source_id"), str
        ):
            raise AvailabilityLedgerError(
                "source registry contains an invalid source"
            )
        source_id = str(row["source_id"])
        if source_id in registry:
            raise AvailabilityLedgerError(
                "source registry contains duplicate source_id"
            )
        registry[source_id] = row
    admitted = {
        str(row["source_id"])
        for row in configured_rows
        if isinstance(row, Mapping)
        and row.get("admitted") is True
        and isinstance(row.get("source_id"), str)
    }
    approved: set[str] = set()
    for source_id in admitted:
        row = registry.get(source_id)
        if row is None:
            continue
        if row.get("licence_status") in {"unknown", "prohibited"}:
            continue
        if not isinstance(row.get("allowed_use"), str) or not row["allowed_use"]:
            continue
        approved.add(source_id)
    return approved


def _source_and_identity_failure(
    claim: Mapping[str, Any], *, approved_source_ids: set[str]
) -> str | None:
    provenance = claim.get("provenance")
    if not isinstance(provenance, Mapping):
        return "provenance_missing"
    source_ids = provenance.get("source_ids")
    if (
        not isinstance(source_ids, list)
        or not source_ids
        or any(not isinstance(value, str) or not value for value in source_ids)
    ):
        return "source_ids_invalid"
    if not set(source_ids) <= approved_source_ids:
        return "source_not_registry_approved"
    hashes = provenance.get("source_hashes")
    if not isinstance(hashes, Mapping) or set(hashes) != set(source_ids):
        return "source_hashes_missing_or_unbound"
    for source_id in source_ids:
        digest = hashes[source_id]
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            return "source_hash_invalid"
    if provenance.get("identity_resolution") != "exact":
        return "identity_not_exact"
    return None


def apply_persistent_availability_challenger(
    solver_input: Mapping[str, Any],
    *,
    ledger: Mapping[str, Any],
    decision_at: str,
    checkpoint_id: str,
    policy: Mapping[str, Any],
    source_registry: Mapping[str, Any],
    evidence_config: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Apply active availability state only to a named challenger copy.

    The baseline solver input is copied before any validation or adjustment. A
    disabled policy therefore returns the exact input bytes, while an enabled
    policy can only reduce the copied player projections.
    """

    if not isinstance(checkpoint_id, str) or not checkpoint_id:
        raise AvailabilityLedgerError("checkpoint_id must be a non-empty string")
    baseline = deepcopy(dict(solver_input))
    players = baseline.get("players")
    if not isinstance(players, list):
        raise AvailabilityLedgerError("solver input players must be a list")
    indexed: dict[str, dict[str, Any]] = {}
    for row in players:
        if not isinstance(row, dict) or not isinstance(row.get("player_id"), str):
            raise AvailabilityLedgerError(
                "solver input player identity is invalid"
            )
        player_id = str(row["player_id"])
        if player_id in indexed:
            raise AvailabilityLedgerError(
                "solver input contains duplicate player identity"
            )
        for field in (
            "expected_points",
            "expected_minutes",
            "start_probability",
        ):
            value = row.get(field)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise AvailabilityLedgerError(
                    f"solver input {field} is invalid"
                )
        indexed[player_id] = row

    persistent = _availability_challenger_policy(policy)
    baseline_hash = artifact_hash(baseline)
    view = project_availability(
        ledger, decision_at=decision_at, player_uids=sorted(indexed)
    )
    audit: dict[str, Any] = {
        "schema_version": "1.0",
        "challenger_id": persistent["challenger_id"],
        "enabled": persistent["enabled"],
        "decision_at": decision_at,
        "checkpoint_id": checkpoint_id,
        "policy_sha256": artifact_hash(policy),
        "ledger_sha256": ledger["content_sha256"],
        "availability_view_sha256": view["content_sha256"],
        "baseline_solver_input_sha256": baseline_hash,
        "applied": [],
        "restored": [],
        "quarantined": [],
        "abstentions": deepcopy(view["abstentions"]),
    }
    if not persistent["enabled"]:
        audit["status"] = "disabled"
        audit["output_solver_input_sha256"] = baseline_hash
        return baseline, _seal(audit)

    approved_source_ids = _approved_availability_sources(
        source_registry, evidence_config
    )
    for conflict in view["conflicts"]:
        audit["quarantined"].append(
            {
                "player_uid": conflict["player_uid"],
                "claim_ids": deepcopy(conflict["claim_ids"]),
                "reason": "unresolved_conflict",
            }
        )
    for claim in view["accepted"]:
        player_uid = str(claim["player_uid"])
        failure = _source_and_identity_failure(
            claim, approved_source_ids=approved_source_ids
        )
        if failure is not None:
            audit["quarantined"].append(
                {
                    "claim_id": str(claim["claim_id"]),
                    "player_uid": player_uid,
                    "reason": failure,
                }
            )
            continue
        player = indexed.get(player_uid)
        if player is None:
            audit["quarantined"].append(
                {
                    "claim_id": str(claim["claim_id"]),
                    "player_uid": player_uid,
                    "reason": "player_not_in_solver_input",
                }
            )
            continue
        before = {
            "status": player.get("status"),
            "start_probability": float(player["start_probability"]),
            "expected_minutes": float(player["expected_minutes"]),
            "expected_points": float(player["expected_points"]),
        }
        status = str(claim["status"])
        if status == "available":
            audit["restored"].append(
                {
                    "claim_id": str(claim["claim_id"]),
                    "player_uid": player_uid,
                    "source_hashes": deepcopy(
                        claim["provenance"]["source_hashes"]
                    ),
                    "baseline": before,
                    "reason": (
                        "available_or_recovery_uses_structured_baseline"
                    ),
                }
            )
            continue
        if status == "unavailable":
            player.update(
                {
                    "status": "i",
                    "start_probability": 0.0,
                    "expected_minutes": 0.0,
                    "expected_points": 0.0,
                }
            )
            effect = "zero_projection"
        elif status == "doubtful":
            cap = float(
                persistent["effects"]["doubtful"][
                    "max_start_probability_delta"
                ]
            )
            after_probability = max(0.0, before["start_probability"] - cap)
            ratio = (
                after_probability / before["start_probability"]
                if before["start_probability"]
                else 0.0
            )
            player.update(
                {
                    "status": "d",
                    "start_probability": round(after_probability, 4),
                    "expected_minutes": round(
                        before["expected_minutes"] * ratio, 1
                    ),
                    "expected_points": round(
                        before["expected_points"] * ratio, 2
                    ),
                }
            )
            effect = "bounded_reduction"
        else:
            audit["quarantined"].append(
                {
                    "claim_id": str(claim["claim_id"]),
                    "player_uid": player_uid,
                    "reason": "unsupported_availability_status",
                }
            )
            continue
        audit["applied"].append(
            {
                "claim_id": str(claim["claim_id"]),
                "player_uid": player_uid,
                "status": status,
                "effect": effect,
                "available_at": str(claim["available_at"]),
                "expires_at": str(claim["expires_at"]),
                "supersedes_claim_ids": sorted(
                    str(value)
                    for value in claim.get("supersedes_claim_ids", [])
                ),
                "source_hashes": deepcopy(claim["provenance"]["source_hashes"]),
                "before": before,
                "after": {
                    "status": player.get("status"),
                    "start_probability": float(player["start_probability"]),
                    "expected_minutes": float(player["expected_minutes"]),
                    "expected_points": float(player["expected_points"]),
                },
            }
        )
    audit["status"] = "applied" if audit["applied"] else "enabled_no_effect"
    audit["applied"].sort(
        key=lambda row: (row["player_uid"], row["claim_id"])
    )
    audit["restored"].sort(
        key=lambda row: (row["player_uid"], row["claim_id"])
    )
    audit["quarantined"].sort(
        key=lambda row: (
            str(row.get("player_uid", "")),
            str(row.get("claim_id", "")),
            str(row["reason"]),
        )
    )
    audit["output_solver_input_sha256"] = artifact_hash(baseline)
    return baseline, _seal(audit)


def synchronise_availability_from_live_evidence(
    ledger: Mapping[str, Any],
    *,
    live_evidence_ledger: Mapping[str, Any],
    decision_at: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Append admitted player-availability evidence from the live ledger.

    This is a one-way, additive bridge. The governed live-evidence ledger is
    authoritative for source rights, source hashes, identity bindings and
    lifecycle; this function only derives the compact longitudinal state used
    by the projection challenger.
    """

    from src.evidence.live_evidence_ledger import project_live_evidence

    validate_availability_ledger(ledger)
    view = project_live_evidence(live_evidence_ledger, decision_at=decision_at)
    if ledger["season"] != live_evidence_ledger.get("season"):
        raise AvailabilityLedgerError(
            "live evidence ledger season differs from availability ledger"
        )
    result = deepcopy(dict(ledger))
    audit: dict[str, Any] = {
        "schema_version": "1.0",
        "decision_at": decision_at,
        "live_ledger_sha256": live_evidence_ledger["content_sha256"],
        "live_view_sha256": view["content_sha256"],
        "availability_ledger_before_sha256": ledger["content_sha256"],
        "appended_claim_ids": [],
        "idempotent_claim_ids": [],
        "refused": [],
    }
    status_map = {
        "a": "available",
        "d": "doubtful",
        "i": "unavailable",
        "s": "unavailable",
        "u": "unavailable",
    }
    for live_claim in sorted(
        view["accepted"],
        key=lambda row: (str(row["available_at"]), str(row["claim_id"])),
    ):
        if live_claim.get("claim_type") != "player_availability":
            continue
        bindings = [
            row
            for row in live_claim["identity_bindings"]
            if row["entity_type"] == "player_uid"
            and row["match_status"] == "exact"
        ]
        if len(bindings) != 1:
            audit["refused"].append(
                {
                    "claim_id": str(live_claim["claim_id"]),
                    "reason": "player_identity_not_exactly_resolved",
                }
            )
            continue
        raw_status = str(live_claim.get("value", {}).get("status", ""))
        status = status_map.get(raw_status)
        if status is None:
            audit["refused"].append(
                {
                    "claim_id": str(live_claim["claim_id"]),
                    "player_uid": str(bindings[0]["stable_id"]),
                    "reason": "official_availability_status_unsupported",
                }
            )
            continue
        player_uid = str(bindings[0]["stable_id"])
        supersedes = set(
            str(value) for value in live_claim.get("supersedes_claim_ids", [])
        )
        if status == "available":
            supersedes.update(
                _previous_unsuperseded_negative_claims(
                    list(result["claims"]),
                    player_uid,
                    at_time=str(live_claim["available_at"]),
                )
            )
        candidate: dict[str, Any] = {
            "claim_id": str(live_claim["claim_id"]),
            "player_uid": player_uid,
            "status": status,
            "confidence": float(live_claim["confidence"]),
            "published_at": str(live_claim["published_at"]),
            "observed_at": str(live_claim["observed_at"]),
            "available_at": str(live_claim["available_at"]),
            "expires_at": str(live_claim["expires_at"]),
            "provenance": {
                "source_ids": [str(live_claim["source_id"])],
                "source_hashes": {
                    str(live_claim["source_id"]): str(
                        live_claim["source_hash_sha256"]
                    )
                },
                "identity_resolution": "exact",
                "transformation_version": "availability-live-bridge-v1",
            },
            "supersedes_claim_ids": sorted(supersedes),
        }
        if status == "available":
            candidate["recovery"] = {
                "condition": "declared_fit",
                "condition_met": True,
            }
        existing = next(
            (
                row
                for row in result["claims"]
                if str(row["claim_id"]) == candidate["claim_id"]
            ),
            None,
        )
        try:
            result = append_availability_claim(result, candidate)
        except AvailabilityLedgerError as exc:
            audit["refused"].append(
                {
                    "claim_id": candidate["claim_id"],
                    "player_uid": player_uid,
                    "reason": str(exc),
                }
            )
            continue
        if existing is None:
            audit["appended_claim_ids"].append(candidate["claim_id"])
        else:
            audit["idempotent_claim_ids"].append(candidate["claim_id"])
    audit["appended_claim_ids"].sort()
    audit["idempotent_claim_ids"].sort()
    audit["refused"].sort(
        key=lambda row: (str(row.get("player_uid", "")), row["claim_id"])
    )
    audit["availability_ledger_after_sha256"] = result["content_sha256"]
    audit["status"] = "complete" if not audit["refused"] else "degraded"
    return result, _seal(audit)
