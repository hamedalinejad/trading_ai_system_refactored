"""
Models Module - ML models, ensemble methods, predictions (v79.2)
"""

from .models import (
    PredictionResult,
    ModelMetrics,
    ModelCheckpoint,
    FeatureImportance,
    BaseModel,
    LightGBMModel,
    EnsembleModel,
    MetaModel,
    IsotonicCalibrator,
    ModelError,
    ModelInferenceError,
    ModelTrainingError,
    ModelValidationError,
    calculate_metrics,
    get_feature_importance,
    get_discovered_features,
)

__all__ = [
    "PredictionResult",
    "ModelMetrics",
    "ModelCheckpoint",
    "FeatureImportance",
    "BaseModel",
    "LightGBMModel",
    "EnsembleModel",
    "MetaModel",
    "IsotonicCalibrator",
    "ModelError",
    "ModelInferenceError",
    "ModelTrainingError",
    "ModelValidationError",
    "calculate_metrics",
    "get_feature_importance",
    "get_discovered_features",
]

__version__ = "0.79.2"
