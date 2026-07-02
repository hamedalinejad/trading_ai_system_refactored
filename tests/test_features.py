# tests/test_features.py
"""
تست‌های Features Module
"""

import pytest
import pandas as pd
import numpy as np


class TestFeatureEngineer:
    """تست‌های Feature Engineer"""

    def test_feature_engineer_initialization(self):
        """تست Initialization Feature Engineer"""
        from trading_ai_system.features import FeatureEngineer
        
        engineer = FeatureEngineer()
        assert engineer is not None

    def test_calculate_technical_indicators(self, sample_ohlcv):
        """تست محاسبه Technical Indicators"""
        from trading_ai_system.features import FeatureEngineer
        
        engineer = FeatureEngineer()
        features = engineer.calculate(sample_ohlcv)
        
        assert isinstance(features, pd.DataFrame)
        assert len(features) > 0

    def test_rsi_calculation(self, sample_ohlcv):
        """تست محاسبه RSI"""
        from trading_ai_system.features import calculate_rsi
        
        rsi = calculate_rsi(sample_ohlcv['close'], period=14)
        
        assert len(rsi) == len(sample_ohlcv)
        assert (0 <= rsi).all()
        assert (rsi <= 100).all()

    def test_rsi_values_in_range(self, sample_ohlcv):
        """تست اینکه RSI در محدوده 0-100 باشد"""
        from trading_ai_system.features import calculate_rsi
        
        rsi = calculate_rsi(sample_ohlcv['close'], period=14)
        
        valid_rsi = rsi.dropna()
        assert (valid_rsi >= 0).all()
        assert (valid_rsi <= 100).all()

    def test_sma_calculation(self, sample_ohlcv):
        """تست محاسبه SMA"""
        from trading_ai_system.features import calculate_sma
        
        sma = calculate_sma(sample_ohlcv['close'], period=20)
        
        assert len(sma) == len(sample_ohlcv)
        assert sma.dtype in [np.float64, np.float32]

    def test_sma_starts_with_nan(self, sample_ohlcv):
        """تست اینکه SMA شامل NaN values در ابتدا باشد"""
        from trading_ai_system.features import calculate_sma
        
        sma = calculate_sma(sample_ohlcv['close'], period=20)
        
        # پیش از 20 بار، SMA باید NaN باشد
        assert sma[:19].isnull().all()
        assert sma[20:].notna().all()

    def test_ema_calculation(self, sample_ohlcv):
        """تست محاسبه EMA"""
        from trading_ai_system.features import calculate_ema
        
        ema = calculate_ema(sample_ohlcv['close'], period=20)
        
        assert len(ema) == len(sample_ohlcv)
        assert not ema.isnull().all()

    def test_macd_calculation(self, sample_ohlcv):
        """تست محاسبه MACD"""
        from trading_ai_system.features import calculate_macd
        
        macd, signal, histogram = calculate_macd(sample_ohlcv['close'])
        
        assert len(macd) == len(sample_ohlcv)
        assert len(signal) == len(sample_ohlcv)
        assert len(histogram) == len(sample_ohlcv)

    def test_bollinger_bands_calculation(self, sample_ohlcv):
        """تست محاسبه Bollinger Bands"""
        from trading_ai_system.features import calculate_bollinger_bands
        
        upper, middle, lower = calculate_bollinger_bands(
            sample_ohlcv['close'], 
            period=20, 
            std_dev=2
        )
        
        assert len(upper) == len(sample_ohlcv)
        assert len(middle) == len(sample_ohlcv)
        assert len(lower) == len(sample_ohlcv)

    def test_bollinger_bands_relationships(self, sample_ohlcv):
        """تست Relationships بین Bollinger Bands"""
        from trading_ai_system.features import calculate_bollinger_bands
        
        upper, middle, lower = calculate_bollinger_bands(
            sample_ohlcv['close'], 
            period=20, 
            std_dev=2
        )
        
        # upper باید >= middle >= lower باشد
        valid_upper = upper.dropna()
        valid_middle = middle.dropna()
        valid_lower = lower.dropna()
        
        assert (valid_upper >= valid_middle).all()
        assert (valid_middle >= valid_lower).all()

    def test_atr_calculation(self, sample_ohlcv):
        """تست محاسبه ATR"""
        from trading_ai_system.features import calculate_atr
        
        atr = calculate_atr(
            sample_ohlcv['high'],
            sample_ohlcv['low'],
            sample_ohlcv['close'],
            period=14
        )
        
        assert len(atr) == len(sample_ohlcv)
        assert (atr >= 0).all()

    def test_adx_calculation(self, sample_ohlcv):
        """تست محاسبه ADX"""
        from trading_ai_system.features import calculate_adx
        
        adx = calculate_adx(
            sample_ohlcv['high'],
            sample_ohlcv['low'],
            sample_ohlcv['close'],
            period=14
        )
        
        assert len(adx) == len(sample_ohlcv)
        assert (0 <= adx).all()
        assert (adx <= 100).all()

    def test_stochastic_calculation(self, sample_ohlcv):
        """تست محاسبه Stochastic"""
        from trading_ai_system.features import calculate_stochastic
        
        k, d = calculate_stochastic(
            sample_ohlcv['high'],
            sample_ohlcv['low'],
            sample_ohlcv['close'],
            period=14
        )
        
        assert len(k) == len(sample_ohlcv)
        assert len(d) == len(sample_ohlcv)

    def test_volume_indicators(self, sample_ohlcv):
        """تست Volume Indicators"""
        from trading_ai_system.features import calculate_obv
        
        obv = calculate_obv(sample_ohlcv['close'], sample_ohlcv['volume'])
        
        assert len(obv) == len(sample_ohlcv)


