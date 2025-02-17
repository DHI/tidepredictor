from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import xarray as xr


@dataclass
class LevelConstituent:
    """
    Represents a tidal constituent.
    """

    name: str
    amplitude: float
    phase: float


@dataclass
class CurrentConstituent:
    """
    Represents a tidal constituent.
    """

    name: str
    phase: float
    major_axis: float
    minor_axis: float
    inclination: float


class ConstituentReader:
    """
    Reads constituents from a file.
    """

    def __init__(self, file_path: Path):
        self.file_path = file_path
        assert self.file_path.exists()

    def get_level_constituents(
        self, *, lat: float, lon: float
    ) -> dict[str, LevelConstituent]:
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
        with xr.open_dataset(self.file_path) as ds:
            df = ds.sel(lon=lon, lat=lat, method="nearest").to_dataframe()

            constituents = {}
            for name, amplitude, phase in zip(
                df["amplitude"].index, df["amplitude"], df["phase"]
            ):
                constituent = LevelConstituent(
                    name=name, amplitude=amplitude, phase=phase
                )
                constituents[name] = constituent

            return constituents

    def get_current_constituents(
        self, *, lat: float, lon: float
    ) -> dict[str, CurrentConstituent]:
        """Reads constituents from a file and returns them as a dictionary.

        Parameters
        ----------
        lat : float
            The latitude.
        lon : float
            The longitude.

        Returns
        -------
        dict[str, CurrentConstituent]
            The constituents.
        """
        with xr.open_dataset(self.file_path) as ds:
            df = ds.sel(lon=lon, lat=lat, method="nearest").to_dataframe()

            constituents = {}
            for name, phase, major_axis, minor_axis, inclination in zip(
                df["phase"].index,
                df["phase"],
                df["major_axis"],
                df["minor_axis"],
                df["inclination"],
            ):
                constituent = CurrentConstituent(
                    name=name,
                    phase=phase,
                    major_axis=major_axis,
                    minor_axis=minor_axis,
                    inclination=inclination,
                )
                constituents[name] = constituent

            return constituents


class ConstituentRepository(Protocol):
    def get_level_constituents(
        self, lon: float, lat: float
    ) -> dict[str, LevelConstituent]:
        pass

    def get_current_constituents(
        self, lon: float, lat: float
    ) -> dict[str, CurrentConstituent]:
        pass


class NetCDFConstituentRepository(ConstituentRepository):
    def __init__(self, fp: Path) -> None:
        self._reader = ConstituentReader(fp)

    def get_level_constituents(
        self, lon: float, lat: float
    ) -> dict[str, LevelConstituent]:
        return self._reader.get_level_constituents(lat=lat, lon=lon)

    def get_current_constituents(
        self, lon: float, lat: float
    ) -> dict[str, CurrentConstituent]:
        return self._reader.get_current_constituents(lat=lat, lon=lon)
