import numpy as np
import pandas as pd
import pytest

from bike_demand.features import build_features
from bike_demand.data import load_hourly


def sample_hourly():
    index = pd.date_range("2011-01-01", periods=400, freq="h", name="target_timestamp")
    return pd.DataFrame({"cnt": np.arange(400, dtype=float), "holiday": 0, "workingday": 1}, index=index)


def test_target_and_future_demand_cannot_change_prediction_features():
    hourly = sample_hourly()
    origin = hourly.index[200]
    original = build_features(hourly)
    hourly.loc[origin:, "cnt"] = 999999
    changed = build_features(hourly)
    pd.testing.assert_frame_equal(original.loc[:origin], changed.loc[:origin])
    assert original.loc[origin, "demand_lag_1"] == 199
    assert original.loc[origin, "demand_lag_168"] == 32
    assert original.loc[origin, "demand_mean_24"] == np.mean(np.arange(176, 200))


def test_hourly_grid_keeps_missing_demand_at_elapsed_hour():
    hourly = sample_hourly()
    hourly.loc[hourly.index[199], "cnt"] = np.nan
    features = build_features(hourly)
    assert pd.isna(features.iloc[200]["demand_lag_1"])
    assert pd.isna(features.iloc[200]["demand_mean_24"])
    with pytest.raises(ValueError, match="hourly grid"):
        build_features(hourly.drop(hourly.index[199]))


def test_forbidden_columns_and_weather_are_ignored():
    hourly = sample_hourly()
    expected = build_features(hourly)
    for column in ["casual", "registered", "temp", "atemp", "hum", "windspeed", "weathersit"]:
        hourly[column] = 999999
    pd.testing.assert_frame_equal(expected, build_features(hourly))


def test_loader_reindexes_missing_hour_and_rejects_duplicates(tmp_path):
    path = tmp_path / "hour.csv"
    frame = pd.DataFrame({"dteday": ["2011-01-01"] * 2, "hr": [0, 2], "cnt": [4, 8], "casual": [1, 2], "registered": [3, 6]})
    frame.to_csv(path, index=False)
    hourly = load_hourly(path)
    assert len(hourly) == 3
    assert pd.isna(hourly.iloc[1]["cnt"])
    pd.concat([frame, frame.iloc[:1]]).to_csv(path, index=False)
    with pytest.raises(ValueError, match="Duplicate"):
        load_hourly(path)
