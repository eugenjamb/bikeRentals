# Histogram gradient boosting: grid-search summary

Development-only search: 32 configurations x 3 expanding folds.
Selection metric: mean validation MAE. Final-test evaluation is a separate command.

Selected parameters:
```json
{
  "regressor__l2_regularization": 1.0,
  "regressor__learning_rate": 0.1,
  "regressor__max_iter": 200,
  "regressor__max_leaf_nodes": 31,
  "select__feature_set": "calendar_and_history"
}
```

Mean fold metrics (MAE, RMSE, R2):
```text
                                   mae       rmse        r2
configuration                                              
selected_grid_configuration  31.603292  50.083177  0.954302
untuned_full_features        32.069645  50.461044  0.953645
```

Complete fitted pipeline: `outputs/models/tuned_forecast_pipeline.joblib`.
All candidates and fold scores are saved beside metadata in `outputs/experiments/hgb_grid_search/`.
See `model/README.md` for the pipeline contract and interview walkthrough.
