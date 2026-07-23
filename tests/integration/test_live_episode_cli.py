"""Operator CLI contracts for immutable live-shadow episode construction."""

from __future__ import annotations

import json
from pathlib import Path

from scripts import build_live_episode as cli
from src.orchestration.episode_builder import LiveEpisodeError


def test_cli_passes_local_governed_inputs_and_prints_safe_index(
    monkeypatch, tmp_path: Path, capsys
):
    captured: dict = {}

    def fake_build(**kwargs):
        captured.update(kwargs)
        return {
            "episode_id": "live-shadow:2025-26:gw01:manager-test",
            "observed_episode_sha256": "a" * 64,
        }

    monkeypatch.setattr(cli, "build_live_episode", fake_build)
    exit_code = cli.main(
        [
            "--capture-summary",
            str(tmp_path / "capture-summary.json"),
            "--manager-state",
            str(tmp_path / "manager.json"),
            "--rules",
            str(tmp_path / "rules.yaml"),
            "--out",
            str(tmp_path / "episode"),
            "--code-commit",
            "b" * 40,
        ]
    )

    assert exit_code == 0
    assert captured["capture_summary_path"] == tmp_path / "capture-summary.json"
    assert captured["manager_state_path"] == tmp_path / "manager.json"
    assert captured["rules_path"] == tmp_path / "rules.yaml"
    assert captured["out_dir"] == tmp_path / "episode"
    assert captured["code_commit"] == "b" * 40
    assert captured["compatibility_policy"] == []
    assert json.loads(capsys.readouterr().out)["observed_episode_sha256"] == "a" * 64


def test_cli_refuses_invalid_build_without_traceback(monkeypatch, tmp_path: Path, capsys):
    def refuse(**_kwargs):
        raise LiveEpisodeError("capture is after cutoff")

    monkeypatch.setattr(cli, "build_live_episode", refuse)
    exit_code = cli.main(
        [
            "--capture-summary",
            str(tmp_path / "capture-summary.json"),
            "--manager-state",
            str(tmp_path / "manager.json"),
            "--out",
            str(tmp_path / "episode"),
        ]
    )

    output = capsys.readouterr()
    assert exit_code == 2
    assert output.out == ""
    assert output.err == "refused: capture is after cutoff\n"
