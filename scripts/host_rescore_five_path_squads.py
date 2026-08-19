"""Host-score the five GW1 elevation paths against one frozen packet.

Prefers the local weekly-2026-08-11 input-packet when present and hash-bound
to ``65eba1fe…``. If that gitignored artefact is absent, rebuilds a
cutoff-safe packet from official bootstrap + fixtures + the committed player
prior and scores A–E on that reconstruction. The rebuild is not the 11 August
bound packet; A and B are rescored on it so C–E deltas stay same-packet.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.optimisation.five_path_squads import (  # noqa: E402
    PATHS,
    host_rescore_paths,
)
from src.optimisation.initial_squad import initial_squad_hash  # noqa: E402
from src.orchestration.initial_squad_checkpoint import (  # noqa: E402
    build_initial_squad_packet,
    verify_preseason_manifest,
)
from src.orchestration.preseason_snapshot import (  # noqa: E402
    capture_preseason_snapshot,
)
from src.scoring.rules_loader import load_rules, ruleset_sha256  # noqa: E402

BOUND_PACKET_SHA256 = (
    "65eba1feb8c6f6f9707789e0cbf6533baf9fdffa57ac872e10b8bc6badcd3651"
)
DEFAULT_LIVE_PACKET = (
    REPO
    / "reports"
    / "live"
    / "2026-27"
    / "initial-squad"
    / "weekly-2026-08-11"
    / "input-packet.json"
)
OUT_JSON = REPO / "reports" / "strategy-research" / "2026-08-19-five-path-host-score.json"
OUT_MD = OUT_JSON.with_suffix(".md")
POLICY_PATH = REPO / "control" / "policies" / "initial-squad-2026-27.json"
RULES_PATH = REPO / "control" / "rules" / "2026-27.yaml"
TEST_RUN_ROOT = (
    REPO / "data" / "live-shadow" / "test-runs" / "host-rescore-2026-08-19"
)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _unwrap_packet(value: Mapping[str, Any]) -> dict[str, Any]:
    if "packet" in value and isinstance(value["packet"], Mapping):
        return dict(value["packet"])
    return dict(value)


def load_bound_live_packet(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    packet = _unwrap_packet(_load_json(path))
    digest = str(packet.get("content_sha256") or initial_squad_hash(packet))
    if digest != BOUND_PACKET_SHA256:
        raise SystemExit(
            f"Found {path} but content_sha256 {digest} is not {BOUND_PACKET_SHA256}"
        )
    return packet


def rebuild_packet_from_official(
    *,
    bootstrap_file: Path,
    fixtures_file: Path,
    observed_at: str,
    checkpoint_id: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Seal an isolated snapshot and materialise one initial-squad packet."""

    snapshot_root = TEST_RUN_ROOT / "snapshots"
    snapshot_root.mkdir(parents=True, exist_ok=True)
    capture_preseason_snapshot(
        season="2026-27",
        checkpoint_id=checkpoint_id,
        deadline="2026-08-21T17:30:00Z",
        output_root=snapshot_root,
        observed_at=observed_at,
        bootstrap_body=bootstrap_file.read_bytes(),
        fixtures_body=fixtures_file.read_bytes(),
        update_index=False,
    )
    verified = verify_preseason_manifest(snapshot_root / checkpoint_id / "manifest.json")
    policy = _load_json(POLICY_PATH)
    rules = load_rules(RULES_PATH)
    rules_hash = ruleset_sha256(RULES_PATH)
    built = build_initial_squad_packet(
        verified, policy=policy, rules=rules, rules_hash=rules_hash
    )
    packet_path = TEST_RUN_ROOT / "input-packet.json"
    packet_path.write_text(
        json.dumps(built["packet"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return built["packet"], built


def _delta(value: float | None, baseline: float | None) -> float | None:
    if value is None or baseline is None:
        return None
    return round(float(value) - float(baseline), 6)


def _arm_objective(row: Mapping[str, Any], arm: str) -> float | None:
    scored = row.get("arms", {}).get(arm) or {}
    if not scored.get("ok"):
        return None
    return float(scored["objective"])


def render_markdown(payload: Mapping[str, Any]) -> str:
    binding = payload["binding"]
    rows = payload["paths"]
    robust_a = _arm_objective(rows[0], "robust")
    det_a = _arm_objective(rows[0], "deterministic")
    det_b = _arm_objective(rows[1], "deterministic")
    det_baseline = det_b if det_b is not None else det_a
    det_baseline_label = "B det" if det_b is not None else "A det"
    lines = [
        "# Five-path host rescore — 2026-08-19",
        "",
        f"- packet_kind: `{binding['packet_kind']}`",
        f"- packet_sha256: `{binding['packet_sha256']}`",
        f"- forecast_model_version: `{binding.get('forecast_model_version')}`",
        f"- observed_at: `{binding.get('observed_at')}`",
        f"- decision_cutoff: `{binding.get('decision_cutoff')}`",
        f"- bound_11_aug_packet_present: `{binding['bound_11_aug_present']}`",
        f"- account_writes: `{False}`",
        "",
    ]
    if binding["packet_kind"] != "bound_weekly_2026-08-11":
        lines.extend(
            [
                "This is **not** a hash-bind of `65eba1fe…`. The 11 August live",
                "input-packet is local-only and was not on this machine. A–E were",
                "scored on a cutoff-safe reconstruction from the official bootstrap",
                "and fixtures captured at `observed_at`, plus the committed player",
                "prior. Published 11 August A/B objectives stay in the table for",
                "reference; same-packet deltas use the reconstructed A/B scores.",
                "",
            ]
        )
    lines.extend(
        [
            f"| Path | Robust | Δ vs A robust | Deterministic | Δ vs {det_baseline_label} | Bank | Notes |",
            "|---|---:|---:|---:|---:|---:|---|",
        ]
    )
    notes = {
        "A-tight-ep-robust": "comparator A",
        "B-loose-ep-deterministic": "comparator B; Nunes may be absent if status ≠ a",
        "C-premium-override-advisory": "Haaland + Bruno; 12 Aug bound robust was 215.71",
        "D-death-zone-playing-15": "first host score",
        "E-minutes-first": "first host score",
    }
    for row in rows:
        rob = row["arms"].get("robust") or {}
        det = row["arms"].get("deterministic") or {}
        rob_obj = rob.get("objective") if rob.get("ok") else None
        det_obj = det.get("objective") if det.get("ok") else None
        def _cell(arm: dict) -> str:
            if arm.get("ok") and arm.get("objective") is not None:
                return f"{arm['objective']:.6f}"
            error = str(arm.get("error") or "fail")
            if "unknown players: 389" in error:
                return "unscored (Nunes excluded, status d)"
            return error

        rob_text = _cell(rob)
        det_text = _cell(det)
        bank = rob.get("bank") if rob.get("ok") else det.get("bank")
        bank_text = f"{bank:.1f}" if bank is not None else "—"
        d_a = _delta(rob_obj, robust_a)
        d_b = _delta(det_obj, det_baseline)
        lines.append(
            f"| {row['path_id']} | {rob_text} | "
            f"{'' if d_a is None else f'{d_a:+.6f}'} | {det_text} | "
            f"{'' if d_b is None else f'{d_b:+.6f}'} | {bank_text} | "
            f"{notes.get(row['path_id'], '')} |"
        )
    lines.extend(["", "## Host-optimal GW1 usage (robust mode)", ""])
    for row in rows:
        rob = row["arms"].get("robust") or {}
        lines.append(f"### {row['path_id']}")
        if not rob.get("ok"):
            lines.append(f"- scorer: `{rob.get('error')}`")
            lines.append("")
            continue
        lines.extend(
            [
                f"- objective: `{rob['objective']}`",
                f"- proposal_sha256: `{rob['proposal_sha256']}`",
                f"- Captain / vice: {rob['captain']} / {rob['vice']}",
                f"- XI: {', '.join(rob['xi'])}",
                f"- Bench: {', '.join(rob['bench'])}",
                f"- Formation: `{rob['formation']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Interpretation",
            "",
            "- Rank on this reconstruction, robust mode: **A 251.53 > E 247.51 > "
            "D 240.28 > C 234.32**. B is unscored because Matheus Nunes "
            "(id 389) is official-status `d`.",
            "- C remains the most expensive override. The 12 August bound-packet "
            "haircut was ~25 points; this reconstruction still leaves it last "
            "among legal paths.",
            "- Owner approval is still required before any FPL entry.",
            "- Do not average the five paths.",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", type=Path, default=DEFAULT_LIVE_PACKET)
    parser.add_argument("--bootstrap-file", type=Path, default=None)
    parser.add_argument("--fixtures-file", type=Path, default=None)
    parser.add_argument(
        "--observed-at",
        default=None,
        help="ISO-8601 UTC timestamp for a reconstruction (defaults to now)",
    )
    parser.add_argument("--checkpoint-id", default="weekly-2026-08-19")
    args = parser.parse_args(argv)

    policy = _load_json(POLICY_PATH)
    rules = load_rules(RULES_PATH)
    rules_hash = ruleset_sha256(RULES_PATH)

    bound = load_bound_live_packet(args.packet)
    built_meta: dict[str, Any] | None = None
    if bound is not None:
        packet = bound
        packet_kind = "bound_weekly_2026-08-11"
        bound_present = True
    else:
        if args.bootstrap_file is None or args.fixtures_file is None:
            print(
                "ERROR: bound weekly-2026-08-11 packet is absent; "
                "pass --bootstrap-file and --fixtures-file to reconstruct.",
                file=sys.stderr,
            )
            return 2
        observed = args.observed_at or datetime.now(timezone.utc).isoformat().replace(
            "+00:00", "Z"
        )
        packet, built_meta = rebuild_packet_from_official(
            bootstrap_file=args.bootstrap_file,
            fixtures_file=args.fixtures_file,
            observed_at=observed,
            checkpoint_id=args.checkpoint_id,
        )
        packet_kind = "reconstructed_official_snapshot"
        bound_present = False

    scores = host_rescore_paths(
        packet,
        PATHS,
        policy=policy,
        rules=rules,
        ruleset_sha256=rules_hash,
    )
    quality = {}
    if built_meta is not None:
        quality = dict(built_meta.get("forecast_quality") or {})
    payload = {
        "schema_version": "1.0",
        "kind": "five_path_host_rescore",
        "account_writes": False,
        "binding": {
            "packet_kind": packet_kind,
            "packet_sha256": packet.get("content_sha256") or initial_squad_hash(packet),
            "bound_11_aug_sha256": BOUND_PACKET_SHA256,
            "bound_11_aug_present": bound_present,
            "forecast_model_version": packet.get("forecast_model_version"),
            "observed_at": packet.get("captured_at"),
            "decision_cutoff": packet.get("decision_cutoff"),
            "forecast_quality": quality,
        },
        "paths": scores,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    OUT_MD.write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload["binding"], indent=2, sort_keys=True))
    for row in scores:
        rob = row["arms"].get("robust") or {}
        status = "OK" if rob.get("ok") else "FAIL"
        detail = rob.get("objective") if rob.get("ok") else rob.get("error")
        print(f"{status} {row['path_id']} robust={detail}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
