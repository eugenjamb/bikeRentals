"""Initial experiment settings; feature rows use target timestamps."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "hour.csv"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

RANDOM_SEED = 42
FORECAST_HORIZON_HOURS = 1
TEST_PERIOD_DAYS = 90
DEMAND_LAGS_HOURS = (1, 2, 24, 48, 168)
ROLLING_WINDOWS_HOURS = (24, 168)
FORBIDDEN_PREDICTORS = frozenset({"cnt", "casual", "registered"})
