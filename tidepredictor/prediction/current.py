from typing import Collection
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from dataclasses import asdict
from tidepredictor.data import ConstituentRepository

import polars as pl

import warnings

from .coef import Coef

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    warnings.filterwarnings("ignore", category=UserWarning)
    from utide import reconstruct, ut_constants

from ..data import ut_constants


class CurrentPredictor:
    """Predict tidal currents.

    Parameters
    ----------
    constituent_repo:
        Current constituent repository.
    alpha:
        Current profile power exponent.

    """

    def __init__(
        self, constituent_repo: ConstituentRepository, alpha: float = 1.0 / 7
    ) -> None:
        self._constituent_repo = constituent_repo
        self._alpha = alpha

    def predict_profile(
        self,
        lon: float,
        lat: float,
        start: datetime,
        end: datetime,
        water_depth: float | None = None,
        interval: timedelta = timedelta(hours=1),
        levels: Collection[float] | None = None,
    ) -> pl.DataFrame:
        """Predict current profiles."""
        df = self.predict_depth_averaged(
            lon=lon, lat=lat, start=start, end=end, interval=interval
        ).rename({"u": "uavg", "v": "vavg"})

        u_vals = df["uavg"].to_numpy()
        v_vals = df["vavg"].to_numpy()

        cs, cd = uv2spddir(u_vals, v_vals)

        # Assign speed and direction
        df = df.with_columns(
            pl.Series("CS_avg", cs),
            pl.Series(r"CD_avg", cd),
        )

        if water_depth is None:
            total_water_depth = self._constituent_repo.get_bathymetry(lon, lat)
        else:
            total_water_depth = water_depth

        if levels is None:
            depths = np.linspace(-total_water_depth, 0, num=10)
        else:
            depths = levels  # type: ignore

        # Validate depths are in valid range
        depths_list = []
        for depth in depths:
            if abs(depth) > total_water_depth:
                raise ValueError(
                    f"Depth: {depth} exceeds total water depth of {total_water_depth} m"
                )
            depths_list.append(depth)
        depths = depths_list
        z = total_water_depth
        alpha = self._alpha

        for depth in depths:
            factor = (1.0 + alpha) * ((depth + z) / z) ** (alpha)

            # Calculate speed and direction for each layer
            u_vals = df["uavg"].to_numpy() * factor
            v_vals = df["vavg"].to_numpy() * factor
            cs, cd = uv2spddir(u_vals, v_vals)

            # Assign calculated speed and direction of each layer
            df = df.with_columns(
                pl.Series(f"CS_({depth})", cs),
                pl.Series(rf"CD_({depth})", cd),
            )

        return df.drop(["uavg", "vavg"])

    def predict_depth_averaged(
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


def uv2spddir(
    u: float | np.ndarray, v: float | np.ndarray
) -> tuple[float | np.ndarray, float | np.ndarray]:
    """
    Function to convert u and v component of the current speed into magnitude (m/s) and direction (degree)

    Parameters
    ----------
    u : float | np.ndarray
        Horizontal component of the current speed (m/s)
    v : float | np.ndarray
        Vertical component of the current speed (m/s)

    Returns
    -------
    tuple[ float | np.ndarray, float | np.ndarray ]
        (spd,dir) Magnitude and direction of the current speed
    """

    mag = np.sqrt(u**2 + v**2)
    direction = np.arctan2(u, v) * 180 / np.pi

    direction = np.mod(direction, 360)

    return mag, direction
