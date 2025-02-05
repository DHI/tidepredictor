from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import xarray as xr


@dataclass
class LevelConstituent:
    """
    Represents a tidal constituent.
    """

    amplitude: float
    phase: float


@dataclass
class CurrentConstituent:
    """
    Represents a tidal constituent.
    """

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
        df = (
            xr.open_dataset(self.file_path)
            .sel(lon=lon, lat=lat, method="nearest")
            .to_dataframe()
        )

        amps = df["amplitude"]
        phases = df["phase"]

        merged = {
            key: {"amplitude": amp, "phase": phase}
            for key, amp, phase in zip(amps.index, amps, phases)
        }

        res = {k: LevelConstituent(**v) for k, v in merged.items()}

        return res

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
        dict[str, CurrentConsituent]
            The constituents.
        """
        df = (
            xr.open_dataset(self.file_path)
            .sel(lon=lon, lat=lat, method="nearest")
            .to_dataframe()
        )

        phases = df["phase"]
        major_axis = df["major_axis"]
        minor_axis = df["minor_axis"]
        inclination = df["inclination"]

        merged = {
            key: {
                "phase": phase,
                "major_axis": major,
                "minor_axis": minor,
                "inclination": incl,
            }
            for key, phase, major, minor, incl in zip(
                phases.index, phases, major_axis, minor_axis, inclination
            )
        }

        res = {k: CurrentConstituent(**v) for k, v in merged.items()}
        return res


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
