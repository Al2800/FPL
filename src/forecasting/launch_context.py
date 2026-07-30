"""Validate and apply prospective 2026/27 cold-start context."""

from __future__ import annotations

from copy import deepcopy
import csv
import io
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from typing import Any, Mapping, Sequence

from src.ingestion.acquisition import content_hash


class LaunchContextError(ValueError):
    """Raised when launch context is ambiguous, inconsistent, or temporally late."""


FATIGUE_TIERS = ("none", "moderate", "high", "extreme")


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def artifact_hash(value: Mapping[str, Any]) -> str:
    payload = {key: item for key, item in value.items() if key != "content_sha256"}
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def _timestamp(value: Any, field: str) -> tuple[str, datetime]:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise LaunchContextError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise LaunchContextError(f"{field} must include a timezone")
    utc = parsed.astimezone(timezone.utc)
    return utc.isoformat().replace("+00:00", "Z"), utc


def _integer_set(values: Any, field: str) -> set[int]:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        raise LaunchContextError(f"{field} must be a list")
    parsed = [int(value) for value in values]
    if len(parsed) != len(set(parsed)):
        raise LaunchContextError(f"{field} contains duplicate identities")
    return set(parsed)


def load_launch_context(path: Path) -> dict[str, Any]:
    """Load a self-hashed launch-context artifact."""

    value = json.loads(path.read_text(encoding="utf-8"))
    expected = str(value.get("content_sha256", ""))
    if len(expected) != 64 or artifact_hash(value) != expected:
        raise LaunchContextError("Launch-context content hash mismatch")
    return value


def load_world_cup_priors(path: Path) -> list[dict[str, str]]:
    """Load the World Cup ledger without performing permissive name joins."""

    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def world_cup_csv_hash(rows: Sequence[Mapping[str, Any]]) -> str:
    """Canonical CSV hash helper for synthetic and generated ledgers."""

    if not rows:
        return hashlib.sha256(b"").hexdigest()
    fields = list(rows[0])
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return hashlib.sha256(output.getvalue().encode("utf-8")).hexdigest()


def _validated_context(
    bootstrap: Mapping[str, Any],
    context: Mapping[str, Any],
    *,
    cutoff: datetime,
) -> tuple[set[int], set[int], set[int], dict[str, float], dict[str, Any]]:
    source = context.get("source_bindings", {}).get("official_bootstrap", {})
    _, observed = _timestamp(source.get("observed_at"), "official_bootstrap.observed_at")
    if observed >= cutoff:
        raise LaunchContextError(
            "Official launch context must be observed strictly before decision cutoff"
        )
    if len(str(source.get("sha256", ""))) != 64:
        raise LaunchContextError("Official bootstrap binding has no valid SHA-256")

    raw_players = list(bootstrap.get("elements", []))
    player_codes = [int(row["code"]) for row in raw_players]
    if len(player_codes) != len(set(player_codes)):
        raise LaunchContextError("Official bootstrap contains duplicate player codes")
    official_teams = {int(row["id"]): row for row in bootstrap.get("teams", [])}
    team_ids = set(official_teams)

    promoted_rows = list(context.get("promoted_teams", []))
    promoted = {int(row["team_id"]) for row in promoted_rows}
    if len(promoted) != len(promoted_rows):
        raise LaunchContextError("Promoted-team identities are duplicated")
    if not promoted or not promoted <= team_ids:
        raise LaunchContextError("Promoted-team identities are empty or unknown")
    for row in promoted_rows:
        official = official_teams[int(row["team_id"])]
        if int(row.get("team_code", -1)) != int(official.get("code", -2)):
            raise LaunchContextError("Promoted-team stable code does not match official team")
        if str(row.get("name", "")) != str(official.get("name", "")):
            raise LaunchContextError("Promoted-team name does not match official team")

    new = _integer_set(context.get("new_player_codes", []), "new_player_codes")
    transferred = _integer_set(
        context.get("transferred_player_codes", []), "transferred_player_codes"
    )
    known_codes = set(player_codes)
    if not new or not new <= known_codes:
        raise LaunchContextError("New-player identities are empty or unknown")
    if not transferred or not transferred <= known_codes:
        raise LaunchContextError("Transferred-player identities are empty or unknown")

    policy = context.get("classification_policy", {})
    precedence = list(policy.get("precedence", []))
    expected_precedence = [
        "promoted_team",
        "new_to_fpl",
        "transferred_player",
        "established",
    ]
    if precedence != expected_precedence:
        raise LaunchContextError("Cold-start precedence is not the registered policy")
    risk = {
        str(key): float(value)
        for key, value in context.get("cold_start_risk", {}).items()
    }
    if set(risk) != set(expected_precedence):
        raise LaunchContextError("Cold-start risk is incomplete")
    if any(value < 0.0 or value > 1.0 for value in risk.values()):
        raise LaunchContextError("Cold-start risk must be between zero and one")

    return promoted, new, transferred, risk, deepcopy(dict(policy))


