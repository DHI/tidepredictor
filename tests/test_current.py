from datetime import datetime, timedelta
from pathlib import Path

import mikeio
import polars as pl
from tidepredictor import (
    CurrentPredictor,
    NetCDFConstituentRepository,
)


def test_utide_returns_dataframe_with_current_profile() -> None:
    repo = NetCDFConstituentRepository(Path("tests/data/currents.nc"))
    predictor = CurrentPredictor(constituent_repo=repo)

    df = predictor.predict(
        lat=0.0,
        lon=0.0,
        start=datetime(2024, 1, 1),
        end=datetime(2024, 1, 2),
        interval=timedelta(hours=1),
    )

    assert isinstance(df, pl.DataFrame)
    assert df["u"].max() > 0
    assert df["u"].min() < 0
    assert df["v"].max() > 0
    assert df["v"].min() < 0


def test_utide_vs_mike_precalculated_currents():
    ds = mikeio.read("tests/data/tide_currents.dfs0")
    v_item = "Tidal current component (geographic North) (Current (0,0))"
    mdf = pl.from_pandas(ds[v_item].to_dataframe().reset_index()).rename(
        {"index": "time", v_item: "mike"}
    )

    # TODO checks all locations in the file
    lat = 0.0
    lon = 0.0
    repo = NetCDFConstituentRepository(Path("tests/data/currents.nc"))
    predictor = CurrentPredictor(
        constituent_repo=repo,
    )

    udf = predictor.predict(
        lon=lon,
        lat=lat,
        start=ds.time[0].to_pydatetime(),
        end=ds.time[-1].to_pydatetime(),
        interval=timedelta(hours=1),
    ).rename({"v": "utide"})

    both = udf.join(mdf, on="time")

    diff = both["utide"] - both["mike"]
    assert diff.abs().max() < 0.0008
