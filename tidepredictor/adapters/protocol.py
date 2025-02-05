from datetime import datetime, timedelta

from typing import Protocol
import polars as pl

from enum import Enum

from tidepredictor.data import ConstituentRepository


class PredictionType(str, Enum):
    level = "level"
    current = "current"


class TidePredictorAdapter(Protocol):
    """Adapter for different tide predictor engines."""

    def __init__(
        self, consituent_repo: ConstituentRepository, type: PredictionType
    ) -> None: ...

    def predict(
        self,
        lon: float,
        lat: float,
        start: datetime,
        end: datetime,
        freq: timedelta = timedelta(hours=1),
    ) -> pl.DataFrame: ...
