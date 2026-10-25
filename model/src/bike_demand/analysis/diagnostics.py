"""Inspect saved out-of-fold predictions without scoring the final test."""

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ..config import OUTPUT_DIR
from ..evaluation import closeness_metrics


def validate_predictions(predictions, metadata):
    """Reject holdout rows, malformed folds and inconsistent model coverage."""
    test_start = pd.Timestamp(metadata["test_split"]["test_start_inclusive"])
    timestamps = predictions["target_timestamp"]
    if timestamps.isna().any() or (timestamps >= test_start).any():
        raise ValueError("Diagnostics accept only pre-test validation predictions")
    if predictions.duplicated(["model", "target_timestamp"]).any():
        raise ValueError("Duplicate model/timestamp predictions")
    known_folds = {fold["fold"] for fold in metadata["folds"]}
    if set(predictions["fold"]) != known_folds:
        raise ValueError("Prediction fold IDs differ from metadata")
    reference = None
    for _, group in predictions.groupby("model"):
        for fold in metadata["folds"]:
            block = group.loc[group["fold"] == fold["fold"]]
            start = pd.Timestamp(fold["validation_start"])
            end = pd.Timestamp(fold["validation_end_exclusive"])
            if len(block) != fold["eligible_validation_rows"] or not block["target_timestamp"].between(start, end, inclusive="left").all():
                raise ValueError("Validation rows differ from recorded fold boundaries or coverage")
        current = group.set_index("target_timestamp")[["actual", "fold"]].sort_index()
        if reference is not None and not current.equals(reference):
            raise ValueError("Models must share timestamps, actual counts and folds")
        reference = current
    expected_models = {"hist_gradient_boosting"}
    if set(predictions["model"]) != expected_models:
        raise ValueError("Prediction models differ from experiment metadata")


