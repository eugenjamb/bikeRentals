"""Shared paths and settings for the one-hour-ahead forecast workflow."""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "hour.csv"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

RANDOM_SEED = 42
# Keep the grid serial and bound native computation. Supplying joblib's CPU
# budget avoids its unavailable Windows physical-core discovery command.
CPU_THREADS = 2
os.environ.setdefault("LOKY_MAX_CPU_COUNT", str(CPU_THREADS))
TEST_PERIOD_DAYS = 90
DEMAND_LAGS_HOURS = (1, 2, 24, 48, 168)
ROLLING_WINDOWS_HOURS = (24, 168)
