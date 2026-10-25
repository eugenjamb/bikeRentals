"""Run from the project root: python model/run_eda.py."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from bike_demand.eda import run_eda


if __name__ == "__main__":
    print(json.dumps(run_eda(), indent=2))
