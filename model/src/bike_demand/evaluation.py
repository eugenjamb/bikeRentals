"""Regression metrics and final evaluation; no model fitting or tuning."""

import hashlib
import json
from datetime import datetime, timezone

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error

from .config import CPU_THREADS, OUTPUT_DIR, PROCESSED_DATA_DIR, RAW_DATA_PATH
from .data import load_hourly
from .forecast_pipeline import prepare_forecast_requests
from .data import prepare_development


def metrics(actual, predicted):
    predicted = np.maximum(0, predicted)
    return {"mae": mean_absolute_error(actual, predicted), "rmse": root_mean_squared_error(actual, predicted), "r2": r2_score(actual, predicted)}


def closeness_metrics(actual, predicted):
    """Pooled descriptive errors; tolerance rates are not classification accuracy."""
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    if actual.ndim != 1 or actual.shape != predicted.shape or actual.size == 0:
        raise ValueError("Expected equal nonempty one-dimensional arrays")
    if not np.isfinite(actual).all() or not np.isfinite(predicted).all():
        raise ValueError("Actual and predicted values must be finite")
    if (actual < 0).any() or (predicted < 0).any():
        raise ValueError("Rental counts and postprocessed predictions must be nonnegative")
    errors = np.abs(predicted - actual)
    positive = actual > 0
    return {
        "rows": len(actual),
        "pooled_mae": errors.mean(),
        "within_20_rentals_pct": 100 * (errors <= 20).mean(),
        "within_50_rentals_pct": 100 * (errors <= 50).mean(),
        "within_20_percent_pct": float(100 * (errors[positive] <= 0.2 * actual[positive]).mean()) if positive.any() else None,
        "relative_tolerance_rows": int(positive.sum()),
        "relative_tolerance_excluded_zero_rows": int((~positive).sum()),
        "wape_pct": float(100 * errors.sum() / actual.sum()) if actual.sum() > 0 else None,
        "p90_absolute_error": float(np.quantile(errors, 0.9)),
        "mean_signed_error": float((predicted - actual).mean()),
    }


def evaluate_holdout(pipeline, hourly, start, end):
    """Predict with frozen parameters; all comparison rules share eligible hours."""
    if end <= start:
        raise ValueError("Test end must follow its start")
    if start < hourly.index.min() or end > hourly.index.max() + pd.Timedelta(hours=1):
        raise ValueError("Requested test period is outside the source timeline")
    requests = prepare_forecast_requests(hourly)
    target = hourly["cnt"]
    previous_hour = target.shift(1)
    previous_week = target.shift(168)
    period = (hourly.index >= start) & (hourly.index < end)
    observed = period & target.notna()
    recent_available = observed & previous_hour.notna()
    eligible = recent_available & previous_week.notna()
    if not eligible.any():
        raise ValueError("No eligible test hours with target and required history")
    with threadpool_limits(limits=CPU_THREADS):
        predicted = np.asarray(pipeline.predict(requests.loc[eligible]), dtype=float)
    if predicted.shape != (int(eligible.sum()),) or not np.isfinite(predicted).all() or (predicted < 0).any():
        raise ValueError("Saved pipeline must return one finite nonnegative prediction per target")
    predictions = pd.DataFrame({
        "actual": target.loc[eligible],
        "hist_gradient_boosting": predicted,
        "last_hour": previous_hour.loc[eligible],
        "seasonal_naive": previous_week.loc[eligible],
    })
    coverage = {
        "expected_hours": int(period.sum()),
        "observed_target_hours": int(observed.sum()),
        "missing_target_hours": int((period & target.isna()).sum()),
        "observed_hours_excluded_missing_previous_hour": int((observed & previous_hour.isna()).sum()),
        "additional_hours_excluded_missing_previous_week": int((recent_available & previous_week.isna()).sum()),
        "scored_hours": len(predictions),
        "scored_fraction_of_observed": len(predictions) / int(observed.sum()),
    }
    return predictions, coverage


