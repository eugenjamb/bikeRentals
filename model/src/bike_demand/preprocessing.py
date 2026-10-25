"""Preprocessing fitted independently inside each chronological training fold."""

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def numeric_feature_columns(features):
    return [name for name in features.columns if name not in ("hour", "weekday", "month")]


def make_preprocessor():
    return ColumnTransformer([
        ("calendar", OneHotEncoder(handle_unknown="ignore", sparse_output=False), ["hour", "weekday", "month"]),
        ("numeric", Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), numeric_feature_columns),
    ])
