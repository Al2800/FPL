"""Render and validate a Gameweek Decision Record (plan Sections 3.1 and 16)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover
    Draft202012Validator = None  # type: ignore

REPO = Path(__file__).resolve().parents[2]
SCHEMA_REL = "decisions/gameweek_decision_records.json"

# Section 3.1 coverage checklist (human-readable → schema fields)
SECTION_31_FIELDS = {
    "data_cutoff_and_deadline": ["decision_cutoff", "deadline"],
    "manager_state": ["manager_state"],
    "projections": ["projections_summary"],
    "candidate_strategies": ["candidate_plans"],
    "recommended_xi_captain_bench": ["recommendation"],
    "optional_chip": ["recommendation"],
    "expected_gain_vs_do_nothing": ["baseline_comparison"],
    "alternative_plans": ["alternatives"],
    "evidence": ["evidence"],
    "rules_validation": ["validation"],
    "human_decision": ["approval"],
    "outcome_and_retrospective": ["outcome", "retrospective"],
}


def _load_gdr_schema() -> dict[str, Any]:
    schemas = REPO / "control" / "schemas"
    schema = json.loads((schemas / SCHEMA_REL).read_text(encoding="utf-8"))
    defs = json.loads((schemas / "_defs.json").read_text(encoding="utf-8"))["$defs"]

    def rewrite(obj: Any) -> Any:
        if isinstance(obj, dict):
            if set(obj.keys()) == {"$ref"} and "/$defs/" in obj["$ref"]:
                return defs[obj["$ref"].split("/$defs/")[-1]]
            return {k: rewrite(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [rewrite(v) for v in obj]
        return obj

    return rewrite(schema)


def validate_decision_record(record: dict[str, Any]) -> None:
    if Draft202012Validator is None:
        raise RuntimeError("jsonschema is required")
    Draft202012Validator(_load_gdr_schema()).validate(record)


def section_31_coverage(record: dict[str, Any]) -> dict[str, bool]:
    """Return whether each Section 3.1 element is present on the record."""
    out: dict[str, bool] = {}
    for label, keys in SECTION_31_FIELDS.items():
        if label == "outcome_and_retrospective":
            # Present as keys (may be null until finalisation)
            out[label] = all(k in record for k in keys)
        elif label == "optional_chip":
            out[label] = "recommendation" in record and "chip" in (
                record.get("recommendation") or {}
            )
        else:
            out[label] = all(k in record and record[k] is not None for k in keys)
    return out


def build_decision_record(payload: dict[str, Any], *, validate: bool = False) -> dict[str, Any]:
    """Assemble a GDR. Set validate=True for full schema check (WP-09 records)."""
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
    record = dict(payload)
    # Defaults so Section 3.1 keys exist even for the walking skeleton
    record.setdefault("record_id", f"gdr_gw{record['gameweek']}")
    record.setdefault("season", record.get("season") or "unknown")
    record.setdefault(
        "manager_state",
        record.get("manager_state")
        or {"bank": 0.0, "free_transfers": 1, "chips_available": [], "squad_player_ids": []},
    )
    if "squad_player_ids" not in record["manager_state"] and record.get("squad_player_ids"):
        record["manager_state"]["squad_player_ids"] = record["squad_player_ids"]
    record.setdefault(
        "baseline_comparison",
        {
            "do_nothing_objective": 0.0,
            "recommended_objective": 0.0,
            "expected_advantage": 0.0,
            "notes": "Not computed",
        },
    )
    record.setdefault("candidate_plans", [])
    record.setdefault("alternatives", {"conservative": None, "aggressive": None})
    record.setdefault(
        "evidence",
        {
            "supporting_claim_ids": [],
            "conflicting_claim_ids": [],
            "conflict_ids": [],
            "proposed_adjustment_ids": [],
        },
    )
    record.setdefault("approval", {"status": "pending"})
    record.setdefault("execution", {"mode": "manual"})
    record.setdefault("outcome", None)
    record.setdefault("retrospective", None)
    record.setdefault("projections_summary", {})
    if "chip" not in record["recommendation"]:
        record["recommendation"]["chip"] = None
    if validate:
        # Ensure timestamps/provenance for schema
        if "observed_at" not in record or "available_at" not in record or "provenance" not in record:
            raise ValueError("Validated GDR requires observed_at, available_at, provenance")
        validate_decision_record(record)
    return record


def render_text(record: dict[str, Any]) -> str:
    rec = record["recommendation"]
    lineup = rec.get("lineup", {})
    xi = lineup.get("starting_xi") or []
    if xi and isinstance(xi[0], dict):
        xi_names = [p.get("web_name", p["player_id"]) for p in xi]
    else:
        xi_names = [str(x) for x in (lineup.get("starting_xi_ids") or [])]
    baseline = record.get("baseline_comparison") or {}
    approval = record.get("approval")
    if isinstance(approval, dict):
        approval_s = approval.get("status", "n/a")
    else:
        approval_s = approval if approval is not None else "n/a"
    execution = record.get("execution")
    if isinstance(execution, dict):
        execution_s = execution.get("mode", "n/a")
    else:
        execution_s = execution if execution is not None else "n/a"
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
        f"  Expected XI points: {lineup.get('expected_xi_points')}",
        "",
        f"Expected advantage over do-nothing: {baseline.get('expected_advantage', record.get('expected_advantage', 'n/a'))}",
        f"Confidence: {record.get('confidence', 'n/a')}",
        f"Principal uncertainty: {record.get('principal_uncertainty', 'n/a')}",
        "",
        "Validation:",
        f"  Squad: {'passed' if record['validation'].get('squad', {}).get('ok') else 'FAILED'}",
        f"  Line-up: {'passed' if record['validation'].get('lineup', {}).get('ok') else 'FAILED'}",
        "",
        f"Approval: {approval_s}",
        f"Execution: {execution_s}",
    ]
    if record.get("retrospective"):
        lines.extend(
            [
                "",
                "Retrospective:",
                f"  {record['retrospective'].get('process_notes', '')}",
            ]
        )
    return "\n".join(lines) + "\n"


def write_decision_record(record: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    text_path = path.with_suffix(".txt")
    text_path.write_text(render_text(record), encoding="utf-8")
