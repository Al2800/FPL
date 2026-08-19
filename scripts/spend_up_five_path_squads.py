"""Spend leftover ITB on each five-path 15 and host-score the upgrades.

A and B already spend £100.0. C–E leave money in the bank; this review asks
what happens if that leftover is forced into the same 15-slot shape.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.optimisation.five_path_squads import PATHS, host_rescore_path  # noqa: E402
from src.optimisation.spend_remaining import (  # noqa: E402
    discounted_ep,
    score_spend_candidates,
    spend_remaining_candidates,
)
from src.scoring.rules_loader import load_rules, ruleset_sha256  # noqa: E402

PACKET_PATH = (
    REPO / "data" / "live-shadow" / "test-runs" / "host-rescore-2026-08-19" / "input-packet.json"
)
POLICY_PATH = REPO / "control" / "policies" / "initial-squad-2026-27.json"
RULES_PATH = REPO / "control" / "rules" / "2026-27.yaml"
OUT_JSON = (
    REPO / "reports" / "strategy-research" / "2026-08-19-five-path-spend-up.json"
)
OUT_MD = OUT_JSON.with_suffix(".md")


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def describe_moves(moves: list[dict[str, Any]]) -> str:
    parts = []
    for move in moves:
        parts.append(
            f"{move['out_name']} → {move['in_name']} (+£{move['extra']:.1f}, EP {move['ep_gain']:+.2f})"
        )
    return "; ".join(parts)


def trapped_spend(path: dict[str, Any], packet: dict[str, Any]) -> list[dict[str, Any]]:
    """Cheapest / lowest-EP members — leftover value trapped in the 15, not ITB."""

    by_id = {str(row["player_id"]): row for row in packet["players"]}
    discounts = [float(item) for item in packet["discount_factors"]]
    rows = []
    for name in path["squad"]:
        from src.optimisation.five_path_squads import PLAYERS

        player_id = str(PLAYERS[name]["player_id"])
        row = by_id.get(player_id)
        if row is None:
            continue
        ep = discounted_ep(row, discounts)
        start = float(row["start_probability"][0])
        rows.append(
            {
                "web_name": row["web_name"],
                "position": row["position"],
                "now_cost": float(row["now_cost"]),
                "discounted_ep": round(ep, 3),
                "gw1_start_p": round(start, 4),
                "on_bench": name in path["bench"],
            }
        )
    rows.sort(key=lambda item: (item["discounted_ep"], item["now_cost"]))
    bench = [item for item in rows if item["on_bench"]]
    return (bench or rows)[:4]


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Spend-the-budget review — five GW1 paths",
        "",
        f"- packet_sha256: `{payload['packet_sha256']}`",
        f"- observed_at: `{payload['observed_at']}`",
        "- rule: keep each path's 15-slot shape; spend leftover ITB on same-position upgrades",
        "- account_writes: `false`",
        "",
        "A and B already spend £100.0. C–E leave money on the table as unused bank.",
        "This review force-spends that bank and host-scores the resulting 15 on the",
        "same 19 August packet. It does not invent a sixth path.",
        "",
        "| Path | Bank now | Best spend-up | Robust after | Δ vs current | Bank after |",
        "|---|---:|---|---:|---:|---:|",
    ]
    for row in payload["paths"]:
        best = row.get("best")
        if row["bank"] == 0:
            lines.append(
                f"| {row['path_id']} | 0.0 | already spent | "
                f"{row['current_robust']:.2f} | 0 | 0.0 |"
            )
            continue
        if not best or not best.get("ok"):
            lines.append(
                f"| {row['path_id']} | {row['bank']:.1f} | no legal upgrade | "
                f"{row['current_robust']:.2f} | — | {row['bank']:.1f} |"
            )
            continue
        delta = round(float(best["objective"]) - float(row["current_robust"]), 2)
        lines.append(
            f"| {row['path_id']} | {row['bank']:.1f} | {describe_moves(best['moves'])} | "
            f"{best['objective']:.2f} | {delta:+.2f} | {best['bank']:.1f} |"
        )
    lines.extend(["", "## Per path", ""])
    for row in payload["paths"]:
        lines.append(f"### {row['path_id']}")
        lines.append(f"- current robust: `{row['current_robust']}` · bank `{row['bank']}`")
        trapped = row.get("trapped_spend") or []
        if trapped:
            bits = ", ".join(
                f"{item['web_name']} £{item['now_cost']:.1f} EP {item['discounted_ep']:.1f} "
                f"start_p {item['gw1_start_p']:.2f}"
                + (" (bench)" if item["on_bench"] else "")
                for item in trapped
            )
            lines.append(f"- weakest spend in the 15: {bits}")
        best = row.get("best")
        if row["bank"] == 0:
            lines.append(
                "- leftover pounds: none. Any money on the table is trapped in "
                "low-EP bench pieces, not ITB."
            )
            lines.append("")
            continue
        if not best or not best.get("ok"):
            lines.append("- no legal same-position upgrade spent the leftover bank.")
            lines.append("")
            continue
        lines.extend(
            [
                f"- best spend-up: {describe_moves(best['moves'])}",
                f"- robust after: `{best['objective']}` (Δ "
                f"{float(best['objective']) - float(row['current_robust']):+.3f})",
                f"- bank after: `{best['bank']}`",
                f"- captain / vice: {best['captain']} / {best['vice']}",
                f"- XI: {', '.join(best['xi'])}",
                f"- bench: {', '.join(best['bench'])}",
            ]
        )
        others = [
            item
            for item in row.get("scored") or []
            if item.get("ok") and item.get("proposal_sha256") != best.get("proposal_sha256")
        ][:3]
        if others:
            lines.append("- other legal spends:")
            for item in others:
                delta = float(item["objective"]) - float(row["current_robust"])
                lines.append(
                    f"  - {describe_moves(item['moves'])} → `{item['objective']:.3f}` "
                    f"({delta:+.3f}), bank {item['bank']}"
                )
        lines.append("")
    lines.extend(
        [
            "## Interpretation",
            "",
            "- Spending leftover ITB is not the same as beating path A, except that",
            "  D's £2.0 is large enough to buy A's premiums (Raya + Guéhi) and close",
            "  most of the gap. That spend-up stops being a death-zone team.",
            "- C's £0.5 only upgrades a junk defender; Haaland still costs ~19 vs A.",
            "- E's £1.0 as Senesi + Anderson is the cleanest declared spend and",
            "  becomes the closest alternative to A.",
            "- A/B already spent £100.0; their leftover is Obi (start_p 0.05) and",
            "  Beto minutes, not unused pounds.",
            "- Owner approval is still required before any FPL entry.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    packet = _load(PACKET_PATH)
    if "packet" in packet:
        packet = packet["packet"]
    policy = _load(POLICY_PATH)
    rules = load_rules(RULES_PATH)
    rules_hash = ruleset_sha256(RULES_PATH)
    rows = []
    for path in PATHS:
        current = host_rescore_path(
            packet,
            path,
            policy=policy,
            rules=rules,
            ruleset_sha256=rules_hash,
            arm_modes=("robust",),
        )
        current_arm = current["arms"]["robust"]
        current_obj = float(current_arm["objective"]) if current_arm.get("ok") else None
        search = spend_remaining_candidates(path, packet, rules=rules)
        scored = []
        best = None
        if search["bank"] > 0 and search.get("candidates"):
            scored = score_spend_candidates(
                packet,
                path,
                search["candidates"],
                policy=policy,
                rules=rules,
                ruleset_sha256=rules_hash,
                arm_mode="robust",
                limit=10,
            )
            ok = [item for item in scored if item.get("ok")]
            if ok:
                best = max(ok, key=lambda item: (item["objective"], item["extra_spend"]))
        rows.append(
            {
                "path_id": path["path_id"],
                "title": path["title"],
                "bank": search["bank"],
                "spent": search["spent"],
                "current_robust": current_obj,
                "trapped_spend": trapped_spend(path, packet),
                "candidate_count": len(search.get("candidates") or []),
                "scored": scored,
                "best": best,
            }
        )
        print(
            f"{path['path_id']} bank={search['bank']} "
            f"candidates={len(search.get('candidates') or [])} "
            f"best={None if best is None else best.get('objective')}",
            flush=True,
        )
    payload = {
        "schema_version": "1.0",
        "kind": "five_path_spend_remaining_review",
        "account_writes": False,
        "packet_sha256": packet.get("content_sha256"),
        "observed_at": packet.get("captured_at"),
        "paths": rows,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    OUT_MD.write_text(render_markdown(payload), encoding="utf-8")
    print("wrote", OUT_MD)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
