# First model comparison: fixed settings

This is an initial development experiment, not a final test evaluation. No GridSearchCV or other hyperparameter search was performed. This is a historical record: alternative-model training has been removed from the active single-model workflow. See `model/README.md` for the current commands. Exact settings, library versions, dataset checksum, boundaries, fold metrics and validation predictions are recorded in `outputs/experiments/initial_fixed_settings/`.

## Validation

Three expanding training windows precede validation blocks 2012-07-11–2012-08-07, 2012-08-08–2012-09-04 and 2012-09-05–2012-10-02. Each block has 672 eligible observed hours. Every algorithm is scored on those same hours. Preprocessing is fitted within each training window.

The model is fitted once per fold. Predictions roll forward one hour at a time in their information assumptions: earlier actual validation counts are available as history for later targets. This is not a single 28-day forecast made before the validation block starts. Updating historical inputs does not mean retraining model parameters every hour.

## Results

The table gives arithmetic means of the three fold scores, not pooled metrics. Smaller MAE/RMSE is better; larger R² is better. MAE is the selection metric. Predictions are clipped to zero without rounding.

| Model | Mean MAE | Mean RMSE | Mean R² |
| --- | ---: | ---: | ---: |
| Histogram gradient boosting | 32.07 | 50.46 | 0.9536 |
| Random Forest | 34.03 | 55.43 | 0.9441 |
| Ridge | 47.83 | 70.80 | 0.9085 |
| Same hour previous week | 55.97 | 98.68 | 0.8226 |
| Last observed hour | 97.57 | 142.29 | 0.6298 |

Histogram gradient boosting is the provisional learned-model choice. Its fold MAEs are 30.70, 28.35 and 37.17. The recent validation advantage does not establish superiority in every season or in production, and no statistical-significance claim is made.

The nonlinear tree models outperform this additive Ridge configuration. A plausible explanation is that they capture interactions between hour, working-day context and recent demand; this has not been isolated through ablation experiments. Ridge remains a useful interpretable reference model.

## Error analysis and limitations

For gradient boosting, MAE at 18:00 is 70.93, versus 3.73 at 04:00, with 84 scored observations per hour. Higher-demand commute periods merit more scrutiny than the overall MAE alone suggests. Hour and weekday error tables are saved with the experiment. Demand-band analysis and wider seasonal validation remain later work.

The validation blocks cover July through early October 2012, rather than every season. Missing recent or weekly history reduces eligible coverage in general; these validation blocks happen to have full coverage. The dataset is an older aggregate of one system and cannot establish current demand or generalize automatically to another city. Holidays are assumed known and counts are assumed available immediately when each hour closes. Weather is excluded.

`outputs/models/development_pipeline.joblib` contains the best learned pipeline refitted on eligible pre-test data. It accepts the engineered feature columns recorded in metadata; raw-history feature creation and nonnegative clipping remain the caller's responsibility. This is a development artifact, not a deployed API.

The final 90-day test remains unscored. Before final evaluation, review feature choices and validation coverage. Hyperparameter tuning, if requested later, must stay inside development data. The frontend, API, Docker and server deployment are outside this modelling stage.
