"""Paths and deployment settings, separate from model-training configuration."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = Path(os.getenv("MODEL_PATH", ROOT / "outputs/models/tuned_forecast_pipeline.joblib"))
ASSET_DIR = Path(__file__).resolve().parent / "assets"
FIGURE_DIR = ROOT / "outputs/figures"
FRONTEND_DIR = ROOT / "frontend/dist"
ROOT_PATH = os.getenv("ROOT_PATH", "")
