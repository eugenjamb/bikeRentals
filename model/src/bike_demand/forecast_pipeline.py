"""Raw forecast requests -> causal features -> selection -> preprocessing -> count."""

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.pipeline import Pipeline
from sklearn.utils.validation import check_is_fitted

from .config import DEMAND_LAGS_HOURS, RANDOM_SEED, ROLLING_WINDOWS_HOURS
from .preprocessing import make_preprocessor

HISTORY_HOURS = max(*DEMAND_LAGS_HOURS, *ROLLING_WINDOWS_HOURS)
REQUEST_COLUMNS = ("holiday", "workingday", "demand_history")
FEATURE_SETS = ("calendar_and_history", "calendar_and_lags")


def calendar_features(index, holiday, workingday):
    """Calendar features shared by exploration and the saved forecast pipeline."""
    features = pd.DataFrame(index=index)
    features["hour"] = index.hour
    features["weekday"] = index.dayofweek
    features["month"] = index.month
    features["is_weekend"] = (index.dayofweek >= 5).astype(int)
    # Holiday and workingday are calendar facts known in advance.
    features["holiday"] = holiday
    features["workingday"] = workingday
    features["days_since_start"] = (index - pd.Timestamp("2011-01-01")) / pd.Timedelta(days=1)
    for name, values, period in (("hour", index.hour, 24), ("weekday", index.dayofweek, 7), ("month", index.month - 1, 12)):
        features[f"{name}_sin"] = np.sin(2 * np.pi * values / period)
        features[f"{name}_cos"] = np.cos(2 * np.pi * values / period)
    return features


def prepare_forecast_requests(hourly):
    """Package per-row prior history before CV; no learned transformations here.

    Each history vector contains t-168 through t-1, oldest first. It never
    contains target t. Self-contained requests preserve missing hours and history
    at fold boundaries even after sklearn slices the sample rows.
    """
    expected = pd.date_range(hourly.index.min(), hourly.index.max(), freq="h", name=hourly.index.name)
    if not hourly.index.equals(expected):
        raise ValueError("Request preparation requires a complete sorted hourly grid")
    counts = hourly["cnt"].to_numpy(dtype=float)
    padded = np.pad(counts, (HISTORY_HOURS, 0), constant_values=np.nan)
    windows = np.lib.stride_tricks.sliding_window_view(padded, HISTORY_HOURS)[:-1]
    requests = hourly[["holiday", "workingday"]].copy()
    requests["demand_history"] = [row.copy() for row in windows]
    return requests


def make_forecast_request(history, target_timestamp, *, holiday, workingday):
    """Build one prediction request from a timestamped Series of past counts."""
    target = pd.Timestamp(target_timestamp)
    if target.tz is not None or target != target.floor("h"):
        raise ValueError("Use a timezone-naive target timestamp at an hour boundary")
    if not isinstance(history.index, pd.DatetimeIndex) or history.index.tz is not None:
        raise ValueError("History needs a timezone-naive DatetimeIndex")
    if history.index.has_duplicates or not (history.index == history.index.floor("h")).all():
        raise ValueError("History timestamps must be unique hour boundaries")
    if (history.index >= target).any():
        raise ValueError("History must end before the target hour; future observations are forbidden")
    index = pd.date_range(target - pd.Timedelta(hours=HISTORY_HOURS), periods=HISTORY_HOURS, freq="h")
    values = history.reindex(index).to_numpy(dtype=float)
    if not np.isfinite(values[-1]):
        raise ValueError("The last completed hour's count must be available")
    return pd.DataFrame({"holiday": [holiday], "workingday": [workingday], "demand_history": [values]}, index=pd.DatetimeIndex([target], name="target_timestamp"))


class DemandFeatureTransformer(TransformerMixin, BaseEstimator):
    """Deterministic feature engineering on self-contained forecast requests."""

    def fit(self, X, y=None):
        transformed = self._features(X)
        self.feature_names_out_ = transformed.columns.to_numpy()
        return self

    def transform(self, X):
        check_is_fitted(self, "feature_names_out_")
        return self._features(X)

    def get_feature_names_out(self, input_features=None):
        check_is_fitted(self, "feature_names_out_")
        return self.feature_names_out_.copy()

    def _features(self, requests):
        if not isinstance(requests, pd.DataFrame) or set(requests.columns) != set(REQUEST_COLUMNS):
            raise ValueError(f"Expected only request columns {REQUEST_COLUMNS}; target and weather are forbidden")
        index = requests.index
        if not isinstance(index, pd.DatetimeIndex) or index.tz is not None or index.has_duplicates or not (index == index.floor("h")).all():
            raise ValueError("Requests require unique timezone-naive target hours")
        if len(requests) == 0:
            raise ValueError("At least one forecast request is required")
        if not requests[["holiday", "workingday"]].isin([0, 1]).all().all():
            raise ValueError("Calendar flags must be known binary values")
        history = np.stack(requests["demand_history"].to_numpy()).astype(float)
        if history.shape != (len(requests), HISTORY_HOURS):
            raise ValueError(f"Each history must contain exactly {HISTORY_HOURS} hourly counts")
        if np.isinf(history).any() or (history < 0).any():
            raise ValueError("Historical counts must be nonnegative or NaN for unknown hours")
        if not np.isfinite(history[:, -1]).all():
            raise ValueError("The last completed hour's count must be available")
        features = calendar_features(index, requests["holiday"], requests["workingday"])
        for lag in DEMAND_LAGS_HOURS:
            features[f"demand_lag_{lag}"] = history[:, -lag]
        for window in ROLLING_WINDOWS_HOURS:
            # np.mean/std propagate unknown history, matching full rolling windows.
            features[f"demand_mean_{window}"] = np.mean(history[:, -window:], axis=1)
            features[f"demand_std_{window}"] = np.std(history[:, -window:], axis=1, ddof=1)
        return features


class ForecastFeatureSelector(TransformerMixin, BaseEstimator):
    """Explicit domain feature sets, selected within chronological grid search."""

    def __init__(self, feature_set="calendar_and_history"):
        self.feature_set = feature_set

    def fit(self, X, y=None):
        if self.feature_set not in FEATURE_SETS:
            raise ValueError(f"Choose a feature set from {FEATURE_SETS}")
        self.columns_ = [name for name in X.columns if self.feature_set == "calendar_and_history" or not name.startswith(("demand_mean_", "demand_std_"))]
        return self

    def transform(self, X):
        check_is_fitted(self, "columns_")
        return X.loc[:, self.columns_].copy()

    def get_feature_names_out(self, input_features=None):
        check_is_fitted(self, "columns_")
        return np.asarray(self.columns_, dtype=object)


class NonnegativeHistGradientBoostingRegressor(HistGradientBoostingRegressor):
    """Use the same clipping policy during grid scoring and saved prediction."""

    def predict(self, X):
        return np.maximum(0, super().predict(X))


def make_forecast_pipeline():
    # Reuse the existing preprocessing configuration, with numeric columns resolved
    # after feature selection. All fitted steps remain inside each grid-search fold.
    estimator = NonnegativeHistGradientBoostingRegressor(early_stopping=False, random_state=RANDOM_SEED)
    return Pipeline([
        ("features", DemandFeatureTransformer()),
        ("select", ForecastFeatureSelector()),
        ("preprocess", make_preprocessor()),
        ("regressor", estimator),
    ])
