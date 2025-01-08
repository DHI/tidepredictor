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
        df = (
            xr.open_dataset(self.file_path)
            .sel(lon=lon, lat=lat, method="nearest")
            .to_dataframe()
        )
        amps = df["amplitude"].to_dict()
        phases = df["phase"].to_dict()

        merged = {
            key: dict(amplitude=amps[key], phase=phases[key]) for key in amps.keys()
        }

        res = {k: Constituent(**v) for k, v in merged.items()}

        return res
