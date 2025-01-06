import marimo

__generated_with = "0.10.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import mikeio
    import polars as pl
    import plotly.express as px
    return mikeio, mo, pl, px


@app.cell
def _(mikeio):
    ds = mikeio.read("../data/MIKE/tide_elevation.dfs0")
    ds
    return (ds,)


@app.cell
def _():
    from pathlib import Path
    from tidepredictor.data import ConstituentReader

    reader = ConstituentReader(
        Path("../data/constituents_2min/GlobalTideElevation_DTU-TPXO8_2min_v1_UpperCase.nc")
    )
    return ConstituentReader, Path, reader


@app.cell
def _(item_sel):
    item_sel.value
    coordinates = item_sel.value.split("Level ")[1].strip("()")
    lon, lat = map(float, coordinates.split(","))
    return coordinates, lat, lon


@app.cell
def _(lat, lon, reader):
    cons = reader.get_constituents(lon=lon,lat=lat)
    from utide._ut_constants import ut_constants
    import numpy as np
    from scripts.coef_dataclass import Coef
    from dataclasses import asdict

    template = Coef.from_toml("../scripts/coef.toml")

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
    return (
        Coef,
        amps,
        asdict,
        coef,
        cons,
        freq_map,
        freqs,
        names,
        np,
        phases,
        template,
        ufreqs,
        unames,
        ut_constants,
    )


@app.cell
def _(asdict, coef, dates):
    from utide import reconstruct
    import pandas as pd

    t = pd.date_range(start=dates.value[0], end=dates.value[1], freq="1h")

    tide = reconstruct(t, asdict(coef))
    return pd, reconstruct, t, tide


@app.cell
def _(pl, t, tide):
    udf = pl.DataFrame({"time": t,"utide": tide["h"]})
    return (udf,)


@app.cell
def _(ds, item_sel, pl):
    mdf = pl.from_pandas(ds[item_sel.value].to_dataframe().reset_index()).rename({"index":"time", item_sel.value: "mike"})
    return (mdf,)


@app.cell
def _(ds):
    start = ds.time[0].to_pydatetime().date()
    stop = ds.time[-1].to_pydatetime().date()
    return start, stop


@app.cell
def _(mo, start, stop):
    from datetime import date
    dates = mo.ui.date_range(value=(date(2024,1,1),date(2024,1,4)),start=start,stop=stop)
    dates
    return date, dates


@app.cell
def _(ds, mo):
    items = [x.name for x in ds.items]
    item_sel = mo.ui.dropdown(items,value=items[0])
    item_sel
    return item_sel, items


@app.cell
def _(lat, lon, mdf, px, udf):
    both = udf.join(mdf, on="time")
    df = both.unpivot(index="time")
    px.line(df, x="time", y="value", color="variable", title=f"{lon}E, {lat}N")
    return both, df


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
