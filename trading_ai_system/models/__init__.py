"""
Models Module - Machine learning models and predictions

v79.1 Exports:
- Base model classes
- LightGBM models
- Ensemble methods
- Meta models (stacking)
- Model evaluation utilities
"""

from .models import (
    # Data Classes
    PredictionResult,
    ModelMetrics,
    ModelCheckpoint,
    
    # Base Classes
    BaseModel,
    LightGBMModel,
    EnsembleModel,
    MetaModel,
    IsotonicCalibrator,
    
    # Exceptions
    ModelError,
    ModelInferenceError,
    ModelTrainingError,
    ModelValidationError,
    
    # Functions
    calculate_metrics,
    get_feature_importance,
)

__all__ = [
    # Data Classes
    "PredictionResult",
    "ModelMetrics",
    "ModelCheckpoint",
    
    # Base Classes
    "BaseModel",
    "LightGBMModel",
    "EnsembleModel",
    "MetaModel",
    "IsotonicCalibrator",
    
    # Exceptions
    "ModelError",
    "ModelInferenceError",
    "ModelTrainingError",
    "ModelValidationError",
    
    # Functions
    "calculate_metrics",
    "get_feature_importance",
]

__version__ = "0.79.1"
