"""Structural, no-network preflight for approved live-source credentials.

This command intentionally does *not* construct an HTTP client or call an
endpoint. It answers one operational question only: whether a registered,
approved source has the named credential in the current process environment.
It never serialises credential values.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.ingestion.lineups_minutes import (
    LineupsMinutesError,
    provider_activation_gate,
)


DEFAULT_ODDS_CONFIG = ROOT / "config/data_sources/2026-27-live-odds-provider.json"
DEFAULT_LINEUPS_CONFIG = ROOT / "config/data_sources/2026-27-lineups-minutes.json"


class LiveSourcePreflightError(ValueError):
    """Raised when a source configuration cannot safely be preflighted."""


def _load_json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LiveSourcePreflightError(f"Cannot load JSON config: {path}") from exc
    if not isinstance(value, dict):
        raise LiveSourcePreflightError(f"Config must be a JSON object: {path}")
    return value


def _environment_has_value(environ: Mapping[str, str], name: str) -> bool:
    """Check only non-blank presence; callers must never return the value."""

    value = environ.get(name)
    return isinstance(value, str) and bool(value.strip())


def _odds_preflight(
    config: Mapping[str, Any], environ: Mapping[str, str]
) -> dict[str, Any]:
    request = config.get("request")
    provider = config.get("provider")
    if not isinstance(request, Mapping) or not isinstance(provider, Mapping):
        raise LiveSourcePreflightError("Odds config requires provider and request objects")
    environment_name = request.get("secret_environment_variable")
    source_id = provider.get("source_id")
    if not isinstance(environment_name, str) or not environment_name:
        raise LiveSourcePreflightError("Odds config requires secret_environment_variable")
    if not isinstance(source_id, str) or not source_id:
        raise LiveSourcePreflightError("Odds config requires provider.source_id")

    present = _environment_has_value(environ, environment_name)
    return {
        "family": "odds",
        "source_id": source_id,
        "credential_environment": environment_name,
        "credential_checked": True,
        "credential_present": present,
        "status": "ready_structural" if present else "degraded",
        "reason": None if present else "missing_credential_no_network",
        "network_actions": False,
        "value_redacted": True,
    }


def _selected_provider_entry(
    config: Mapping[str, Any], provider_id: str
) -> Mapping[str, Any] | None:
    providers = config.get("providers")
    if not isinstance(providers, list):
        raise LiveSourcePreflightError("Lineups config requires a providers list")
    for item in providers:
        if isinstance(item, Mapping) and item.get("provider_id") == provider_id:
            return item
    return None


def _lineups_preflight(
    config: Mapping[str, Any], environ: Mapping[str, str]
) -> dict[str, Any]:
    selected = config.get("selected_provider")
    if selected is None or selected == "":
        # Candidate keys are deliberately not inspected or reported. This makes
        # a null selection an explicit no-network, no-secret boundary.
        return {
            "family": "lineups_minutes",
            "selected_provider": None,
            "credential_checked": False,
            "credential_present": None,
            "status": "degraded",
            "reason": "no_provider_selected",
            "network_actions": False,
        }
    if not isinstance(selected, str):
        raise LiveSourcePreflightError("selected_provider must be a string or null")

    entry = _selected_provider_entry(config, selected)
    if entry is None:
        return {
            "family": "lineups_minutes",
            "selected_provider": selected,
            "credential_checked": False,
            "credential_present": None,
            "status": "degraded",
            "reason": "selected_provider_not_registered",
            "network_actions": False,
        }
    try:
        activation_reason = provider_activation_gate(config, selected)
    except LineupsMinutesError as exc:
        raise LiveSourcePreflightError("Invalid selected lineups provider") from exc

    capture_method = entry.get("capture_method")
    environment_name = entry.get("credential_environment")
    if capture_method == "manual_citation":
        # Official team-sheet capture is citation-based; no API key and no
        # automated network scrape are required for structural readiness.
        return {
            "family": "lineups_minutes",
            "selected_provider": selected,
            "capture_method": "manual_citation",
            "credential_checked": False,
            "credential_present": None,
            "activation_status": "ready" if activation_reason is None else "degraded",
            "status": "ready_structural" if activation_reason is None else "degraded",
            "reason": activation_reason,
            "network_actions": False,
        }
    if not isinstance(environment_name, str) or not environment_name:
        raise LiveSourcePreflightError(
            "Selected lineups provider requires credential_environment"
        )

    present = _environment_has_value(environ, environment_name)
    reason = activation_reason or (None if present else "missing_credential_no_network")
    return {
        "family": "lineups_minutes",
        "selected_provider": selected,
        "credential_environment": environment_name,
        "credential_checked": True,
        "credential_present": present,
        "activation_status": "ready" if activation_reason is None else "degraded",
        "status": "ready_structural" if reason is None else "degraded",
        "reason": reason,
        "network_actions": False,
        "value_redacted": True,
    }


def build_live_source_preflight(
    *,
    odds_config: Mapping[str, Any],
    lineups_config: Mapping[str, Any],
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Build a redacted source-readiness report without network activity.

    A degraded report is successful command execution: it makes the missing
    source family visible and leaves the shared structured forecast available.
    Invalid configuration remains an error because it cannot be interpreted
    safely.
    """

    environment = environ if environ is not None else os.environ
    odds = _odds_preflight(odds_config, environment)
    lineups = _lineups_preflight(lineups_config, environment)
    families = [odds, lineups]
    degraded = [
        {"family": row["family"], "reason": row["reason"]}
        for row in families
        if row["status"] == "degraded"
    ]
    return {
        "schema_version": "1.0",
        "season": odds_config.get("season"),
        "preflight_status": "ready" if not degraded else "degraded",
        "network_actions": False,
        "account_writes": False,
        "families": families,
        "degraded_families": degraded,
        "eligible_source_families": [
            row["family"] for row in families if row["status"] == "ready_structural"
        ],
        "baseline_policy": "shared_structured_forecast_unchanged_when_family_degraded",
    }


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--odds-config", type=Path, default=DEFAULT_ODDS_CONFIG)
    parser.add_argument("--lineups-config", type=Path, default=DEFAULT_LINEUPS_CONFIG)
    return parser.parse_args()


def main() -> int:
    args = _arguments()
    report = build_live_source_preflight(
        odds_config=_load_json_object(args.odds_config),
        lineups_config=_load_json_object(args.lineups_config),
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
