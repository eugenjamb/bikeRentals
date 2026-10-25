import numpy as np
import pandas as pd
import pytest

from bike_demand.evaluation import closeness_metrics, evaluate_holdout
from bike_demand.analysis.diagnostics import validate_predictions


def test_tolerances_are_inclusive_and_wape_is_not_accuracy():
    result = closeness_metrics([100, 200, 0], [120, 250, 0])
    assert result["within_20_rentals_pct"] == pytest.approx(200 / 3)
    assert result["within_50_rentals_pct"] == 100
    assert result["within_20_percent_pct"] == 50
    assert result["relative_tolerance_rows"] == 2
    assert result["relative_tolerance_excluded_zero_rows"] == 1
    assert result["wape_pct"] == pytest.approx(100 * 70 / 300)
    assert result["mean_signed_error"] == pytest.approx(70 / 3)


def test_zero_demand_relative_metrics_are_undefined():
    result = closeness_metrics([0, 0], [0, 10])
    assert result["wape_pct"] is None
    assert result["within_20_percent_pct"] is None


@pytest.mark.parametrize("actual,predicted", [([], []), ([1], [1, 2]), ([1], [np.nan]), ([-1], [0])])
def test_invalid_metric_inputs_are_rejected(actual, predicted):
    with pytest.raises(ValueError):
        closeness_metrics(actual, predicted)


def test_diagnostics_refuses_final_test_predictions():
    metadata = {"test_split": {"test_start_inclusive": "2012-10-03"}}
    predictions = pd.DataFrame({"target_timestamp": pd.to_datetime(["2012-10-03"])})
    with pytest.raises(ValueError, match="pre-test"):
        validate_predictions(predictions, metadata)


class PredictionOnlyModel:
    """Any attempt to refit this evaluation model must fail."""

    def fit(self, *args, **kwargs):
        raise AssertionError("Final evaluation must never fit")

    def predict(self, requests):
        return np.asarray([history[-1] for history in requests.demand_history])


def test_holdout_only_predicts_and_preserves_pretest_history(hourly_data):
    hourly = hourly_data.copy()
    start, end = hourly.index[300], hourly.index[320]
    predictions, coverage = evaluate_holdout(PredictionOnlyModel(), hourly, start, end)
    assert coverage["scored_hours"] == 20
    assert predictions.index.min() == start
    assert predictions.index.max() < end
    assert predictions.iloc[0].hist_gradient_boosting == 299
    assert predictions.iloc[1].hist_gradient_boosting == 300
    assert predictions.iloc[0].seasonal_naive == 132


def test_test_coverage_exclusions_are_disjoint_and_unknown_counts_stay_missing(hourly_data):
    hourly = hourly_data.copy()
    hourly.loc[hourly.index[300], "cnt"] = np.nan
    hourly.loc[hourly.index[135], "cnt"] = np.nan  # lag 168 missing at target 303
    predictions, coverage = evaluate_holdout(PredictionOnlyModel(), hourly, hourly.index[300], hourly.index[310])
    assert coverage["expected_hours"] == 10
    assert coverage["observed_target_hours"] == 9
    assert coverage["missing_target_hours"] == 1
    assert coverage["observed_hours_excluded_missing_previous_hour"] == 1
    assert coverage["additional_hours_excluded_missing_previous_week"] == 1
    assert coverage["scored_hours"] == 7
    assert not predictions.index.isin(hourly.index[[300, 301, 303]]).any()
