"""Deterministic live Gameweek orchestrator (plain Python, ADR-0010).

Chains pre-deadline snapshot selection → optional episode build → forecast →
ticket-01 adapter → optimiser → baseline comparison → Gameweek Decision Record.
Evidence/challenger inputs are optional; absence marks the record degraded.
"""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.forecasting.live_faithful import (
    LiveFaithfulForecastError,
    build_live_faithful_forecast,
)
from src.forecasting.monte_carlo import (
    MonteCarloError,
    attach_monte_carlo_to_decision_record,
    simulate_gameweek,
)
from src.optimisation.io import fingerprint
from src.orchestration.freshness_monitor import apply_freshness_to_decision_record
from src.orchestration.live_solver_adapter import (
    LiveSolverAdapterError,
    adapt_solve_and_record,
)
from src.quality.point_in_time import assert_no_lookahead, filter_by_deadline
from src.reporting.decision_record import write_decision_record
from src.scoring.rules_loader import DEFAULT_RULES_PATH, load_rules


REPO_ROOT = Path(__file__).resolve().parents[2]


class RunGameweekError(ValueError):
    """Raised when the live Gameweek chain cannot complete safely."""


def select_latest_predeadline_snapshot(
    candidates: Sequence[Mapping[str, Any]],
    *,
    deadline: str,
) -> dict[str, Any]:
    """Return the latest snapshot with available_at <= deadline.

    Later observations may exist in the candidate pool; they are ignored, never
    selected. The returned snapshot is asserted to be cutoff-safe.
    """

    eligible = filter_by_deadline(candidates, deadline)
    if not eligible:
        raise RunGameweekError(
            f"No pre-deadline snapshots with available_at <= {deadline}"
        )
    ranked = sorted(
        eligible,
        key=lambda row: (str(row["available_at"]), str(row.get("observed_at") or "")),
    )
    selected = dict(ranked[-1])
    assert_no_lookahead([selected], deadline)
    return selected


def load_snapshot_candidates(paths: Sequence[Path]) -> list[dict[str, Any]]:
    """Load capture-summary style JSON objects as snapshot candidates."""

    candidates: list[dict[str, Any]] = []
    for path in paths:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, ValueError) as exc:
            raise RunGameweekError(f"Cannot read snapshot candidate {path}: {exc}") from exc
        if not isinstance(payload, dict):
            raise RunGameweekError(f"Snapshot candidate must be a JSON object: {path}")
        available_at = payload.get("available_at") or payload.get("observed_at")
        if not available_at:
            raise RunGameweekError(
                f"Snapshot candidate missing available_at/observed_at: {path}"
            )
        row = dict(payload)
        row["available_at"] = str(available_at)
        row.setdefault("observed_at", str(available_at))
        row["path"] = str(path)
        candidates.append(row)
    return candidates


def forecast_market_from_live_faithful(forecast_view: Mapping[str, Any]) -> dict[str, Any]:
    """Project a live-faithful forecast view into the live solver adapter market."""

    players = []
    for row in forecast_view.get("players", []):
        if not isinstance(row, Mapping):
            raise RunGameweekError("live-faithful forecast players must be objects")
        quote = row.get("quote") if isinstance(row.get("quote"), Mapping) else {}
        projection = (
            row.get("projection") if isinstance(row.get("projection"), Mapping) else row
        )
        try:
            now_cost = float(quote.get("now_cost", row.get("now_cost")))
            expected_points = float(
                projection.get("expected_points", row.get("expected_points"))
            )
        except (TypeError, ValueError) as exc:
            raise RunGameweekError(
                f"live-faithful player {row.get('player_id')} lacks market fields"
            ) from exc
        players.append(
            {
                "player_id": str(row["player_id"]),
                "web_name": str(row.get("name") or row.get("web_name") or row["player_id"]),
                "position": str(row["position"]),
                "club_id": str(row["club_id"]),
                "now_cost": round(now_cost, 1),
                "expected_points": round(expected_points, 2),
                "status": str(row.get("status") or "a"),
            }
        )
    market = {
        "season": str(forecast_view["season"]),
        "gameweek": int(forecast_view["gameweek"]),
        "model_version": str(forecast_view.get("model_version") or "live_faithful"),
        "model_status": str(forecast_view.get("model_status") or forecast_view.get("status")),
        "status": str(forecast_view.get("status") or "complete"),
        "limitations": list(forecast_view.get("limitations") or []),
        "players": players,
    }
    if forecast_view.get("content_sha256"):
        market["content_sha256"] = str(forecast_view["content_sha256"])
        market["live_faithful_sha256"] = str(forecast_view["content_sha256"])
    return market


