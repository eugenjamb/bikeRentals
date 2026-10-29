# Model workflow

One algorithm: **Histogram Gradient Boosting regression**. One saved sklearn pipeline. Four commands, run from the repository root with your venv activated:

```bash
python model/scripts/prepare.py
python model/scripts/train.py
python model/scripts/evaluate.py --split validation
python model/scripts/evaluate.py --split test
```

`prepare` downloads/reuses the data, audits timestamps, freezes the time split and creates EDA figures. `train` runs the original 32-configuration grid, saves the winner and generates learning/prediction diagnostics. Evaluation never fits or tunes: validation reads saved fold predictions, while test loads the frozen pipeline.

Training logs each stage with a timestamp and each completed CV fit with parameters, negative-MAE scores and duration. Negative MAE closer to zero is better; final metrics use positive MAE. Learning-curve progress is logged every 50 trees. CPU use defaults to two native threads, with an explicit joblib budget to avoid Windows physical-core discovery warnings. No extra shell variable is needed.

For a single prediction, provide your own past-only CSV with `timestamp,cnt` columns:

```bash
python model/scripts/predict.py --history data/past_counts.csv --target "2012-10-03T00:00:00" --holiday 0 --workingday 1
```

The most recent completed hour must be present. History is aligned to the preceding 168 hourly positions. Missing counts remain unknown; target/future observations are rejected.

## Read the code in this order

| File in `src/bike_demand/` | Responsibility | Start with |
| --- | --- | --- |
| `data.py` | Download, timestamp validation, hourly grid and development folds | `load_hourly`, `prepare_development` |
| `forecast_pipeline.py` | History requests, causal features, feature selection and HGB | `make_forecast_pipeline` |
| `preprocessing.py` | Fold-fitted encoding, numeric imputation and scaling | `make_preprocessor` |
| `training.py` | Expanding CV, GridSearchCV, scores and saved pipeline | `run_grid_search`, `train_model` |
| `evaluation.py` | Regression metrics and final evaluation without fitting | `metrics`, `evaluate_holdout` |
| `config.py` | Paths, seeds and history-window settings | module constants |

`analysis/` groups EDA, validation plots and learning curves. Plotting is separate from model logic. `scripts/` contains only command-line entry points. The notebook explores the data; it does not implement another training pipeline.

```text
model/
  README.md
  requirements.txt
  requirements-lock.txt
  pytest.ini
  scripts/
    prepare.py
    train.py
    evaluate.py
    predict.py
  src/bike_demand/
    config.py
    data.py
    forecast_pipeline.py
    preprocessing.py
    training.py
    evaluation.py
    analysis/
      eda.py
      diagnostics.py
      learning.py
  notebooks/01_exploration.ipynb
  tests/
    conftest.py
    test_data.py
    test_pipeline.py
    test_training.py
    test_evaluation.py
```

## Interview walkthrough

**Problem:** after hour t ends, predict total rentals (`cnt`) during t+1. This is numerical regression. Counts are assumed available immediately when each hour closes.

**X and y:** each request contains the target timestamp, known `holiday`/`workingday` flags and the previous 168 hourly counts. The target's own `cnt` stays separate as y. `casual` and `registered` are excluded because they sum to y. Observed target-hour weather is unavailable at forecast origin and excluded.

**Features:** calendar facts, cyclical encodings, elapsed time, demand lags 1/2/24/48/168 and shifted 24/168-hour means/std. Every history window ends before the target. Missing timestamps are restored before constructing history.

**Pipeline:** `features → select → preprocess → regressor`. Feature selection compares two domain sets: calendar + lags, with or without rolling summaries. Encoding, numeric medians and scaling fit inside each training fold. The regressor adds trees that correct current errors; saved predictions are clipped at zero.

**Validation:** three expanding training windows precede 28-day blocks starting 11 July, 8 August and 5 September 2012. The final 90 days start 3 October. Calendar boundaries are fixed before missing-history rows are filtered. Earlier observed validation/test counts become history for later targets, matching rolling one-hour-ahead operation. Model parameters stay fixed within a block.

**Grid search:** two feature sets × two learning rates × two iteration counts × two leaf limits × two regularization values = 32 configurations and 96 CV fits. Selection minimizes mean fold MAE. The winner is refitted on development data. Grid search runs during training, never during prediction.

**Selected settings:** full feature set, learning rate 0.1, 200 iterations, 31 leaves, L2 regularization 1. Minimum leaf size stays 20, seed 42 and internal random early stopping is disabled.

**Results:** validation MAE 31.6033 versus 32.0696 before tuning. Final-test MAE 27.124, RMSE 42.667 and R² 0.9551 over 2,076 eligible hours. The periods differ, so the validation-to-test change is not a measurement of tuning improvement. Tolerance percentages are explicitly defined, not classification accuracy. The final test has now been used; keep it out of further tuning decisions.

## Tests and artifacts

```bash
python -m pytest -c model/pytest.ini model/tests
```

Tests cover missing timestamps, future-demand leakage, past-only requests, pipeline serialization, chronological folds, grid integration, metric edge cases and evaluation without fitting.

Outputs stay outside the source directory:

- `outputs/models/tuned_forecast_pipeline.joblib`: the one fitted pipeline.
- `outputs/experiments/hgb_grid_search/`: candidates, selected parameters and fold scores.
- `outputs/experiments/final_test/`: final metrics, coverage and model/data hashes.
- `outputs/figures/` and `outputs/reports/`: plots and explanations.

The cleanup preserves saved-pipeline class locations and does not require retraining. Dependencies and modelling settings remain unchanged. `requirements.txt` pins direct dependencies; `requirements-lock.txt` records the full reference Windows environment.

## Application integration

The fitted pipeline is loaded once by `backend/app/service.py`; inference does not call grid search or retrain. The API validates 168 ordered past hourly positions and rejects target/future observations before passing them to the same feature pipeline.

For setup, routes and serving details, see the [backend guide](../backend/README.md). The [frontend guide](../frontend/README.md) explains the case study and historical forecast lab. The raw dataset and model binary are ignored by Git, so a fresh clone needs preparation, training and evaluation before exporting matching showcase assets.
