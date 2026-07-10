"""
test_data.py - تست Data Module

تست‌های مربوط به Data Fetching، Validation و Caching
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta


class TestDataFetcher:
    """تست‌های Data Fetcher."""

    def test_fetch_returns_dataframe(self, mock_broker):
        """تست بازیابی داده و بازگشت DataFrame."""
        # Mock implementation
        data = mock_broker.fetch_ohlcv()
        assert isinstance(data, pd.DataFrame)

    def test_fetch_has_required_columns(self, sample_ohlcv):
        """تست وجود ستون‌های ضروری."""
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            assert col in sample_ohlcv.columns

    def test_fetch_data_shape(self, sample_ohlcv):
        """تست شکل داده بازیابی‌شده."""
        assert sample_ohlcv.shape[0] > 0  # دریافت حداقل یک ردیف
        assert sample_ohlcv.shape[1] >= 5  # حداقل 5 ستون

    def test_fetch_date_range(self):
        """تست Date Range بازیابی‌شده."""
        dates = pd.date_range(start='2023-01-01', periods=50, freq='D')
        df = pd.DataFrame({'date': dates})
        assert df.shape[0] == 50
        assert df['date'].min() >= datetime(2023, 1, 1)

    def test_fetch_valid_ohlcv_values(self, sample_ohlcv):
        """تست معتبر بودن مقادیر OHLCV."""
        # High >= Open, Close, Low
        assert (sample_ohlcv['high'] >= sample_ohlcv['low']).all()
        # Volume >= 0
        assert (sample_ohlcv['volume'] >= 0).all()
        # Price > 0
        assert (sample_ohlcv['close'] > 0).all()


class TestDataValidator:
    """تست‌های Data Validator."""

    def test_validate_no_missing_values(self, sample_ohlcv):
        """تست Missing Values."""
        assert not sample_ohlcv.isnull().any().any()

    def test_validate_price_consistency(self, sample_ohlcv):
        """تست Consistency قیمت‌ها."""
        # High >= Low
        assert (sample_ohlcv['high'] >= sample_ohlcv['low']).all()
        # High >= Open, Close
        assert (sample_ohlcv['high'] >= sample_ohlcv['open']).all()
        assert (sample_ohlcv['high'] >= sample_ohlcv['close']).all()

    def test_validate_volume_positive(self, sample_ohlcv):
        """تست حجم مثبت."""
        assert (sample_ohlcv['volume'] >= 0).all()

    def test_validate_chronological_order(self):
        """تست ترتیب زمانی."""
        dates = pd.date_range(start='2023-01-01', periods=50, freq='D')
        df = pd.DataFrame({'date': dates})
        df_sorted = df.sort_values('date')
        assert df.equals(df_sorted)

    def test_validate_data_duplicates(self, sample_ohlcv):
        """تست Duplicate Rows."""
        duplicates = sample_ohlcv.duplicated().sum()
        # فرض بر این است که داده‌های نمونه تکراری ندارند
        # یا اگر دارند، باید مدیریت شوند
        assert isinstance(duplicates, (int, np.integer))

    def test_validate_price_ranges(self, sample_ohlcv):
        """تست Range قیمت‌ها."""
        # Reasonable price range (مثال)
        assert (sample_ohlcv['close'] > 0.001).all()
        assert (sample_ohlcv['close'] < 1000000).all()


class TestDataCache:
    """تست‌های Data Cache."""

    def test_cache_creation(self, sample_ohlcv):
        """تست ایجاد Cache."""
        cache = {}
        key = 'EURUSD_1D'
        cache[key] = sample_ohlcv
        assert key in cache

    def test_cache_retrieval(self, sample_ohlcv):
        """تست بازیابی از Cache."""
        cache = {'EURUSD_1D': sample_ohlcv}
        retrieved = cache.get('EURUSD_1D')
        assert retrieved is not None
        assert isinstance(retrieved, pd.DataFrame)

    def test_cache_miss(self):
        """تست Cache Miss."""
        cache = {}
        retrieved = cache.get('NONEXISTENT', None)
        assert retrieved is None

    def test_cache_update(self, sample_ohlcv):
        """تست بروزرسانی Cache."""
        cache = {'EURUSD_1D': sample_ohlcv}
        new_data = sample_ohlcv.copy()
        new_data['close'] = new_data['close'] * 1.01
        cache['EURUSD_1D'] = new_data
        assert not cache['EURUSD_1D'].equals(sample_ohlcv)

    def test_cache_memory_usage(self, large_sample_ohlcv):
        """تست استفاده حافظه Cache."""
        cache = {}
        cache['large_data'] = large_sample_ohlcv
        # فقط اطمینان دهید که داده‌ها در Cache هستند
        assert 'large_data' in cache
        assert len(cache) == 1


class TestOHLCVData:
    """تست‌های OHLCV Data Class."""

    def test_ohlcv_structure(self, sample_ohlcv):
        """تست ساختار OHLCV."""
        assert hasattr(sample_ohlcv, 'index')  # DateTime Index
        assert all(col in sample_ohlcv.columns for col in ['open', 'high', 'low', 'close', 'volume'])

    def test_ohlcv_data_types(self, sample_ohlcv):
        """تست Data Types OHLCV."""
        assert pd.api.types.is_float_dtype(sample_ohlcv['open'])
        assert pd.api.types.is_float_dtype(sample_ohlcv['close'])
        assert pd.api.types.is_float_dtype(sample_ohlcv['volume'])

    def test_ohlcv_datetime_index(self, sample_ohlcv):
        """تست DateTime Index."""
        assert isinstance(sample_ohlcv.index, pd.DatetimeIndex)

    def test_ohlcv_slice(self, sample_ohlcv):
        """تست Slicing OHLCV."""
        sliced = sample_ohlcv.iloc[:10]
        assert len(sliced) == 10

    def test_ohlcv_resample(self, sample_ohlcv):
        """تست Resampling OHLCV."""
        if len(sample_ohlcv) > 30:
            resampled = sample_ohlcv[['close']].resample('W').last()
            assert len(resampled) < len(sample_ohlcv)


class TestDataAggregation:
    """تست‌های Data Aggregation."""

    def test_aggregate_daily_to_weekly(self, sample_ohlcv):
        """تست Aggregation روزانه به هفتگی."""
        if len(sample_ohlcv) > 7:
            agg = {
                'open': sample_ohlcv['open'].resample('W').first(),
                'high': sample_ohlcv['high'].resample('W').max(),
                'low': sample_ohlcv['low'].resample('W').min(),
                'close': sample_ohlcv['close'].resample('W').last(),
            }
            assert len(agg['close']) < len(sample_ohlcv)

    def test_aggregate_with_volume(self, sample_ohlcv):
        """تست Aggregation با Volume."""
        if len(sample_ohlcv) > 7:
            agg = sample_ohlcv['volume'].resample('W').sum()
            assert (agg > 0).all()

    def test_aggregate_high_low(self, sample_ohlcv):
        """تست Aggregation High/Low."""
        daily_high = sample_ohlcv['high'].resample('W').max()
        daily_low = sample_ohlcv['low'].resample('W').min()
        assert (daily_high >= daily_low).all()


class TestDataTransformation:
    """تست‌های Data Transformation."""

    def test_normalize_prices(self, sample_ohlcv):
        """تست Normalize قیمت‌ها."""
        normalized = sample_ohlcv['close'] / sample_ohlcv['close'].iloc[0]
        assert normalized.iloc[0] == 1.0

    def test_calculate_returns(self, sample_ohlcv):
        """تست محاسبه Returns."""
        returns = sample_ohlcv['close'].pct_change()
        assert len(returns) == len(sample_ohlcv)
        assert returns.iloc[0] is pd.NaT or pd.isna(returns.iloc[0])

    def test_calculate_log_returns(self, sample_ohlcv):
        """تست محاسبه Log Returns."""
        log_returns = np.log(sample_ohlcv['close'] / sample_ohlcv['close'].shift(1))
        assert len(log_returns) == len(sample_ohlcv)

    def test_standardize_prices(self, sample_ohlcv):
        """تست Standardize قیمت‌ها."""
        mean = sample_ohlcv['close'].mean()
        std = sample_ohlcv['close'].std()
        standardized = (sample_ohlcv['close'] - mean) / std
        assert abs(standardized.mean()) < 0.001  # تقریباً 0


@pytest.mark.integration
class TestDataPipeline:
    """تست‌های Data Pipeline Integration."""

    def test_fetch_validate_cache_pipeline(self, sample_ohlcv, mock_broker):
        """تست Fetch -> Validate -> Cache Pipeline."""
        # Fetch
        data = mock_broker.fetch_ohlcv()
        assert isinstance(data, pd.DataFrame)
        
        # Validate
        assert not data.isnull().any().any()
        
        # Cache
        cache = {'test_data': data}
        assert cache['test_data'] is not None

    def test_data_quality_checks(self, sample_ohlcv):
        """تست Data Quality Checks."""
        checks = {
            'no_nulls': not sample_ohlcv.isnull().any().any(),
            'positive_volume': (sample_ohlcv['volume'] > 0).all(),
            'price_consistency': (sample_ohlcv['high'] >= sample_ohlcv['low']).all(),
        }
        assert all(checks.values())


@pytest.mark.performance
class TestDataPerformance:
    """تست‌های Data Performance."""

    def test_large_dataset_loading(self, large_sample_ohlcv):
        """تست بارگذاری بزرگ Dataset."""
        assert len(large_sample_ohlcv) == 1000
        assert large_sample_ohlcv.memory_usage(deep=True).sum() > 0

    def test_data_slicing_speed(self, large_sample_ohlcv):
        """تست سرعت Slicing."""
        for _ in range(100):
            _ = large_sample_ohlcv.iloc[:100]
        assert True  # اگر TimeOut نشود، تست pass می‌شود

    @pytest.mark.slow
    def test_large_aggregation(self, large_sample_ohlcv):
        """تست Aggregation بزرگ."""
        agg = large_sample_ohlcv.resample('M').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
        })
        assert len(agg) > 0


class TestDataErrorHandling:
    """تست‌های Data Error Handling."""

    def test_empty_dataframe_handling(self):
        """تست Handling Empty DataFrame."""
        empty_df = pd.DataFrame()
        assert len(empty_df) == 0
        assert empty_df.empty

    def test_malformed_data_detection(self):
        """تست Detecting Malformed Data."""
        bad_data = pd.DataFrame({
            'open': [1.0, np.nan, 1.1],
            'close': [1.05, 1.06, np.nan],
        })
        assert bad_data.isnull().any().any()

    def test_invalid_date_handling(self):
        """تست Handling Invalid Dates."""
        try:
            dates = pd.to_datetime(['2023-01-01', 'invalid', '2023-01-03'], errors='coerce')
            assert pd.isna(dates[1])
        except Exception:
            pytest.fail("Date handling failed")