def default_output_dir(*, season: str, gameweek: int, root: Path | None = None) -> Path:
    base = root or (REPO_ROOT / "reports" / "gameweeks")
    return base / f"{season}-gw{int(gameweek):02d}"


def run_gameweek(
    *,
    manager_state: Mapping[str, Any],
    forecast: Mapping[str, Any] | None = None,
    live_faithful_inputs: Mapping[str, Mapping[str, Any]] | None = None,
    snapshot_candidates: Sequence[Mapping[str, Any]] | None = None,
    evidence: Mapping[str, Any] | None = None,
    freshness_report: Mapping[str, Any] | None = None,
    monte_carlo: Mapping[str, Any] | None = None,
    rules_path: Path | None = None,
    out_dir: Path | None = None,
    active_chip: str | None = None,
    max_transfers: int = 3,
    validate_record: bool = True,
) -> dict[str, Any]:
    """Run the deterministic advisory Gameweek chain and write the GDR.

    ``monte_carlo`` may supply ``fixtures``, ``players``, ``n_paths`` and
    ``seed`` for distributional projections (ticket 05).
    """

    state = dict(manager_state)
    for field in ("season", "gameweek", "deadline", "available_at"):
        if field not in state:
            raise RunGameweekError(f"manager_state is missing {field}")

    deadline = str(state["deadline"])
    selected_snapshot: dict[str, Any] | None = None
    if snapshot_candidates:
        selected_snapshot = select_latest_predeadline_snapshot(
            snapshot_candidates, deadline=deadline
        )

    degraded_reasons: list[str] = []
    forecast_view: dict[str, Any] | None = None
    if forecast is not None:
        market = dict(forecast)
    elif live_faithful_inputs is not None:
        required = (
            "feature_state",
            "identity_map",
            "player_prior",
            "team_prior",
            "model_config",
        )
        missing = [name for name in required if name not in live_faithful_inputs]
        if missing:
            raise RunGameweekError(f"live_faithful_inputs missing {missing}")
        try:
            forecast_view = build_live_faithful_forecast(
                feature_state=live_faithful_inputs["feature_state"],
                identity_map=live_faithful_inputs["identity_map"],
                player_prior=live_faithful_inputs["player_prior"],
                team_prior=live_faithful_inputs["team_prior"],
                model_config=live_faithful_inputs["model_config"],
            )
        except LiveFaithfulForecastError as exc:
            raise RunGameweekError(str(exc)) from exc
        market = forecast_market_from_live_faithful(forecast_view)
        if forecast_view.get("status") == "degraded" or forecast_view.get("limitations"):
            degraded_reasons.append("live_faithful_degraded")
            degraded_reasons.extend(
                f"forecast:{item}" for item in forecast_view.get("limitations") or []
            )
    else:
        raise RunGameweekError("Provide forecast or live_faithful_inputs")

    if evidence is None:
        degraded_reasons.append("evidence_absent_fallback_deterministic")
    elif evidence.get("status") in {"absent", "late", "missing"}:
        degraded_reasons.append(f"evidence_{evidence.get('status')}")

    rules = rules_path or DEFAULT_RULES_PATH
    try:
        bundle = adapt_solve_and_record(
            manager_state=state,
            forecast=market,
            rules_path=rules,
            active_chip=active_chip,
            max_transfers=max_transfers,
            validate_record=validate_record,
        )
    except LiveSolverAdapterError as exc:
        raise RunGameweekError(str(exc)) from exc

    record = deepcopy(bundle["decision_record"])
    degraded = bool(degraded_reasons)
    record["data_quality"] = "degraded" if degraded else "complete"
    record["degraded"] = degraded
    record["degraded_reasons"] = sorted(set(degraded_reasons))
    record["freshness"] = {
        "manager_available_at": str(state["available_at"]),
        "deadline": deadline,
        "snapshot_available_at": (
            None if selected_snapshot is None else str(selected_snapshot.get("available_at"))
        ),
        "snapshot_path": None if selected_snapshot is None else selected_snapshot.get("path"),
        "point_in_time_ok": True,
    }
    if freshness_report is not None:
        record = apply_freshness_to_decision_record(record, freshness_report)
        degraded_reasons = list(record.get("degraded_reasons") or [])
        degraded = bool(record.get("degraded"))

    simulation: dict[str, Any] | None = None
    if monte_carlo is not None:
        try:
            from src.forecasting.appearance_distribution import AppearanceDistribution
            from src.forecasting.monte_carlo import (
                FixtureSimulationInput,
                PlayerSimulationInput,
            )

            fixtures = [
                FixtureSimulationInput(**dict(row))
                for row in monte_carlo["fixtures"]
            ]
            players = []
            for row in monte_carlo["players"]:
                payload = dict(row)
                appearance = payload.pop("appearance")
                if isinstance(appearance, Mapping):
                    appearance = AppearanceDistribution.from_mapping(appearance)
                players.append(
                    PlayerSimulationInput(appearance=appearance, **payload)
                )
            simulation = simulate_gameweek(
                fixtures=fixtures,
                players=players,
                n_paths=int(monte_carlo.get("n_paths", 500)),
                seed=int(monte_carlo.get("seed", 0)),
                rules=load_rules(rules),
            )
            record = attach_monte_carlo_to_decision_record(record, simulation)
        except (MonteCarloError, KeyError, TypeError, ValueError) as exc:
            raise RunGameweekError(f"monte_carlo inputs invalid: {exc}") from exc

    if selected_snapshot is not None:
        record.setdefault("pipeline", {})
        if isinstance(record["pipeline"], dict):
            record["pipeline"] = dict(record["pipeline"])
            record["pipeline"]["selected_snapshot"] = {
                "available_at": selected_snapshot.get("available_at"),
                "observed_at": selected_snapshot.get("observed_at"),
                "path": selected_snapshot.get("path"),
            }

    destination = out_dir or default_output_dir(
        season=str(state["season"]), gameweek=int(state["gameweek"])
    )
    destination.mkdir(parents=True, exist_ok=True)
    gdr_path = destination / "decision-record.json"
    write_decision_record(record, gdr_path)
    solver_input_path = destination / "solver-input.json"
    solver_output_path = destination / "solver-output.json"
    forecast_path = destination / "forecast-market.json"
    solver_input_path.write_text(
        json.dumps(bundle["solver_input"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    solver_output_path.write_text(
        json.dumps(bundle["solver_output"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    forecast_path.write_text(
        json.dumps(market, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    result = {
        "season": str(state["season"]),
        "gameweek": int(state["gameweek"]),
        "out_dir": str(destination),
        "decision_record_path": str(gdr_path),
        "decision_record_sha256": fingerprint(record),
        "solver_input_fingerprint": bundle["solver_output"].get("input_fingerprint"),
        "solver_output_fingerprint": bundle["solver_output"].get("output_fingerprint"),
        "degraded": degraded,
        "degraded_reasons": record["degraded_reasons"],
        "selected_snapshot": selected_snapshot,
        "record": record,
        "solver_input": bundle["solver_input"],
        "solver_output": bundle["solver_output"],
        "forecast_market": market,
        "live_faithful_forecast": forecast_view,
        "monte_carlo": simulation,
    }
    return result
