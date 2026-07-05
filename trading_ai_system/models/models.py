"""
Trading AI System - Models Module
Machine learning models, ensemble methods, and prediction infrastructure.

v79.2 Enhancements:
- Thread-safe model management
- Better error handling for optional dependencies
- Model versioning and checkpointing
- Cross-validation support
- Advanced ensemble techniques
- Feature importance analysis
- Indicator discovery integration
"""

import sys
import logging
from typing import Dict, Any, Optional, Tuple, List, Union
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from threading import RLock
import json
from datetime import datetime, timezone

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

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


@dataclass
class FeatureImportance:
    """Feature importance analysis result"""
    feature_name: str
    importance_score: float
    normalized_score: float = 0.0
    rank: int = 0
    category: str = ""
    discovered: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "feature_name": self.feature_name,
            "importance_score": self.importance_score,
            "normalized_score": self.normalized_score,
            "rank": self.rank,
            "category": self.category,
            "discovered": self.discovered
        }


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


@dataclass
class PredictionResult:
    """Model prediction result."""
    prediction: int
    probability: float
    timestamp: Optional[datetime] = None
    model_name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "prediction": self.prediction,
            "probability": self.probability,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
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
    profit_factor: float = 0.0
    feature_importance: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "accuracy": self.accuracy,
            "precision": self.precision,
            "recall": self.recall,
            "f1_score": self.f1_score,
            "roc_auc": self.roc_auc,
            "sharpe_ratio": self.sharpe_ratio,
            "max_drawdown": self.max_drawdown,
            "win_rate": self.win_rate,
            "profit_factor": self.profit_factor,
            "feature_importance": self.feature_importance,
        }
    
    def is_valid(self) -> bool:
        """Check if metrics are valid."""
        return (0 <= self.accuracy <= 1 and 
                0 <= self.precision <= 1 and 
                0 <= self.recall <= 1)


@dataclass
class ModelCheckpoint:
    """Model checkpoint/version."""
    timestamp: datetime
    version: str
    metrics: ModelMetrics
    params: Dict[str, Any] = field(default_factory=dict)
    feature_importance: Dict[str, FeatureImportance] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "version": self.version,
            "metrics": self.metrics.to_dict(),
            "params": self.params,
            "feature_importance": {k: v.to_dict() for k, v in self.feature_importance.items()},
        }


