"""Download, validate the hourly timeline and construct development splits."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile

import pandas as pd

from .config import PROCESSED_DATA_DIR, RAW_DATA_PATH
from .forecast_pipeline import prepare_forecast_requests


def download_data():
    raw = RAW_DATA_PATH.parent
    raw.mkdir(parents=True, exist_ok=True)
    url = "https://archive.ics.uci.edu/static/public/275/bike+sharing+dataset.zip"
    archive = raw / "bike-sharing.zip"
    if not archive.exists():
        with urlopen(url, timeout=60) as response:
            archive.write_bytes(response.read())
    with ZipFile(archive) as source:
        for name in ("hour.csv", "day.csv", "Readme.txt"):
            matches = [item for item in source.namelist() if Path(item).name == name]
            if len(matches) != 1:
                raise ValueError(f"Expected one archive member named {name}")
            (raw / name).write_bytes(source.read(matches[0]))
    provenance = raw / "provenance.json"
    if not provenance.exists():
        provenance.write_text(json.dumps({
            "download_url": url,
            "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
            "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
            "dataset_doi": "10.24432/C5W894",
            "attribution": "Fanaee-T, Hadi. Bike Sharing. UCI Machine Learning Repository.",
            "license": "CC BY 4.0",
        }, indent=2) + "\n", encoding="utf-8")
    print(f"Dataset available at {raw}")



def load_hourly(path):
    frame = pd.read_csv(path)
    timestamps = pd.to_datetime(frame["dteday"]) + pd.to_timedelta(frame["hr"], unit="h")
    if timestamps.duplicated().any():
        raise ValueError("Duplicate hourly timestamps need investigation")
    frame.index = pd.DatetimeIndex(timestamps, name="target_timestamp")
    frame = frame.sort_index()
    if frame["cnt"].isna().any() or (frame["cnt"] < 0).any():
        raise ValueError("Observed demand must be present and nonnegative")
    if not (frame["casual"] + frame["registered"]).equals(frame["cnt"]):
        raise ValueError("Target component totals do not match cnt")
    grid = pd.date_range(frame.index.min(), frame.index.max(), freq="h", name=frame.index.name)
    return frame.reindex(grid)


def prepare_development():
    """Derive folds directly from the frozen split, without old-model artifacts."""
    split = json.loads((PROCESSED_DATA_DIR / "split.json").read_text())
    test_start = pd.Timestamp(split["test_start_inclusive"])
    development = load_hourly(RAW_DATA_PATH).loc[lambda frame: frame.index < test_start]
    requests = prepare_forecast_requests(development)
    # Fixed eligibility preserves the weekly-reference comparison from early experiments.
    eligible = development["cnt"].notna() & development["cnt"].shift(1).notna() & development["cnt"].shift(168).notna()
    eligible &= requests.index >= requests.index.min() + pd.Timedelta(hours=168)
    requests = requests.loc[eligible]
    target = development.loc[eligible, "cnt"]
    folds = []
    for number in range(3):
        start = test_start - pd.Timedelta(days=28 * (3 - number))
        end = start + pd.Timedelta(days=28)
        train_index = requests.index[requests.index < start]
        valid_index = requests.index[(requests.index >= start) & (requests.index < end)]
        if train_index.empty or valid_index.empty:
            raise ValueError("Insufficient development data for three chronological folds")
        folds.append({
            "fold": number + 1,
            "train_start": str(train_index.min()),
            "train_end": str(train_index.max()),
            "validation_start": str(start),
            "validation_end_exclusive": str(end),
            "training_rows": len(train_index),
            "eligible_validation_rows": len(valid_index),
            "observed_validation_rows": int(development.loc[(development.index >= start) & (development.index < end), "cnt"].notna().sum()),
        })
    return requests, target, split, folds
