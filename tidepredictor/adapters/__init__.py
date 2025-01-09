"""Adapter for different tide predictor engines."""

from .protocol import TidePredictorAdapter, PredictionType

__all__ = ["TidePredictorAdapter", "PredictionType"]