def apply_launch_context(
    *,
    bootstrap: Mapping[str, Any],
    context: Mapping[str, Any],
    world_cup_rows: Sequence[Mapping[str, Any]],
    official_bootstrap_source_sha256: str,
    world_cup_source_sha256: str,
    decision_cutoff: str,
    gameweek: int,
) -> dict[str, Any]:
    """Classify the official universe and attach cutoff-safe World Cup priors."""

    cutoff_text, cutoff = _timestamp(decision_cutoff, "decision_cutoff")
    if gameweek < 1:
        raise LaunchContextError("gameweek must be positive")
    promoted, new, transferred, class_risk, policy = _validated_context(
        bootstrap, context, cutoff=cutoff
    )
    bindings = context.get("source_bindings", {})
    if official_bootstrap_source_sha256 != str(
        bindings.get("official_bootstrap", {}).get("sha256", "")
    ):
        raise LaunchContextError("Official bootstrap source hash mismatch")
    if world_cup_source_sha256 != str(
        bindings.get("world_cup_priors", {}).get("sha256", "")
    ):
        raise LaunchContextError("World Cup prior source hash mismatch")

    world_policy = context.get("world_cup_policy", {})
    tier_scores = {
        str(key): float(value)
        for key, value in world_policy.get("fatigue_tier_score", {}).items()
    }
    if set(tier_scores) != set(FATIGUE_TIERS):
        raise LaunchContextError("World Cup fatigue tiers are incomplete")
    fades = [float(value) for value in world_policy.get("gameweek_fade", [])]
    if not fades or any(value < 0.0 or value > 1.0 for value in fades):
        raise LaunchContextError("World Cup gameweek fade is invalid")
    fade = fades[gameweek - 1] if gameweek <= len(fades) else 0.0

    official_codes = {int(row["code"]) for row in bootstrap.get("elements", [])}
    world_by_code: dict[int, dict[str, Any]] = {}
    seen_world_codes: set[int] = set()
    degraded: list[dict[str, Any]] = []
    coverage = {
        "ledger_rows": len(world_cup_rows),
        "matched_rows": 0,
        "blank_code_rows": 0,
        "non_current_code_rows": 0,
        "late_rows": 0,
        "missing_return_to_training_rows": 0,
    }
    for index, raw in enumerate(world_cup_rows, start=2):
        row = dict(raw)
        code_text = str(row.get("fpl_code", "")).strip()
        if not code_text:
            coverage["blank_code_rows"] += 1
            degraded.append(
                {
                    "feature": "world_cup_prior",
                    "row": index,
                    "reason": "blank_stable_fpl_code_no_name_join",
                }
            )
            continue
        try:
            code = int(code_text)
        except ValueError as exc:
            raise LaunchContextError(
                f"World Cup stable code is not an integer at row {index}: {code_text}"
            ) from exc
        if code in seen_world_codes:
            raise LaunchContextError(f"Duplicate World Cup stable code: {code}")
        seen_world_codes.add(code)
        if code not in official_codes:
            coverage["non_current_code_rows"] += 1
            degraded.append(
                {
                    "feature": "world_cup_prior",
                    "fpl_code": code,
                    "reason": "stable_code_not_in_current_official_universe",
                }
            )
            continue
        observed_text, observed = _timestamp(
            row.get("observed_at"), f"world_cup_rows[{index}].observed_at"
        )
        if observed >= cutoff:
            coverage["late_rows"] += 1
            degraded.append(
                {
                    "feature": "world_cup_prior",
                    "fpl_code": code,
                    "reason": "observed_at_or_after_decision_cutoff",
                }
            )
            continue
        tier = str(row.get("fatigue_prior", ""))
        if tier not in tier_scores:
            raise LaunchContextError(
                f"Unknown World Cup fatigue tier for stable code {code}: {tier}"
            )
        return_date = str(row.get("return_to_training_date", "")).strip() or None
        if return_date is None:
            coverage["missing_return_to_training_rows"] += 1
        world_by_code[code] = {
            "status": "matched",
            "fatigue_tier": tier,
            "fatigue_score": tier_scores[tier],
            "gameweek_fade": fade,
            "effective_fatigue": round(tier_scores[tier] * fade, 6),
            "wc_minutes": (
                int(row["wc_minutes"]) if str(row.get("wc_minutes", "")).strip() else None
            ),
            "elimination_date": str(row.get("elimination_date", "")) or None,
            "return_to_training_date": return_date,
            "observed_at": observed_text,
        }
        coverage["matched_rows"] += 1

    players: list[dict[str, Any]] = []
    class_counts = {
        "promoted_team": 0,
        "new_to_fpl": 0,
        "transferred_player": 0,
        "established": 0,
    }
    for row in bootstrap.get("elements", []):
        code = int(row["code"])
        team_id = int(row["team"])
        cold_class = (
            "promoted_team"
            if team_id in promoted
            else "new_to_fpl"
            if code in new
            else "transferred_player"
            if code in transferred
            else "established"
        )
        class_counts[cold_class] += 1
        players.append(
            {
                "player_id": int(row["id"]),
                "fpl_code": code,
                "team_id": team_id,
                "cold_start_class": cold_class,
                "cold_start_risk": class_risk[cold_class],
                "is_new_to_fpl": code in new,
                "changed_club": code in transferred,
                "world_cup": world_by_code.get(
                    code,
                    {
                        "status": "not_in_admitted_ledger",
                        "fatigue_tier": None,
                        "fatigue_score": 0.0,
                        "gameweek_fade": fade,
                        "effective_fatigue": 0.0,
                    },
                ),
            }
        )

    expected = {
        str(key): int(value)
        for key, value in policy.get("expected_class_counts", {}).items()
    }
    if expected and class_counts != expected:
        raise LaunchContextError(
            f"Official universe no longer matches frozen class counts: {class_counts}"
        )
    if sum(class_counts.values()) != len(players):
        raise LaunchContextError("Not every official player received exactly one class")

    result: dict[str, Any] = {
        "schema_version": "1.0",
        "season": str(context.get("season", "")),
        "decision_cutoff": cutoff_text,
        "gameweek": gameweek,
        "classification_policy": policy,
        "class_counts": class_counts,
        "world_cup_coverage": coverage,
        "degraded_features": degraded,
        "players": sorted(players, key=lambda item: item["player_id"]),
        "source_bindings": deepcopy(dict(context.get("source_bindings", {}))),
    }
    result["content_sha256"] = artifact_hash(result)
    return result

