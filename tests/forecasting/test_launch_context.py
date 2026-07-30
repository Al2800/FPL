"""Contracts for prospective launch classification and World Cup priors."""

from __future__ import annotations

from copy import deepcopy
import json
import os
import subprocess
from pathlib import Path

import pytest

from src.orchestration.preseason_snapshot import capture_preseason_snapshot

from src.forecasting.launch_context import (
    LaunchContextError,
    LaunchContextBuildConflict,
    LaunchContextBuildError,
    build_launch_context,
    apply_launch_context,
    artifact_hash,
    load_launch_context,
)


ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP_HASH = "a" * 64
WORLD_CUP_HASH = "b" * 64


def _bootstrap() -> dict:
    return {
        "teams": [
            {"id": 1, "code": 101, "name": "Promoted"},
            {"id": 2, "code": 202, "name": "Incumbent"},
        ],
        "elements": [
            {"id": 1, "code": 10, "team": 1},
            {"id": 2, "code": 20, "team": 2},
            {"id": 3, "code": 30, "team": 2},
            {"id": 4, "code": 40, "team": 2},
        ],
    }


def _context() -> dict:
    return {
        "season": "2026-27",
        "source_bindings": {
            "official_bootstrap": {
                "observed_at": "2026-07-20T08:00:00Z",
                "sha256": BOOTSTRAP_HASH,
            },
            "world_cup_priors": {"sha256": WORLD_CUP_HASH},
        },
        "promoted_teams": [{"team_id": 1, "team_code": 101, "name": "Promoted"}],
        "new_player_codes": [10, 20],
        "transferred_player_codes": [10, 30],
        "classification_policy": {
            "precedence": [
                "promoted_team",
                "new_to_fpl",
                "transferred_player",
                "established",
            ],
            "expected_class_counts": {
                "promoted_team": 1,
                "new_to_fpl": 1,
                "transferred_player": 1,
                "established": 1,
            },
        },
        "cold_start_risk": {
            "promoted_team": 0.1,
            "new_to_fpl": 0.08,
            "transferred_player": 0.08,
            "established": 0.0,
        },
        "world_cup_policy": {
            "fatigue_tier_score": {
                "none": 0.0,
                "moderate": 0.35,
                "high": 0.7,
                "extreme": 1.0,
            },
            "gameweek_fade": [1.0, 1.0, 0.5, 0.5, 0.25, 0.0],
        },
    }


def _world_rows() -> list[dict[str, str]]:
    return [
        {
            "fpl_code": "10",
            "fatigue_prior": "high",
            "wc_minutes": "420",
            "elimination_date": "2026-07-15",
            "return_to_training_date": "",
            "observed_at": "2026-07-20T07:00:00Z",
        },
        {
            "fpl_code": "999",
            "fatigue_prior": "moderate",
            "wc_minutes": "180",
            "elimination_date": "2026-07-01",
            "return_to_training_date": "",
            "observed_at": "2026-07-20T07:00:00Z",
        },
        {
            "fpl_code": "",
            "fatigue_prior": "none",
            "wc_minutes": "",
            "elimination_date": "",
            "return_to_training_date": "",
            "observed_at": "2026-07-20T07:00:00Z",
        },
    ]


def _apply(
    *,
    context: dict | None = None,
    world_rows: list[dict[str, str]] | None = None,
    cutoff: str = "2026-08-14T17:30:00Z",
    gameweek: int = 3,
) -> dict:
    return apply_launch_context(
        bootstrap=_bootstrap(),
        context=context or _context(),
        world_cup_rows=world_rows or _world_rows(),
        official_bootstrap_source_sha256=BOOTSTRAP_HASH,
        world_cup_source_sha256=WORLD_CUP_HASH,
        decision_cutoff=cutoff,
        gameweek=gameweek,
    )


def test_classifies_every_player_once_and_keeps_orthogonal_flags() -> None:
    result = _apply()
    assert result["class_counts"] == {
        "promoted_team": 1,
        "new_to_fpl": 1,
        "transferred_player": 1,
        "established": 1,
    }
    players = {row["fpl_code"]: row for row in result["players"]}
    assert players[10]["cold_start_class"] == "promoted_team"
    assert players[10]["is_new_to_fpl"] is True
    assert players[10]["changed_club"] is True
    assert players[20]["cold_start_class"] == "new_to_fpl"
    assert players[30]["cold_start_class"] == "transferred_player"
    assert players[40]["cold_start_class"] == "established"


