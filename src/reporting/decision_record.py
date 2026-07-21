"""Render a Gameweek Decision Record (plan Sections 3.1 and 16)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def build_decision_record(payload: dict[str, Any]) -> dict[str, Any]:
    required = [
        "gameweek",
        "decision_cutoff",
        "deadline",
        "ruleset_id",
        "recommendation",
        "validation",
    ]
    missing = [k for k in required if k not in payload]
    if missing:
        raise ValueError(f"Decision record missing fields: {missing}")
    return payload


def render_text(record: dict[str, Any]) -> str:
    rec = record["recommendation"]
    lineup = rec.get("lineup", {})
    xi_names = [p.get("web_name", p["player_id"]) for p in lineup.get("starting_xi", [])]
    lines = [
        f"Gameweek: {record['gameweek']}",
        f"Decision cutoff: {record['decision_cutoff']}",
        f"Deadline: {record['deadline']}",
        f"Ruleset: {record['ruleset_id']}",
        f"Data quality: {record.get('data_quality', 'n/a')}",
        "",
        "Recommendation:",
        f"  Strategy: {rec.get('strategy')}",
        f"  Captain: {rec.get('captain_name', lineup.get('captain_id'))}",
        f"  Vice-captain: {rec.get('vice_captain_name', lineup.get('vice_captain_id'))}",
        f"  Starting XI: {', '.join(xi_names)}",
        f"  Expected XI points (crude): {lineup.get('expected_xi_points')}",
        "",
        f"Expected advantage over current setup: {record.get('expected_advantage', 'n/a')}",
        f"Confidence: {record.get('confidence', 'Low — walking skeleton')}",
        f"Principal uncertainty: {record.get('principal_uncertainty', 'Crude projections')}",
        "",
        "Validation:",
        f"  Squad: {'passed' if record['validation'].get('squad', {}).get('ok') else 'FAILED'}",
        f"  Line-up: {'passed' if record['validation'].get('lineup', {}).get('ok') else 'FAILED'}",
        "",
        f"Approval: {record.get('approval', 'Pending human')}",
        f"Execution: {record.get('execution', 'Manual in initial phase')}",
    ]
    return "\n".join(lines) + "\n"


def write_decision_record(record: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    text_path = path.with_suffix(".txt")
    text_path.write_text(render_text(record), encoding="utf-8")
