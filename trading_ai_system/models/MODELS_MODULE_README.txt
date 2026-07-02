═══════════════════════════════════════════════════════════════════════════
MODELS MODULE - trading_ai_system.models
═══════════════════════════════════════════════════════════════════════════

FILE: trading_ai_system/models/__init__.py (or models.py as standalone)
SIZE: 479 lines
SYNTAX: ✓ Valid

PURPOSE:
═════════
Machine learning models, ensemble methods, and prediction infrastructure.
Complete ML pipeline for:
  • Model training and inference
  • Ensemble learning (voting & stacking)
  • Probability calibration
  • Performance metrics
  • Feature importance


MODULES INCLUDED:
════════════════

1. EXCEPTION CLASSES
   • ModelInferenceError - Prediction error
   • ModelTrainingError - Training error
   • ModelValidationError - Validation error

2. DATA CLASSES
   
   @dataclass PredictionResult:
     - prediction (-1, 0, 1)
     - probability (confidence 0-1)
     - timestamp, model_name
     - metadata (dict)
     Methods: to_dict()
   
   @dataclass ModelMetrics:
     - accuracy, precision, recall, f1_score
     - roc_auc, sharpe_ratio, max_drawdown
     - win_rate
     Methods: to_dict()

3. BASE MODEL INTERFACE
   class BaseModel (ABC):
     • fit(X_train, y_train, **kwargs)
     • predict(X) → np.ndarray
     • predict_proba(X) → np.ndarray
     • set_metrics(), get_metrics()

4. LIGHTGBM MODEL
   class LightGBMModel(BaseModel):
     - Wrapper around LightGBM
     - Multi-class (3 classes: -1, 0, 1)
     - Methods: fit(), predict(), predict_proba()
     
     Parameters:
     • objective='multiclass'
     • num_class=3
     • learning_rate=0.05
     • num_leaves=31
     • max_depth=7

5. ENSEMBLE MODEL (VOTING)
   class EnsembleModel(BaseModel):
     - Weighted voting ensemble
     - Combines multiple models
     
     Methods:
     • add_model(model)
     • fit(X_train, y_train)
     • predict(X)
     • predict_proba(X)
     • set_weights(weights)
     
     Prediction: weighted average + argmax

6. META MODEL (STACKING)
   class MetaModel(BaseModel):
     - Stacking ensemble with meta-learner
     - Base models + meta learner
     
     Methods:
     • fit(X_train, y_train)
     • predict(X)
     • predict_proba(X)
     
     Process:
     1. Train base models
     2. Get base model probabilities
     3. Stack as meta features
     4. Train meta learner on stacked features

7. ISOTONIC CALIBRATION
   class IsotonicCalibrator(BaseModel):
     - Probability calibration
     - Uses isotonic regression
     
     Methods:
     • fit(y_true, y_pred)
     • predict_proba(X) - calibrated probabilities

8. MODEL UTILITIES
   
   calculate_metrics(y_true, y_pred, y_proba)
     Returns: ModelMetrics
     • accuracy, precision, recall, f1
     • roc_auc (if proba available)
   
   get_feature_importance(model, feature_names)
     Returns: Dict[feature_name, importance]


USAGE EXAMPLES:
═══════════════

# Single Model
from trading_ai_system.models import LightGBMModel, calculate_metrics

model = LightGBMModel(name="main_model")
model.fit(X_train, y_train, num_boost_round=100)

y_pred = model.predict(X_test)
y_proba = model.predict_proba(X_test)

metrics = calculate_metrics(y_test, y_pred, y_proba)
print(f"Accuracy: {metrics.accuracy:.4f}")
print(f"F1 Score: {metrics.f1_score:.4f}")

# Ensemble (Voting)
from trading_ai_system.models import EnsembleModel

ensemble = EnsembleModel(name="voting_ensemble")
ensemble.add_model(LightGBMModel("model_1"))
ensemble.add_model(LightGBMModel("model_2"))
ensemble.add_model(LightGBMModel("model_3"))

ensemble.fit(X_train, y_train)
ensemble.set_weights([0.5, 0.3, 0.2])  # Unequal weights

y_pred = ensemble.predict(X_test)

# Stacking Ensemble
from trading_ai_system.models import MetaModel

base_models = [
    LightGBMModel("lgb_1"),
    LightGBMModel("lgb_2"),
    LightGBMModel("xgb_3")
]

meta = MetaModel(
    name="stacking_ensemble",
    base_models=base_models,
    meta_learner=LightGBMModel("meta_lgb")
)

meta.fit(X_train, y_train)
y_pred = meta.predict(X_test)
y_proba = meta.predict_proba(X_test)

# Probability Calibration
from trading_ai_system.models import IsotonicCalibrator

calibrator = IsotonicCalibrator()
calibrator.fit(y_val, y_val_proba[:, 0])

y_test_calibrated = calibrator.predict_proba(y_test_proba[:, 0])

# Feature Importance
from trading_ai_system.models import get_feature_importance

importance = get_feature_importance(model, feature_names)
for feat, imp in sorted(importance.items(), key=lambda x: x[1], reverse=True)[:10]:
    print(f"{feat}: {imp:.4f}")


PREDICTION CLASSES:
════════════════════

Output is 3-class prediction:
  -1: SELL signal
   0: HOLD signal
   1: BUY signal

Probability output shape: (n_samples, 3)
  proba[:, 0] = P(SELL)
  proba[:, 1] = P(HOLD)
  proba[:, 2] = P(BUY)


