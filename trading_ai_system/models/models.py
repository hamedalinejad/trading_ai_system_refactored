"""
Trading AI System - Models Module
Machine learning models, ensemble methods, and prediction infrastructure.
"""

import sys
import logging
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

import numpy as np
import pandas as pd

# ✅ Fixed: Proper error handling for optional dependencies
logger = logging.getLogger(__name__)

# Try to import optional dependencies
try:
    from trading_ai_system.core import (
        TradingSystemError,
        get_global_config,
        register_feature,
    )
except ImportError:
    TradingSystemError = Exception
    def get_global_config():
        return {}
    def register_feature(*args, **kwargs):
        pass


# ═══════════════════════════════════════════════════════════════════════════
# EXCEPTION CLASSES
# ═══════════════════════════════════════════════════════════════════════════

class ModelError(TradingSystemError):
    """Base model error."""
    pass


class ModelInferenceError(ModelError):
    """Model inference/prediction error."""
    pass


class ModelTrainingError(ModelError):
    """Model training error."""
    pass


class ModelValidationError(ModelError):
    """Model validation error."""
    pass


# ═══════════════════════════════════════════════════════════════════════════
# DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class PredictionResult:
    """Model prediction result."""
    prediction: int  # -1, 0, 1 for sell, hold, buy
    probability: float  # Confidence 0-1
    timestamp: Any = None
    model_name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "prediction": self.prediction,
            "probability": self.probability,
            "timestamp": str(self.timestamp) if self.timestamp else None,
            "model_name": self.model_name,
            "metadata": self.metadata
        }


@dataclass
class ModelMetrics:
    """Model performance metrics."""
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    roc_auc: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            "accuracy": self.accuracy,
            "precision": self.precision,
            "recall": self.recall,
            "f1_score": self.f1_score,
            "roc_auc": self.roc_auc,
            "sharpe_ratio": self.sharpe_ratio,
            "max_drawdown": self.max_drawdown,
            "win_rate": self.win_rate
        }


# ═══════════════════════════════════════════════════════════════════════════
# BASE MODEL INTERFACE
# ═══════════════════════════════════════════════════════════════════════════

class BaseModel(ABC):
    """Abstract base class for all models."""
    
    def __init__(self, name: str):
        """Initialize model."""
        self.name = name
        self.is_trained = False
        self.metrics = ModelMetrics()
    
    @abstractmethod
    def fit(self, X_train: pd.DataFrame, y_train: pd.Series, **kwargs) -> 'BaseModel':
        """Train model."""
        pass
    
    @abstractmethod
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Make predictions."""
        pass
    
    @abstractmethod
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Get prediction probabilities."""
        pass
    
    def set_metrics(self, metrics: ModelMetrics) -> None:
        """Set model metrics."""
        self.metrics = metrics
    
    def get_metrics(self) -> ModelMetrics:
        """Get model metrics."""
        return self.metrics


# ═══════════════════════════════════════════════════════════════════════════
# LIGHTGBM WRAPPER
# ═══════════════════════════════════════════════════════════════════════════

class LightGBMModel(BaseModel):
    """LightGBM model wrapper."""
    
    def __init__(self, name: str = "lgb_model", **kwargs):
        """Initialize LightGBM model."""
        super().__init__(name)
        self.model = None
        self.params = kwargs
        
        # ✅ Check dependency at init
        try:
            import lightgbm as lgb
            self._lgb = lgb
        except ImportError:
            self._lgb = None
            logger.warning("LightGBM not installed - model will fail at training")
    
    def fit(self, X_train: pd.DataFrame, y_train: pd.Series, **kwargs) -> 'LightGBMModel':
        """Train LightGBM model."""
        if self._lgb is None:
            raise ModelTrainingError(
                "LightGBM not installed. Run: pip install lightgbm"
            )
        
        try:
            # Default parameters
            params = {
                'objective': 'multiclass',
                'num_class': 3,
                'learning_rate': 0.05,
                'num_leaves': 31,
                'max_depth': 7,
                'verbose': -1,
            }
            params.update(self.params)
            
            # Create dataset
            train_data = self._lgb.Dataset(X_train, label=y_train)
            
            # Train model
            self.model = self._lgb.train(
                params,
                train_data,
                num_boost_round=100,
                **kwargs
            )
            
            self.is_trained = True
            logger.info(f"Trained {self.name} on {len(X_train)} samples")
            
            return self
        
        except Exception as e:
            raise ModelTrainingError(f"Training failed: {e}")
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Get class predictions."""
        if not self.is_trained or self.model is None:
            raise ModelInferenceError("Model not trained")
        
        try:
            proba = self.model.predict(X, num_iteration=self.model.best_iteration)
            return np.argmax(proba, axis=1) - 1  # Convert 0,1,2 to -1,0,1
        except Exception as e:
            raise ModelInferenceError(f"Prediction failed: {e}")
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Get prediction probabilities."""
        if not self.is_trained or self.model is None:
            raise ModelInferenceError("Model not trained")
        
        try:
            return self.model.predict(X, num_iteration=self.model.best_iteration)
        except Exception as e:
            raise ModelInferenceError(f"Probability prediction failed: {e}")


