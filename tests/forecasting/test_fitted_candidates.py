"""Tests for fitted forecast candidates (ticket 17)."""

from __future__ import annotations

import numpy as np
import pytest

from src.forecasting.fitted_candidates import (
    FittedCandidateError,
    fit_logistic_l2,
    fit_ridge,
    load_preregistration,
    predict_logistic,
)


def test_preregistration_forbids_2025_26_fit() -> None:
    prereg = load_preregistration()
    assert "2025-26" in prereg["forbidden_fit_seasons"]
    assert prereg["locked_validation_season"] == "2024-25"
    assert len(prereg["families"]) == 3


def test_ridge_recovers_linear_signal() -> None:
    rng = np.random.default_rng(0)
    x = np.column_stack([np.ones(200), rng.normal(size=200)])
    true = np.array([0.5, 1.5])
    y = x @ true + rng.normal(scale=0.05, size=200)
    fitted = fit_ridge(x, y, l2=0.01)
    assert fitted[1] == pytest.approx(1.5, abs=0.1)


def test_logistic_separates_simple_signal() -> None:
    rng = np.random.default_rng(1)
    x1 = rng.normal(loc=-1.0, size=150)
    x2 = rng.normal(loc=1.0, size=150)
    x = np.column_stack(
        [np.ones(300), np.concatenate([x1, x2])]
    )
    y = np.concatenate([np.zeros(150), np.ones(150)])
    weights = fit_logistic_l2(x, y, l2=0.1)
    probs = predict_logistic(x, weights)
    assert probs[150:].mean() > probs[:150].mean()


def test_logistic_rejects_non_binary() -> None:
    x = np.ones((10, 2))
    y = np.linspace(0, 1, 10)
    with pytest.raises(FittedCandidateError, match="binary"):
        fit_logistic_l2(x, y, l2=1.0)
