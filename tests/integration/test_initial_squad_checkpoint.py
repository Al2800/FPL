from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from src.orchestration.initial_squad_checkpoint import (
    InitialSquadCheckpointConflict,
    InitialSquadCheckpointError,
    run_initial_squad_checkpoint,
    verify_preseason_manifest,
)
from src.orchestration.preseason_snapshot import (
    artifact_hash,
    capture_preseason_snapshot,
)


REPO = Path(__file__).resolve().parents[2]
DEADLINE = "2026-08-21T17:30:00Z"


def _bootstrap(*, boost_player_id: int | None = None, goalkeepers: int = 4) -> dict:
    elements: list[dict] = []
    player_id = 1
    for element_type, count, base in (
        (1, goalkeepers, 3.6),
        (2, 8, 4.4),
        (3, 8, 5.8),
        (4, 6, 5.2),
    ):
        for index in range(count):
            ep_next = round(base - index * 0.1, 2)
            if player_id == boost_player_id:
                ep_next = 12.0
            elements.append(
                {
                    "id": player_id,
                    "code": 100_000 + player_id,
                    "web_name": f"Player {player_id}",
                    "element_type": element_type,
                    "team": (player_id - 1) % 10 + 1,
                    "now_cost": 40 + (index % 3) * 5,
                    "status": "a",
                    "ep_next": str(ep_next),
                    "chance_of_playing_next_round": None,
                }
            )
            player_id += 1
    elements.append(
        {
            "id": 999,
            "code": 199_999,
            "web_name": "Unavailable Player",
            "element_type": 3,
            "team": 1,
            "now_cost": 45,
            "status": "i",
            "ep_next": "9.0",
            "chance_of_playing_next_round": 0,
        }
    )
    return {
        "events": [{"id": 1, "deadline_time": DEADLINE}],
        "elements": elements,
        "teams": [
            {"id": index, "name": f"Team {index}", "code": index}
            for index in range(1, 11)
        ],
    }


def _policy(path: Path) -> Path:
    value = json.loads(
        (REPO / "control" / "policies" / "initial-squad-2026-27.json").read_text(
            encoding="utf-8"
        )
    )
    value["policy_version"] = "test-v1"
    value["search"].update(
        {
            "beam_width": 120,
            "candidate_limit_per_position": 12,
            "cheapest_per_position": 4,
            "retained_squads": 3,
        }
    )
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _capture(
    tmp_path: Path,
    *,
    checkpoint_id: str,
    observed_at: str,
    predecessor_checkpoint_hash: str | None = None,
    boost_player_id: int | None = None,
    goalkeepers: int = 4,
) -> Path:
    root = tmp_path / "snapshots"
    manifest = capture_preseason_snapshot(
        season="2026-27",
        checkpoint_id=checkpoint_id,
        deadline=DEADLINE,
        output_root=root,
        observed_at=observed_at,
        bootstrap_body=json.dumps(
            _bootstrap(boost_player_id=boost_player_id, goalkeepers=goalkeepers),
            sort_keys=True,
        ).encode("utf-8"),
        fixtures_body=b"[]",
        index_manifest_path=tmp_path / "index.json",
        predecessor_checkpoint_hash=predecessor_checkpoint_hash,
        update_index=False,
    )
    path = root / checkpoint_id / "manifest.json"
    assert json.loads(path.read_text(encoding="utf-8"))["content_sha256"] == manifest[
        "content_sha256"
    ]
    return path


def _run(
    tmp_path: Path,
    manifest_path: Path,
    policy_path: Path,
) -> dict:
    return run_initial_squad_checkpoint(
        manifest_path=manifest_path,
        output_root=tmp_path / "reports",
        policy_path=policy_path,
    )


def _reseal_manifest(path: Path, value: dict) -> None:
    value["content_sha256"] = artifact_hash(value)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_degraded_checkpoint_produces_a_legal_advisory_packet_and_named_gaps(
    tmp_path: Path,
) -> None:
    manifest_path = _capture(
        tmp_path,
        checkpoint_id="weekly-2026-07-30",
        observed_at="2026-07-30T08:00:00Z",
    )
    checkpoint = _run(tmp_path, manifest_path, _policy(tmp_path / "policy.json"))

    report_dir = tmp_path / "reports" / "weekly-2026-07-30"
    recommendation = json.loads(
        (report_dir / "recommendation.json").read_text(encoding="utf-8")
    )
    proposal = recommendation["selection"]["selection"]["proposal"]
    assert checkpoint["account_writes"] is False
    assert checkpoint["approval_status"] == "blocked"
    assert len(proposal["squad_player_ids"]) == 15
    assert proposal["validation"]["squad"]["ok"] is True
    assert proposal["validation"]["first_lineup"]["ok"] is True
    assert len(proposal["weekly_plans"][0]["lineup"]["starting_xi"]) == 11
    assert len(proposal["weekly_plans"][0]["lineup"]["bench"]) == 4
    assert recommendation["source_families"]["licensed_odds"]["state"] == "unavailable"
    assert "licensed_odds" in json.loads(
        (report_dir / "input-packet.json").read_text(encoding="utf-8")
    )["fallbacks"]
    assert "forecast_baseline_not_approval_eligible" in recommendation["selection"][
        "approval_gate"
    ]["blockers"]
    assert (report_dir / "diff.md").is_file()


