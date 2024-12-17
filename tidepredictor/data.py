from dataclasses import dataclass
from pathlib import Path

import xarray as xr


@dataclass
class Constituent:
    """
    Represents a tidal constituent.
    """

    amplitude: float
    phase: float


class ConstituentReader:
    """
    Reads constituents from a file.
    """

    def __init__(self, file_path: Path):
        self.file_path = file_path

    def read_constituents(self, *, lat: float, lon: float) -> dict[str, Constituent]:
        """
        Reads constituents from a file and returns them as a dictionary.
        """

        ds = xr.open_dataset(self.file_path)

        amps = {
            k.split("_")[0]: {"amplitude": v["data"]}
            for k, v in ds.isel(time=0)
            .drop_vars("time")
            .sel(lon=lon, lat=lat, method="nearest")
            .to_dict()["data_vars"]
            .items()
            if k.endswith("amplitude")
        }

        phases = {
            k.split("_")[0]: {"phase": v["data"]}
            for k, v in ds.isel(time=0)
            .drop_vars("time")
            .sel(lon=lon, lat=lat, method="nearest")
            .to_dict()["data_vars"]
            .items()
            if k.endswith("phase")
        }

        merged = {key: {**amps[key], **phases[key]} for key in amps.keys()}

        merged

        res = {k: Constituent(**v) for k, v in merged.items()}

        return res
