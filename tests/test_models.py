# tests/test_models.py
"""
تست‌های Models Module
"""

import pytest
import numpy as np
import pandas as pd


class TestLGBModel:
    """تست‌های LightGBM Model"""

    def test_lgb_model_initialization(self):
        """تست Initialization LGB Model"""
        from trading_ai_system.models import LGBModel
        
        model = LGBModel(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=5
        )
        assert model is not None

    def test_lgb_model_training(self, sample_features):
        """تست Training LGB Model"""
        from trading_ai_system.models import LGBModel
        
        model = LGBModel()
        
        # تولید target
        y = np.random.randint(0, 2, len(sample_features))
        
        model.fit(sample_features, y)
        assert model.is_trained

    def test_lgb_model_prediction(self, sample_features, mock_model):
        """تست Prediction با LGB Model"""
        # استفاده از mock_model
        predictions = mock_model.predict(sample_features)
        
        assert len(predictions) == len(sample_features)
        assert predictions.dtype in [np.int64, np.int32, np.float64]

    def test_lgb_model_predict_proba(self, sample_features, mock_model):
        """تست Predict Proba با LGB Model"""
        proba = mock_model.predict_proba(sample_features)
        
        assert proba.shape[0] == len(sample_features)
        assert proba.shape[1] == 2
        assert (proba >= 0).all()
        assert (proba <= 1).all()

    def test_lgb_model_feature_importance(self, sample_features, mock_model):
        """تست Feature Importance"""
        importance = mock_model.feature_importance
        
        assert isinstance(importance, (dict, np.ndarray, pd.Series))


class TestRandomForestModel:
    """تست‌های Random Forest Model"""

    def test_rf_model_initialization(self):
        """تست Initialization Random Forest Model"""
        from trading_ai_system.models import RandomForestModel
        
        model = RandomForestModel(
            n_estimators=100,
            max_depth=10
        )
        assert model is not None

    def test_rf_model_training(self, sample_features):
        """تست Training Random Forest Model"""
        from trading_ai_system.models import RandomForestModel
        
        model = RandomForestModel()
        
        y = np.random.randint(0, 2, len(sample_features))
        model.fit(sample_features, y)
        
        assert model.is_trained

    def test_rf_model_prediction(self, sample_features, mock_model):
        """تست Prediction با Random Forest"""
        predictions = mock_model.predict(sample_features)
        
        assert len(predictions) == len(sample_features)


class TestNeuralNetworkModel:
    """تست‌های Neural Network Model"""

    def test_nn_model_initialization(self):
        """تست Initialization Neural Network Model"""
        from trading_ai_system.models import NeuralNetworkModel
        
        model = NeuralNetworkModel(
            input_dim=10,
            hidden_dims=[64, 32],
            output_dim=1
        )
        assert model is not None

    def test_nn_model_training(self, sample_features):
        """تست Training Neural Network Model"""
        from trading_ai_system.models import NeuralNetworkModel
        
        model = NeuralNetworkModel(
            input_dim=sample_features.shape[1],
            hidden_dims=[64, 32],
            output_dim=1
        )
        
        y = np.random.rand(len(sample_features), 1)
        model.fit(sample_features, y, epochs=5)
        
        assert model.is_trained

    def test_nn_model_prediction(self, sample_features, mock_model):
        """تست Prediction با Neural Network"""
        predictions = mock_model.predict(sample_features)
        
        assert len(predictions) == len(sample_features)


class TestXGBoostModel:
    """تست‌های XGBoost Model"""

    def test_xgb_model_initialization(self):
        """تست Initialization XGBoost Model"""
        from trading_ai_system.models import XGBoostModel
        
        model = XGBoostModel(
            n_estimators=100,
            learning_rate=0.1
        )
        assert model is not None

    def test_xgb_model_training(self, sample_features):
        """تست Training XGBoost Model"""
        from trading_ai_system.models import XGBoostModel
        
        model = XGBoostModel()
        
        y = np.random.randint(0, 2, len(sample_features))
        model.fit(sample_features, y)
        
        assert model.is_trained

    def test_xgb_model_prediction(self, sample_features, mock_model):
        """تست Prediction با XGBoost"""
        predictions = mock_model.predict(sample_features)
        
        assert len(predictions) == len(sample_features)


