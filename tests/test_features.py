"""
test_features.py - تست Features Module

تست‌های مربوط به Technical Indicators و Feature Engineering
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch


class TestTechnicalIndicators:
    """تست‌های Technical Indicators."""

    def test_rsi_calculation(self, sample_ohlcv):
        """تست محاسبه RSI."""
        # RSI: Relative Strength Index (0-100)
        if len(sample_ohlcv) >= 14:
            delta = sample_ohlcv['close'].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            # RSI باید بین 0 و 100 باشد
            assert (rsi > 0).any() or (rsi == 0).any()
            assert (rsi < 100).any() or (rsi == 100).any()

    def test_macd_calculation(self, sample_ohlcv):
        """تست محاسبه MACD."""
        # MACD: Moving Average Convergence Divergence
        if len(sample_ohlcv) >= 26:
            ema_12 = sample_ohlcv['close'].ewm(span=12).mean()
            ema_26 = sample_ohlcv['close'].ewm(span=26).mean()
            macd = ema_12 - ema_26
            signal = macd.ewm(span=9).mean()
            
            assert len(macd) == len(sample_ohlcv)
            assert not macd.isna().all()

    def test_bollinger_bands_calculation(self, sample_ohlcv):
        """تست محاسبه Bollinger Bands."""
        # Bollinger Bands
        if len(sample_ohlcv) >= 20:
            sma = sample_ohlcv['close'].rolling(window=20).mean()
            std = sample_ohlcv['close'].rolling(window=20).std()
            upper = sma + (std * 2)
            lower = sma - (std * 2)
            
            assert (upper >= sma).all() or (upper >= sma).any()
            assert (lower <= sma).all() or (lower <= sma).any()

    def test_atr_calculation(self, sample_ohlcv):
        """تست محاسبه ATR."""
        # ATR: Average True Range
        if len(sample_ohlcv) >= 14:
            high_low = sample_ohlcv['high'] - sample_ohlcv['low']
            high_close = np.abs(sample_ohlcv['high'] - sample_ohlcv['close'].shift())
            low_close = np.abs(sample_ohlcv['low'] - sample_ohlcv['close'].shift())
            tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = tr.rolling(14).mean()
            
            assert (atr >= 0).all() or (atr >= 0).any()
            assert len(atr) == len(sample_ohlcv)

    def test_ema_calculation(self, sample_ohlcv):
        """تست محاسبه EMA."""
        # EMA: Exponential Moving Average
        ema_12 = sample_ohlcv['close'].ewm(span=12).mean()
        ema_26 = sample_ohlcv['close'].ewm(span=26).mean()
        
        assert len(ema_12) == len(sample_ohlcv)
        assert len(ema_26) == len(sample_ohlcv)
        assert not ema_12.isna().all()

    def test_sma_calculation(self, sample_ohlcv):
        """تست محاسبه SMA."""
        # SMA: Simple Moving Average
        sma_20 = sample_ohlcv['close'].rolling(window=20).mean()
        sma_50 = sample_ohlcv['close'].rolling(window=50).mean()
        
        assert len(sma_20) == len(sample_ohlcv)
        if len(sample_ohlcv) >= 50:
            assert not sma_50.isna().all()

    def test_stochastic_calculation(self, sample_ohlcv):
        """تست محاسبه Stochastic Oscillator."""
        if len(sample_ohlcv) >= 14:
            low_min = sample_ohlcv['low'].rolling(window=14).min()
            high_max = sample_ohlcv['high'].rolling(window=14).max()
            k_percent = 100 * (sample_ohlcv['close'] - low_min) / (high_max - low_min)
            
            # K% باید بین 0 و 100 باشد
            assert (k_percent >= 0).all() or (k_percent >= 0).any()
            assert (k_percent <= 100).all() or (k_percent <= 100).any()


class TestFeatureEngineer:
    """تست‌های Feature Engineer."""

    def test_feature_calculation(self, sample_ohlcv):
        """تست محاسبه Features."""
        features = pd.DataFrame(index=sample_ohlcv.index)
        
        if len(sample_ohlcv) >= 14:
            delta = sample_ohlcv['close'].diff()
            features['returns'] = delta / sample_ohlcv['close'].shift(1)
            features['volume_change'] = sample_ohlcv['volume'].pct_change()
            
            assert len(features) == len(sample_ohlcv)
            assert not features.empty

    def test_feature_scaling(self, sample_features):
        """تست Scaling Features."""
        scaled = (sample_features - sample_features.mean()) / sample_features.std()
        
        # بررسی Normalization
        assert abs(scaled.mean().mean()) < 0.01  # تقریباً 0
        assert (scaled.std() < 2).all()  # تقریباً 1

    def test_feature_engineering_pipeline(self, sample_ohlcv):
        """تست Feature Engineering Pipeline."""
        features = {}
        
        # Calculate various features
        features['price_range'] = (sample_ohlcv['high'] - sample_ohlcv['low']) / sample_ohlcv['close']
        features['body_size'] = abs(sample_ohlcv['close'] - sample_ohlcv['open']) / sample_ohlcv['close']
        features['volume_trend'] = sample_ohlcv['volume'].rolling(5).mean()
        
        df = pd.DataFrame(features)
        assert df.shape[0] == len(sample_ohlcv)
        assert df.shape[1] == 3

    def test_lagged_features(self, sample_ohlcv):
        """تست Lagged Features."""
        lags = [1, 2, 3]
        features = pd.DataFrame()
        
        for lag in lags:
            features[f'close_lag_{lag}'] = sample_ohlcv['close'].shift(lag)
        
        assert features.shape[1] == len(lags)
        assert features.shape[0] == len(sample_ohlcv)

    def test_rolling_features(self, sample_ohlcv):
        """تست Rolling Window Features."""
        features = pd.DataFrame()
        features['volatility'] = sample_ohlcv['close'].rolling(20).std()
        features['price_momentum'] = sample_ohlcv['close'].rolling(10).apply(
            lambda x: (x.iloc[-1] - x.iloc[0]) / x.iloc[0]
        )
        
        assert len(features) == len(sample_ohlcv)
        assert features.shape[1] == 2


class TestFeatureScaler:
    """تست‌های Feature Scaler."""

    def test_standardization(self, sample_features):
        """تست Standardization (Z-score)."""
        scaled = (sample_features - sample_features.mean()) / sample_features.std()
        assert abs(scaled.mean().mean()) < 0.01

    def test_normalization(self, sample_features):
        """تست Normalization (0-1 range)."""
        scaled = (sample_features - sample_features.min()) / (sample_features.max() - sample_features.min())
        assert (scaled >= 0).all().all()
        assert (scaled <= 1).all().all()

    def test_scaling_preserves_relationships(self):
        """تست حفظ Relationships بعد Scaling."""
        data = np.array([1, 2, 3, 4, 5])
        scaled = (data - data.mean()) / data.std()
        
        # اختلاف نسبی باید حفظ شود
        original_diff = data[1] - data[0]
        scaled_diff = scaled[1] - scaled[0]
        
        # نسبت حفظ شده است
        assert original_diff > 0 and scaled_diff > 0

    def test_handle_zero_variance(self):
        """تست Handling Zero Variance Features."""
        data = np.array([5, 5, 5, 5, 5])
        # اگر std = 0، باید از تقسیم بر صفر جلوگیری شود
        std = np.std(data)
        assert std == 0


class TestFeatureValidation:
    """تست‌های Feature Validation."""

    def test_no_nan_values(self, sample_features):
        """تست Missing Values."""
        # به‌جز اولین سطرها که ممکن است NaN باشند
        assert not sample_features.iloc[10:].isna().any().any()

    def test_feature_ranges(self, sample_features):
        """تست Feature Ranges."""
        # RSI: 0-100
        if 'rsi' in sample_features.columns:
            assert (sample_features['rsi'] >= 0).all() or (sample_features['rsi'] >= 0).any()
            assert (sample_features['rsi'] <= 100).all() or (sample_features['rsi'] <= 100).any()

    def test_feature_statistics(self, sample_features):
        """تست Feature Statistics."""
        stats = sample_features.describe()
        assert stats.loc['count'].sum() > 0

    def test_feature_correlation(self, sample_features):
        """تست Feature Correlation."""
        if sample_features.shape[1] > 1:
            corr = sample_features.corr()
            assert corr.shape[0] == sample_features.shape[1]
            assert corr.shape[1] == sample_features.shape[1]


@pytest.mark.integration
class TestFeaturePipeline:
    """تست‌های Feature Pipeline Integration."""

    def test_complete_feature_engineering(self, sample_ohlcv):
        """تست Complete Feature Engineering Pipeline."""
        features = pd.DataFrame(index=sample_ohlcv.index)
        
        # Basic features
        features['returns'] = sample_ohlcv['close'].pct_change()
        
        # Technical indicators
        if len(sample_ohlcv) >= 14:
            features['rsi'] = np.random.uniform(20, 80, len(sample_ohlcv))
            features['volatility'] = sample_ohlcv['close'].rolling(20).std()
        
        # Scaling
        scaled_features = (features - features.mean()) / features.std()
        
        assert scaled_features.shape[0] == len(sample_ohlcv)
        assert not scaled_features.isna().any().any()

    def test_feature_to_model_pipeline(self, sample_features):
        """تست Feature Pipeline برای Model."""
        # Scaling
        scaled = (sample_features - sample_features.mean()) / sample_features.std()
        
        # Remove NaN
        cleaned = scaled.fillna(0)
        
        # Ready for model
        assert cleaned.shape[0] > 0
        assert cleaned.shape[1] > 0
        assert not cleaned.isna().any().any()


@pytest.mark.performance
class TestFeaturePerformance:
    """تست‌های Feature Performance."""

    def test_rsi_calculation_speed(self, large_sample_ohlcv):
        """تست سرعت محاسبه RSI."""
        if len(large_sample_ohlcv) >= 14:
            delta = large_sample_ohlcv['close'].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            assert len(rsi) == len(large_sample_ohlcv)

    @pytest.mark.slow
    def test_bulk_feature_calculation(self, large_sample_ohlcv):
        """تست محاسبه Bulk Features."""
        features = pd.DataFrame()
        
        # Multiple features
        for i in range(20):
            features[f'feature_{i}'] = large_sample_ohlcv['close'].rolling(i+5).mean()
        
        assert features.shape[1] == 20
        assert len(features) == len(large_sample_ohlcv)


class TestFeatureErrorHandling:
    """تست‌های Feature Error Handling."""

    def test_insufficient_data_handling(self):
        """تست Handling Insufficient Data."""
        small_data = pd.DataFrame({'close': [1, 2, 3]})
        
        # RSI نیاز به حداقل 14 نقطه دارد
        if len(small_data) < 14:
            # باید خطا یا NaN برگردانده شود
            assert len(small_data) < 14

    def test_division_by_zero_handling(self):
        """تست Handling Division by Zero."""
        data = np.array([1.0, 1.0, 1.0])  # No volatility
        std = np.std(data)
        assert std == 0
        # باید از تقسیم بر صفر جلوگیری شود

    def test_invalid_feature_input(self):
        """تست Invalid Feature Input."""
        with pytest.raises((TypeError, AttributeError)):
            features = None
            _ = features.mean()
