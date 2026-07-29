"""Expected planning value for legal FPL squad contingencies."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from copy import deepcopy
from functools import lru_cache
from itertools import combinations, permutations, product
from typing import Any

from src.forecasting.appearance_distribution import (
    AppearanceDistribution,
    distribution_for_player,
)


class SquadContingencyError(ValueError):
    """Raised when contingency planning inputs are incomplete or invalid."""


POSITIONS = ("DEF", "MID", "FWD")


def _rank_key(player: Mapping[str, Any]) -> tuple[float, str]:
    return (-float(player["expected_points"]), str(player["player_id"]))


def _missing_count_distribution(
    starters: Sequence[Mapping[str, Any]],
    appearances: Mapping[str, AppearanceDistribution],
) -> dict[tuple[int, int, int], float]:
    states: dict[tuple[int, int, int], float] = {(0, 0, 0): 1.0}
    position_index = {position: index for index, position in enumerate(POSITIONS)}
    for player in starters:
        position = str(player["position"])
        if position == "GKP":
            continue
        probability_zero = appearances[str(player["player_id"])].zero
        index = position_index[position]
        updated: dict[tuple[int, int, int], float] = defaultdict(float)
        for counts, probability in states.items():
            updated[counts] += probability * (1.0 - probability_zero)
            missing = list(counts)
            missing[index] += 1
            updated[tuple(missing)] += probability * probability_zero
        states = dict(updated)
    return states


def _formation_valid(counts: Mapping[str, int], constraints: Mapping[str, Any]) -> bool:
    return all(
        int(bounds["min"]) <= int(counts.get(position, 0)) <= int(bounds["max"])
        for position, bounds in constraints.items()
    )


def _subset_can_legally_replace(
    *,
    formation: Mapping[str, int],
    missing: tuple[int, int, int],
    bench_positions: Sequence[str],
    constraints: Mapping[str, Any],
) -> bool:
    if len(bench_positions) > sum(missing):
        return False
    missing_slots = [
        position
        for position, count in zip(POSITIONS, missing, strict=True)
        for _ in range(count)
    ]
    for slots in permutations(missing_slots, len(bench_positions)):
        counts = {position: int(value) for position, value in formation.items()}
        counts["GKP"] = 1
        for removed, added in zip(slots, bench_positions, strict=True):
            counts[removed] -= 1
            counts[added] = counts.get(added, 0) + 1
        if _formation_valid(counts, constraints):
            return True
    return False


@lru_cache(maxsize=4096)
def _selected_bench_indices_cached(
    formation_items: tuple[tuple[str, int], ...],
    missing: tuple[int, int, int],
    bench_positions: tuple[str, ...],
    appeared: tuple[bool, ...],
    constraint_items: tuple[tuple[str, int, int], ...],
) -> tuple[int, ...]:
    formation = dict(formation_items)
    constraints = {
        position: {"min": minimum, "max": maximum}
        for position, minimum, maximum in constraint_items
    }
    available = [index for index, value in enumerate(appeared) if value]
    feasible: list[tuple[int, ...]] = []
    for count in range(min(sum(missing), len(available)) + 1):
        for subset in combinations(available, count):
            positions = [bench_positions[index] for index in subset]
            if _subset_can_legally_replace(
                formation=formation,
                missing=missing,
                bench_positions=positions,
                constraints=constraints,
            ):
                feasible.append(subset)
    if not feasible:
        return ()
    return min(
        feasible,
        key=lambda subset: (
            -len(subset),
            tuple(0 if index in subset else 1 for index in range(len(bench_positions))),
        ),
    )


def _selected_bench_indices(
    *,
    formation: Mapping[str, int],
    missing: tuple[int, int, int],
    bench: Sequence[Mapping[str, Any]],
    appeared: Sequence[bool],
    constraints: Mapping[str, Any],
) -> tuple[int, ...]:
    return _selected_bench_indices_cached(
        tuple(sorted((str(key), int(value)) for key, value in formation.items())),
        missing,
        tuple(str(player["position"]) for player in bench),
        tuple(bool(value) for value in appeared),
        tuple(
            sorted(
                (
                    str(position),
                    int(bounds["min"]),
                    int(bounds["max"]),
                )
                for position, bounds in constraints.items()
            )
        ),
    )


@lru_cache(maxsize=4096)
def _substitution_lookup(
    formation_items: tuple[tuple[str, int], ...],
    bench_positions: tuple[str, ...],
    constraint_items: tuple[tuple[str, int, int], ...],
) -> dict[tuple[tuple[int, int, int], tuple[bool, ...]], tuple[int, ...]]:
    formation = dict(formation_items)
    bench = [{"position": position} for position in bench_positions]
    constraints = {
        position: {"min": minimum, "max": maximum}
        for position, minimum, maximum in constraint_items
    }
    lookup: dict[
        tuple[tuple[int, int, int], tuple[bool, ...]], tuple[int, ...]
    ] = {}
    for missing in product(
        range(formation["DEF"] + 1),
        range(formation["MID"] + 1),
        range(formation["FWD"] + 1),
    ):
        for appeared in product((False, True), repeat=len(bench_positions)):
            lookup[(missing, appeared)] = _selected_bench_indices(
                formation=formation,
                missing=missing,
                bench=bench,
                appeared=appeared,
                constraints=constraints,
            )
    return lookup


def expected_auto_sub_points(
    *,
    starting_xi: Sequence[Mapping[str, Any]],
    bench: Sequence[Mapping[str, Any]],
    appearances: Mapping[str, AppearanceDistribution],
    formation: Mapping[str, int],
    constraints: Mapping[str, Any],
    missing_states: Mapping[tuple[int, int, int], float] | None = None,
) -> dict[str, Any]:
    """Return expected goalkeeper and formation-valid outfield bench points."""

    starter_gkp = next(player for player in starting_xi if player["position"] == "GKP")
    bench_gkp = next(player for player in bench if player["position"] == "GKP")
    goalkeeper_points = (
        appearances[str(starter_gkp["player_id"])].zero
        * float(bench_gkp["expected_points"])
    )

    outfield_bench = [player for player in bench if player["position"] != "GKP"]
    states = (
        dict(missing_states)
        if missing_states is not None
        else _missing_count_distribution(starting_xi, appearances)
    )
    formation_items = tuple(
        sorted((str(key), int(value)) for key, value in formation.items())
    )
    bench_positions = tuple(str(player["position"]) for player in outfield_bench)
    constraint_items = tuple(
        sorted(
            (str(position), int(bounds["min"]), int(bounds["max"]))
            for position, bounds in constraints.items()
        )
    )
    substitution_lookup = _substitution_lookup(
        formation_items, bench_positions, constraint_items
    )
    outfield_points = 0.0
    selection_probability = {
        str(player["player_id"]): 0.0 for player in outfield_bench
    }
    zero_probs = [
        appearances[str(player["player_id"])].zero for player in outfield_bench
    ]
    appear_probs = [
        appearances[str(player["player_id"])].appears for player in outfield_bench
    ]
    expected_points = [
        float(player["expected_points"]) for player in outfield_bench
    ]
    player_ids = [str(player["player_id"]) for player in outfield_bench]
    conditional_points = [
        (points / appears) if appears > 0.0 else 0.0
        for points, appears in zip(expected_points, appear_probs, strict=True)
    ]
    for missing, missing_probability in states.items():
        for appeared in product((False, True), repeat=len(outfield_bench)):
            scenario_probability = missing_probability
            for index, did_appear in enumerate(appeared):
                scenario_probability *= (
                    appear_probs[index] if did_appear else zero_probs[index]
                )
                if scenario_probability == 0.0:
                    break
            if scenario_probability == 0.0:
                continue
            selected = substitution_lookup[(missing, appeared)]
            for index in selected:
                outfield_points += scenario_probability * conditional_points[index]
                selection_probability[player_ids[index]] += scenario_probability
    return {
        "goalkeeper": round(goalkeeper_points, 6),
        "outfield": round(outfield_points, 6),
        "total": round(goalkeeper_points + outfield_points, 6),
        "outfield_selection_probability": {
            player_id: round(probability, 6)
            for player_id, probability in selection_probability.items()
        },
    }


def _best_captain_pair(
    starting_xi: Sequence[Mapping[str, Any]],
    appearances: Mapping[str, AppearanceDistribution],
    *,
    extra_multiplier: int,
) -> tuple[str, str, float, float]:
    best: tuple[tuple[float, str, str], str, str, float, float] | None = None
    for captain in starting_xi:
        captain_id = str(captain["player_id"])
        captain_points = float(captain["expected_points"])
        for vice in starting_xi:
            vice_id = str(vice["player_id"])
            if vice_id == captain_id:
                continue
            fallback = (
                appearances[captain_id].zero * float(vice["expected_points"])
            )
            extra = extra_multiplier * (captain_points + fallback)
            key = (-extra, captain_id, vice_id)
            candidate = (key, captain_id, vice_id, extra, fallback)
            if best is None or candidate[0] < best[0]:
                best = candidate
    if best is None:
        raise SquadContingencyError("A captain and vice-captain could not be selected")
    return best[1], best[2], best[3], best[4]


def evaluate_contingency_lineup(
    *,
    starting_xi: Sequence[Mapping[str, Any]],
    bench: Sequence[Mapping[str, Any]],
    formation: Mapping[str, int],
    calibration: Mapping[str, Any],
    constraints: Mapping[str, Any],
    active_chip: str | None,
    appearance_distributions: Mapping[str, AppearanceDistribution] | None = None,
    missing_states: Mapping[tuple[int, int, int], float] | None = None,
) -> dict[str, Any]:
    """Return an auditable expected-value decomposition for one legal lineup."""

    players = list(starting_xi) + list(bench)
    appearances = (
        dict(appearance_distributions)
        if appearance_distributions is not None
        else {
            str(player["player_id"]): distribution_for_player(player, calibration)
            for player in players
        }
    )
    triple = bool(active_chip and "triple_captain" in active_chip)
    bench_boost = bool(active_chip and "bench_boost" in active_chip)
    extra_multiplier = 2 if triple else 1
    captain_id, vice_id, captain_extra, vice_fallback = _best_captain_pair(
        starting_xi, appearances, extra_multiplier=extra_multiplier
    )
    xi_points = sum(float(player["expected_points"]) for player in starting_xi)
    if bench_boost:
        bench_value = sum(float(player["expected_points"]) for player in bench)
        auto_sub = {
            "goalkeeper": 0.0,
            "outfield": 0.0,
            "total": 0.0,
            "outfield_selection_probability": {},
        }
    else:
        auto_sub = expected_auto_sub_points(
            starting_xi=starting_xi,
            bench=bench,
            appearances=appearances,
            formation=formation,
            constraints=constraints,
            missing_states=missing_states,
        )
        bench_value = float(auto_sub["total"])
    total = xi_points + captain_extra + bench_value
    return {
        "planning_value": round(total, 6),
        "xi_expected_points": round(xi_points, 6),
        "captain_extra": round(captain_extra, 6),
        "vice_fallback_component": round(
            extra_multiplier * vice_fallback, 6
        ),
        "bench_contingency_value": round(bench_value, 6),
        "auto_sub": auto_sub,
        "captain_id": captain_id,
        "vice_captain_id": vice_id,
        "appearance_distributions": {
            player_id: distribution.as_dict()
            for player_id, distribution in sorted(appearances.items())
        },
        "active_chip": active_chip,
    }


def choose_contingency_lineup(
    squad: Sequence[Mapping[str, Any]],
    *,
    formations: Sequence[Mapping[str, int]],
    calibration: Mapping[str, Any],
    constraints: Mapping[str, Any],
    active_chip: str | None,
    lineup_cache: dict[tuple[Any, ...], dict[str, Any]] | None = None,
    evaluation_cache: dict[tuple[Any, ...], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Choose formation, ordered bench and captain pair by contingency value."""

    ranked = sorted((dict(player) for player in squad), key=_rank_key)
    cache_key: tuple[Any, ...] | None = None
    if lineup_cache is not None:
        appearance_items: list[tuple[Any, ...]] = []
        for player in ranked:
            player_id = str(player["player_id"])
            explicit = player.get("appearance_distribution")
            if explicit is not None:
                appearance_items.append(
                    (
                        player_id,
                        float(player["expected_points"]),
                        str(player["position"]),
                        round(float(explicit["zero"]), 8),
                        round(float(explicit["under_60"]), 8),
                        round(float(explicit["60_plus"]), 8),
                    )
                )
            else:
                appearance_items.append(
                    (
                        player_id,
                        float(player["expected_points"]),
                        str(player["position"]),
                        round(float(player["start_probability"]), 8),
                        int(player.get("fixture_count", 1)),
                    )
                )
        cache_key = (
            tuple(appearance_items),
            active_chip,
            str(calibration.get("content_sha256")),
            tuple(
                tuple(sorted((str(k), int(v)) for k, v in formation.items()))
                for formation in formations
            ),
            tuple(
                sorted(
                    (str(position), int(bounds["min"]), int(bounds["max"]))
                    for position, bounds in constraints.items()
                )
            ),
        )
        cached = lineup_cache.get(cache_key)
        if cached is not None:
            return deepcopy(cached)

    goalkeepers = [player for player in ranked if player["position"] == "GKP"]
    if len(goalkeepers) != 2:
        raise SquadContingencyError("Squad must contain two goalkeepers")
    appearances = {
        str(player["player_id"]): distribution_for_player(player, calibration)
        for player in ranked
    }

    def player_token(player: Mapping[str, Any]) -> tuple[Any, ...]:
        player_id = str(player["player_id"])
        distribution = appearances[player_id]
        return (
            player_id,
            float(player["expected_points"]),
            str(player["position"]),
            round(distribution.zero, 8),
            round(distribution.under_60, 8),
            round(distribution.sixty_plus, 8),
        )

    best: tuple[tuple[float, tuple[str, ...], str, str], dict[str, Any]] | None = None
    best_value = float("-inf")
    for source_formation in formations:
        formation = {
            position: int(source_formation[position]) for position in POSITIONS
        }
        starting = [goalkeepers[0]]
        for position, count in formation.items():
            starting.extend(
                [player for player in ranked if player["position"] == position][
                    :count
                ]
            )
        if len(starting) != 11:
            continue
        used = {str(player["player_id"]) for player in starting}
        bench_pool = [
            player for player in ranked if str(player["player_id"]) not in used
        ]
        bench_gkp = next(
            player for player in bench_pool if player["position"] == "GKP"
        )
        outfield = [player for player in bench_pool if player["position"] != "GKP"]
        xi_points = sum(float(player["expected_points"]) for player in starting)
        _, _, captain_extra_bound, _ = _best_captain_pair(
            starting, appearances, extra_multiplier=(
                2 if active_chip and "triple_captain" in active_chip else 1
            )
        )
        if active_chip and "bench_boost" in active_chip:
            bench_upper = sum(float(player["expected_points"]) for player in bench_pool)
        else:
            # Optimistic: every remaining outfielder and the bench keeper can contribute
            # their full expected points through auto-subs.
            bench_upper = sum(float(player["expected_points"]) for player in bench_pool)
        upper_bound = xi_points + captain_extra_bound + bench_upper
        if best is not None and upper_bound < best_value - 1e-12:
            continue
        # Shared across every bench permutation of this starting XI.
        missing_states = _missing_count_distribution(starting, appearances)
        for ordered_outfield in permutations(outfield):
            ordered_bench = [bench_gkp, *ordered_outfield]
            evaluation_key = None
            if evaluation_cache is not None:
                evaluation_key = (
                    tuple(sorted((str(k), int(v)) for k, v in formation.items())),
                    tuple(player_token(player) for player in starting),
                    tuple(player_token(player) for player in ordered_bench),
                    active_chip,
                )
                cached_evaluation = evaluation_cache.get(evaluation_key)
                if cached_evaluation is not None:
                    evaluation = cached_evaluation
                else:
                    evaluation = evaluate_contingency_lineup(
                        starting_xi=starting,
                        bench=ordered_bench,
                        formation=formation,
                        calibration=calibration,
                        constraints=constraints,
                        active_chip=active_chip,
                        appearance_distributions=appearances,
                        missing_states=missing_states,
                    )
                    evaluation_cache[evaluation_key] = evaluation
            else:
                evaluation = evaluate_contingency_lineup(
                    starting_xi=starting,
                    bench=ordered_bench,
                    formation=formation,
                    calibration=calibration,
                    constraints=constraints,
                    active_chip=active_chip,
                    appearance_distributions=appearances,
                    missing_states=missing_states,
                )
            identity = tuple(
                str(player["player_id"]) for player in [*starting, *ordered_bench]
            )
            planning_value = float(evaluation["planning_value"])
            key = (
                -planning_value,
                identity,
                str(evaluation["captain_id"]),
                str(evaluation["vice_captain_id"]),
            )
            result = {
                "formation": formation,
                "starting_xi": starting,
                "bench": ordered_bench,
                "captain_id": evaluation["captain_id"],
                "vice_captain_id": evaluation["vice_captain_id"],
                "expected_xi_points": round(planning_value, 2),
                "contingency": evaluation,
            }
            if best is None or key < best[0]:
                best = (key, result)
                best_value = planning_value
    if best is None:
        raise SquadContingencyError("No legal contingency lineup could be built")
    if lineup_cache is not None and cache_key is not None:
        lineup_cache[cache_key] = deepcopy(best[1])
    return best[1]