ENSEMBLE VOTING PROCESS:
═════════════════════════

Multiple models make predictions:
  Model 1: proba = [0.3, 0.4, 0.3]
  Model 2: proba = [0.2, 0.5, 0.3]
  Model 3: proba = [0.4, 0.3, 0.3]

Weighted average (weights=[0.5, 0.3, 0.2]):
  avg_proba = (0.5*[0.3, 0.4, 0.3] +
               0.3*[0.2, 0.5, 0.3] +
               0.2*[0.4, 0.3, 0.3])
            = [0.30, 0.41, 0.29]

Final prediction: argmax(avg_proba) = 1 (BUY)


STACKING PROCESS:
═════════════════

1. Base Model Training
   ├─ Model 1 (LightGBM): fit(X_train, y_train)
   ├─ Model 2 (LightGBM): fit(X_train, y_train)
   └─ Model 3 (LightGBM): fit(X_train, y_train)

2. Meta Feature Generation
   ├─ model1_proba = Model1.predict_proba(X_train) [n, 3]
   ├─ model2_proba = Model2.predict_proba(X_train) [n, 3]
   └─ model3_proba = Model3.predict_proba(X_train) [n, 3]
   
   meta_features = concat([model1, model2, model3]) [n, 9]

3. Meta Learner Training
   MetaLearner.fit(meta_features, y_train)

4. Inference
   base_probas = [Model1.predict_proba(X_test),
                  Model2.predict_proba(X_test),
                  Model3.predict_proba(X_test)]
   meta_features = concat(base_probas)
   y_pred = MetaLearner.predict(meta_features)


PERFORMANCE METRICS:
═════════════════════

Calculated by calculate_metrics():

Classification Metrics:
  • Accuracy: (TP + TN) / Total
  • Precision: TP / (TP + FP) [per class, weighted]
  • Recall: TP / (TP + FN) [per class, weighted]
  • F1 Score: 2 * (Precision * Recall) / (Precision + Recall)

Ranking Metric:
  • ROC AUC: Area under ROC curve (binary: class 1 vs rest)

Trading Metrics (optional):
  • Sharpe Ratio: (Return - Risk-free) / StdDev
  • Max Drawdown: Peak-to-trough decline
  • Win Rate: Profitable trades / Total trades


FEATURE IMPORTANCE:
════════════════════

Available from LightGBM:
  importance = get_feature_importance(model, feature_names)
  
  Returns: Dict[str, float]
  Example:
  {
    "rsi_14": 0.150,
    "macd": 0.120,
    "bb_width": 0.095,
    "atr_14": 0.085,
    ...
  }

Sum of importances ≈ 1.0 (relative)


CALIBRATION PROCESS:
═════════════════════

Raw Model Predictions:
  [0.2, 0.5, 0.3, ...]  (uncalibrated probabilities)

Isotonic Regression:
  fit(y_val, y_raw_proba)  (on validation set)

Calibrated Predictions:
  [0.25, 0.48, 0.27, ...]  (better calibrated)

Benefits:
  • Better probability estimates
  • Improved confidence scores
  • More reliable decision thresholds


INTEGRATION WITH OTHER MODULES:
════════════════════════════════

features/ module:
  ✓ Provides feature vectors (X_train, X_test)
  ✓ Feature names for importance analysis

data/ module:
  ✓ Provides cleaned training/test data
  ✓ Quality validation

strategy/ module:
  ✓ Uses model predictions for signals
  ✓ Uses probability for confidence filtering

live/ module:
  ✓ Uses predict_proba for position sizing
  ✓ Uses predictions for entry/exit

risk/ module:
  ✓ Monitors model performance drift
  ✓ Triggers retraining if needed


ERROR HANDLING:
════════════════

try:
    model = LightGBMModel()
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    
except ModelTrainingError as e:
    logger.error(f"Training failed: {e}")
    
except ModelInferenceError as e:
    logger.error(f"Prediction failed: {e}")


EXTENDING THE MODELS MODULE:
══════════════════════════════

To add new model type:
  1. Inherit from BaseModel
  2. Implement fit(), predict(), predict_proba()
  3. Call set_metrics() after training

Example - Add XGBoost:
  class XGBoostModel(BaseModel):
      def fit(self, X_train, y_train, **kwargs):
          import xgboost as xgb
          self.model = xgb.XGBClassifier(...)
          self.model.fit(X_train, y_train)
          self.is_trained = True
          return self
      
      def predict(self, X):
          return self.model.predict(X)
      
      def predict_proba(self, X):
          return self.model.predict_proba(X)

To add custom ensemble:
  1. Inherit from BaseModel
  2. Store base models
  3. Combine predictions via custom logic


PERFORMANCE NOTES:
═══════════════════

Training Time:
  • Single LightGBM: 1-10s (depending on data size)
  • Ensemble (3 models): 3-30s
  • Stacking (3 base + meta): 5-40s

Inference Time:
  • Single model: <1ms per sample
  • Ensemble (3 models): <3ms
  • Stacking: <5ms

Memory Usage:
  • Model object: 10-100MB
  • Ensemble (3 models): 30-300MB


REQUIRED IMPORTS:
═════════════════

From core:
  logger, ModelError

Standard Library:
  logging, typing, abc, dataclasses

Third-Party:
  numpy, pandas
  lightgbm (for LightGBMModel)
  scikit-learn (for metrics, calibration)

═══════════════════════════════════════════════════════════════════════════
