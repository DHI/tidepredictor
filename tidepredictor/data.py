"""
Data handling.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import xarray as xr

FES2014_CONSTITUENTS = [
    "2n2.nc",
    "eps2.nc",
    "j1.nc",
    "k1.nc",
    "k2.nc",
    "l2.nc",
    "la2.nc",
    "m2.nc",
    "m3.nc",
    "m4.nc",
    "m6.nc",
    "m8.nc",
    "mf.nc",
    "mks2.nc",
    "mm.nc",
    "mn4.nc",
    "ms4.nc",
    "msf.nc",
    # "msqm.nc", excluded for now
    # "mtm.nc",
    "mu2.nc",
    "n2.nc",
    "n4.nc",
    "nu2.nc",
    "o1.nc",
    "p1.nc",
    "q1.nc",
    "r2.nc",
    "s1.nc",
    "s2.nc",
    "s4.nc",
    "sa.nc",
    "ssa.nc",
    "t2.nc",
]


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
        if ".nc" not in self.file_path.suffixes:
            constituents = {}
            lon, lat = _convert_FES2014_coords(lon, lat)
            for cons in FES2014_CONSTITUENTS:
                file_path = self.file_path / cons
                name = cons.split(".")[0].upper()

                if name == "LA2":  # Special case for LA2
                    name = "LDA2"

                with xr.open_dataset(file_path) as ds:
                    self._validate_data_domain(ds, lon, lat)

                    df = ds.sel(lon=lon, lat=lat, method="nearest").to_dataframe()

                    for amplitude, phase in zip(df["amplitude"], df["phase"]):
                        constituent = LevelConstituent(
                            name=name, amplitude=amplitude, phase=phase
                        )
                        constituents[name] = constituent

        else:
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

    def get_bathymetry(self, lon: float, lat: float) -> float: ...


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
        self._fp = fp
        # TODO inline functions from reader
        self._reader = ConstituentReader(fp)

    def get_bathymetry(self, lon: float, lat: float) -> float:
        with xr.open_dataset(self._fp) as ds:
            bathy = -ds.bathymetry.sel(lon=lon, lat=lat, method="nearest").item()
        return bathy

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


def _convert_FES2014_coords(lon: float, lat: float) -> tuple[float, float]:
    """
    Function to convert coordinates to FES2014 format.

    Parameters
    ----------
    lat : float
        latitude in degrees (-90 to 90)
    lon : float
        longitude in degrees (-180 to 180)

    Returns
    -------
    tuple[float, float]
        Latitude and Longitude in corrected format for FES2014
    """
    if lat < -90 or lat > 90:
        raise ValueError("Latitude must be between -90 and 90 degrees.")
    if lon < -180 or lon > 180:
        raise ValueError("Longitude must be between -180 and 180 degrees.")

    # Conversion to FES2014 format
    if lon < 0:
        lon += 360

    return lon, lat