def test_world_cup_prior_joins_by_code_fades_and_reports_unknowns() -> None:
    result = _apply(gameweek=3)
    players = {row["fpl_code"]: row for row in result["players"]}
    assert players[10]["world_cup"]["effective_fatigue"] == 0.35
    assert players[10]["world_cup"]["return_to_training_date"] is None
    assert players[20]["world_cup"]["status"] == "not_in_admitted_ledger"
    assert result["world_cup_coverage"] == {
        "ledger_rows": 3,
        "matched_rows": 1,
        "blank_code_rows": 1,
        "non_current_code_rows": 1,
        "late_rows": 0,
        "missing_return_to_training_rows": 1,
    }
    assert {row["reason"] for row in result["degraded_features"]} == {
        "blank_stable_fpl_code_no_name_join",
        "stable_code_not_in_current_official_universe",
    }


def test_late_world_cup_row_degrades_but_late_official_context_blocks() -> None:
    rows = _world_rows()
    rows[0]["observed_at"] = "2026-08-14T17:30:00Z"
    result = _apply(world_rows=rows)
    assert result["world_cup_coverage"]["late_rows"] == 1
    assert next(
        row for row in result["players"] if row["fpl_code"] == 10
    )["world_cup"]["status"] == "not_in_admitted_ledger"

    context = _context()
    context["source_bindings"]["official_bootstrap"]["observed_at"] = (
        "2026-08-14T17:30:00Z"
    )
    with pytest.raises(LaunchContextError, match="strictly before decision cutoff"):
        _apply(context=context)


def test_unknown_identity_duplicate_world_code_and_source_hash_fail_closed() -> None:
    context = _context()
    context["promoted_teams"][0]["team_code"] = 999
    with pytest.raises(LaunchContextError, match="stable code does not match"):
        _apply(context=context)

    context = _context()
    context["transferred_player_codes"].append(999)
    with pytest.raises(LaunchContextError, match="empty or unknown"):
        _apply(context=context)

    duplicate = _world_rows()
    duplicate.append(deepcopy(duplicate[1]))
    with pytest.raises(LaunchContextError, match="Duplicate World Cup stable code"):
        _apply(world_rows=duplicate)

    with pytest.raises(LaunchContextError, match="source hash mismatch"):
        apply_launch_context(
            bootstrap=_bootstrap(),
            context=_context(),
            world_cup_rows=_world_rows(),
            official_bootstrap_source_sha256="c" * 64,
            world_cup_source_sha256=WORLD_CUP_HASH,
            decision_cutoff="2026-08-14T17:30:00Z",
            gameweek=1,
        )


def test_committed_context_is_self_hashed_and_non_empty() -> None:
    path = ROOT / "control" / "identities" / "2026-27-launch-context.json"
    context = load_launch_context(path)
    assert context["content_sha256"] == artifact_hash(context)
    assert len(context["promoted_teams"]) == 3
    assert context["new_player_codes"]
    assert context["transferred_player_codes"]
    assert sum(context["classification_policy"]["expected_class_counts"].values()) == 558


def test_hash_tamper_is_rejected(tmp_path: Path) -> None:
    context = _context()
    context["content_sha256"] = artifact_hash(context)
    context["season"] = "tampered"
    path = tmp_path / "context.json"
    path.write_text(json.dumps(context), encoding="utf-8")
    with pytest.raises(LaunchContextError, match="content hash mismatch"):
        load_launch_context(path)

# ---------------------------------------------------------------------------
# FPL-757 — immutable successor derivation for changed player universes
# ---------------------------------------------------------------------------

BUILD_CUTOFF = "2026-08-21T17:30:00Z"
BUILD_OBSERVED = "2026-08-03T12:05:00Z"


def _builder_bootstrap() -> dict:
    return {
        "teams": [
            {"id": 1, "code": 101, "name": "Promoted"},
            {"id": 2, "code": 202, "name": "Incumbent"},
        ],
        "elements": [
            {"id": 1, "code": 10, "team": 1},
            {"id": 2, "code": 20, "team": 2},
            {"id": 3, "code": 40, "team": 2},
            {"id": 4, "code": 50, "team": 2},
        ],
        "events": [{"id": 1, "deadline_time": BUILD_CUTOFF}],
    }


