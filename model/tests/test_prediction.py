import joblib
import numpy as np

from sklearn.linear_model import Ridge

from bike_demand.features import build_features
from bike_demand.training import make_pipeline
from test_features import sample_hourly


def test_pipeline_predicts_unseen_hour_and_survives_save(tmp_path):
    hourly = sample_hourly()
    features = build_features(hourly)
    pipeline = make_pipeline(Ridge(), features.columns)
    pipeline.fit(features.iloc[168:300], hourly["cnt"].iloc[168:300])
    request = features.iloc[[300]].copy()
    request["month"] = 12  # category unseen during training
    predicted = pipeline.predict(request)
    assert predicted.shape == (1,)
    assert np.isfinite(predicted).all()
    path = tmp_path / "pipeline.joblib"
    joblib.dump(pipeline, path)
    np.testing.assert_allclose(joblib.load(path).predict(request), predicted)