class LaunchContextBuildError(LaunchContextError):
    """Raised when a successor launch context cannot be derived safely."""


class LaunchContextBuildConflict(LaunchContextBuildError):
    """Raised when a content-addressed successor path contains other bytes."""


_COLD_START_RISK = {
    "promoted_team": 0.10,
    "new_to_fpl": 0.08,
    "transferred_player": 0.08,
    "established": 0.0,
}
_WORLD_CUP_POLICY = {
    "fatigue_tier_score": {
        "none": 0.0,
        "moderate": 0.35,
        "high": 0.70,
        "extreme": 1.0,
    },
    "gameweek_fade": [1.0, 1.0, 0.5, 0.5, 0.25, 0.0],
    "return_to_training_date_policy": "cited_pre_cutoff_values_only",
    "missing_return_date_policy": "degrade_without_neutral_imputation",
}
_PRECEDENCE = [
    "promoted_team",
    "new_to_fpl",
    "transferred_player",
    "established",
]


def _canonical_file_bytes(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _source_temporal_binding(
    *,
    source_id: str,
    sha256: str,
    observed_at: str,
    available_at: str,
    cutoff: datetime,
    label: str,
    season: str | None = None,
) -> dict[str, str]:
    observed_text, observed = _timestamp(observed_at, f"{label}.observed_at")
    available_text, available = _timestamp(available_at, f"{label}.available_at")
    if observed < available:
        raise LaunchContextBuildError(
            f"{label}.observed_at must not be earlier than available_at"
        )
    if observed >= cutoff or available >= cutoff:
        raise LaunchContextBuildError(f"{label} must be strictly before decision cutoff")
    result = {
        "source_id": source_id,
        "sha256": sha256,
        "observed_at": observed_text,
        "available_at": available_text,
    }
    if season is not None:
        result["season"] = season
    return result


def _load_bootstrap_bytes(path: Path) -> tuple[bytes, dict[str, Any]]:
    try:
        body = path.read_bytes()
        value = json.loads(body)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LaunchContextBuildError(f"Unable to read official bootstrap: {path}") from exc
    if not isinstance(value, dict):
        raise LaunchContextBuildError("Official bootstrap must be a JSON object")
    return body, value


def _integer(value: Any, field: str) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError) as exc:
        raise LaunchContextBuildError(f"{field} must be a non-empty integer") from exc


