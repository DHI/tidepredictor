import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from dataclasses import asdict
from tidepredictor.data import ConstituentRepository

import polars as pl

import warnings

from .coef import Coef

# Suppress warnings issued by utide
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)
from utide import reconstruct, ut_constants  # noqa: E402


class CurrentPredictor:
    def __init__(self, constituent_repo: ConstituentRepository) -> None:
        self._constituent_repo = constituent_repo

    def predict(
        self,
        lon: float,
        lat: float,
        start: datetime,
        end: datetime,
        interval: timedelta = timedelta(hours=1),
    ) -> pl.DataFrame:
        """Predict tide levels or currents using utide.

        Parameters
        ----------
        lon : float
            The longitude.
        lat : float
            The latitude.
        start : datetime
            The start date.
        end : datetime
            The end date.
        interval : timedelta
            The interval between predictions.

        Returns
        -------
        pl.DataFrame
            The predicted tide levels or currents.

        Notes
        -----
        The workhorse of this functions the `reconstruct` function from [`UTide`](https://github.com/wesleybowman/UTide)
        """

        df = pl.DataFrame().with_columns(
            # TODO use ms instead of ns
            pl.datetime_range(start, end, interval=interval, time_unit="ns").alias(
                "time"
            ),
        )
        # TODO do we need this?
        t = pd.date_range(start=start, end=end, freq=interval)

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
        )

        return df

    def _coef(self, lon: float, lat: float) -> Coef:
        coef = Coef.template()

        ccons = self._constituent_repo.get_current_constituents(lon=lon, lat=lat)
        coef.Lsmaj = np.array([v.major_axis for v in ccons.values()])
        coef.Lsmin = np.array([v.minor_axis for v in ccons.values()])
        coef.theta = np.array([v.inclination for v in ccons.values()])
        coef.g = np.array([v.phase for v in ccons.values()])
        names = list(ccons.keys())

        # TODO extract below into common function for level and current
        unames = ut_constants["const"]["name"]
        ufreqs = ut_constants["const"]["freq"]

        freq_map = {n: float(f) for n, f in zip(unames, ufreqs)}

        coef.name = names
        freqs = np.array([freq_map[name] for name in names])

        coef.aux["frq"] = freqs
        coef.aux["lind"] = np.array([unames.tolist().index(n) for n in names])

        return coef
