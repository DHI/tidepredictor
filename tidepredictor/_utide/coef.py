"""Coef class for utide adapter."""

from dataclasses import dataclass
from typing import Any
import numpy as np


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
        # TODO add validation for current
        assert len(self.A) == len(self.g) == len(self.name) == len(self.aux["frq"])

    @staticmethod
    def template() -> "Coef":
        """Create a template Coef object with default values from the original configuration."""
        return Coef(
            name=["K1", "K2", "M2", "M4", "MF", "MM", "MN4", "MS4", "N2"],
            mean=0.0,
            umean=0.0,
            vmean=0.0,
            A=np.array(
                [
                    1.00227454,
                    0.02250278,
                    0.01775812,
                    0.01605451,
                    0.01220086,
                    0.00751468,
                    0.00708371,
                    0.00577484,
                    0.00313313,
                ]
            ),
            g=np.array(
                [
                    139.03197411,
                    144.78007052,
                    117.14151752,
                    104.1430418,
                    216.82454621,
                    4.40876086,
                    240.44658427,
                    50.66603851,
                    144.04531879,
                ]
            ),
            Lsmaj=np.array([]),
            Lsmin=np.array([]),
            theta=np.array([]),
            aux={
                "reftime": 737429.1458333333,
                "frq": np.array(
                    [
                        0.0805114,
                        0.04178075,
                        0.3220456,
                        0.20280355,
                        0.1207671,
                        0.28331495,
                        0.1610228,
                        0.2415342,
                        0.20844741,
                    ]
                ),
                "lind": np.array([47, 20, 124, 95, 68, 119, 81, 105, 98]),
                "lat": 42.0,
                "opt": {
                    "twodim": False,
                    "nodiagn": True,
                    "nodsatlint": 0,
                    "nodsatnone": True,
                    "gwchlint": False,
                    "gwchnone": False,
                    "notrend": True,
                    "prefilt": np.array([]),
                },
            },
        )
