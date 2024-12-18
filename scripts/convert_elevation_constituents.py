import xarray as xr
from pathlib import Path

path = Path("data/constituents_2min/GlobalTideElevation_DTU-TPXO8_2min_v1_UpperCase.nc")

el = xr.open_dataset(path)

# Remove the time dimension also from the coordinates
el_not = el.squeeze(dim="time").drop_vars("time")

names = [v.split("_")[0] for v in el_not.data_vars][::2]

amplitudes = xr.concat([el_not[f"{name}_amplitude"] for name in names], dim="cons")
amplitude = amplitudes.assign_coords(cons=names)

phases = xr.concat([el_not[f"{name}_phase"] for name in names], dim="cons")
phase = phases.assign_coords(cons=names)

final = xr.Dataset({"amplitude": amplitude, "phase": phase})


final.to_netcdf("data/constituents_2min/GlobalTideElevation_DTU-TPXO8_2min_v1_clean.nc")