# ═══════════════════════════════════════════════════════════════════════════
# ENSEMBLE MODELS
# ═══════════════════════════════════════════════════════════════════════════

class EnsembleModel(BaseModel):
    """Ensemble of multiple models."""
    
    def __init__(self, name: str = "ensemble", models: Optional[List[BaseModel]] = None):
        """Initialize ensemble."""
        super().__init__(name)
        self.models = models or []
        self.weights = [1.0 / len(self.models)] if self.models else []
    
    def add_model(self, model: BaseModel) -> None:
        """Add model to ensemble."""
        self.models.append(model)
        self.weights = [1.0 / len(self.models)] * len(self.models)
    
    def fit(self, X_train: pd.DataFrame, y_train: pd.Series, **kwargs) -> 'EnsembleModel':
        """Train all models in ensemble."""
        for i, model in enumerate(self.models):
            logger.info(f"Training model {i+1}/{len(self.models)}: {model.name}")
            model.fit(X_train, y_train, **kwargs)
        
        self.is_trained = all(m.is_trained for m in self.models)
        return self
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Get ensemble predictions."""
        if not self.is_trained:
            raise ModelInferenceError("Ensemble not trained")
        
        try:
            predictions = np.array([
                m.predict(X) for m in self.models
            ])
            
            # Weighted average + argmax
            weighted_pred = np.average(predictions, axis=0, weights=self.weights)
            return np.round(weighted_pred).astype(int) - 1  # Convert to -1,0,1
        
        except Exception as e:
            raise ModelInferenceError(f"Ensemble prediction failed: {e}")
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Get ensemble probabilities."""
        if not self.is_trained:
            raise ModelInferenceError("Ensemble not trained")
        
        try:
            probas = np.array([
                m.predict_proba(X) for m in self.models
            ])
            
            # Weighted average across models
            return np.average(probas, axis=0, weights=self.weights)
        
        except Exception as e:
            raise ModelInferenceError(f"Ensemble probability failed: {e}")
    
    def set_weights(self, weights: List[float]) -> None:
        """Set ensemble weights."""
        if len(weights) != len(self.models):
            raise ValueError(f"Expected {len(self.models)} weights, got {len(weights)}")
        
        # Normalize weights
        total = sum(weights)
        self.weights = [w / total for w in weights]


# ═══════════════════════════════════════════════════════════════════════════
# META MODEL (STACKING)
# ═══════════════════════════════════════════════════════════════════════════