def _load_prior_roster(path: Path) -> tuple[bytes, dict[int, int]]:
    try:
        body = path.read_bytes()
        rows = list(csv.DictReader(io.StringIO(body.decode("utf-8-sig"))))
    except (OSError, UnicodeDecodeError, csv.Error) as exc:
        raise LaunchContextBuildError(f"Unable to read prior roster CSV: {path}") from exc
    if not rows:
        raise LaunchContextBuildError("Prior roster CSV must contain at least one row")
    header = set(rows[0])
    missing = {"code", "team_code"} - header
    if missing:
        raise LaunchContextBuildError(
            "Prior roster CSV is missing required columns: " + ", ".join(sorted(missing))
        )
    result: dict[int, int] = {}
    for index, row in enumerate(rows, start=2):
        code = _integer(row.get("code"), f"prior_roster[{index}].code")
        team_code = _integer(row.get("team_code"), f"prior_roster[{index}].team_code")
        if code in result:
            raise LaunchContextBuildError(f"Duplicate prior stable FPL code: {code}")
        result[code] = team_code
    return body, result


def _load_world_cup_rows(path: Path) -> tuple[bytes, list[dict[str, str]]]:
    try:
        body = path.read_bytes()
        rows = list(csv.DictReader(io.StringIO(body.decode("utf-8-sig"))))
    except (OSError, UnicodeDecodeError, csv.Error) as exc:
        raise LaunchContextBuildError(f"Unable to read World Cup priors CSV: {path}") from exc
    if not rows or not {"fpl_code", "observed_at"} <= set(rows[0]):
        raise LaunchContextBuildError(
            "World Cup priors CSV must contain fpl_code and observed_at columns"
        )
    return body, [dict(row) for row in rows]


