export interface Metric {
  model: string;
  mae: number;
  rmse: number;
  r2: number;
  within_50_rentals_pct: number;
  within_20_percent_pct: number;
}

export interface Study {
  model_hash: string;
  data: {
    observed_rows: number;
    missing_timestamps: number;
    development_observed_rows: number;
  };
  selection: Record<string, string | number>;
  validation: {
    configuration: string;
    mae: number;
    rmse: number;
    r2: number;
  }[];
  final: Metric[];
  coverage: {
    scored_hours: number;
    observed_target_hours: number;
    scored_fraction_of_observed: number;
  };
  heatmap: { weekday: number; hour: number; demand: number }[];
  initial_comparison: { model: string; mae: number }[];
  learning: {
    iteration: number;
    training_mae: number;
    validation_mae: number;
  }[];
  candidates: {
    rank_test_score: number;
    mean_validation_mae: number;
    param_regressor__learning_rate: number;
    param_regressor__max_iter: number;
    param_regressor__max_leaf_nodes: number;
    param_regressor__l2_regularization: number;
    param_select__feature_set: string;
  }[];
  hour_errors: { target_timestamp: number; mae: number }[];
}

export interface ForecastRequest {
  target_timestamp: string;
  holiday: boolean;
  workingday: boolean;
  history: { timestamp: string; count: number | null }[];
}

export interface Scenario {
  id: string;
  label: string;
  description: string;
  actual: number;
  request?: ForecastRequest;
}

export interface Forecast {
  target_timestamp: string;
  predicted_rentals: number;
  display_rentals: number;
  elapsed_ms: number;
  model_version: string;
}
