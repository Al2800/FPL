"""Time-ordered calibration for the live-faithful cold-start parameters."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd


POSITION_MAP = {"GK": "GKP", "GKP": "GKP", "DEF": "DEF", "MID": "MID", "FWD": "FWD"}
DEFAULT_BANDS = ((0.0, 5.5), (5.5, 7.5), (7.5, 10.0), (10.0, 20.0))
EVENT_FIELDS = (
    "expected_goals",
    "expected_assists",
    "clean_sheets",
    "saves",
    "bonus",
    "yellow_cards",
    "red_cards",
)


class CalibrationError(ValueError):
    """Raised when source seasons cannot form a leakage-safe calibration frame."""


@dataclass(frozen=True)
class ForecastParameters:
    prior_equivalent_minutes: float
    start_prior_equivalent_matches: float
    cameo_minutes: float
    team_fixture_scale: float = 0.0
    player_prior_reliability_minutes: float = 0.0
    event_model_weight: float = 0.0
    recent_minutes_weight: float = 0.0


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _price_band(price: float, bands: Iterable[Iterable[float]]) -> str:
    parsed = [tuple(float(value) for value in band) for band in bands]
    for index, (lower, upper) in enumerate(parsed):
        if lower >= upper:
            raise CalibrationError("Invalid price band")
        if lower <= price < upper or (index == len(parsed) - 1 and price == upper):
            return f"{lower:g}-{upper:g}"
    return "outside"


def load_season_rows(
    season: str,
    *,
    vaastav_root: Path,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Load fixture rows and attach stable player codes from one frozen checkout."""

    season_root = vaastav_root / season
    gw_path = season_root / "gws" / "merged_gw.csv"
    players_path = season_root / "players_raw.csv"
    if not gw_path.exists() or not players_path.exists():
        raise CalibrationError(f"Missing source files for {season}")
    rows = pd.read_csv(gw_path, low_memory=False)
    players = pd.read_csv(players_path, low_memory=False)
    required = {"element", "fixture", "position", "minutes", "total_points", "value", "GW"}
    missing = sorted(required - set(rows.columns))
    if missing:
        raise CalibrationError(f"{season} merged_gw missing fields: {missing}")
    if not {"id", "code"} <= set(players.columns):
        raise CalibrationError(f"{season} players_raw lacks id/code")
    identity = players[["id", "code"]].drop_duplicates()
    if identity["id"].duplicated().any() or identity["code"].duplicated().any():
        raise CalibrationError(f"{season} identity is ambiguous")
    frame = rows.merge(identity, left_on="element", right_on="id", how="left", validate="many_to_one")
    if frame["code"].isna().any():
        raise CalibrationError(f"{season} has unresolved player codes")
    raw_positions = frame["position"].astype(str).str.upper()
    unsupported = sorted(set(raw_positions) - set(POSITION_MAP) - {"AM"})
    if unsupported:
        raise CalibrationError(f"{season} has unsupported positions: {unsupported}")
    assistant_manager_rows = int((raw_positions == "AM").sum())
    frame = frame.loc[raw_positions != "AM"].copy()
    frame["position"] = frame["position"].astype(str).str.upper().map(POSITION_MAP)
    if frame["position"].isna().any():
        raise CalibrationError(f"{season} has unknown positions")
    for field in ("minutes", "total_points", "value", "GW", "fixture", "code"):
        frame[field] = pd.to_numeric(frame[field], errors="raise")
    if "expected_goals" not in frame:
        frame["expected_goals"] = frame.get("goals_scored", 0)
    if "expected_assists" not in frame:
        frame["expected_assists"] = frame.get("assists", 0)
    for field in EVENT_FIELDS:
        if field not in frame:
            frame[field] = 0.0
        frame[field] = pd.to_numeric(frame[field], errors="coerce").fillna(0.0)
    start_source = "recorded"
    if "starts" not in frame.columns:
        # This is used only for the 2021/22 prior, never as a target label.
        frame["starts"] = (frame["minutes"] >= 60).astype(int)
        start_source = "minutes_ge_60_prior_fallback"
    else:
        frame["starts"] = pd.to_numeric(frame["starts"], errors="coerce")
    frame = frame.sort_values(["GW", "fixture", "code"], kind="stable").reset_index(drop=True)
    lineage = {
        "season": season,
        "merged_gw_sha256": _sha256(gw_path),
        "players_raw_sha256": _sha256(players_path),
        "row_count": int(len(frame)),
        "start_source": start_source,
        "excluded_assistant_manager_rows": assistant_manager_rows,
    }
    return frame, lineage


