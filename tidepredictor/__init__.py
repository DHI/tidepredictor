"""Tidepredictor package."""

from .adapters.protocol import PredictionType

from ._utide import UtideAdapter


__all__ = ["UtideAdapter", "PredictionType"]
