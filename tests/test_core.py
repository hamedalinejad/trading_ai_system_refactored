# tests/test_core.py
"""
تست‌های Core Module
"""

import pytest
from datetime import datetime, timedelta


class TestCoreModuleConfig:
    """تست‌های Core Configuration"""

    def test_config_creation_with_defaults(self, sample_config):
        """تست ایجاد config با مقادیر پیشفرض"""
        assert sample_config['symbol'] == 'EURUSD'
        assert sample_config['initial_balance'] == 10000.0
        assert sample_config['timeframe'] == '1H'

    def test_config_required_fields(self, sample_config):
        """تست اینکه تمام فیلد‌های ضروری موجود باشند"""
        required_fields = [
            'symbol', 'timeframe', 'initial_balance', 
            'max_position_size', 'stop_loss_pips'
        ]
        for field in required_fields:
            assert field in sample_config

    def test_config_values_are_valid(self, sample_config):
        """تست اینکه مقادیر config معتبر باشند"""
        assert sample_config['initial_balance'] > 0
        assert sample_config['max_position_size'] > 0
        assert sample_config['max_spread'] > 0
        assert 0 <= sample_config['commission'] <= 1

    def test_config_symbol_format(self, sample_config):
        """تست فرمت symbol"""
        assert len(sample_config['symbol']) == 6
        assert '_' in sample_config['symbol'] or sample_config['symbol'].isupper()

    def test_config_timeframe_valid(self, sample_config):
        """تست اینکه timeframe معتبر باشد"""
        valid_timeframes = ['1M', '5M', '15M', '30M', '1H', '4H', '1D', '1W']
        assert sample_config['timeframe'] in valid_timeframes


class TestEnvironmentSetup:
    """تست‌های Setup محیط"""

    def test_imports_work(self):
        """تست اینکه module‌های اصلی import شوند"""
        try:
            import numpy as np
            import pandas as pd
            assert True
        except ImportError:
            assert False, "Required packages not installed"

    def test_mock_objects_work(self, mock_broker):
        """تست اینکه Mock Objects درست کار کنند"""
        assert mock_broker is not None
        balance = mock_broker.get_account_balance()
        assert balance == 10000.0

    def test_fixtures_are_available(self, sample_ohlcv, sample_features):
        """تست اینکه تمام fixtures دسترسی‌پذیر باشند"""
        assert sample_ohlcv is not None
        assert sample_features is not None
        assert len(sample_ohlcv) > 0
        assert len(sample_features) > 0

    def test_random_seed_is_set(self):
        """تست اینکه Random Seed تعریف شده باشد"""
        import numpy as np
        # اولین random call باید همیشه یکسان باشد
        np.random.seed(42)
        val1 = np.random.random()
        
        np.random.seed(42)
        val2 = np.random.random()
        
        assert val1 == val2


class TestCoreLogging:
    """تست‌های Core Logging"""

    def test_logger_configuration(self):
        """تست اینکه logger درست کانفیگ شده باشد"""
        import logging
        logger = logging.getLogger('trading_ai_system')
        assert logger is not None
        assert logger.level >= logging.DEBUG

    def test_logger_handlers(self):
        """تست اینکه logger handlers موجود باشند"""
        import logging
        logger = logging.getLogger('trading_ai_system')
        assert len(logger.handlers) > 0 or len(logging.root.handlers) > 0


class TestErrorHandling:
    """تست‌های Error Handling"""

    def test_invalid_symbol_raises_error(self):
        """تست اینکه symbol نامعتبر Exception raise کند"""
        from trading_ai_system.core import validate_symbol
        
        with pytest.raises(ValueError):
            validate_symbol("INVALID")

    def test_invalid_timeframe_raises_error(self):
        """تست اینکه timeframe نامعتبر Exception raise کند"""
        from trading_ai_system.core import validate_timeframe
        
        with pytest.raises(ValueError):
            validate_timeframe("INVALID_TF")

    def test_negative_balance_raises_error(self):
        """تست اینکه balance منفی Exception raise کند"""
        from trading_ai_system.core import validate_balance
        
        with pytest.raises(ValueError):
            validate_balance(-1000)

    def test_invalid_position_size_raises_error(self):
        """تست اینکه position size نامعتبر Exception raise کند"""
        from trading_ai_system.core import validate_position_size
        
        with pytest.raises(ValueError):
            validate_position_size(0)


