# Bike Rental Demand Prediction

Predict next-hour bike rental demand with Python and scikit-learn, using the UCI Bike Sharing dataset. This project focuses on regression, leakage prevention, chronological validation and reproducible experiments.

**Current status:** EDA, historical features, regression pipelines and an initial fixed-setting model comparison are implemented. Hyperparameter tuning and final-test evaluation are pending. The FastAPI backend, frontend and Docker packaging are planned; their folders are placeholders.

## Initial results

Scores below are the arithmetic means of three expanding-window validation folds. They are **development-validation results, not final-test results**. No hyperparameter search has been performed.

| Model | MAE ↓ | RMSE ↓ | R² ↑ |
| --- | ---: | ---: | ---: |
| Histogram gradient boosting | **32.07** | **50.46** | **0.9536** |
| Random Forest | 34.03 | 55.43 | 0.9441 |
| Ridge | 47.83 | 70.80 | 0.9085 |
| Same hour previous week | 55.97 | 98.68 | 0.8226 |
| Previous hour | 97.57 | 142.29 | 0.6298 |

MAE and RMSE are measured in rentals per hour. Histogram gradient boosting is the provisional choice by mean validation MAE. Its error is higher around evening demand peaks; see the [initial model report](outputs/reports/initial_model_report.md) for fold scores, error analysis and limitations.

## Exploration

![Mean demand by weekday and hour](outputs/figures/02_weekday_hour_heatmap.png)

Weekdays show morning and evening peaks, while weekends have broader midday demand. Additional figures cover demand distribution, changes over time, temperature, weather correlations and missing timestamps.

- [Executed exploration notebook](model/notebooks/01_exploration.ipynb)
- [EDA findings and feature decisions](outputs/reports/eda_findings.md)
- [Saved experiment metrics and parameters](outputs/experiments/initial_fixed_settings/)

The source file contains 17,379 observations between 2011-01-01 and 2012-12-31. There are 165 absent hourly timestamps. The loader reindexes to a complete hourly grid so lags represent elapsed hours. Missing observations remain unknown; they are not assumed to be zero demand.

## Prediction contract

After hour **t** finishes and its count becomes available, predict the total rentals during hour **t + 1**. Feature rows are indexed by the hour being predicted.

For a prediction covering 18:00–18:59, the latest available demand is from 17:00–17:59. A lag of 168 refers to the same target hour one week earlier.

| Input family | Features |
| --- | --- |
| Calendar | Hour, weekday, month, weekend, holiday and working-day flags |
| Calendar cycles | Sine/cosine encodings of hour, weekday and month |
| Time trend | Days since 2011-01-01 |
| Demand history | Lags of 1, 2, 24, 48 and 168 hours |
| Historical summaries | Shifted 24-hour and 168-hour rolling means and standard deviations |

Rolling summaries exclude the target hour. The initial shared feature set is domain-informed and has not undergone feature ablation or optimization.

`casual` and `registered` are excluded because their sum equals the target `cnt`. The record identifier `instant` is excluded. Target-hour observed weather is excluded because it is unavailable at forecast origin; weather plots are descriptive only.

## Evaluation design

- **Holdout:** 2012-10-03 00:00 through 2012-12-31 23:00, the final 90 days. Its demand has not been scored or used in the EDA figures.
- **Validation:** three successive 28-day blocks, starting 2012-07-11, 2012-08-08 and 2012-09-05. Each training window expands up to the next validation boundary.
- **Shared coverage:** score all models on the same observed target hours with available last-hour and previous-week counts. Each validation block currently has 672 eligible hours.
- **Preprocessing:** one-hot encoding, numeric median imputation and scaling are fitted inside each training pipeline. Histogram gradient boosting's random internal early stopping is disabled.
- **Selection:** lowest mean fold MAE. Report RMSE and R² alongside it. Negative predictions are clipped to zero without rounding.

This is **rolling one-hour-ahead evaluation**: earlier observed validation counts become available as inputs for later validation predictions. Model parameters remain fixed within each fold. It is not a forecast of an entire future block made from a single origin.

Current settings are Ridge alpha 1, Random Forest 100 trees, and histogram gradient boosting with 100 boosting iterations. Exact parameters, versions, split boundaries and dataset checksum are recorded in [experiment metadata](outputs/experiments/initial_fixed_settings/metadata.json).

