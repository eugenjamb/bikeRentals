"""Evaluate saved predictions or the frozen model; never fit or tune."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bike_demand.analysis.diagnostics import run_diagnostics
from bike_demand.evaluation import run_test_evaluation


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", choices=["validation", "test"], required=True)
    args = parser.parse_args()
    scores = run_test_evaluation() if args.split == "test" else run_diagnostics()
    print(scores.round(3).to_string())