class TestDateTimeHandling:
    """تست‌های DateTime Handling"""

    def test_datetime_parsing(self):
        """تست Parse کردن DateTime"""
        from trading_ai_system.core import parse_datetime
        
        date_str = "2023-01-01"
        parsed = parse_datetime(date_str)
        assert isinstance(parsed, datetime)

    def test_timeframe_to_minutes_conversion(self):
        """تست تبدیل Timeframe به دقیقه‌ها"""
        from trading_ai_system.core import timeframe_to_minutes
        
        assert timeframe_to_minutes('1M') == 1
        assert timeframe_to_minutes('5M') == 5
        assert timeframe_to_minutes('1H') == 60
        assert timeframe_to_minutes('1D') == 1440

    def test_date_range_calculation(self):
        """تست محاسبه Date Range"""
        from trading_ai_system.core import calculate_date_range
        
        start = datetime(2023, 1, 1)
        end = datetime(2023, 1, 31)
        days = calculate_date_range(start, end)
        assert days == 30


class TestSystemHealth:
    """تست‌های Health Check سیستم"""

    def test_memory_availability(self):
        """تست دسترسی به Memory"""
        import psutil
        memory = psutil.virtual_memory()
        assert memory.available > 0

    def test_disk_space_availability(self):
        """تست دسترسی به Disk Space"""
        import os
        stat = os.statvfs('/')
        available = stat.f_bavail * stat.f_frsize
        assert available > 0

    @pytest.mark.slow
    def test_system_performance(self):
        """تست Performance سیستم"""
        import time
        start = time.time()
        # Dummy operation
        _ = sum([i**2 for i in range(1000000)])
        elapsed = time.time() - start
        # باید کمتر از 5 ثانیه طول بکشد
        assert elapsed < 5.0


class TestConfiguration:
    """تست‌های Configuration Validation"""

    def test_load_default_config(self):
        """تست Load Default Configuration"""
        from trading_ai_system.core import load_default_config
        
        config = load_default_config()
        assert config is not None
        assert isinstance(config, dict)

    def test_config_merge(self):
        """تست Merge Configurations"""
        from trading_ai_system.core import merge_config
        
        default = {'a': 1, 'b': 2}
        custom = {'b': 3, 'c': 4}
        merged = merge_config(default, custom)
        
        assert merged['a'] == 1
        assert merged['b'] == 3
        assert merged['c'] == 4

    def test_config_validation(self):
        """تست Configuration Validation"""
        from trading_ai_system.core import validate_config
        
        valid_config = {
            'symbol': 'EURUSD',
            'initial_balance': 10000.0,
            'timeframe': '1H'
        }
        
        assert validate_config(valid_config) is True

    def test_invalid_config_raises_error(self):
        """تست Invalid Configuration raise Error"""
        from trading_ai_system.core import validate_config
        
        invalid_config = {
            'symbol': 'INVALID',
            'initial_balance': -1000,
            'timeframe': 'BAD_TF'
        }
        
        with pytest.raises(ValueError):
            validate_config(invalid_config)


class TestConstants:
    """تست‌های Constants"""

    def test_default_constants(self):
        """تست Default Constants"""
        from trading_ai_system.core import DEFAULT_LEVERAGE
        from trading_ai_system.core import DEFAULT_COMMISSION
        from trading_ai_system.core import MIN_LOT_SIZE
        
        assert DEFAULT_LEVERAGE > 0
        assert DEFAULT_COMMISSION >= 0
        assert MIN_LOT_SIZE > 0

    def test_supported_symbols(self):
        """تست Supported Symbols"""
        from trading_ai_system.core import SUPPORTED_SYMBOLS
        
        assert 'EURUSD' in SUPPORTED_SYMBOLS
        assert len(SUPPORTED_SYMBOLS) > 0

    def test_supported_timeframes(self):
        """تست Supported Timeframes"""
        from trading_ai_system.core import SUPPORTED_TIMEFRAMES
        
        assert '1H' in SUPPORTED_TIMEFRAMES
        assert '1D' in SUPPORTED_TIMEFRAMES
        assert len(SUPPORTED_TIMEFRAMES) > 0