class TestModelEvaluation:
    """تست‌های Model Evaluation"""

    def test_accuracy_calculation(self, mock_model, sample_features):
        """تست محاسبه Accuracy"""
        y_true = np.random.randint(0, 2, len(sample_features))
        y_pred = mock_model.predict(sample_features)
        
        from trading_ai_system.models import calculate_accuracy
        accuracy = calculate_accuracy(y_true, y_pred)
        
        assert 0 <= accuracy <= 1

    def test_precision_calculation(self, sample_features):
        """تست محاسبه Precision"""
        y_true = np.random.randint(0, 2, len(sample_features))
        y_pred = np.random.randint(0, 2, len(sample_features))
        
        from trading_ai_system.models import calculate_precision
        precision = calculate_precision(y_true, y_pred)
        
        assert 0 <= precision <= 1

    def test_recall_calculation(self, sample_features):
        """تست محاسبه Recall"""
        y_true = np.random.randint(0, 2, len(sample_features))
        y_pred = np.random.randint(0, 2, len(sample_features))
        
        from trading_ai_system.models import calculate_recall
        recall = calculate_recall(y_true, y_pred)
        
        assert 0 <= recall <= 1

    def test_f1_score_calculation(self, sample_features):
        """تست محاسبه F1 Score"""
        y_true = np.random.randint(0, 2, len(sample_features))
        y_pred = np.random.randint(0, 2, len(sample_features))
        
        from trading_ai_system.models import calculate_f1_score
        f1 = calculate_f1_score(y_true, y_pred)
        
        assert 0 <= f1 <= 1

    def test_roc_auc_calculation(self, mock_model, sample_features):
        """تست محاسبه ROC AUC"""
        y_true = np.random.randint(0, 2, len(sample_features))
        y_pred_proba = mock_model.predict_proba(sample_features)[:, 1]
        
        from trading_ai_system.models import calculate_roc_auc
        auc = calculate_roc_auc(y_true, y_pred_proba)
        
        assert 0 <= auc <= 1

    def test_confusion_matrix_calculation(self, sample_features):
        """تست محاسبه Confusion Matrix"""
        y_true = np.random.randint(0, 2, len(sample_features))
        y_pred = np.random.randint(0, 2, len(sample_features))
        
        from trading_ai_system.models import calculate_confusion_matrix
        cm = calculate_confusion_matrix(y_true, y_pred)
        
        assert cm.shape == (2, 2)


class TestModelValidation:
    """تست‌های Model Validation"""

    def test_train_test_split(self, sample_features):
        """تست Train-Test Split"""
        from trading_ai_system.models import train_test_split
        
        y = np.random.randint(0, 2, len(sample_features))
        
        X_train, X_test, y_train, y_test = train_test_split(
            sample_features, y, test_size=0.2
        )
        
        assert len(X_train) + len(X_test) == len(sample_features)
        assert len(X_train) > len(X_test)

    def test_cross_validation(self, sample_features, mock_model):
        """تست Cross Validation"""
        from trading_ai_system.models import cross_validate
        
        y = np.random.randint(0, 2, len(sample_features))
        
        scores = cross_validate(mock_model, sample_features, y, cv=5)
        
        assert len(scores) == 5
        assert all(0 <= score <= 1 for score in scores)

    def test_stratified_kfold(self, sample_features):
        """تست Stratified KFold"""
        from trading_ai_system.models import stratified_kfold
        
        y = np.random.randint(0, 2, len(sample_features))
        
        splits = list(stratified_kfold(sample_features, y, n_splits=5))
        
        assert len(splits) == 5

    @pytest.mark.slow
    def test_grid_search(self, sample_features):
        """تست Grid Search"""
        from trading_ai_system.models import GridSearchCV, LGBModel
        
        model = LGBModel()
        params = {
            'n_estimators': [50, 100],
            'learning_rate': [0.05, 0.1]
        }
        
        y = np.random.randint(0, 2, len(sample_features))
        
        grid_search = GridSearchCV(model, params)
        grid_search.fit(sample_features, y)
        
        assert grid_search.best_params_ is not None


class TestModelPersistence:
    """تست‌های Model Persistence"""

    def test_save_model(self, mock_model, test_data_dir):
        """تست Save کردن Model"""
        from trading_ai_system.models import save_model
        
        model_path = test_data_dir / "test_model.pkl"
        save_model(mock_model, str(model_path))
        
        assert model_path.exists()

    def test_load_model(self, mock_model, test_data_dir):
        """تست Load کردن Model"""
        from trading_ai_system.models import save_model, load_model
        
        model_path = test_data_dir / "test_model.pkl"
        save_model(mock_model, str(model_path))
        
        loaded_model = load_model(str(model_path))
        
        assert loaded_model is not None

    def test_model_serialization(self, mock_model, test_data_dir):
        """تست Serialization Model"""
        from trading_ai_system.models import serialize_model, deserialize_model
        
        serialized = serialize_model(mock_model)
        deserialized = deserialize_model(serialized)
        
        assert deserialized is not None


class TestModelEnsemble:
    """تست‌های Model Ensemble"""

    def test_voting_ensemble(self, sample_features):
        """تست Voting Ensemble"""
        from trading_ai_system.models import VotingEnsemble
        
        ensemble = VotingEnsemble()
        
        y = np.random.randint(0, 2, len(sample_features))
        ensemble.fit(sample_features, y)
        
        predictions = ensemble.predict(sample_features)
        assert len(predictions) == len(sample_features)

    def test_stacking_ensemble(self, sample_features):
        """تست Stacking Ensemble"""
        from trading_ai_system.models import StackingEnsemble
        
        ensemble = StackingEnsemble()
        
        y = np.random.randint(0, 2, len(sample_features))
        ensemble.fit(sample_features, y)
        
        predictions = ensemble.predict(sample_features)
        assert len(predictions) == len(sample_features)

    def test_blending_ensemble(self, sample_features):
        """تست Blending Ensemble"""
        from trading_ai_system.models import BlendingEnsemble
        
        ensemble = BlendingEnsemble()
        
        y = np.random.randint(0, 2, len(sample_features))
        ensemble.fit(sample_features, y)
        
        predictions = ensemble.predict(sample_features)
        assert len(predictions) == len(sample_features)
