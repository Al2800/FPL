"""Build a cutoff-disciplined, exploratory historical GW1 seed counterfactual."""

from __future__ import annotations

from collections import Counter
import csv
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from src.optimisation.io import fingerprint


class HistoricalSeedCounterfactualError(ValueError):
    """Raised when a seed counterfactual cannot be built without leakage."""


POSITION_COUNTS = {"GKP": 2, "DEF": 5, "MID": 5, "FWD": 3}
PREDEADLINE_EXCLUSIONS = {
    383: {
        "player": "Luis Diaz",
        "reason": "Permanent transfer to Bayern Munich completed before GW1 deadline",
        "published_at": "2025-07-30T00:00:00Z",
        "source_url": "https://www.liverpoolfc.com/news/luis-diaz-completes-permanent-move-bayern-munich",
    }
}
FORMATION_COUNTS = (
    {"DEF": defenders, "MID": midfielders, "FWD": 10 - defenders - midfielders}
    for defenders in range(3, 6)
    for midfielders in range(2, 6)
    if 1 <= 10 - defenders - midfielders <= 3
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _number(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _prior_by_code(previous_players_path: Path) -> tuple[dict[int, dict[str, float]], dict[str, float]]:
    rows = _rows(previous_players_path)
    by_code: dict[int, dict[str, float]] = {}
    position_rates: dict[str, list[float]] = {key: [] for key in POSITION_COUNTS}
    position_from_type = {"1": "GKP", "2": "DEF", "3": "MID", "4": "FWD"}
    for row in rows:
        position = position_from_type.get(str(row.get("element_type", "")))
        code = int(_number(row.get("code"), -1))
        minutes = _number(row.get("minutes"))
        points = _number(row.get("total_points"))
        if position is None or code < 0:
            continue
        appearances = minutes / 90.0
        if appearances >= 5:
            position_rates[position].append(points / appearances)
        by_code[code] = {
            "minutes": minutes,
            "points": points,
            "appearances": appearances,
        }
    means = {
        position: (
            sum(values) / len(values)
            if values
            else {"GKP": 3.5, "DEF": 3.2, "MID": 3.6, "FWD": 3.7}[position]
        )
        for position, values in position_rates.items()
    }
    return by_code, means


def _fixture_difficulty(
    episode_root: Path,
    identity_map: Mapping[str, Any],
    horizon: int,
) -> dict[str, float]:
    team_by_fpl = {
        int(row["fpl_team_id"]): str(row["canonical_id"])
        for row in identity_map["teams"]
    }
    values: dict[str, list[int]] = {team: [] for team in team_by_fpl.values()}
    for gameweek in range(1, horizon + 1):
        observed = json.loads(
            (episode_root / f"gw-{gameweek:02d}" / "observed.json").read_text(
                encoding="utf-8"
            )
        )
        for fixture in observed["fixtures"]:
            home = team_by_fpl[int(fixture["team_h"])]
            away = team_by_fpl[int(fixture["team_a"])]
            values[home].append(int(fixture["team_h_difficulty"]))
            values[away].append(int(fixture["team_a_difficulty"]))
    return {
        team: (sum(difficulties) / len(difficulties))
        for team, difficulties in values.items()
        if difficulties
    }


def build_candidate_pool(
    *,
    gw1_path: Path,
    current_players_path: Path,
    previous_players_path: Path,
    identity_map_path: Path,
    episode_root: Path,
    horizon: int = 6,
) -> dict[str, Any]:
    """Build only from whitelisted launch fields and completed prior-season data."""

    identity = json.loads(identity_map_path.read_text(encoding="utf-8"))
    canonical_by_element = {
        int(row["fpl_player_id"]): str(row["canonical_id"])
        for row in identity["players"]
    }
    club_by_name = {
        str(row["fpl_name"]): str(row["canonical_id"]) for row in identity["teams"]
    }
    code_by_element = {
        int(_number(row.get("id"), -1)): int(_number(row.get("code"), -1))
        for row in _rows(current_players_path)
    }
    prior_by_code, position_means = _prior_by_code(previous_players_path)
    difficulty = _fixture_difficulty(episode_root, identity, horizon)
    unique: dict[int, dict[str, str]] = {}
    for row in _rows(gw1_path):
        element = int(_number(row.get("element"), -1))
        if element < 0:
            continue
        projection = {
            key: row.get(key, "")
            for key in ("name", "position", "team", "element", "value")
        }
        if element in unique and unique[element] != projection:
            raise HistoricalSeedCounterfactualError(
                f"Inconsistent launch fields for element {element}"
            )
        unique[element] = projection

    candidates: list[dict[str, Any]] = []
    for element, row in unique.items():
        if element in PREDEADLINE_EXCLUSIONS:
            continue
        raw_position = str(row["position"])
        position = "GKP" if raw_position == "GK" else raw_position
        team_name = str(row["team"])
        if (
            position not in POSITION_COUNTS
            or team_name not in club_by_name
            or element not in canonical_by_element
        ):
            continue
        price = round(_number(row["value"]) / 10.0, 1)
        if price <= 0:
            continue
        code = code_by_element.get(element, -1)
        prior = prior_by_code.get(code)
        mean = position_means[position]
        if prior is None:
            rate = mean * 0.72
            availability = 0.68
            prior_class = "promoted_or_new_player_position_prior"
        else:
            equivalent_games = prior["appearances"]
            rate = (prior["points"] + mean * 6.0) / (equivalent_games + 6.0)
            availability = min(1.0, equivalent_games / 30.0)
            prior_class = "matched_completed_2024_25_player"
        expected_per_game = rate * (0.45 + 0.55 * availability)
        fixture_factor = 1.0 + (3.0 - difficulty[club_by_name[team_name]]) * 0.08
        six_week_score = round(expected_per_game * horizon * fixture_factor, 6)
        candidates.append(
            {
                "player_id": canonical_by_element[element],
                "fpl_element_id": element,
                "web_name": str(row["name"]),
                "position": position,
                "club_id": club_by_name[team_name],
                "club_name": team_name,
                "price": price,
                "selection_score": six_week_score,
                "prior_class": prior_class,
                "prior_rate_per_90": round(rate, 6),
                "availability_prior": round(availability, 6),
                "fixture_difficulty_mean_gw1_gw6": round(
                    difficulty[club_by_name[team_name]], 4
                ),
            }
        )
    candidates.sort(key=lambda row: str(row["player_id"]))
    if len(candidates) < 15:
        raise HistoricalSeedCounterfactualError("Launch candidate pool is incomplete")
    payload = {
        "schema_version": "1.0",
        "policy": "completed_2024_25_shrunk_rate_x_availability_x_gw1_6_fdr",
        "horizon_gameweeks": horizon,
        "candidate_count": len(candidates),
        "whitelisted_current_fields": ["name", "position", "team", "element", "value"],
        "predeadline_exclusions": PREDEADLINE_EXCLUSIONS,
        "explicitly_excluded_gw1_fields": [
            "xP",
            "minutes",
            "starts",
            "total_points",
            "goals_scored",
            "assists",
            "bonus",
            "bps",
            "selected",
            "transfers_in",
            "transfers_out",
        ],
        "source_files": {
            "gw1_launch_field_reconstruction": {
                "path": gw1_path.as_posix(),
                "sha256": _sha256(gw1_path),
            },
            "current_identity_bridge": {
                "path": current_players_path.as_posix(),
                "sha256": _sha256(current_players_path),
            },
            "completed_prior_season": {
                "path": previous_players_path.as_posix(),
                "sha256": _sha256(previous_players_path),
            },
            "canonical_identity_map": {
                "path": identity_map_path.as_posix(),
                "sha256": _sha256(identity_map_path),
            },
        },
        "limitations": [
            "retrospective_reconstruction_not_immutable_predeadline_capture",
            "current_players_export_used_only_as_element_to_stable_code_bridge",
            "predeadline_player_eligibility_not_a_complete_immutable_snapshot",
            "no_predeadline_injury_news_or_odds",
            "promoted_and_new_players_use_shrunk_position_prior",
            "exploratory_production_ineligible",
        ],
        "players": candidates,
    }
    payload["content_sha256"] = fingerprint(payload)
    return payload


def _valid_squad(rows: Iterable[Mapping[str, Any]]) -> bool:
    selected = list(rows)
    if Counter(str(row["position"]) for row in selected) != Counter(POSITION_COUNTS):
        return False
    if max(Counter(str(row["club_id"]) for row in selected).values()) > 3:
        return False
    return sum(float(row["price"]) for row in selected) <= 100.000001


def _initial_for_lambda(
    candidates: list[dict[str, Any]], price_penalty: float
) -> list[dict[str, Any]] | None:
    selected: list[dict[str, Any]] = []
    club_counts: Counter[str] = Counter()
    for position, required in POSITION_COUNTS.items():
        pool = sorted(
            (row for row in candidates if row["position"] == position),
            key=lambda row: (
                -(float(row["selection_score"]) - price_penalty * float(row["price"])),
                float(row["price"]),
                str(row["player_id"]),
            ),
        )
        for row in pool:
            if club_counts[str(row["club_id"])] >= 3:
                continue
            selected.append(row)
            club_counts[str(row["club_id"])] += 1
            if sum(item["position"] == position for item in selected) == required:
                break
    return selected if _valid_squad(selected) else None


def _improve_single_swaps(
    selected: list[dict[str, Any]], candidates: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    current = list(selected)
    while True:
        ids = {str(row["player_id"]) for row in current}
        current_cost = sum(float(row["price"]) for row in current)
        clubs = Counter(str(row["club_id"]) for row in current)
        best: tuple[float, float, str, str, dict[str, Any], dict[str, Any]] | None = None
        for outgoing in current:
            for incoming in candidates:
                if (
                    incoming["position"] != outgoing["position"]
                    or str(incoming["player_id"]) in ids
                ):
                    continue
                new_cost = current_cost - float(outgoing["price"]) + float(incoming["price"])
                if new_cost > 100.000001:
                    continue
                incoming_club = str(incoming["club_id"])
                outgoing_club = str(outgoing["club_id"])
                if incoming_club != outgoing_club and clubs[incoming_club] >= 3:
                    continue
                gain = float(incoming["selection_score"]) - float(
                    outgoing["selection_score"]
                )
                if gain <= 1e-9:
                    continue
                key = (
                    gain,
                    -new_cost,
                    str(outgoing["player_id"]),
                    str(incoming["player_id"]),
                    outgoing,
                    incoming,
                )
                if best is None or key[:4] > best[:4]:
                    best = key
        if best is None:
            return current
        current[current.index(best[4])] = best[5]


def select_squad(candidate_pool: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Deterministic Lagrangian starts followed by constraint-safe local search."""

    candidates = [dict(row) for row in candidate_pool["players"]]
    alternatives: list[list[dict[str, Any]]] = []
    for step in range(0, 401):
        initial = _initial_for_lambda(candidates, step / 100.0)
        if initial is not None:
            alternatives.append(_improve_single_swaps(initial, candidates))
    if not alternatives:
        raise HistoricalSeedCounterfactualError("No legal seed squad found")
    legal = [rows for rows in alternatives if _valid_squad(rows)]
    return max(
        legal,
        key=lambda rows: (
            sum(float(row["selection_score"]) for row in rows),
            -sum(float(row["price"]) for row in rows),
            tuple(sorted(str(row["player_id"]) for row in rows)),
        ),
    )


def _lineup(squad: list[dict[str, Any]]) -> dict[str, Any]:
    goalkeeper = max(
        (row for row in squad if row["position"] == "GKP"),
        key=lambda row: (row["selection_score"], row["player_id"]),
    )
    best: tuple[float, list[dict[str, Any]]] | None = None
    for formation in FORMATION_COUNTS:
        selected = [goalkeeper]
        for position, count in formation.items():
            selected.extend(
                sorted(
                    (row for row in squad if row["position"] == position),
                    key=lambda row: (-row["selection_score"], row["player_id"]),
                )[:count]
            )
        score = sum(float(row["selection_score"]) for row in selected)
        if best is None or score > best[0]:
            best = (score, selected)
    if best is None:
        raise HistoricalSeedCounterfactualError("No legal starting XI found")
    starters = best[1]
    starter_ids = {str(row["player_id"]) for row in starters}
    ranked = sorted(
        starters,
        key=lambda row: (-float(row["selection_score"]), str(row["player_id"])),
    )
    bench_goalkeeper = next(
        row
        for row in squad
        if row["position"] == "GKP" and str(row["player_id"]) not in starter_ids
    )
    bench_outfield = sorted(
        (
            row
            for row in squad
            if row["position"] != "GKP" and str(row["player_id"]) not in starter_ids
        ),
        key=lambda row: (-float(row["selection_score"]), str(row["player_id"])),
    )
    formation = Counter(row["position"] for row in starters)
    return {
        "starting_xi_ids": [str(row["player_id"]) for row in starters],
        "bench_ids": [str(bench_goalkeeper["player_id"])]
        + [str(row["player_id"]) for row in bench_outfield],
        "captain_id": str(ranked[0]["player_id"]),
        "vice_captain_id": str(ranked[1]["player_id"]),
        "active_chip": None,
        "formation": {
            position: int(formation[position]) for position in ("DEF", "MID", "FWD")
        },
    }


def build_counterfactual_seed(
    candidate_pool: Mapping[str, Any],
    control_seed: Mapping[str, Any],
) -> dict[str, Any]:
    selected = select_squad(candidate_pool)
    total_cost = round(sum(float(row["price"]) for row in selected), 1)
    plan = _lineup(selected)
    seed = deepcopy(dict(control_seed))
    seed.update(
        {
            "seed_id": "benchmark-v0-structured-prior-gw1-counterfactual",
            "seed_policy": "exploratory_reconstructed_structured_prior_v1",
            "bank": round(100.0 - total_cost, 1),
            "free_transfers": 0,
            "evidence": [
                {
                    "source_id": "frozen-local-completed-2024-25-plus-launch-fields",
                    "source_url": "local-reconstructed-inputs",
                    "title": "Structured prior seed counterfactual input bundle",
                    "published_at": "2025-08-15T17:29:59Z",
                    "use": "retrospective_field_whitelist_experiment",
                }
            ],
            "squad": [
                {
                    "player_id": str(row["player_id"]),
                    "fpl_element_id": int(row["fpl_element_id"]),
                    "web_name": str(row["web_name"]),
                    "position": str(row["position"]),
                    "club_id": str(row["club_id"]),
                    "purchase_price": float(row["price"]),
                    "current_price": float(row["price"]),
                    "selling_price": float(row["price"]),
                }
                for row in sorted(selected, key=lambda value: str(value["player_id"]))
            ],
            "initial_plan": {
                key: value for key, value in plan.items() if key != "formation"
            },
            "limitations": sorted(
                set(control_seed.get("limitations", []))
                | set(candidate_pool["limitations"])
                | {
                    "selection_uses_deterministic_local_search_not_global_milp_proof",
                    "not_a_2026_27_live_seed_policy",
                }
            ),
        }
    )
    seed["counterfactual_metadata"] = {
        "candidate_pool_sha256": str(candidate_pool["content_sha256"]),
        "selection_algorithm": "lagrangian_grid_plus_single_swap_local_search_v1",
        "selection_objective": round(
            sum(float(row["selection_score"]) for row in selected), 6
        ),
        "squad_cost": total_cost,
        "lineup": plan,
    }
    seed["content_sha256"] = fingerprint(seed)
    return seed


def decompose_seed_result(
    *,
    control_root: Path,
    branch_root: Path,
    stop_gameweek: int,
    branch_arm: str = "forecast_optimizer",
) -> dict[str, Any]:
    weeks: list[dict[str, Any]] = []
    for gameweek in range(1, stop_gameweek + 1):
        control = json.loads(
            (control_root / f"gw-{gameweek:02d}" / "run-summary.json").read_text(
                encoding="utf-8"
            )
        )
        branch = json.loads(
            (branch_root / f"gw-{gameweek:02d}" / "run-summary.json").read_text(
                encoding="utf-8"
            )
        )
        control_arm = control["arms"][branch_arm]
        branch_value = branch["arms"][branch_arm]
        weeks.append(
            {
                "gameweek": gameweek,
                "control_net_points": int(control_arm["net_points"]),
                "branch_net_points": int(branch_value["net_points"]),
                "weekly_delta": int(branch_value["net_points"])
                - int(control_arm["net_points"]),
                "control_cumulative": int(control_arm["cumulative_points"]),
                "branch_cumulative": int(branch_value["cumulative_points"]),
                "cumulative_delta": int(branch_value["cumulative_points"])
                - int(control_arm["cumulative_points"]),
                "control_transfers": int(control_arm["transfers"]),
                "branch_transfers": int(branch_value["transfers"]),
            }
        )
    result = {
        "schema_version": "1.0",
        "experiment": "historical_gw1_seed_counterfactual",
        "branch_arm": branch_arm,
        "stop_gameweek": stop_gameweek,
        "decomposition": {
            "gw1_initial_seed_realised_delta": weeks[0]["weekly_delta"],
            "gw2_to_stop_policy_and_carried_state_delta": sum(
                row["weekly_delta"] for row in weeks[1:]
            ),
            "total_delta": weeks[-1]["cumulative_delta"],
            "interpretation": (
                "GW1 isolates the different starting squad under its frozen lineup. "
                "GW2 onward combines carried seed state with the same deterministic "
                "weekly policy; it is not a pure seed-only causal effect."
            ),
        },
        "weeks": weeks,
        "limitations": [
            "exploratory_production_ineligible",
            "retrospective_launch_field_reconstruction",
            "one_realised_season_not_expected_value",
            "gw2_onward_contains_policy_by_state_interaction",
            "no_unstructured_predeadline_evidence_in_seed_policy",
        ],
    }
    result["content_sha256"] = fingerprint(result)
    return result
