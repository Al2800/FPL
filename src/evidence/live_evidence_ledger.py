"""Immutable, rights-aware unstructured evidence ledger for live decisions."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from src.evidence.lifecycle import scan_injection


class LiveEvidenceLedgerError(ValueError):
    """Raised when live evidence cannot be admitted or projected safely."""


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def live_evidence_hash(value: Mapping[str, Any]) -> str:
    projection = {
        key: item for key, item in value.items() if key != "content_sha256"
    }
    return hashlib.sha256(_canonical_bytes(projection)).hexdigest()


def _seal(value: Mapping[str, Any]) -> dict[str, Any]:
    result = deepcopy(dict(value))
    result["content_sha256"] = live_evidence_hash(result)
    return result


def _timestamp(value: Any, field: str) -> tuple[str, datetime]:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise LiveEvidenceLedgerError(
            f"{field} must be an ISO-8601 timestamp"
        ) from exc
    if parsed.tzinfo is None:
        raise LiveEvidenceLedgerError(f"{field} must include a timezone")
    utc = parsed.astimezone(timezone.utc)
    return utc.isoformat().replace("+00:00", "Z"), utc


def _sha256(value: Any, field: str) -> str:
    digest = str(value)
    if len(digest) != 64 or any(
        character not in "0123456789abcdef" for character in digest
    ):
        raise LiveEvidenceLedgerError(f"{field} must be a lower-case SHA-256")
    return digest


def _source_entry(
    source_registry: Mapping[str, Any], source_id: str
) -> dict[str, Any]:
    source = next(
        (
            deepcopy(dict(row))
            for row in source_registry.get("sources", [])
            if row.get("source_id") == source_id
        ),
        None,
    )
    if source is None:
        raise LiveEvidenceLedgerError(
            f"Evidence source is not registered: {source_id}"
        )
    return source


def _source_policy(config: Mapping[str, Any], source_id: str) -> dict[str, Any]:
    source = next(
        (
            deepcopy(dict(row))
            for row in config.get("sources", [])
            if row.get("source_id") == source_id
        ),
        None,
    )
    if source is None or not source.get("admitted"):
        raise LiveEvidenceLedgerError(
            f"Evidence source is not admitted by live policy: {source_id}"
        )
    return source


def _rights_snapshot(
    registry: Mapping[str, Any],
    configured: Mapping[str, Any],
    *,
    claim_precision: str,
) -> dict[str, Any]:
    licence = str(registry.get("licence_status", "unknown"))
    allowed_use = str(registry.get("allowed_use", ""))
    if licence == "prohibited" or allowed_use in {"", "unresolved"}:
        raise LiveEvidenceLedgerError("Evidence source rights prohibit admission")
    mode = str(configured.get("admission_mode"))
    if mode == "automated_snapshot":
        if not registry.get("enabled"):
            raise LiveEvidenceLedgerError(
                "Automated evidence admission requires an enabled source"
            )
        if licence == "unknown":
            raise LiveEvidenceLedgerError(
                "Automated evidence admission requires resolved licence status"
            )
        method = str(registry.get("collection_method", ""))
        if method in {"", "manual", "manual_citation"}:
            raise LiveEvidenceLedgerError(
                "Automated evidence admission requires an automated "
                "collection method"
            )
        precision = "registry_enabled_resolved"
    elif mode == "manual_citation":
        if claim_precision == "verbatim_excerpt" and licence == "unknown":
            raise LiveEvidenceLedgerError(
                "Unknown-rights manual evidence must be a derived claim, not a verbatim excerpt"
            )
        precision = (
            "manual_citation_rights_pending"
            if licence == "unknown"
            else "manual_citation_registered_rights"
        )
    else:
        raise LiveEvidenceLedgerError(f"Unsupported admission mode: {mode}")
    return {
        "authority": str(registry.get("authority", "unknown")),
        "licence_status": licence,
        "allowed_use": allowed_use,
        "retention_policy": str(registry.get("retention_policy", "")),
        "collection_method": str(registry.get("collection_method", "")),
        "registry_enabled": bool(registry.get("enabled", False)),
        "admission_mode": mode,
        "rights_precision": precision,
        "raw_content_retained": bool(configured.get("raw_content_retained", False)),
        "attribution": str(registry.get("attribution", "")),
    }


def new_live_evidence_ledger(*, season: str, created_at: str) -> dict[str, Any]:
    if not isinstance(season, str) or not season:
        raise LiveEvidenceLedgerError("season must be a non-empty string")
    created_text, _ = _timestamp(created_at, "created_at")
    return _seal(
        {
            "schema_version": "1.0",
            "ledger_id": f"live-evidence:{season}",
            "season": season,
            "created_at": created_text,
            "claims": [],
        }
    )


def _identity_bindings(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list) or not value:
        raise LiveEvidenceLedgerError(
            "identity_bindings must contain at least one stable binding"
        )
    result: list[dict[str, str]] = []
    for index, source in enumerate(value):
        if not isinstance(source, Mapping):
            raise LiveEvidenceLedgerError(
                f"identity_bindings[{index}] must be an object"
            )
        row = {
            "entity_type": str(source.get("entity_type", "")),
            "stable_id": str(source.get("stable_id", "")),
            "source_label": str(source.get("source_label", "")),
            "match_status": str(source.get("match_status", "")),
        }
        if not all(row.values()):
            raise LiveEvidenceLedgerError(
                f"identity_bindings[{index}] has empty fields"
            )
        if row["match_status"] not in {"exact", "manual_verified"}:
            raise LiveEvidenceLedgerError(
                "identity binding must be exact or manual_verified"
            )
        result.append(row)
    stable_keys = [(row["entity_type"], row["stable_id"]) for row in result]
    if len(stable_keys) != len(set(stable_keys)):
        raise LiveEvidenceLedgerError("identity bindings must be unique")
    return sorted(result, key=lambda row: (row["entity_type"], row["stable_id"]))


def _normalise_claim(
    claim: Mapping[str, Any],
    *,
    source_registry: Mapping[str, Any],
    config: Mapping[str, Any],
) -> dict[str, Any]:
    value = deepcopy(dict(claim))
    required = {
        "claim_id",
        "source_id",
        "document_id",
        "source_url",
        "source_hash_sha256",
        "claim_text",
        "claim_precision",
        "claim_type",
        "value",
        "confidence",
        "published_at",
        "observed_at",
        "available_at",
        "expires_at",
        "identity_bindings",
        "decision_boundary_ids",
    }
    missing = sorted(required - set(value))
    if missing:
        raise LiveEvidenceLedgerError(
            "Evidence claim missing fields: " + ", ".join(missing)
        )
    for field in (
        "claim_id",
        "source_id",
        "document_id",
        "source_url",
        "claim_text",
        "claim_precision",
        "claim_type",
    ):
        if not isinstance(value[field], str) or not value[field].strip():
            raise LiveEvidenceLedgerError(f"{field} must be a non-empty string")
    confidence = value["confidence"]
    if (
        isinstance(confidence, bool)
        or not isinstance(confidence, (int, float))
        or not 0.0 <= float(confidence) <= 1.0
    ):
        raise LiveEvidenceLedgerError("confidence must be in [0, 1]")
    minimum = float(config["thresholds"]["minimum_claim_confidence"])
    if float(confidence) < minimum:
        raise LiveEvidenceLedgerError(
            f"confidence is below live minimum {minimum}"
        )
    published_text, published = _timestamp(value["published_at"], "published_at")
    observed_text, observed = _timestamp(value["observed_at"], "observed_at")
    available_text, available = _timestamp(value["available_at"], "available_at")
    expires_text, expires = _timestamp(value["expires_at"], "expires_at")
    if not published <= observed <= available < expires:
        raise LiveEvidenceLedgerError(
            "Evidence timestamps must satisfy published <= observed <= available < expires"
        )
    boundaries = value["decision_boundary_ids"]
    if not isinstance(boundaries, list) or any(
        not isinstance(item, str) or not item for item in boundaries
    ):
        raise LiveEvidenceLedgerError(
            "decision_boundary_ids must be a string list"
        )
    source_id = str(value["source_id"])
    registry = _source_entry(source_registry, source_id)
    configured = _source_policy(config, source_id)
    rights = _rights_snapshot(
        registry, configured, claim_precision=str(value["claim_precision"])
    )
    if rights["admission_mode"] == "manual_citation" and value.get("raw_content"):
        raise LiveEvidenceLedgerError(
            "Manual citation evidence must not retain raw source content"
        )
    injection = scan_injection(str(value["claim_text"]))
    result = {
        "claim_id": str(value["claim_id"]),
        "source_id": source_id,
        "document_id": str(value["document_id"]),
        "source_url": str(value["source_url"]),
        "source_hash_sha256": _sha256(
            value["source_hash_sha256"], "source_hash_sha256"
        ),
        "claim_text": str(value["claim_text"]),
        "claim_precision": str(value["claim_precision"]),
        "claim_type": str(value["claim_type"]),
        "value": deepcopy(value["value"]),
        "confidence": float(confidence),
        "published_at": published_text,
        "observed_at": observed_text,
        "available_at": available_text,
        "expires_at": expires_text,
        "identity_bindings": _identity_bindings(value["identity_bindings"]),
        "decision_boundary_ids": sorted(set(str(item) for item in boundaries)),
        "estimated_impact_points": float(value.get("estimated_impact_points", 0.0)),
        "supersedes_claim_ids": sorted(
            set(str(item) for item in value.get("supersedes_claim_ids", []))
        ),
        "source_rights": rights,
        "quarantine": {
            "quarantined": injection.quarantined,
            "reason": injection.reason,
            "matched_patterns": list(injection.matched_patterns),
        },
    }
    if result["estimated_impact_points"] < 0:
        raise LiveEvidenceLedgerError(
            "estimated_impact_points must be non-negative"
        )
    return result


def validate_live_evidence_ledger(ledger: Mapping[str, Any]) -> None:
    if ledger.get("schema_version") != "1.0":
        raise LiveEvidenceLedgerError("Unsupported live evidence schema")
    season = str(ledger.get("season", ""))
    if not season or ledger.get("ledger_id") != f"live-evidence:{season}":
        raise LiveEvidenceLedgerError("Live evidence ledger identity mismatch")
    _timestamp(ledger.get("created_at"), "created_at")
    if ledger.get("content_sha256") != live_evidence_hash(ledger):
        raise LiveEvidenceLedgerError("Live evidence ledger content hash mismatch")
    claims = ledger.get("claims")
    if not isinstance(claims, list):
        raise LiveEvidenceLedgerError("Live evidence claims must be a list")
    seen: dict[str, Mapping[str, Any]] = {}
    previous: datetime | None = None
    for claim in claims:
        if not isinstance(claim, Mapping):
            raise LiveEvidenceLedgerError("Live evidence claims must be objects")
        claim_id = str(claim.get("claim_id", ""))
        if not claim_id or claim_id in seen:
            raise LiveEvidenceLedgerError(
                f"Duplicate or empty evidence claim_id: {claim_id}"
            )
        _sha256(claim.get("source_hash_sha256"), "source_hash_sha256")
        _identity_bindings(claim.get("identity_bindings"))
        _, published = _timestamp(
            claim.get("published_at"), "published_at"
        )
        _, observed = _timestamp(
            claim.get("observed_at"), "observed_at"
        )
        _, available = _timestamp(
            claim.get("available_at"), "available_at"
        )
        _, expires = _timestamp(claim.get("expires_at"), "expires_at")
        if not published <= observed <= available < expires:
            raise LiveEvidenceLedgerError(
                "Evidence timestamps must satisfy published <= observed <= available < expires"
            )
        supersedes = claim.get("supersedes_claim_ids", [])
        if not isinstance(supersedes, list) or any(
            not isinstance(value, str) or not value for value in supersedes
        ) or len(supersedes) != len(set(supersedes)):
            raise LiveEvidenceLedgerError(
                "supersedes_claim_ids must contain unique non-empty strings"
            )
        if previous is not None and available < previous:
            raise LiveEvidenceLedgerError(
                "Evidence claims must be appended in available_at order"
            )
        for superseded_id in claim.get("supersedes_claim_ids", []):
            prior = seen.get(str(superseded_id))
            if prior is None:
                raise LiveEvidenceLedgerError(
                    f"Superseded claim does not precede claim: {superseded_id}"
                )
            prior_key = (
                prior["claim_type"],
                sorted(
                    (row["entity_type"], row["stable_id"])
                    for row in prior["identity_bindings"]
                ),
            )
            current_key = (
                claim["claim_type"],
                sorted(
                    (row["entity_type"], row["stable_id"])
                    for row in claim["identity_bindings"]
                ),
            )
            _, prior_available = _timestamp(
                prior["available_at"], "available_at"
            )
            if prior_available >= available:
                raise LiveEvidenceLedgerError(
                    "A claim may supersede only an earlier claim"
                )
            if prior_key != current_key:
                raise LiveEvidenceLedgerError(
                    "A claim may supersede only the same subject and claim type"
                )
        seen[claim_id] = claim
        previous = available


def append_live_evidence_claim(
    ledger: Mapping[str, Any],
    claim: Mapping[str, Any],
    *,
    source_registry: Mapping[str, Any],
    config: Mapping[str, Any],
) -> dict[str, Any]:
    """Append one governed claim without mutating prior history."""

    validate_live_evidence_ledger(ledger)
    candidate = _normalise_claim(
        claim, source_registry=source_registry, config=config
    )
    claims = deepcopy(list(ledger["claims"]))
    if any(row["claim_id"] == candidate["claim_id"] for row in claims):
        raise LiveEvidenceLedgerError(
            f"Duplicate evidence claim_id: {candidate['claim_id']}"
        )
    if claims:
        _, latest = _timestamp(claims[-1]["available_at"], "available_at")
        _, incoming = _timestamp(candidate["available_at"], "available_at")
        if incoming < latest:
            raise LiveEvidenceLedgerError(
                "Evidence claims must be appended in available_at order"
            )
    indexed = {str(row["claim_id"]): row for row in claims}
    for superseded_id in candidate["supersedes_claim_ids"]:
        prior = indexed.get(superseded_id)
        if prior is None:
            raise LiveEvidenceLedgerError(
                f"Superseded claim does not precede claim: {superseded_id}"
            )
        prior_subject = (
            prior["claim_type"],
            [(row["entity_type"], row["stable_id"]) for row in prior["identity_bindings"]],
        )
        candidate_subject = (
            candidate["claim_type"],
            [(row["entity_type"], row["stable_id"]) for row in candidate["identity_bindings"]],
        )
        _, prior_available = _timestamp(prior["available_at"], "available_at")
        _, candidate_available = _timestamp(
            candidate["available_at"], "available_at"
        )
        if prior_available >= candidate_available:
            raise LiveEvidenceLedgerError(
                "A claim may supersede only an earlier claim"
            )
        if prior_subject != candidate_subject:
            raise LiveEvidenceLedgerError(
                "A claim may supersede only the same subject and claim type"
            )
    claims.append(candidate)
    result = deepcopy(dict(ledger))
    result["claims"] = claims
    return _seal(result)


def _subject_key(claim: Mapping[str, Any]) -> str:
    identities = ",".join(
        f"{row['entity_type']}:{row['stable_id']}"
        for row in claim["identity_bindings"]
    )
    return f"{claim['claim_type']}|{identities}"


def project_live_evidence(
    ledger: Mapping[str, Any], *, decision_at: str
) -> dict[str, Any]:
    """Create an immutable decision-time view with explicit exclusions."""

    validate_live_evidence_ledger(ledger)
    decision_text, cutoff = _timestamp(decision_at, "decision_at")
    claims = deepcopy(list(ledger["claims"]))
    known = []
    future = []
    for claim in claims:
        times = [
            _timestamp(claim[field], field)[1]
            for field in ("published_at", "observed_at", "available_at")
        ]
        (known if all(item <= cutoff for item in times) else future).append(claim)
    effective_superseders = [
        claim
        for claim in known
        if not claim["quarantine"]["quarantined"]
        and _timestamp(claim["expires_at"], "expires_at")[1] > cutoff
    ]
    superseded_ids = {
        str(superseded_id)
        for claim in effective_superseders
        for superseded_id in claim.get("supersedes_claim_ids", [])
    }
    superseded = [
        claim for claim in known if claim["claim_id"] in superseded_ids
    ]
    current = [
        claim for claim in known if claim["claim_id"] not in superseded_ids
    ]
    expired = [
        claim
        for claim in current
        if _timestamp(claim["expires_at"], "expires_at")[1] <= cutoff
    ]
    quarantined = [
        claim for claim in current if claim["quarantine"]["quarantined"]
    ]
    eligible = [
        claim
        for claim in current
        if claim not in expired and claim not in quarantined
    ]
    groups: dict[str, list[dict[str, Any]]] = {}
    for claim in eligible:
        groups.setdefault(_subject_key(claim), []).append(claim)
    accepted: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    for subject_key, group in sorted(groups.items()):
        values = {
            hashlib.sha256(_canonical_bytes(row["value"])).hexdigest()
            for row in group
        }
        if len(values) > 1:
            conflicts.append(
                {
                    "subject_key": subject_key,
                    "claim_ids": sorted(row["claim_id"] for row in group),
                    "resolution": "exclude_pending_explicit_supersession",
                }
            )
            continue
        ranked = sorted(
            group,
            key=lambda row: (
                -float(row["confidence"]),
                str(row["available_at"]),
                str(row["claim_id"]),
            ),
        )
        canonical = deepcopy(ranked[0])
        canonical["corroborating_claim_ids"] = sorted(
            row["claim_id"] for row in ranked[1:]
        )
        accepted.append(canonical)
    return _seal(
        {
            "schema_version": "1.0",
            "ledger_id": ledger["ledger_id"],
            "ledger_sha256": ledger["content_sha256"],
            "decision_at": decision_text,
            "accepted": sorted(
                accepted, key=lambda row: str(row["claim_id"])
            ),
            "conflicts": conflicts,
            "excluded": {
                "future": sorted(future, key=lambda row: str(row["claim_id"])),
                "expired": sorted(expired, key=lambda row: str(row["claim_id"])),
                "superseded": sorted(
                    superseded, key=lambda row: str(row["claim_id"])
                ),
                "quarantined": sorted(
                    quarantined, key=lambda row: str(row["claim_id"])
                ),
            },
        }
    )


def build_live_evidence_packet(
    *,
    evidence_view: Mapping[str, Any],
    engine_output_sha256: str,
    boundaries: Sequence[Mapping[str, Any]],
    config: Mapping[str, Any],
) -> dict[str, Any]:
    """Rank relevant active claims and enforce deterministic packet budgets."""

    if evidence_view.get("content_sha256") != live_evidence_hash(evidence_view):
        raise LiveEvidenceLedgerError("Evidence view content hash mismatch")
    engine_hash = _sha256(engine_output_sha256, "engine_output_sha256")
    boundary_map: dict[str, dict[str, Any]] = {}
    for source in boundaries:
        row = deepcopy(dict(source))
        boundary_id = str(row.get("boundary_id", ""))
        if not boundary_id or boundary_id in boundary_map:
            raise LiveEvidenceLedgerError(
                "Decision boundaries require unique non-empty IDs"
            )
        margin = row.get("margin_points")
        if (
            isinstance(margin, bool)
            or not isinstance(margin, (int, float))
            or float(margin) < 0
        ):
            raise LiveEvidenceLedgerError(
                "Decision boundary margin_points must be non-negative"
            )
        row["boundary_id"] = boundary_id
        row["margin_points"] = float(margin)
        boundary_map[boundary_id] = row
    ranked: list[dict[str, Any]] = []
    irrelevant: list[str] = []
    for claim in evidence_view["accepted"]:
        matches = [
            boundary_map[boundary_id]
            for boundary_id in claim["decision_boundary_ids"]
            if boundary_id in boundary_map
        ]
        if not matches:
            irrelevant.append(str(claim["claim_id"]))
            continue
        best_margin = min(float(row["margin_points"]) for row in matches)
        impact = float(claim["estimated_impact_points"]) * float(
            claim["confidence"]
        )
        ranked.append(
            {
                "claim": deepcopy(claim),
                "matched_boundary_ids": sorted(
                    str(row["boundary_id"]) for row in matches
                ),
                "best_margin_points": best_margin,
                "confidence_weighted_impact_points": round(impact, 6),
                "can_flip": impact >= best_margin,
            }
        )
    ranked.sort(
        key=lambda row: (
            not row["can_flip"],
            row["best_margin_points"],
            -row["confidence_weighted_impact_points"],
            -float(row["claim"]["confidence"]),
            str(row["claim"]["claim_id"]),
        )
    )
    maximum_claims = int(config["packet_limits"]["maximum_claims"])
    maximum_characters = int(config["packet_limits"]["maximum_claim_characters"])
    selected: list[dict[str, Any]] = []
    omitted_budget: list[str] = []
    characters = 0
    for row in ranked:
        text_length = len(str(row["claim"]["claim_text"]))
        if len(selected) >= maximum_claims or characters + text_length > maximum_characters:
            omitted_budget.append(str(row["claim"]["claim_id"]))
            continue
        selected.append(row)
        characters += text_length
    status = "complete" if selected else "degraded"
    return _seal(
        {
            "schema_version": "1.0",
            "packet_id": (
                f"live-evidence-packet:{evidence_view['ledger_id']}:"
                f"{evidence_view['decision_at']}"
            ),
            "status": status,
            "degraded_reasons": (
                [] if selected else ["no_boundary_relevant_active_evidence"]
            ),
            "decision_at": evidence_view["decision_at"],
            "engine_output_sha256": engine_hash,
            "evidence_view_sha256": evidence_view["content_sha256"],
            "boundaries": [boundary_map[key] for key in sorted(boundary_map)],
            "evidence": selected,
            "conflicts": deepcopy(evidence_view["conflicts"]),
            "exclusion_counts": {
                key: len(value)
                for key, value in evidence_view["excluded"].items()
            },
            "omitted": {
                "irrelevant_claim_ids": sorted(irrelevant),
                "packet_budget_claim_ids": sorted(omitted_budget),
            },
            "limits": {
                "maximum_claims": maximum_claims,
                "maximum_claim_characters": maximum_characters,
                "selected_claims": len(selected),
                "selected_claim_characters": characters,
            },
        }
    )


def write_live_evidence_artifact(
    path: Path, value: Mapping[str, Any]
) -> None:
    encoded = (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")
    if path.exists():
        if path.read_bytes() != encoded:
            raise LiveEvidenceLedgerError(
                f"Refusing to overwrite live evidence artifact: {path}"
            )
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encoded)