def _builder_inputs(tmp_path: Path, *, bootstrap: dict | None = None) -> tuple[Path, Path, Path]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    bootstrap_path = tmp_path / "bootstrap.json"
    bootstrap_path.write_text(json.dumps(bootstrap or _builder_bootstrap()), encoding="utf-8")
    prior_path = tmp_path / "prior.csv"
    prior_path.write_text("code,team_code\n20,303\n30,404\n50,202\n", encoding="utf-8")
    world_cup_path = tmp_path / "world-cup.csv"
    world_cup_path.write_text(
        "fpl_code,observed_at,return_to_training_date\n10,2026-07-21T17:21:28Z,\n999,2026-07-21T17:21:28Z,\n,2026-07-21T17:21:28Z,\n",
        encoding="utf-8",
    )
    return bootstrap_path, prior_path, world_cup_path


def _build_successor(
    tmp_path: Path, *, bootstrap: dict | None = None, output_root: Path | None = None
) -> dict:
    bootstrap_path, prior_path, world_cup_path = _builder_inputs(tmp_path, bootstrap=bootstrap)
    return build_launch_context(
        season="2026-27",
        bootstrap_path=bootstrap_path,
        bootstrap_observed_at="2026-08-03T12:00:00Z",
        bootstrap_available_at="2026-08-03T12:00:00Z",
        prior_roster_path=prior_path,
        prior_roster_observed_at="2026-05-25T12:00:00Z",
        prior_roster_available_at="2026-05-25T12:00:00Z",
        world_cup_priors_path=world_cup_path,
        world_cup_observed_at="2026-07-21T17:21:28Z",
        world_cup_available_at="2026-07-21T17:21:28Z",
        context_observed_at=BUILD_OBSERVED,
        context_available_at=BUILD_OBSERVED,
        decision_cutoff=BUILD_CUTOFF,
        output_root=output_root or (tmp_path / "derived"),
    )


def test_successor_context_derives_classes_delta_and_is_idempotent(tmp_path: Path) -> None:
    first = _build_successor(tmp_path)
    second = _build_successor(tmp_path)
    context = first["context"]
    assert second["context"] == context
    assert context["source_bindings"]["official_bootstrap"]["available_at"] == "2026-08-03T12:00:00Z"
    assert context["new_player_codes"] == [10, 40]
    assert context["transferred_player_codes"] == [20]
    assert context["promoted_team_ids"] == [1]
    assert context["classification_policy"]["expected_class_counts"] == {
        "promoted_team": 1,
        "new_to_fpl": 1,
        "transferred_player": 1,
        "established": 1,
    }
    assert context["universe_delta"]["removed_player_codes"] == [30]
    assert context["universe_delta"]["changed_team_codes"] == [20]
    assert context["world_cup_coverage"] == {
        "ledger_rows": 3,
        "current_official_code_matches": 1,
        "non_current_stable_codes": 1,
        "blank_stable_codes": 1,
        "late_rows": 0,
        "return_to_training_dates_present": 0,
    }
    assert first["context_path"].is_file()
    assert first["manifest_path"].is_file()
    assert json.loads(first["context_path"].read_text())["content_sha256"] == context["content_sha256"]


def test_successor_changed_universe_is_additive_not_overwrite(tmp_path: Path) -> None:
    first = _build_successor(tmp_path)
    original_context_bytes = first["context_path"].read_bytes()
    changed = _builder_bootstrap()
    changed["elements"].append({"id": 5, "code": 60, "team": 2})
    second = _build_successor(
        tmp_path / "changed", bootstrap=changed, output_root=tmp_path / "derived"
    )
    assert second["context_path"] != first["context_path"]
    assert first["context_path"].read_bytes() == original_context_bytes
    assert 60 in second["context"]["new_player_codes"]


