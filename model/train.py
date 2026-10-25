"""Run initial fixed-setting models: python model/train.py."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from bike_demand.training import train_initial_models


if __name__ == "__main__":
    print(train_initial_models().to_string())
