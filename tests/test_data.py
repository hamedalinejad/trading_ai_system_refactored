# tests/test_data.py
"""
تست‌های Data Module
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class TestDataFetcher:
    """تست‌های Data Fetcher"""

    def test_data_fetcher_initialization(self, mock_broker):
        """تست Initialization Data Fetcher"""
        # Mock یک Data Fetcher
        fetcher = mock_broker
        assert fetcher is not None
        assert fetcher.is_connected() is True

    def test_fetch_returns_valid_ohlcv(self, sample_ohlcv):
        """تست بازیابی داده OHLCV معتبر"""
        assert isinstance(sample_ohlcv, pd.DataFrame)
        assert len(sample_ohlcv) > 0
        
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            assert col in sample_ohlcv.columns

    def test_ohlcv_data_types(self, sample_ohlcv):
        """تست اینکه OHLCV data types درست باشند"""
        assert sample_ohlcv['open'].dtype in [np.float64, np.float32]
        assert sample_ohlcv['high'].dtype in [np.float64, np.float32]
        assert sample_ohlcv['low'].dtype in [np.float64, np.float32]
        assert sample_ohlcv['close'].dtype in [np.float64, np.float32]
        assert sample_ohlcv['volume'].dtype in [np.float64, np.int64]

    def test_ohlcv_data_integrity(self, sample_ohlcv):
        """تست Integrity داده OHLCV"""
        # high باید >= low باشد
        assert (sample_ohlcv['high'] >= sample_ohlcv['low']).all()
        
        # open و close باید بین low و high باشند
        assert (sample_ohlcv['open'] >= sample_ohlcv['low']).all()
        assert (sample_ohlcv['open'] <= sample_ohlcv['high']).all()
        assert (sample_ohlcv['close'] >= sample_ohlcv['low']).all()
        assert (sample_ohlcv['close'] <= sample_ohlcv['high']).all()
        
        # volume باید مثبت باشد
        assert (sample_ohlcv['volume'] > 0).all()

    def test_ohlcv_no_missing_values(self, sample_ohlcv):
        """تست اینکه OHLCV Missing Values نداشته باشد"""
        assert not sample_ohlcv.isnull().any().any()

    def test_ohlcv_date_index(self, sample_ohlcv):
        """تست اینکه Index تاریخ صحیح باشد"""
        assert isinstance(sample_ohlcv.index, pd.DatetimeIndex)
        # اندیکس باید مرتب باشد
        assert sample_ohlcv.index.is_monotonic_increasing

    def test_fetch_with_date_range(self, mock_data_fetcher):
        """تست بازیابی داده با Date Range"""
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 31)
        
        mock_data_fetcher.fetch('EURUSD', start_date, end_date)
        mock_data_fetcher.fetch.assert_called_once_with('EURUSD', start_date, end_date)

    def test_fetch_with_invalid_symbol(self, mock_data_fetcher):
        """تست بازیابی داده با Symbol نامعتبر"""
        with pytest.raises(ValueError):
            mock_data_fetcher.fetch('INVALID_SYMBOL', None, None)

    @pytest.mark.slow
    def test_fetch_large_dataset(self, sample_ohlcv):
        """تست بازیابی Dataset بزرگ"""
        large_data = pd.concat([sample_ohlcv] * 10, ignore_index=False)
        assert len(large_data) >= 1000


class TestDataValidation:
    """تست‌های Data Validation"""

    def test_validate_ohlcv_structure(self, sample_ohlcv):
        """تست Validate کردن ساختار OHLCV"""
        from trading_ai_system.data import validate_ohlcv_structure
        
        assert validate_ohlcv_structure(sample_ohlcv) is True

    def test_validate_ohlcv_values(self, sample_ohlcv):
        """تست Validate کردن مقادیر OHLCV"""
        from trading_ai_system.data import validate_ohlcv_values
        
        assert validate_ohlcv_values(sample_ohlcv) is True

    def test_invalid_ohlcv_missing_column(self):
        """تست Invalid OHLCV با Column گمشده"""
        from trading_ai_system.data import validate_ohlcv_structure
        
        df = pd.DataFrame({'open': [1], 'high': [1]})
        assert validate_ohlcv_structure(df) is False

    def test_invalid_ohlcv_high_less_than_low(self):
        """تست Invalid OHLCV که high کمتر از low باشد"""
        df = pd.DataFrame({
            'open': [1.0],
            'high': [0.9],
            'low': [1.0],
            'close': [1.0],
            'volume': [1000]
        })
        
        from trading_ai_system.data import validate_ohlcv_values
        assert validate_ohlcv_values(df) is False


class TestDataCleaning:
    """تست‌های Data Cleaning"""

    def test_remove_missing_values(self, sample_ohlcv):
        """تست حذف Missing Values"""
        from trading_ai_system.data import remove_missing_values
        
        # Add some NaN values
        df_with_nan = sample_ohlcv.copy()
        df_with_nan.iloc[0, 0] = np.nan
        
        cleaned = remove_missing_values(df_with_nan)
        assert not cleaned.isnull().any().any()

    def test_handle_outliers(self, sample_ohlcv):
        """تست Handling Outliers"""
        from trading_ai_system.data import handle_outliers
        
        df_with_outliers = sample_ohlcv.copy()
        df_with_outliers.iloc[0, 0] = 1000  # Outlier
        
        cleaned = handle_outliers(df_with_outliers, method='iqr')
        assert len(cleaned) <= len(df_with_outliers)

    def test_normalize_data(self, sample_ohlcv):
        """تست Normalize داده"""
        from trading_ai_system.data import normalize_data
        
        normalized = normalize_data(sample_ohlcv, method='minmax')
        
        # بعد از normalization، مقادیر باید بین 0 و 1 باشند
        assert (normalized >= 0).all().all()
        assert (normalized <= 1).all().all()

    def test_standardize_data(self, sample_ohlcv):
        """تست Standardize داده"""
        from trading_ai_system.data import standardize_data
        
        standardized = standardize_data(sample_ohlcv)
        
        # بعد از standardization، mean باید نزدیک 0 و std نزدیک 1 باشد
        for col in standardized.columns:
            assert abs(standardized[col].mean()) < 0.01
            assert abs(standardized[col].std() - 1.0) < 0.1


class TestDataTransformation:
    """تست‌های Data Transformation"""

    def test_resample_timeframe(self, sample_ohlcv):
        """تست Resample کردن Timeframe"""
        from trading_ai_system.data import resample_ohlcv
        
        # Resample از روزانه به هفتگی
        resampled = resample_ohlcv(sample_ohlcv, '1W')
        
        assert len(resampled) < len(sample_ohlcv)

    def test_calculate_returns(self, sample_ohlcv):
        """تست محاسبه Returns"""
        from trading_ai_system.data import calculate_returns
        
        returns = calculate_returns(sample_ohlcv['close'])
        
        assert len(returns) == len(sample_ohlcv) - 1
        assert not returns.isnull().all()

    def test_calculate_log_returns(self, sample_ohlcv):
        """تست محاسبه Log Returns"""
        from trading_ai_system.data import calculate_log_returns
        
        log_returns = calculate_log_returns(sample_ohlcv['close'])
        
        assert len(log_returns) == len(sample_ohlcv) - 1
        assert log_returns.dtype in [np.float64, np.float32]

    def test_create_lagged_features(self, sample_ohlcv):
        """تست ایجاد Lagged Features"""
        from trading_ai_system.data import create_lagged_features
        
        lagged = create_lagged_features(sample_ohlcv['close'], lags=3)
        
        assert lagged.shape[1] == 4  # original + 3 lags
        assert len(lagged) == len(sample_ohlcv)


class TestDataCaching:
    """تست‌های Data Caching"""

    def test_cache_data(self, sample_ohlcv, test_data_dir):
        """تست Caching داده"""
        from trading_ai_system.data import cache_data
        
        cache_file = test_data_dir / "test_cache.parquet"
        cache_data(sample_ohlcv, str(cache_file))
        
        assert cache_file.exists()

    def test_load_cached_data(self, sample_ohlcv, test_data_dir):
        """تست Load کردن Cached داده"""
        from trading_ai_system.data import cache_data, load_cached_data
        
        cache_file = test_data_dir / "test_cache.parquet"
        cache_data(sample_ohlcv, str(cache_file))
        
        loaded = load_cached_data(str(cache_file))
        pd.testing.assert_frame_equal(sample_ohlcv, loaded)

    def test_cache_exists_check(self, test_data_dir):
        """تست بررسی Cache Existence"""
        from trading_ai_system.data import cache_exists
        
        non_existent = test_data_dir / "non_existent.parquet"
        assert cache_exists(str(non_existent)) is False


class TestDataStatistics:
    """تست‌های Data Statistics"""

    def test_calculate_basic_stats(self, sample_ohlcv):
        """تست محاسبه Basic Statistics"""
        from trading_ai_system.data import calculate_basic_stats
        
        stats = calculate_basic_stats(sample_ohlcv)
        
        assert 'mean' in stats
        assert 'std' in stats
        assert 'min' in stats
        assert 'max' in stats

    def test_calculate_correlation(self, sample_ohlcv):
        """تست محاسبه Correlation"""
        from trading_ai_system.data import calculate_correlation
        
        correlation = calculate_correlation(sample_ohlcv)
        
        assert correlation.shape == (len(sample_ohlcv.columns), len(sample_ohlcv.columns))

    def test_detect_trend(self, sample_ohlcv):
        """تست تشخیص Trend"""
        from trading_ai_system.data import detect_trend
        
        trend = detect_trend(sample_ohlcv['close'])
        
        assert trend in ['UPTREND', 'DOWNTREND', 'SIDEWAYS']

    def test_calculate_volatility(self, sample_ohlcv):
        """تست محاسبه Volatility"""
        from trading_ai_system.data import calculate_volatility
        
        volatility = calculate_volatility(sample_ohlcv['close'], window=20)
        
        assert len(volatility) == len(sample_ohlcv)
        assert (volatility >= 0).all()
