import marimo

__generated_with = "0.10.9"
app = marimo.App(width="medium")


@app.cell
def _():
    import xarray as xr

    return (xr,)


@app.cell
def _(xr):
    ds = xr.open_dataset(
        "data/constituents_2min/GlobalTideCurrent_DTU-TPXO8_2min_v1.nc"
    )
    ds
    return (ds,)


@app.cell
def _(ds):
    ds.Bathymetry.sel(lon=slice(5, 15), lat=slice(50, 60)).plot(x="lon", y="lat")
    return


@app.cell
def _(ds):
    ds.Bathymetry.sel(lon=9, lat=56, method="nearest").values
    return


@app.cell
def _(ds):
    import numpy as np

    bathy = ds.Bathymetry.squeeze(dim="t").drop_vars("t")
    return bathy, np


@app.cell
def _(bathy):
    bathy.sel(lon=slice(5, 15), lat=slice(50, 60)).plot(x="lon")
    return


@app.cell
def _(bathy, np):
    def find_nearest_ocean_point(lat, lon):
        # Get the latitude and longitude values
        lats = bathy["lat"].values
        lons = bathy["lon"].values

        # Create a 2D meshgrid of lat/lon
        lon_grid, lat_grid = np.meshgrid(lats, lons)

        # Mask out NaN (land) values
        ocean_mask = bathy.values < 0.0
        ocean_lats = lat_grid[ocean_mask]
        ocean_lons = lon_grid[ocean_mask]

        # Calculate Cartesian distance (in degrees)
        dlat = ocean_lats - lat
        dlon = (ocean_lons - lon) * np.cos(
            np.radians(lat)
        )  # Scale longitude by latitude
        distances = np.sqrt(dlat**2 + dlon**2)

        # Find the nearest point
        min_idx = np.argmin(distances)
        nearest_lat = ocean_lats[min_idx]
        nearest_lon = ocean_lons[min_idx]
        nearest_distance = distances[min_idx]

        return nearest_lat, nearest_lon, nearest_distance

    return (find_nearest_ocean_point,)


@app.cell
def _(find_nearest_ocean_point):
    nlon, nlat, _ = find_nearest_ocean_point(9, 55)
    return nlat, nlon


@app.cell
def _(bathy, nlat, nlon):
    bathy.sel(lon=nlon, lat=nlat)
    return


@app.cell
def _(nlon):
    nlon
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
