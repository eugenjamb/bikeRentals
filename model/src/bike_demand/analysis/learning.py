"""Explain boosting progress with training and chronological validation MAE."""

import json
import logging
from time import perf_counter

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.metrics import mean_absolute_error
from threadpoolctl import threadpool_limits

from ..config import CPU_THREADS, OUTPUT_DIR
from ..forecast_pipeline import make_forecast_pipeline
from ..data import prepare_development
from ..training import expanding_splits

logger = logging.getLogger(__name__)


def iteration_errors(pipeline, requests, target, splits):
    """Refit the fixed selected configuration per fold; do not tune from this plot."""
    rows = []
    for fold, (train, valid) in enumerate(splits, start=1):
        started = perf_counter()
        logger.info("Learning curve: fold %d/%d fitting the selected model", fold, len(splits))
        fitted = clone(pipeline).fit(requests.iloc[train], target.iloc[train])
        transformed_train = fitted[:-1].transform(requests.iloc[train])
        transformed_valid = fitted[:-1].transform(requests.iloc[valid])
        regressor = fitted.named_steps["regressor"]
        stages = zip(regressor.staged_predict(transformed_train), regressor.staged_predict(transformed_valid))
        for iteration, (train_prediction, valid_prediction) in enumerate(stages, start=1):
            rows.append({
                "fold": fold,
                "iteration": iteration,
                "training_mae": mean_absolute_error(target.iloc[train], np.maximum(0, train_prediction)),
                "validation_mae": mean_absolute_error(target.iloc[valid], np.maximum(0, valid_prediction)),
            })
            if iteration == 1 or iteration % 50 == 0:
                logger.info("Learning curve: fold %d/%d | iteration %d/%d | train MAE %.3f | validation MAE %.3f", fold, len(splits), iteration, regressor.n_iter_, rows[-1]["training_mae"], rows[-1]["validation_mae"])
        logger.info("Learning curve: fold %d/%d finished in %.1fs", fold, len(splits), perf_counter() - started)
    return pd.DataFrame(rows)


def explain_learning():
    experiment = OUTPUT_DIR / "experiments" / "hgb_grid_search"
    metadata = json.loads((experiment / "metadata.json").read_text())
    requests, target, split, folds = prepare_development()
    if split != metadata["test_split"] or folds != metadata["folds"]:
        raise ValueError("Current data/splits differ from the saved selection experiment")
    splits = expanding_splits(requests.index, folds, pd.Timestamp(split["test_start_inclusive"]))
    pipeline = make_forecast_pipeline().set_params(**metadata["best_parameters"])
    with threadpool_limits(limits=CPU_THREADS):
        progress = iteration_errors(pipeline, requests, target, splits)
    progress.to_csv(experiment / "learning_progress.csv", index=False)
    means = progress.groupby("iteration")[["training_mae", "validation_mae"]].mean()
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(means.index, means.training_mae, label="Training MAE (mean of 3 folds)")
    ax.plot(means.index, means.validation_mae, label="Validation MAE (mean of 3 folds)")
    ax.set(title="How HGB learned: fixed selected settings", xlabel="Boosting iteration (trees added)", ylabel="Mean absolute error (rentals/hour)")
    ax.legend()
    ax.grid(alpha=0.25)
    fig.tight_layout()
    (OUTPUT_DIR / "figures").mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_DIR / "figures" / "08_hgb_learning_progress.png", dpi=150)
    plt.close(fig)
    first, last = means.iloc[0], means.iloc[-1]
    report = f"""# How the selected model learned

Algorithm: Histogram Gradient Boosting regression. It starts with a constant prediction,
then adds regression trees that correct errors in the current ensemble. Learning rate scales
each tree's contribution. Here there are {len(means)} iterations. This is tree boosting, not
neural-network epochs or pretrained-model fine-tuning. Model fitting minimizes squared error;
we monitor MAE because MAE is the model-selection metric, so MAE need not fall at every step.

## Training versus validation

Each curve averages three folds. Preprocessing and the model are refitted using only each
fold's training period. Validation predictions use earlier observed demand as history.

| Boosting stage | Mean training MAE | Mean validation MAE |
| --- | ---: | ---: |
| After first tree | {first.training_mae:.2f} | {first.validation_mae:.2f} |
| After {len(means)} trees | {last.training_mae:.2f} | {last.validation_mae:.2f} |

Training error measures fit to examples used for learning. Validation error measures later
hours not used to fit that fold. Lower validation error indicates more useful predictions.
A growing training/validation gap can indicate overfitting, but this plot alone does not
establish a model's generalization performance. These folds already selected the parameters.
We do not change the iteration count based on this diagnostic plot.

The saved deployment-candidate pipeline is separately refitted on all eligible development
hours. This plot describes fold models, not a score from that final refit on its own training data.
Final-test results are recorded separately; this learning plot uses development folds only. Inspect actual-versus-predicted plots and the first-day
prediction examples in `validation_closeness.md` to connect these curves to concrete errors.
"""
    (OUTPUT_DIR / "reports" / "hgb_learning.md").write_text(report, encoding="utf-8")
    print(f"Learning progress: first-tree validation MAE {first.validation_mae:.2f}; final {last.validation_mae:.2f}.")
    return progress
