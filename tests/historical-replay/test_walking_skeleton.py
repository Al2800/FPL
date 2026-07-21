"""Walking skeleton reproducibility and end-to-end acceptance."""

from pathlib import Path

from src.orchestration.walking_skeleton import run_skeleton

REPO = Path(__file__).resolve().parents[2]
FIXTURE = REPO / "evals" / "golden-cases" / "skeleton-gw3-fixture.json"


def test_skeleton_reproduces_identical_hash(tmp_path):
    out1 = tmp_path / "run1"
    out2 = tmp_path / "run2"
    r1 = run_skeleton(FIXTURE, out1)
    r2 = run_skeleton(FIXTURE, out2)
    assert r1["repro_hash"] == r2["repro_hash"]
    assert r1["validation"]["squad"]["ok"] is True
    assert r1["validation"]["lineup"]["ok"] is True
    assert (out1 / "decision-record.json").exists()
    assert (out1 / "decision-record.txt").exists()
    assert (out1 / "projections.parquet").exists()


def test_skeleton_selects_captain_from_starting_xi(tmp_path):
    record = run_skeleton(FIXTURE, tmp_path / "run")
    lineup = record["recommendation"]["lineup"]
    xi_ids = {p["player_id"] for p in lineup["starting_xi"]}
    assert lineup["captain_id"] in xi_ids
    assert lineup["vice_captain_id"] in xi_ids
    assert lineup["captain_id"] != lineup["vice_captain_id"]
