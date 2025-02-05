import marimo

__generated_with = "0.10.12"
app = marimo.App()


@app.cell
def _():
    from plotly import express as px

    import polars as pl

    # df = pl.DataFrame({"level": tide["h"], "time": t})
    # px.line(df, x="time", y="level", title="Tide prediction")
    return pl, px


@app.cell(hide_code=True)
def _(mo):
    lat = mo.ui.slider(-90, 90, step=0.5, value=0.0, label="Latitude")
    lon = mo.ui.slider(-180, 180, step=0.5, value=0.0, label="Longitude")
    mo.vstack([lon, lat])
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
def _(consdf, px):
    px.bar(consdf, x="name", y="amplitude")
    return


@app.cell
def _():
    from pathlib import Path
    from tidepredictor.data import ConstituentReader

    reader = ConstituentReader(Path("../tests/data/level.nc"))
    return ConstituentReader, Path, reader


@app.cell
def _(lat, lon, reader):
    cons = reader.get_level_constituents(lon=lon.value, lat=lat.value)
    cons
    return (cons,)


@app.cell
def _(cons, pl):
    consdf = pl.DataFrame(
        [dict(name=k, amplitude=v.amplitude, phase=v.phase) for k, v in cons.items()]
    ).sort("amplitude", descending=True)
    # mo.ui.table(consdf, selection=None)
    return (consdf,)


@app.cell
def _():
    import marimo as mo

    return (mo,)


if __name__ == "__main__":
    app.run()
