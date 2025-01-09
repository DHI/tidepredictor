from dataclasses import dataclass
from pathlib import Path

import xarray as xr


@dataclass
class LevelConsituent:
    """
    Represents a tidal constituent.
    """

    amplitude: float
    phase: float


@dataclass
class CurrentConsituent:
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
    ) -> dict[str, LevelConsituent]:
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

        res = {k: LevelConsituent(**v) for k, v in merged.items()}

        return res

    def get_current_constituents(
        self, *, lat: float, lon: float
    ) -> dict[str, CurrentConsituent]:
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

        res = {k: CurrentConsituent(**v) for k, v in merged.items()}
        return res
