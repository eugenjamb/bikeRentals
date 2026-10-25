"""Train the complete HGB pipeline with chronological grid search."""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bike_demand.training import train_model


if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stdout,
    )
    try:
        train_model()
    except KeyboardInterrupt:
        logging.getLogger(__name__).warning("Training interrupted by user.")
        sys.exit(130)
