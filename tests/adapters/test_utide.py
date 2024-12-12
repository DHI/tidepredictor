from datetime import datetime, timedelta

import polars as pl
from tidepredictor.adapters import PredictionType, UtideAdapter


def test_utide_returns_dataframe_with_levels() -> None:
    # TODO figure out format of constituents
    predictor = UtideAdapter(consituents=None, type=PredictionType.level)

    df = predictor.predict(
        start=datetime(2024, 1, 1),
        end=datetime(2024, 1, 2),
        interval=timedelta(hours=1),
    )
    assert isinstance(df, pl.DataFrame)
    assert "level" in df.columns


def test_utide_returns_dataframe_with_currents() -> None:
    # TODO figure out format of constituents
    predictor = UtideAdapter(consituents=None, type=PredictionType.current)

    df = predictor.predict(
        start=datetime(2024, 1, 1),
        end=datetime(2024, 1, 2),
        interval=timedelta(hours=1),
    )
    assert isinstance(df, pl.DataFrame)
    assert "u" in df.columns
    assert "v" in df.columns
