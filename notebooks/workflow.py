import marimo

__generated_with = "0.10.2"
app = marimo.App(layout_file="layouts/workflow.grid.json")


@app.cell
def _(t, tide):
    from plotly import express as px

    import polars as pl


    df = pl.DataFrame({"level": tide["h"], "time": t})
    px.line(df, x="time", y="level", title="Tide prediction")
    return df, pl, px


@app.cell(hide_code=True)
def _(mo):
    lat = mo.ui.slider(-90,90,step=0.5, value=0.0, label="Latitude")
    lon = mo.ui.slider(-180,180,step=0.5, value=0.0,label="Longitude")
    mo.vstack([lon,lat])
    return lat, lon


@app.cell(hide_code=True)
def _(lat, lon):
    import folium

    map = folium.Map()
    folium.Marker(
          location=[lat.value, lon.value],
       ).add_to(map)
    map
    return folium, map


@app.cell
def _():
    from pathlib import Path
    from tidepredictor.data import ConstituentReader

    reader = ConstituentReader(
        Path("../data/constituents_2min/GlobalTideElevation_DTU-TPXO8_2min_v1_UpperCase.nc")
    )
    return ConstituentReader, Path, reader


@app.cell
def _(lat, lon, reader):
    cons = reader.get_constituents(lon=lon.value, lat=lat.value)
    cons
    return (cons,)


@app.cell
def _(cons, pl):
    consdf = pl.DataFrame([dict(name=k, amplitude=v.amplitude, phase=v.phase) for k,v in cons.items()]).sort("amplitude", descending=True)
    #mo.ui.table(consdf, selection=None)
    return (consdf,)


@app.cell
def _(consdf, px):
    px.bar(consdf, x='name', y='amplitude')
    return


@app.cell(hide_code=True)
def _(cons):
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
def _(asdict, coef):
    from utide import reconstruct
    import pandas as pd

    t = pd.date_range("2000", periods=200, freq="30min")

    tide = reconstruct(t, asdict(coef))
    return pd, reconstruct, t, tide


@app.cell
def _():
    import marimo as mo
    return (mo,)


if __name__ == "__main__":
    app.run()
