"""Utide adapter module."""

from tidepredictor.adapters import TidePredictorAdapter, PredictionType

from datetime import datetime, timedelta

import polars as pl
# import utide


class UtideAdapter(TidePredictorAdapter):
    """Adapter for the utide tide predictor engine.

    Parameters
    ----------
    consituents : Any
        The constituents to use for the prediction.
    type : PredictionType
        The type of prediction to make.
    """

    def __init__(self, consituents, type: PredictionType) -> None:
        self._consituents = consituents
        self._type = type

        # TODO convert constituents to utide format

    def predict(
        self, start: datetime, end: datetime, interval: timedelta = timedelta(hours=1)
    ) -> pl.DataFrame:
        """Predict tide levels or currents using utide."""
        # res = utide.reconstruct(t=, coef= , epoch=, constit=)
        # TODO convert utide.Bunch to polars.DataFrame

        df = pl.DataFrame().with_columns(
            pl.datetime_range(start, end, interval=interval).alias("time"),
        )

        match self._type:
            case PredictionType.level:
                df = df.with_columns(
                    pl.zeros(pl.col("time").len()).alias("level"),
                )
            case PredictionType.current:
                df = df.with_columns(
                    pl.zeros(pl.col("time").len()).alias("u"),
                    pl.zeros(pl.col("time").len()).alias("v"),
                )

        return df