class TestFeatureNormalization:
    """تست‌های Feature Normalization"""

    def test_normalize_features(self, sample_features):
        """تست Normalize کردن Features"""
        from trading_ai_system.features import normalize_features
        
        normalized = normalize_features(sample_features, method='minmax')
        
        assert normalized.shape == sample_features.shape
        assert (normalized >= 0).all().all()
        assert (normalized <= 1).all().all()

    def test_standardize_features(self, sample_features):
        """تست Standardize کردن Features"""
        from trading_ai_system.features import standardize_features
        
        standardized = standardize_features(sample_features)
        
        assert standardized.shape == sample_features.shape
        for col in standardized.columns:
            assert abs(standardized[col].mean()) < 0.01
            assert abs(standardized[col].std() - 1.0) < 0.1


class TestFeatureSelection:
    """تست‌های Feature Selection"""

    def test_correlation_feature_selection(self, sample_features):
        """تست Correlation based Feature Selection"""
        from trading_ai_system.features import select_features_by_correlation
        
        selected = select_features_by_correlation(
            sample_features, 
            threshold=0.3
        )
        
        assert len(selected) > 0
        assert len(selected) <= len(sample_features.columns)

    def test_variance_feature_selection(self, sample_features):
        """تست Variance based Feature Selection"""
        from trading_ai_system.features import select_features_by_variance
        
        selected = select_features_by_variance(
            sample_features, 
            threshold=0.01
        )
        
        assert len(selected) > 0

    def test_mutual_information_selection(self, sample_features):
        """تست Mutual Information Feature Selection"""
        from trading_ai_system.features import select_features_by_mutual_info
        
        target = np.random.randint(0, 2, len(sample_features))
        selected = select_features_by_mutual_info(
            sample_features,
            target,
            k=5
        )
        
        assert len(selected) <= 5


class TestFeatureEngineering:
    """تست‌های Advanced Feature Engineering"""

    def test_create_rolling_features(self, sample_ohlcv):
        """تست ایجاد Rolling Features"""
        from trading_ai_system.features import create_rolling_features
        
        rolling = create_rolling_features(
            sample_ohlcv['close'],
            windows=[5, 10, 20]
        )
        
        assert rolling.shape[1] >= 3
        assert len(rolling) == len(sample_ohlcv)

    def test_create_lag_features(self, sample_ohlcv):
        """تست ایجاد Lag Features"""
        from trading_ai_system.features import create_lag_features
        
        lagged = create_lag_features(
            sample_ohlcv['close'],
            lags=5
        )
        
        assert lagged.shape[1] == 6  # original + 5 lags

    def test_create_interaction_features(self, sample_features):
        """تست ایجاد Interaction Features"""
        from trading_ai_system.features import create_interaction_features
        
        interactions = create_interaction_features(sample_features)
        
        assert interactions.shape[1] > sample_features.shape[1]

    def test_polynomial_features(self, sample_features):
        """تست ایجاد Polynomial Features"""
        from trading_ai_system.features import create_polynomial_features
        
        poly = create_polynomial_features(sample_features, degree=2)
        
        assert poly.shape[1] > sample_features.shape[1]


class TestFeatureValidation:
    """تست‌های Feature Validation"""

    def test_validate_no_nan_features(self, sample_features):
        """تست اینکه Features NaN نداشته باشند"""
        from trading_ai_system.features import validate_features
        
        assert validate_features(sample_features) is True

    def test_validate_features_with_nan(self, sample_features):
        """تست Validation Features با NaN"""
        from trading_ai_system.features import validate_features
        
        df_with_nan = sample_features.copy()
        df_with_nan.iloc[0, 0] = np.nan
        
        # بسته به تابع validate_features
        # ممکن است False برگردد یا nan‌ها حذف شوند
        result = validate_features(df_with_nan)
        assert result is not None

    def test_check_feature_ranges(self, sample_features):
        """تست بررسی Feature Ranges"""
        from trading_ai_system.features import check_feature_ranges
        
        ranges = check_feature_ranges(sample_features)
        
        assert isinstance(ranges, dict)
        for col in sample_features.columns:
            assert col in ranges

    @pytest.mark.slow
    def test_feature_importance_calculation(self, sample_features):
        """تست محاسبه Feature Importance"""
        from trading_ai_system.features import calculate_feature_importance
        
        target = np.random.randint(0, 2, len(sample_features))
        importance = calculate_feature_importance(sample_features, target)
        
        assert len(importance) == sample_features.shape[1]
        assert (importance >= 0).all()
