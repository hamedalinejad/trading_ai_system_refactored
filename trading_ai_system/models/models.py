"""
Trading AI System - Models Module (v79.3)
ML models, ensemble methods, prediction infrastructure with discovery integration.
"""

import sys
import logging
from typing import Dict, Any, Optional, Tuple, List, Union
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from threading import RLock
import json
from datetime import datetime, timezone
from pathlib import Path

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
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)


class ModelError(TradingSystemError):
    pass


class ModelInferenceError(ModelError):
    pass


class ModelTrainingError(ModelError):
    pass


class ModelValidationError(ModelError):
    pass


@dataclass
class PredictionResult:
    prediction: int
    probability: float
    timestamp: Optional[datetime] = None
    model_name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "prediction": self.prediction,
            "probability": self.probability,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "model_name": self.model_name,
            "metadata": self.metadata
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)


@dataclass
class ModelMetrics:
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
        return (0 <= self.accuracy <= 1 and 
                0 <= self.precision <= 1 and 
                0 <= self.recall <= 1)


@dataclass
class ModelCheckpoint:
    timestamp: datetime
    version: str
    metrics: ModelMetrics
    params: Dict[str, Any] = field(default_factory=dict)
    feature_importance: Dict[str, FeatureImportance] = field(default_factory=dict)
    discovered_features: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "version": self.version,
            "metrics": self.metrics.to_dict(),
            "params": self.params,
            "feature_importance": {k: v.to_dict() for k, v in self.feature_importance.items()},
            "discovered_features": self.discovered_features,
        }


