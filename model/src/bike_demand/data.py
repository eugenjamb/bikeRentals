"""Load hourly data without silently treating absent observations as zero."""

import pandas as pd


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