class MetaModel(BaseModel):
    """Meta learner for stacking ensemble."""
    
    def __init__(
        self,
        name: str = "meta_model",
        base_models: Optional[List[BaseModel]] = None,
        meta_learner: Optional[BaseModel] = None
    ):
        """Initialize meta model."""
        super().__init__(name)
        self.base_models = base_models or []
        self.meta_learner = meta_learner or LightGBMModel("meta_lgb")
        self.is_trained_base = False
    
    def fit(self, X_train: pd.DataFrame, y_train: pd.Series, **kwargs) -> 'MetaModel':
        """Train stacking model."""
        try:
            # Train base models
            logger.info(f"Training {len(self.base_models)} base models")
            for i, model in enumerate(self.base_models):
                logger.info(f"  Base model {i+1}/{len(self.base_models)}: {model.name}")
                model.fit(X_train, y_train, **kwargs)
            
            self.is_trained_base = all(m.is_trained for m in self.base_models)
            
            # Generate meta features from base models
            logger.info("Generating meta features")
            meta_features = np.concatenate([
                m.predict_proba(X_train) for m in self.base_models
            ], axis=1)
            
            meta_df = pd.DataFrame(
                meta_features,
                columns=[f"base_{i}_class_{j}" for i in range(len(self.base_models))
                        for j in range(meta_features.shape[1] // len(self.base_models))]
            )
            
            # Train meta learner
            logger.info("Training meta learner")
            self.meta_learner.fit(meta_df, y_train, **kwargs)
            
            self.is_trained = self.is_trained_base and self.meta_learner.is_trained
            logger.info(f"Trained {self.name} successfully")
            
            return self
        
        except Exception as e:
            raise ModelTrainingError(f"Meta model training failed: {e}")
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Get meta model predictions."""
        if not self.is_trained:
            raise ModelInferenceError("Meta model not trained")
        
        try:
            # Get base predictions
            meta_features = np.concatenate([
                m.predict_proba(X) for m in self.base_models
            ], axis=1)
            
            meta_df = pd.DataFrame(meta_features)
            
            # Meta learner prediction
            return self.meta_learner.predict(meta_df)
        
        except Exception as e:
            raise ModelInferenceError(f"Meta prediction failed: {e}")
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Get meta model probabilities."""
        if not self.is_trained:
            raise ModelInferenceError("Meta model not trained")
        
        try:
            # Get base predictions
            meta_features = np.concatenate([
                m.predict_proba(X) for m in self.base_models
            ], axis=1)
            
            meta_df = pd.DataFrame(meta_features)
            
            # Meta learner probabilities
            return self.meta_learner.predict_proba(meta_df)
        
        except Exception as e:
            raise ModelInferenceError(f"Meta probability failed: {e}")


# ═══════════════════════════════════════════════════════════════════════════
# MODEL CALIBRATION
# ═══════════════════════════════════════════════════════════════════════════

class IsotonicCalibrator(BaseModel):
    """Isotonic regression calibration."""
    
    def __init__(self, name: str = "isotonic_calibrator"):
        """Initialize calibrator."""
        super().__init__(name)
        self.calibrator = None
    
    def fit(self, y_true: np.ndarray, y_pred: np.ndarray, **kwargs) -> 'IsotonicCalibrator':
        """Train calibrator."""
        try:
            from sklearn.isotonic import IsotonicRegression
            
            self.calibrator = IsotonicRegression(out_of_bounds='clip')
            self.calibrator.fit(y_pred, y_true)
            
            self.is_trained = True
            logger.info("Trained isotonic calibrator")
            
            return self
        
        except ImportError:
            raise ModelTrainingError("scikit-learn not installed")
        except Exception as e:
            raise ModelTrainingError(f"Calibration failed: {e}")
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Not implemented for calibrator."""
        raise NotImplementedError("Use predict_proba for calibrator")
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Calibrate probabilities."""
        if not self.is_trained or self.calibrator is None:
            raise ModelInferenceError("Calibrator not trained")
        
        try:
            return self.calibrator.predict(X)
        except Exception as e:
            raise ModelInferenceError(f"Calibration failed: {e}")


# ═══════════════════════════════════════════════════════════════════════════
# MODEL UTILITIES
# ═══════════════════════════════════════════════════════════════════════════

def calculate_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_proba: Optional[np.ndarray] = None
) -> ModelMetrics:
    """Calculate model performance metrics."""
    try:
        from sklearn.metrics import (
            accuracy_score, precision_score, recall_score,
            f1_score, roc_auc_score
        )
        
        metrics = ModelMetrics()
        
        # Classification metrics
        metrics.accuracy = accuracy_score(y_true, y_pred)
        metrics.precision = precision_score(y_true, y_pred, average='weighted', zero_division=0)
        metrics.recall = recall_score(y_true, y_pred, average='weighted', zero_division=0)
        metrics.f1_score = f1_score(y_true, y_pred, average='weighted', zero_division=0)
        
        # ROC AUC (if probabilities available)
        if y_proba is not None:
            try:
                # Convert to binary for ROC AUC (use class 1 vs rest)
                y_binary = (y_true > -1).astype(int)
                metrics.roc_auc = roc_auc_score(y_binary, y_proba[:, 1] if y_proba.shape[1] > 1 else y_proba[:, 0])
            except:
                metrics.roc_auc = 0.0
        
        logger.info(f"Calculated metrics: accuracy={metrics.accuracy:.4f}, f1={metrics.f1_score:.4f}")
        
        return metrics
    
    except Exception as e:
        logger.error(f"Metrics calculation failed: {e}")
        return ModelMetrics()


def get_feature_importance(model: BaseModel, feature_names: List[str]) -> Dict[str, float]:
    """Extract feature importance from model."""
    try:
        if hasattr(model, 'model') and hasattr(model.model, 'feature_importance'):
            importances = model.model.feature_importance()
            return dict(zip(feature_names, importances))
        else:
            logger.warning(f"Model {model.name} doesn't support feature importance")
            return {}
    
    except Exception as e:
        logger.error(f"Feature importance extraction failed: {e}")
        return {}


# ═══════════════════════════════════════════════════════════════════════════
# EXPORTS
# ═══════════════════════════════════════════════════════════════════════════

__all__ = [
    # Classes
    'BaseModel', 'LightGBMModel', 'EnsembleModel', 'MetaModel',
    'IsotonicCalibrator', 'PredictionResult', 'ModelMetrics',
    
    # Exceptions
    'ModelError', 'ModelInferenceError', 'ModelTrainingError', 'ModelValidationError',
    
    # Functions
    'calculate_metrics', 'get_feature_importance',
]