class BaseModel(ABC):
    """Abstract base class for all models."""
    
    def __init__(self, name: str, version: str = "1.0"):
        """Initialize model."""
        self.name = name
        self.version = version
        self.is_trained = False
        self.metrics = ModelMetrics()
        self.checkpoints: List[ModelCheckpoint] = []
        self.feature_importance: Dict[str, FeatureImportance] = {}
        self._lock = RLock()
        self.training_history: Dict[str, List] = {
            "loss": [],
            "accuracy": [],
        }
    
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
        with self._lock:
            self.metrics = metrics
    
    def get_metrics(self) -> ModelMetrics:
        """Get model metrics."""
        with self._lock:
            return self.metrics
    
    def set_feature_importance(self, feature_importance: Dict[str, float]) -> None:
        """Set feature importance."""
        with self._lock:
            self.feature_importance = {}
            total = sum(feature_importance.values()) if feature_importance else 1.0
            for rank, (feat_name, importance) in enumerate(
                sorted(feature_importance.items(), key=lambda x: x[1], reverse=True), 1
            ):
                self.feature_importance[feat_name] = FeatureImportance(
                    feature_name=feat_name,
                    importance_score=importance,
                    normalized_score=importance / total if total > 0 else 0,
                    rank=rank
                )
    
    def get_feature_importance(self) -> Dict[str, FeatureImportance]:
        """Get feature importance."""
        with self._lock:
            return self.feature_importance.copy()
    
    def get_top_features(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """Get top N most important features."""
        with self._lock:
            sorted_features = sorted(
                self.feature_importance.values(),
                key=lambda x: x.importance_score,
                reverse=True
            )
            return [f.to_dict() for f in sorted_features[:top_n]]
    
    def create_checkpoint(self, metrics: Optional[ModelMetrics] = None) -> ModelCheckpoint:
        """Create model checkpoint."""
        checkpoint = ModelCheckpoint(
            timestamp=datetime.now(timezone.utc),
            version=self.version,
            metrics=metrics or self.metrics,
            feature_importance=self.feature_importance.copy()
        )
        with self._lock:
            self.checkpoints.append(checkpoint)
        logger.info(f"Checkpoint created for {self.name} v{self.version}")
        return checkpoint
    
    def get_best_checkpoint(self) -> Optional[ModelCheckpoint]:
        """Get best checkpoint by F1 score."""
        with self._lock:
            if not self.checkpoints:
                return None
            return max(self.checkpoints, key=lambda c: c.metrics.f1_score)
    
    def add_training_history(self, epoch: int, loss: float, accuracy: float) -> None:
        """Add training history."""
        with self._lock:
            self.training_history["loss"].append(loss)
            self.training_history["accuracy"].append(accuracy)


class LightGBMModel(BaseModel):
    """LightGBM model wrapper."""
    
    def __init__(self, name: str = "lgb_model", version: str = "1.0", **kwargs):
        """Initialize LightGBM model."""
        super().__init__(name, version)
        self.model = None
        self.params = kwargs
        self._lgb = None
        self._init_lgb()
    
    def _init_lgb(self) -> None:
        """Initialize LightGBM safely."""
        try:
            import lightgbm as lgb
            self._lgb = lgb
        except ImportError:
            logger.warning("LightGBM not installed")
    
    def fit(self, X_train: pd.DataFrame, y_train: pd.Series, **kwargs) -> 'LightGBMModel':
        """Train LightGBM model."""
        if self._lgb is None:
            raise ModelTrainingError("LightGBM not installed")
        
        try:
            with self._lock:
                params = {
                    'objective': 'multiclass',
                    'num_class': 3,
                    'learning_rate': 0.05,
                    'num_leaves': 31,
                    'max_depth': 7,
                    'verbose': -1,
                }
                params.update(self.params)
                
                train_data = self._lgb.Dataset(X_train, label=y_train)
                
                self.model = self._lgb.train(
                    params,
                    train_data,
                    num_boost_round=100,
                    **kwargs
                )
                
                importances = self.model.feature_importance()
                feature_importance = dict(zip(X_train.columns, importances))
                self.set_feature_importance(feature_importance)
                
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
            with self._lock:
                proba = self.model.predict(X, num_iteration=self.model.best_iteration)
                return np.argmax(proba, axis=1) - 1
        except Exception as e:
            raise ModelInferenceError(f"Prediction failed: {e}")
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Get prediction probabilities."""
        if not self.is_trained or self.model is None:
            raise ModelInferenceError("Model not trained")
        
        try:
            with self._lock:
                return self.model.predict(X, num_iteration=self.model.best_iteration)
        except Exception as e:
            raise ModelInferenceError(f"Probability prediction failed: {e}")


class EnsembleModel(BaseModel):
    """Ensemble of multiple models."""
    
    def __init__(self, name: str = "ensemble", models: Optional[List[BaseModel]] = None, version: str = "1.0"):
        """Initialize ensemble."""
        super().__init__(name, version)
        self.models = models or []
        self.weights = [1.0 / len(self.models)] if self.models else []
    
    def fit(self, X_train: pd.DataFrame, y_train: pd.Series, **kwargs) -> 'EnsembleModel':
        """Train all ensemble models."""
        try:
            with self._lock:
                logger.info(f"Training {len(self.models)} models in ensemble")
                for i, model in enumerate(self.models):
                    logger.info(f"  Model {i+1}/{len(self.models)}: {model.name}")
                    model.fit(X_train, y_train, **kwargs)
                
                self.is_trained = all(m.is_trained for m in self.models)
                
                ensemble_importance = {}
                for model in self.models:
                    for feat, importance_obj in model.feature_importance.items():
                        if feat not in ensemble_importance:
                            ensemble_importance[feat] = 0
                        ensemble_importance[feat] += importance_obj.importance_score
                
                for feat in ensemble_importance:
                    ensemble_importance[feat] /= len(self.models)
                
                self.set_feature_importance(ensemble_importance)
                
                logger.info(f"Ensemble {self.name} trained")
            
            return self
        
        except Exception as e:
            raise ModelTrainingError(f"Ensemble training failed: {e}")
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Get ensemble predictions."""
        if not self.is_trained:
            raise ModelInferenceError("Ensemble not trained")
        
        try:
            with self._lock:
                preds = np.array([m.predict(X) for m in self.models])
                return np.apply_along_axis(
                    lambda x: np.argmax(np.bincount(x.astype(int))),
                    axis=0,
                    arr=preds
                )
        
        except Exception as e:
            raise ModelInferenceError(f"Ensemble prediction failed: {e}")
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Get ensemble probabilities."""
        if not self.is_trained:
            raise ModelInferenceError("Ensemble not trained")
        
        try:
            with self._lock:
                probas = np.array([m.predict_proba(X) for m in self.models])
                return np.average(probas, axis=0, weights=self.weights)
        
        except Exception as e:
            raise ModelInferenceError(f"Ensemble probability failed: {e}")
    
    def set_weights(self, weights: List[float]) -> None:
        """Set ensemble weights."""
        if len(weights) != len(self.models):
            raise ValueError(f"Expected {len(self.models)} weights")
        
        with self._lock:
            total = sum(weights)
            self.weights = [w / total for w in weights]


class MetaModel(BaseModel):
    """Meta learner for stacking ensemble."""
    
    def __init__(
        self,
        name: str = "meta_model",
        base_models: Optional[List[BaseModel]] = None,
        meta_learner: Optional[BaseModel] = None,
        version: str = "1.0"
    ):
        """Initialize meta model."""
        super().__init__(name, version)
        self.base_models = base_models or []
        self.meta_learner = meta_learner or LightGBMModel("meta_lgb")
        self.is_trained_base = False
    
    def fit(self, X_train: pd.DataFrame, y_train: pd.Series, **kwargs) -> 'MetaModel':
        """Train stacking model."""
        try:
            with self._lock:
                logger.info(f"Training {len(self.base_models)} base models")
                for i, model in enumerate(self.base_models):
                    logger.info(f"  Base model {i+1}: {model.name}")
                    model.fit(X_train, y_train, **kwargs)
                
                self.is_trained_base = all(m.is_trained for m in self.base_models)
                
                logger.info("Generating meta features")
                meta_features = np.concatenate(
                    [m.predict_proba(X_train) for m in self.base_models],
                    axis=1
                )
                
                meta_df = pd.DataFrame(meta_features)
                
                logger.info("Training meta learner")
                self.meta_learner.fit(meta_df, y_train, **kwargs)
                
                self.feature_importance = self.meta_learner.feature_importance.copy()
                
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
            with self._lock:
                meta_features = np.concatenate(
                    [m.predict_proba(X) for m in self.base_models],
                    axis=1
                )
                meta_df = pd.DataFrame(meta_features)
                return self.meta_learner.predict(meta_df)
        
        except Exception as e:
            raise ModelInferenceError(f"Meta prediction failed: {e}")
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Get meta model probabilities."""
        if not self.is_trained:
            raise ModelInferenceError("Meta model not trained")
        
        try:
            with self._lock:
                meta_features = np.concatenate(
                    [m.predict_proba(X) for m in self.base_models],
                    axis=1
                )
                meta_df = pd.DataFrame(meta_features)
                return self.meta_learner.predict_proba(meta_df)
        
        except Exception as e:
            raise ModelInferenceError(f"Meta probability failed: {e}")


class IsotonicCalibrator(BaseModel):
    """Isotonic regression calibration."""
    
    def __init__(self, name: str = "isotonic_calibrator", version: str = "1.0"):
        """Initialize calibrator."""
        super().__init__(name, version)
        self.calibrator = None
    
    def fit(self, y_true: np.ndarray, y_pred: np.ndarray, **kwargs) -> 'IsotonicCalibrator':
        """Train calibrator."""
        try:
            from sklearn.isotonic import IsotonicRegression
            
            with self._lock:
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
        raise NotImplementedError("Use predict_proba")
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Calibrate probabilities."""
        if not self.is_trained or self.calibrator is None:
            raise ModelInferenceError("Calibrator not trained")
        
        try:
            with self._lock:
                return self.calibrator.predict(X)
        except Exception as e:
            raise ModelInferenceError(f"Calibration failed: {e}")


def calculate_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_proba: Optional[np.ndarray] = None,
    feature_importance: Optional[Dict[str, float]] = None
) -> ModelMetrics:
    """Calculate model performance metrics."""
    try:
        from sklearn.metrics import (
            accuracy_score, precision_score, recall_score,
            f1_score, roc_auc_score
        )
        
        metrics = ModelMetrics()
        metrics.accuracy = float(accuracy_score(y_true, y_pred))
        metrics.precision = float(precision_score(y_true, y_pred, average='weighted', zero_division=0))
        metrics.recall = float(recall_score(y_true, y_pred, average='weighted', zero_division=0))
        metrics.f1_score = float(f1_score(y_true, y_pred, average='weighted', zero_division=0))
        
        if y_proba is not None:
            try:
                y_binary = (y_true > -1).astype(int)
                metrics.roc_auc = float(roc_auc_score(
                    y_binary,
                    y_proba[:, 1] if y_proba.shape[1] > 1 else y_proba[:, 0]
                ))
            except:
                metrics.roc_auc = 0.0
        
        if feature_importance:
            metrics.feature_importance = feature_importance.copy()
        
        logger.info(f"Metrics: accuracy={metrics.accuracy:.4f}, f1={metrics.f1_score:.4f}")
        return metrics
    
    except Exception as e:
        logger.error(f"Metrics calculation failed: {e}")
        return ModelMetrics()


def get_feature_importance(model: BaseModel, feature_names: List[str]) -> Dict[str, float]:
    """Extract feature importance from model."""
    try:
        importance_dict = {}
        
        if hasattr(model, 'feature_importance') and model.feature_importance:
            return {
                feat: imp_obj.importance_score
                for feat, imp_obj in model.feature_importance.items()
            }
        
        if hasattr(model, 'model') and hasattr(model.model, 'feature_importance'):
            importances = model.model.feature_importance()
            if len(importances) == len(feature_names):
                return dict(zip(feature_names, importances))
        
        logger.warning(f"Model {model.name} doesn't support feature importance")
        return {}
    
    except Exception as e:
        logger.error(f"Feature importance extraction failed: {e}")
        return {}


def get_discovered_features(feature_importance: Dict[str, FeatureImportance]) -> List[Dict[str, Any]]:
    """Get discovered high-importance features."""
    discovered = [
        {
            'name': feat.feature_name,
            'score': feat.importance_score,
            'normalized': feat.normalized_score,
            'rank': feat.rank
        }
        for feat in feature_importance.values()
        if feat.discovered or feat.normalized_score > 0.05
    ]
    return sorted(discovered, key=lambda x: x['score'], reverse=True)


__all__ = [
    'BaseModel',
    'LightGBMModel',
    'EnsembleModel',
    'MetaModel',
    'IsotonicCalibrator',
    'PredictionResult',
    'ModelMetrics',
    'ModelCheckpoint',
    'FeatureImportance',
    'ModelError',
    'ModelInferenceError',
    'ModelTrainingError',
    'ModelValidationError',
    'calculate_metrics',
    'get_feature_importance',
    'get_discovered_features',
]
