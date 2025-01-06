from dataclasses import asdict
from datetime import datetime, timedelta
from pathlib import Path

from utide._ut_constants import ut_constants
import numpy as np
from scripts.coef_dataclass import Coef


import mikeio
import pandas as pd
import polars as pl
from utide import reconstruct
from tidepredictor.adapters import PredictionType, UtideAdapter
from tidepredictor.data import ConstituentReader


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
    template = Coef.from_toml("scripts/coef.toml")
    lat = 0.0
    lon = 0.0
    reader = ConstituentReader(
        Path("tests/data/GlobalTideElevation_DTU-TPXO8_2min_v1_UpperCase_test.nc")
    )
    cons = reader.get_constituents(lon=lon, lat=lat)
    names = list(cons.keys())
    amps = np.array([v.amplitude for v in cons.values()])
    phases = np.array([v.phase for v in cons.values()])

    coef = Coef(**asdict(template))

    coef.name = names
    coef.A = amps
    coef.g = phases

    unames = ut_constants["const"]["name"]
    ufreqs = ut_constants["const"]["freq"]

    freq_map = {n: float(f) for n, f in zip(unames, ufreqs)}

    freqs = np.array([freq_map[name] for name in names])

    coef.aux["frq"] = freqs
    coef.aux["lind"] = np.array([unames.tolist().index(n) for n in names])
    t = pd.date_range(start=ds.time[0], end=ds.time[1], freq="1h")

    tide = reconstruct(t, asdict(coef))
    udf = pl.DataFrame({"time": t, "utide": tide["h"]})

    both = udf.join(mdf, on="time")

    diff = both["utide"] - both["mike"]
    assert diff.abs().max() < 0.05
