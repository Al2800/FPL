"""Validate five GW1 strategy-path squads against the 2026/27 ruleset.

Paths 1–2 are the frozen weekly-2026-08-11 optimiser arms (published
objectives). Paths 3–5 are declared alternatives. Full host rescoring of
3–5 still needs the local input-packet; this script only proves legality.
"""

from __future__ import annotations

import json
from pathlib import Path

from src.scoring.rules_loader import load_rules
from src.scoring.validator import validate_lineup, validate_squad

REPO = Path(__file__).resolve().parents[1]
OUT_JSON = REPO / "reports" / "strategy-research" / "2026-08-19-five-path-squads.json"

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
    "LEE": "13",
    "LIV": "14",
    "MCI": "15",
    "MUN": "16",
    "NFO": "18",
    "TOT": "19",
    "SUN": "20",
    "IPS": "12",
}


def P(player_id: str, name: str, pos: str, club: str, cost: float) -> dict:
    return {
        "player_id": player_id,
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
    "Verbruggen": P("verbruggen", "Verbruggen", "GKP", "BHA", 4.5),
    "Dubravka": P("dubravka", "Dubravka", "GKP", "TOT", 4.0),
    "Kinsky": P("kinsky", "Kinsky", "GKP", "TOT", 4.5),
    "Mitchell": P("204", "Mitchell", "DEF", "CRY", 4.5),
    "Tarkowski": P("229", "Tarkowski", "DEF", "EVE", 6.0),
    "Virgil": P("356", "Virgil", "DEF", "LIV", 6.5),
    "Matheus N.": P("389", "Matheus N.", "DEF", "MCI", 6.0),
    "Truffert": P("61", "Truffert", "DEF", "BOU", 5.5),
    "Van Hecke": P("112", "Van Hecke", "DEF", "TOT", 5.0),
    "Shaw": P("423", "Shaw", "DEF", "MUN", 4.5),
    "Diop": P("diop", "Diop", "DEF", "IPS", 4.0),
    "van Ewijk": P("van-ewijk", "van Ewijk", "DEF", "COV", 4.0),
    "Calafiori": P("calafiori", "Calafiori", "DEF", "ARS", 5.5),
    "Wilson": P("260", "Wilson", "MID", "LEE", 6.5),
    "Semenyo": P("397", "Semenyo", "MID", "MCI", 8.5),
    "B.Fernandes": P("426", "B.Fernandes", "MID", "MUN", 12.0),
    "Gibbs-White": P("480", "Gibbs-White", "MID", "NFO", 8.0),
    "E.Le Fée": P("542", "E.Le Fée", "MID", "SUN", 6.0),
    "Xhaka": P("xhaka", "Xhaka", "MID", "SUN", 5.5),
    "João Pedro": P("165", "João Pedro", "FWD", "CHE", 7.5),
    "Beto": P("248", "Beto", "FWD", "EVE", 5.5),
    "Calvert-Lewin": P("346", "Calvert-Lewin", "FWD", "LEE", 6.0),
    "Thiago": P("106", "Thiago", "FWD", "BRE", 8.0),
    "Obi": P("441", "Obi", "FWD", "MUN", 4.5),
    "Haaland": P("haaland", "Haaland", "FWD", "MCI", 15.5),
}


PATHS = [
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


def materialise(names: list[str]) -> list[dict]:
    return [PLAYERS[name] for name in names]


def main() -> int:
    rules = load_rules(REPO / "control" / "rules" / "2026-27.yaml")
    results = []
    for path in PATHS:
        squad = materialise(path["squad"])
        xi = materialise(path["xi"])
        bench = materialise(path["bench"])
        spent = round(sum(float(p["now_cost"]) for p in squad), 1)
        bank = round(100.0 - spent, 1)
        squad_v = validate_squad(squad, bank=bank, rules=rules)
        lineup_v = validate_lineup(
            xi,
            bench,
            captain_id=PLAYERS[path["captain"]]["player_id"],
            vice_captain_id=PLAYERS[path["vice"]]["player_id"],
            rules=rules,
        )
        clubs = {}
        for player in squad:
            clubs.setdefault(player["club"], 0)
            clubs[player["club"]] += 1
        results.append(
            {
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
                        "web_name": p["web_name"],
                        "position": p["position"],
                        "club": p["club"],
                        "now_cost": p["now_cost"],
                    }
                    for p in squad
                ],
                "xi": [p["web_name"] for p in xi],
                "bench": [p["web_name"] for p in bench],
            }
        )
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    failed = [row for row in results if not (row["squad_ok"] and row["lineup_ok"])]
    for row in results:
        status = "OK" if row["squad_ok"] and row["lineup_ok"] else "FAIL"
        print(
            f"{status} {row['path_id']} £{row['spent']:.1f} bank {row['bank']:.1f} "
            f"obj={row['published_objective']}"
        )
        if row["squad_errors"] or row["lineup_errors"]:
            print(" ", row["squad_errors"], row["lineup_errors"])
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
