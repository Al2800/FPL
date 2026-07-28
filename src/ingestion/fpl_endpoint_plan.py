"""Bounded checkpoint planning and schema checks for public FPL endpoints."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Any


class FplEndpointPlanError(ValueError):
    """Raised when an endpoint run cannot be planned safely."""


ALLOWED_TEMPLATES = {
    "bootstrap-static": "/api/bootstrap-static/",
    "fixtures": "/api/fixtures/",
    "element-summary": "/api/element-summary/{player_id}/",
    "event-live": "/api/event/{gameweek}/live/",
}


def _positive_int(value: Any, field: str) -> int:
    if isinstance(value, bool):
        raise FplEndpointPlanError(f"{field} must be a positive integer")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise FplEndpointPlanError(f"{field} must be a positive integer") from exc
    if parsed <= 0 or str(parsed) != str(value):
        raise FplEndpointPlanError(f"{field} must be a positive integer")
    return parsed


def _player_ids(value: Sequence[int] | None, *, maximum: int) -> list[int]:
    if value is None:
        return []
    if isinstance(value, (str, bytes)):
        raise FplEndpointPlanError("player_ids must be an integer sequence")
    result = sorted(
        {
            _positive_int(item, "player_id")
            for item in value
        }
    )
    if len(result) > maximum:
        raise FplEndpointPlanError(
            f"player_ids exceeds configured maximum of {maximum}"
        )
    return result


def _contracts(config: Mapping[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    automated = config.get("automated_collection")
    if not isinstance(automated, Mapping):
        raise FplEndpointPlanError("automated_collection config is missing")
    official = automated.get("official_fpl_endpoints")
    if not isinstance(official, Mapping):
        raise FplEndpointPlanError("official_fpl_endpoints config is missing")
    rows = official.get("contracts")
    if not isinstance(rows, list) or not rows:
        raise FplEndpointPlanError("official endpoint contracts are missing")
    by_id: set[str] = set()
    contracts: list[dict[str, Any]] = []
    for source in rows:
        if not isinstance(source, Mapping):
            raise FplEndpointPlanError("official endpoint contracts must be objects")
        row = deepcopy(dict(source))
        endpoint_id = str(row.get("endpoint_id", ""))
        template = str(row.get("path_template", ""))
        if endpoint_id not in ALLOWED_TEMPLATES:
            raise FplEndpointPlanError(
                f"unsupported official endpoint: {endpoint_id}"
            )
        if template != ALLOWED_TEMPLATES[endpoint_id]:
            raise FplEndpointPlanError(
                f"official endpoint template mismatch: {endpoint_id}"
            )
        if endpoint_id in by_id:
            raise FplEndpointPlanError(
                f"duplicate official endpoint contract: {endpoint_id}"
            )
        checkpoints = row.get("checkpoints")
        if (
            not isinstance(checkpoints, list)
            or any(not isinstance(item, str) or not item for item in checkpoints)
        ):
            raise FplEndpointPlanError(
                f"official endpoint checkpoints are invalid: {endpoint_id}"
            )
        by_id.add(endpoint_id)
        contracts.append(row)
    return deepcopy(dict(official)), contracts


def _planned_row(
    contract: Mapping[str, Any],
    *,
    path: str,
    artifact_name: str,
    entity_id: int | None = None,
) -> dict[str, Any]:
    return {
        "endpoint_id": str(contract["endpoint_id"]),
        "path": path,
        "artifact_name": artifact_name,
        "entity_id": entity_id,
        "schema": deepcopy(dict(contract.get("schema", {}))),
    }


def build_endpoint_capture_plan(
    *,
    config: Mapping[str, Any],
    checkpoint_id: str,
    player_ids: Sequence[int] | None = None,
    gameweek: int | None = None,
) -> list[dict[str, Any]]:
    """Return a deterministic request plan or refuse before network access."""

    official, contracts = _contracts(config)
    maximum_players = _positive_int(
        official.get("maximum_player_ids_per_run"),
        "maximum_player_ids_per_run",
    )
    maximum_requests = _positive_int(
        official.get("maximum_requests_per_run"),
        "maximum_requests_per_run",
    )
    players = _player_ids(player_ids, maximum=maximum_players)
    resolved_gameweek = (
        _positive_int(gameweek, "gameweek") if gameweek is not None else None
    )

    plan: list[dict[str, Any]] = []
    for contract in contracts:
        if checkpoint_id not in contract["checkpoints"]:
            continue
        endpoint_id = str(contract["endpoint_id"])
        if endpoint_id == "element-summary":
            for player_id in players:
                plan.append(
                    _planned_row(
                        contract,
                        path=f"/api/element-summary/{player_id}/",
                        artifact_name=f"element-summary-{player_id}.json",
                        entity_id=player_id,
                    )
                )
        elif endpoint_id == "event-live":
            if resolved_gameweek is None:
                raise FplEndpointPlanError(
                    "gameweek is required for an event-live checkpoint"
                )
            plan.append(
                _planned_row(
                    contract,
                    path=f"/api/event/{resolved_gameweek}/live/",
                    artifact_name=f"event-{resolved_gameweek}-live.json",
                    entity_id=resolved_gameweek,
                )
            )
        else:
            plan.append(
                _planned_row(
                    contract,
                    path=ALLOWED_TEMPLATES[endpoint_id],
                    artifact_name=f"{endpoint_id}.json",
                )
            )

    if not plan:
        raise FplEndpointPlanError(
            f"checkpoint has no official FPL endpoint plan: {checkpoint_id}"
        )
    if len(plan) > maximum_requests:
        raise FplEndpointPlanError(
            f"request plan exceeds configured maximum of {maximum_requests}"
        )
    return plan


def validate_endpoint_payload(
    payload: Any,
    *,
    schema: Mapping[str, Any],
) -> list[str]:
    """Return stable schema-drift reasons without discarding raw data."""

    expected_type = str(schema.get("top_level_type", ""))
    if expected_type == "object":
        if not isinstance(payload, Mapping):
            return ["schema_drift:top_level_type:object"]
        required = {
            str(value) for value in schema.get("required_fields", [])
        }
        missing = sorted(required - set(str(key) for key in payload))
        if missing:
            return [f"schema_drift:missing_fields:{','.join(missing)}"]
        return []
    if expected_type == "array":
        if not isinstance(payload, list):
            return ["schema_drift:top_level_type:array"]
        required = {
            str(value) for value in schema.get("sample_required_fields", [])
        }
        missing: set[str] = set()
        for row in payload:
            if not isinstance(row, Mapping):
                return ["schema_drift:non_object_array_item"]
            missing.update(required - set(str(key) for key in row))
        if missing:
            return [
                f"schema_drift:sample_missing_fields:{','.join(sorted(missing))}"
            ]
        return []
    return ["schema_drift:contract_top_level_type_missing"]
