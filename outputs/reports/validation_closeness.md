# How close are the selected model's predictions?

Model: **tuned Histogram Gradient Boosting**. Source: 2016 saved out-of-fold
predictions over three chronological validation folds. Final-test results are recorded separately in final_test_report.md.
These folds were used for model selection, so the scores are not an independent final estimate.
No new hyperparameters are selected by this diagnostics command.

- Average absolute error: **31.60 rentals/hour**.
- Within +/-20 rentals: **52.28%**.
- Within +/-50 rentals: **80.46%**.
- Within +/-20% of actual demand: **74.55%** on positive-demand hours.
- WAPE: **10.85%** (sum of absolute errors / sum of actual rentals).
- 90th percentile absolute error: **76.05 rentals**.
- Mean signed error (predicted minus actual): **-6.88 rentals**.

Tolerance conditions are separate illustrative thresholds, not classification accuracy.
Relative tolerance excludes 0 zero-demand hours.
WAPE is not a percentage of correct predictions. Signed errors can cancel.

## Actual prediction examples

These are the first 24 validation hours, selected by date rather than performance.
Each prediction is made by a model trained only before that validation block; later observations
within the block supply history for later one-hour-ahead predictions. This is not a 24-hour
forecast issued at midnight.

| Target hour | Actual rentals | Predicted rentals | Absolute error |
| --- | ---: | ---: | ---: |
| 2012-07-11 00:00:00 | 44 | 84.79 | 40.79 |
| 2012-07-11 01:00:00 | 14 | 58.81 | 44.81 |
| 2012-07-11 02:00:00 | 5 | 37.10 | 32.10 |
| 2012-07-11 03:00:00 | 5 | 18.77 | 13.77 |
| 2012-07-11 04:00:00 | 7 | 21.64 | 14.64 |
| 2012-07-11 05:00:00 | 41 | 32.84 | 8.16 |
| 2012-07-11 06:00:00 | 185 | 137.65 | 47.35 |
| 2012-07-11 07:00:00 | 497 | 416.71 | 80.29 |
| 2012-07-11 08:00:00 | 674 | 531.95 | 142.05 |
| 2012-07-11 09:00:00 | 328 | 324.55 | 3.45 |
| 2012-07-11 10:00:00 | 195 | 309.01 | 114.01 |
| 2012-07-11 11:00:00 | 229 | 235.44 | 6.44 |
| 2012-07-11 12:00:00 | 292 | 294.07 | 2.07 |
| 2012-07-11 13:00:00 | 273 | 339.59 | 66.59 |
| 2012-07-11 14:00:00 | 241 | 280.84 | 39.84 |
| 2012-07-11 15:00:00 | 276 | 298.70 | 22.70 |
| 2012-07-11 16:00:00 | 411 | 423.10 | 12.10 |
| 2012-07-11 17:00:00 | 830 | 756.84 | 73.16 |
| 2012-07-11 18:00:00 | 814 | 819.46 | 5.46 |
| 2012-07-11 19:00:00 | 633 | 579.91 | 53.09 |
| 2012-07-11 20:00:00 | 483 | 533.58 | 50.58 |
| 2012-07-11 21:00:00 | 391 | 448.02 | 57.02 |
| 2012-07-11 22:00:00 | 244 | 329.75 | 85.75 |
| 2012-07-11 23:00:00 | 152 | 150.59 | 1.41 |

The first-week time plot uses the same date-based selection. All 2,016 validation hours appear
in the scatter/error-coverage plots. In the scatter plot, points on the diagonal are perfect;
points below it are underpredictions. Look at the largest-error CSV alongside these averages.

Hour, weekday and demand-band errors are saved in `outputs/experiments/hgb_grid_search/`.
Demand bands use each fold's training-demand 25th and 75th percentiles, not validation quantiles;
the thresholds are recorded separately. Actual demand bands are retrospective diagnostics,
not input features available at forecast origin.

Keep the recorded final test separate from feature and parameter selection.
