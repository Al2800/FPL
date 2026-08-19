"""Five GW1 elevation-path squads and same-packet host scoring.

Paths A and B are the frozen weekly-2026-08-11 optimiser arms. Paths C–E
are declared alternatives. Official FPL player IDs are from the 19 August
2026 bootstrap; A/B IDs also match the committed 11 August recommendation.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from src.optimisation.initial_squad import (
    InitialSquadError,
    score_declared_initial_squad,
)
from src.scoring.validator import validate_lineup, validate_squad

# Club IDs from the weekly-2026-08-11 recommendation (FPL bootstrap order).
CLUB = {
    "ARS": "1",
    "AVL": "2",
    "BOU": "3",
    "BRE": "4",
    "BHA": "5",
    "CHE": "6",
    "COV": "7",
    "CRY": "8",
    "EVE": "9",
    "IPS": "12",
    "LEE": "13",
    "LIV": "14",
    "MCI": "15",
    "MUN": "16",
    "NFO": "18",
    "TOT": "19",
    "SUN": "20",
}

ARM_MODES = ("robust", "deterministic", "human_reference")


def P(player_id: str, name: str, pos: str, club: str, cost: float) -> dict[str, Any]:
    return {
        "player_id": str(player_id),
        "web_name": name,
        "position": pos,
        "club_id": CLUB[club],
        "club": club,
        "purchase_price": cost,
        "now_cost": cost,
    }


PLAYERS = {
    "Raya": P("1", "Raya", "GKP", "ARS", 6.0),
    "Donnarumma": P("384", "Donnarumma", "GKP", "MCI", 5.5),
    "Verbruggen": P("109", "Verbruggen", "GKP", "BHA", 4.5),
    "Dubravka": P("497", "Dubravka", "GKP", "TOT", 4.0),
    "Kinsky": P("496", "Kinsky", "GKP", "TOT", 4.5),
    "Mitchell": P("204", "Mitchell", "DEF", "CRY", 4.5),
    "Tarkowski": P("229", "Tarkowski", "DEF", "EVE", 6.0),
    "Virgil": P("356", "Virgil", "DEF", "LIV", 6.5),
    "Matheus N.": P("389", "Matheus N.", "DEF", "MCI", 6.0),
    "Truffert": P("61", "Truffert", "DEF", "BOU", 5.5),
    "Van Hecke": P("112", "Van Hecke", "DEF", "TOT", 5.0),
    "Shaw": P("423", "Shaw", "DEF", "MUN", 4.5),
    "Diop": P("259", "Diop", "DEF", "IPS", 4.0),
    "van Ewijk": P("175", "van Ewijk", "DEF", "COV", 4.0),
    "Calafiori": P("8", "Calafiori", "DEF", "ARS", 5.5),
    "Wilson": P("260", "Wilson", "MID", "LEE", 6.5),
    "Semenyo": P("397", "Semenyo", "MID", "MCI", 8.5),
    "B.Fernandes": P("426", "B.Fernandes", "MID", "MUN", 12.0),
    "Gibbs-White": P("480", "Gibbs-White", "MID", "NFO", 8.0),
    "E.Le Fée": P("542", "E.Le Fée", "MID", "SUN", 6.0),
    "Xhaka": P("544", "Xhaka", "MID", "SUN", 5.5),
    "João Pedro": P("165", "João Pedro", "FWD", "CHE", 7.5),
    "Beto": P("248", "Beto", "FWD", "EVE", 5.5),
    "Calvert-Lewin": P("346", "Calvert-Lewin", "FWD", "LEE", 6.0),
    "Thiago": P("106", "Thiago", "FWD", "BRE", 8.0),
    "Obi": P("441", "Obi", "FWD", "MUN", 4.5),
    "Haaland": P("411", "Haaland", "FWD", "MCI", 15.5),
}


PATHS: list[dict[str, Any]] = [
    {
        "path_id": "A-tight-ep-robust",
        "title": "Tight expected points (robust optimiser)",
        "elevation": "uncertainty-penalised six-GW EP; high start_p; no Haaland",
        "published_objective": 240.724705,
        "published_proposal_sha256": (
            "eafe0eda68a68456a5ff91fd91548a2f21673bbe52a393da80dd3c99480f7b0d"
        ),
        "squad": [
            "Raya",
            "Donnarumma",
            "Van Hecke",
            "Mitchell",
            "Tarkowski",
            "Virgil",
            "Truffert",
            "Wilson",
            "Semenyo",
            "B.Fernandes",
            "Gibbs-White",
            "E.Le Fée",
            "Thiago",
            "João Pedro",
            "Obi",
        ],
        "xi": [
            "Raya",
            "Tarkowski",
            "Virgil",
            "Van Hecke",
            "B.Fernandes",
            "Gibbs-White",
            "Semenyo",
            "E.Le Fée",
            "Wilson",
            "Thiago",
            "João Pedro",
        ],
        "bench": ["Donnarumma", "Mitchell", "Truffert", "Obi"],
        "captain": "B.Fernandes",
        "vice": "Semenyo",
        "chip": "none — hold; BB later only if bench is playing",
    },
    {
        "path_id": "B-loose-ep-deterministic",
        "title": "Loose expected points (deterministic optimiser)",
        "elevation": "raw point forecast; still no Haaland; City via Semenyo + Nunes",
        "published_objective": 244.244457,
        "published_proposal_sha256": (
            "56c936de5ccb0d1934c01485dccc92da2ca33bd9cfc5aa7f1c675473327cd4e4"
        ),
        "squad": [
            "Raya",
            "Donnarumma",
            "Mitchell",
            "Tarkowski",
            "Virgil",
            "Matheus N.",
            "Truffert",
            "Wilson",
            "Semenyo",
            "B.Fernandes",
            "Gibbs-White",
            "E.Le Fée",
            "João Pedro",
            "Beto",
            "Calvert-Lewin",
        ],
        "xi": [
            "Raya",
            "Tarkowski",
            "Virgil",
            "Matheus N.",
            "B.Fernandes",
            "Gibbs-White",
            "Semenyo",
            "E.Le Fée",
            "Wilson",
            "João Pedro",
            "Calvert-Lewin",
        ],
        "bench": ["Donnarumma", "Mitchell", "Truffert", "Beto"],
        "captain": "B.Fernandes",
        "vice": "Semenyo",
        "chip": "none — hold; Matheus N. is now bootstrap doubtful",
    },
    {
        "path_id": "C-premium-override-advisory",
        "title": "Premium override (current advisory)",
        "elevation": "accept ~25 packet-EV haircut to own Haaland + Bruno",
        "published_objective": 215.705381,
        "published_objective_note": "12 Aug host rescore in robust mode vs 240.72",
        "published_proposal_sha256": None,
        "squad": [
            "Verbruggen",
            "Dubravka",
            "Van Hecke",
            "Mitchell",
            "Shaw",
            "Diop",
            "van Ewijk",
            "B.Fernandes",
            "Gibbs-White",
            "E.Le Fée",
            "Wilson",
            "Xhaka",
            "Haaland",
            "João Pedro",
            "Thiago",
        ],
        "xi": [
            "Verbruggen",
            "Van Hecke",
            "Mitchell",
            "Shaw",
            "B.Fernandes",
            "Gibbs-White",
            "E.Le Fée",
            "Wilson",
            "Haaland",
            "João Pedro",
            "Thiago",
        ],
        "bench": ["Dubravka", "Xhaka", "Diop", "van Ewijk"],
        "captain": "B.Fernandes",
        "vice": "Haaland",
        "chip": "none — BB blocked by Diop/van Ewijk",
    },
    {
        "path_id": "D-death-zone-playing-15",
        "title": "Death-zone spine (mid-price engine + playing bench)",
        "elevation": "lean into £6.5–8.5 attackers; no Haaland; no £4.0 lottery",
        "published_objective": None,
        "squad": [
            "Verbruggen",
            "Kinsky",
            "Van Hecke",
            "Shaw",
            "Tarkowski",
            "Truffert",
            "Calafiori",
            "B.Fernandes",
            "Semenyo",
            "Gibbs-White",
            "E.Le Fée",
            "Wilson",
            "João Pedro",
            "Thiago",
            "Calvert-Lewin",
        ],
        "xi": [
            "Verbruggen",
            "Van Hecke",
            "Tarkowski",
            "Calafiori",
            "B.Fernandes",
            "Semenyo",
            "Gibbs-White",
            "E.Le Fée",
            "Wilson",
            "João Pedro",
            "Thiago",
        ],
        "bench": ["Kinsky", "Shaw", "Truffert", "Calvert-Lewin"],
        "captain": "B.Fernandes",
        "vice": "Semenyo",
        "chip": "BB1 is discussable only after official Spurs/Leeds/Arsenal XIs",
    },
    {
        "path_id": "E-minutes-first",
        "title": "Minutes-first (start-probability over upside)",
        "elevation": "maximise likely starters; drop Wilson/Obi/Haaland rust and promoted lottery",
        "published_objective": None,
        "squad": [
            "Raya",
            "Donnarumma",
            "Virgil",
            "Van Hecke",
            "Truffert",
            "Shaw",
            "Mitchell",
            "B.Fernandes",
            "Semenyo",
            "Gibbs-White",
            "E.Le Fée",
            "Xhaka",
            "Thiago",
            "João Pedro",
            "Calvert-Lewin",
        ],
        "xi": [
            "Raya",
            "Virgil",
            "Van Hecke",
            "Shaw",
            "B.Fernandes",
            "Semenyo",
            "Gibbs-White",
            "E.Le Fée",
            "Xhaka",
            "Thiago",
            "João Pedro",
        ],
        "bench": ["Donnarumma", "Mitchell", "Truffert", "Calvert-Lewin"],
        "captain": "B.Fernandes",
        "vice": "Semenyo",
        "chip": "none — bench is more playable than C but not a default BB1",
    },
]


def materialise(names: Sequence[str]) -> list[dict[str, Any]]:
    return [PLAYERS[name] for name in names]


def path_player_ids(path: Mapping[str, Any]) -> list[str]:
    return [str(PLAYERS[name]["player_id"]) for name in path["squad"]]


def validate_path_rules(path: Mapping[str, Any], *, rules: Mapping[str, Any]) -> dict[str, Any]:
    squad = materialise(path["squad"])
    xi = materialise(path["xi"])
    bench = materialise(path["bench"])
    spent = round(sum(float(player["now_cost"]) for player in squad), 1)
    bank = round(100.0 - spent, 1)
    squad_v = validate_squad(squad, bank=bank, rules=rules)
    lineup_v = validate_lineup(
        xi,
        bench,
        captain_id=PLAYERS[path["captain"]]["player_id"],
        vice_captain_id=PLAYERS[path["vice"]]["player_id"],
        rules=rules,
    )
    clubs: dict[str, int] = {}
    for player in squad:
        clubs[str(player["club"])] = clubs.get(str(player["club"]), 0) + 1
    return {
        "path_id": path["path_id"],
        "title": path["title"],
        "elevation": path["elevation"],
        "spent": spent,
        "bank": bank,
        "captain": path["captain"],
        "vice": path["vice"],
        "chip": path["chip"],
        "published_objective": path.get("published_objective"),
        "published_proposal_sha256": path.get("published_proposal_sha256"),
        "squad_ok": squad_v.ok,
        "lineup_ok": lineup_v.ok,
        "squad_errors": squad_v.errors,
        "lineup_errors": lineup_v.errors,
        "club_counts": clubs,
        "squad": [
            {
                "web_name": player["web_name"],
                "position": player["position"],
                "club": player["club"],
                "now_cost": player["now_cost"],
                "player_id": player["player_id"],
            }
            for player in squad
        ],
        "xi": [player["web_name"] for player in xi],
        "bench": [player["web_name"] for player in bench],
    }


def _names_for_ids(scored: Mapping[str, Any], ids: Sequence[str]) -> list[str]:
    by_id = {str(row["player_id"]): str(row["web_name"]) for row in scored["squad"]}
    return [by_id[str(player_id)] for player_id in ids]


def compact_host_score(scored: Mapping[str, Any]) -> dict[str, Any]:
    first = scored["weekly_plans"][0]["lineup"]
    return {
        "objective": scored["objective"],
        "bank": scored["bank"],
        "proposal_sha256": scored["proposal_sha256"],
        "decomposition": scored["decomposition"],
        "captain": _names_for_ids(scored, [first["captain_id"]])[0],
        "vice": _names_for_ids(scored, [first["vice_captain_id"]])[0],
        "xi": _names_for_ids(scored, first["starting_xi"]),
        "bench": _names_for_ids(scored, first["bench"]),
        "formation": first["formation"],
        "validation_ok": bool(
            scored["validation"]["squad"]["ok"]
            and scored["validation"]["first_lineup"]["ok"]
        ),
    }


def host_rescore_path(
    packet: Mapping[str, Any],
    path: Mapping[str, Any],
    *,
    policy: Mapping[str, Any],
    rules: Mapping[str, Any],
    ruleset_sha256: str,
    arm_modes: Sequence[str] = ARM_MODES,
) -> dict[str, Any]:
    """Score one declared 15 against a frozen packet in each requested arm."""

    result: dict[str, Any] = {
        "path_id": path["path_id"],
        "title": path["title"],
        "squad_player_ids": path_player_ids(path),
        "published_objective": path.get("published_objective"),
        "arms": {},
    }
    for arm_mode in arm_modes:
        try:
            scored = score_declared_initial_squad(
                packet,
                path_player_ids(path),
                policy=policy,
                arm_mode=arm_mode,
                rules=rules,
                ruleset_sha256=ruleset_sha256,
            )
        except InitialSquadError as exc:
            result["arms"][arm_mode] = {"ok": False, "error": str(exc)}
            continue
        result["arms"][arm_mode] = {
            "ok": True,
            **compact_host_score(scored),
        }
    return result


def host_rescore_paths(
    packet: Mapping[str, Any],
    paths: Sequence[Mapping[str, Any]] | None = None,
    *,
    policy: Mapping[str, Any],
    rules: Mapping[str, Any],
    ruleset_sha256: str,
    arm_modes: Sequence[str] = ARM_MODES,
) -> list[dict[str, Any]]:
    selected = list(paths) if paths is not None else PATHS
    return [
        host_rescore_path(
            packet,
            path,
            policy=policy,
            rules=rules,
            ruleset_sha256=ruleset_sha256,
            arm_modes=arm_modes,
        )
        for path in selected
    ]
