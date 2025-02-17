"""
Data handling.
"""

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
            self._validate_data_domain(ds, lon, lat)

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
            self._validate_data_domain(ds, lon, lat)
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

    @staticmethod
    def _validate_data_domain(ds: xr.Dataset, lon: float, lat: float) -> None:
        """
        Validates the data domain.
        """
        if lon < ds.lon.min() or lon > ds.lon.max():
            raise ValueError(f"Longitude {lon} is outside the data domain")
        if lat < ds.lat.min() or lat > ds.lat.max():
            raise ValueError(f"Latitude {lat} is outside the data domain")


class ConstituentRepository(Protocol):
    """
    A repository of tidal constituents.
    """

    def get_level_constituents(
        self, lon: float, lat: float
    ) -> dict[str, LevelConstituent]: ...

    def get_current_constituents(
        self, lon: float, lat: float
    ) -> dict[str, CurrentConstituent]: ...


class NetCDFConstituentRepository(ConstituentRepository):
    """
    A repository of tidal constituents stored in a NetCDF file.
    """

    def __init__(self, fp: Path) -> None:
        """
        Parameters
        ----------
        fp : Path
            The path to the NetCDF file.
        """
        self._reader = ConstituentReader(fp)

    def get_level_constituents(
        self, lon: float, lat: float
    ) -> dict[str, LevelConstituent]:
        """
        Get the level constituents for a given longitude and latitude.

        Parameters
        ----------
        lon : float
            The longitude.
        lat : float
            The latitude.

        Returns
        -------
        dict[str, LevelConstituent]
            The level constituents.
        """
        return self._reader.get_level_constituents(lat=lat, lon=lon)

    def get_current_constituents(
        self, lon: float, lat: float
    ) -> dict[str, CurrentConstituent]:
        """
        Get the current constituents for a given longitude and latitude.

        Parameters
        ----------
        lon : float
            The longitude.
        lat : float
            The latitude.

        Returns
        -------
        dict[str, CurrentConstituent]
            The current constituents.
        """
        return self._reader.get_current_constituents(lat=lat, lon=lon)
