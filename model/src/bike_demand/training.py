"""Chronological feature-set and HGB hyperparameter selection; no test scoring."""

import json
import logging
import platform
from importlib.metadata import version
from time import perf_counter

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.model_selection import GridSearchCV, ParameterGrid
from threadpoolctl import threadpool_limits

from .config import CPU_THREADS, OUTPUT_DIR, RAW_DATA_PATH
from .evaluation import closeness_metrics, metrics
from .forecast_pipeline import FEATURE_SETS, make_forecast_pipeline
from .data import prepare_development

logger = logging.getLogger(__name__)

PARAMETER_GRID = {
    "select__feature_set": list(FEATURE_SETS),
    "regressor__learning_rate": [0.05, 0.1],
    "regressor__max_iter": [100, 200],
    "regressor__max_leaf_nodes": [15, 31],
    "regressor__l2_regularization": [0.0, 1.0],
}


def expanding_splits(index, fold_metadata, test_start):
    """Use fixed calendar boundaries before any sample filtering, never row counts."""
    splits = []
    for fold in fold_metadata:
        start = pd.Timestamp(fold["validation_start"])
        end = pd.Timestamp(fold["validation_end_exclusive"])
        if end > test_start:
            raise ValueError("Validation must end before the held-out test")
        train = np.flatnonzero(index < start)
        valid = np.flatnonzero((index >= start) & (index < end))
        if len(train) == 0 or len(valid) == 0 or index[train].max() >= index[valid].min():
            raise ValueError("Each expanding fold needs earlier training and later validation")
        if len(train) != fold["training_rows"] or len(valid) != fold["eligible_validation_rows"]:
            raise ValueError("Fold coverage differs from its recorded definition; investigate")
        splits.append((train, valid))
    return splits


def evaluate_configuration(pipeline, requests, target, splits, name):
    scores, predictions = [], []
    for fold, (train, valid) in enumerate(splits, start=1):
        started = perf_counter()
        logger.info("%s: fold %d/%d starting (%d training, %d validation rows)", name, fold, len(splits), len(train), len(valid))
        fitted = clone(pipeline).fit(requests.iloc[train], target.iloc[train])
        predicted = fitted.predict(requests.iloc[valid])
        scores.append({"configuration": name, "fold": fold, **metrics(target.iloc[valid], predicted)})
        logger.info("%s: fold %d/%d finished in %.1fs | MAE %.3f", name, fold, len(splits), perf_counter() - started, scores[-1]["mae"])
        predictions.append(pd.DataFrame({"target_timestamp": requests.index[valid], "configuration": name, "fold": fold, "actual": target.iloc[valid].to_numpy(), "predicted": predicted}))
    return pd.DataFrame(scores), pd.concat(predictions, ignore_index=True)