def _prior_tables(
    rows: pd.DataFrame,
    *,
    bands: Iterable[Iterable[float]],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    frame = rows.copy()
    for field in EVENT_FIELDS:
        if field not in frame:
            frame[field] = 0.0
    first = (
        frame.sort_values(["GW", "fixture"], kind="stable")
        .groupby("code", sort=False)
        .first()[["position", "value"]]
    )
    grouped = frame.groupby("code", sort=True).agg(
        prior_minutes=("minutes", "sum"),
        prior_points=("total_points", "sum"),
        prior_starts=("starts", "sum"),
        prior_fixtures=("fixture", "count"),
        prior_start_minutes=("minutes", lambda values: float(values[frame.loc[values.index, "starts"].fillna(0) > 0].sum())),
        **{
            f"prior_{field}": (field, "sum")
            for field in EVENT_FIELDS
        },
    )
    grouped = grouped.join(first)
    grouped["price"] = grouped["value"] / 10.0
    grouped["price_band"] = grouped["price"].map(lambda value: _price_band(float(value), bands))
    grouped["prior_points_per_90"] = np.where(
        grouped["prior_minutes"] > 0,
        90.0 * grouped["prior_points"] / grouped["prior_minutes"],
        np.nan,
    )
    grouped["prior_start_probability"] = (
        grouped["prior_starts"] / grouped["prior_fixtures"].clip(lower=1)
    )
    grouped["prior_minutes_per_start"] = np.where(
        grouped["prior_starts"] > 0,
        grouped["prior_start_minutes"] / grouped["prior_starts"],
        np.nan,
    )
    for field in EVENT_FIELDS:
        grouped[f"prior_{field}_per_90"] = np.where(
            grouped["prior_minutes"] > 0,
            90.0 * grouped[f"prior_{field}"] / grouped["prior_minutes"],
            0.0,
        )

    valid = grouped[
        grouped["prior_points_per_90"].notna()
        & grouped["prior_minutes_per_start"].notna()
    ].reset_index()
    fallback = (
        valid.groupby(["position", "price_band"], sort=True)
        .apply(
            lambda group: pd.Series(
                {
                    "fallback_points_per_90": float(
                        90.0 * group["prior_points"].sum() / max(group["prior_minutes"].sum(), 1)
                    ),
                    "fallback_start_probability": float(
                        group["prior_starts"].sum() / max(group["prior_fixtures"].sum(), 1)
                    ),
                    "fallback_minutes_per_start": float(
                        group["prior_start_minutes"].sum() / max(group["prior_starts"].sum(), 1)
                    ),
                    "fallback_players": int(len(group)),
                    **{
                        f"fallback_{field}_per_90": float(
                            90.0
                            * group[f"prior_{field}"].sum()
                            / max(group["prior_minutes"].sum(), 1)
                        )
                        for field in EVENT_FIELDS
                    },
                }
            ),
            include_groups=False,
        )
        .reset_index()
    )
    position_fallback = (
        valid.groupby("position", sort=True)
        .apply(
            lambda group: pd.Series(
                {
                    "position_points_per_90": float(
                        90.0 * group["prior_points"].sum() / max(group["prior_minutes"].sum(), 1)
                    ),
                    "position_start_probability": float(
                        group["prior_starts"].sum() / max(group["prior_fixtures"].sum(), 1)
                    ),
                    "position_minutes_per_start": float(
                        group["prior_start_minutes"].sum() / max(group["prior_starts"].sum(), 1)
                    ),
                    **{
                        f"position_{field}_per_90": float(
                            90.0
                            * group[f"prior_{field}"].sum()
                            / max(group["prior_minutes"].sum(), 1)
                        )
                        for field in EVENT_FIELDS
                    },
                }
            ),
            include_groups=False,
        )
        .reset_index()
    )
    return grouped.reset_index(), fallback, position_fallback


def build_calibration_cases(
    *,
    prior_rows: pd.DataFrame,
    target_rows: pd.DataFrame,
    prior_season: str,
    target_season: str,
    bands: Iterable[Iterable[float]] = DEFAULT_BANDS,
) -> pd.DataFrame:
    """Build one prediction case per player/Gameweek using only earlier target GWs."""

    prior, fallback, position_fallback = _prior_tables(prior_rows, bands=bands)
    target = target_rows.copy()
    for field in EVENT_FIELDS:
        if field not in target:
            target[field] = 0.0
    target["price"] = target["value"] / 10.0
    target["price_band"] = target["price"].map(lambda value: _price_band(float(value), bands))
    grouped = (
        target.groupby(["code", "GW"], sort=True)
        .agg(
            position=("position", "first"),
            price_band=("price_band", "first"),
            actual_points=("total_points", "sum"),
            actual_minutes=("minutes", "sum"),
            actual_started=("starts", "max"),
            fixture_count=("fixture", "count"),
            expected_result_score=(
                "expected_result_score"
                if "expected_result_score" in target.columns
                else "fixture",
                "mean" if "expected_result_score" in target.columns else (lambda _: 0.5),
            ),
            **{
                f"actual_{field}": (field, "sum")
                for field in EVENT_FIELDS
            },
        )
        .reset_index()
        .sort_values(["GW", "code"], kind="stable")
    )
    grouped = grouped.merge(
        prior[
            [
                "code",
                "prior_points_per_90",
                "prior_start_probability",
                "prior_minutes_per_start",
                "prior_minutes",
                *[f"prior_{field}_per_90" for field in EVENT_FIELDS],
            ]
        ],
        on="code",
        how="left",
        validate="many_to_one",
    )
    grouped = grouped.merge(
        fallback,
        on=["position", "price_band"],
        how="left",
        validate="many_to_one",
    )
    grouped = grouped.merge(
        position_fallback,
        on="position",
        how="left",
        validate="many_to_one",
    )
    for destination, exact, band, position in (
        (
            "base_points_per_90",
            "prior_points_per_90",
            "fallback_points_per_90",
            "position_points_per_90",
        ),
        (
            "base_start_probability",
            "prior_start_probability",
            "fallback_start_probability",
            "position_start_probability",
        ),
        (
            "base_minutes_per_start",
            "prior_minutes_per_start",
            "fallback_minutes_per_start",
            "position_minutes_per_start",
        ),
    ):
        grouped[destination] = grouped[exact].fillna(grouped[band]).fillna(grouped[position])
    for field in EVENT_FIELDS:
        grouped[f"base_{field}_per_90"] = grouped[
            f"prior_{field}_per_90"
        ].fillna(grouped[f"fallback_{field}_per_90"]).fillna(
            grouped[f"position_{field}_per_90"]
        )
        grouped[f"group_{field}_per_90"] = grouped[
            f"fallback_{field}_per_90"
        ].fillna(grouped[f"position_{field}_per_90"])
    grouped["group_points_per_90"] = grouped["fallback_points_per_90"].fillna(
        grouped["position_points_per_90"]
    )
    grouped["group_start_probability"] = grouped[
        "fallback_start_probability"
    ].fillna(grouped["position_start_probability"])
    grouped["group_minutes_per_start"] = grouped[
        "fallback_minutes_per_start"
    ].fillna(grouped["position_minutes_per_start"])
    if grouped[
        ["base_points_per_90", "base_start_probability", "base_minutes_per_start"]
    ].isna().any().any():
        raise CalibrationError(f"{target_season} has unresolved prior fallbacks")
    grouped["prior_source"] = np.where(
        grouped["prior_points_per_90"].notna(), "fpl_code", "position_price_fallback"
    )

    outputs = []
    for _, player in grouped.groupby("code", sort=False):
        player = player.sort_values("GW", kind="stable").copy()
        player["current_minutes"] = player["actual_minutes"].cumsum().shift(fill_value=0)
        player["current_points"] = player["actual_points"].cumsum().shift(fill_value=0)
        player["current_matches"] = player["fixture_count"].cumsum().shift(fill_value=0)
        player["current_starts"] = player["actual_started"].cumsum().shift(fill_value=0)
        for field in EVENT_FIELDS:
            player[f"current_{field}"] = (
                player[f"actual_{field}"].cumsum().shift(fill_value=0)
            )
        per_fixture_minutes = player["actual_minutes"] / player["fixture_count"].clip(lower=1)
        player["recent_minutes_per_fixture"] = (
            per_fixture_minutes.shift().rolling(3, min_periods=1).mean()
        )
        rolling = player["actual_points"].shift().rolling(3, min_periods=1).mean()
        player["raw_rolling_expected_points"] = rolling.fillna(2.0) * player["fixture_count"]
        outputs.append(player)
    cases = pd.concat(outputs, ignore_index=True)
    cases["prior_season"] = prior_season
    cases["target_season"] = target_season
    return cases.sort_values(["GW", "code"], kind="stable").reset_index(drop=True)


def predictions(cases: pd.DataFrame, params: ForecastParameters) -> pd.DataFrame:
    """Calculate prior-only and shrunken predictions over fixed cases."""

    frame = cases.copy()
    reliability = frame["prior_minutes"].fillna(0) / (
        frame["prior_minutes"].fillna(0)
        + params.player_prior_reliability_minutes
    )
    if params.player_prior_reliability_minutes == 0:
        reliability = np.where(frame["prior_minutes"].notna(), 1.0, 0.0)
    base_rate = (
        reliability * frame["base_points_per_90"]
        + (1.0 - reliability) * frame["group_points_per_90"]
    )
    base_start = (
        reliability * frame["base_start_probability"]
        + (1.0 - reliability) * frame["group_start_probability"]
    )
    base_minutes_per_start = (
        reliability * frame["base_minutes_per_start"]
        + (1.0 - reliability) * frame["group_minutes_per_start"]
    )
    base_event_rates: dict[str, pd.Series] = {}
    for field in EVENT_FIELDS:
        base_event_rates[field] = (
            reliability * frame[f"base_{field}_per_90"]
            + (1.0 - reliability) * frame[f"group_{field}_per_90"]
        )
    current_rate = np.where(
        frame["current_minutes"] > 0,
        90.0 * frame["current_points"] / frame["current_minutes"],
        base_rate,
    )
    posterior_rate = (
        base_rate * params.prior_equivalent_minutes
        + current_rate * frame["current_minutes"]
    ) / (params.prior_equivalent_minutes + frame["current_minutes"])
    posterior_start = (
        base_start * params.start_prior_equivalent_matches
        + frame["current_starts"]
    ) / (params.start_prior_equivalent_matches + frame["current_matches"])
    posterior_start = posterior_start.clip(0.0, 1.0)
    expected_minutes_each = (
        posterior_start * base_minutes_per_start
        + (1.0 - posterior_start) * params.cameo_minutes
    )
    expected_minutes_each = (
        (1.0 - params.recent_minutes_weight) * expected_minutes_each
        + params.recent_minutes_weight
        * frame["recent_minutes_per_fixture"].fillna(expected_minutes_each)
    )
    prior_minutes_each = (
        base_start * base_minutes_per_start
        + (1.0 - base_start) * params.cameo_minutes
    )
    frame["prior_only_expected_points"] = (
        base_rate
        * prior_minutes_each
        / 90.0
        * frame["fixture_count"]
    )
    frame["live_faithful_expected_minutes"] = expected_minutes_each * frame["fixture_count"]
    frame["live_faithful_start_probability"] = posterior_start
    frame["live_faithful_expected_points"] = (
        posterior_rate
        * expected_minutes_each
        / 90.0
        * frame["fixture_count"]
    )
    frame["team_multiplier"] = np.clip(
        (frame["expected_result_score"] / 0.5) ** params.team_fixture_scale,
        0.7,
        1.3,
    )
    frame["live_faithful_expected_points"] *= frame["team_multiplier"]
    position_goal_points = frame["position"].map(
        {"GKP": 6.0, "DEF": 6.0, "MID": 5.0, "FWD": 4.0}
    )
    position_cs_points = frame["position"].map(
        {"GKP": 4.0, "DEF": 4.0, "MID": 1.0, "FWD": 0.0}
    )
    event_rates: dict[str, pd.Series] = {}
    for field in EVENT_FIELDS:
        current_rate = np.where(
            frame["current_minutes"] > 0,
            90.0 * frame[f"current_{field}"] / frame["current_minutes"],
            base_event_rates[field],
        )
        event_rates[field] = (
            base_event_rates[field] * params.prior_equivalent_minutes
            + current_rate * frame["current_minutes"]
        ) / (params.prior_equivalent_minutes + frame["current_minutes"])
    appearance_points = (1.0 + posterior_start) * frame["fixture_count"]
    event_expected = appearance_points + (
        event_rates["expected_goals"] * position_goal_points
        + event_rates["expected_assists"] * 3.0
        + event_rates["clean_sheets"] * position_cs_points
        + np.where(frame["position"] == "GKP", event_rates["saves"] / 3.0, 0.0)
        + event_rates["bonus"]
        - event_rates["yellow_cards"]
        - 3.0 * event_rates["red_cards"]
    ) * expected_minutes_each / 90.0 * frame["fixture_count"]
    frame["event_expected_points"] = event_expected * frame["team_multiplier"]
    frame["rate_expected_points"] = frame["live_faithful_expected_points"]
    frame["live_faithful_expected_points"] = (
        (1.0 - params.event_model_weight) * frame["rate_expected_points"]
        + params.event_model_weight * frame["event_expected_points"]
    )
    return frame


def _metrics(frame: pd.DataFrame, prediction: str) -> dict[str, Any]:
    error = frame[prediction] - frame["actual_points"]
    result: dict[str, Any] = {
        "n": int(len(frame)),
        "mae": float(error.abs().mean()),
        "rmse": float(np.sqrt((error**2).mean())),
    }
    if prediction == "live_faithful_expected_points":
        minute_error = frame["live_faithful_expected_minutes"] - frame["actual_minutes"]
        start_error = frame["live_faithful_start_probability"] - frame["actual_started"]
        result["expected_minutes_mae"] = float(minute_error.abs().mean())
        result["start_brier"] = float((start_error**2).mean())
        top_precision = []
        for _, gameweek in frame.groupby("GW"):
            count = min(15, len(gameweek))
            actual = set(gameweek.nlargest(count, "actual_points")["code"])
            predicted = set(gameweek.nlargest(count, prediction)["code"])
            top_precision.append(len(actual & predicted) / count)
        result["top15_precision"] = float(np.mean(top_precision))
    return result


def evaluate_cases(cases: pd.DataFrame, params: ForecastParameters) -> dict[str, Any]:
    frame = predictions(cases, params)
    early = frame[(frame["GW"] >= 2) & (frame["GW"] <= 5)]
    actionable = frame[
        (frame["base_start_probability"] >= 0.25)
        | (frame["current_minutes"] > 0)
    ]
    early_actionable = actionable[
        (actionable["GW"] >= 2) & (actionable["GW"] <= 5)
    ]
    result: dict[str, Any] = {
        "parameters": asdict(params),
        "all": {},
        "early_gw2_5": {},
        "actionable": {},
        "actionable_early_gw2_5": {},
    }
    for prediction in (
        "raw_rolling_expected_points",
        "prior_only_expected_points",
        "live_faithful_expected_points",
    ):
        result["all"][prediction] = _metrics(frame, prediction)
        result["early_gw2_5"][prediction] = _metrics(early, prediction)
        result["actionable"][prediction] = _metrics(actionable, prediction)
        result["actionable_early_gw2_5"][prediction] = _metrics(
            early_actionable, prediction
        )
    return result


def calibration_objective(evaluation: Mapping[str, Any]) -> float:
    """Rank configurations on early points first, with minutes/start as tie-breakers."""

    metrics = evaluation["actionable_early_gw2_5"][
        "live_faithful_expected_points"
    ]
    return float(
        metrics["mae"]
        + 0.01 * metrics["expected_minutes_mae"]
        + 0.5 * metrics["start_brier"]
    )


def select_parameters(
    cases: pd.DataFrame,
    *,
    prior_equivalent_minutes: Iterable[float],
    start_prior_equivalent_matches: Iterable[float],
    cameo_minutes: Iterable[float],
    team_fixture_scale: Iterable[float] = (0.0,),
    player_prior_reliability_minutes: Iterable[float] = (0.0,),
    event_model_weight: Iterable[float] = (0.0,),
    recent_minutes_weight: Iterable[float] = (0.0,),
) -> tuple[ForecastParameters, list[dict[str, Any]]]:
    """Select deterministically from a declared grid using training cases only."""

    candidates = []
    for minutes in prior_equivalent_minutes:
        for starts in start_prior_equivalent_matches:
            for cameo in cameo_minutes:
                for team_scale in team_fixture_scale:
                    for reliability in player_prior_reliability_minutes:
                        for event_weight in event_model_weight:
                            for recent_weight in recent_minutes_weight:
                                params = ForecastParameters(
                                    float(minutes),
                                    float(starts),
                                    float(cameo),
                                    float(team_scale),
                                    float(reliability),
                                    float(event_weight),
                                    float(recent_weight),
                                )
                                evaluation = evaluate_cases(cases, params)
                                candidates.append(
                                    {
                                        "parameters": asdict(params),
                                        "objective": calibration_objective(evaluation),
                                        "training": evaluation,
                                    }
                                )
    candidates.sort(
        key=lambda row: (
            row["objective"],
            row["parameters"]["prior_equivalent_minutes"],
            row["parameters"]["start_prior_equivalent_matches"],
            row["parameters"]["cameo_minutes"],
        )
    )
    return ForecastParameters(**candidates[0]["parameters"]), candidates
