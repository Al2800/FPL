"""Seed-reproducible Monte Carlo FPL outcome simulation (ticket 05).

Composes appearance distributions × per-90 event rates on shared Poisson
scorelines, then scores every sampled path through :mod:`src.scoring.engine`.
No ML fitting happens here — weak marginals must not be disguised by simulation.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
from random import Random
from typing import Any

from src.forecasting.appearance_distribution import AppearanceDistribution
from src.scoring.engine import score_match_stats
from src.scoring.rules_loader import load_rules


MONTE_CARLO_VERSION = "1.0"
_APPEARANCE_MINUTES = {"zero": 0, "under_60": 45, "sixty_plus": 90}


class MonteCarloError(ValueError):
    """Raised when simulation inputs cannot produce a safe run."""


@dataclass(frozen=True)
class FixtureSimulationInput:
    fixture_id: str
    home_club_id: str
    away_club_id: str
    expected_home_xg: float
    expected_away_xg: float

    def __post_init__(self) -> None:
        for name, value in (
            ("expected_home_xg", self.expected_home_xg),
            ("expected_away_xg", self.expected_away_xg),
        ):
            if not math.isfinite(value) or value < 0:
                raise MonteCarloError(f"{name} must be a finite non-negative number")


@dataclass(frozen=True)
class PlayerSimulationInput:
    player_id: str
    position: str
    club_id: str
    fixture_id: str
    appearance: AppearanceDistribution
    goals_per_90: float
    assists_per_90: float
    saves_per_90: float = 0.0

    def __post_init__(self) -> None:
        if self.position not in {"GKP", "DEF", "MID", "FWD"}:
            raise MonteCarloError(f"Unsupported position: {self.position}")
        for name, value in (
            ("goals_per_90", self.goals_per_90),
            ("assists_per_90", self.assists_per_90),
            ("saves_per_90", self.saves_per_90),
        ):
            if not math.isfinite(value) or value < 0:
                raise MonteCarloError(f"{name} must be a finite non-negative number")


def _artifact_hash(value: Mapping[str, Any]) -> str:
    body = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(body).hexdigest()


def _poisson(rng: Random, rate: float) -> int:
    if rate <= 0:
        return 0
    # Knuth for small rates; sufficient for FPL event counts.
    limit = math.exp(-rate)
    count = 0
    product = 1.0
    while True:
        product *= rng.random()
        if product <= limit:
            return count
        count += 1
        if count > 40:
            return count


def _sample_appearance(rng: Random, appearance: AppearanceDistribution) -> str:
    draw = rng.random()
    if draw < appearance.zero:
        return "zero"
    if draw < appearance.zero + appearance.under_60:
        return "under_60"
    return "sixty_plus"


def percentile_summary(samples: Sequence[float]) -> dict[str, float]:
    """Return mean plus P10/P50/P90 for a finite sample."""

    if not samples:
        raise MonteCarloError("Cannot summarise an empty sample")
    ordered = sorted(float(value) for value in samples)
    if any(not math.isfinite(value) for value in ordered):
        raise MonteCarloError("Simulation samples must be finite")

    def at(fraction: float) -> float:
        if len(ordered) == 1:
            return ordered[0]
        index = fraction * (len(ordered) - 1)
        lower = math.floor(index)
        upper = math.ceil(index)
        if lower == upper:
            return ordered[lower]
        weight = index - lower
        return ordered[lower] * (1.0 - weight) + ordered[upper] * weight

    return {
        "mean": round(sum(ordered) / len(ordered), 6),
        "p10": round(at(0.10), 6),
        "p50": round(at(0.50), 6),
        "p90": round(at(0.90), 6),
    }


def _player_match_stats(
    *,
    player: PlayerSimulationInput,
    minutes: int,
    team_goals: int,
    opponent_goals: int,
    rng: Random,
) -> dict[str, Any]:
    if minutes <= 0:
        return {
            "position": player.position,
            "minutes": 0,
            "goals": 0,
            "assists": 0,
            "clean_sheet": False,
            "goals_conceded": 0,
            "saves": 0,
            "yellow_cards": 0,
            "red_cards": 0,
            "own_goals": 0,
            "penalty_misses": 0,
            "penalty_saves": 0,
            "defensive_actions": 0,
            "bonus": 0,
        }
    scale = minutes / 90.0
    goals = _poisson(rng, player.goals_per_90 * scale)
    assists = _poisson(rng, player.assists_per_90 * scale)
    # Soft conditioning: cannot exceed a generous multiple of team goals.
    if team_goals == 0:
        goals = 0
    else:
        goals = min(goals, team_goals)
    saves = (
        _poisson(rng, player.saves_per_90 * scale)
        if player.position == "GKP"
        else 0
    )
    return {
        "position": player.position,
        "minutes": minutes,
        "goals": goals,
        "assists": assists,
        "clean_sheet": opponent_goals == 0 and minutes >= 60,
        "goals_conceded": opponent_goals,
        "saves": saves,
        "yellow_cards": 0,
        "red_cards": 0,
        "own_goals": 0,
        "penalty_misses": 0,
        "penalty_saves": 0,
        "defensive_actions": 0,
        "bonus": 0,
    }


def simulate_gameweek(
    *,
    fixtures: Sequence[FixtureSimulationInput],
    players: Sequence[PlayerSimulationInput],
    n_paths: int,
    seed: int,
    rules: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Simulate ``n_paths`` correlated player-point outcomes.

    Teammates share the sampled fixture scoreline so clean sheets and goals
    conceded are intra-team correlated. Appearance and attacking events are
    drawn per player conditional on that scoreline.
    """

    if not isinstance(n_paths, int) or isinstance(n_paths, bool) or n_paths < 1:
        raise MonteCarloError("n_paths must be a positive integer")
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise MonteCarloError("seed must be an integer")
    fixture_map = {row.fixture_id: row for row in fixtures}
    if len(fixture_map) != len(fixtures):
        raise MonteCarloError("fixture_id values must be unique")
    for player in players:
        if player.fixture_id not in fixture_map:
            raise MonteCarloError(
                f"Player {player.player_id} references unknown fixture {player.fixture_id}"
            )
        fixture = fixture_map[player.fixture_id]
        if player.club_id not in {fixture.home_club_id, fixture.away_club_id}:
            raise MonteCarloError(
                f"Player {player.player_id} club_id is not in fixture {player.fixture_id}"
            )

    scoring_rules = dict(rules) if rules is not None else load_rules()
    rng = Random(seed)
    path_points: dict[str, list[float]] = {player.player_id: [] for player in players}

    for _ in range(n_paths):
        scorelines: dict[str, tuple[int, int]] = {}
        for fixture in fixtures:
            scorelines[fixture.fixture_id] = (
                _poisson(rng, fixture.expected_home_xg),
                _poisson(rng, fixture.expected_away_xg),
            )
        for player in players:
            fixture = fixture_map[player.fixture_id]
            home_goals, away_goals = scorelines[player.fixture_id]
            if player.club_id == fixture.home_club_id:
                team_goals, opponent_goals = home_goals, away_goals
            else:
                team_goals, opponent_goals = away_goals, home_goals
            state = _sample_appearance(rng, player.appearance)
            minutes = _APPEARANCE_MINUTES[state]
            stats = _player_match_stats(
                player=player,
                minutes=minutes,
                team_goals=team_goals,
                opponent_goals=opponent_goals,
                rng=rng,
            )
            points = float(score_match_stats(stats, scoring_rules)["total"])
            path_points[player.player_id].append(points)

    player_summaries = {
        player_id: percentile_summary(samples)
        for player_id, samples in sorted(path_points.items())
    }
    # Pool all player means into a projection envelope for the GDR summary.
    all_means = [row["mean"] for row in player_summaries.values()]
    pooled = percentile_summary(all_means) if all_means else None

    result = {
        "schema_version": MONTE_CARLO_VERSION,
        "n_paths": n_paths,
        "seed": seed,
        "model": {
            "type": "appearance_x_rates_x_shared_poisson_scorelines",
            "scoring": "src.scoring.engine.score_match_stats",
        },
        "players": player_summaries,
        "player_path_points": path_points,
        "projections_envelope": pooled,
        "fixture_ids": sorted(fixture_map),
        "player_ids": sorted(path_points),
    }
    # Hash without the full path matrix (large); bind summaries + controls.
    bindable = {
        key: value
        for key, value in result.items()
        if key != "player_path_points"
    }
    result["content_sha256"] = _artifact_hash(bindable)
    return result


