"""Utide adapter module."""

from pathlib import Path
import numpy as np
import toml
from dataclasses import dataclass
from typing import Any

from dataclasses import asdict

from utide import ut_constants
from tidepredictor.adapters import TidePredictorAdapter, PredictionType

from datetime import datetime, timedelta

import polars as pl

from tidepredictor.data import ConstituentReader
# import utide


@dataclass
class Coef:
    name: list[str]
    mean: float
    A: np.ndarray
    g: np.ndarray
    aux: dict[str, Any]  # TODO exctract aux to a separate dataclass

    def __post_init__(self):
        assert len(self.A) == len(self.g) == len(self.name) == len(self.aux["frq"])

    @staticmethod
    def _convert_data(data: dict[str, Any]) -> dict[str, Any]:
        data["A"] = np.array(data["A"])
        data["g"] = np.array(data["g"])
        data["aux"]["opt"]["prefilt"] = np.array(data["aux"]["opt"]["prefilt"])
        data["aux"]["frq"] = np.array(data["aux"]["frq"])
        data["aux"]["lind"] = np.array(data["aux"]["lind"])
        return data

    @staticmethod
    def from_toml(file_path: Path) -> "Coef":
        with open(file_path, "r") as file:
            data = toml.load(file)
        data = Coef._convert_data(data)
        return Coef(**data)


class UtideAdapter(TidePredictorAdapter):
    """Adapter for the utide tide predictor engine.

    Parameters
    ----------
    consituents : Any
        The constituents to use for the prediction.
    type : PredictionType
        The type of prediction to make.
    """

    def __init__(self, consituents, type: PredictionType) -> None:
        self._consituents = consituents
        self._type = type

        # TODO convert constituents to utide format

    def predict(
        self, start: datetime, end: datetime, interval: timedelta = timedelta(hours=1)
    ) -> pl.DataFrame:
        """Predict tide levels or currents using utide."""
        # res = utide.reconstruct(t=, coef= , epoch=, constit=)
        # TODO convert utide.Bunch to polars.DataFrame

        df = pl.DataFrame().with_columns(
            pl.datetime_range(start, end, interval=interval).alias("time"),
        )

        match self._type:
            case PredictionType.level:
                df = df.with_columns(
                    pl.zeros(pl.col("time").len()).alias("level"),
                )
            case PredictionType.current:
                df = df.with_columns(
                    pl.zeros(pl.col("time").len()).alias("u"),
                    pl.zeros(pl.col("time").len()).alias("v"),
                )

        return df

    # TODO this should probably be a private method
    @staticmethod
    def coef(fp: Path, lon: float, lat: float) -> Coef:
        """Get the coefficients for a given location.

        Parameters
        ----------
        fp : Path
            The path to the data file.
        lon : float
            The longitude of the location.
        lat : float
            The latitude of the location.
        """
        reader = ConstituentReader(fp)

        cons = reader.get_constituents(lon=lon, lat=lat)
        names = list(cons.keys())
        amps = np.array([v.amplitude for v in cons.values()])
        phases = np.array([v.phase for v in cons.values()])

        template = Coef.from_toml(Path(__file__).parent / "coef.toml")
        coef = Coef(**asdict(template))

        coef.name = names
        coef.A = amps
        coef.g = phases

        unames = ut_constants["const"]["name"]
        ufreqs = ut_constants["const"]["freq"]

        freq_map = {n: float(f) for n, f in zip(unames, ufreqs)}

        freqs = np.array([freq_map[name] for name in names])

        coef.aux["frq"] = freqs
        coef.aux["lind"] = np.array([unames.tolist().index(n) for n in names])

        return coef