def run_test_evaluation():
    model_path = OUTPUT_DIR / "models" / "tuned_forecast_pipeline.joblib"
    experiment = OUTPUT_DIR / "experiments" / "hgb_grid_search"
    selection = json.loads((experiment / "metadata.json").read_text())
    split = json.loads((PROCESSED_DATA_DIR / "split.json").read_text())
    if split != selection["test_split"]:
        raise ValueError("Final-test boundaries differ from the frozen model-selection split")
    pipeline = joblib.load(model_path)
    for name, value in selection["best_parameters"].items():
        if pipeline.get_params()[name] != value:
            raise ValueError("Saved model parameters differ from the selected configuration")
    selected_columns = pipeline.named_steps["select"].get_feature_names_out().tolist()
    if selected_columns != selection["selected_features"]:
        raise ValueError("Saved feature set differs from the selected configuration")
    hourly = load_hourly(RAW_DATA_PATH)
    start = pd.Timestamp(split["test_start_inclusive"])
    end = pd.Timestamp(split["test_end_exclusive"])
    predictions, coverage = evaluate_holdout(pipeline, hourly, start, end)
    rows = []
    for name in ["hist_gradient_boosting", "seasonal_naive", "last_hour"]:
        rows.append({"model": name, **metrics(predictions.actual, predictions[name]), **closeness_metrics(predictions.actual, predictions[name])})
    scores = pd.DataFrame(rows).set_index("model")
    destination = OUTPUT_DIR / "experiments" / "final_test"
    destination.mkdir(parents=True, exist_ok=True)
    scores.to_csv(destination / "metrics.csv")
    predictions.to_csv(destination / "test_predictions.csv")
    predictions.head(24).to_csv(destination / "prediction_examples.csv")
    errors = predictions[["actual", "hist_gradient_boosting"]].copy()
    errors["absolute_error"] = (errors.hist_gradient_boosting - errors.actual).abs()
    errors["signed_error"] = errors.hist_gradient_boosting - errors.actual
    for name, groups in [("hour", errors.index.hour), ("weekday", errors.index.day_name())]:
        errors.groupby(groups).agg(mae=("absolute_error", "mean"), rows=("absolute_error", "size")).to_csv(destination / f"errors_by_{name}.csv")
    _, development_target, _, _ = prepare_development()
    low, high = development_target.quantile([0.25, 0.75])
    errors["demand_band"] = np.where(errors.actual <= low, "low", np.where(errors.actual <= high, "middle", "high"))
    errors.groupby("demand_band").agg(mae=("absolute_error", "mean"), rows=("absolute_error", "size")).to_csv(destination / "errors_by_demand_band.csv")
    errors.nlargest(10, "absolute_error").to_csv(destination / "largest_prediction_errors.csv")
    metadata = {
        "evaluated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "final holdout evaluated; do not use these scores to tune this model",
        "protocol": "rolling one-hour-ahead; fixed saved model; earlier actual test observations become later history",
        "test_split": split,
        "coverage": coverage,
        "selected_parameters": selection["best_parameters"],
        "model_sha256": hashlib.sha256(model_path.read_bytes()).hexdigest(),
        "hour_csv_sha256": hashlib.sha256(RAW_DATA_PATH.read_bytes()).hexdigest(),
        "training_only_demand_band_thresholds": {"q25": low, "q75": high},
        "versions": selection["versions"],
        "retrained_or_tuned": False,
    }
    (destination / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    figures = OUTPUT_DIR / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    first_week = predictions.loc[predictions.index < start + pd.Timedelta(days=7)].reindex(pd.date_range(start, periods=168, freq="h"))
    fig, ax = plt.subplots(figsize=(13, 4))
    ax.plot(first_week.index, first_week.actual, label="Actual")
    ax.plot(first_week.index, first_week.hist_gradient_boosting, label="Predicted", alpha=0.8)
    ax.set(title="Final test: first seven calendar days (rolling one hour ahead)", xlabel="Target hour", ylabel="Rentals per hour")
    ax.legend()
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(figures / "09_final_test_predictions.png", dpi=150)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.scatter(predictions.actual, predictions.hist_gradient_boosting, s=12, alpha=0.2)
    maximum = max(predictions.actual.max(), predictions.hist_gradient_boosting.max())
    ax.plot([0, maximum], [0, maximum], "k--", label="Perfect prediction")
    ax.set(title="Final test: all scored hours", xlabel="Actual rentals", ylabel="Predicted rentals")
    ax.set_aspect("equal", adjustable="box")
    ax.legend()
    fig.tight_layout()
    fig.savefig(figures / "10_final_test_scatter.png", dpi=150)
    plt.close(fig)
    table = ["| Model | MAE | RMSE | R² | Within ±50 rentals | Within ±20% |", "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for name, row in scores.iterrows():
        table.append(f"| {name} | {row.mae:.2f} | {row.rmse:.2f} | {row.r2:.4f} | {row.within_50_rentals_pct:.2f}% | {row.within_20_percent_pct:.2f}% |")
    report = f"""# Final chronological test evaluation

The previously selected pipeline was loaded and evaluated without fitting or tuning.
Test period: {start} through just before {end}. Parameters and model/data hashes are
recorded in `outputs/experiments/final_test/metadata.json`.

{chr(10).join(table)}

## Coverage

There are {coverage['expected_hours']} hourly positions, {coverage['observed_target_hours']} observed
targets and {coverage['missing_target_hours']} absent target hours. We scored {coverage['scored_hours']}
hours ({100 * coverage['scored_fraction_of_observed']:.2f}% of observed targets), shared by every comparison.
Of observed targets, {coverage['observed_hours_excluded_missing_previous_hour']} lack previous-hour demand;
another {coverage['additional_hours_excluded_missing_previous_week']} lack previous-week demand.
These exclusion counts do not overlap. Missing demand is never filled with zero.

## Interpretation and limits

MAE/RMSE are rentals per hour; tolerance percentages are not classification accuracy. These
metrics summarize the whole test period, unlike the earlier mean-of-fold validation scores.
Relative tolerance excludes zero-demand hours. Error tables cover hour, weekday and actual-demand
bands using only development-target thresholds ({low:.2f}, {high:.2f}); band membership is a
retrospective diagnostic, not a future input.

This is rolling one-hour-ahead prediction. Earlier observed test counts are available as history
for later targets. The fitted parameters stay fixed. This is not a 90-day forecast made in October.
The first-week plot is selected by date; the scatter plot covers every scored test hour.

This holdout is now used. Report its results as observed; do not keep tuning against it and then
claim it is still an untouched test. Future modelling changes need a separate evaluation strategy.
Historical single-city data, immediate count availability, missing-hour coverage and timezone-naive
timestamps still limit generalization. The baseline rows are simple prediction rules, not additional
trained models. The saved HGB pipeline was not changed by this evaluation.
"""
    (OUTPUT_DIR / "reports" / "final_test_report.md").write_text(report, encoding="utf-8")
    print(f"Scored {coverage['scored_hours']} of {coverage['observed_target_hours']} observed test hours; no fitting or tuning.")
    return scores[["mae", "rmse", "r2", "within_50_rentals_pct", "within_20_percent_pct"]]