def _official_universe(bootstrap: Mapping[str, Any]) -> tuple[dict[int, dict[str, Any]], dict[int, dict[str, Any]]]:
    teams: dict[int, dict[str, Any]] = {}
    team_codes: set[int] = set()
    for index, row in enumerate(bootstrap.get("teams", []), start=1):
        if not isinstance(row, Mapping):
            raise LaunchContextBuildError(f"Official team row {index} must be an object")
        team_id = _integer(row.get("id"), f"official_teams[{index}].id")
        team_code = _integer(row.get("code"), f"official_teams[{index}].code")
        if team_id in teams or team_code in team_codes:
            raise LaunchContextBuildError("Official bootstrap has duplicate team identity")
        teams[team_id] = {"team_id": team_id, "team_code": team_code, "name": str(row.get("name", ""))}
        team_codes.add(team_code)
    if not teams:
        raise LaunchContextBuildError("Official bootstrap has no teams")

    players: dict[int, dict[str, Any]] = {}
    for index, row in enumerate(bootstrap.get("elements", []), start=1):
        if not isinstance(row, Mapping):
            raise LaunchContextBuildError(f"Official player row {index} must be an object")
        code = _integer(row.get("code"), f"official_players[{index}].code")
        team_id = _integer(row.get("team"), f"official_players[{index}].team")
        player_id = _integer(row.get("id"), f"official_players[{index}].id")
        if code in players:
            raise LaunchContextBuildError(f"Duplicate official stable FPL code: {code}")
        if team_id not in teams:
            raise LaunchContextBuildError(f"Official player {code} has unknown team id: {team_id}")
        players[code] = {
            "player_id": player_id,
            "fpl_code": code,
            "team_id": team_id,
            "team_code": teams[team_id]["team_code"],
        }
    if not players:
        raise LaunchContextBuildError("Official bootstrap has no players")
    return teams, players


def _world_cup_coverage(
    rows: Sequence[Mapping[str, str]], *, current_codes: set[int], cutoff: datetime
) -> dict[str, int]:
    seen: set[int] = set()
    coverage = {
        "ledger_rows": len(rows),
        "current_official_code_matches": 0,
        "non_current_stable_codes": 0,
        "blank_stable_codes": 0,
        "late_rows": 0,
        "return_to_training_dates_present": 0,
    }
    for index, row in enumerate(rows, start=2):
        code_text = str(row.get("fpl_code", "")).strip()
        if not code_text:
            coverage["blank_stable_codes"] += 1
            continue
        code = _integer(code_text, f"world_cup_rows[{index}].fpl_code")
        if code in seen:
            raise LaunchContextBuildError(f"Duplicate World Cup stable FPL code: {code}")
        seen.add(code)
        if code not in current_codes:
            coverage["non_current_stable_codes"] += 1
            continue
        _, observed = _timestamp(row.get("observed_at"), f"world_cup_rows[{index}].observed_at")
        if observed >= cutoff:
            coverage["late_rows"] += 1
            continue
        coverage["current_official_code_matches"] += 1
        if str(row.get("return_to_training_date", "")).strip():
            coverage["return_to_training_dates_present"] += 1
    return coverage


