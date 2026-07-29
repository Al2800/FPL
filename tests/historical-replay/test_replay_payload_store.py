from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.optimisation.io import fingerprint
from src.orchestration.replay_payload_store import (
    ReplayPayloadStoreError,
    build_payload_ref,
    is_payload_ref,
    load_reviewed_payload,
    resolve_reviewed_payload,
    store_payload_once,
    validate_payload_digest,
    write_arm_payload_ref,
    write_store_manifest,
)


REPO = Path(__file__).resolve().parents[2]
GW4 = REPO / "reports/benchmarks/2025-26/gw-04"
GW3 = REPO / "reports/benchmarks/2025-26/gw-03"
ARMS = (
    "forecast_optimizer",
    "naive_baseline",
    "human_decision",
    "evidence_agent",
    "evidence_challenger",
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
    manifest = write_store_manifest(
        setup, input_hashes={hash_a, hash_b}, output_hashes=set()
    )

    assert hash_a != hash_b
    assert manifest["unique_solver_inputs"] == 2
    assert len(list((setup / "payloads" / "solver-input").glob("*.json"))) == 2
    assert resolve_reviewed_payload(arm_a, "solver_input") == input_a
    assert resolve_reviewed_payload(arm_b, "solver_input") == input_b
    ref = json.loads((arm_a / "reviewed-engine-input.json").read_text())
    assert is_payload_ref(ref)
    assert ref["payload_sha256"] == hash_a
    assert "content_sha256" in ref
    assert ref["content_sha256"] != hash_a
    assert fingerprint(resolve_reviewed_payload(arm_a, "solver_input")) == hash_a


def test_payload_ref_rejects_kind_mismatch_and_path_like_digest(
    tmp_path: Path,
) -> None:
    setup = tmp_path / "setup"
    arm = setup / "arms" / "forecast_optimizer"
    arm.mkdir(parents=True)
    payload = {"gameweek": 4, "bank": 2.0}
    digest = store_payload_once(setup, "solver_input", payload)
    write_store_manifest(setup, input_hashes={digest}, output_hashes=set())

    bad_kind = build_payload_ref("solver_output", digest)
    (arm / "reviewed-engine-input.json").write_text(
        json.dumps(bad_kind, indent=2, sort_keys=True) + "\n"
    )
    with pytest.raises(ReplayPayloadStoreError, match="kind mismatch"):
        resolve_reviewed_payload(arm, "solver_input")

    with pytest.raises(ReplayPayloadStoreError, match="lowercase 64-hex"):
        validate_payload_digest("../etc/passwd")
    with pytest.raises(ReplayPayloadStoreError, match="path components"):
        validate_payload_digest("AB" + "a" * 62)


def test_payload_ref_requires_manifest_membership(tmp_path: Path) -> None:
    setup = tmp_path / "setup"
    arm = setup / "arms" / "forecast_optimizer"
    arm.mkdir(parents=True)
    payload = {"gameweek": 4, "bank": 3.0}
    digest = store_payload_once(setup, "solver_input", payload)
    write_arm_payload_ref(arm, "solver_input", digest)
    # Manifest lists a different digest only.
    other = store_payload_once(setup, "solver_input", {"gameweek": 4, "bank": 9.0})
    write_store_manifest(setup, input_hashes={other}, output_hashes=set())
    with pytest.raises(ReplayPayloadStoreError, match="not listed in store manifest"):
        resolve_reviewed_payload(arm, "solver_input")


def test_legacy_content_sha256_target_ref_is_rejected(tmp_path: Path) -> None:
    setup = tmp_path / "setup"
    arm = setup / "arms" / "forecast_optimizer"
    arm.mkdir(parents=True)
    payload = {"gameweek": 4, "bank": 4.0}
    digest = store_payload_once(setup, "solver_input", payload)
    write_store_manifest(setup, input_hashes={digest}, output_hashes=set())
    legacy = {
        "schema_version": "1.0",
        "kind": "solver_input_ref",
        "content_sha256": digest,
    }
    (arm / "reviewed-engine-input.json").write_text(
        json.dumps(legacy, indent=2, sort_keys=True) + "\n"
    )
    with pytest.raises(ReplayPayloadStoreError, match="payload_sha256"):
        resolve_reviewed_payload(arm, "solver_input")


@pytest.mark.skipif(not GW4.exists(), reason="GW4 sealed setup absent")
def test_gw4_cross_consumer_payload_resolution_matrix() -> None:
    """Every migrated consumer entrypoint must resolve GW4 refs to full payloads."""

    arm = GW4 / "setup/arms/forecast_optimizer"
    via_arm = resolve_reviewed_payload(arm, "solver_input")
    via_path = load_reviewed_payload(
        arm / "reviewed-engine-input.json", expected_kind="solver_input"
    )
    via_output = load_reviewed_payload(
        arm / "reviewed-engine-output.json", expected_kind="solver_output"
    )
    assert via_arm == via_path
    assert "players" in via_arm and len(via_arm["players"]) > 0
    assert "selected" in via_output

    # Central loader is what captain/challenger/chip/contingency/transfer/
    # agent_fork/evidence_fork/multiweek paths now share.
    consumers = {
        "captain_counterfactual": via_arm,
        "challenger_matrix": via_arm,
        "chip_counterfactual": via_arm,
        "squad_contingency": via_arm,
        "transfer_counterfactual": via_arm,
        "agent_fork_adapter": via_arm,
        "evidence_fork": via_arm,
        "multiweek_challenger": via_arm,
    }
    for name, payload in consumers.items():
        assert payload["gameweek"] == 4, name
        assert "players" in payload, name

    for arm_name in ARMS:
        arm_dir = GW4 / "setup/arms" / arm_name
        ref = json.loads((arm_dir / "reviewed-engine-input.json").read_text())
        assert is_payload_ref(ref)
        assert ref["payload_sha256"] != ref["content_sha256"]
        resolved = resolve_reviewed_payload(arm_dir, "solver_input")
        assert fingerprint(resolved) == ref["payload_sha256"]


@pytest.mark.skipif(not GW3.exists(), reason="GW3 sealed setup absent")
def test_gw3_inline_payloads_still_load_via_central_loader() -> None:
    arm = GW3 / "setup/arms/forecast_optimizer"
    inline = json.loads((arm / "reviewed-engine-input.json").read_text())
    assert not is_payload_ref(inline)
    loaded = load_reviewed_payload(
        arm / "reviewed-engine-input.json", expected_kind="solver_input"
    )
    assert loaded == inline
    assert "players" in loaded
