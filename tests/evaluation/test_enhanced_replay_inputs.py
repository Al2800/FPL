from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from src.evaluation.enhanced_replay_inputs import (
    EnhancedReplayInputError,
    FAMILIES,
    artifact_hash,
    build_enhanced_episode_pack,
    build_enhanced_index,
    stable_hash,
    validate_enhanced_episode_pack,
    write_immutable_json,
)


SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64
SHA_D = "d" * 64


def _inputs(*, late_history: bool = False):
    cutoff = "2025-08-22T17:30:00Z"
    lagged = [
        {
            "GW": 1,
            "element": 1,
            "fixture": 1,
            "kickoff_time": (
                "2025-08-22T14:00:00Z"
                if late_history
                else "2025-08-17T15:30:00Z"
            ),
        }
    ]
    fixtures = [
        {
            "id": 11,
            "event": 2,
            "kickoff_time": "2025-08-23T14:00:00Z",
            "team_h": 1,
            "team_a": 2,
        }
    ]
    results = [
        {
            "kickoff_time": "2025-08-17T15:30:00Z",
            "home_team_id": "team:2025-26:1",
            "away_team_id": "team:2025-26:2",
            "home_goals": 2,
            "away_goals": 1,
        }
    ]
    identity = {
        "season": "2025-26",
        "players": [{"fpl_player_id": 1, "canonical_id": "player:2025-26:1"}],
        "teams": [
            {
                "fpl_team_id": 1,
                "fpl_name": "Alpha",
                "canonical_id": "team:2025-26:1",
            },
            {
                "fpl_team_id": 2,
                "fpl_name": "Beta",
                "canonical_id": "team:2025-26:2",
            },
        ],
    }
    observed = {
        "observed_partition_version": "1.0",
        "episode_id": "benchmark-v0:2025-26:gw02:manager-neutral",
        "season": "2025-26",
        "gameweek": 2,
        "cutoff": cutoff,
        "deadline": cutoff,
        "dataset_id": "benchmark-v0-2025-26",
        "dataset_hash": SHA_A,
        "lagged_from_gameweek": 1,
        "lagged_player_features": lagged,
        "fixtures": fixtures,
        "prior_match_results": results,
        "identity_map_ref": {"content_sha256": stable_hash(identity)},
        "limitations": [],
    }
    manifest = {
        "schema_version": "1.0",
        "episode_id": observed["episode_id"],
        "season": "2025-26",
        "gameweek": 2,
        "mode": "historical_structured",
        "cutoff": cutoff,
        "deadline": cutoff,
        "hidden_outcome_ref": {
            "content_sha256": SHA_D,
            "reveal_after": "proposal_frozen",
        },
        "observed": {
            "feature_snapshot_ref": {
                "content_sha256": stable_hash(observed)
            },
            "source_artifacts": [
                {
                    "artifact_id": "historical:lagged-player-features:gw02:test",
                    "content_sha256": stable_hash(lagged),
                    "available_at": cutoff,
                },
                {
                    "artifact_id": "historical:fixture-schedule:gw02:test",
                    "content_sha256": stable_hash(fixtures),
                    "available_at": cutoff,
                },
                {
                    "artifact_id": "historical:prior-match-results:gw02:test",
                    "content_sha256": stable_hash(results),
                    "available_at": cutoff,
                },
            ],
        },
    }
    dataset = {
        "status": "frozen",
        "season": "2025-26",
        "dataset_id": "benchmark-v0-2025-26",
        "dataset_hash": SHA_A,
        "created_at": "2026-07-22T12:57:20Z",
        "sources": [
            {
                "dataset_role": "fpl_gameweeks",
                "source_id": "vaastav-fpl",
                "observed_at": "2026-07-22T12:57:20Z",
                "content_hash_sha256": SHA_A,
            },
            {
                "dataset_role": "fpl_fixtures",
                "source_id": "vaastav-fpl",
                "observed_at": "2026-07-22T12:57:20Z",
                "content_hash_sha256": SHA_B,
            },
            {
                "dataset_role": "match_results",
                "source_id": "football-data-co-uk",
                "observed_at": "2026-07-22T12:57:20Z",
                "content_hash_sha256": SHA_C,
            },
        ],
    }
    evidence = {
        "gameweek": 2,
        "decision_cutoff": cutoff,
        "researched_at": "2026-07-27T10:18:35Z",
        "candidates": [
            {
                "source_id": "official-analysis",
                "published_at": "2025-08-21T12:00:00Z",
            }
        ],
    }
    odds = {
        "schema_version": "1.0",
        "source_id": "football-data-co-uk",
        "season": "2025-26",
        "observed_at": "2026-07-22T12:57:20Z",
        "available_at": "2026-07-22T12:57:20Z",
        "source_sha256": SHA_C,
        "timing_label": "source_scheduled_preclosing",
        "live_forecast_admission": False,
        "matches": [],
    }
    odds["content_sha256"] = artifact_hash(odds)
    return manifest, observed, identity, dataset, evidence, odds