## Run locally

Use Python 3.11. From the repository root in **Git Bash on Windows**:

```bash
py -3.11 -m venv .venv
source .venv/Scripts/activate
python -m pip install -r model/requirements-lock.txt
```

If your environment already exists and is activated, start with the installation command. The lock file records the full Windows environment used for the checked-in results. On Linux/macOS, create the environment with `python3.11 -m venv .venv`, activate with `source .venv/bin/activate`, and install `model/requirements.txt`; the full Windows lock includes platform-specific packages.

Run each stage in order:

```bash
# Download the original archive and record provenance/checksum.
python model/download_data.py

# Audit timestamps, freeze the holdout boundary and save EDA figures.
python model/run_eda.py

# Check feature leakage, missing hours and saved-pipeline prediction.
python -m pytest -c model/pytest.ini

# Compare the two baselines and three regressors with fixed settings.
python model/train.py

# Explore the notebook interactively.
python -m jupyterlab model/notebooks/01_exploration.ipynb
```

On Windows, if joblib warns that it cannot detect physical CPU cores, training still works using its fallback. You can supply a core-count value for the command:

```bash
LOKY_MAX_CPU_COUNT=4 python model/train.py
```

Training saves `outputs/models/development_pipeline.joblib`. It expects engineered features, not a raw timestamp or history payload. Feature construction and clipping predictions to zero remain the caller's responsibility. The saved pipeline is a development artifact; the serving layer is not implemented yet.

Commands regenerate files in their output locations. Small reference figures, summary metrics and reports are included in Git for review. Downloaded datasets, processed data, per-hour validation prediction exports, virtual environments and trained model binaries are excluded and can be rebuilt locally.

## Repository structure

```text
.
├── model/
│   ├── notebooks/01_exploration.ipynb
│   ├── src/bike_demand/       # loading, features, EDA and training
│   ├── tests/                # leakage and prediction checks
│   ├── download_data.py
│   ├── run_eda.py
│   ├── train.py
│   ├── requirements.txt      # pinned direct dependencies
│   └── requirements-lock.txt # full reference Windows environment
├── data/
│   ├── raw/                  # downloaded archive and source files (ignored)
│   └── processed/            # frozen split metadata (ignored)
├── outputs/
│   ├── experiments/          # reference metrics and parameters
│   ├── figures/              # EDA plots
│   ├── reports/              # findings and initial model report
│   └── models/               # generated fitted pipelines (ignored)
├── backend/                  # planned FastAPI service
├── frontend/                 # planned demonstration interface
└── .vscode/settings.json     # workspace-relative interpreter and source paths
```

## Limitations and next steps

The data describes one historical system in 2011–2012. Results do not establish present-day demand or performance in another city. Validation currently covers July through early October, so broader seasonal validation is needed. Immediate demand availability and an advance holiday calendar are assumptions. Local date/hour labels lack timezone offsets, leaving daylight-saving ambiguity unresolved.

Temperature plots retain normalized source units because the bundled README and current UCI web metadata disagree about the Celsius conversion. Weather associations do not establish causal effects.

Planned work:

- Review feature ablations, peak-hour errors and demand-level error analysis.
- Perform manageable `GridSearchCV` hyperparameter tuning on chronological development folds.
- Freeze the selected configuration, evaluate the final test and report MAE, RMSE and R² against baselines.
- Add a tested FastAPI prediction service, then a small frontend and Docker packaging.

## Dataset attribution

[UCI Bike Sharing](https://doi.org/10.24432/C5W894), contributed by Hadi Fanaee-T, contains hourly and daily Capital Bikeshare counts from Washington, DC during 2011–2012. UCI lists the dataset under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). This project uses `hour.csv`; the downloader retains the original archive and README locally and records the source URL, timestamp and SHA-256 checksum.

The archive requests citation of: Fanaee-T, Hadi, and Gama, Joao. “Event labeling combining ensemble detectors and background knowledge.” *Progress in Artificial Intelligence* (2013). [doi:10.1007/s13748-013-0040-3](https://doi.org/10.1007/s13748-013-0040-3).
