"""Tidepredictor package."""

from .utide import UtideAdapter
from .adapters.protocol import PredictionType
import warnings

# Suppress warnings issued by utide
warnings.filterwarnings("ignore", category=RuntimeWarning)


__all__ = ["UtideAdapter", "PredictionType"]
