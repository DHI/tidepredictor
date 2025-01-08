from datetime import datetime, timedelta
from pathlib import Path

import mikeio
import polars as pl
from tidepredictor.adapters import PredictionType, UtideAdapter


def test_utide_returns_dataframe_with_levels() -> None:
    predictor = UtideAdapter(
        consituents=Path("tests/data/elevation.nc"),
        type=PredictionType.level,
    )

    df = predictor.predict(
        lon=0.0,
        lat=0.0,
        start=datetime(2024, 1, 1),
        end=datetime(2024, 1, 2),
        interval=timedelta(hours=1),
    )
    assert isinstance(df, pl.DataFrame)
    assert "level" in df.columns
    assert df["level"].max() > 0
    assert df["level"].min() < 0


def test_utide_returns_dataframe_with_currents() -> None:
    # TODO figure out format of constituents
    predictor = UtideAdapter(
        consituents=Path("tests/data/GlobalTideCurrent_DTU-TPXO8_2min_v1_test.nc"),
        type=PredictionType.current,
    )

    df = predictor.predict(
        lat=0.0,
        lon=0.0,
        start=datetime(2024, 1, 1),
        end=datetime(2024, 1, 2),
        interval=timedelta(hours=1),
    )
    assert isinstance(df, pl.DataFrame)
    assert "u" in df.columns
    assert "v" in df.columns


def test_utide_vs_mike_precalculated():
    ds = mikeio.read("tests/data/tide_elevation.dfs0")
    item = "Level (0,0)"
    mdf = pl.from_pandas(ds[item].to_dataframe().reset_index()).rename(
        {"index": "time", item: "mike"}
    )

    # TODO checks all locations in the file
    lat = 0.0
    lon = 0.0
    predictor = UtideAdapter(
        consituents=Path("tests/data/elevation.nc"),
        type=PredictionType.level,
    )

    udf = predictor.predict(
        lon=lon,
        lat=lat,
        start=ds.time[0].to_pydatetime(),
        end=ds.time[-1].to_pydatetime(),
        interval=timedelta(hours=1),
    ).rename({"level": "utide"})

    both = udf.join(mdf, on="time")

    diff = both["utide"] - both["mike"]
    assert diff.abs().max() < 0.08
