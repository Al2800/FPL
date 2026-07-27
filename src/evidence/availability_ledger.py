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
    if any(existing["claim_id"] == claim_id for existing in claims):
        raise AvailabilityLedgerError(
            f"duplicate availability claim_id: {claim_id}"
        )
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