def plan_points_samples(
    path_points: Mapping[str, Sequence[float]],
    *,
    starting_xi: Sequence[str],
    captain_id: str,
    hit_cost: int = 0,
) -> list[float]:
    """Aggregate per-path XI points with a double-counted captain."""

    if captain_id not in starting_xi:
        raise MonteCarloError("captain_id must be in starting_xi")
    lengths = {len(path_points[player_id]) for player_id in starting_xi}
    if len(lengths) != 1:
        raise MonteCarloError("starting_xi players must share path length")
    n_paths = next(iter(lengths))
    samples: list[float] = []
    for index in range(n_paths):
        total = 0.0
        for player_id in starting_xi:
            points = float(path_points[player_id][index])
            total += points * (2.0 if player_id == captain_id else 1.0)
        samples.append(total - float(hit_cost))
    return samples


def attach_monte_carlo_to_decision_record(
    record: Mapping[str, Any],
    simulation: Mapping[str, Any],
) -> dict[str, Any]:
    """Attach P10/P50/P90 projections and plan distributions to a GDR."""

    result = dict(record)
    summary = dict(result.get("projections_summary") or {})
    envelope = simulation.get("projections_envelope") or {}
    summary.update(
        {
            "p10": envelope.get("p10"),
            "p50": envelope.get("p50"),
            "p90": envelope.get("p90"),
            "mean": envelope.get("mean"),
            "simulation": {
                "n_paths": simulation.get("n_paths"),
                "seed": simulation.get("seed"),
                "content_sha256": simulation.get("content_sha256"),
                "model": simulation.get("model"),
                "players": simulation.get("players"),
            },
        }
    )
    versions = list(summary.get("model_versions") or [])
    if "monte_carlo_v1" not in versions:
        versions.append("monte_carlo_v1")
    summary["model_versions"] = versions
    result["projections_summary"] = summary

    path_points = simulation.get("player_path_points") or {}
    plans = []
    for plan in result.get("candidate_plans") or []:
        updated = dict(plan)
        xi = list(updated.get("starting_xi") or [])
        captain = updated.get("captain_id")
        if xi and captain and all(player_id in path_points for player_id in xi):
            samples = plan_points_samples(
                path_points,
                starting_xi=xi,
                captain_id=str(captain),
                hit_cost=int(updated.get("hit_cost") or 0),
            )
            updated["points_distribution"] = {
                **percentile_summary(samples),
                "n_paths": len(samples),
                "seed": simulation.get("seed"),
            }
        plans.append(updated)
    result["candidate_plans"] = plans
    return result


