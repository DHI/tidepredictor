"""Tidepredictor package."""

from enum import Enum
from pathlib import Path
from .prediction import LevelPredictor, CurrentPredictor
from .data import NetCDFConstituentRepository


class PredictionType(str, Enum):
    level = "level"
    current = "current"


def get_default_constituent_path(
    prediction_type: PredictionType,
    model_name: str = "DTU10",
) -> Path:
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
    if model_name not in ["DTU10", "FES2014"]:
        raise ValueError(
            f"Unsupported model name: {model_name}. Supported models are: DTU10, FES2014."
        )

    if model_name == "DTU10":
        DATA_DIR = Path("~/.local/share/tidepredictor/DTU10")
        NAME = {PredictionType.current: "currents.nc", PredictionType.level: "level.nc"}
        path = (DATA_DIR / NAME[prediction_type]).expanduser()

    elif model_name == "FES2014":
        DATA_DIR = Path("~/.local/share/tidepredictor/FES2014")
        FOLD_NAME = {
            PredictionType.current: "current",
            PredictionType.level: "level",
        }

        path = (DATA_DIR / FOLD_NAME[prediction_type]).expanduser()

    return path


__all__ = [
    "LevelPredictor",
    "CurrentPredictor",
    "PredictionType",
    "NetCDFConstituentRepository",
    "get_default_constituent_path",
]
