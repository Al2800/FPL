"""Official FPL field benchmarks for ticket 06 / WP-05 residual work.

Evaluates cutoff-safe ``ep_next``, FDR and bootstrap team-strength ratings
against naive baselines when paired outcomes exist. When the live corpus has
pre-deadline snapshots but no finished Gameweek outcomes, the report records
``insufficient_sample`` rather than inventing metrics (plan §11.2 null results).

Fields are never auto-promoted into the live forecast; promotion requires an
explicit owner gate after a positive, reproducible marginal-value result.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
from typing import Any


BENCHMARK_VERSION = "1.0"
DEFAULT_MINIMUM_PAIRED = 38  # one full season of player-GW rows is not required;
# callers may lower this for synthetic tests. Live corpus uses the default.


class OfficialFieldBenchmarkError(ValueError):
    """Raised when benchmark inputs are malformed."""


def _artifact_hash(value: Mapping[str, Any]) -> str:
    body = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(body).hexdigest()


def _mae(predicted: Sequence[float], actual: Sequence[float]) -> float:
    if len(predicted) != len(actual) or not predicted:
        raise OfficialFieldBenchmarkError("MAE requires equal non-empty sequences")
    errors = [abs(float(a) - float(p)) for p, a in zip(predicted, actual, strict=True)]
    return sum(errors) / len(errors)


def _correlation(left: Sequence[float], right: Sequence[float]) -> float | None:
    if len(left) < 2 or len(left) != len(right):
        return None
    mean_l = sum(left) / len(left)
    mean_r = sum(right) / len(right)
    num = sum((a - mean_l) * (b - mean_r) for a, b in zip(left, right, strict=True))
    den_l = math.sqrt(sum((a - mean_l) ** 2 for a in left))
    den_r = math.sqrt(sum((b - mean_r) ** 2 for b in right))
    if den_l == 0 or den_r == 0:
        return None
    return num / (den_l * den_r)


def assess_element_summary_adoption(
    *,
    summary_paths: Sequence[Path | str],
) -> dict[str, Any]:
    """Document whether element-summary histories are safe to adopt as priors."""

    paths = [Path(path) for path in summary_paths]
    existing = [path for path in paths if path.is_file()]
    if not existing:
        return {
            "status": "no_corpus",
            "n_files": 0,
            "adopt": False,
            "duplication_note": (
                "No element-summary artifacts are present in the evaluation "
                "corpus. The governed vaastav merged_gw warehouse already "
                "supplies past-season player-match histories for priors."
            ),
            "leakage_note": (
                "element-summary history rows can include the current "
                "Gameweek once fixtures start; any adoption must filter "
                "strictly by kickoff/available_at <= decision cutoff. Without "
                "a cutoff-labelled corpus this leakage risk cannot be measured."
            ),
            "retention_note": (
                "Official element-summary payloads are restricted Tier-0 "
                "snapshots (ADR-0001/0002): private local retention only, no "
                "redistribution. Expanding capture without a proven prior "
                "gain increases retention surface for no decision benefit."
            ),
            "recommendation": (
                "Do not adopt. Re-run after a cutoff-safe element-summary "
                "corpus exists and a paired ablation vs vaastav priors is "
                "positive."
            ),
        }
    return {
        "status": "corpus_present_unevaluated",
        "n_files": len(existing),
        "adopt": False,
        "duplication_note": (
            "element-summary histories overlap the vaastav warehouse for "
            "completed seasons; treat as a challenger prior, not a second "
            "source of truth."
        ),
        "leakage_note": (
            "Require available_at <= cutoff on every history row before "
            "joining into forecast features."
        ),
        "retention_note": (
            "Retain only the bounded player IDs already registered for "
            "capture; do not widen the set until marginal value is proven."
        ),
        "recommendation": (
            "Corpus files exist but no paired time-based ablation has been "
            "run; leave unadopted (null result retained)."
        ),
    }


def evaluate_official_fields(
    *,
    paired_rows: Sequence[Mapping[str, Any]],
    bootstrap_strength_pairs: Sequence[Mapping[str, Any]],
    element_summary_paths: Sequence[Path | str],
    predeadline_snapshot_count: int,
    minimum_paired_outcomes: int = DEFAULT_MINIMUM_PAIRED,
    notes: str | None = None,
) -> dict[str, Any]:
    """Return a sealed benchmark report for official forecast fields.

    ``paired_rows`` must each contain ``ep_next``, ``naive_points``,
    ``actual_points``, and optionally FDR / team-strength columns for the
    secondary comparisons.
    """

    if predeadline_snapshot_count < 0:
        raise OfficialFieldBenchmarkError("predeadline_snapshot_count must be >= 0")
    rows = [dict(row) for row in paired_rows]
    for index, row in enumerate(rows):
        for field in ("ep_next", "naive_points", "actual_points"):
            if field not in row:
                raise OfficialFieldBenchmarkError(
                    f"paired_rows[{index}] missing {field}"
                )

    element = assess_element_summary_adoption(summary_paths=element_summary_paths)
    n_paired = len(rows)
    sufficient = n_paired >= int(minimum_paired_outcomes)

    fields: dict[str, Any] = {}
    improved: list[str] = []

    if not sufficient:
        reason = (
            f"Need at least {minimum_paired_outcomes} cutoff-safe "
            f"player-Gameweek pairs with realised points; found {n_paired}. "
            f"Pre-deadline snapshots observed: {predeadline_snapshot_count}."
        )
        for name in ("ep_next", "fdr", "bootstrap_team_strength"):
            fields[name] = {
                "status": "insufficient_sample",
                "reason": reason,
                "n": n_paired,
                "mae": None,
                "promoted": False,
            }
    else:
        ep = [float(row["ep_next"]) for row in rows]
        naive = [float(row["naive_points"]) for row in rows]
        actual = [float(row["actual_points"]) for row in rows]
        ep_mae = _mae(ep, actual)
        naive_mae = _mae(naive, actual)
        fields["ep_next"] = {
            "status": "ok",
            "n": n_paired,
            "mae": round(ep_mae, 6),
            "naive_mae": round(naive_mae, 6),
            "beats_naive": bool(ep_mae < naive_mae),
            "promoted": False,
            "baseline_refs": ["naive_rolling_or_last_points", "odds_implied_when_registered"],
        }
        if ep_mae < naive_mae:
            improved.append("ep_next")

        if all("fdr_multiplier" in row for row in rows):
            # FDR is ordinal difficulty; compare its mapped multiplier to a
            # flat-1.0 naive and to the existing team-strength multiplier when present.
            fdr_mult = [float(row["fdr_multiplier"]) for row in rows]
            # Proxy error: distance of multiplier from realised clean-sheet proxy is
            # not points MAE; use correlation of FDR multiplier vs actual points as
            # a weak ordinal signal when CS labels absent.
            fdr_corr = _correlation(fdr_mult, actual)
            fields["fdr"] = {
                "status": "ok",
                "n": n_paired,
                "correlation_with_actual_points": fdr_corr,
                "note": (
                    "FDR is an official ordinal difficulty; this reports "
                    "association with realised points, not a substitute for "
                    "Elo/team-context models."
                ),
                "promoted": False,
            }
            if (
                all("team_strength_multiplier" in row for row in rows)
                and fdr_corr is not None
            ):
                team_corr = _correlation(
                    [float(row["team_strength_multiplier"]) for row in rows],
                    actual,
                )
                fields["fdr"]["team_strength_correlation"] = team_corr
                if team_corr is not None and fdr_corr > team_corr:
                    improved.append("fdr")
        else:
            fields["fdr"] = {
                "status": "insufficient_sample",
                "reason": "paired rows lack fdr_multiplier",
                "n": n_paired,
                "promoted": False,
            }

        strength_pairs = [dict(row) for row in bootstrap_strength_pairs]
        if len(strength_pairs) >= 3 and all(
            "official_attack" in row and "model_attack" in row for row in strength_pairs
        ):
            official = [float(row["official_attack"]) for row in strength_pairs]
            model = [float(row["model_attack"]) for row in strength_pairs]
            fields["bootstrap_team_strength"] = {
                "status": "ok",
                "n": len(strength_pairs),
                "correlation_with_model_attack": _correlation(official, model),
                "note": (
                    "Compares official bootstrap attack ratings to the lab "
                    "team-strength/attack-defence model scale; not a points MAE."
                ),
                "promoted": False,
            }
        else:
            fields["bootstrap_team_strength"] = {
                "status": "insufficient_sample",
                "reason": (
                    "Need >=3 clubs with official_attack and model_attack pairs"
                ),
                "n": len(strength_pairs),
                "promoted": False,
            }

    fields["element_summary"] = element

    status = "ok" if sufficient else "insufficient_sample"
    report = {
        "report_id": "official-fpl-field-benchmarks",
        "benchmark_version": BENCHMARK_VERSION,
        "observed_at": datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "status": status,
        "n_predeadline_snapshots": int(predeadline_snapshot_count),
        "n_paired_outcomes": n_paired,
        "minimum_paired_outcomes": int(minimum_paired_outcomes),
        "fields": fields,
        "promotion": {
            "improved_vs_naive": improved,
            "promoted_fields": [],
            "policy": (
                "Null or positive results are recorded; promotion into the "
                "live forecast requires an explicit owner gate and retained "
                "source/transform versions (plan §11.2)."
            ),
        },
        "notes": notes
        or (
            "Live 2026/27 has preseason/pre-deadline captures but no finished "
            "Gameweek outcomes yet; metrics stay insufficient until paired."
        ),
        "wp05_alignment": (
            "docs/data-sources/wp05-status.md deferred official ep_next/FDR "
            "until a pre-deadline snapshot corpus with outcomes exists."
        ),
    }
    report["content_sha256"] = _artifact_hash(
        {key: value for key, value in report.items() if key != "content_sha256"}
    )
    return report


def write_official_field_benchmark_report(
    out_dir: Path,
    report: Mapping[str, Any],
) -> dict[str, Path]:
    """Persist JSON + Markdown benchmark artefacts."""

    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "official-fpl-field-benchmarks.json"
    md_path = out_dir / "official-fpl-field-benchmarks.md"
    payload = dict(report)
    json_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    fields = payload.get("fields") or {}
    lines = [
        "# Official FPL field benchmarks",
        "",
        str(payload.get("notes") or ""),
        "",
        f"- Status: `{payload.get('status')}`",
        f"- Pre-deadline snapshots: `{payload.get('n_predeadline_snapshots')}`",
        f"- Paired outcomes: `{payload.get('n_paired_outcomes')}` "
        f"(minimum `{payload.get('minimum_paired_outcomes')}`)",
        f"- Content hash: `{payload.get('content_sha256')}`",
        "",
        "## Fields",
        "",
    ]
    for name in ("ep_next", "fdr", "bootstrap_team_strength", "element_summary"):
        row = fields.get(name) or {}
        lines.append(f"### {name}")
        lines.append("")
        lines.append(f"- Status: `{row.get('status')}`")
        if row.get("reason"):
            lines.append(f"- Reason: {row['reason']}")
        if row.get("mae") is not None:
            lines.append(f"- MAE: `{row.get('mae')}` (naive `{row.get('naive_mae')}`)")
        if row.get("duplication_note"):
            lines.append(f"- Duplication: {row['duplication_note']}")
        if row.get("leakage_note"):
            lines.append(f"- Leakage: {row['leakage_note']}")
        if row.get("retention_note"):
            lines.append(f"- Retention: {row['retention_note']}")
        if row.get("recommendation"):
            lines.append(f"- Recommendation: {row['recommendation']}")
        lines.append(f"- Promoted: `{row.get('promoted', False)}`")
        lines.append("")
    promo = payload.get("promotion") or {}
    lines.extend(
        [
            "## Promotion",
            "",
            f"- Improved vs naive: `{', '.join(promo.get('improved_vs_naive') or []) or 'none'}`",
            f"- Promoted fields: `{', '.join(promo.get('promoted_fields') or []) or 'none'}`",
            f"- Policy: {promo.get('policy')}",
            "",
        ]
    )
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return {"json": json_path, "markdown": md_path}


def count_predeadline_bootstrap_snapshots(roots: Sequence[Path]) -> int:
    """Count bootstrap-static JSON files under known capture roots (offline)."""

    count = 0
    for root in roots:
        if not root.exists():
            continue
        count += sum(1 for _ in root.rglob("*bootstrap-static*.json"))
        count += sum(1 for _ in root.rglob("api_bootstrap-static.json"))
    return count
