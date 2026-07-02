"""
Pytest Configuration و Fixtures
برای استفاده در تمام تست‌های پروژه
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


# اضافه کردن مسیر پروژه به sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# ===========================
# Pytest Markers Definition
# ===========================
def pytest_configure(config):
    """تعریف Markers برای pytest"""
    config.addinivalue_line(
        "markers", "slow: علامت تست‌های کند"
    )
    config.addinivalue_line(
        "markers", "integration: علامت تست‌های یکپارچگی"
    )
    config.addinivalue_line(
        "markers", "performance: علامت تست‌های کارایی"
    )
    config.addinivalue_line(
        "markers", "security: علامت تست‌های امنیتی"
    )
    config.addinivalue_line(
        "markers", "unit: علامت تست‌های واحد"
    )


# ===========================
# Fixtures for Sample Data
# ===========================

@pytest.fixture
def sample_ohlcv():
    """
    فیکسچر برای داده OHLCV نمونه
    بازگشت: DataFrame شامل Open, High, Low, Close, Volume
    """
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    data = {
        'timestamp': dates,
        'open': np.random.uniform(1.0, 1.5, 100),
        'high': np.random.uniform(1.5, 2.0, 100),
        'low': np.random.uniform(0.5, 1.0, 100),
        'close': np.random.uniform(1.0, 1.5, 100),
        'volume': np.random.randint(1000000, 5000000, 100),
    }
    df = pd.DataFrame(data)
    df.set_index('timestamp', inplace=True)
    return df


@pytest.fixture
def sample_features():
    """
    فیکسچر برای ویژگی‌های نمونه
    شامل SMA, RSI, MACD و غیره
    """
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    features = {
        'timestamp': dates,
        'sma_20': np.random.uniform(1.0, 1.5, 100),
        'sma_50': np.random.uniform(1.0, 1.5, 100),
        'rsi': np.random.uniform(30, 70, 100),
        'macd': np.random.uniform(-0.1, 0.1, 100),
        'macd_signal': np.random.uniform(-0.1, 0.1, 100),
        'bollinger_upper': np.random.uniform(1.5, 2.0, 100),
        'bollinger_lower': np.random.uniform(0.5, 1.0, 100),
    }
    df = pd.DataFrame(features)
    df.set_index('timestamp', inplace=True)
    return df


@pytest.fixture
def sample_trade():
    """
    فیکسچر برای معاملات نمونه
    """
    return {
        'symbol': 'EURUSD',
        'entry_time': datetime.now() - timedelta(hours=1),
        'exit_time': datetime.now(),
        'entry_price': 1.1050,
        'exit_price': 1.1120,
        'size': 1.0,
        'direction': 'BUY',
        'pnl': 70.0,
        'pnl_percent': 0.63,
    }


@pytest.fixture
def sample_portfolio():
    """
    فیکسچر برای پورتفولیو نمونه
    """
    return {
        'total_balance': 100000,
        'equity': 105000,
        'used_margin': 10000,
        'free_margin': 95000,
        'margin_level': 1050,
        'positions': [
            {'symbol': 'EURUSD', 'size': 1.0, 'entry_price': 1.1050},
            {'symbol': 'GBPUSD', 'size': 0.5, 'entry_price': 1.2750},
        ]
    }


# ===========================
# Fixtures for Mock Objects
# ===========================

@pytest.fixture
def mock_broker():
    """
    فیکسچر برای mock کردن Broker
    """
    broker = MagicMock()
    broker.connect = MagicMock(return_value=True)
    broker.disconnect = MagicMock(return_value=True)
    broker.get_balance = MagicMock(return_value=100000)
    broker.get_positions = MagicMock(return_value=[])
    broker.place_order = MagicMock(return_value={'order_id': 'ORD123'})
    broker.close_order = MagicMock(return_value=True)
    return broker


@pytest.fixture
def mock_data_fetcher():
    """
    فیکسچر برای mock کردن Data Fetcher
    """
    fetcher = MagicMock()
    fetcher.fetch = MagicMock(return_value=pd.DataFrame({
        'open': [1.1, 1.2],
        'high': [1.15, 1.25],
        'low': [1.05, 1.15],
        'close': [1.12, 1.22],
        'volume': [1000000, 1100000],
    }))
    return fetcher


@pytest.fixture
def mock_feature_engineer():
    """
    فیکسچر برای mock کردن Feature Engineer
    """
    engineer = MagicMock()
    engineer.calculate = MagicMock(return_value=pd.DataFrame({
        'rsi': [50, 55],
        'sma_20': [1.1, 1.2],
        'macd': [0.01, 0.02],
    }))
    return engineer


@pytest.fixture
def mock_model():
    """
    فیکسچر برای mock کردن Model
    """
    model = MagicMock()
    model.predict = MagicMock(return_value=np.array([0, 1, 0]))
    model.train = MagicMock(return_value=None)
    model.evaluate = MagicMock(return_value={'accuracy': 0.85})
    return model


# ===========================
# Configuration Fixtures
# ===========================

@pytest.fixture
def config_dict():
    """
    فیکسچر برای تنظیمات نمونه
    """
    return {
        'api_key': 'test_key_123',
        'api_secret': 'test_secret_456',
        'account_type': 'demo',
        'leverage': 10,
        'symbol': 'EURUSD',
        'timeframe': '1H',
        'risk_percent': 2.0,
    }


@pytest.fixture
def logger_config():
    """
    فیکسچر برای تنظیمات logging
    """
    return {
        'level': 'DEBUG',
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'handlers': ['console', 'file'],
    }


# ===========================
# Timing Fixtures
# ===========================

@pytest.fixture
def benchmark_timer():
    """
    فیکسچر برای اندازه‌گیری زمان اجرای تست
    """
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = datetime.now()
        
        def stop(self):
            self.end_time = datetime.now()
        
        def elapsed(self):
            if self.start_time and self.end_time:
                return (self.end_time - self.start_time).total_seconds()
            return None
    
    return Timer()


# ===========================
# Cleanup Fixtures
# ===========================

@pytest.fixture(autouse=True)
def cleanup():
    """
    فیکسچر برای cleanup خودکار بعد از هر تست
    """
    yield  # تست اجرا می‌شود
    # Cleanup کد اینجا قرار می‌گیرد
    pass


# ===========================
# Parametrize Helpers
# ===========================

def pytest_generate_tests(metafunc):
    """
    Pytest Hook برای parametrize کردن تست‌ها
    """
    if "sample_symbols" in metafunc.fixturenames:
        symbols = ['EURUSD', 'GBPUSD', 'USDJPY']
        metafunc.parametrize("sample_symbols", symbols)
    
    if "timeframes" in metafunc.fixturenames:
        frames = ['5m', '15m', '1h', '4h', '1d']
        metafunc.parametrize("timeframes", frames)


# ===========================
# Exception Handling Fixtures
# ===========================

@pytest.fixture
def assert_raises_context():
    """
    فیکسچر برای assert کردن Exceptions
    """
    from contextlib import contextmanager
    
    @contextmanager
    def _assert_raises(exception_type, message=None):
        try:
            yield
            pytest.fail(f"Expected {exception_type.__name__} to be raised")
        except exception_type as e:
            if message and message not in str(e):
                pytest.fail(f"Expected message '{message}' not found in exception: {str(e)}")
    
    return _assert_raises


# ===========================
# Utility Functions
# ===========================

def create_test_dataframe(rows=100, columns=None):
    """
    کمکی برای ایجاد DataFrame تست
    """
    if columns is None:
        columns = ['open', 'high', 'low', 'close', 'volume']
    
    dates = pd.date_range(start='2023-01-01', periods=rows, freq='D')
    data = {col: np.random.random(rows) * 100 for col in columns}
    df = pd.DataFrame(data, index=dates)
    return df


@pytest.fixture
def temp_data_dir(tmp_path):
    """
    فیکسچر برای فولدر موقت برای ذخیره‌سازی داده‌های تست
    """
    return tmp_path


# ===========================
# Session Scope Fixtures
# ===========================

@pytest.fixture(scope="session")
def test_session_config():
    """
    تنظیمات برای کل جلسه تست
    """
    return {
        'test_environment': 'CI',
        'timeout': 300,
        'log_level': 'DEBUG',
    }
