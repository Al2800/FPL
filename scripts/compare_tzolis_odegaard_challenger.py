"""Host-score Tzolis-in / Ødegaard-in 15s against the frozen weekly-2026-08-11 packet.

Fails closed if the live input-packet is missing or its SHA-256 is not
``65eba1feb8c6f6f9707789e0cbf6533baf9fdffa57ac872e10b8bc6badcd3651``.
Does not invent expected-points vectors from the committed packet summary.
"""

from __future__ import annotations

import json
import sys
from itertools import combinations
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

CHECKPOINT = REPO / "reports" / "live" / "2026-27" / "initial-squad" / "weekly-2026-08-11"
PACKET_SUMMARY = REPO / "reports" / "strategy-research" / "packets" / "weekly-2026-08-11.json"
POLICY = REPO / "control" / "policies" / "initial-squad-2026-27.json"
RULES = REPO / "control" / "rules" / "2026-27.yaml"
OUT_JSON = REPO / "reports" / "strategy-research" / "2026-08-18-tzolis-odegaard-challenger.json"
OUT_MD = OUT_JSON.with_suffix(".md")

REQUIRED_PACKET_SHA256 = (
    "65eba1feb8c6f6f9707789e0cbf6533baf9fdffa57ac872e10b8bc6badcd3651"
)
MODES = ("human_reference", "robust", "deterministic")

# Advisory 15 web_names. Wilson is Harry Wilson (Leeds MID); resolved by id when present.
BASELINE_NAMES = [
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
]
FUNDING_IDS = {"260", "542", "544"}  # Wilson, E.Le Fée, Xhaka
LOCKED_IDS = {
    "411",  # Haaland
    "426",  # B.Fernandes
    "112",  # Van Hecke
    "204",  # Mitchell
    "423",  # Shaw
}


class PacketBindError(RuntimeError):
    """Raised when the frozen packet body cannot be bound."""


def _load_packet() -> tuple[dict, str]:
    path = CHECKPOINT / "input-packet.json"
    if not path.is_file():
        summary_sha = None
        if PACKET_SUMMARY.is_file():
            summary = json.loads(PACKET_SUMMARY.read_text(encoding="utf-8"))
            summary_sha = (
                summary.get("recommendation", {}).get("input_packet_sha256")
                or summary.get("checkpoint", {}).get("input_packet_sha256")
            )
        raise PacketBindError(
            "Live checkpoint input-packet missing at "
            f"{path}. Committed packet summary is a decision surface only "
            "(no EP vectors; see scripts/publish_decision_packet_summary.py). "
            f"Summary binds SHA {summary_sha}; body required to score. "
            f"Expected SHA {REQUIRED_PACKET_SHA256}."
        )
    wrap = json.loads(path.read_text(encoding="utf-8"))
    packet = wrap["packet"] if "packet" in wrap else wrap
    rec_path = CHECKPOINT / "recommendation.json"
    rec_sha = None
    if rec_path.is_file():
        rec = json.loads(rec_path.read_text(encoding="utf-8"))
        rec_sha = rec.get("input_packet_sha256")
    bound = rec_sha or wrap.get("content_sha256") or packet.get("content_sha256")
    if bound != REQUIRED_PACKET_SHA256:
        raise PacketBindError(
            f"Bound packet SHA {bound} does not match required "
            f"{REQUIRED_PACKET_SHA256}."
        )
    return packet, bound


def _resolve(by_name: dict[str, list[dict]], web_name: str, player_id: str | None = None) -> dict:
    rows = by_name.get(web_name, [])
    if player_id is not None:
        for row in rows:
            if str(row["player_id"]) == str(player_id):
                return row
        raise PacketBindError(f"{web_name} id {player_id} not in bound packet")
    if len(rows) != 1:
        raise PacketBindError(
            f"{web_name} missing or ambiguous in bound packet ({len(rows)} rows)"
        )
    return rows[0]


def _player_card(row: dict) -> dict:
    return {
        "web_name": row["web_name"],
        "player_id": str(row["player_id"]),
        "now_cost": float(row["now_cost"]),
        "club_id": str(row["club_id"]),
        "position": str(row["position"]),
        "gw1_expected_points": float(row["expected_points"][0]),
        "gw1_start_p": float(row["start_probability"][0]),
    }


