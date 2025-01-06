from dataclasses import asdict
from datetime import datetime, timedelta
from pathlib import Path

# from tidepredictor.utide import Coef


import mikeio
import pandas as pd
import polars as pl
from utide import reconstruct
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


def test_utide_vs_mike_precalculated():
    ds = mikeio.read("data/MIKE/tide_elevation.dfs0")
    item = "Level (0,0)"
    mdf = pl.from_pandas(ds[item].to_dataframe().reset_index()).rename(
        {"index": "time", item: "mike"}
    )

    lat = 0.0
    lon = 0.0
    # TODO use re-organized datafile
    coef = UtideAdapter.coef(
        fp=Path("tests/data/GlobalTideElevation_DTU-TPXO8_2min_v1_UpperCase_test.nc"),
        lon=lon,
        lat=lat,
    )
    t = pd.date_range(start=ds.time[0], end=ds.time[1], freq="1h")
    tide = reconstruct(t, asdict(coef))
    udf = pl.DataFrame({"time": t, "utide": tide["h"]})

    both = udf.join(mdf, on="time")

    diff = both["utide"] - both["mike"]
    assert diff.abs().max() < 0.05
