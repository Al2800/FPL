"""Host-score Haaland-in alternatives against the frozen weekly-2026-08-08 packet."""

from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path

from src.optimisation.initial_squad import InitialSquadError, score_declared_initial_squad
from src.scoring.rules_loader import load_rules, ruleset_sha256

REPO = Path(__file__).resolve().parents[1]
CHECKPOINT = REPO / "reports" / "live" / "2026-27" / "initial-squad" / "weekly-2026-08-08"
OUT = REPO / "reports" / "strategy-research" / "2026-08-08-haaland-in-comparison.json"
OUT_MD = OUT.with_suffix(".md")

POSITION_NEED = {"GKP": 2, "DEF": 5, "MID": 5, "FWD": 3}


def main() -> int:
    packet_wrap = json.loads(
        (CHECKPOINT / "input-packet.json").read_text(encoding="utf-8")
    )
    packet = packet_wrap["packet"] if "packet" in packet_wrap else packet_wrap
    policy = json.loads(
        (REPO / "control" / "policies" / "initial-squad-2026-27.json").read_text(
            encoding="utf-8"
        )
    )
    rules_path = REPO / "control" / "rules" / "2026-27.yaml"
    rules = load_rules(rules_path)
    rules_hash = ruleset_sha256(rules_path)

    rec = json.loads((CHECKPOINT / "recommendation.json").read_text(encoding="utf-8"))
    robust = rec["selection"]["selection"]["proposal"]
    robust_ids = [str(x) for x in robust["squad_player_ids"]]
    robust_obj = float(robust["objective"])
    det = rec["selection"]["arms"]["deterministic"]["result"]["selected"]
    det_obj = float(det["objective"])

    by_id = {str(p["player_id"]): p for p in packet["players"]}
    haaland = next(p for p in packet["players"] if p.get("web_name") == "Haaland")
    hid = str(haaland["player_id"])

    robust_set = set(robust_ids)
    pool = [
        p
        for p in packet["players"]
        if str(p["player_id"]) not in robust_set and str(p["player_id"]) != hid
    ]
    discounts = [float(x) for x in packet["discount_factors"]]

    def rank(row: dict) -> tuple:
        ep = sum(
            d * float(v) for d, v in zip(discounts, row["expected_points"], strict=True)
        )
        return (-ep, float(row["now_cost"]), str(row["player_id"]))

    pool_by_pos: dict[str, list] = {"GKP": [], "DEF": [], "MID": [], "FWD": []}
    for p in pool:
        pool_by_pos[str(p["position"])].append(p)
    for pos, rows in pool_by_pos.items():
        rows.sort(key=rank)
        pool_by_pos[pos] = rows[:40]

    def counts(ids: list[str]) -> dict[str, int]:
        c = {"GKP": 0, "DEF": 0, "MID": 0, "FWD": 0}
        for i in ids:
            c[str(by_id[i]["position"])] += 1
        return c

    def total_cost(ids: list[str]) -> float:
        return sum(float(by_id[i]["now_cost"]) for i in ids)

    best: dict | None = None
    top: list[dict] = []
    tried = 0
    errors = 0

    robust_fwds = [
        i for i in robust_ids if str(by_id[i]["position"]) == "FWD"
    ]
    haaland_cost = float(haaland["now_cost"])

    for drop_n in (2, 3, 4):
        for dropped in combinations(robust_ids, drop_n):
            # Haaland is FWD: must free at least one FWD slot.
            if not any(i in robust_fwds for i in dropped):
                continue
            # Must free enough budget for Haaland before fillers.
            if sum(float(by_id[i]["now_cost"]) for i in dropped) + 1e-9 < haaland_cost:
                continue
            remaining = [i for i in robust_ids if i not in dropped]
            base = remaining + [hid]
            c = counts(base)
            need = {pos: POSITION_NEED[pos] - c[pos] for pos in POSITION_NEED}
            if any(v < 0 for v in need.values()):
                continue
            fill_n = sum(need.values())
            if fill_n != drop_n - 1:
                continue
            if total_cost(base) > 100.0001:
                continue
            pos_slots: list[str] = []
            for pos, n in need.items():
                pos_slots.extend([pos] * n)
            # Bound filler breadth; tighten for larger swaps.
            cap = 14 if drop_n <= 3 else 8
            lists = [pool_by_pos[pos][:cap] for pos in pos_slots]

            def rec_fill(idx: int, chosen_ids: list[str]) -> None:
                nonlocal best, tried, errors, top
                partial = base + chosen_ids
                if total_cost(partial) > 100.0001:
                    return
                if idx == len(lists):
                    ids = partial
                    if len(set(ids)) != 15:
                        return
                    tried += 1
                    try:
                        scored = score_declared_initial_squad(
                            packet,
                            ids,
                            policy=policy,
                            arm_mode="robust",
                            rules=rules,
                            ruleset_sha256=rules_hash,
                        )
                        scored_det = score_declared_initial_squad(
                            packet,
                            ids,
                            policy=policy,
                            arm_mode="deterministic",
                            rules=rules,
                            ruleset_sha256=rules_hash,
                        )
                    except InitialSquadError:
                        errors += 1
                        return
                    if not scored.get("validation", {}).get("squad", {}).get("ok"):
                        return
                    obj = float(scored["objective"])
                    gw = scored["weekly_plans"][0]["lineup"]
                    row = {
                        "objective_robust": obj,
                        "objective_deterministic": float(scored_det["objective"]),
                        "delta_vs_robust": round(obj - robust_obj, 6),
                        "delta_vs_deterministic": round(
                            float(scored_det["objective"]) - det_obj, 6
                        ),
                        "bank": float(scored["bank"]),
                        "squad_player_ids": list(scored["squad_player_ids"]),
                        "names": [by_id[i]["web_name"] for i in scored["squad_player_ids"]],
                        "proposal_sha256_robust_mode": scored["proposal_sha256"],
                        "proposal_sha256_deterministic_mode": scored_det[
                            "proposal_sha256"
                        ],
                        "dropped": [by_id[i]["web_name"] for i in dropped],
                        "added_fillers": [by_id[i]["web_name"] for i in chosen_ids],
                        "captain": by_id[str(gw["captain_id"])]["web_name"],
                        "vice": by_id[str(gw["vice_captain_id"])]["web_name"],
                        "starting_xi": [
                            by_id[str(i)]["web_name"] for i in gw["starting_xi"]
                        ],
                        "bench": [by_id[str(i)]["web_name"] for i in gw["bench"]],
                        "formation": gw["formation"],
                    }
                    top.append(row)
                    top.sort(
                        key=lambda r: (
                            -float(r["objective_robust"]),
                            str(r["proposal_sha256_robust_mode"]),
                        )
                    )
                    top[:] = top[:10]
                    if best is None or obj > float(best["objective_robust"]):
                        best = row
                    return
                for ply in lists[idx]:
                    pid = str(ply["player_id"])
                    if pid in chosen_ids or pid in base:
                        continue
                    rec_fill(idx + 1, chosen_ids + [pid])

            rec_fill(0, [])

    # Also score human_reference mode on the winner for host handoff shape
    host = None
    if best is not None:
        host = score_declared_initial_squad(
            packet,
            best["squad_player_ids"],
            policy=policy,
            arm_mode="human_reference",
            rules=rules,
            ruleset_sha256=rules_hash,
        )

    report = {
        "schema_version": "1.0",
        "report_id": "strategy-haaland-in-comparison-2026-08-08",
        "bound_packet_sha256": rec.get("input_packet_sha256")
        or packet_wrap.get("content_sha256")
        or packet.get("content_sha256"),
        "checkpoint_id": "weekly-2026-08-08",
        "haaland_player_id": hid,
        "haaland_now_cost": float(haaland["now_cost"]),
        "search": {
            "drop_ns": [2, 3, 4],
            "tried_legal_candidates": tried,
            "scorer_errors_or_rejects": errors,
            "pool_caps_per_position": 12,
        },
        "baselines": {
            "robust_objective": robust_obj,
            "robust_proposal_sha256": robust["proposal_sha256"],
            "robust_names": [by_id[i]["web_name"] for i in robust_ids],
            "deterministic_objective": det_obj,
            "deterministic_proposal_sha256": det["proposal_sha256"],
            "deterministic_names": [
                by_id[str(i)]["web_name"] for i in det["squad_player_ids"]
            ],
        },
        "best_haaland_in": best,
        "top_haaland_in": top,
        "host_human_reference_score": (
            {
                "objective": float(host["objective"]),
                "bank": float(host["bank"]),
                "proposal_sha256": host["proposal_sha256"],
                "validation_ok": host["validation"]["squad"]["ok"],
                "captain": by_id[str(host["weekly_plans"][0]["lineup"]["captain_id"])][
                    "web_name"
                ],
                "vice": by_id[
                    str(host["weekly_plans"][0]["lineup"]["vice_captain_id"])
                ]["web_name"],
            }
            if host is not None
            else None
        ),
        "verdict": (
            "haaland_in_beats_robust"
            if best and float(best["delta_vs_robust"]) > 0
            else "haaland_in_does_not_beat_robust"
            if best
            else "no_legal_haaland_in_found"
        ),
        "account_writes": False,
    }

    # Constrained Haaland + Bruno search (community core).
    bruno = next(p for p in packet["players"] if p.get("web_name") == "B.Fernandes")
    bid = str(bruno["player_id"])
    best_bruno: dict | None = None
    tried_bruno = 0
    drop_pool = [i for i in robust_ids if i != bid]
    for drop_n in (2, 3, 4):
        for dropped in combinations(drop_pool, drop_n):
            if not any(i in robust_fwds for i in dropped):
                continue
            if sum(float(by_id[i]["now_cost"]) for i in dropped) + 1e-9 < haaland_cost:
                continue
            remaining = [i for i in robust_ids if i not in dropped]
            base = remaining + [hid]
            if bid not in base:
                continue
            c = counts(base)
            need = {pos: POSITION_NEED[pos] - c[pos] for pos in POSITION_NEED}
            if any(v < 0 for v in need.values()):
                continue
            if sum(need.values()) != drop_n - 1:
                continue
            if total_cost(base) > 100.0001:
                continue
            pos_slots = []
            for pos, n in need.items():
                pos_slots.extend([pos] * n)
            cap = 12 if drop_n <= 3 else 8
            lists = [pool_by_pos[pos][:cap] for pos in pos_slots]

            def rec_bruno(idx: int, chosen_ids: list[str]) -> None:
                nonlocal best_bruno, tried_bruno
                partial = base + chosen_ids
                if total_cost(partial) > 100.0001:
                    return
                if idx == len(lists):
                    ids = partial
                    if len(set(ids)) != 15:
                        return
                    tried_bruno += 1
                    try:
                        scored = score_declared_initial_squad(
                            packet,
                            ids,
                            policy=policy,
                            arm_mode="robust",
                            rules=rules,
                            ruleset_sha256=rules_hash,
                        )
                    except InitialSquadError:
                        return
                    if not scored.get("validation", {}).get("squad", {}).get("ok"):
                        return
                    obj = float(scored["objective"])
                    gw = scored["weekly_plans"][0]["lineup"]
                    row = {
                        "objective_robust": obj,
                        "delta_vs_robust": round(obj - robust_obj, 6),
                        "bank": float(scored["bank"]),
                        "names": [by_id[i]["web_name"] for i in scored["squad_player_ids"]],
                        "squad_player_ids": list(scored["squad_player_ids"]),
                        "proposal_sha256_robust_mode": scored["proposal_sha256"],
                        "dropped": [by_id[i]["web_name"] for i in dropped],
                        "added_fillers": [by_id[i]["web_name"] for i in chosen_ids],
                        "captain": by_id[str(gw["captain_id"])]["web_name"],
                        "vice": by_id[str(gw["vice_captain_id"])]["web_name"],
                        "starting_xi": [
                            by_id[str(i)]["web_name"] for i in gw["starting_xi"]
                        ],
                        "bench": [by_id[str(i)]["web_name"] for i in gw["bench"]],
                    }
                    if best_bruno is None or obj > float(best_bruno["objective_robust"]):
                        best_bruno = row
                    return
                for ply in lists[idx]:
                    pid = str(ply["player_id"])
                    if pid in chosen_ids or pid in base:
                        continue
                    rec_bruno(idx + 1, chosen_ids + [pid])

            rec_bruno(0, [])

    report["search"]["haaland_bruno_tried"] = tried_bruno
    report["best_haaland_bruno"] = best_bruno
    report["verdict_haaland_bruno"] = (
        "haaland_bruno_beats_robust"
        if best_bruno and float(best_bruno["delta_vs_robust"]) > 0
        else "haaland_bruno_does_not_beat_robust"
        if best_bruno
        else "no_legal_haaland_bruno_found"
    )

    OUT.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    lines = [
        "# Haaland-in host-scored comparison — 2026-08-08",
        "",
        f"- bound_packet / checkpoint: `weekly-2026-08-08`",
        f"- packet sha: `{report['bound_packet_sha256']}`",
        f"- Haaland: id `{hid}`, £{haaland['now_cost']}m",
        f"- search tried: `{tried}` legal candidates; scorer rejects: `{errors}`",
        f"- verdict: `{report['verdict']}`",
        "",
        "## Baselines",
        "",
        f"- Robust objective: `{robust_obj}` (`{robust['proposal_sha256'][:16]}…`)",
        f"- Deterministic objective: `{det_obj}`",
        "",
        "## Best Haaland-in (robust-mode score)",
        "",
    ]
    if best is None:
        lines.append("No legal Haaland-in 15 found in the bounded search.")
    else:
        lines.extend(
            [
                f"- Robust-mode objective: `{best['objective_robust']}` "
                f"(delta vs robust `{best['delta_vs_robust']:+}`)",
                f"- Deterministic-mode objective: `{best['objective_deterministic']}` "
                f"(delta vs deterministic `{best['delta_vs_deterministic']:+}`)",
                f"- Bank: `{best['bank']}`",
                f"- Dropped from robust: {', '.join(best['dropped'])}",
                f"- Fillers added: {', '.join(best['added_fillers']) or 'none'}",
                f"- Captain / vice: {best['captain']} / {best['vice']}",
                f"- Proposal sha (robust mode): `{best['proposal_sha256_robust_mode']}`",
                "",
                "### 15",
                "",
                ", ".join(best["names"]),
                "",
                "### GW1",
                "",
                f"- XI: {', '.join(best['starting_xi'])}",
                f"- Bench: {', '.join(best['bench'])}",
                f"- Formation: `{best['formation']}`",
                "",
                "## Host handoff",
                "",
                f"- human_reference objective: "
                f"`{report['host_human_reference_score']['objective']}`",
                f"- human_reference proposal sha: "
                f"`{report['host_human_reference_score']['proposal_sha256']}`",
                "- Account writes: false; owner approval still required",
                "",
                "## Top alternatives (by robust-mode objective)",
                "",
            ]
        )
        for i, row in enumerate(top[:5], 1):
            lines.append(
                f"{i}. obj `{row['objective_robust']}` "
                f"(Δ `{row['delta_vs_robust']:+}`) — "
                f"drop {', '.join(row['dropped'])}; "
                f"add {', '.join(row['added_fillers']) or '—'}"
            )
    lines.extend(
        [
            "",
            "## Best Haaland + Bruno (constrained)",
            "",
            f"- candidates tried: `{tried_bruno}`",
            f"- verdict: `{report['verdict_haaland_bruno']}`",
            "",
        ]
    )
    if best_bruno is None:
        lines.append("No legal Haaland+Bruno 15 found in the bounded search.")
    else:
        lines.extend(
            [
                f"- Robust-mode objective: `{best_bruno['objective_robust']}` "
                f"(delta vs robust `{best_bruno['delta_vs_robust']:+}`)",
                f"- Dropped: {', '.join(best_bruno['dropped'])}",
                f"- Fillers: {', '.join(best_bruno['added_fillers']) or 'none'}",
                f"- Captain / vice: {best_bruno['captain']} / {best_bruno['vice']}",
                f"- 15: {', '.join(best_bruno['names'])}",
                f"- XI: {', '.join(best_bruno['starting_xi'])}",
                f"- Bench: {', '.join(best_bruno['bench'])}",
            ]
        )
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(OUT)
    print(report["verdict"], report["verdict_haaland_bruno"])
    if best:
        print("haaland_in", best["objective_robust"], best["delta_vs_robust"], best["names"])
    if best_bruno:
        print(
            "haaland_bruno",
            best_bruno["objective_robust"],
            best_bruno["delta_vs_robust"],
            best_bruno["names"],
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
