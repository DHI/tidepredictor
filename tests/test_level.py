from datetime import datetime, timedelta
from pathlib import Path

import mikeio
import polars as pl
from tidepredictor import (
    LevelPredictor,
    NetCDFConstituentRepository,
)
from tidepredictor.data import ConstituentRepository, LevelConstituent


class FakeConstituentRepository(ConstituentRepository):
    def get_level_constituents(self, lon, lat):
        return {
            "MM": LevelConstituent("MM", amplitude=0.009100, phase=353.7),
            "MF": LevelConstituent("MF", amplitude=0.01800, phase=0.00010),
            "Q1": LevelConstituent("Q1", amplitude=0.005000, phase=126.9),
            "O1": LevelConstituent("O1", amplitude=0.01610, phase=299.7),
            "P1": LevelConstituent("P1", amplitude=0.03100, phase=345.1),
            "K1": LevelConstituent("K1", amplitude=0.1064, phase=350.8),
            "N2": LevelConstituent("N2", amplitude=0.09610, phase=102.0),
            "M2": LevelConstituent("M2", amplitude=0.4350, phase=105.6),
            "S2": LevelConstituent("S2", amplitude=0.1543, phase=132.9),
            "K2": LevelConstituent("K2", amplitude=0.04190, phase=130.2),
            "MN4": LevelConstituent("MN4", amplitude=0.002000, phase=270.0),
            "M4": LevelConstituent("M4", amplitude=0.005700, phase=315.0),
            "MS4": LevelConstituent("MS4", amplitude=0.001000, phase=0.00060),
        }

    def get_current_constituents(self, lon, lat):
        return NotImplementedError()


def test_semidiurnal_tide() -> None:
    repo = FakeConstituentRepository()

    predictor = LevelPredictor(
        constituent_repo=repo,
    )

    df = predictor.predict(
        lon=-118,
        lat=34,
        start=datetime(2024, 1, 1),
        end=datetime(2024, 1, 2),
        interval=timedelta(hours=1),
    )

    assert isinstance(df, pl.DataFrame)
    assert "level" in df.columns
    assert df["level"].max() > 0
    assert df["level"].min() < 0


def test_utide_returns_dataframe_with_levels() -> None:
    repo = NetCDFConstituentRepository(Path("tests/data/level.nc"))

    predictor = LevelPredictor(
        constituent_repo=repo,
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


def test_utide_vs_mike_precalculated():
    ds = mikeio.read("tests/data/tide_level.dfs0")
    item = "Level (0,0)"
    mdf = pl.from_pandas(ds[item].to_dataframe().reset_index()).rename(
        {"index": "time", item: "mike"}
    )

    # TODO checks all locations in the file
    lat = 0.0
    lon = 0.0
    repo = NetCDFConstituentRepository(Path("tests/data/level.nc"))
    predictor = LevelPredictor(
        constituent_repo=repo,
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
