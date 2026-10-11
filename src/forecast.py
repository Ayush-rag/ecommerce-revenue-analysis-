"""Forecast the next 3 months of revenue, choosing the method by a fair test.

1. WALK-FORWARD BACKTEST - for each of the last 6 known months (Mar-Aug 2018),
   pretend we are 1, 2 and 3 months before it, forecast it using only the
   months known at that point, and record how far off each method was.
   This copies exactly how the real forecast will be used (1-3 months ahead).
2. PICK the method with the smallest average error (MAPE).
3. FORECAST Sep-Nov 2018 with that method, using all known months. Each month
   gets a range of +/- the winner's backtest error at that distance, so the
   range widens the further ahead we look.

Three simple, explainable methods are compared:
  * Naive            - next months = the last month
  * 3-month average  - next months = average of the last 3 months
  * Linear trend     - a straight line fitted through all past months
"""
import numpy as np
import pandas as pd

from config import BACKTEST_MONTHS, FORECAST_MONTHS


def naive(history: pd.Series, steps: int) -> np.ndarray:
    return np.repeat(history.iloc[-1], steps)


def moving_average_3(history: pd.Series, steps: int) -> np.ndarray:
    return np.repeat(history.iloc[-3:].mean(), steps)


def linear_trend(history: pd.Series, steps: int) -> np.ndarray:
    x = np.arange(len(history))
    slope, intercept = np.polyfit(x, history.to_numpy(), 1)
    return intercept + slope * np.arange(len(history), len(history) + steps)


METHODS = {
    "Naive (last month)": naive,
    "3-month moving average": moving_average_3,
    "Linear trend": linear_trend,
}


def walk_forward(revenue: pd.Series) -> pd.DataFrame:
    """One row per (method, target month, months ahead) with the prediction and its error."""
    rows = []
    n = len(revenue)
    for name, method in METHODS.items():
        for target in range(n - BACKTEST_MONTHS, n):
            for ahead in range(1, FORECAST_MONTHS + 1):
                history = revenue.iloc[: target - ahead + 1]       # only what was known then
                predicted = method(history, ahead)[-1]
                actual = revenue.iloc[target]
                rows.append({
                    "method": name,
                    "target_month": revenue.index[target],
                    "months_ahead": ahead,
                    "forecast_made_after": revenue.index[target - ahead],
                    "actual": round(actual, 2),
                    "predicted": round(float(predicted), 2),
                    "abs_pct_error": round(abs(actual - predicted) / actual * 100, 2),
                })
    return pd.DataFrame(rows)


def next_months(last_month: str, steps: int) -> list[str]:
    start = pd.Period(last_month, freq="M") + 1
    return [str(start + i) for i in range(steps)]


def run(monthly: pd.DataFrame) -> dict:
    """monthly: columns month ('YYYY-MM') and revenue, sorted by month."""
    revenue = monthly.set_index("month")["revenue"]

    # 1. Backtest
    backtest = walk_forward(revenue)
    scores = (backtest.groupby("method")["abs_pct_error"].mean().round(1)
              .rename("mape_pct").reset_index().sort_values("mape_pct").reset_index(drop=True))
    by_horizon = (backtest.pivot_table(index="method", columns="months_ahead",
                                       values="abs_pct_error", aggfunc="mean").round(1))
    by_horizon.columns = [f"mape_{h}_month_ahead" for h in by_horizon.columns]
    scores = scores.merge(by_horizon.reset_index(), on="method")

    # 2. Pick the winner
    best = scores.iloc[0]["method"]
    horizon_error = [by_horizon.loc[best, f"mape_{h}_month_ahead"] / 100
                     for h in range(1, FORECAST_MONTHS + 1)]

    # 3. Forecast with all known months
    point = METHODS[best](revenue, FORECAST_MONTHS)
    forecast = pd.DataFrame({
        "month": next_months(revenue.index[-1], FORECAST_MONTHS),
        "months_ahead": range(1, FORECAST_MONTHS + 1),
        "forecast": point.round(2),
        "low": (point * (1 - np.array(horizon_error))).round(2),
        "high": (point * (1 + np.array(horizon_error))).round(2),
        "method": best,
    })

    return {"backtest": backtest, "scores": scores, "forecast": forecast,
            "best_method": best, "best_mape": float(scores.iloc[0]["mape_pct"])}
