"""Cutoff-safe inventory for retrospective GW1-GW11 evidence research."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from datetime import datetime
import hashlib
import json
from pathlib import Path
from typing import Any

from src.forecasting.live_faithful import artifact_hash


class EarlySeasonEvidenceManifestError(ValueError):
    """Raised when early-season evidence cannot be audited safely."""


MANIFEST_VERSION = "early-season-evidence-manifest-v1"
ADMISSION_STATUSES = {"admitted_exploratory", "excluded"}
COMPLETENESS_STATUSES = {"ready", "partial", "abstain"}


def _parse_timestamp(value: Any, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise EarlySeasonEvidenceManifestError(
            f"{field} must be an ISO timestamp"
        ) from exc
    if parsed.tzinfo is None:
        raise EarlySeasonEvidenceManifestError(
            f"{field} must include a timezone"
        )
    return parsed


def _non_empty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EarlySeasonEvidenceManifestError(
            f"{field} must be a non-empty string"
        )
    return value


def _string_list(value: Any, field: str, *, allow_empty: bool = True) -> list[str]:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        raise EarlySeasonEvidenceManifestError(
            f"{field} must be a list of non-empty strings"
        )
    if not allow_empty and not value:
        raise EarlySeasonEvidenceManifestError(f"{field} cannot be empty")
    if len(value) != len(set(value)):
        raise EarlySeasonEvidenceManifestError(f"{field} contains duplicates")
    return list(value)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _seal(value: Mapping[str, Any]) -> dict[str, Any]:
    result = deepcopy(dict(value))
    result["content_sha256"] = artifact_hash(result)
    return result


def _validate_candidate(
    candidate: Mapping[str, Any],
    *,
    gameweek: int,
    deadline: str,
    researched_at: str,
) -> dict[str, Any]:
    required = {
        "evidence_id",
        "source_registry_id",
        "source_id",
        "url",
        "title",
        "published_at",
        "published_at_precision",
        "observed_at",
        "available_at",
        "citation_excerpt",
        "citation_excerpt_sha256",
        "claim_summary",
        "player_ids",
        "boundary_ids",
        "rights_status",
        "admission_status",
        "exclusion_reasons",
    }
    missing = sorted(required - set(candidate))
    if missing:
        raise EarlySeasonEvidenceManifestError(
            f"GW{gameweek} evidence candidate missing fields: {missing}"
        )

    evidence_id = _non_empty_string(
        candidate["evidence_id"], f"GW{gameweek}.evidence_id"
    )
    for field in (
        "source_registry_id",
        "source_id",
        "url",
        "title",
        "published_at_precision",
        "claim_summary",
        "rights_status",
    ):
        _non_empty_string(candidate[field], f"{evidence_id}.{field}")
    if not str(candidate["url"]).startswith(("https://", "http://")):
        raise EarlySeasonEvidenceManifestError(
            f"{evidence_id}.url must be HTTP(S)"
        )

    cutoff = _parse_timestamp(deadline, "decision_cutoff")
    published = _parse_timestamp(
        candidate["published_at"], f"{evidence_id}.published_at"
    )
    observed = _parse_timestamp(
        candidate["observed_at"], f"{evidence_id}.observed_at"
    )
    available = _parse_timestamp(
        candidate["available_at"], f"{evidence_id}.available_at"
    )
    researched = _parse_timestamp(researched_at, "researched_at")
    if published > cutoff:
        raise EarlySeasonEvidenceManifestError(
            f"{evidence_id} was published after the GW{gameweek} cutoff"
        )
    if observed < published:
        raise EarlySeasonEvidenceManifestError(
            f"{evidence_id}.observed_at precedes published_at"
        )
    if available < observed:
        raise EarlySeasonEvidenceManifestError(
            f"{evidence_id}.available_at precedes observed_at"
        )
    if available > researched:
        raise EarlySeasonEvidenceManifestError(
            f"{evidence_id}.available_at is after researched_at"
        )

    excerpt = _non_empty_string(
        candidate["citation_excerpt"], f"{evidence_id}.citation_excerpt"
    )
    if candidate["citation_excerpt_sha256"] != _sha256_text(excerpt):
        raise EarlySeasonEvidenceManifestError(
            f"{evidence_id} citation excerpt hash mismatch"
        )
    player_ids = _string_list(
        candidate["player_ids"], f"{evidence_id}.player_ids"
    )
    boundary_ids = _string_list(
        candidate["boundary_ids"], f"{evidence_id}.boundary_ids", allow_empty=False
    )
    reasons = _string_list(
        candidate["exclusion_reasons"], f"{evidence_id}.exclusion_reasons"
    )
    admission = candidate["admission_status"]
    if admission not in ADMISSION_STATUSES:
        raise EarlySeasonEvidenceManifestError(
            f"{evidence_id}.admission_status is unsupported"
        )
    if admission == "excluded" and not reasons:
        raise EarlySeasonEvidenceManifestError(
            f"{evidence_id} is excluded without an exclusion reason"
        )
    if admission == "admitted_exploratory" and reasons:
        raise EarlySeasonEvidenceManifestError(
            f"{evidence_id} is admitted but has exclusion reasons"
        )

    # Retrospectively recovered evidence can be explored only. It must never be
    # represented as information actually observed by the historical agent.
    production_eligible = available <= cutoff
    if production_eligible:
        raise EarlySeasonEvidenceManifestError(
            f"{evidence_id} is unexpectedly point-in-time; use the live evidence contract"
        )

    return _seal(
        {
            **deepcopy(dict(candidate)),
            "player_ids": player_ids,
            "boundary_ids": boundary_ids,
            "exclusion_reasons": reasons,
            "published_before_cutoff": True,
            "observed_before_cutoff": False,
            "available_before_cutoff": False,
            "production_eligible": False,
            "historical_use": (
                "exploratory_replay"
                if admission == "admitted_exploratory"
                else "excluded_from_replay"
            ),
        }
    )


def build_manifest_entry(
    *,
    episode: Mapping[str, Any],
    research_record: Mapping[str, Any],
) -> dict[str, Any]:
    """Bind one operator research record to one sealed benchmark episode."""

    gameweek = int(episode.get("gameweek", 0))
    if not 1 <= gameweek <= 11:
        raise EarlySeasonEvidenceManifestError(
            "early-season entries support GW1 through GW11"
        )
    if research_record.get("schema_version") != "1.0":
        raise EarlySeasonEvidenceManifestError(
            f"GW{gameweek} research record schema must be 1.0"
        )
    if int(research_record.get("gameweek", 0)) != gameweek:
        raise EarlySeasonEvidenceManifestError(
            f"GW{gameweek} research record gameweek mismatch"
        )
    season = _non_empty_string(episode.get("season"), "episode.season")
    if research_record.get("season") != season:
        raise EarlySeasonEvidenceManifestError(
            f"GW{gameweek} research record season mismatch"
        )
    episode_id = _non_empty_string(
        episode.get("episode_id"), f"GW{gameweek}.episode_id"
    )
    deadline = _non_empty_string(
        episode.get("deadline"), f"GW{gameweek}.deadline"
    )
    _parse_timestamp(deadline, f"GW{gameweek}.deadline")
    observed_hash = _non_empty_string(
        episode.get("observed_episode_sha256"),
        f"GW{gameweek}.observed_episode_sha256",
    )
    researched_at = _non_empty_string(
        research_record.get("researched_at"), f"GW{gameweek}.researched_at"
    )
    _parse_timestamp(researched_at, f"GW{gameweek}.researched_at")
    search_scope = _string_list(
        research_record.get("search_scope"),
        f"GW{gameweek}.search_scope",
        allow_empty=False,
    )
    boundary_ids = _string_list(
        research_record.get("boundary_ids"),
        f"GW{gameweek}.boundary_ids",
        allow_empty=False,
    )
    candidates_raw = research_record.get("candidates")
    if not isinstance(candidates_raw, list):
        raise EarlySeasonEvidenceManifestError(
            f"GW{gameweek}.candidates must be a list"
        )
    candidates = [
        _validate_candidate(
            candidate,
            gameweek=gameweek,
            deadline=deadline,
            researched_at=researched_at,
        )
        for candidate in candidates_raw
    ]
    evidence_ids = [str(item["evidence_id"]) for item in candidates]
    if len(evidence_ids) != len(set(evidence_ids)):
        raise EarlySeasonEvidenceManifestError(
            f"GW{gameweek} contains duplicate evidence_id values"
        )
    identities = [
        (
            str(item["url"]),
            str(item["claim_summary"]),
            tuple(item["player_ids"]),
        )
        for item in candidates
    ]
    if len(identities) != len(set(identities)):
        raise EarlySeasonEvidenceManifestError(
            f"GW{gameweek} contains duplicate evidence claims"
        )
    unknown_boundaries = sorted(
        {
            boundary
            for item in candidates
            for boundary in item["boundary_ids"]
            if boundary not in boundary_ids
        }
    )
    if unknown_boundaries:
        raise EarlySeasonEvidenceManifestError(
            f"GW{gameweek} evidence references unknown boundaries: {unknown_boundaries}"
        )

    admitted = [
        item for item in candidates
        if item["admission_status"] == "admitted_exploratory"
    ]
    excluded = [
        item for item in candidates if item["admission_status"] == "excluded"
    ]
    requested_status = research_record.get("completeness_status")
    if requested_status not in COMPLETENESS_STATUSES:
        raise EarlySeasonEvidenceManifestError(
            f"GW{gameweek}.completeness_status is unsupported"
        )
    derived_status = (
        "abstain"
        if not admitted
        else "ready"
        if research_record.get("search_complete") is True
        else "partial"
    )
    if requested_status != derived_status:
        raise EarlySeasonEvidenceManifestError(
            f"GW{gameweek} completeness_status must be {derived_status}"
        )
    abstention_reason = research_record.get("abstention_reason")
    if derived_status == "abstain":
        _non_empty_string(
            abstention_reason, f"GW{gameweek}.abstention_reason"
        )
    elif abstention_reason is not None:
        raise EarlySeasonEvidenceManifestError(
            f"GW{gameweek} has evidence and cannot declare abstention"
        )

    decision_type = (
        "initial_squad_selection" if gameweek == 1 else "weekly_management"
    )
    declared_type = research_record.get("decision_type")
    if declared_type != decision_type:
        raise EarlySeasonEvidenceManifestError(
            f"GW{gameweek}.decision_type must be {decision_type}"
        )

    return _seal(
        {
            "schema_version": "1.0",
            "manifest_version": MANIFEST_VERSION,
            "season": season,
            "gameweek": gameweek,
            "decision_type": decision_type,
            "decision_cutoff": deadline,
            "episode_id": episode_id,
            "observed_episode_sha256": observed_hash,
            "ruleset_id": episode.get("ruleset_id"),
            "ruleset_sha256": episode.get("ruleset_sha256"),
            "researched_at": researched_at,
            "research_method": research_record.get("research_method"),
            "search_scope": search_scope,
            "search_complete": bool(research_record.get("search_complete")),
            "boundary_ids": boundary_ids,
            "case_selection": "retrospective_exploratory_not_preregistered",
            "production_eligible": False,
            "promotion_eligible": False,
            "completeness": {
                "status": derived_status,
                "candidate_count": len(candidates),
                "admitted_count": len(admitted),
                "excluded_count": len(excluded),
                "abstention_reason": abstention_reason,
            },
            "candidates": candidates,
            "limitations": sorted(
                {
                    "sources_recovered_after_historical_decision",
                    "retrospective_case_selection_can_overstate_evidence_value",
                    *research_record.get("limitations", []),
                }
            ),
        }
    )


def build_early_season_manifest(
    *,
    index: Mapping[str, Any],
    research_records: Mapping[int, Mapping[str, Any]],
) -> dict[str, Any]:
    """Build and seal the complete GW1-GW11 evidence inventory."""

    episodes_raw = index.get("episodes")
    if not isinstance(episodes_raw, list):
        raise EarlySeasonEvidenceManifestError("benchmark index has no episodes")
    episodes = {
        int(item["gameweek"]): item
        for item in episodes_raw
        if 1 <= int(item.get("gameweek", 0)) <= 11
    }
    expected = set(range(1, 12))
    if set(episodes) != expected:
        raise EarlySeasonEvidenceManifestError(
            "benchmark index must contain GW1 through GW11 exactly once"
        )
    if set(research_records) != expected:
        missing = sorted(expected - set(research_records))
        extra = sorted(set(research_records) - expected)
        raise EarlySeasonEvidenceManifestError(
            f"research records must cover GW1-GW11; missing={missing}, extra={extra}"
        )
    entries = [
        build_manifest_entry(
            episode=episodes[gameweek],
            research_record=research_records[gameweek],
        )
        for gameweek in range(1, 12)
    ]
    admitted = sum(
        int(entry["completeness"]["admitted_count"]) for entry in entries
    )
    excluded = sum(
        int(entry["completeness"]["excluded_count"]) for entry in entries
    )
    candidates = admitted + excluded
    abstained = sum(
        entry["completeness"]["status"] == "abstain" for entry in entries
    )
    manifest = _seal(
        {
            "schema_version": "1.0",
            "manifest_version": MANIFEST_VERSION,
            "manifest_id": f"{MANIFEST_VERSION}:{index.get('season')}:gw01-gw11",
            "season": index.get("season"),
            "benchmark_dataset_id": index.get("dataset_id"),
            "benchmark_dataset_hash": index.get("dataset_hash"),
            "case_selection": "retrospective_exploratory_not_preregistered",
            "production_eligible": False,
            "promotion_eligible": False,
            "entries": entries,
            "coverage": {
                "gameweek_count": len(entries),
                "candidate_count": candidates,
                "admitted_count": admitted,
                "excluded_count": excluded,
                "abstained_gameweek_count": abstained,
                "abstention_rate": abstained / len(entries),
                "admission_rate": admitted / candidates if candidates else 0.0,
                "search_complete_gameweek_count": sum(
                    bool(entry["search_complete"]) for entry in entries
                ),
            },
        }
    )
    validate_early_season_manifest(manifest, index=index)
    return manifest


def validate_early_season_manifest(
    manifest: Mapping[str, Any],
    *,
    index: Mapping[str, Any],
) -> None:
    """Rebuild the manifest from embedded records and verify every binding."""

    if manifest.get("content_sha256") != artifact_hash(manifest):
        raise EarlySeasonEvidenceManifestError("manifest content hash mismatch")
    if manifest.get("production_eligible") is not False:
        raise EarlySeasonEvidenceManifestError(
            "retrospective manifest cannot be production eligible"
        )
    if manifest.get("benchmark_dataset_hash") != index.get("dataset_hash"):
        raise EarlySeasonEvidenceManifestError("benchmark dataset hash mismatch")
    entries = manifest.get("entries")
    if not isinstance(entries, list) or [
        int(entry.get("gameweek", 0)) for entry in entries
    ] != list(range(1, 12)):
        raise EarlySeasonEvidenceManifestError(
            "manifest entries must be ordered GW1 through GW11"
        )
    episodes = {
        int(item["gameweek"]): item
        for item in index["episodes"]
        if 1 <= int(item.get("gameweek", 0)) <= 11
    }
    seen_ids: set[str] = set()
    for entry in entries:
        gameweek = int(entry["gameweek"])
        episode = episodes[gameweek]
        if entry.get("content_sha256") != artifact_hash(entry):
            raise EarlySeasonEvidenceManifestError(
                f"GW{gameweek} entry content hash mismatch"
            )
        if entry.get("decision_cutoff") != episode.get("deadline"):
            raise EarlySeasonEvidenceManifestError(
                f"GW{gameweek} decision cutoff mismatch"
            )
        if entry.get("episode_id") != episode.get("episode_id"):
            raise EarlySeasonEvidenceManifestError(
                f"GW{gameweek} episode identity mismatch"
            )
        if entry.get("observed_episode_sha256") != episode.get(
            "observed_episode_sha256"
        ):
            raise EarlySeasonEvidenceManifestError(
                f"GW{gameweek} observed episode hash mismatch"
            )
        expected_type = (
            "initial_squad_selection" if gameweek == 1 else "weekly_management"
        )
        if entry.get("decision_type") != expected_type:
            raise EarlySeasonEvidenceManifestError(
                f"GW{gameweek} decision type mismatch"
            )
        if entry.get("production_eligible") is not False:
            raise EarlySeasonEvidenceManifestError(
                f"GW{gameweek} cannot be production eligible"
            )
        for candidate in entry["candidates"]:
            if candidate.get("content_sha256") != artifact_hash(candidate):
                raise EarlySeasonEvidenceManifestError(
                    f"{candidate.get('evidence_id')} content hash mismatch"
                )
            evidence_id = str(candidate["evidence_id"])
            if evidence_id in seen_ids:
                raise EarlySeasonEvidenceManifestError(
                    f"duplicate cross-week evidence_id: {evidence_id}"
                )
            seen_ids.add(evidence_id)
            if candidate.get("production_eligible") is not False:
                raise EarlySeasonEvidenceManifestError(
                    f"{evidence_id} cannot be production eligible"
                )
    coverage = manifest.get("coverage", {})
    admitted = sum(
        int(entry["completeness"]["admitted_count"]) for entry in entries
    )
    excluded = sum(
        int(entry["completeness"]["excluded_count"]) for entry in entries
    )
    abstained = sum(
        entry["completeness"]["status"] == "abstain" for entry in entries
    )
    expected_coverage = {
        "gameweek_count": 11,
        "candidate_count": admitted + excluded,
        "admitted_count": admitted,
        "excluded_count": excluded,
        "abstained_gameweek_count": abstained,
        "abstention_rate": abstained / 11,
        "admission_rate": (
            admitted / (admitted + excluded) if admitted + excluded else 0.0
        ),
        "search_complete_gameweek_count": sum(
            bool(entry["search_complete"]) for entry in entries
        ),
    }
    if coverage != expected_coverage:
        raise EarlySeasonEvidenceManifestError("manifest coverage mismatch")


def write_immutable_json(path: Path, value: Mapping[str, Any]) -> None:
    """Write canonical formatted JSON once, refusing conflicting replacement."""

    encoded = json.dumps(
        value, indent=2, sort_keys=True, ensure_ascii=False
    ) + "\n"
    if path.exists():
        if path.read_text(encoding="utf-8") != encoded:
            raise EarlySeasonEvidenceManifestError(
                f"refusing to overwrite different sealed manifest: {path}"
            )
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(encoded, encoding="utf-8")

