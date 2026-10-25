"""Validate the one-hour prediction contract at the API boundary."""

from datetime import datetime, timedelta
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

Count = Annotated[float, Field(ge=0, le=100_000, allow_inf_nan=False)]


class Observation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timestamp: datetime
    count: Count | None


class PredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_timestamp: datetime
    holiday: bool
    workingday: bool
    history: list[Observation] = Field(min_length=168, max_length=168)

    @model_validator(mode="after")
    def validate_hourly_history(self):
        target = self.target_timestamp
        if not 2011 <= target.year <= 2100:
            raise ValueError("Target year must be between 2011 and 2100")
        if target.tzinfo is not None or any((target.minute, target.second, target.microsecond)):
            raise ValueError("Use a timezone-naive target at an hour boundary, matching source labels")
        for position, observation in enumerate(self.history):
            expected = target - timedelta(hours=168 - position)
            if observation.timestamp != expected or observation.timestamp.tzinfo is not None:
                raise ValueError("History must contain the 168 preceding hours in order; target/future hours are forbidden")
        if self.history[-1].count is None:
            raise ValueError("The most recent completed hour must have an observed count")
        expected_workingday = target.weekday() < 5 and not self.holiday
        if self.workingday != expected_workingday:
            raise ValueError("Working-day flag must agree with weekday and holiday")
        return self


class PredictionResponse(BaseModel):
    target_timestamp: datetime
    predicted_rentals: float
    display_rentals: int
    elapsed_ms: float
    model_version: str
    horizon_hours: int = 1
    scope: str = "system-wide hourly demand"
