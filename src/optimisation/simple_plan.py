"""Crude deterministic plan generator for the walking skeleton."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import pandas as pd

from src.scoring.validator import legal_formations, validate_lineup, validate_squad


def _rank_key(player: Mapping[str, Any]) -> tuple[float, str]:
    return (-float(player["expected_points"]), str(player["player_id"]))


def choose_starting_xi_rows(
    squad: Sequence[Mapping[str, Any]],
    *,
    formations: Sequence[Mapping[str, int]],
) -> dict[str, Any]:
    """Pick the highest-EP legal XI using only Python records."""
    ranked = sorted((dict(player) for player in squad), key=_rank_key)
    goalkeepers = [player for player in ranked if player["position"] == "GKP"]
    if not goalkeepers:
        raise ValueError("Squad has no goalkeeper")

    best: dict[str, Any] | None = None
    best_score = float("-inf")
    for source_formation in formations:
        formation = {
            position: int(source_formation[position])
            for position in ("DEF", "MID", "FWD")
        }
        selected = [goalkeepers[0]]
        used = {str(goalkeepers[0]["player_id"])}
        for position, count in formation.items():
            pool = [
                player
                for player in ranked
                if player["position"] == position
                and str(player["player_id"]) not in used
            ]
            if len(pool) < count:
                break
            for player in pool[:count]:
                selected.append(player)
                used.add(str(player["player_id"]))
        else:
            captain_order = sorted(selected, key=_rank_key)
            score = sum(float(player["expected_points"]) for player in selected)
            score += float(captain_order[0]["expected_points"])
            if score > best_score:
                best_score = score
                bench_pool = [
                    player
                    for player in ranked
                    if str(player["player_id"]) not in used
                ]
                bench_gkp = [
                    player for player in bench_pool if player["position"] == "GKP"
                ][:1]
                bench_out = [
                    player for player in bench_pool if player["position"] != "GKP"
                ][:3]
                best = {
                    "formation": formation,
                    "starting_xi": selected,
                    "bench": bench_gkp + bench_out,
                    "captain_id": str(captain_order[0]["player_id"]),
                    "vice_captain_id": str(captain_order[1]["player_id"]),
                    "expected_xi_points": round(score, 2),
                }
    if best is None:
        raise ValueError("No legal formation could be built from squad")
    return best


def choose_starting_xi(
    squad: pd.DataFrame,
    *,
    rules: Mapping[str, Any],
) -> dict[str, Any]:
    """Compatibility wrapper around the pure-data selector."""
    return choose_starting_xi_rows(
        squad.to_dict(orient="records"),
        formations=legal_formations(dict(rules)),
    )


def choose_starting_xi_reference(
    squad: pd.DataFrame,
    *,
    rules: Mapping[str, Any],
) -> dict[str, Any]:
    """Independent pandas reference retained for differential tests."""
    ranked = squad.copy()
    ranked["player_id"] = ranked["player_id"].astype(str)
    ranked = ranked.sort_values(
        ["expected_points", "player_id"],
        ascending=[False, True],
        kind="mergesort",
    )
    goalkeepers = ranked[ranked["position"] == "GKP"].head(1)
    if goalkeepers.empty:
        raise ValueError("Squad has no goalkeeper")
    best: dict[str, Any] | None = None
    best_score = float("-inf")
    for formation in legal_formations(dict(rules)):
        selected = [goalkeepers.iloc[0]]
        used = {str(goalkeepers.iloc[0]["player_id"])}
        for position, count in formation.items():
            pool = ranked[
                (ranked["position"] == position)
                & ~ranked["player_id"].isin(used)
            ]
            if len(pool) < count:
                break
            for _, row in pool.head(count).iterrows():
                selected.append(row)
                used.add(str(row["player_id"]))
        else:
            xi = pd.DataFrame(selected)
            captain_order = xi.sort_values(
                ["expected_points", "player_id"],
                ascending=[False, True],
                kind="mergesort",
            )
            score = float(
                xi["expected_points"].sum()
                + captain_order.iloc[0]["expected_points"]
            )
            if score > best_score:
                best_score = score
                bench_pool = ranked[~ranked["player_id"].isin(used)]
                bench = pd.concat(
                    [
                        bench_pool[bench_pool["position"] == "GKP"].head(1),
                        bench_pool[bench_pool["position"] != "GKP"].head(3),
                    ],
                    ignore_index=True,
                )
                best = {
                    "formation": dict(formation),
                    "starting_xi": xi.to_dict(orient="records"),
                    "bench": bench.to_dict(orient="records"),
                    "captain_id": str(captain_order.iloc[0]["player_id"]),
                    "vice_captain_id": str(captain_order.iloc[1]["player_id"]),
                    "expected_xi_points": round(score, 2),
                }
    if best is None:
        raise ValueError("No legal formation could be built from squad")
    return best


def no_transfer_plan(
    squad_players: list[dict[str, Any]],
    projected: pd.DataFrame,
    *,
    rules: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate current squad and emit a no-transfer lineup plan."""
    squad_df = projected[projected["player_id"].isin([str(p["player_id"]) for p in squad_players])].copy()
    # Ensure purchase_price present for validation
    purchase = {str(p["player_id"]): p.get("purchase_price", p.get("now_cost")) for p in squad_players}
    club = {str(p["player_id"]): p["club_id"] for p in squad_players}
    squad_df["purchase_price"] = squad_df["player_id"].map(purchase)
    squad_df["club_id"] = squad_df["player_id"].map(club)

    squad_result = validate_squad(
        squad_df.to_dict(orient="records"), rules=dict(rules)
    )
    plan = choose_starting_xi(squad_df, rules=rules)
    lineup_result = validate_lineup(
        plan["starting_xi"],
        plan["bench"],
        captain_id=plan["captain_id"],
        vice_captain_id=plan["vice_captain_id"],
        rules=dict(rules),
    )
    return {
        "strategy": "no_transfer",
        "transfers": [],
        "hit_cost": 0,
        "lineup": plan,
        "validation": {
            "squad": squad_result.as_dict(),
            "lineup": lineup_result.as_dict(),
        },
    }
