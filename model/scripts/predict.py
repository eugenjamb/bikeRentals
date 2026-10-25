"""Predict one hour from a CSV containing timestamp,cnt history columns."""

import argparse
import json
import sys
from pathlib import Path

import joblib
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bike_demand.config import OUTPUT_DIR
from bike_demand.forecast_pipeline import make_forecast_request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--history", type=Path, required=True, help="CSV with timestamp,cnt; include only observations before target")
    parser.add_argument("--target", required=True, help="Target hour, e.g. 2012-10-03T00:00:00")
    parser.add_argument("--holiday", type=int, choices=[0, 1], required=True)
    parser.add_argument("--workingday", type=int, choices=[0, 1], required=True)
    parser.add_argument("--model", type=Path, default=OUTPUT_DIR / "models" / "tuned_forecast_pipeline.joblib")
    args = parser.parse_args()
    history = pd.read_csv(args.history, parse_dates=["timestamp"]).set_index("timestamp")["cnt"]
    request = make_forecast_request(history, args.target, holiday=args.holiday, workingday=args.workingday)
    pipeline = joblib.load(args.model)
    predicted = float(pipeline.predict(request)[0])
    print(json.dumps({"target_timestamp": str(request.index[0]), "predicted_rentals": predicted}, indent=2))


if __name__ == "__main__":
    main()
