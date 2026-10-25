"""Download the data, freeze the split and generate EDA figures."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bike_demand.data import download_data
from bike_demand.analysis.eda import run_eda


if __name__ == "__main__":
    download_data()
    print(json.dumps(run_eda(), indent=2))
