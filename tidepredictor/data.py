"""
Data handling.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import xarray as xr

import warnings
import numpy as np

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    warnings.filterwarnings("ignore", category=UserWarning)
    import utide


def _add_constituent(name: str, freq_rad_per_sec: str) -> dict:
    """
    Aux function to add a complete constituent to UTide with all required fields
    """

    const = utide.ut_constants

    # Current number of constituents
    n_existing = len(const["const"]["name"])

    # Add to all arrays with appropriate default values
    const["const"]["name"] = np.append(const["const"]["name"], name)
    const["const"]["freq"] = np.append(const["const"]["freq"], freq_rad_per_sec)

    # Extend all other arrays to match
    for key, value in const["const"].items():
        if key not in ["name", "freq"] and isinstance(value, np.ndarray):
            if value.ndim == 1 and len(value) == n_existing:
                # 1D array - append appropriate default
                if "f" in key.lower() or key == "v0u":
                    default_val = 1.0  # nodal factors default to 1
                else:
                    default_val = 0.0  # most other things default to 0
                const["const"][key] = np.append(value, default_val)
            elif value.ndim == 2 and value.shape[0] == n_existing:
                # 2D array - append row of zeros
                zeros_row = np.zeros((1, value.shape[1]), dtype=value.dtype)
                const["const"][key] = np.vstack([value, zeros_row])
    return const


# Add MSQM
freq_cycles_per_year = 51.472
seconds_per_year = 365.25 * 24 * 3600
freq_rad_per_sec = freq_cycles_per_year * 2 * np.pi / seconds_per_year

ut_constants = _add_constituent("MSQM", freq_rad_per_sec)

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
    "msqm.nc",
    # "mtm.nc", # Not included in UTide
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

        # Check if the file is a NetCDF file or a directory
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
                        amplitude /= 100  # Convert from cm to m
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
        constituents = {}

        # Check if the file is a NetCDF file or a directory
        if ".nc" not in self.file_path.suffixes:
            lon, lat = _convert_FES2014_coords(lon, lat)
            for cons in FES2014_CONSTITUENTS:
                file_path_u = self.file_path / "eastward_velocity" / cons
                file_path_v = self.file_path / "northward_velocity" / cons

                name = cons.split(".")[0].upper()

                if name == "LA2":  # Special case for LA2
                    name = "LDA2"

                with xr.open_dataset(file_path_u) as ds_u:
                    self._validate_data_domain(ds_u, lon, lat)

                    df_u = ds_u.sel(lon=lon, lat=lat, method="nearest").to_dataframe()
                with xr.open_dataset(file_path_v) as ds_v:
                    self._validate_data_domain(ds_v, lon, lat)

                    df_v = ds_v.sel(lon=lon, lat=lat, method="nearest").to_dataframe()

                major_axis_list, minor_axis_list, inclination_list, phase_list = ap2ep(
                    df_u["Ua"].values / 100,
                    df_u["Ug"].values,
                    df_v["Va"].values / 100,
                    df_v["Vg"].values,
                )
                for major_axis, minor_axis, inclination, phase in zip(
                    major_axis_list, minor_axis_list, inclination_list, phase_list
                ):
                    constituent = CurrentConstituent(
                        name=name,
                        phase=phase,
                        major_axis=major_axis,
                        minor_axis=minor_axis,
                        inclination=inclination,
                    )
                    constituents[name] = constituent

        else:
            with xr.open_dataset(self.file_path) as ds:
                self._validate_data_domain(ds, lon, lat)
                df = ds.sel(lon=lon, lat=lat, method="nearest").to_dataframe()

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


def ap2ep(
    Au: np.ndarray, PHIu: np.ndarray, Av: np.ndarray, PHIv: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Convert tidal amplitude and phase lag (ap-) parameters into tidal ellipse (ep-) parameters.
    Inspired from 'https://www.mathworks.com/matlabcentral/fileexchange/347-tidal_ellipse'

    Parameters
    -----------
    Au : array_like
        Amplitudes of eastward (u) component
    PHIu : array_like
        Phase lags of u component (degrees)
    Av : array_like
        Amplitudes of northward (v) component
    PHIv : array_like
        Phase lags of v component (degrees)
    plot_demo : tuple of indices (optional)
        Indices into the arrays to plot a demo ellipse.

    Returns
    --------
    major_ax : ndarray
        Semi-major axis (max speed)
    minor_ax : ndarray
        Semi-minor axis (min speed)
    inc : ndarray
        Inclination (degrees)
    phase : ndarray
        Phase angle (degrees)
    """
    # Convert phase lags from degrees to radians
    PHIu_rad = np.radians(PHIu)
    PHIv_rad = np.radians(PHIv)

    # Complex representations of u and v components
    u = Au * np.exp(-1j * PHIu_rad)
    v = Av * np.exp(-1j * PHIv_rad)

    # Decompose into circular components
    wp = (u + 1j * v) / 2  # anticlockwise
    wm = np.conj(u - 1j * v) / 2  # clockwise

    # Amplitudes and angles
    Wp = np.abs(wp)
    Wm = np.abs(wm)
    THETAp = np.angle(wp)
    THETAm = np.angle(wm)

    # Ellipse parameters
    major_ax = Wp + Wm
    minor_ax = Wp - Wm
    phase = (THETAm - THETAp) / 2
    inc = (THETAm + THETAp) / 2

    # Convert radians to degrees
    phase = np.degrees(phase) % 360
    inc = np.degrees(inc) % 360

    # Adjust to northern semi-major axis (Foreman convention)
    k = (inc // 180).astype(int)
    inc -= k * 180
    phase = (phase + k * 180) % 360

    return major_ax, minor_ax, inc, phase
