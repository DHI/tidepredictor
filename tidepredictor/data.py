"""
Data handling.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Optional

import xarray as xr

import warnings
import numpy as np

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    warnings.filterwarnings("ignore", category=UserWarning)
    import utide
    from utide.ellipse_params import ut_cs2cep


def _add_constituent(name: str, freq_rad_per_sec: float) -> dict:
    """
    Aux function to add a complete constituent to UTide with all required fields
    """

    const = utide.ut_constants

    new_const = const.copy()

    # Current number of constituents
    n_existing = len(new_const["const"]["name"])

    # Add to all arrays with appropriate default values
    new_const["const"]["name"] = np.append(new_const["const"]["name"], name)
    new_const["const"]["freq"] = np.append(new_const["const"]["freq"], freq_rad_per_sec)

    # Extend all other arrays to match
    for key, value in new_const["const"].items():
        if key not in ["name", "freq"] and isinstance(value, np.ndarray):
            if value.ndim == 1 and len(value) == n_existing:
                # 1D array - append appropriate default
                if "f" in key.lower() or key == "v0u":
                    default_val = 1.0  # nodal factors default to 1
                else:
                    default_val = 0.0  # most other things default to 0
                new_const["const"][key] = np.append(value, default_val)
            elif value.ndim == 2 and value.shape[0] == n_existing:
                # 2D array - append row of zeros
                zeros_row = np.zeros((1, value.shape[1]), dtype=value.dtype)
                new_const["const"][key] = np.vstack([value, zeros_row])
    return const


# Add MSQM
freq_cycles_per_year = 51.472
seconds_per_year = 365.25 * 24 * 3600
freq_rad_per_sec = freq_cycles_per_year * 2 * np.pi / seconds_per_year

ut_constants = _add_constituent("MSQM", freq_rad_per_sec)

FES2014_CONSTITUENTS = [
    "2n2",
    "eps2",
    "j1",
    "k1",
    "k2",
    "l2",
    "la2",
    "m2",
    "m3",
    "m4",
    "m6",
    "m8",
    "mf",
    "mks2",
    "mm",
    "mn4",
    "ms4",
    "msf",
    "msqm",
    # "mtm", # Not included in UTide
    "mu2",
    "n2",
    "n4",
    "nu2",
    "o1",
    "p1",
    "q1",
    "r2",
    "s1",
    "s2",
    "s4",
    "sa",
    "ssa",
    "t2",
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


class ConstituentReaderProtocol(Protocol):
    def get_level_constituents(
        self, *, lat: float, lon: float
    ) -> dict[str, LevelConstituent]: ...
    def get_current_constituents(
        self, *, lat: float, lon: float
    ) -> dict[str, CurrentConstituent]: ...


class ConstituentReaderDTU14:
    """
    Reads constituents from a DTU14 file.
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


class ConstituentReaderFES:
    """
    Reads constituents from FES files.
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
        constituents = {}
        lon, lat = _convert_FES2014_coords(lon, lat)
        for cons in FES2014_CONSTITUENTS:
            file_path = self.file_path / f"{cons}.nc"
            name = cons.upper()

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
        lon, lat = _convert_FES2014_coords(lon, lat)
        for cons in FES2014_CONSTITUENTS:
            file_path_u = self.file_path / "eastward_velocity" / f"{cons}.nc"
            file_path_v = self.file_path / "northward_velocity" / f"{cons}.nc"

            name = cons.upper()

            if name == "LA2":  # Special case for LA2
                name = "LDA2"

            with xr.open_dataset(file_path_u) as ds_u:
                self._validate_data_domain(ds_u, lon, lat)

                df_u = ds_u.sel(lon=lon, lat=lat, method="nearest").to_dataframe()

                Ua = df_u["Ua"].unique()[0] / 100  # conversion from cm/s to m/s
                Ug = df_u["Ug"].unique()[0]
            with xr.open_dataset(file_path_v) as ds_v:
                self._validate_data_domain(ds_v, lon, lat)

                df_v = ds_v.sel(lon=lon, lat=lat, method="nearest").to_dataframe()
                Va = df_v["Va"].unique()[0] / 100  # conversion from cm/s to m/s
                Vg = df_v["Vg"].unique()[0]

            Ug_rad = np.deg2rad(Ug)
            Vg_rad = np.deg2rad(Vg)

            # Convert amplitude and phase into cosine and sine coefficients
            Xu = Ua * np.cos(Ug_rad)
            Yu = Ua * np.sin(Ug_rad)
            Xv = Va * np.cos(Vg_rad)
            Yv = Va * np.sin(Vg_rad)

            major_axis, minor_axis, inclination, phase = ut_cs2cep(Xu, Yu, Xv, Yv)

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

    _reader: ConstituentReaderProtocol

    def __init__(self, fp: Path, *, model_name: Optional[str] = None) -> None:
        """
        Parameters
        ----------
        fp : Path
            The path to the NetCDF file.
        model : str
            The model name, e.g., "FES2014" or "DTU14
        """
        self._fp = fp
        self.model_name = model_name
        if model_name is not None:
            # TODO inline functions from reader
            if model_name.upper() == "FES2014":
                self._reader = ConstituentReaderFES(fp)
            elif model_name.upper() == "DTU14":
                self._reader = ConstituentReaderDTU14(fp)
            else:
                raise ValueError(
                    f"Unsupported model name: {model_name}. Available models: 'DTU14' and 'FES2014'"
                )
        else:
            raise ValueError(
                "Specify a model! Available models: 'DTU14' and 'FES2014' ."
            )

    def get_bathymetry(self, lon: float, lat: float) -> float:
        if self.model_name == "FES2014":
            raise NotImplementedError(
                "The FES2014 constituent files do not include any bathymetry data! Please specify water detpth instead."
            )
        else:
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

    # Conversion to FES2014 format
    return (lon + 360 if lon < 0 else lon, lat)
