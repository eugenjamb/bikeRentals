import joblib
import numpy as np
import pandas as pd
import pytest
from sklearn.base import clone
from sklearn.model_selection import GridSearchCV
from threadpoolctl import threadpool_limits

from bike_demand.forecast_pipeline import (
    DemandFeatureTransformer,
    ForecastFeatureSelector,
    make_forecast_pipeline,
    make_forecast_request,
    prepare_forecast_requests,
)


def test_lags_and_rolling_windows_use_elapsed_hours_and_exclude_target(hourly_data):
    hourly_data.loc[hourly_data.index[180], "cnt"] = np.nan
    requests = prepare_forecast_requests(hourly_data).iloc[[200, 360]]
    features = DemandFeatureTransformer().fit_transform(requests)
    assert features.iloc[0].demand_lag_1 == 199
    assert features.iloc[0].demand_lag_168 == 32
    assert pd.isna(features.iloc[0].demand_mean_24)
    assert features.iloc[1].demand_mean_24 == np.mean(np.arange(336, 360))
    assert np.isclose(features.iloc[1].demand_std_24, np.std(np.arange(336, 360), ddof=1))


def test_future_and_target_mutation_cannot_change_request_or_features(hourly_data):
    hourly = hourly_data.copy()
    timestamp = hourly.index[200]
    original_requests = prepare_forecast_requests(hourly).loc[[timestamp]]
    hourly.loc[timestamp:, "cnt"] = 999999
    changed_requests = prepare_forecast_requests(hourly).loc[[timestamp]]
    np.testing.assert_array_equal(original_requests.iloc[0].demand_history, changed_requests.iloc[0].demand_history)
    transformer = DemandFeatureTransformer().fit(original_requests)
    pd.testing.assert_frame_equal(transformer.transform(original_requests), transformer.transform(changed_requests))
    assert original_requests.iloc[0].demand_history[-1] == 199
    assert original_requests.iloc[0].demand_history[0] == 32


def test_single_forecast_matches_batch_and_rejects_future_observations(hourly_data):
    hourly = hourly_data.copy()
    target = hourly.index[300]
    single = make_forecast_request(hourly["cnt"].loc[hourly.index < target], target, holiday=0, workingday=1)
    batch = prepare_forecast_requests(hourly).loc[[target]]
    transformer = DemandFeatureTransformer().fit(batch)
    pd.testing.assert_frame_equal(transformer.transform(single), transformer.transform(batch))
    with pytest.raises(ValueError, match="future observations"):
        make_forecast_request(hourly["cnt"], target, holiday=0, workingday=1)
    with pytest.raises(ValueError, match="last completed"):
        make_forecast_request(hourly["cnt"].loc[hourly.index < target - pd.Timedelta(hours=1)], target, holiday=0, workingday=1)


def test_target_columns_are_rejected_and_selection_removes_only_rolling_statistics(hourly_data):
    requests = prepare_forecast_requests(hourly_data.copy()).iloc[168:]
    with pytest.raises(ValueError, match="forbidden"):
        DemandFeatureTransformer().fit(requests.assign(cnt=1))
    features = DemandFeatureTransformer().fit_transform(requests)
    selected = ForecastFeatureSelector("calendar_and_lags").fit_transform(features)
    assert "demand_lag_168" in selected
    assert "workingday" in selected
    assert "demand_mean_24" not in selected
    assert selected.shape[1] == features.shape[1] - 4


def test_complete_pipeline_grid_search_and_saved_single_hour_prediction(tmp_path, hourly_data):
    hourly = hourly_data.copy()
    requests = prepare_forecast_requests(hourly).iloc[168:]
    target = hourly["cnt"].iloc[168:]
    pipeline = make_forecast_pipeline()
    assert list(clone(pipeline).named_steps) == ["features", "select", "preprocess", "regressor"]
    splits = [(np.arange(100), np.arange(100, 130)), (np.arange(130), np.arange(130, 160))]
    search = GridSearchCV(pipeline, {"select__feature_set": ["calendar_and_history", "calendar_and_lags"], "regressor__max_iter": [5]}, cv=splits, scoring="neg_mean_absolute_error", error_score="raise")
    with threadpool_limits(limits=2):
        search.fit(requests, target)
        saved_path = tmp_path / "forecast.joblib"
        joblib.dump(search.best_estimator_, saved_path)
        next_hour = hourly.index[-1] + pd.Timedelta(hours=1)
        request = make_forecast_request(hourly["cnt"], next_hour, holiday=0, workingday=1)
        predictions = joblib.load(saved_path).predict(request)
        assert predictions.shape == (1,)
        assert np.isfinite(predictions).all() and (predictions >= 0).all()
        np.testing.assert_allclose(predictions, search.best_estimator_.predict(request))