def test_successor_rejects_duplicate_late_and_tampered_inputs(tmp_path: Path) -> None:
    bootstrap_path, prior_path, world_cup_path = _builder_inputs(tmp_path)
    prior_path.write_text("code,team_code\n20,101\n20,202\n", encoding="utf-8")
    with pytest.raises(LaunchContextBuildError, match="Duplicate prior"):
        build_launch_context(
            season="2026-27", bootstrap_path=bootstrap_path,
            bootstrap_observed_at="2026-08-03T12:00:00Z", bootstrap_available_at="2026-08-03T12:00:00Z",
            prior_roster_path=prior_path, prior_roster_observed_at="2026-05-25T12:00:00Z",
            prior_roster_available_at="2026-05-25T12:00:00Z",
            world_cup_priors_path=world_cup_path, world_cup_observed_at="2026-07-21T17:21:28Z",
            world_cup_available_at="2026-07-21T17:21:28Z",
            context_observed_at=BUILD_OBSERVED, context_available_at=BUILD_OBSERVED,
            decision_cutoff=BUILD_CUTOFF, output_root=tmp_path / "derived",
        )

    bootstrap_path, prior_path, world_cup_path = _builder_inputs(tmp_path / "late")
    with pytest.raises(LaunchContextBuildError, match="strictly before decision cutoff"):
        build_launch_context(
            season="2026-27", bootstrap_path=bootstrap_path,
            bootstrap_observed_at=BUILD_CUTOFF, bootstrap_available_at=BUILD_CUTOFF,
            prior_roster_path=prior_path, prior_roster_observed_at="2026-05-25T12:00:00Z",
            prior_roster_available_at="2026-05-25T12:00:00Z",
            world_cup_priors_path=world_cup_path, world_cup_observed_at="2026-07-21T17:21:28Z",
            world_cup_available_at="2026-07-21T17:21:28Z",
            context_observed_at=BUILD_OBSERVED, context_available_at=BUILD_OBSERVED,
            decision_cutoff=BUILD_CUTOFF, output_root=tmp_path / "late" / "derived",
        )

    result = _build_successor(tmp_path / "tampered")
    copied_bootstrap = result["context_path"].parent / "inputs" / "bootstrap-static.json"
    copied_bootstrap.write_text("tampered", encoding="utf-8")
    with pytest.raises(LaunchContextBuildConflict, match="failed hash validation"):
        _build_successor(tmp_path / "tampered")


def test_successor_context_is_admitted_only_by_matching_checkpoint(tmp_path: Path) -> None:
    result = _build_successor(tmp_path)
    bootstrap = _builder_bootstrap()
    bootstrap_body = (result["context_path"].parent / "inputs" / "bootstrap-static.json").read_bytes()
    common = {
        "season": "2026-27",
        "checkpoint_id": "launch",
        "deadline": BUILD_CUTOFF,
        "observed_at": BUILD_OBSERVED,
        "bootstrap_body": bootstrap_body,
        "fixtures_body": b"[]",
        "rules_path": ROOT / "control" / "rules" / "2026-27.yaml",
        "config_path": ROOT / "config" / "data_sources" / "2026-27-preseason.json",
        "code_commit": "a" * 40,
        "launch_context_path": result["context_path"],
        "world_cup_priors_path": result["context_path"].parent / "inputs" / "world-cup-priors.csv",
    }
    matching = capture_preseason_snapshot(
        **common, output_root=tmp_path / "matching", index_manifest_path=tmp_path / "matching-index.json"
    )
    assert matching["families"]["launch_context"]["status"] == "admitted"

    changed = _builder_bootstrap()
    changed["elements"].append({"id": 5, "code": 60, "team": 2})
    mismatch_common = dict(common)
    mismatch_common["bootstrap_body"] = json.dumps(changed, sort_keys=True).encode("utf-8")
    mismatching = capture_preseason_snapshot(
        **mismatch_common,
        output_root=tmp_path / "mismatching",
        index_manifest_path=tmp_path / "mismatching-index.json",
    )
    family = mismatching["families"]["launch_context"]
    assert family["status"] == "degraded"
    assert family["reasons"] == ["official_bootstrap_hash_mismatch"]
    assert family["artifact_path"] is None


def test_successor_builder_cli_reports_paths_hashes_and_delta(tmp_path: Path) -> None:
    bootstrap_path, prior_path, world_cup_path = _builder_inputs(tmp_path)
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT)
    result = subprocess.run(
        [
            "python", str(ROOT / "scripts" / "build_launch_context.py"),
            "--bootstrap-file", str(bootstrap_path),
            "--bootstrap-observed-at", "2026-08-03T12:00:00Z",
            "--bootstrap-available-at", "2026-08-03T12:00:00Z",
            "--prior-roster-file", str(prior_path),
            "--prior-roster-observed-at", "2026-05-25T12:00:00Z",
            "--prior-roster-available-at", "2026-05-25T12:00:00Z",
            "--world-cup-priors-file", str(world_cup_path),
            "--world-cup-observed-at", "2026-07-21T17:21:28Z",
            "--world-cup-available-at", "2026-07-21T17:21:28Z",
            "--context-observed-at", BUILD_OBSERVED,
            "--context-available-at", BUILD_OBSERVED,
            "--decision-cutoff", BUILD_CUTOFF,
            "--output-root", str(tmp_path / "cli-derived"),
        ],
        cwd=ROOT, capture_output=True, text=True, check=False, env=env,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert Path(payload["context_path"]).is_file()
    assert Path(payload["manifest_path"]).is_file()
    assert payload["universe_delta"]["removed_player_codes"] == [30]
    assert len(payload["context_content_sha256"]) == 64
