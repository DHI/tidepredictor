"""Tidepredictor package."""

from pathlib import Path
from .adapters.protocol import PredictionType

from ._utide import UtideAdapter
from .data import NetCDFConstituentRepository


def get_default_constituent_path(prediction_type: PredictionType) -> Path:
    """
    Get the default path to the constituent file.

    Parameters
    ----------
    prediction_type : PredictionType
        The type of prediction.

    Returns
    -------
    Path
        The path to the constituent file.
    """
    DATA_DIR = Path("~/.local/share/tidepredictor")

    NAME = {PredictionType.current: "currents.nc", PredictionType.level: "level.nc"}
    path = (DATA_DIR / NAME[prediction_type]).expanduser()
    return path


__all__ = [
    "UtideAdapter",
    "PredictionType",
    "NetCDFConstituentRepository",
    "get_default_constituent_path",
]
