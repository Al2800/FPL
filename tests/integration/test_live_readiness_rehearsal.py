from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from src.orchestration.initial_squad_checkpoint import run_initial_squad_checkpoint
from src.orchestration.live_readiness_rehearsal import (
    LiveReadinessRehearsalConflict,
    LiveReadinessRehearsalError,
    compare_final_checkpoint,
    run_live_readiness_rehearsal,
)
from src.orchestration.preseason_snapshot import (
    artifact_hash,
    capture_preseason_snapshot,
)


REPO = Path(__file__).resolve().parents[2]
DEADLINE = "2026-08-21T17:30:00Z"
T48 = "2026-08-19T17:30:00Z"


def _bootstrap(*, goalkeepers: int = 4) -> dict:
    elements: list[dict] = []
    player_id = 1
    for element_type, count, base in (
        (1, goalkeepers, 3.8),
        (2, 8, 4.6),
        (3, 8, 5.9),
        (4, 6, 5.4),
    ):
        for index in range(count):
            elements.append(
                {
                    "id": player_id,
                    "code": 500_000 + player_id,
                    "web_name": f"Player {player_id}",
                    "element_type": element_type,
                    "team": (player_id - 1) % 10 + 1,
                    "now_cost": 40 + (index % 3) * 5,
                    "status": "a",
                    "ep_next": str(round(base - index * 0.1, 2)),
                    "chance_of_playing_next_round": None,
                }
            )
            player_id += 1
    return {
        "events": [{"id": 1, "deadline_time": DEADLINE}],
        "elements": elements,
        "teams": [{"id": index, "name": f"Team {index}"} for index in range(1, 11)],
    }


def _policy(path: Path, *, version: str = "rehearsal-test-v1") -> Path:
    policy = json.loads(
        (REPO / "control" / "policies" / "initial-squad-2026-27.json").read_text(
            encoding="utf-8"
        )
    )
    policy["policy_version"] = version
    policy["search"].update(
        {
            "beam_width": 120,
            "candidate_limit_per_position": 12,
            "cheapest_per_position": 4,
            "retained_squads": 3,
        }
    )
    path.write_text(json.dumps(policy, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _capture(
    tmp_path: Path,
    *,
    checkpoint_id: str = "weekly-2026-08-19",
    observed_at: str = T48,
    goalkeepers: int = 4,
) -> Path:
    root = tmp_path / "snapshots"
    capture_preseason_snapshot(
        season="2026-27",
        checkpoint_id=checkpoint_id,
        deadline=DEADLINE,
        output_root=root,
        observed_at=observed_at,
        bootstrap_body=json.dumps(_bootstrap(goalkeepers=goalkeepers), sort_keys=True).encode(),
        fixtures_body=b"[]",
        index_manifest_path=tmp_path / "index.json",
        update_index=False,
    )
    return root / checkpoint_id / "manifest.json"


def _reseal(path: Path, value: dict) -> None:
    value["content_sha256"] = artifact_hash(value)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_t48_rehearsal_writes_hash_bound_degraded_advisory_gdr_and_is_idempotent(
    tmp_path: Path,
) -> None:
    manifest = _capture(tmp_path)
    output_root = tmp_path / "readiness"
    report = run_live_readiness_rehearsal(
        manifest_path=manifest,
        output_root=output_root,
        policy_path=_policy(tmp_path / "policy.json"),
    )
    run_dir = output_root / "weekly-2026-08-19"
    gdr = json.loads((run_dir / "gameweek-decision-record.json").read_text())
    recommendation = json.loads((run_dir / "recommendation.json").read_text())

    assert report["operational_status"] == "go_degraded"
    assert report["approval_status"] == "blocked"
    assert report["account_writes"] is False
    assert gdr["account_writes"] is False
    assert gdr["execution"]["mode"] == "manual"
    assert gdr["provenance"]["recommendation_sha256"] == recommendation["content_sha256"]
    assert "licensed_odds" in report["coverage"]["optional_gaps"]

    before = {path.relative_to(run_dir): path.read_bytes() for path in run_dir.rglob("*") if path.is_file()}
    second = run_live_readiness_rehearsal(
        manifest_path=manifest,
        output_root=output_root,
        policy_path=_policy(tmp_path / "policy.json"),
    )
    after = {path.relative_to(run_dir): path.read_bytes() for path in run_dir.rglob("*") if path.is_file()}
    assert report == second
    assert before == after


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("missing_mandatory", "Mandatory manifest family is not admitted"),
        ("bad_hash", "content hash mismatch"),
        ("post_cutoff", "available_at.*after decision cutoff"),
    ],
)
def test_integrity_and_chronology_failures_write_no_frozen_recommendation(
    tmp_path: Path,
    mutation: str,
    message: str,
) -> None:
    manifest = _capture(tmp_path)
    value = json.loads(manifest.read_text())
    if mutation == "missing_mandatory":
        value["families"]["official_bootstrap"]["status"] = "unavailable"
        _reseal(manifest, value)
    elif mutation == "bad_hash":
        value["content_sha256"] = "0" * 64
        manifest.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    else:
        value["families"]["official_bootstrap"]["available_at"] = DEADLINE
        _reseal(manifest, value)

    output_root = tmp_path / "readiness"
    with pytest.raises(LiveReadinessRehearsalError, match=message):
        run_live_readiness_rehearsal(
            manifest_path=manifest,
            output_root=output_root,
            policy_path=_policy(tmp_path / "policy.json"),
        )
    assert not (output_root / "weekly-2026-08-19" / "recommendation.json").exists()


