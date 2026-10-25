"""Load the model once and reuse its exact feature pipeline for every request."""

import hashlib
import json
import sys
from threading import Lock
from time import perf_counter

import joblib
import pandas as pd
from threadpoolctl import threadpool_limits

from . import settings
from .schemas import PredictionRequest, PredictionResponse

sys.path.insert(0, str(settings.ROOT / "model/src"))

from bike_demand.forecast_pipeline import make_forecast_request


class ForecastService:
    def __init__(self):
        self.model = joblib.load(settings.MODEL_PATH)
        self.version = hashlib.sha256(settings.MODEL_PATH.read_bytes()).hexdigest()[:12]
        self.study = json.loads((settings.ASSET_DIR / "study.json").read_text(encoding="utf-8"))
        self.scenarios = json.loads((settings.ASSET_DIR / "scenarios.json").read_text(encoding="utf-8"))
        if self.study["model_hash"] != self.version:
            raise ValueError("Showcase assets do not match the model; run backend/scripts/export_content.py")
        self.lock = Lock()

    def predict(self, payload: PredictionRequest) -> PredictionResponse:
        started = perf_counter()
        history = pd.Series(
            [entry.count for entry in payload.history],
            index=pd.DatetimeIndex([entry.timestamp for entry in payload.history]),
            dtype=float,
        )
        request = make_forecast_request(
            history,
            payload.target_timestamp,
            holiday=int(payload.holiday),
            workingday=int(payload.workingday),
        )
        # Serialize short CPU-bound predictions and cap native threads on the VPS.
        with self.lock, threadpool_limits(limits=1):
            predicted = float(self.model.predict(request)[0])
        return PredictionResponse(
            target_timestamp=payload.target_timestamp,
            predicted_rentals=predicted,
            display_rentals=round(predicted),
            elapsed_ms=round((perf_counter() - started) * 1000, 2),
            model_version=self.version,
        )
