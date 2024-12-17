from dataclasses import dataclass
from pathlib import Path
from typing import Any

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
        assert self.file_path.exists()

    def get_constituents(self, *, lat: float, lon: float) -> dict[str, Constituent]:
        """
        Reads constituents from a file and returns them as a dictionary.

        Parameters
        ----------
        lat : float
            The latitude.
        lon : float
            The longitude.

        Returns
        -------
        dict[str, Constituent]
            The constituents.
        """

        data = (
            xr.open_dataset(self.file_path)
            .isel(time=0)  # TODO remove time from datafile
            .drop_vars("time")
            .sel(lon=lon, lat=lat, method="nearest")
            .to_dict()["data_vars"]
        )

        amps = self._extract_data(data, "amplitude")
        phases = self._extract_data(data, "phase")

        merged = {key: {**amps[key], **phases[key]} for key in amps.keys()}

        res = {k: Constituent(**v) for k, v in merged.items()}

        return res

    @staticmethod
    def _extract_data(data: dict[str, Any], name: str) -> dict[str, Any]:
        res = {
            k.split("_")[0]: {name: v["data"]}  # there is also attrs in the dict
            for k, v in data.items()
            if k.endswith(name)
        }
        return res