def write_calibration_report(
    out_dir: Path,
    *,
    simulation: Mapping[str, Any],
    calibration: Mapping[str, Any],
    notes: str,
) -> dict[str, Path]:
    """Persist Monte Carlo calibration JSON + Markdown under ``out_dir``."""

    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "report_id": "monte-carlo-calibration",
        "simulation": {
            "n_paths": simulation.get("n_paths"),
            "seed": simulation.get("seed"),
            "content_sha256": simulation.get("content_sha256"),
            "model": simulation.get("model"),
            "players": simulation.get("players"),
        },
        "calibration": dict(calibration),
        "notes": notes,
    }
    payload["content_sha256"] = _artifact_hash(payload)
    json_path = out_dir / "monte-carlo-calibration.json"
    md_path = out_dir / "monte-carlo-calibration.md"
    json_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    players = simulation.get("players") or {}
    lines = [
        "# Monte Carlo calibration",
        "",
        notes,
        "",
        f"- Paths: `{simulation.get('n_paths')}`",
        f"- Seed: `{simulation.get('seed')}`",
        f"- Simulation hash: `{simulation.get('content_sha256')}`",
        "",
        "## Point calibration",
        "",
        f"- n: `{calibration.get('n')}`",
        f"- bias (actual − predicted): `{calibration.get('bias_actual_minus_predicted')}`",
        f"- MAE: `{calibration.get('mean_absolute_error')}`",
        f"- RMSE: `{calibration.get('root_mean_square_error')}`",
        f"- correlation: `{calibration.get('correlation')}`",
        "",
        "## Player P10 / P50 / P90",
        "",
    ]
    for player_id, row in sorted(players.items()):
        lines.append(
            f"- `{player_id}`: P10={row.get('p10')}, P50={row.get('p50')}, "
            f"P90={row.get('p90')}, mean={row.get('mean')}"
        )
    lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return {"json": json_path, "markdown": md_path}
