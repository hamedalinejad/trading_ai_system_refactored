"""
Models Module - Machine learning models and predictions

v79.2 Exports:
- Base model classes
- LightGBM models
- Ensemble methods
- Meta models (stacking)
- Model evaluation utilities
- Feature importance analysis
- Indicator discovery integration
"""

from .models import (
    # Data Classes
    PredictionResult,
    ModelMetrics,
    ModelCheckpoint,
    FeatureImportance,
    
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
    get_discovered_features,
)

__all__ = [
    # Data Classes
    "PredictionResult",
    "ModelMetrics",
    "ModelCheckpoint",
    "FeatureImportance",
    
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
    "get_discovered_features",
]

__version__ = "0.79.2"
