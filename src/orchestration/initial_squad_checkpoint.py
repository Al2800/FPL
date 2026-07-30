"""Hash-bound, advisory-only initial-squad checkpoint orchestration.

This module turns one immutable preseason manifest into a reproducible
initial-15 selection artifact.  It deliberately owns no HTTP, browser, or FPL
account interaction: collection is performed by ``preseason_snapshot`` and
selection by the existing deterministic optimiser.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from src.forecasting.live_faithful import artifact_hash
from src.optimisation.initial_squad import (
    InitialSquadError,
    initial_squad_hash,
    score_declared_initial_squad,
    validate_initial_squad_packet,
)
from src.orchestration.evidence_checkpoint_runner import (
    EvidenceCheckpointConflict,
    _exclusive_lock,
    _write_immutable_json,
)
from src.orchestration.live_seed_selection import run_live_seed_selection
from src.orchestration.preseason_snapshot import (
    artifact_hash as preseason_artifact_hash,
    validate_checkpoint_id,
)
from src.scoring.rules_loader import load_rules, ruleset_sha256


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "reports" / "live" / "2026-27" / "initial-squad"
DEFAULT_POLICY_PATH = REPO_ROOT / "control" / "policies" / "initial-squad-2026-27.json"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_POSITIONS = {1: "GKP", 2: "DEF", 3: "MID", 4: "FWD"}
_BASELINE_MODEL = "official-ep-next-flat-horizon-baseline-v1"


class InitialSquadCheckpointError(ValueError):
    """Raised when a checkpoint cannot safely produce an advisory artifact."""


class InitialSquadCheckpointConflict(InitialSquadCheckpointError):
    """Raised when an immutable checkpoint output already differs."""


def _canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")


def _timestamp(value: Any, field: str) -> tuple[str, datetime]:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise InitialSquadCheckpointError(
            f"{field} must be an ISO-8601 timestamp"
        ) from exc
    if parsed.tzinfo is None:
        raise InitialSquadCheckpointError(f"{field} must include a timezone")
    utc = parsed.astimezone(timezone.utc)
    return utc.isoformat().replace("+00:00", "Z"), utc


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InitialSquadCheckpointError(f"Cannot read {label}: {path}") from exc
    if not isinstance(value, Mapping):
        raise InitialSquadCheckpointError(f"{label} must be a JSON object")
    return deepcopy(dict(value))


def _read_json_list(path: Path, label: str) -> list[Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InitialSquadCheckpointError(f"Cannot read {label}: {path}") from exc
    if not isinstance(value, list):
        raise InitialSquadCheckpointError(f"{label} must be a JSON list")
    return deepcopy(value)


def _require_sha256(value: Any, field: str) -> str:
    digest = str(value)
    if not _SHA256.fullmatch(digest):
        raise InitialSquadCheckpointError(f"{field} must be a lower-case SHA-256")
    return digest


def _resolve_bound_artifact(
    manifest_path: Path,
    path_value: Any,
    *,
    family_id: str,
) -> Path:
    if not isinstance(path_value, str) or not path_value:
        raise InitialSquadCheckpointError(
            f"Manifest family {family_id} has no artifact path"
        )
    candidate_path = Path(path_value)
    if candidate_path.is_absolute():
        candidate = candidate_path.resolve()
    else:
        checkpoint_root = manifest_path.parent.resolve()
        candidate = (checkpoint_root / candidate_path).resolve()
        if candidate != checkpoint_root and checkpoint_root not in candidate.parents:
            raise InitialSquadCheckpointError(
                f"Manifest family {family_id} artifact escapes checkpoint root"
            )
    if not candidate.is_file():
        raise InitialSquadCheckpointError(
            f"Manifest family {family_id} artifact is missing: {candidate}"
        )
    return candidate


def _verify_family(
    manifest_path: Path,
    family_id: str,
    family: Mapping[str, Any],
    *,
    required: bool,
) -> tuple[Path, str] | None:
    status = str(family.get("status", ""))
    if required and status != "admitted":
        raise InitialSquadCheckpointError(
            f"Mandatory manifest family is not admitted: {family_id}"
        )
    if status != "admitted":
        return None
    expected = _require_sha256(
        family.get("artifact_sha256"), f"families.{family_id}.artifact_sha256"
    )
    path = _resolve_bound_artifact(
        manifest_path, family.get("artifact_path"), family_id=family_id
    )
    actual = _sha256_file(path)
    if actual != expected:
        raise InitialSquadCheckpointError(
            f"Manifest family {family_id} artifact hash mismatch"
        )
    return path, expected


def _family_states(
    manifest_path: Path,
    families: Mapping[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[str, Path]]:
    states: dict[str, dict[str, Any]] = {}
    paths: dict[str, Path] = {}
    for family_id in sorted(families):
        source = families[family_id]
        if not isinstance(source, Mapping):
            raise InitialSquadCheckpointError(
                f"Manifest family {family_id} must be an object"
            )
        status = str(source.get("status", ""))
        mandatory = bool(source.get("mandatory", False))
        bound = _verify_family(
            manifest_path,
            family_id,
            source,
            required=mandatory,
        )
        if bound is not None:
            path, digest = bound
            paths[family_id] = path
            state = "admitted"
        else:
            digest = source.get("artifact_sha256")
            path = None
            state = "unavailable"
        reasons = source.get("reasons", [])
        if not isinstance(reasons, list):
            raise InitialSquadCheckpointError(
                f"Manifest family {family_id} reasons must be a list"
            )
        states[family_id] = {
            "state": state,
            "manifest_status": status,
            "mandatory": mandatory,
            "source_id": str(source.get("source_id", "unknown")),
            "artifact_sha256": digest,
            "artifact_path": str(path) if path is not None else None,
            "observed_at": source.get("observed_at"),
            "available_at": source.get("available_at"),
            "reasons": [str(reason) for reason in reasons],
        }
    return states, paths


def verify_preseason_manifest(manifest_path: Path) -> dict[str, Any]:
    """Load a self-hashed preorder checkpoint and verify all bound bytes."""

    path = manifest_path.resolve()
    manifest = _read_json_object(path, "preseason manifest")
    expected_hash = _require_sha256(manifest.get("content_sha256"), "content_sha256")
    if preseason_artifact_hash(manifest) != expected_hash:
        raise InitialSquadCheckpointError("Preseason manifest content hash mismatch")

    required = {
        "schema_version",
        "season",
        "checkpoint_id",
        "observed_at",
        "available_at",
        "deadline",
        "families",
        "ruleset_sha256",
        "account_writes",
    }
    missing = sorted(required - set(manifest))
    if missing:
        raise InitialSquadCheckpointError(
            f"Preseason manifest missing fields: {', '.join(missing)}"
        )
    if manifest["season"] != "2026-27":
        raise InitialSquadCheckpointError("Only season 2026-27 is supported")
    deadline_text, deadline = _timestamp(manifest["deadline"], "manifest.deadline")
    checkpoint_id = validate_checkpoint_id(
        str(manifest["checkpoint_id"]), deadline=deadline_text
    )
    observed_text, observed = _timestamp(
        manifest["observed_at"], "manifest.observed_at"
    )
    available_text, available = _timestamp(
        manifest["available_at"], "manifest.available_at"
    )
    if observed >= deadline or available >= deadline:
        raise InitialSquadCheckpointError(
            "Preseason manifest was observed or available after its decision cutoff"
        )
    if available > observed:
        raise InitialSquadCheckpointError(
            "Preseason manifest available_at is after observed_at"
        )
    if manifest.get("account_writes") is not False:
        raise InitialSquadCheckpointError("Preseason manifest must forbid account writes")
    families = manifest["families"]
    if not isinstance(families, Mapping):
        raise InitialSquadCheckpointError("Preseason manifest families must be an object")
    for family_id in ("official_bootstrap", "official_fixtures", "ruleset"):
        if family_id not in families:
            raise InitialSquadCheckpointError(
                f"Preseason manifest missing mandatory family: {family_id}"
            )

    family_states, paths = _family_states(path, families)
    for family_id, family in family_states.items():
        if family["state"] != "admitted":
            continue
        for field in ("observed_at", "available_at"):
            value = family.get(field)
            if value is None:
                continue
            _, family_time = _timestamp(value, f"families.{family_id}.{field}")
            if family_time >= deadline:
                raise InitialSquadCheckpointError(
                    f"Manifest family {family_id} {field} is after decision cutoff"
                )
            if family_time > observed:
                raise InitialSquadCheckpointError(
                    f"Manifest family {family_id} {field} is after checkpoint observation"
                )
    for family_id in ("official_bootstrap", "official_fixtures", "ruleset"):
        if family_states[family_id]["state"] != "admitted":
            raise InitialSquadCheckpointError(
                f"Mandatory family unavailable: {family_id}"
            )
    rules_hash = _require_sha256(manifest["ruleset_sha256"], "ruleset_sha256")
    if family_states["ruleset"]["artifact_sha256"] != rules_hash:
        raise InitialSquadCheckpointError("Manifest ruleset hash does not match ruleset family")

    bootstrap = _read_json_object(paths["official_bootstrap"], "official bootstrap")
    fixtures = _read_json_list(paths["official_fixtures"], "official fixtures")
    events = bootstrap.get("events")
    if not isinstance(events, list):
        raise InitialSquadCheckpointError("Official bootstrap events must be a list")
    matching_events = [
        row
        for row in events
        if isinstance(row, Mapping) and int(row.get("id", 0)) == 1
    ]
    if len(matching_events) != 1:
        raise InitialSquadCheckpointError("Official bootstrap must contain exactly one GW1")
    event_deadline, _ = _timestamp(
        matching_events[0].get("deadline_time"), "official GW1 deadline"
    )
    if event_deadline != deadline_text:
        raise InitialSquadCheckpointError(
            "Official GW1 deadline does not match preseason manifest"
        )

    result = {
        "manifest_path": path,
        "manifest": manifest,
        "checkpoint_id": checkpoint_id,
        "observed_at": observed_text,
        "available_at": available_text,
        "deadline": deadline_text,
        "bootstrap": bootstrap,
        "fixtures": fixtures,
        "family_states": family_states,
        "bound_paths": paths,
    }
    return result


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    text = str(value).strip()
    if not text or text == "-":
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0.0 else None


def _start_probability(source: Mapping[str, Any]) -> tuple[float, str]:
    raw = source.get("chance_of_playing_next_round")
    if raw is None or str(raw).strip() == "":
        return 1.0, "official_active_status_without_explicit_chance"
    chance = _number(raw)
    if chance is None or chance > 100.0:
        return 1.0, "official_active_status_invalid_chance_ignored"
    return round(chance / 100.0, 6), "official_chance_of_playing_next_round"


def _source_fallbacks(family_states: Mapping[str, Mapping[str, Any]]) -> dict[str, str]:
    result: dict[str, str] = {}
    for family_id, state in sorted(family_states.items()):
        if state["state"] == "admitted":
            continue
        result[family_id] = (
            "unavailable_at_checkpoint; no evidence-derived numerical adjustment "
            "was emitted into the optimiser packet"
        )
    return result


def build_initial_squad_packet(
    verified: Mapping[str, Any],
    *,
    policy: Mapping[str, Any],
    rules: Mapping[str, Any],
    rules_hash: str,
) -> dict[str, Any]:
    """Build the provisional official-EP baseline packet from verified bytes.

    The production six-week forecast is deliberately not fabricated here.  The
    adapter repeats the one official ``ep_next`` value solely so every
    selection, sealing and review component can be rehearsed before that
    upstream materialisation is available.
    """

    manifest = deepcopy(dict(verified["manifest"]))
    bootstrap = deepcopy(dict(verified["bootstrap"]))
    family_states = deepcopy(dict(verified["family_states"]))
    horizon_size = int(policy["horizon_gameweeks"])
    if horizon_size < 1:
        raise InitialSquadCheckpointError("Initial-squad policy horizon must be positive")
    discounts = [float(value) for value in policy["discount_factors"]]
    if len(discounts) != horizon_size:
        raise InitialSquadCheckpointError(
            "Initial-squad policy discount horizon does not match its configured horizon"
        )

    elements = bootstrap.get("elements")
    if not isinstance(elements, list):
        raise InitialSquadCheckpointError("Official bootstrap elements must be a list")
    candidate_universe: list[dict[str, Any]] = []
    players: list[dict[str, Any]] = []
    exclusions: list[dict[str, Any]] = []
    source_available_at = str(verified["available_at"])
    for raw in sorted(
        (dict(row) for row in elements if isinstance(row, Mapping)),
        key=lambda row: int(row.get("id", 0)),
    ):
        player_id = raw.get("id")
        try:
            identity = str(int(player_id))
            position = _POSITIONS[int(raw.get("element_type"))]
            club_id = str(int(raw.get("team")))
        except (KeyError, TypeError, ValueError):
            exclusions.append(
                {"player_id": str(player_id), "reason": "invalid_official_identity_or_position"}
            )
            continue
        status = str(raw.get("status", ""))
        expected = _number(raw.get("ep_next"))
        cost_tenths = _number(raw.get("now_cost"))
        universe_row = {
            "player_id": identity,
            "web_name": str(raw.get("web_name", "")),
            "position": position,
            "club_id": club_id,
            "official_status": status,
            "official_ep_next": expected,
            "official_now_cost": cost_tenths,
        }
        if status != "a":
            reason = f"official_status_not_available:{status or 'missing'}"
            exclusions.append({"player_id": identity, "reason": reason})
            universe_row["eligible"] = False
            universe_row["exclusion_reason"] = reason
            candidate_universe.append(universe_row)
            continue
        if expected is None:
            reason = "official_ep_next_unavailable"
            exclusions.append({"player_id": identity, "reason": reason})
            universe_row["eligible"] = False
            universe_row["exclusion_reason"] = reason
            candidate_universe.append(universe_row)
            continue
        if cost_tenths is None:
            reason = "official_now_cost_unavailable"
            exclusions.append({"player_id": identity, "reason": reason})
            universe_row["eligible"] = False
            universe_row["exclusion_reason"] = reason
            candidate_universe.append(universe_row)
            continue
        start_probability, availability_basis = _start_probability(raw)
        universe_row.update(
            {
                "eligible": True,
                "availability_basis": availability_basis,
                "start_probability": start_probability,
            }
        )
        candidate_universe.append(universe_row)
        players.append(
            {
                "player_id": identity,
                "web_name": str(raw.get("web_name", "")),
                "position": position,
                "club_id": club_id,
                "now_cost": round(cost_tenths / 10.0, 1),
                "available_at": source_available_at,
                "expected_points": [round(expected, 4)] * horizon_size,
                "start_probability": [start_probability] * horizon_size,
                "uncertainty": [round(1.0 - start_probability, 4)] * horizon_size,
                "status": "a",
            }
        )

    feature_state = {
        "schema_version": "1.0",
        "season": manifest["season"],
        "checkpoint_id": manifest["checkpoint_id"],
        "manifest_sha256": manifest["content_sha256"],
        "official_bootstrap_sha256": family_states["official_bootstrap"][
            "artifact_sha256"
        ],
        "official_fixtures_sha256": family_states["official_fixtures"][
            "artifact_sha256"
        ],
        "projection_strategy": _BASELINE_MODEL,
        "horizon_gameweeks": list(range(1, horizon_size + 1)),
        "source_families": family_states,
    }
    feature_state["content_sha256"] = artifact_hash(feature_state)
    packet: dict[str, Any] = {
        "schema_version": "1.0",
        "decision_id": f"initial-squad:{manifest['season']}:{manifest['checkpoint_id']}",
        "season": manifest["season"],
        "decision_cutoff": verified["deadline"],
        "captured_at": verified["observed_at"],
        "ruleset_id": str(rules["meta"]["ruleset_id"]),
        "ruleset_sha256": rules_hash,
        "feature_state_sha256": feature_state["content_sha256"],
        "forecast_model_version": _BASELINE_MODEL,
        "horizon_gameweeks": list(range(1, horizon_size + 1)),
        "discount_factors": discounts,
        "players": players,
        "forecast_quality": {
            "status": "operational_baseline_only",
            "strategy": _BASELINE_MODEL,
            "reason": (
                "Official ep_next is a one-GW estimate repeated only to rehearse "
                "the checkpoint path; a six-GW live-faithful packet is not bound."
            ),
            "manual_entry_eligible": False,
        },
    }
    validated = validate_initial_squad_packet(
        packet, rules=rules, ruleset_sha256=rules_hash
    )
    return {
        "packet": validated,
        "feature_state": feature_state,
        "candidate_universe": candidate_universe,
        "exclusions": exclusions,
        "source_families": family_states,
        "fallbacks": _source_fallbacks(family_states),
        "forecast_quality": deepcopy(packet["forecast_quality"]),
        "fixture_count": len(verified["fixtures"]),
    }


def _replace_once(values: Sequence[str], old: str, new: str) -> list[str]:
    return [new if value == old else value for value in values]


def _boundary_alternatives(
    packet: Mapping[str, Any],
    *,
    proposal: Mapping[str, Any],
    policy: Mapping[str, Any],
    rules: Mapping[str, Any],
    rules_hash: str,
    per_selected_limit: int = 3,
    screen_limit_per_position: int = 20,
) -> list[dict[str, Any]]:
    """Return legal, one-for-one alternatives near each selected boundary.

    The screen is intentionally bounded and explicitly reported as such.  A
    full rescoring preserves budget, club and lineup legality without claiming
    the candidates are unconstrained player rankings.
    """

    players = [dict(row) for row in packet["players"]]
    by_id = {str(row["player_id"]): row for row in players}
    selected_ids = [str(value) for value in proposal["squad_player_ids"]]
    selected = set(selected_ids)
    by_position: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in players:
        if str(row["player_id"]) not in selected:
            by_position[str(row["position"])].append(row)
    discounts = [float(value) for value in packet["discount_factors"]]

    def rank(row: Mapping[str, Any]) -> tuple[float, float, str]:
        horizon = sum(
            discount * point
            for discount, point in zip(
                discounts, row["expected_points"], strict=True
            )
        )
        return (-float(horizon), float(row["now_cost"]), str(row["player_id"]))

    result: list[dict[str, Any]] = []
    base_objective = float(proposal["objective"])
    for selected_id in sorted(selected):
        source = by_id[selected_id]
        candidates = sorted(by_position[str(source["position"])], key=rank)[
            :screen_limit_per_position
        ]
        scored_rows: list[dict[str, Any]] = []
        for candidate in candidates:
            candidate_id = str(candidate["player_id"])
            trial_ids = _replace_once(selected_ids, selected_id, candidate_id)
            try:
                trial = score_declared_initial_squad(
                    packet,
                    trial_ids,
                    policy=policy,
                    arm_mode="robust",
                    rules=rules,
                    ruleset_sha256=rules_hash,
                )
            except InitialSquadError:
                continue
            delta = round(float(trial["objective"]) - base_objective, 6)
            scored_rows.append(
                {
                    "player_id": candidate_id,
                    "web_name": str(candidate["web_name"]),
                    "now_cost": float(candidate["now_cost"]),
                    "objective": float(trial["objective"]),
                    "objective_delta": delta,
                    "bank": float(trial["bank"]),
                }
            )
        scored_rows.sort(
            key=lambda row: (
                abs(float(row["objective_delta"])),
                -float(row["objective"]),
                str(row["player_id"]),
            )
        )
        result.append(
            {
                "selected_player_id": selected_id,
                "selected_web_name": str(source["web_name"]),
                "position": str(source["position"]),
                "screen_limit_per_position": screen_limit_per_position,
                "legal_one_for_one_alternatives": scored_rows[:per_selected_limit],
            }
        )
    return result


def _read_sealed_output(path: Path, label: str) -> dict[str, Any]:
    value = _read_json_object(path, label)
    expected = _require_sha256(value.get("content_sha256"), f"{label}.content_sha256")
    if artifact_hash(value) != expected:
        raise InitialSquadCheckpointError(f"{label} content hash mismatch: {path}")
    return value


def _predecessor_output(
    output_root: Path,
    predecessor_manifest_hash: Any,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    if predecessor_manifest_hash is None:
        return None, None
    digest = _require_sha256(
        predecessor_manifest_hash, "predecessor_checkpoint_hash"
    )
    if not output_root.exists():
        return None, None
    for checkpoint_path in sorted(output_root.glob("*/checkpoint.json")):
        checkpoint = _read_sealed_output(checkpoint_path, "checkpoint output")
        manifest = checkpoint.get("input_manifest", {})
        if manifest.get("content_sha256") != digest:
            continue
        recommendation_path = checkpoint_path.parent / "recommendation.json"
        if not recommendation_path.is_file():
            raise InitialSquadCheckpointError(
                f"Predecessor checkpoint lacks recommendation artifact: {checkpoint_path}"
            )
        recommendation = _read_sealed_output(
            recommendation_path, "predecessor recommendation"
        )
        if recommendation.get("content_sha256") != checkpoint.get(
            "recommendation_sha256"
        ):
            raise InitialSquadCheckpointError(
                "Predecessor checkpoint recommendation binding mismatch"
            )
        return checkpoint, recommendation
    return None, None


def _proposal_summary(recommendation: Mapping[str, Any]) -> Mapping[str, Any]:
    selection = recommendation.get("selection", {})
    proposal = selection.get("selection", {}).get("proposal")
    if not isinstance(proposal, Mapping):
        raise InitialSquadCheckpointError("Recommendation has no selected proposal")
    return proposal


def _source_family_changes(
    before: Mapping[str, Any], after: Mapping[str, Any]
) -> list[str]:
    changed: list[str] = []
    for family_id in sorted(set(before) | set(after)):
        if before.get(family_id) != after.get(family_id):
            changed.append(family_id)
    return changed


def _recommendation_diff(
    *,
    checkpoint_id: str,
    manifest_hash: str,
    recommendation: Mapping[str, Any],
    predecessor_checkpoint: Mapping[str, Any] | None,
    predecessor_recommendation: Mapping[str, Any] | None,
    source_families: Mapping[str, Any],
) -> dict[str, Any]:
    current = _proposal_summary(recommendation)
    if predecessor_checkpoint is None or predecessor_recommendation is None:
        result = {
            "schema_version": "1.0",
            "status": "no_predecessor_output",
            "checkpoint_id": checkpoint_id,
            "manifest_sha256": manifest_hash,
            "reason": "No prior initial-squad recommendation is bound by the manifest predecessor hash.",
        }
        result["content_sha256"] = artifact_hash(result)
        return result

    previous = _proposal_summary(predecessor_recommendation)
    current_week = current["weekly_plans"][0]["lineup"]
    previous_week = previous["weekly_plans"][0]["lineup"]
    previous_families = predecessor_recommendation.get("source_families", {})
    result = {
        "schema_version": "1.0",
        "status": "compared",
        "checkpoint_id": checkpoint_id,
        "manifest_sha256": manifest_hash,
        "predecessor": {
            "checkpoint_id": predecessor_checkpoint["checkpoint_id"],
            "manifest_sha256": predecessor_checkpoint["input_manifest"][
                "content_sha256"
            ],
            "recommendation_sha256": predecessor_recommendation["content_sha256"],
        },
        "squad": {
            "added": sorted(
                set(current["squad_player_ids"]) - set(previous["squad_player_ids"])
            ),
            "removed": sorted(
                set(previous["squad_player_ids"]) - set(current["squad_player_ids"])
            ),
            "bank_delta": round(float(current["bank"]) - float(previous["bank"]), 4),
            "objective_delta": round(
                float(current["objective"]) - float(previous["objective"]), 6
            ),
        },
        "gw1_lineup": {
            "starting_xi_added": sorted(
                set(current_week["starting_xi"]) - set(previous_week["starting_xi"])
            ),
            "starting_xi_removed": sorted(
                set(previous_week["starting_xi"]) - set(current_week["starting_xi"])
            ),
            "captain": {
                "before": previous_week["captain_id"],
                "after": current_week["captain_id"],
            },
            "vice_captain": {
                "before": previous_week["vice_captain_id"],
                "after": current_week["vice_captain_id"],
            },
            "bench_before": previous_week["bench"],
            "bench_after": current_week["bench"],
        },
        "changed_source_families": _source_family_changes(
            previous_families, source_families
        ),
    }
    result["content_sha256"] = artifact_hash(result)
    return result


def _diff_markdown(diff: Mapping[str, Any]) -> str:
    lines = [
        f"# Initial-squad checkpoint diff: {diff['checkpoint_id']}",
        "",
        f"Status: `{diff['status']}`",
        "",
    ]
    if diff["status"] != "compared":
        lines.append(str(diff["reason"]))
        lines.append("")
        return "\n".join(lines)
    predecessor = diff["predecessor"]
    squad = diff["squad"]
    lineup = diff["gw1_lineup"]
    lines.extend(
        [
            f"Compared with `{predecessor['checkpoint_id']}`.",
            "",
            "## Squad",
            "",
            f"- Added: {', '.join(squad['added']) or 'none'}",
            f"- Removed: {', '.join(squad['removed']) or 'none'}",
            f"- Bank delta: {squad['bank_delta']}",
            f"- Objective delta: {squad['objective_delta']}",
            "",
            "## GW1 lineup",
            "",
            f"- Starting XI added: {', '.join(lineup['starting_xi_added']) or 'none'}",
            f"- Starting XI removed: {', '.join(lineup['starting_xi_removed']) or 'none'}",
            f"- Captain: {lineup['captain']['before']} -> {lineup['captain']['after']}",
            f"- Vice-captain: {lineup['vice_captain']['before']} -> {lineup['vice_captain']['after']}",
            "",
            "## Source changes",
            "",
            f"- {', '.join(diff['changed_source_families']) or 'none'}",
            "",
        ]
    )
    return "\n".join(lines)


def _write_immutable_text(path: Path, text: str) -> None:
    encoded = text.encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as handle:
            handle.write(encoded)
            handle.flush()
    except FileExistsError:
        if path.read_bytes() != encoded:
            raise InitialSquadCheckpointConflict(
                f"Immutable checkpoint path already has different content: {path}"
            )


def run_initial_squad_checkpoint(
    *,
    manifest_path: Path,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    policy_path: Path = DEFAULT_POLICY_PATH,
    rules_path: Path | None = None,
) -> dict[str, Any]:
    """Run and seal a deterministic, advisory-only initial-squad checkpoint."""

    verified = verify_preseason_manifest(manifest_path)
    manifest = verified["manifest"]
    bound_rules_path = verified["bound_paths"]["ruleset"]
    if rules_path is not None and rules_path.resolve() != bound_rules_path.resolve():
        raise InitialSquadCheckpointError(
            "Supplied rules path does not match the manifest-bound ruleset"
        )
    chosen_rules_path = bound_rules_path if rules_path is None else rules_path.resolve()
    actual_rules_hash = ruleset_sha256(chosen_rules_path)
    if actual_rules_hash != manifest["ruleset_sha256"]:
        raise InitialSquadCheckpointError("Manifest-bound ruleset hash mismatch")
    rules = load_rules(chosen_rules_path)
    policy = _read_json_object(policy_path.resolve(), "initial-squad policy")
    try:
        packet_data = build_initial_squad_packet(
            verified,
            policy=policy,
            rules=rules,
            rules_hash=actual_rules_hash,
        )
        packet = packet_data["packet"]
        selection = run_live_seed_selection(
            packet=packet,
            policy=policy,
            rules=rules,
            ruleset_sha256=actual_rules_hash,
            selected_arm="robust",
        )
    except InitialSquadError as exc:
        raise InitialSquadCheckpointError(str(exc)) from exc
    selection = deepcopy(selection)
    approval = dict(selection["approval_gate"])
    blockers = sorted(
        set([*approval.get("blockers", []), "forecast_baseline_not_approval_eligible"])
    )
    approval["status"] = "blocked"
    approval["blockers"] = blockers
    approval["forecast_quality"] = deepcopy(packet_data["forecast_quality"])
    selection["approval_gate"] = approval
    selection["content_sha256"] = initial_squad_hash(selection)
    proposal = selection["selection"]["proposal"]
    boundaries = _boundary_alternatives(
        packet,
        proposal=proposal,
        policy=policy,
        rules=rules,
        rules_hash=actual_rules_hash,
    )
    risks = [
        {
            "risk_id": "forecast_baseline_only",
            "severity": "blocking",
            "detail": packet_data["forecast_quality"]["reason"],
        },
        *[
            {
                "risk_id": f"source_family_unavailable:{family_id}",
                "severity": "degraded",
                "detail": fallback,
            }
            for family_id, fallback in sorted(packet_data["fallbacks"].items())
        ],
    ]
    input_payload = {
        "schema_version": "1.0",
        "checkpoint_id": manifest["checkpoint_id"],
        "season": manifest["season"],
        "input_manifest_sha256": manifest["content_sha256"],
        "packet": packet,
        "feature_state": packet_data["feature_state"],
        "candidate_universe": packet_data["candidate_universe"],
        "exclusions": packet_data["exclusions"],
        "source_families": packet_data["source_families"],
        "fallbacks": packet_data["fallbacks"],
        "forecast_quality": packet_data["forecast_quality"],
        "fixture_count": packet_data["fixture_count"],
    }
    input_payload["content_sha256"] = artifact_hash(input_payload)
    recommendation = {
        "schema_version": "1.0",
        "checkpoint_id": manifest["checkpoint_id"],
        "season": manifest["season"],
        "observed_at": verified["observed_at"],
        "decision_cutoff": verified["deadline"],
        "account_writes": False,
        "browser_actions": False,
        "input_packet_sha256": packet["content_sha256"],
        "selection": selection,
        "source_families": packet_data["source_families"],
        "risk_diagnostics": risks,
        "boundary_alternatives": boundaries,
    }
    recommendation["content_sha256"] = artifact_hash(recommendation)

    output_root = output_root.resolve()
    report_dir = output_root / str(manifest["checkpoint_id"])
    with _exclusive_lock(output_root / ".initial-squad.lock"):
        predecessor_checkpoint, predecessor_recommendation = _predecessor_output(
            output_root, manifest.get("predecessor_checkpoint_hash")
        )
        diff = _recommendation_diff(
            checkpoint_id=str(manifest["checkpoint_id"]),
            manifest_hash=str(manifest["content_sha256"]),
            recommendation=recommendation,
            predecessor_checkpoint=predecessor_checkpoint,
            predecessor_recommendation=predecessor_recommendation,
            source_families=packet_data["source_families"],
        )
        diff_markdown = _diff_markdown(diff)
        checkpoint = {
            "schema_version": "1.0",
            "checkpoint_id": manifest["checkpoint_id"],
            "season": manifest["season"],
            "observed_at": verified["observed_at"],
            "decision_cutoff": verified["deadline"],
            "status": "degraded",
            "account_writes": False,
            "browser_actions": False,
            "input_manifest": {
                "path": str(manifest_path.resolve()),
                "content_sha256": manifest["content_sha256"],
                "request_sha256": manifest.get("request_sha256"),
            },
            "configuration": {
                "policy_path": str(policy_path.resolve()),
                "policy_sha256": initial_squad_hash(policy),
                "policy_id": policy.get("policy_id"),
                "policy_version": policy.get("policy_version"),
                "ruleset_path": str(chosen_rules_path),
                "ruleset_id": rules.get("meta", {}).get("ruleset_id"),
                "ruleset_sha256": actual_rules_hash,
                "forecast_model_version": _BASELINE_MODEL,
            },
            "input_packet_sha256": input_payload["content_sha256"],
            "recommendation_sha256": recommendation["content_sha256"],
            "diff_sha256": diff["content_sha256"],
            "diff_markdown_sha256": hashlib.sha256(
                diff_markdown.encode("utf-8")
            ).hexdigest(),
            "predecessor": (
                {
                    "checkpoint_id": predecessor_checkpoint["checkpoint_id"],
                    "recommendation_sha256": predecessor_recommendation[
                        "content_sha256"
                    ],
                }
                if predecessor_checkpoint is not None
                and predecessor_recommendation is not None
                else {
                    "checkpoint_id": None,
                    "recommendation_sha256": None,
                    "manifest_predecessor_hash": manifest.get(
                        "predecessor_checkpoint_hash"
                    ),
                }
            ),
            "approval_status": selection["approval_gate"]["status"],
        }
        checkpoint["content_sha256"] = artifact_hash(checkpoint)
        try:
            _write_immutable_json(report_dir / "input-packet.json", input_payload)
            _write_immutable_json(report_dir / "recommendation.json", recommendation)
            _write_immutable_json(report_dir / "diff.json", diff)
            _write_immutable_text(report_dir / "diff.md", diff_markdown)
            _write_immutable_json(report_dir / "checkpoint.json", checkpoint)
        except EvidenceCheckpointConflict as exc:
            raise InitialSquadCheckpointConflict(str(exc)) from exc
    return checkpoint
