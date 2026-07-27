"""Build immutable, deadline-bounded inputs for the enhanced historical replay."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping


FAMILIES = (
    "official_fpl_state",
    "promoted_transfer_context",
    "team_strength",
    "player_ratings",
    "set_piece_roles",
    "odds",
    "unstructured_evidence",
)
STATUSES = frozenset(
    {"strict_available", "degraded", "exploratory_only", "unavailable"}
)
COMPLETION_BUFFER_HOURS = 6


class EnhancedReplayInputError(ValueError):
    """Raised when an enhanced replay input would be ambiguous or unsafe."""


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def stable_hash(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def artifact_hash(value: Mapping[str, Any]) -> str:
    return stable_hash(
        {
            key: deepcopy(item)
            for key, item in value.items()
            if key != "content_sha256"
        }
    )


def _timestamp(value: Any, field: str) -> tuple[str, datetime]:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise EnhancedReplayInputError(
            f"{field} must be an ISO-8601 timestamp"
        ) from exc
    if parsed.tzinfo is None:
        raise EnhancedReplayInputError(f"{field} must include a timezone")
    utc = parsed.astimezone(timezone.utc)
    return utc.isoformat().replace("+00:00", "Z"), utc


def _sha256(value: Any, field: str) -> str:
    text = str(value)
    if len(text) != 64 or any(
        character not in "0123456789abcdef" for character in text
    ):
        raise EnhancedReplayInputError(f"{field} must be a lowercase SHA-256")
    return text


def _source_by_role(
    dataset_manifest: Mapping[str, Any], role: str
) -> Mapping[str, Any]:
    matches = [
        source
        for source in dataset_manifest.get("sources", [])
        if source.get("dataset_role") == role
    ]
    if len(matches) != 1:
        raise EnhancedReplayInputError(
            f"dataset manifest requires exactly one {role} source"
        )
    return matches[0]


def _manifest_artifact(
    manifest: Mapping[str, Any], role: str
) -> Mapping[str, Any]:
    marker = f"historical:{role}:"
    matches = [
        artifact
        for artifact in manifest.get("observed", {}).get("source_artifacts", [])
        if marker in str(artifact.get("artifact_id", ""))
    ]
    if len(matches) != 1:
        raise EnhancedReplayInputError(
            f"episode manifest requires exactly one {role} artifact"
        )
    return matches[0]


def _completion_bound(rows: Iterable[Mapping[str, Any]]) -> str | None:
    parsed = [
        _timestamp(row.get("kickoff_time"), "kickoff_time")[1]
        for row in rows
    ]
    if not parsed:
        return None
    bound = max(parsed) + timedelta(hours=COMPLETION_BUFFER_HOURS)
    return bound.isoformat().replace("+00:00", "Z")


def _observation(
    *,
    observation_id: str,
    source_id: str,
    source_ref: str,
    content_sha256: str,
    observed_at: str,
    available_at: str,
    decision_cutoff: str,
    strict_replay_admissible: bool,
    availability_basis: str,
    published_at: str | None = None,
    effective_at: str | None = None,
    finalised_at: str | None = None,
    upstream_source_sha256: str | None = None,
    limitations: Iterable[str] = (),
) -> dict[str, Any]:
    observed_text, _ = _timestamp(observed_at, "observed_at")
    available_text, available = _timestamp(available_at, "available_at")
    cutoff_text, cutoff = _timestamp(decision_cutoff, "decision_cutoff")
    published_text = (
        _timestamp(published_at, "published_at")[0]
        if published_at is not None
        else None
    )
    effective_text = (
        _timestamp(effective_at, "effective_at")[0]
        if effective_at is not None
        else None
    )
    finalised_text = (
        _timestamp(finalised_at, "finalised_at")[0]
        if finalised_at is not None
        else None
    )
    if strict_replay_admissible and available >= cutoff:
        raise EnhancedReplayInputError(
            f"strict observation {observation_id} is not pre-cutoff"
        )
    result = {
        "observation_id": str(observation_id),
        "source_id": str(source_id),
        "source_ref": str(source_ref).replace("\\", "/"),
        "content_sha256": _sha256(content_sha256, "content_sha256"),
        "upstream_source_sha256": (
            _sha256(upstream_source_sha256, "upstream_source_sha256")
            if upstream_source_sha256 is not None
            else None
        ),
        "published_at": published_text,
        "effective_at": effective_text,
        "finalised_at": finalised_text,
        "observed_at": observed_text,
        "available_at": available_text,
        "decision_cutoff": cutoff_text,
        "strict_replay_admissible": bool(strict_replay_admissible),
        "availability_basis": str(availability_basis),
        "limitations": sorted(set(str(item) for item in limitations)),
    }
    return result


def _family(
    family: str,
    *,
    status: str,
    observations: Iterable[Mapping[str, Any]] = (),
    gaps: Iterable[str] = (),
    fallback: str,
) -> dict[str, Any]:
    if family not in FAMILIES:
        raise EnhancedReplayInputError(f"unknown feature family: {family}")
    if status not in STATUSES:
        raise EnhancedReplayInputError(f"unknown family status: {status}")
    observation_rows = [deepcopy(dict(row)) for row in observations]
    strict_count = sum(
        row.get("strict_replay_admissible") is True for row in observation_rows
    )
    if status == "strict_available" and not strict_count:
        raise EnhancedReplayInputError(
            f"{family} cannot be strict_available without a strict observation"
        )
    if status == "unavailable" and observation_rows:
        raise EnhancedReplayInputError(
            f"{family} cannot be unavailable with observations"
        )
    return {
        "family": family,
        "status": status,
        "strict_replay_admissible": strict_count > 0,
        "exploratory_replay_admissible": bool(observation_rows),
        "observation_count": len(observation_rows),
        "strict_observation_count": strict_count,
        "observations": observation_rows,
        "gaps": sorted(set(str(item) for item in gaps)),
        "fallback": str(fallback),
    }


def _validate_canonical(
    manifest: Mapping[str, Any],
    observed: Mapping[str, Any],
    identity_map: Mapping[str, Any],
) -> tuple[int, str, str, str]:
    if manifest.get("mode") != "historical_structured":
        raise EnhancedReplayInputError("canonical episode mode is not historical")
    season = str(manifest.get("season", ""))
    gameweek = int(manifest.get("gameweek", 0))
    episode_id = str(manifest.get("episode_id", ""))
    if season != "2025-26" or not 1 <= gameweek <= 38 or not episode_id:
        raise EnhancedReplayInputError("canonical episode identity is invalid")
    for field in ("episode_id", "season", "gameweek", "cutoff", "deadline"):
        if observed.get(field) != manifest.get(field):
            raise EnhancedReplayInputError(
                f"observed {field} differs from canonical manifest"
            )
    observed_sha = stable_hash(observed)
    expected_observed = (
        manifest.get("observed", {})
        .get("feature_snapshot_ref", {})
        .get("content_sha256")
    )
    if observed_sha != expected_observed:
        raise EnhancedReplayInputError(
            "canonical observed partition content hash mismatch"
        )
    identity_sha = stable_hash(identity_map)
    if (
        observed.get("identity_map_ref", {}).get("content_sha256")
        != identity_sha
    ):
        raise EnhancedReplayInputError("canonical identity-map hash mismatch")
    forbidden = {"player_outcomes", "hidden_outcome", "hidden_outcome_ref"}
    if forbidden & set(observed):
        raise EnhancedReplayInputError(
            "observed partition contains hidden-outcome fields"
        )
    cutoff = _timestamp(manifest.get("cutoff"), "cutoff")[0]
    return gameweek, episode_id, cutoff, observed_sha


def _validate_dataset(
    dataset_manifest: Mapping[str, Any],
    observed: Mapping[str, Any],
) -> None:
    if dataset_manifest.get("status") != "frozen":
        raise EnhancedReplayInputError("dataset manifest is not frozen")
    if dataset_manifest.get("season") != "2025-26":
        raise EnhancedReplayInputError("dataset manifest season mismatch")
    if observed.get("dataset_id") != dataset_manifest.get("dataset_id"):
        raise EnhancedReplayInputError("observed dataset_id mismatch")
    if observed.get("dataset_hash") != dataset_manifest.get("dataset_hash"):
        raise EnhancedReplayInputError("observed dataset_hash mismatch")


def _strict_history_observation(
    *,
    family: str,
    role: str,
    rows: list[Mapping[str, Any]],
    manifest: Mapping[str, Any],
    dataset_manifest: Mapping[str, Any],
    cutoff: str,
    source_ref: str,
) -> dict[str, Any] | None:
    if not rows:
        return None
    available_at = _completion_bound(rows)
    if available_at is None:
        return None
    _, available = _timestamp(available_at, "available_at")
    _, cutoff_time = _timestamp(cutoff, "cutoff")
    if available >= cutoff_time:
        raise EnhancedReplayInputError(
            f"{family} contains a result not conservatively complete pre-cutoff"
        )
    source_role = (
        "fpl_gameweeks" if role == "lagged-player-features" else "match_results"
    )
    source = _source_by_role(dataset_manifest, source_role)
    artifact = _manifest_artifact(manifest, role)
    subset_sha = stable_hash(rows)
    if artifact.get("content_sha256") != subset_sha:
        raise EnhancedReplayInputError(f"{role} subset hash mismatch")
    return _observation(
        observation_id=(
            f"{manifest['episode_id']}:{family}:{role}:"
            f"{subset_sha[:16]}"
        ),
        source_id=str(source["source_id"]),
        source_ref=source_ref,
        content_sha256=subset_sha,
        upstream_source_sha256=str(source["content_hash_sha256"]),
        observed_at=str(source["observed_at"]),
        available_at=available_at,
        decision_cutoff=cutoff,
        strict_replay_admissible=True,
        availability_basis=(
            f"latest_fixture_kickoff_plus_{COMPLETION_BUFFER_HOURS}_hours"
        ),
        limitations=(
            "retrospective_source_acquisition",
            "conservative_event_completion_bound",
        ),
    )


def _exploratory_fixture_observation(
    *,
    manifest: Mapping[str, Any],
    observed: Mapping[str, Any],
    dataset_manifest: Mapping[str, Any],
    cutoff: str,
    source_ref: str,
) -> dict[str, Any]:
    rows = list(observed.get("fixtures", []))
    source = _source_by_role(dataset_manifest, "fpl_fixtures")
    artifact = _manifest_artifact(manifest, "fixture-schedule")
    subset_sha = stable_hash(rows)
    if artifact.get("content_sha256") != subset_sha:
        raise EnhancedReplayInputError("fixture schedule subset hash mismatch")
    return _observation(
        observation_id=(
            f"{manifest['episode_id']}:official_fpl_state:fixtures:"
            f"{subset_sha[:16]}"
        ),
        source_id=str(source["source_id"]),
        source_ref=source_ref,
        content_sha256=subset_sha,
        upstream_source_sha256=str(source["content_hash_sha256"]),
        observed_at=str(source["observed_at"]),
        available_at=str(source["observed_at"]),
        decision_cutoff=cutoff,
        strict_replay_admissible=False,
        availability_basis="postseason_final_export_observation",
        limitations=(
            "final_export_fixture_revision_not_archived",
            "not_an_immutable_predeadline_schedule_snapshot",
        ),
    )


def _exploratory_reference_observation(
    *,
    family: str,
    manifest: Mapping[str, Any],
    artifact: Mapping[str, Any],
    source_ref: str,
    source_id: str,
    observed_at: str,
    available_at: str,
    cutoff: str,
    published_at: str | None,
    limitations: Iterable[str],
) -> dict[str, Any]:
    return _observation(
        observation_id=(
            f"{manifest['episode_id']}:{family}:{stable_hash(artifact)[:16]}"
        ),
        source_id=source_id,
        source_ref=source_ref,
        content_sha256=stable_hash(artifact),
        observed_at=observed_at,
        available_at=available_at,
        decision_cutoff=cutoff,
        strict_replay_admissible=False,
        availability_basis="retrospective_project_observation",
        published_at=published_at,
        limitations=limitations,
    )


def _evidence_observation(
    *,
    manifest: Mapping[str, Any],
    evidence_artifact: Mapping[str, Any],
    evidence_ref: str,
    cutoff: str,
) -> dict[str, Any]:
    artifact = deepcopy(dict(evidence_artifact))
    if int(artifact.get("gameweek", manifest["gameweek"])) != int(
        manifest["gameweek"]
    ):
        raise EnhancedReplayInputError("evidence Gameweek mismatch")
    declared_cutoff = artifact.get("decision_cutoff")
    if declared_cutoff is not None:
        declared_text = _timestamp(declared_cutoff, "evidence decision_cutoff")[0]
        if declared_text != cutoff:
            raise EnhancedReplayInputError("evidence decision cutoff mismatch")
    candidates = list(artifact.get("candidates", artifact.get("sources", [])))
    published = [
        _timestamp(row.get("published_at"), "evidence published_at")[0]
        for row in candidates
        if row.get("published_at") is not None
    ]
    _, cutoff_time = _timestamp(cutoff, "cutoff")
    if any(
        _timestamp(value, "evidence published_at")[1] >= cutoff_time
        for value in published
    ):
        raise EnhancedReplayInputError(
            "evidence artifact contains a post-cutoff publication"
        )
    observed_at = str(
        artifact.get("researched_at")
        or artifact.get("captured_at")
        or ""
    )
    _timestamp(observed_at, "evidence observed_at")
    return _exploratory_reference_observation(
        family="unstructured_evidence",
        manifest=manifest,
        artifact=artifact,
        source_ref=evidence_ref,
        source_id="historical-retrospective-evidence",
        observed_at=observed_at,
        available_at=observed_at,
        cutoff=cutoff,
        published_at=max(published) if published else None,
        limitations=(
            "source_recovered_after_historical_decision",
            "retrospective_case_selection",
            "publication_before_cutoff_does_not_prove_policy_observation",
        ),
    )


def build_enhanced_episode_pack(
    *,
    manifest: Mapping[str, Any],
    observed: Mapping[str, Any],
    identity_map: Mapping[str, Any],
    dataset_manifest: Mapping[str, Any],
    canonical_refs: Mapping[str, str],
    evidence_artifact: Mapping[str, Any] | None = None,
    evidence_ref: str | None = None,
    seed_candidate_pool: Mapping[str, Any] | None = None,
    seed_candidate_ref: str | None = None,
    odds_comparator: Mapping[str, Any] | None = None,
    odds_ref: str | None = None,
) -> dict[str, Any]:
    """Build one safe availability pack without accepting an outcome payload."""

    manifest_copy = deepcopy(dict(manifest))
    observed_copy = deepcopy(dict(observed))
    identity_copy = deepcopy(dict(identity_map))
    dataset_copy = deepcopy(dict(dataset_manifest))
    gameweek, episode_id, cutoff, observed_sha = _validate_canonical(
        manifest_copy, observed_copy, identity_copy
    )
    _validate_dataset(dataset_copy, observed_copy)
    identity_sha = stable_hash(identity_copy)
    manifest_sha = stable_hash(manifest_copy)

    base_ref = str(canonical_refs["observed"]).replace("\\", "/")
    lagged = list(observed_copy.get("lagged_player_features", []))
    lagged_observation = _strict_history_observation(
        family="official_fpl_state",
        role="lagged-player-features",
        rows=lagged,
        manifest=manifest_copy,
        dataset_manifest=dataset_copy,
        cutoff=cutoff,
        source_ref=f"{base_ref}#/lagged_player_features",
    )
    fixture_observation = _exploratory_fixture_observation(
        manifest=manifest_copy,
        observed=observed_copy,
        dataset_manifest=dataset_copy,
        cutoff=cutoff,
        source_ref=f"{base_ref}#/fixtures",
    )
    official_observations = (
        [lagged_observation, fixture_observation]
        if lagged_observation is not None
        else [fixture_observation]
    )
    official_status = "degraded" if lagged_observation else "exploratory_only"
    families = [
        _family(
            "official_fpl_state",
            status=official_status,
            observations=official_observations,
            gaps=(
                "exact_predeadline_fixture_snapshot_unavailable",
                "exact_predeadline_price_snapshot_unavailable",
                *(
                    ("cold_start_no_prior_player_state",)
                    if lagged_observation is None
                    else ()
                ),
            ),
            fallback="canonical_lagged_state_with_visible_schedule_uncertainty",
        )
    ]

    context_observations: list[dict[str, Any]] = []
    if gameweek == 1 and seed_candidate_pool is not None:
        if seed_candidate_ref is None:
            raise EnhancedReplayInputError("seed candidate reference is required")
        observed_at = str(dataset_copy["created_at"])
        context_observations.append(
            _exploratory_reference_observation(
                family="promoted_transfer_context",
                manifest=manifest_copy,
                artifact=seed_candidate_pool,
                source_ref=seed_candidate_ref,
                source_id="historical-seed-counterfactual",
                observed_at=observed_at,
                available_at=observed_at,
                cutoff=cutoff,
                published_at=None,
                limitations=(
                    "retrospective_launch_field_reconstruction",
                    "predeadline_player_eligibility_not_complete",
                    "final_export_used_as_identity_bridge",
                ),
            )
        )
    families.append(
        _family(
            "promoted_transfer_context",
            status="exploratory_only" if context_observations else "unavailable",
            observations=context_observations,
            gaps=(
                "no_immutable_predeadline_transfer_registration_ledger",
                "no_complete_launch_market_snapshot",
            ),
            fallback="shrink_unknown_new_and_promoted_players",
        )
    )

    prior_results = list(observed_copy.get("prior_match_results", []))
    team_observation = _strict_history_observation(
        family="team_strength",
        role="prior-match-results",
        rows=prior_results,
        manifest=manifest_copy,
        dataset_manifest=dataset_copy,
        cutoff=cutoff,
        source_ref=f"{base_ref}#/prior_match_results",
    )
    families.append(
        _family(
            "team_strength",
            status="strict_available" if team_observation else "unavailable",
            observations=[team_observation] if team_observation else [],
            gaps=(
                ("no_prior_season_promoted_team_strength_pack",)
                if team_observation is None
                else ()
            ),
            fallback="neutral_team_strength_prior",
        )
    )

    families.extend(
        [
            _family(
                "player_ratings",
                status="unavailable",
                gaps=(
                    "no_verified_2025_26_point_in_time_rating_source",
                    "do_not_relabel_structured_form_as_vendor_rating",
                ),
                fallback="byte_identical_baseline",
            ),
            _family(
                "set_piece_roles",
                status="unavailable",
                gaps=(
                    "no_immutable_2025_26_official_set_piece_snapshot",
                    "do_not_infer_role_from_later_goals",
                ),
                fallback="byte_identical_baseline",
            ),
        ]
    )

    odds_observations: list[dict[str, Any]] = []
    if odds_comparator is not None:
        if odds_ref is None:
            raise EnhancedReplayInputError("odds reference is required")
        comparator = deepcopy(dict(odds_comparator))
        if comparator.get("contains_results") not in (None, False):
            raise EnhancedReplayInputError("odds comparator contains outcomes")
        if comparator.get("live_forecast_admission") is not False:
            raise EnhancedReplayInputError(
                "historical odds comparator cannot be live-admissible"
            )
        if comparator.get("content_sha256") != artifact_hash(comparator):
            raise EnhancedReplayInputError("odds comparator hash mismatch")
        odds_observations.append(
            _observation(
                observation_id=(
                    f"{episode_id}:odds:{comparator['content_sha256'][:16]}"
                ),
                source_id=str(comparator["source_id"]),
                source_ref=odds_ref,
                content_sha256=str(comparator["content_sha256"]),
                upstream_source_sha256=str(comparator["source_sha256"]),
                observed_at=str(comparator["observed_at"]),
                available_at=str(comparator["available_at"]),
                decision_cutoff=cutoff,
                strict_replay_admissible=False,
                availability_basis="source_schedule_without_quote_timestamp",
                limitations=(
                    "quote_level_availability_timestamp_unavailable",
                    "schedule_inferred_exploratory_comparator_only",
                    "closing_odds_excluded",
                ),
            )
        )
    families.append(
        _family(
            "odds",
            status="exploratory_only" if odds_observations else "unavailable",
            observations=odds_observations,
            gaps=("all_strict_predeadline_odds_slots_unavailable",),
            fallback="shared_structured_forecast_without_odds",
        )
    )

    evidence_observations: list[dict[str, Any]] = []
    if evidence_artifact is not None:
        if evidence_ref is None:
            raise EnhancedReplayInputError("evidence reference is required")
        evidence_observations.append(
            _evidence_observation(
                manifest=manifest_copy,
                evidence_artifact=evidence_artifact,
                evidence_ref=evidence_ref,
                cutoff=cutoff,
            )
        )
    families.append(
        _family(
            "unstructured_evidence",
            status=(
                "exploratory_only" if evidence_observations else "unavailable"
            ),
            observations=evidence_observations,
            gaps=(
                "no_live_captured_predeadline_evidence",
                "retrospective_research_not_strictly_admissible",
            ),
            fallback="frozen_no_evidence_control",
        )
    )

    if [family["family"] for family in families] != list(FAMILIES):
        raise EnhancedReplayInputError("feature family order/coverage mismatch")
    pack: dict[str, Any] = {
        "schema_version": "1.0",
        "pack_id": f"enhanced-input:{episode_id}",
        "content_sha256": "",
        "season": "2025-26",
        "gameweek": gameweek,
        "episode_id": episode_id,
        "decision_cutoff": cutoff,
        "classification": "exploratory_production_ineligible",
        "canonical_inputs": {
            "manifest_ref": str(canonical_refs["manifest"]).replace("\\", "/"),
            "manifest_sha256": manifest_sha,
            "observed_ref": base_ref,
            "observed_sha256": observed_sha,
            "identity_map_ref": str(canonical_refs["identity_map"]).replace(
                "\\", "/"
            ),
            "identity_map_sha256": identity_sha,
            "dataset_id": str(dataset_copy["dataset_id"]),
            "dataset_sha256": str(dataset_copy["dataset_hash"]),
        },
        "feature_availability": families,
        "strict_available_families": [
            family["family"]
            for family in families
            if family["strict_replay_admissible"]
        ],
        "exploratory_only_families": [
            family["family"]
            for family in families
            if family["status"] == "exploratory_only"
        ],
        "unavailable_families": [
            family["family"]
            for family in families
            if family["status"] == "unavailable"
        ],
        "safeguards": {
            "hidden_outcome_payload_read": False,
            "canonical_artifacts_mutated": False,
            "silent_defaults_allowed": False,
            "strict_admission_requires_available_before_cutoff": True,
            "retrospective_evidence_strictly_admissible": False,
        },
    }
    pack["content_sha256"] = artifact_hash(pack)
    return pack


def validate_enhanced_episode_pack(pack: Mapping[str, Any]) -> None:
    value = deepcopy(dict(pack))
    if value.get("content_sha256") != artifact_hash(value):
        raise EnhancedReplayInputError("enhanced input pack hash mismatch")
    if value.get("classification") != "exploratory_production_ineligible":
        raise EnhancedReplayInputError("enhanced input pack classification changed")
    families = value.get("feature_availability")
    if not isinstance(families, list) or [
        family.get("family") for family in families
    ] != list(FAMILIES):
        raise EnhancedReplayInputError("enhanced input pack family matrix invalid")
    cutoff = str(value.get("decision_cutoff", ""))
    for family in families:
        if family.get("status") not in STATUSES:
            raise EnhancedReplayInputError("enhanced input family status invalid")
        if not family.get("fallback"):
            raise EnhancedReplayInputError("enhanced input family fallback missing")
        for observation in family.get("observations", []):
            _sha256(observation.get("content_sha256"), "content_sha256")
            _, available = _timestamp(
                observation.get("available_at"), "available_at"
            )
            _, cutoff_time = _timestamp(cutoff, "decision_cutoff")
            _timestamp(observation.get("observed_at"), "observed_at")
            if (
                observation.get("strict_replay_admissible") is True
                and available >= cutoff_time
            ):
                raise EnhancedReplayInputError(
                    "strict observation is not pre-cutoff"
                )
    serialized = json.dumps(value, sort_keys=True)
    if '"hidden_outcome"' in serialized or '"player_outcomes"' in serialized:
        raise EnhancedReplayInputError("enhanced pack exposes hidden outcomes")


def build_enhanced_index(
    packs: Iterable[Mapping[str, Any]],
    *,
    canonical_tree_sha256: str,
    canonical_file_count: int,
) -> dict[str, Any]:
    values = [deepcopy(dict(pack)) for pack in packs]
    for pack in values:
        validate_enhanced_episode_pack(pack)
    values.sort(key=lambda pack: int(pack["gameweek"]))
    gameweeks = [int(pack["gameweek"]) for pack in values]
    if gameweeks != list(range(1, 39)):
        raise EnhancedReplayInputError(
            "enhanced replay index requires consecutive GW1-GW38 packs"
        )
    if len({pack["episode_id"] for pack in values}) != 38:
        raise EnhancedReplayInputError("enhanced replay episode IDs are not unique")
    coverage = {
        family: {
            status: sum(
                next(
                    row
                    for row in pack["feature_availability"]
                    if row["family"] == family
                )["status"]
                == status
                for pack in values
            )
            for status in sorted(STATUSES)
        }
        for family in FAMILIES
    }
    result: dict[str, Any] = {
        "schema_version": "1.0",
        "index_id": "enhanced-input-index:2025-26",
        "content_sha256": "",
        "season": "2025-26",
        "classification": "exploratory_production_ineligible",
        "gameweeks": gameweeks,
        "episode_count": len(values),
        "canonical_tree": {
            "sha256": _sha256(
                canonical_tree_sha256, "canonical_tree_sha256"
            ),
            "file_count": int(canonical_file_count),
            "allowlist": [
                "episode-manifest.json",
                "observed.json",
                "identity-map.json",
            ],
        },
        "coverage_matrix": coverage,
        "packs": [
            {
                "gameweek": pack["gameweek"],
                "episode_id": pack["episode_id"],
                "pack_id": pack["pack_id"],
                "content_sha256": pack["content_sha256"],
                "path": f"gw-{int(pack['gameweek']):02d}/input-pack.json",
            }
            for pack in values
        ],
        "replay_gate": {
            "ready_for_setup_validation": True,
            "ready_for_strict_feature_complete_claim": False,
            "requires_frozen_no_evidence_control": True,
            "requires_independent_arm_state": True,
            "requires_gap_preserving_fallbacks": True,
        },
    }
    result["content_sha256"] = artifact_hash(result)
    return result


def write_immutable_json(path: Path, value: Mapping[str, Any]) -> str:
    body = json.dumps(
        value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False
    ) + "\n"
    if path.exists():
        if path.read_text(encoding="utf-8") != body:
            raise EnhancedReplayInputError(
                f"refusing to overwrite immutable artifact: {path}"
            )
        return "unchanged"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8", newline="\n")
    return "written"


def canonical_input_tree_hash(
    episode_root: Path,
) -> tuple[str, int]:
    names = ("episode-manifest.json", "observed.json", "identity-map.json")
    records: list[dict[str, str]] = []
    for gameweek in range(1, 39):
        directory = episode_root / f"gw-{gameweek:02d}"
        for name in names:
            path = directory / name
            if not path.is_file():
                raise EnhancedReplayInputError(
                    f"missing canonical input file: {path}"
                )
            records.append(
                {
                    "path": path.relative_to(episode_root).as_posix(),
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
            )
    return stable_hash(records), len(records)
