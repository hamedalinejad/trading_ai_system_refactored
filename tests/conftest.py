# tests/conftest.py
"""
Pytest Configuration و Fixtures
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock


@pytest.fixture
def sample_ohlcv():
    """
    داده نمونه OHLCV را تولید می‌کند
    """
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    data = {
        'open': np.random.uniform(1.0, 1.5, 100),
        'high': np.random.uniform(1.2, 1.6, 100),
        'low': np.random.uniform(0.9, 1.4, 100),
        'close': np.random.uniform(1.0, 1.5, 100),
        'volume': np.random.uniform(1000000, 5000000, 100)
    }
    df = pd.DataFrame(data, index=dates)
    df['timestamp'] = dates
    return df


@pytest.fixture
def sample_features():
    """
    داده نمونه Features را تولید می‌کند
    """
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    features = {
        'rsi': np.random.uniform(20, 80, 100),
        'macd': np.random.uniform(-0.05, 0.05, 100),
        'sma_50': np.random.uniform(1.0, 1.5, 100),
        'sma_200': np.random.uniform(0.95, 1.45, 100),
        'volatility': np.random.uniform(0.01, 0.05, 100),
        'atr': np.random.uniform(0.01, 0.05, 100)
    }
    df = pd.DataFrame(features, index=dates)
    return df


@pytest.fixture
def mock_broker():
    """
    Mock شده Broker را برای تست‌ها فراهم می‌کند
    """
    broker = MagicMock()
    broker.get_account_balance = MagicMock(return_value=10000.0)
    broker.get_positions = MagicMock(return_value=[])
    broker.place_order = MagicMock(return_value={'order_id': '12345'})
    broker.cancel_order = MagicMock(return_value=True)
    broker.get_order_status = MagicMock(return_value='FILLED')
    return broker


@pytest.fixture
def mock_data_fetcher():
    """
    Mock شده Data Fetcher را برای تست‌ها فراهم می‌کند
    """
    fetcher = MagicMock()
    fetcher.fetch = MagicMock()
    fetcher.get_historical_data = MagicMock()
    fetcher.is_connected = MagicMock(return_value=True)
    return fetcher


@pytest.fixture
def sample_config():
    """
    نمونه Configuration را برای تست‌ها فراهم می‌کند
    """
    config = {
        'symbol': 'EURUSD',
        'timeframe': '1H',
        'initial_balance': 10000.0,
        'max_position_size': 2.0,
        'stop_loss_pips': 50,
        'take_profit_pips': 100,
        'max_spread': 2.0,
        'commission': 0.0001
    }
    return config


@pytest.fixture
def sample_trades():
    """
    داده نمونه معاملات را برای تست‌ها فراهم می‌کند
    """
    trades = [
        {
            'entry_time': datetime(2023, 1, 1, 10, 0),
            'exit_time': datetime(2023, 1, 1, 12, 0),
            'entry_price': 1.0500,
            'exit_price': 1.0550,
            'direction': 'BUY',
            'lot_size': 1.0,
            'pnl': 50.0,
            'pnl_percent': 0.48
        },
        {
            'entry_time': datetime(2023, 1, 2, 10, 0),
            'exit_time': datetime(2023, 1, 2, 11, 30),
            'entry_price': 1.0550,
            'exit_price': 1.0520,
            'direction': 'SELL',
            'lot_size': 1.0,
            'pnl': 30.0,
            'pnl_percent': 0.28
        }
    ]
    return trades


@pytest.fixture
def mock_model():
    """
    Mock شده ML Model را برای تست‌ها فراهم می‌کند
    """
    model = MagicMock()
    model.predict = MagicMock(return_value=np.array([0, 1, 0, 1, 1]))
    model.predict_proba = MagicMock(return_value=np.array([
        [0.7, 0.3],
        [0.2, 0.8],
        [0.6, 0.4],
        [0.3, 0.7],
        [0.4, 0.6]
    ]))
    model.score = MagicMock(return_value=0.85)
    return model


@pytest.fixture
def sample_backtest_results():
    """
    نتایج Backtest نمونه را برای تست‌ها فراهم می‌کند
    """
    results = {
        'total_trades': 45,
        'winning_trades': 28,
        'losing_trades': 17,
        'win_rate': 0.6222,
        'gross_profit': 5500.0,
        'gross_loss': -1800.0,
        'net_profit': 3700.0,
        'profit_factor': 3.06,
        'max_drawdown': -1200.0,
        'max_drawdown_percent': -12.0,
        'sharpe_ratio': 1.45,
        'sortino_ratio': 2.10,
        'recovery_factor': 3.08,
        'consecutive_wins': 5,
        'consecutive_losses': 3
    }
    return results


@pytest.fixture
def sample_positions():
    """
    نمونه Positions را برای تست‌ها فراهم می‌کند
    """
    positions = [
        {
            'symbol': 'EURUSD',
            'direction': 'LONG',
            'lot_size': 1.5,
            'entry_price': 1.0500,
            'current_price': 1.0550,
            'unrealized_pnl': 75.0,
            'open_time': datetime(2023, 1, 1, 10, 0)
        },
        {
            'symbol': 'GBPUSD',
            'direction': 'SHORT',
            'lot_size': 1.0,
            'entry_price': 1.2500,
            'current_price': 1.2480,
            'unrealized_pnl': 20.0,
            'open_time': datetime(2023, 1, 1, 12, 0)
        }
    ]
    return positions


@pytest.fixture(scope="session")
def test_data_dir(tmp_path_factory):
    """
    دایرکتوری موقت برای ذخیره‌سازی فایل‌های تست
    """
    return tmp_path_factory.mktemp("test_data")


def pytest_configure(config):
    """
    Pytest Markers را تعریف می‌کند
    """
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )
    config.addinivalue_line(
        "markers", "security: marks tests as security tests"
    )


@pytest.fixture(autouse=True)
def reset_random_seed():
    """
    هر تست را با Seed ثابت شروع می‌کند
    """
    np.random.seed(42)