class BaseModel(ABC):
    def __init__(self, name: str, version: str = "1.0"):
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
        pass
    
    @abstractmethod
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        pass
    
    @abstractmethod
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        pass
    
    def set_metrics(self, metrics: ModelMetrics) -> None:
        with self._lock:
            self.metrics = metrics
    
    def get_metrics(self) -> ModelMetrics:
        with self._lock:
            return self.metrics
    
    def set_feature_importance(self, feature_importance: Dict[str, float]) -> None:
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
        with self._lock:
            return self.feature_importance.copy()
    
    def get_top_features(self, top_n: int = 10) -> List[Dict[str, Any]]:
        with self._lock:
            sorted_features = sorted(
                self.feature_importance.values(),
                key=lambda x: x.importance_score,
                reverse=True
            )
            return [f.to_dict() for f in sorted_features[:top_n]]
    
    def sync_with_discovery(self, discovered_features: List[Dict[str, Any]], top_n: int = 20) -> None:
        """Mark features discovered by discovery module"""
        with self._lock:
            discovered_names = {f['name'] for f in discovered_features[:top_n]}
            for feat_name, feat_obj in self.feature_importance.items():
                if feat_name in discovered_names:
                    feat_obj.discovered = True
                    for disc_feat in discovered_features:
                        if disc_feat['name'] == feat_name:
                            feat_obj.category = disc_feat.get('category', '')
                            break
    
    def create_checkpoint(self, metrics: Optional[ModelMetrics] = None, discovered_features: Optional[List[Dict[str, Any]]] = None) -> ModelCheckpoint:
        checkpoint = ModelCheckpoint(
            timestamp=datetime.now(timezone.utc),
            version=self.version,
            metrics=metrics or self.metrics,
            feature_importance=self.feature_importance.copy(),
            discovered_features=discovered_features or []
        )
        with self._lock:
            self.checkpoints.append(checkpoint)
        logger.info(f"Checkpoint created for {self.name} v{self.version}")
        return checkpoint
    
    def get_best_checkpoint(self) -> Optional[ModelCheckpoint]:
        with self._lock:
            if not self.checkpoints:
                return None
            return max(self.checkpoints, key=lambda c: c.metrics.f1_score)
    
    def add_training_history(self, epoch: int, loss: float, accuracy: float) -> None:
        with self._lock:
            self.training_history["loss"].append(loss)
            self.training_history["accuracy"].append(accuracy)
    
    def save(self, path: Union[str, Path]) -> None:
        """Save model to disk"""
        try:
            import joblib
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            joblib.dump(self, path)
            logger.info(f"Model saved to {path}")
        except ImportError:
            logger.error("joblib not installed for model serialization")
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
    
    @classmethod
    def load(cls, path: Union[str, Path]) -> 'BaseModel':
        """Load model from disk"""
        try:
            import joblib
            path = Path(path)
            model = joblib.load(path)
            logger.info(f"Model loaded from {path}")
            return model
        except ImportError:
            logger.error("joblib not installed for model deserialization")
        except FileNotFoundError:
            logger.error(f"Model file not found: {path}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
        return None


class LightGBMModel(BaseModel):
    def __init__(self, name: str = "lgb_model", version: str = "1.0", **kwargs):
        super().__init__(name, version)
        self.model = None
        self.params = kwargs
        self._lgb = None
        self._init_lgb()
    
    def _init_lgb(self) -> None:
        try:
            import lightgbm as lgb
            self._lgb = lgb
        except ImportError:
            logger.warning("LightGBM not installed")
    
    def fit(self, X_train: pd.DataFrame, y_train: pd.Series, **kwargs) -> 'LightGBMModel':
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
                
                importance_type = params.pop('importance_type', 'gain')
                
                train_data = self._lgb.Dataset(X_train, label=y_train)
                
                self.model = self._lgb.train(
                    params,
                    train_data,
                    num_boost_round=100,
                    **kwargs
                )
                
                importances = self.model.feature_importance(importance_type=importance_type)
                feature_importance = dict(zip(X_train.columns, importances))
                self.set_feature_importance(feature_importance)
                
                self.is_trained = True
                logger.info(f"Trained {self.name} on {len(X_train)} samples")
            
            return self
        
        except Exception as e:
            raise ModelTrainingError(f"Training failed: {e}")
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_trained or self.model is None:
            raise ModelInferenceError("Model not trained")
        
        try:
            with self._lock:
                proba = self.model.predict(X, num_iteration=self.model.best_iteration)
                return np.argmax(proba, axis=1) - 1
        except Exception as e:
            raise ModelInferenceError(f"Prediction failed: {e}")
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_trained or self.model is None:
            raise ModelInferenceError("Model not trained")
        
        try:
            with self._lock:
                return self.model.predict(X, num_iteration=self.model.best_iteration)
        except Exception as e:
            raise ModelInferenceError(f"Probability prediction failed: {e}")


class EnsembleModel(BaseModel):
    def __init__(self, name: str = "ensemble", models: Optional[List[BaseModel]] = None, version: str = "1.0"):
        super().__init__(name, version)
        self.models = models or []
        self.weights = [1.0 / len(self.models)] if self.models else []
    
    def fit(self, X_train: pd.DataFrame, y_train: pd.Series, **kwargs) -> 'EnsembleModel':
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
        if not self.is_trained:
            raise ModelInferenceError("Ensemble not trained")
        
        try:
            with self._lock:
                preds = np.array([m.predict(X) for m in self.models])
                
                voted = np.zeros(preds.shape[1], dtype=int)
                for i in range(preds.shape[1]):
                    votes = preds[:, i]
                    unique, counts = np.unique(votes, return_counts=True)
                    max_count = counts.max()
                    tied = unique[counts == max_count]
                    
                    if len(tied) == 1:
                        voted[i] = tied[0]
                    else:
                        probas = np.array([m.predict_proba(X.iloc[[i]]) for m in self.models])
                        avg_proba = probas.mean(axis=0).flatten()
                        voted[i] = np.argmax(avg_proba) - 1
                
                return voted
        
        except Exception as e:
            raise ModelInferenceError(f"Ensemble prediction failed: {e}")
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_trained:
            raise ModelInferenceError("Ensemble not trained")
        
        try:
            with self._lock:
                probas = np.array([m.predict_proba(X) for m in self.models])
                return np.average(probas, axis=0, weights=self.weights)
        
        except Exception as e:
            raise ModelInferenceError(f"Ensemble probability failed: {e}")
    
    def set_weights(self, weights: List[float]) -> None:
        if len(weights) != len(self.models):
            raise ValueError(f"Expected {len(self.models)} weights")
        
        with self._lock:
            total = sum(weights)
            self.weights = [w / total for w in weights]


class MetaModel(BaseModel):
    def __init__(
        self,
        name: str = "meta_model",
        base_models: Optional[List[BaseModel]] = None,
        meta_learner: Optional[BaseModel] = None,
        version: str = "1.0"
    ):
        super().__init__(name, version)
        self.base_models = base_models or []
        self.meta_learner = meta_learner or LightGBMModel("meta_lgb")
        self.is_trained_base = False
    
    def fit(self, X_train: pd.DataFrame, y_train: pd.Series, **kwargs) -> 'MetaModel':
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
    def __init__(self, name: str = "isotonic_calibrator", version: str = "1.0"):
        super().__init__(name, version)
        self.calibrator = None
    
    def fit(self, X_train: pd.DataFrame, y_train: pd.Series, **kwargs) -> 'IsotonicCalibrator':
        """
        Fit calibrator with model predictions and true labels.
        X_train should contain model predictions, y_train contains true labels.
        """
        try:
            from sklearn.isotonic import IsotonicRegression
            
            y_pred = X_train.values.flatten() if isinstance(X_train, pd.DataFrame) else X_train
            
            with self._lock:
                self.calibrator = IsotonicRegression(out_of_bounds='clip')
                self.calibrator.fit(y_pred, y_train)
                self.is_trained = True
                logger.info("Trained isotonic calibrator")
            
            return self
        
        except ImportError:
            raise ModelTrainingError("scikit-learn not installed")
        except Exception as e:
            raise ModelTrainingError(f"Calibration failed: {e}")
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        raise NotImplementedError("Use predict_proba")
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
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
    discovered = [
        {
            'name': feat.feature_name,
            'score': feat.importance_score,
            'normalized': feat.normalized_score,
            'rank': feat.rank,
            'category': feat.category,
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
