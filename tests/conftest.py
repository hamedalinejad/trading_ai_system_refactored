"""
conftest.py - Pytest Configuration و Fixtures

تعریف Fixtures مشترک برای تمام تست‌ها
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, MagicMock
from datetime import datetime, timedelta


# ============================================================================
# FIXTURES: Data
# ============================================================================

@pytest.fixture
def sample_ohlcv():
    """نمونه داده OHLCV برای تست‌ها."""
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    df = pd.DataFrame({
        'datetime': dates,
        'open': np.random.uniform(1.0, 1.1, 100),
        'high': np.random.uniform(1.1, 1.2, 100),
        'low': np.random.uniform(0.9, 1.0, 100),
        'close': np.random.uniform(1.0, 1.1, 100),
        'volume': np.random.uniform(1000000, 5000000, 100),
    })
    df.set_index('datetime', inplace=True)
    return df


@pytest.fixture
def large_sample_ohlcv():
    """بزرگ‌تر نمونه داده برای تست‌های Performance."""
    dates = pd.date_range(start='2020-01-01', periods=1000, freq='D')
    df = pd.DataFrame({
        'datetime': dates,
        'open': np.random.uniform(1.0, 1.1, 1000),
        'high': np.random.uniform(1.1, 1.2, 1000),
        'low': np.random.uniform(0.9, 1.0, 1000),
        'close': np.random.uniform(1.0, 1.1, 1000),
        'volume': np.random.uniform(1000000, 5000000, 1000),
    })
    df.set_index('datetime', inplace=True)
    return df


@pytest.fixture
def sample_features():
    """نمونه فیچرهای محاسبه‌شده."""
    df = pd.DataFrame({
        'rsi': np.random.uniform(20, 80, 100),
        'macd': np.random.uniform(-0.05, 0.05, 100),
        'bb_upper': np.random.uniform(1.1, 1.2, 100),
        'bb_lower': np.random.uniform(0.9, 1.0, 100),
        'atr': np.random.uniform(0.01, 0.05, 100),
        'ema_12': np.random.uniform(1.0, 1.1, 100),
        'ema_26': np.random.uniform(1.0, 1.1, 100),
    })
    return df


@pytest.fixture
def sample_labels():
    """نمونه label‌های تست برای تست‌های ML."""
    return np.random.choice([0, 1], size=100)


# ============================================================================
# FIXTURES: Mocks
# ============================================================================

@pytest.fixture
def mock_broker():
    """Mock Broker Connector."""
    broker = MagicMock()
    broker.fetch_ohlcv = MagicMock(return_value=pd.DataFrame({
        'open': [1.0] * 50,
        'high': [1.1] * 50,
        'low': [0.9] * 50,
        'close': [1.05] * 50,
        'volume': [1000000] * 50,
    }))
    broker.create_order = MagicMock(return_value={'id': '12345', 'status': 'closed'})
    broker.get_positions = MagicMock(return_value=[])
    return broker


@pytest.fixture
def mock_data_fetcher():
    """Mock Data Fetcher."""
    fetcher = MagicMock()
    fetcher.fetch = MagicMock(return_value=pd.DataFrame({
        'open': np.random.uniform(1.0, 1.1, 50),
        'high': np.random.uniform(1.1, 1.2, 50),
        'low': np.random.uniform(0.9, 1.0, 50),
        'close': np.random.uniform(1.0, 1.1, 50),
        'volume': np.random.uniform(1000000, 5000000, 50),
    }))
    return fetcher


@pytest.fixture
def mock_model():
    """Mock ML Model."""
    model = MagicMock()
    model.predict = MagicMock(return_value=np.random.choice([0, 1], size=50))
    model.train = MagicMock()
    model.save = MagicMock()
    model.load = MagicMock()
    return model


# ============================================================================
# FIXTURES: Configuration
# ============================================================================

@pytest.fixture
def test_config():
    """تست Configuration."""
    config = {
        'data_dir': './test_data',
        'model_dir': './test_models',
        'logging_level': 'DEBUG',
        'trading_pair': 'EURUSD',
        'timeframe': '1D',
        'initial_capital': 10000,
        'risk_per_trade': 0.02,
        'max_positions': 5,
        'max_drawdown': 0.2,
    }
    return config


# ============================================================================
# MARKERS
# ============================================================================

def pytest_configure(config):
    """ثبت Markers سفارشی برای Pytest."""
    config.addinivalue_line(
        "markers", "slow: تست‌های کند (نیاز به زمان بیشتر)"
    )
    config.addinivalue_line(
        "markers", "integration: تست‌های Integration"
    )
    config.addinivalue_line(
        "markers", "performance: تست‌های Performance"
    )
    config.addinivalue_line(
        "markers", "security: تست‌های Security"
    )


# ============================================================================
# HOOKS
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_after_test():
    """پاک‌کردن بعد از هر تست."""
    yield
    # Cleanup code here if needed
