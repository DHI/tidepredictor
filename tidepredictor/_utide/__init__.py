"""Utide adapter module."""

from pathlib import Path
import numpy as np
import pandas as pd
import toml  # type: ignore
from dataclasses import dataclass
from typing import Any
from datetime import datetime, timedelta

from dataclasses import asdict
from tidepredictor.adapters import TidePredictorAdapter, PredictionType

import polars as pl

import warnings

from tidepredictor.adapters.protocol import ConstituentRepository

# Suppress warnings issued by utide
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)
from utide import reconstruct, ut_constants  # noqa: E402


@dataclass
class Coef:
    name: list[str]
    mean: float  # level
    umean: float  # current
    vmean: float  # current
    A: np.ndarray  # level
    g: np.ndarray
    Lsmaj: np.ndarray  # current
    Lsmin: np.ndarray  # current
    theta: np.ndarray  # current
    aux: dict[str, Any]  # TODO exctract aux to a separate dataclass

    def __post_init__(self) -> None:
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
    consituent_repo : ConstituentRepository
        Repository
    type : PredictionType
        The type of prediction to make.
    """

    def __init__(
        self, consituent_repo: ConstituentRepository, type: PredictionType
    ) -> None:
        self._consituent_repo = consituent_repo
        self._type = type

        # TODO validation

    def __repr__(self) -> str:
        return f"UtideAdapter(consituents={self._consituent_repo}, type={self._type})"

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
        # TODO do we need this?
        t = pd.date_range(start=start, end=end, freq=interval)
        match self._type:
            case PredictionType.level:
                coef = self._coef(
                    lon=lon,
                    lat=lat,
                )
                tide = reconstruct(t, asdict(coef), verbose=False)
                df = df.with_columns(
                    pl.Series("level", tide["h"]).alias("level"),
                )
            case PredictionType.current:
                coef = self._coef(
                    lon=lon,
                    lat=lat,
                )
                coefd = asdict(coef)
                coefd["aux"]["opt"]["twodim"] = True
                uv = reconstruct(t, coefd, verbose=False)

                df = df.with_columns(
                    pl.Series("u", uv["u"]).alias("u"),
                    pl.Series("v", uv["v"]).alias("v"),
                    # pl.zeros(pl.col("time").len()).alias("u"),
                    # pl.zeros(pl.col("time").len()).alias("v"),
                )

        return df

    def _coef(self, lon: float, lat: float) -> Coef:
        """Get the coefficients for a given location for level.

        Parameters
        ----------
        lon : float
            The longitude of the location.
        lat : float
            The latitude of the location.
        """
        template = Coef.from_toml(Path(__file__).parent / "coef.toml")
        coef = Coef(**asdict(template))

        match self._type:
            case PredictionType.level:
                cons = self._consituent_repo.get_level_constituents(lon=lon, lat=lat)
                coef.A = np.array([v.amplitude for v in cons.values()])
                coef.g = np.array([v.phase for v in cons.values()])
                names = list(cons.keys())

            case PredictionType.current:
                ccons = self._consituent_repo.get_current_constituents(lon=lon, lat=lat)
                coef.Lsmaj = np.array([v.major_axis for v in ccons.values()])
                coef.Lsmin = np.array([v.minor_axis for v in ccons.values()])
                coef.theta = np.array([v.inclination for v in ccons.values()])
                coef.g = np.array([v.phase for v in ccons.values()])
                names = list(ccons.keys())

        unames = ut_constants["const"]["name"]
        ufreqs = ut_constants["const"]["freq"]

        freq_map = {n: float(f) for n, f in zip(unames, ufreqs)}

        coef.name = names
        freqs = np.array([freq_map[name] for name in names])

        coef.aux["frq"] = freqs
        coef.aux["lind"] = np.array([unames.tolist().index(n) for n in names])

        return coef
