# Final chronological test evaluation

The previously selected pipeline was loaded and evaluated without fitting or tuning.
Test period: 2012-10-03 00:00:00 through just before 2013-01-01 00:00:00. Parameters and model/data hashes are
recorded in `outputs/experiments/final_test/metadata.json`.

| Model | MAE | RMSE | R² | Within ±50 rentals | Within ±20% |
| --- | ---: | ---: | ---: | ---: | ---: |
| hist_gradient_boosting | 27.12 | 42.67 | 0.9551 | 83.77% | 67.34% |
| seasonal_naive | 70.38 | 117.08 | 0.6620 | 59.54% | 43.16% |
| last_hour | 76.13 | 118.90 | 0.6514 | 56.31% | 29.62% |

## Coverage

There are 2160 hourly positions, 2120 observed
targets and 40 absent target hours. We scored 2076
hours (97.92% of observed targets), shared by every comparison.
Of observed targets, 5 lack previous-hour demand;
another 39 lack previous-week demand.
These exclusion counts do not overlap. Missing demand is never filled with zero.

## Interpretation and limits

MAE/RMSE are rentals per hour; tolerance percentages are not classification accuracy. These
metrics summarize the whole test period, unlike the earlier mean-of-fold validation scores.
Relative tolerance excludes zero-demand hours. Error tables cover hour, weekday and actual-demand
bands using only development-target thresholds (42.00, 279.00); band membership is a
retrospective diagnostic, not a future input.

This is rolling one-hour-ahead prediction. Earlier observed test counts are available as history
for later targets. The fitted parameters stay fixed. This is not a 90-day forecast made in October.
The first-week plot is selected by date; the scatter plot covers every scored test hour.

This holdout is now used. Report its results as observed; do not keep tuning against it and then
claim it is still an untouched test. Future modelling changes need a separate evaluation strategy.
Historical single-city data, immediate count availability, missing-hour coverage and timezone-naive
timestamps still limit generalization. The baseline rows are simple prediction rules, not additional
trained models. The saved HGB pipeline was not changed by this evaluation.