def test_illegal_squad_and_budget_failure_do_not_freeze_a_recommendation(
    tmp_path: Path,
) -> None:
    output_root = tmp_path / "readiness"
    illegal = _capture(tmp_path / "illegal", goalkeepers=1)
    with pytest.raises(LiveReadinessRehearsalError, match="Not enough available GKP"):
        run_live_readiness_rehearsal(
            manifest_path=illegal,
            output_root=output_root,
            policy_path=_policy(tmp_path / "illegal-policy.json"),
        )
    assert not (output_root / "weekly-2026-08-19" / "recommendation.json").exists()

    budget = _capture(tmp_path / "budget")
    with pytest.raises(LiveReadinessRehearsalError, match="stage exceeded"):
        run_live_readiness_rehearsal(
            manifest_path=budget,
            output_root=tmp_path / "budget-readiness",
            policy_path=_policy(tmp_path / "budget-policy.json"),
            maximum_checkpoint_seconds=0.0000001,
        )
    assert not (
        tmp_path / "budget-readiness" / "weekly-2026-08-19" / "recommendation.json"
    ).exists()


def test_late_capture_and_attempted_overwrite_are_refused(tmp_path: Path) -> None:
    late = _capture(tmp_path / "late", observed_at="2026-08-19T17:46:00Z")
    with pytest.raises(LiveReadinessRehearsalError, match="T-48h capture"):
        run_live_readiness_rehearsal(
            manifest_path=late,
            output_root=tmp_path / "late-readiness",
            policy_path=_policy(tmp_path / "late-policy.json"),
        )

    manifest = _capture(tmp_path / "overwrite")
    output_root = tmp_path / "overwrite-readiness"
    run_live_readiness_rehearsal(
        manifest_path=manifest,
        output_root=output_root,
        policy_path=_policy(tmp_path / "policy-v1.json", version="v1"),
    )
    with pytest.raises(LiveReadinessRehearsalConflict, match="different request"):
        run_live_readiness_rehearsal(
            manifest_path=manifest,
            output_root=output_root,
            policy_path=_policy(tmp_path / "policy-v2.json", version="v2"),
        )


def test_final_checkpoint_comparison_is_additive(tmp_path: Path) -> None:
    rehearsal_manifest = _capture(tmp_path / "rehearsal")
    output_root = tmp_path / "readiness"
    report = run_live_readiness_rehearsal(
        manifest_path=rehearsal_manifest,
        output_root=output_root,
        policy_path=_policy(tmp_path / "rehearsal-policy.json"),
    )
    rehearsal_dir = output_root / str(report["checkpoint_id"])
    before = {path.relative_to(rehearsal_dir): path.read_bytes() for path in rehearsal_dir.rglob("*") if path.is_file()}

    final_manifest = _capture(
        tmp_path / "final", checkpoint_id="weekly-2026-08-21", observed_at="2026-08-21T12:00:00Z"
    )
    final = run_initial_squad_checkpoint(
        manifest_path=final_manifest,
        output_root=tmp_path / "final-output",
        policy_path=_policy(tmp_path / "final-policy.json"),
    )
    comparison = compare_final_checkpoint(
        rehearsal_root=output_root,
        rehearsal_checkpoint_id=str(report["checkpoint_id"]),
        final_checkpoint_path=tmp_path / "final-output" / "weekly-2026-08-21" / "checkpoint.json",
    )
    after = {path.relative_to(rehearsal_dir): path.read_bytes() for path in rehearsal_dir.rglob("*") if path.is_file()}
    assert before == after
    assert comparison["final_checkpoint_sha256"] == final["content_sha256"]
    assert list((output_root / "final-comparisons").glob("*.json"))