def run_diagnostics():
    experiment = OUTPUT_DIR / "experiments" / "hgb_grid_search"
    source = experiment / "validation_predictions.csv"
    if not source.exists():
        raise FileNotFoundError("Run python model/scripts/train.py first")
    metadata = json.loads((experiment / "metadata.json").read_text())
    predictions = pd.read_csv(source, parse_dates=["target_timestamp"])
    selected = predictions.loc[predictions["configuration"] == "selected_grid_configuration"].copy()
    selected["model"] = "hist_gradient_boosting"
    validate_predictions(selected, metadata)
    selected = selected.sort_values("target_timestamp")
    selected["absolute_error"] = (selected["actual"] - selected["predicted"]).abs()
    selected["signed_error"] = selected["predicted"] - selected["actual"]
    values = closeness_metrics(selected["actual"], selected["predicted"])
    summary = pd.DataFrame([{"model": "hist_gradient_boosting", **values}]).set_index("model")
    summary.to_csv(experiment / "selected_model_closeness.csv")
    selected.head(24).to_csv(experiment / "prediction_examples.csv", index=False)
    selected.nlargest(10, "absolute_error").to_csv(experiment / "largest_prediction_errors.csv", index=False)
    for name, groups in [("hour", selected["target_timestamp"].dt.hour), ("weekday", selected["target_timestamp"].dt.day_name())]:
        selected.groupby(groups).agg(mae=("absolute_error", "mean"), rows=("absolute_error", "size")).to_csv(experiment / f"errors_by_{name}.csv")

    # Demand-band cutoffs are learned from each fold's training target only.
    from ..data import prepare_development
    _, training_target, _, _ = prepare_development()
    selected["demand_band"] = ""
    cutoffs = []
    for fold in metadata["folds"]:
        earlier = training_target.loc[training_target.index < pd.Timestamp(fold["validation_start"])]
        low, high = earlier.quantile([0.25, 0.75])
        mask = selected["fold"] == fold["fold"]
        actual = selected.loc[mask, "actual"]
        selected.loc[mask, "demand_band"] = np.where(actual <= low, "low", np.where(actual <= high, "middle", "high"))
        cutoffs.append({"fold": fold["fold"], "training_q25": low, "training_q75": high})
    selected.groupby("demand_band").agg(mae=("absolute_error", "mean"), rows=("absolute_error", "size")).to_csv(experiment / "errors_by_demand_band.csv")
    pd.DataFrame(cutoffs).to_csv(experiment / "demand_band_thresholds.csv", index=False)
    figures = OUTPUT_DIR / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    start = selected["target_timestamp"].min()
    week = selected.loc[selected["target_timestamp"] < start + pd.Timedelta(days=7)]
    week = week.set_index("target_timestamp").asfreq("h")
    fig, ax = plt.subplots(figsize=(13, 4))
    ax.plot(week.index, week["actual"], label="Actual", linewidth=1.5)
    ax.plot(week.index, week["predicted"], label="Predicted", linewidth=1.1, alpha=0.8)
    ax.set(title="Tuned HGB: first validation week (one hour ahead)", ylabel="Rentals per hour", xlabel="Target hour")
    ax.legend()
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(figures / "06_validation_actual_vs_predicted.png", dpi=150)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    axes[0].scatter(selected["actual"], selected["predicted"], alpha=0.2, s=12)
    maximum = max(selected["actual"].max(), selected["predicted"].max())
    axes[0].plot([0, maximum], [0, maximum], "k--", label="Perfect prediction")
    axes[0].set(xlabel="Actual rentals", ylabel="Predicted rentals", title="Tuned HGB: all validation hours")
    axes[0].set_aspect("equal", adjustable="box")
    axes[0].legend()
    ordered_errors = np.sort(selected["absolute_error"])
    axes[1].plot(ordered_errors, 100 * np.arange(1, len(ordered_errors) + 1) / len(ordered_errors))
    axes[1].axvline(50, color="tab:orange", linestyle="--", label="50 rentals")
    axes[1].set(xlabel="Absolute error (rentals)", ylabel="Predictions within this error (%)", title="Cumulative error distribution", ylim=(0, 100))
    axes[1].legend()
    fig.tight_layout()
    fig.savefig(figures / "07_validation_scatter_and_error_coverage.png", dpi=150)
    plt.close(fig)

    examples = selected.head(24)
    example_lines = ["| Target hour | Actual rentals | Predicted rentals | Absolute error |", "| --- | ---: | ---: | ---: |"]
    for row in examples.itertuples():
        example_lines.append(f"| {row.target_timestamp} | {row.actual:.0f} | {row.predicted:.2f} | {row.absolute_error:.2f} |")
    report = f"""# How close are the selected model's predictions?

Model: **tuned Histogram Gradient Boosting**. Source: {values['rows']} saved out-of-fold
predictions over three chronological validation folds. Final-test results are recorded separately in final_test_report.md.
These folds were used for model selection, so the scores are not an independent final estimate.
No new hyperparameters are selected by this diagnostics command.

- Average absolute error: **{values['pooled_mae']:.2f} rentals/hour**.
- Within +/-20 rentals: **{values['within_20_rentals_pct']:.2f}%**.
- Within +/-50 rentals: **{values['within_50_rentals_pct']:.2f}%**.
- Within +/-20% of actual demand: **{values['within_20_percent_pct']:.2f}%** on positive-demand hours.
- WAPE: **{values['wape_pct']:.2f}%** (sum of absolute errors / sum of actual rentals).
- 90th percentile absolute error: **{values['p90_absolute_error']:.2f} rentals**.
- Mean signed error (predicted minus actual): **{values['mean_signed_error']:.2f} rentals**.

Tolerance conditions are separate illustrative thresholds, not classification accuracy.
Relative tolerance excludes {values['relative_tolerance_excluded_zero_rows']} zero-demand hours.
WAPE is not a percentage of correct predictions. Signed errors can cancel.

## Actual prediction examples

These are the first 24 validation hours, selected by date rather than performance.
Each prediction is made by a model trained only before that validation block; later observations
within the block supply history for later one-hour-ahead predictions. This is not a 24-hour
forecast issued at midnight.

{chr(10).join(example_lines)}

The first-week time plot uses the same date-based selection. All 2,016 validation hours appear
in the scatter/error-coverage plots. In the scatter plot, points on the diagonal are perfect;
points below it are underpredictions. Look at the largest-error CSV alongside these averages.

Hour, weekday and demand-band errors are saved in `outputs/experiments/hgb_grid_search/`.
Demand bands use each fold's training-demand 25th and 75th percentiles, not validation quantiles;
the thresholds are recorded separately. Actual demand bands are retrospective diagnostics,
not input features available at forecast origin.

Keep the recorded final test separate from feature and parameter selection.
"""
    (OUTPUT_DIR / "reports" / "validation_closeness.md").write_text(report, encoding="utf-8")
    return summary
