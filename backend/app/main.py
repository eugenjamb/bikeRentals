"""FastAPI application: prediction endpoints and the built portfolio frontend."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import settings
from .schemas import PredictionRequest, PredictionResponse
from .service import ForecastService


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.forecasts = ForecastService()
    yield
    del app.state.forecasts


app = FastAPI(
    title="Cyclecast · Bike Demand API",
    version="1.0.0",
    description="One-hour system-wide demand prediction with a frozen HGB pipeline.",
    root_path=settings.ROOT_PATH,
    lifespan=lifespan,
)


@app.get("/api/health")
def health(request: Request):
    return {"status": "ok", "model_version": request.app.state.forecasts.version}


@app.get("/api/study")
def project_study(request: Request):
    return request.app.state.forecasts.study


@app.get("/api/scenarios")
def scenarios(request: Request):
    return [
        {key: value for key, value in item.items() if key != "request"}
        for item in request.app.state.forecasts.scenarios
    ]


@app.get("/api/scenarios/{scenario_id}")
def scenario(scenario_id: str, request: Request):
    item = next((item for item in request.app.state.forecasts.scenarios if item["id"] == scenario_id), None)
    if item is None:
        raise HTTPException(status_code=404, detail="Historical scenario not found")
    return item


@app.post("/api/predict", response_model=PredictionResponse)
def predict(payload: PredictionRequest, request: Request):
    return request.app.state.forecasts.predict(payload)


@app.get("/api/figures/{filename}")
def figure(filename: str):
    allowed = {path.name for path in settings.FIGURE_DIR.glob("*.png")}
    if filename not in allowed:
        raise HTTPException(status_code=404, detail="Figure not found")
    return FileResponse(settings.FIGURE_DIR / filename, media_type="image/png")


if settings.FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=settings.FRONTEND_DIR, html=True), name="frontend")