def _build(**kwargs):
    manifest, observed, identity, dataset, evidence, odds = _inputs(
        late_history=kwargs.pop("late_history", False)
    )
    return build_enhanced_episode_pack(
        manifest=manifest,
        observed=observed,
        identity_map=identity,
        dataset_manifest=dataset,
        canonical_refs={
            "manifest": "canonical/gw-02/episode-manifest.json",
            "observed": "canonical/gw-02/observed.json",
            "identity_map": "canonical/gw-02/identity-map.json",
        },
        evidence_artifact=kwargs.pop("evidence", evidence),
        evidence_ref="evidence/gw-02.json",
        odds_comparator=kwargs.pop("odds", odds),
        odds_ref="local/odds.json",
        **kwargs,
    )


def test_pack_exposes_every_family_without_promoting_retrospective_inputs():
    pack = _build()
    validate_enhanced_episode_pack(pack)
    families = {
        row["family"]: row for row in pack["feature_availability"]
    }

    assert list(families) == list(FAMILIES)
    assert families["official_fpl_state"]["status"] == "degraded"
    assert families["official_fpl_state"]["strict_observation_count"] == 1
    assert families["team_strength"]["status"] == "strict_available"
    assert families["player_ratings"]["status"] == "unavailable"
    assert families["set_piece_roles"]["status"] == "unavailable"
    assert families["odds"]["status"] == "exploratory_only"
    assert families["unstructured_evidence"]["status"] == "exploratory_only"
    assert (
        families["unstructured_evidence"]["observations"][0][
            "strict_replay_admissible"
        ]
        is False
    )
    serialized = json.dumps(pack, sort_keys=True)
    assert '"hidden_outcome"' not in serialized
    assert SHA_D not in serialized
    assert pack["safeguards"]["silent_defaults_allowed"] is False


def test_observed_hash_tampering_fails_closed():
    manifest, observed, identity, dataset, _, _ = _inputs()
    observed["fixtures"][0]["team_h"] = 99
    with pytest.raises(
        EnhancedReplayInputError,
        match="observed partition content hash mismatch",
    ):
        build_enhanced_episode_pack(
            manifest=manifest,
            observed=observed,
            identity_map=identity,
            dataset_manifest=dataset,
            canonical_refs={
                "manifest": "manifest.json",
                "observed": "observed.json",
                "identity_map": "identity.json",
            },
        )


def test_history_not_conservatively_complete_before_cutoff_is_rejected():
    with pytest.raises(
        EnhancedReplayInputError,
        match="not conservatively complete pre-cutoff",
    ):
        _build(late_history=True)


def test_post_cutoff_evidence_publication_is_rejected():
    _, _, _, _, evidence, _ = _inputs()
    evidence["candidates"][0]["published_at"] = "2025-08-22T17:30:00Z"
    with pytest.raises(
        EnhancedReplayInputError,
        match="post-cutoff publication",
    ):
        _build(evidence=evidence)


def test_odds_artifact_with_outcomes_is_rejected():
    _, _, _, _, _, odds = _inputs()
    odds["contains_results"] = True
    odds["content_sha256"] = artifact_hash(odds)
    with pytest.raises(
        EnhancedReplayInputError, match="contains outcomes"
    ):
        _build(odds=odds)


def test_immutable_writer_allows_identical_rerun_only(tmp_path: Path):
    pack = _build()
    path = tmp_path / "pack.json"
    assert write_immutable_json(path, pack) == "written"
    assert write_immutable_json(path, pack) == "unchanged"
    changed = deepcopy(pack)
    changed["classification"] = "changed"
    changed["content_sha256"] = artifact_hash(changed)
    with pytest.raises(EnhancedReplayInputError, match="refusing to overwrite"):
        write_immutable_json(path, changed)


def test_index_requires_all_38_consecutive_packs():
    template = _build()
    with pytest.raises(
        EnhancedReplayInputError, match="requires consecutive GW1-GW38"
    ):
        build_enhanced_index(
            [template],
            canonical_tree_sha256=SHA_A,
            canonical_file_count=3,
        )

    packs = []
    for gameweek in range(1, 39):
        pack = deepcopy(template)
        pack["gameweek"] = gameweek
        pack["episode_id"] = (
            f"benchmark-v0:2025-26:gw{gameweek:02d}:manager-neutral"
        )
        pack["pack_id"] = f"enhanced-input:{pack['episode_id']}"
        pack["content_sha256"] = artifact_hash(pack)
        packs.append(pack)
    index = build_enhanced_index(
        packs,
        canonical_tree_sha256=SHA_A,
        canonical_file_count=114,
    )
    assert index["episode_count"] == 38
    assert index["gameweeks"] == list(range(1, 39))
    assert index["replay_gate"]["ready_for_strict_feature_complete_claim"] is False
