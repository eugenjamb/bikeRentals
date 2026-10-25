"""Fixed-setting development comparison. The final test is never scored here."""

import json
import platform
from importlib.metadata import version

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .config import OUTPUT_DIR, PROCESSED_DATA_DIR, RANDOM_SEED, RAW_DATA_PATH
from .data import load_hourly
from .features import build_features


def make_pipeline(estimator, columns):
    categorical = ["hour", "weekday", "month"]
    numeric = [name for name in columns if name not in categorical]
    preprocessing = ColumnTransformer([
        ("calendar", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical),
        ("numeric", Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), numeric),
    ])
    return Pipeline([("preprocess", preprocessing), ("regressor", estimator)])


def model_definitions():
    return {
        "ridge": Ridge(alpha=1.0),
        "random_forest": RandomForestRegressor(n_estimators=100, random_state=RANDOM_SEED, n_jobs=-1),
        # Disable random internal validation; all validation must respect time.
        "hist_gradient_boosting": HistGradientBoostingRegressor(early_stopping=False, random_state=RANDOM_SEED),
    }


def metrics(actual, predicted):
    predicted = np.maximum(0, predicted)
    return {"mae": mean_absolute_error(actual, predicted), "rmse": root_mean_squared_error(actual, predicted), "r2": r2_score(actual, predicted)}


def train_initial_models():
    split = json.loads((PROCESSED_DATA_DIR / "split.json").read_text())
    test_start = pd.Timestamp(split["test_start_inclusive"])
    hourly = load_hourly(RAW_DATA_PATH)
    development = hourly.loc[hourly.index < test_start]
    features = build_features(development)
    # Fair shared coverage; origin demand must be known, and weekly baseline must exist.
    eligible = development["cnt"].notna() & features["demand_lag_1"].notna() & features["demand_lag_168"].notna()
    eligible &= features.index >= features.index.min() + pd.Timedelta(hours=168)
    folds = []
    scores = []
    predictions = []
    estimators = model_definitions()
    for fold in range(3):
        validation_start = test_start - pd.Timedelta(days=28 * (3 - fold))
        validation_end = validation_start + pd.Timedelta(days=28)
        train_mask = eligible & (features.index < validation_start)
        valid_mask = eligible & (features.index >= validation_start) & (features.index < validation_end)
        x_train, x_valid = features.loc[train_mask], features.loc[valid_mask]
        y_train, y_valid = development.loc[train_mask, "cnt"], development.loc[valid_mask, "cnt"]
        if x_train.empty or x_valid.empty:
            raise ValueError("Insufficient data for expanding validation")
        folds.append({"fold": fold + 1, "train_start": str(x_train.index.min()), "train_end": str(x_train.index.max()), "validation_start": str(validation_start), "validation_end_exclusive": str(validation_end), "training_rows": len(x_train), "eligible_validation_rows": len(x_valid), "observed_validation_rows": int(development.loc[(development.index >= validation_start) & (development.index < validation_end), "cnt"].notna().sum())})
        for name in ["last_hour", "seasonal_naive", *estimators]:
            if name in ("last_hour", "seasonal_naive"):
                predicted = x_valid["demand_lag_1" if name == "last_hour" else "demand_lag_168"].to_numpy()
            else:
                pipeline = make_pipeline(estimators[name], features.columns)
                pipeline.fit(x_train, y_train)
                predicted = pipeline.predict(x_valid)
            predicted = np.maximum(0, predicted)
            scores.append({"model": name, "fold": fold + 1, **metrics(y_valid, predicted)})
            predictions.append(pd.DataFrame({"target_timestamp": x_valid.index, "model": name, "fold": fold + 1, "actual": y_valid.to_numpy(), "predicted": predicted}))
    scores = pd.DataFrame(scores)
    ranking = scores.groupby("model")[["mae", "rmse", "r2"]].mean().sort_values("mae")
    best_learned = ranking.loc[ranking.index.isin(estimators)].index[0]
    fitted = make_pipeline(estimators[best_learned], features.columns)
    fitted.fit(features.loc[eligible], development.loc[eligible, "cnt"])
    destination = OUTPUT_DIR / "experiments" / "initial_fixed_settings"
    destination.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "models").mkdir(parents=True, exist_ok=True)
    joblib.dump(fitted, OUTPUT_DIR / "models" / "development_pipeline.joblib")
    scores.to_csv(destination / "fold_metrics.csv", index=False)
    ranking.to_csv(destination / "mean_cv_metrics.csv")
    combined = pd.concat(predictions, ignore_index=True)
    combined.to_csv(destination / "validation_predictions.csv", index=False)
    selected = combined.loc[combined.model == best_learned].copy()
    selected["absolute_error"] = (selected.actual - selected.predicted).abs()
    times = pd.to_datetime(selected.target_timestamp)
    selected["hour"] = times.dt.hour
    selected["weekday"] = times.dt.day_name()
    for group in ["hour", "weekday"]:
        selected.groupby(group).agg(mae=("absolute_error", "mean"), rows=("absolute_error", "size")).to_csv(destination / f"errors_by_{group}.csv")
    metadata = {
        "status": "initial fixed-setting comparison; final test untouched",
        "selection_metric": "unweighted mean fold MAE",
        "best_learned_model": best_learned,
        "best_overall_including_baselines": ranking.index[0],
        "prediction_postprocessing": "clip negative predictions to zero",
        "feature_columns": features.columns.tolist(),
        "model_parameters": {name: estimator.get_params() for name, estimator in estimators.items()},
        "folds": folds,
        "dataset_provenance": json.loads((RAW_DATA_PATH.parent / "provenance.json").read_text()),
        "versions": {"python": platform.python_version(), **{name: version(name) for name in ["numpy", "pandas", "scikit-learn", "joblib"]}},
        "test_split": split,
        "limitations": ["Only three recent 28-day validation blocks; not all seasons represented.", "Missing lag_1 or lag_168 observations excluded for every model.", "No weather inputs; no hyperparameter search; final test not evaluated.", "Saved pipeline expects engineered features and requires nonnegative clipping at inference."],
    }
    (destination / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    return ranking