def test_same_checkpoint_rerun_is_byte_identical(tmp_path: Path) -> None:
    manifest_path = _capture(
        tmp_path,
        checkpoint_id="weekly-2026-07-30",
        observed_at="2026-07-30T08:00:00Z",
    )
    policy_path = _policy(tmp_path / "policy.json")
    first = _run(tmp_path, manifest_path, policy_path)
    report_dir = tmp_path / "reports" / "weekly-2026-07-30"
    before = {path.name: path.read_bytes() for path in report_dir.iterdir() if path.is_file()}
    second = _run(tmp_path, manifest_path, policy_path)
    after = {path.name: path.read_bytes() for path in report_dir.iterdir() if path.is_file()}
    assert first == second
    assert before == after


def test_successive_checkpoint_reports_a_hash_bound_machine_and_human_diff(
    tmp_path: Path,
) -> None:
    policy_path = _policy(tmp_path / "policy.json")
    first_manifest_path = _capture(
        tmp_path,
        checkpoint_id="weekly-2026-07-30",
        observed_at="2026-07-30T08:00:00Z",
    )
    first = _run(tmp_path, first_manifest_path, policy_path)
    second_manifest_path = _capture(
        tmp_path,
        checkpoint_id="weekly-2026-08-01",
        observed_at="2026-08-01T08:00:00Z",
        predecessor_checkpoint_hash=first["input_manifest"]["content_sha256"],
        boost_player_id=15,
    )
    second = _run(tmp_path, second_manifest_path, policy_path)
    report_dir = tmp_path / "reports" / "weekly-2026-08-01"
    diff = json.loads((report_dir / "diff.json").read_text(encoding="utf-8"))

    assert second["predecessor"]["checkpoint_id"] == "weekly-2026-07-30"
    assert diff["status"] == "compared"
    assert diff["predecessor"]["manifest_sha256"] == first["input_manifest"][
        "content_sha256"
    ]
    assert "Compared with `weekly-2026-07-30`." in (report_dir / "diff.md").read_text(
        encoding="utf-8"
    )


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("bad_hash", "content hash mismatch"),
        ("late_checkpoint", "observed or available after"),
        ("late_family", "official_bootstrap available_at is after decision cutoff"),
        ("unknown_ruleset", "ruleset hash does not match"),
    ],
)
def test_manifest_validation_fails_closed(
    tmp_path: Path,
    mutation: str,
    message: str,
) -> None:
    manifest_path = _capture(
        tmp_path,
        checkpoint_id="weekly-2026-07-30",
        observed_at="2026-07-30T08:00:00Z",
    )
    value = json.loads(manifest_path.read_text(encoding="utf-8"))
    if mutation == "bad_hash":
        value["content_sha256"] = "0" * 64
        manifest_path.write_text(
            json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    elif mutation == "late_checkpoint":
        value["observed_at"] = DEADLINE
        value["available_at"] = DEADLINE
        _reseal_manifest(manifest_path, value)
    elif mutation == "late_family":
        value["families"]["official_bootstrap"]["available_at"] = DEADLINE
        _reseal_manifest(manifest_path, value)
    else:
        value["ruleset_sha256"] = "f" * 64
        _reseal_manifest(manifest_path, value)

    with pytest.raises(InitialSquadCheckpointError, match=message):
        verify_preseason_manifest(manifest_path)


def test_illegal_candidate_pool_and_different_checkpoint_overwrite_fail_closed(
    tmp_path: Path,
) -> None:
    policy_path = _policy(tmp_path / "policy.json")
    illegal_manifest = _capture(
        tmp_path,
        checkpoint_id="weekly-2026-07-30",
        observed_at="2026-07-30T08:00:00Z",
        goalkeepers=1,
    )
    with pytest.raises(InitialSquadCheckpointError, match="Not enough available GKP"):
        _run(tmp_path, illegal_manifest, policy_path)

    valid_manifest = _capture(
        tmp_path,
        checkpoint_id="weekly-2026-08-01",
        observed_at="2026-08-01T08:00:00Z",
    )
    _run(tmp_path, valid_manifest, policy_path)
    changed_policy = deepcopy(json.loads(policy_path.read_text(encoding="utf-8")))
    changed_policy["policy_version"] = "test-v2"
    changed_path = tmp_path / "changed-policy.json"
    changed_path.write_text(
        json.dumps(changed_policy, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    with pytest.raises(InitialSquadCheckpointConflict, match="different content"):
        _run(tmp_path, valid_manifest, changed_path)