def run_grid_search():
    started = perf_counter()
    logger.info("[1/4] Loading development data and preparing chronological folds")
    requests, target, split, folds = prepare_development()
    logger.info("Prepared %d eligible rows | %s through %s | final test excluded", len(requests), requests.index.min(), requests.index.max())
    test_start = pd.Timestamp(split["test_start_inclusive"])
    splits = expanding_splits(requests.index, folds, test_start)
    destination = OUTPUT_DIR / "experiments" / "hgb_grid_search"
    destination.mkdir(parents=True, exist_ok=True)
    pipeline = make_forecast_pipeline()
    count = len(ParameterGrid(PARAMETER_GRID))
    logger.info("[2/4] Grid search: %d configurations x %d folds = %d fits, followed by development refit", count, len(splits), count * len(splits))
    logger.info("CPU budget: %d native threads; one grid fit at a time. CV train/test scores are NEGATIVE MAE (closer to zero is better).", CPU_THREADS)
    search = GridSearchCV(pipeline, PARAMETER_GRID, scoring="neg_mean_absolute_error", cv=splits, refit=True, return_train_score=True, n_jobs=1, error_score="raise", verbose=3)
    # Bound CPU use; grid candidates run serially to avoid Windows worker overhead.
    with threadpool_limits(limits=CPU_THREADS):
        search.fit(requests, target)
        logger.info("Grid search and development refit completed in %.1fs | best CV MAE %.3f", perf_counter() - started, -search.best_score_)
        logger.info("Selected parameters: %s", search.best_params_)
        logger.info("Rechecking untuned and selected HGB settings on each validation fold")
        baseline_scores, baseline_predictions = evaluate_configuration(pipeline, requests, target, splits, "untuned_full_features")
        tuned_scores, tuned_predictions = evaluate_configuration(search.best_estimator_, requests, target, splits, "selected_grid_configuration")
    results = pd.DataFrame(search.cv_results_)
    results["mean_validation_mae"] = -results["mean_test_score"]
    # sklearn calls CV validation "test" in cv_results_; it is NOT our final holdout.
    results.sort_values("rank_test_score").to_csv(destination / "cv_results.csv", index=False)
    scores = pd.concat([baseline_scores, tuned_scores], ignore_index=True)
    scores.to_csv(destination / "fold_metrics.csv", index=False)
    predictions = pd.concat([baseline_predictions, tuned_predictions], ignore_index=True)
    predictions.to_csv(destination / "validation_predictions.csv", index=False)
    close = pd.DataFrame([{"configuration": name, **closeness_metrics(group.actual, group.predicted)} for name, group in predictions.groupby("configuration")])
    close.to_csv(destination / "validation_closeness.csv", index=False)
    summary = scores.groupby("configuration")[["mae", "rmse", "r2"]].mean()
    summary.to_csv(destination / "mean_cv_metrics.csv")
    selected_features = search.best_estimator_.named_steps["select"].get_feature_names_out().tolist()
    model_path = OUTPUT_DIR / "models" / "tuned_forecast_pipeline.joblib"
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(search.best_estimator_, model_path)
    logger.info("Saved fitted pipeline: %s", model_path)
    metadata = {
        "status": "development-only search; this command does not evaluate the final test",
        "algorithm": "HistogramGradientBoostingRegressor with nonnegative prediction clipping",
        "selection_metric": "mean fold MAE",
        "best_cv_mae": -search.best_score_,
        "best_parameters": search.best_params_,
        "selected_features": selected_features,
        "parameter_grid": PARAMETER_GRID,
        "candidate_count": count,
        "cv_fit_count": count * len(splits),
        "folds": folds,
        "test_split": split,
        "development_fit_rows": len(requests),
        "final_regressor_parameters": search.best_estimator_.named_steps["regressor"].get_params(),
        "pipeline_steps": list(search.best_estimator_.named_steps),
        "request_contract": "DatetimeIndex target hours; holiday/workingday binary calendar flags; demand_history holds exactly 168 counts t-168..t-1, oldest first, with NaN for unknown hours. Last completed count required. No target count or target-hour observed weather.",
        "feature_selection": "Two predeclared domain feature sets, chosen within CV; no target-correlation filtering",
        "validation_protocol": "Rolling one-hour-ahead, parameters fixed per fold; earlier validation observations are available as later history",
        "dataset_provenance": json.loads((RAW_DATA_PATH.parent / "provenance.json").read_text()),
        "versions": {"python": platform.python_version(), **{name: version(name) for name in ["numpy", "pandas", "scikit-learn", "joblib"]}},
        "limitations": ["Selected CV scores are optimistic after searching these same folds; Independent final-test results are recorded separately.", "Validation covers July through early October rather than all seasons.", "Single-city historical data and immediate count availability assumptions still apply."],
    }
    (destination / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    report = f"""# Histogram gradient boosting: grid-search summary

Development-only search: {count} configurations x {len(splits)} expanding folds.
Selection metric: mean validation MAE. Final-test evaluation is a separate command.

Selected parameters:
```json
{json.dumps(search.best_params_, indent=2)}
```

Mean fold metrics (MAE, RMSE, R2):
```text
{summary.to_string()}
```

Complete fitted pipeline: `outputs/models/tuned_forecast_pipeline.joblib`.
All candidates and fold scores are saved beside metadata in `outputs/experiments/hgb_grid_search/`.
See `model/README.md` for the pipeline contract and interview walkthrough.
"""
    (OUTPUT_DIR / "reports" / "hgb_grid_search.md").write_text(report, encoding="utf-8")
    print("Best parameters:", search.best_params_)
    print(summary.to_string())
    print(f"Saved complete forecast pipeline: {model_path}")
    logger.info("Search artifacts and scores saved to %s", destination)
    return search


def train_model():
    """Execute the complete HGB workflow; never evaluate the final holdout."""
    from .analysis.diagnostics import run_diagnostics
    from .analysis.learning import explain_learning

    started = perf_counter()
    search = run_grid_search()
    logger.info("[3/4] Generating validation predictions, error tables and plots")
    print(run_diagnostics().round(2).to_string())
    logger.info("[4/4] Generating learning curves with the fixed selected parameters")
    explain_learning()
    logger.info("Training workflow complete in %.1fs. Final test was not evaluated by this command.", perf_counter() - started)
    return search
