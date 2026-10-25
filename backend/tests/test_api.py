import copy

import numpy as np
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def scenario(client):
    return client.get("/api/scenarios/morning").json()


def test_health_and_recorded_results(client):
    assert client.get("/api/health").json()["status"] == "ok"
    study = client.get("/api/study").json()
    assert study["coverage"]["scored_hours"] == 2076
    assert study["final"][0]["mae"] == pytest.approx(27.124222625147464)
    assert len(study["heatmap"]) == 168


def test_prediction_uses_same_saved_pipeline_and_historical_replay(client):
    item = scenario(client)
    response = client.post("/api/predict", json=item["request"])
    assert response.status_code == 200
    output = response.json()
    assert np.isfinite(output["predicted_rentals"]) and output["predicted_rentals"] >= 0
    assert output["horizon_hours"] == 1
    assert output["target_timestamp"] == item["request"]["target_timestamp"]
    # The example lies in the final holdout; its actual count never enters the request.
    assert "actual" not in item["request"]
    assert all(row["timestamp"] < item["request"]["target_timestamp"] for row in item["request"]["history"])


@pytest.mark.parametrize("mutation", ["future", "negative", "missing_recent", "short", "target_component", "timezone", "wrong_calendar"])
def test_invalid_or_leaking_requests_are_rejected(client, mutation):
    payload = copy.deepcopy(scenario(client)["request"])
    if mutation == "future":
        payload["history"][-1]["timestamp"] = payload["target_timestamp"]
    elif mutation == "negative":
        payload["history"][0]["count"] = -1
    elif mutation == "missing_recent":
        payload["history"][-1]["count"] = None
    elif mutation == "short":
        payload["history"].pop()
    elif mutation == "target_component":
        payload["registered"] = 100
    elif mutation == "timezone":
        payload["target_timestamp"] += "Z"
    elif mutation == "wrong_calendar":
        payload["workingday"] = False
    assert client.post("/api/predict", json=payload).status_code == 422


def test_all_demonstration_scenarios_predict(client):
    for item in client.get("/api/scenarios").json():
        payload = client.get(f"/api/scenarios/{item['id']}").json()["request"]
        assert client.post("/api/predict", json=payload).status_code == 200


def test_missing_scenario_and_private_files_are_not_exposed(client):
    assert client.get("/api/scenarios/not-found").status_code == 404
    assert client.get("/api/figures/not-a-figure.png").status_code == 404
    assert client.get("/outputs/models/tuned_forecast_pipeline.joblib").status_code == 404
