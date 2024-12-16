from datetime import datetime, timedelta

from typing import Protocol
import polars as pl

from enum import Enum


class PredictionType(str, Enum):
    level = "level"
    current = "current"


class TidePredictorAdapter(Protocol):
    """Adapter for different tide predictor engines."""

    # TODO figure out format of constituents
    def __init__(self, consituents, type: PredictionType) -> None: ...

    def predict(
        self, start: datetime, end: datetime, freq: timedelta = timedelta(hours=1)
    ) -> pl.DataFrame: ...
