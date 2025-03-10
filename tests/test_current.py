from datetime import datetime, timedelta
from pathlib import Path

import mikeio
import polars as pl
from tidepredictor import (
    CurrentPredictor,
    NetCDFConstituentRepository,
)


def test_utide_returns_dataframe_with_current() -> None:
    repo = NetCDFConstituentRepository(Path("tests/data/currents.nc"))
    predictor = CurrentPredictor(constituent_repo=repo)

    df = predictor.predict_depth_averaged(
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


def test_predict_current_profile() -> None:
    repo = NetCDFConstituentRepository(Path("tests/data/currents.nc"))
    predictor = CurrentPredictor(constituent_repo=repo)

    df = predictor.predict_profile(
        lat=0.0,
        lon=0.0,
        start=datetime(2024, 1, 1),
        end=datetime(2024, 1, 1, 2),
        interval=timedelta(hours=1),
        levels=[-5.0, -15],
    )

    assert isinstance(df, pl.DataFrame)
    assert len(df) == 6  # 3 times * 2 levels
    assert "time" in df.columns
    assert "depth" in df.columns
    assert "u" in df.columns
    assert "v" in df.columns

    cs = df.with_columns((pl.col("u").pow(2) + pl.col("v").pow(2)).sqrt().alias("cs"))

    cs5 = cs.filter(depth=-5, time=datetime(2024, 1, 1))["cs"]
    cs15 = cs.filter(depth=-15, time=datetime(2024, 1, 1))["cs"]
    assert (cs5 > cs15).all()


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

    udf = predictor.predict_depth_averaged(
        lon=lon,
        lat=lat,
        start=ds.time[0].to_pydatetime(),
        end=ds.time[-1].to_pydatetime(),
        interval=timedelta(hours=1),
    ).rename({"v": "utide"})

    both = udf.join(mdf, on="time")

    diff = both["utide"] - both["mike"]
    assert diff.abs().max() < 0.0008