def _load_scorer():
    from src.optimisation.initial_squad import (  # noqa: PLC0415
        InitialSquadError,
        score_declared_initial_squad,
    )
    from src.scoring.rules_loader import load_rules, ruleset_sha256  # noqa: PLC0415

    return InitialSquadError, score_declared_initial_squad, load_rules, ruleset_sha256


def _score_modes(packet: dict, ids: list[str], policy: dict, rules: dict, rules_hash: str) -> dict:
    _, score_declared_initial_squad, _, _ = _load_scorer()
    by_id = {str(p["player_id"]): p for p in packet["players"]}
    out: dict = {}
    for mode in MODES:
        scored = score_declared_initial_squad(
            packet,
            ids,
            policy=policy,
            arm_mode=mode,
            rules=rules,
            ruleset_sha256=rules_hash,
        )
        gw = scored["weekly_plans"][0]["lineup"]
        out[mode] = {
            "objective": float(scored["objective"]),
            "bank": float(scored["bank"]),
            "proposal_sha256": scored["proposal_sha256"],
            "validation_ok": bool(scored["validation"]["squad"]["ok"]),
            "captain": by_id[str(gw["captain_id"])]["web_name"],
            "vice": by_id[str(gw["vice_captain_id"])]["web_name"],
            "starting_xi": [by_id[str(i)]["web_name"] for i in gw["starting_xi"]],
            "bench": [by_id[str(i)]["web_name"] for i in gw["bench"]],
            "formation": gw["formation"],
        }
    return out


def _legal_swap(
    packet: dict,
    baseline_ids: list[str],
    add_id: str,
    policy: dict,
    rules: dict,
    rules_hash: str,
) -> dict:
    """Drop only from Wilson / E.Le Fée / Xhaka. One extra like-for-like MID only if required."""

    InitialSquadError, score_declared_initial_squad, _, _ = _load_scorer()
    by_id = {str(p["player_id"]): p for p in packet["players"]}
    add = by_id[add_id]
    add_cost = float(add["now_cost"])
    funding = [i for i in baseline_ids if i in FUNDING_IDS]
    rest = [i for i in baseline_ids if i not in FUNDING_IDS]
    errors: list[str] = []

    def try_ids(ids: list[str], dropped: list[str], extra: str | None) -> dict | None:
        if any(i in LOCKED_IDS for i in dropped):
            return None
        try:
            scored = score_declared_initial_squad(
                packet,
                ids,
                policy=policy,
                arm_mode="deterministic",
                rules=rules,
                ruleset_sha256=rules_hash,
            )
        except InitialSquadError as exc:
            errors.append(str(exc))
            return None
        if not scored.get("validation", {}).get("squad", {}).get("ok"):
            return None
        return {
            "squad_player_ids": [str(x) for x in scored["squad_player_ids"]],
            "dropped": [by_id[i]["web_name"] for i in dropped],
            "added": [add["web_name"]] + ([extra] if extra else []),
            "extra_swap": extra,
            "bank": float(scored["bank"]),
            "squad_cost": round(100.0 - float(scored["bank"]), 1),
        }

    # Single then double drops from the funding pool, cheapest-first among legal.
    candidates: list[dict] = []
    for drop_n in (1, 2):
        for dropped in combinations(funding, drop_n):
            remaining_funding = [i for i in funding if i not in dropped]
            base = rest + remaining_funding + [add_id]
            if drop_n == 1:
                row = try_ids(base, list(dropped), None)
                if row:
                    candidates.append(row)
                continue
            # Two drops free a MID slot: fill with cheapest legal MID not already in the 15
            # and not a locked playing piece. Bench-enabler preference: lowest cost, then id.
            mid_pool = [
                p
                for p in packet["players"]
                if str(p["position"]) == "MID"
                and str(p["player_id"]) not in set(base)
                and str(p["player_id"]) not in LOCKED_IDS
            ]
            mid_pool.sort(key=lambda p: (float(p["now_cost"]), str(p["player_id"])))
            for filler in mid_pool[:12]:
                row = try_ids(base + [str(filler["player_id"])], list(dropped), filler["web_name"])
                if row:
                    candidates.append(row)
                    break

    if not candidates:
        raise PacketBindError(
            f"No legal funding path to add {add['web_name']} (£{add_cost}m) from "
            f"Wilson / E.Le Fée / Xhaka. Scorer notes: {errors[:3]}"
        )
    candidates.sort(key=lambda r: (len(r["dropped"]), -r["bank"], r["dropped"]))
    return candidates[0]


