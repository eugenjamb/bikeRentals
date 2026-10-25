import numpy as np
import pandas as pd
import pytest
from threadpoolctl import threadpool_limits

from bike_demand.forecast_pipeline import make_forecast_pipeline, prepare_forecast_requests
from bike_demand.analysis.learning import iteration_errors
from bike_demand.training import expanding_splits


def test_learning_curve_final_stage_matches_pipeline_predictions(hourly_data):
    hourly = hourly_data.copy()
    requests = prepare_forecast_requests(hourly).iloc[168:]
    target = hourly["cnt"].iloc[168:]
    train, valid = np.arange(100), np.arange(100, 130)
    pipeline = make_forecast_pipeline().set_params(regressor__max_iter=5)
    with threadpool_limits(limits=2):
        progress = iteration_errors(pipeline, requests, target, [(train, valid)])
        pipeline.fit(requests.iloc[train], target.iloc[train])
        expected_mae = np.abs(pipeline.predict(requests.iloc[valid]) - target.iloc[valid]).mean()
    assert progress.iteration.tolist() == [1, 2, 3, 4, 5]
    assert np.isclose(progress.iloc[-1].validation_mae, expected_mae)


def test_calendar_folds_preserve_expanding_order_and_reject_holdout():
    index = pd.date_range("2012-01-01", periods=100, freq="h")
    fold = {"validation_start": str(index[60]), "validation_end_exclusive": str(index[80]), "training_rows": 60, "eligible_validation_rows": 20}
    train, valid = expanding_splits(index, [fold], index[90])[0]
    assert index[train].max() < index[valid].min()
    with pytest.raises(ValueError, match="held-out"):
        expanding_splits(index, [fold], index[70])
