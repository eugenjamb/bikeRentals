"""Features indexed by the hour being predicted; demand is always shifted."""

import numpy as np
import pandas as pd

from .config import DEMAND_LAGS_HOURS, ROLLING_WINDOWS_HOURS


def build_features(hourly):
    expected = pd.date_range(hourly.index.min(), hourly.index.max(), freq="h", name=hourly.index.name)
    if not hourly.index.equals(expected):
        raise ValueError("Features require a sorted complete hourly grid")
    features = pd.DataFrame(index=hourly.index)
    features["hour"] = hourly.index.hour
    features["weekday"] = hourly.index.dayofweek
    features["month"] = hourly.index.month
    features["is_weekend"] = (hourly.index.dayofweek >= 5).astype(int)
    # Holiday and workingday are calendar facts known in advance.
    features["holiday"] = hourly["holiday"]
    features["workingday"] = hourly["workingday"]
    features["days_since_start"] = (hourly.index - pd.Timestamp("2011-01-01")) / pd.Timedelta(days=1)
    for name, values, period in (("hour", hourly.index.hour, 24), ("weekday", hourly.index.dayofweek, 7), ("month", hourly.index.month - 1, 12)):
        features[f"{name}_sin"] = np.sin(2 * np.pi * values / period)
        features[f"{name}_cos"] = np.cos(2 * np.pi * values / period)
    for lag in DEMAND_LAGS_HOURS:
        features[f"demand_lag_{lag}"] = hourly["cnt"].shift(lag)
    history = hourly["cnt"].shift(1)
    for window in ROLLING_WINDOWS_HOURS:
        # Require a full history window; missing windows are imputed in the pipeline.
        features[f"demand_mean_{window}"] = history.rolling(window, min_periods=window).mean()
        features[f"demand_std_{window}"] = history.rolling(window, min_periods=window).std()
    return features