def main() -> int:
    try:
        packet, bound = _load_packet()
    except PacketBindError as exc:
        print(f"BLOCKER: {exc}")
        return 2

    _, _, load_rules, ruleset_sha256 = _load_scorer()
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    rules = load_rules(RULES)
    rules_hash = ruleset_sha256(RULES)
    by_name: dict[str, list[dict]] = {}
    for row in packet["players"]:
        by_name.setdefault(str(row["web_name"]), []).append(row)

    resolved = {
        "Tzolis": _resolve(by_name, "Tzolis") if "Tzolis" in by_name else None,
        "Ødegaard": _resolve(by_name, "Ødegaard") if "Ødegaard" in by_name else None,
        "Wilson": _resolve(by_name, "Wilson", "260"),
        "E.Le Fée": _resolve(by_name, "E.Le Fée", "542"),
        "Xhaka": _resolve(by_name, "Xhaka") if "Xhaka" in by_name else None,
    }
    blockers: list[str] = []
    if resolved["Xhaka"] is None:
        blockers.append("Xhaka missing or ambiguous in bound packet")
    baseline_ids = []
    for name in BASELINE_NAMES:
        pid = "260" if name == "Wilson" else None
        try:
            baseline_ids.append(str(_resolve(by_name, name, pid)["player_id"]))
        except PacketBindError as exc:
            blockers.append(str(exc))

    report: dict = {
        "schema_version": "1.0",
        "report_id": "strategy-tzolis-odegaard-challenger-2026-08-18",
        "bound_packet_sha256": bound,
        "checkpoint_id": "weekly-2026-08-11",
        "packet_binding_status": "bound",
        "resolved_from_packet": {
            key: (_player_card(row) if row is not None else None)
            for key, row in resolved.items()
        },
        "account_writes": False,
    }
    if blockers:
        report["blocker"] = blockers
        OUT_JSON.write_text(
            json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        print("BLOCKER:", "; ".join(blockers))
        return 2

    baseline_scores = _score_modes(packet, baseline_ids, policy, rules, rules_hash)
    report["baseline"] = {
        "squad_player_ids": baseline_ids,
        "names": [by_name_id(packet, i) for i in baseline_ids],
        "scores": baseline_scores,
    }

    challengers: dict = {}
    for label, web in (("tzolis_in", "Tzolis"), ("odegaard_in", "Ødegaard")):
        row = resolved[web]
        if row is None:
            challengers[label] = {
                "status": "stopped",
                "blocker": f"{web} missing or ambiguous in bound packet",
            }
            continue
        try:
            constructed = _legal_swap(
                packet,
                baseline_ids,
                str(row["player_id"]),
                policy,
                rules,
                rules_hash,
            )
            scores = _score_modes(
                packet, constructed["squad_player_ids"], policy, rules, rules_hash
            )
            deltas = {
                mode: round(
                    float(scores[mode]["objective"])
                    - float(baseline_scores[mode]["objective"]),
                    6,
                )
                for mode in MODES
            }
            challengers[label] = {
                "status": "scored",
                **constructed,
                "names": [by_name_id(packet, i) for i in constructed["squad_player_ids"]],
                "scores": scores,
                "delta_vs_baseline": deltas,
            }
        except PacketBindError as exc:
            challengers[label] = {"status": "illegal_or_unfunded", "blocker": str(exc)}
    report["challengers"] = challengers

    beats = {
        label: {
            mode: bool(
                item.get("status") == "scored"
                and float(item["delta_vs_baseline"][mode]) > 0
            )
            for mode in ("human_reference", "robust")
        }
        for label, item in challengers.items()
    }
    report["beats_baseline"] = beats
    any_beat = any(flag for flags in beats.values() for flag in flags.values())
    report["verdict"] = (
        "challenger_beats_advisory_on_human_reference_or_robust"
        if any_beat
        else "neither_challenger_beats_advisory_on_human_reference_or_robust"
    )
    report["recommendation"] = (
        "adopt_challenger" if any_beat else "keep_current_15"
    )

    OUT_JSON.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(OUT_JSON)
    print(report["verdict"])
    return 0


def by_name_id(packet: dict, player_id: str) -> str:
    for row in packet["players"]:
        if str(row["player_id"]) == str(player_id):
            return str(row["web_name"])
    return str(player_id)


if __name__ == "__main__":
    raise SystemExit(main())
