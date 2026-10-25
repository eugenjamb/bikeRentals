import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def hourly_data():
    """Deterministic hourly counts for leakage and elapsed-time checks."""
    index = pd.date_range("2011-01-01", periods=400, freq="h", name="target_timestamp")
    return pd.DataFrame({"cnt": np.arange(400, dtype=float), "holiday": 0, "workingday": 1}, index=index)