def _write_immutable_bytes(path: Path, body: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != body:
            raise LaunchContextBuildConflict(
                f"Immutable launch-context artifact has different bytes: {path}"
            )
        return
    path.write_bytes(body)


def _verify_derived_manifest(manifest_path: Path, context_dir: Path) -> dict[str, Any]:
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LaunchContextBuildConflict(
            f"Existing launch-context manifest is unreadable: {manifest_path}"
        ) from exc
    if not isinstance(manifest, dict) or manifest.get("content_sha256") != artifact_hash(manifest):
        raise LaunchContextBuildConflict("Existing launch-context manifest self-hash is invalid")
    for value in manifest.get("artifacts", {}).values():
        if not isinstance(value, Mapping):
            raise LaunchContextBuildConflict("Existing launch-context artifact entry is invalid")
        candidate = context_dir / str(value.get("path", ""))
        if not candidate.is_file() or content_hash(candidate.read_bytes()) != value.get("sha256"):
            raise LaunchContextBuildConflict(
                f"Existing launch-context artifact failed hash validation: {candidate}"
            )
    return manifest


def build_launch_context(
    *,
    season: str,
    bootstrap_path: Path,
    bootstrap_observed_at: str,
    bootstrap_available_at: str,
    prior_roster_path: Path,
    prior_roster_observed_at: str,
    prior_roster_available_at: str,
    world_cup_priors_path: Path,
    world_cup_observed_at: str,
    world_cup_available_at: str,
    context_observed_at: str,
    context_available_at: str,
    decision_cutoff: str,
    output_root: Path,
    previous_season: str = "2025-26",
) -> dict[str, Any]:
    """Build an immutable successor context from explicit, cutoff-safe inputs."""

    if season != "2026-27":
        raise LaunchContextBuildError("Only season 2026-27 is supported")
    cutoff_text, cutoff = _timestamp(decision_cutoff, "decision_cutoff")
    context_observed, context_observed_dt = _timestamp(context_observed_at, "context_observed_at")
    context_available, context_available_dt = _timestamp(context_available_at, "context_available_at")
    if context_observed_dt > context_available_dt or context_available_dt >= cutoff:
        raise LaunchContextBuildError("Context timestamps must be ordered and strictly before cutoff")

    bootstrap_body, bootstrap = _load_bootstrap_bytes(bootstrap_path)
    prior_body, prior_roster = _load_prior_roster(prior_roster_path)
    world_cup_body, world_cup_rows = _load_world_cup_rows(world_cup_priors_path)
    bootstrap_hash = content_hash(bootstrap_body)
    prior_hash = content_hash(prior_body)
    world_cup_hash = content_hash(world_cup_body)
    bootstrap_binding = _source_temporal_binding(
        source_id="fpl-official-endpoints", sha256=bootstrap_hash,
        observed_at=bootstrap_observed_at, available_at=bootstrap_available_at,
        cutoff=cutoff, label="official_bootstrap",
    )
    prior_binding = _source_temporal_binding(
        source_id="vaastav-fpl-historical", sha256=prior_hash,
        observed_at=prior_roster_observed_at, available_at=prior_roster_available_at,
        cutoff=cutoff, label="previous_season_players", season=previous_season,
    )
    world_cup_binding = _source_temporal_binding(
        source_id="world-cup-2026", sha256=world_cup_hash,
        observed_at=world_cup_observed_at, available_at=world_cup_available_at,
        cutoff=cutoff, label="world_cup_priors",
    )
    if any(
        _timestamp(item["observed_at"], "source.observed_at")[1] > context_observed_dt
        or _timestamp(item["available_at"], "source.available_at")[1] > context_available_dt
        for item in (bootstrap_binding, prior_binding, world_cup_binding)
    ):
        raise LaunchContextBuildError("Context cannot precede one of its source observations")

    teams, players = _official_universe(bootstrap)
    current_codes = set(players)
    prior_codes = set(prior_roster)
    promoted_team_codes = {
        row["team_code"] for row in teams.values()
    } - set(prior_roster.values())
    new_codes = current_codes - prior_codes
    transferred_codes = {
        code for code in current_codes & prior_codes
        if players[code]["team_code"] != prior_roster[code]
    }
    primary_counts = {name: 0 for name in _PRECEDENCE}
    for player in players.values():
        code = player["fpl_code"]
        primary = (
            "promoted_team" if player["team_code"] in promoted_team_codes
            else "new_to_fpl" if code in new_codes
            else "transferred_player" if code in transferred_codes
            else "established"
        )
        primary_counts[primary] += 1
    coverage = _world_cup_coverage(world_cup_rows, current_codes=current_codes, cutoff=cutoff)
    promoted_teams = sorted(
        (row for row in teams.values() if row["team_code"] in promoted_team_codes),
        key=lambda row: row["team_id"],
    )
    universe_delta = {
        "baseline": "supplied_previous_season_roster",
        "added_player_codes": sorted(new_codes),
        "removed_player_codes": sorted(prior_codes - current_codes),
        "changed_team_codes": sorted(transferred_codes),
        "promoted_team_codes": sorted(promoted_team_codes),
        "current_player_count": len(current_codes),
        "prior_player_count": len(prior_codes),
    }
    context: dict[str, Any] = {
        "schema_version": "1.1",
        "season": season,
        "status": "prospective_shadow_context",
        "observed_at": context_observed,
        "available_at": context_available,
        "decision_cutoff": cutoff_text,
        "source_bindings": {
            "official_bootstrap": bootstrap_binding,
            "previous_season_players": prior_binding,
            "world_cup_priors": world_cup_binding,
        },
        "promoted_teams": promoted_teams,
        "promoted_team_ids": [row["team_id"] for row in promoted_teams],
        "new_player_codes": sorted(new_codes),
        "transferred_player_codes": sorted(transferred_codes),
        "classification_policy": {
            "identity_key": "stable_fpl_code",
            "precedence": _PRECEDENCE,
            "expected_class_counts": primary_counts,
            "orthogonal_flags_retained": ["is_new_to_fpl", "changed_club", "world_cup"],
        },
        "cold_start_risk": _COLD_START_RISK,
        "world_cup_policy": _WORLD_CUP_POLICY,
        "world_cup_coverage": coverage,
        "universe_delta": universe_delta,
        "unknown_policy": {
            "unknown_promoted_or_player_identity": "block",
            "duplicate_stable_code": "block",
            "official_context_at_or_after_cutoff": "block",
            "world_cup_row_at_or_after_cutoff": "exclude_and_degrade",
            "non_current_world_cup_code": "exclude_and_degrade",
            "blank_world_cup_code": "exclude_and_degrade_no_name_join",
            "missing_return_to_training_date": "degrade_without_neutral_imputation",
        },
    }
    context["content_sha256"] = artifact_hash(context)
    context_body = _canonical_file_bytes(context)
    context_dir = output_root / context["content_sha256"]
    artifacts = {
        "context": {"path": "context.json", "sha256": content_hash(context_body)},
        "official_bootstrap": {"path": "inputs/bootstrap-static.json", "sha256": bootstrap_hash},
        "previous_season_players": {"path": "inputs/prior-roster.csv", "sha256": prior_hash},
        "world_cup_priors": {"path": "inputs/world-cup-priors.csv", "sha256": world_cup_hash},
    }
    manifest = {
        "schema_version": "1.0",
        "season": season,
        "context_content_sha256": context["content_sha256"],
        "context_path": "context.json",
        "decision_cutoff": cutoff_text,
        "observed_at": context_observed,
        "available_at": context_available,
        "source_bindings": context["source_bindings"],
        "artifacts": artifacts,
        "universe_delta": universe_delta,
    }
    manifest["content_sha256"] = artifact_hash(manifest)
    manifest_body = _canonical_file_bytes(manifest)
    manifest_path = context_dir / "manifest.json"
    if manifest_path.exists():
        existing = _verify_derived_manifest(manifest_path, context_dir)
        if existing != manifest:
            raise LaunchContextBuildConflict("Existing context manifest differs for same context path")
        return {
            "context": context,
            "manifest": existing,
            "context_path": context_dir / "context.json",
            "manifest_path": manifest_path,
        }
    _write_immutable_bytes(context_dir / "context.json", context_body)
    _write_immutable_bytes(context_dir / "inputs" / "bootstrap-static.json", bootstrap_body)
    _write_immutable_bytes(context_dir / "inputs" / "prior-roster.csv", prior_body)
    _write_immutable_bytes(context_dir / "inputs" / "world-cup-priors.csv", world_cup_body)
    _write_immutable_bytes(manifest_path, manifest_body)
    return {
        "context": context,
        "manifest": manifest,
        "context_path": context_dir / "context.json",
        "manifest_path": manifest_path,
    }
