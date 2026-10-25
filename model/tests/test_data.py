import pandas as pd
import pytest

from bike_demand.data import load_hourly
from bike_demand.forecast_pipeline import prepare_forecast_requests


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


def test_history_packaging_refuses_row_based_lags_across_a_gap(hourly_data):
    with pytest.raises(ValueError, match="complete sorted hourly grid"):
        prepare_forecast_requests(hourly_data.drop(hourly_data.index[199]))
