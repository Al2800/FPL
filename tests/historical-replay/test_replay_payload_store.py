from __future__ import annotations

import json
from pathlib import Path

from src.optimisation.io import fingerprint
from src.orchestration.replay_payload_store import (
    is_payload_ref,
    resolve_reviewed_payload,
    store_payload_once,
    write_arm_payload_ref,
    write_store_manifest,
)


def test_divergent_solver_inputs_receive_distinct_payload_files(
    tmp_path: Path,
) -> None:
    setup = tmp_path / "setup"
    arm_a = setup / "arms" / "forecast_optimizer"
    arm_b = setup / "arms" / "naive_baseline"
    arm_a.mkdir(parents=True)
    arm_b.mkdir(parents=True)

    input_a = {"gameweek": 4, "bank": 1.0, "free_transfers": 2}
    input_b = {"gameweek": 4, "bank": 1.0, "free_transfers": 3}
    hash_a = store_payload_once(setup, "solver_input", input_a)
    hash_b = store_payload_once(setup, "solver_input", input_b)
    write_arm_payload_ref(arm_a, "solver_input", hash_a)
    write_arm_payload_ref(arm_b, "solver_input", hash_b)
    manifest = write_store_manifest(setup, input_hashes={hash_a, hash_b}, output_hashes=set())

    assert hash_a != hash_b
    assert manifest["unique_solver_inputs"] == 2
    assert len(list((setup / "payloads" / "solver-input").glob("*.json"))) == 2
    assert resolve_reviewed_payload(arm_a, "solver_input") == input_a
    assert resolve_reviewed_payload(arm_b, "solver_input") == input_b
    assert is_payload_ref(
        json.loads((arm_a / "reviewed-engine-input.json").read_text())
    )
    assert fingerprint(resolve_reviewed_payload(arm_a, "solver_input")) == hash_a
