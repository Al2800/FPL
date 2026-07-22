"""Crude deterministic plan generator for the walking skeleton."""

from __future__ import annotations

from typing import Any

import pandas as pd

from src.scoring.validator import legal_formations, validate_lineup, validate_squad


def choose_starting_xi(squad: pd.DataFrame) -> dict[str, Any]:
    """Pick a legal XI maximising sum of expected_points; captain = highest EP in XI."""
    ranked = squad.sort_values("expected_points", ascending=False)
    gkp = ranked[ranked["position"] == "GKP"].head(1)
    if gkp.empty:
        raise ValueError("Squad has no goalkeeper")

    best: dict[str, Any] | None = None
    best_score = float("-inf")

    for formation in legal_formations():
        selected = [gkp.iloc[0]]
        used = {gkp.iloc[0]["player_id"]}
        ok = True
        for pos, n in formation.items():
            pool = ranked[(ranked["position"] == pos) & ~ranked["player_id"].isin(used)]
            if len(pool) < n:
                ok = False
                break
            for _, row in pool.head(n).iterrows():
                selected.append(row)
                used.add(row["player_id"])
        if not ok:
            continue
        xi = pd.DataFrame(selected)
        score = float(xi["expected_points"].sum() + xi["expected_points"].max())  # captain doubles top
        if score > best_score:
            best_score = score
            captain = xi.sort_values("expected_points", ascending=False).iloc[0]
            vice = xi.sort_values("expected_points", ascending=False).iloc[1]
            bench_pool = ranked[~ranked["player_id"].isin(used)]
            # Bench: remaining GKP first, then by EP
            bench_gkp = bench_pool[bench_pool["position"] == "GKP"].head(1)
            bench_out = bench_pool[bench_pool["position"] != "GKP"].head(3)
            bench = pd.concat([bench_gkp, bench_out], ignore_index=True)
            best = {
                "formation": formation,
                "starting_xi": xi.to_dict(orient="records"),
                "bench": bench.to_dict(orient="records"),
                "captain_id": str(captain["player_id"]),
                "vice_captain_id": str(vice["player_id"]),
                "expected_xi_points": round(score, 2),
            }
    if best is None:
        raise ValueError("No legal formation could be built from squad")
    return best


def no_transfer_plan(squad_players: list[dict[str, Any]], projected: pd.DataFrame) -> dict[str, Any]:
    """Validate current squad and emit a no-transfer lineup plan."""
    squad_df = projected[projected["player_id"].isin([str(p["player_id"]) for p in squad_players])].copy()
    # Ensure purchase_price present for validation
    purchase = {str(p["player_id"]): p.get("purchase_price", p.get("now_cost")) for p in squad_players}
    club = {str(p["player_id"]): p["club_id"] for p in squad_players}
    squad_df["purchase_price"] = squad_df["player_id"].map(purchase)
    squad_df["club_id"] = squad_df["player_id"].map(club)

    squad_result = validate_squad(squad_df.to_dict(orient="records"))
    plan = choose_starting_xi(squad_df)
    lineup_result = validate_lineup(
        plan["starting_xi"],
        plan["bench"],
        captain_id=plan["captain_id"],
        vice_captain_id=plan["vice_captain_id"],
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
