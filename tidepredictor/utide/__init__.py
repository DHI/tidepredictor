"""Utide adapter module."""

from pathlib import Path
import numpy as np
import pandas as pd
import toml  # type: ignore
from dataclasses import dataclass
from typing import Any

from dataclasses import asdict

from utide import reconstruct, ut_constants
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

    def __init__(self, consituents: Path, type: PredictionType) -> None:
        self._consituents = consituents
        self._type = type

        # TODO convert constituents to utide format

    def predict(
        self,
        lon: float,
        lat: float,
        start: datetime,
        end: datetime,
        interval: timedelta = timedelta(hours=1),
    ) -> pl.DataFrame:
        """Predict tide levels or currents using utide."""

        df = pl.DataFrame().with_columns(
            # TODO use ms instead of ns
            pl.datetime_range(start, end, interval=interval, time_unit="ns").alias(
                "time"
            ),
        )

        match self._type:
            case PredictionType.level:
                coef = self._coef(
                    fp=self._consituents,
                    lon=lon,
                    lat=lat,
                )
                # TODO do we need this?
                t = pd.date_range(start=start, end=end, freq=interval)
                tide = reconstruct(t, asdict(coef), verbose=False)
                df = df.with_columns(
                    pl.Series("level", tide["h"]).alias("level"),
                )
            case PredictionType.current:
                df = df.with_columns(
                    # TODO implement currents
                    pl.zeros(pl.col("time").len()).alias("u"),
                    pl.zeros(pl.col("time").len()).alias("v"),
                )

        return df

    def _coef(self, fp: Path, lon: float, lat: float) -> Coef:
        """Get the coefficients for a given location for elevation.

        Parameters
        ----------
        fp : Path
            The path to the data file.
        lon : float
            The longitude of the location.
        lat : float
            The latitude of the location.
        """

        if self._type != PredictionType.level:
            raise NotImplementedError("Only level predictions are supported.")

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
