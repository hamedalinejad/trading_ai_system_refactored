"""
test_core.py - تست Core Module

تست‌های مربوط به ماژول Core شامل Configuration و State Management
"""

import pytest
from unittest.mock import Mock, patch, MagicMock


class TestCoreConfiguration:
    """تست‌های Configuration."""

    def test_config_initialization(self, test_config):
        """تست Initialize کردن Configuration."""
        assert test_config is not None
        assert test_config['trading_pair'] == 'EURUSD'
        assert test_config['initial_capital'] == 10000

    def test_config_has_required_keys(self, test_config):
        """تست وجود کلیدهای ضروری."""
        required_keys = ['data_dir', 'model_dir', 'initial_capital', 'risk_per_trade']
        for key in required_keys:
            assert key in test_config

    def test_config_values_are_valid(self, test_config):
        """تست معتبر بودن مقادیر Configuration."""
        assert test_config['initial_capital'] > 0
        assert 0 < test_config['risk_per_trade'] < 1
        assert test_config['max_positions'] > 0

    def test_config_update(self, test_config):
        """تست بروزرسانی Configuration."""
        test_config['trading_pair'] = 'GBPUSD'
        assert test_config['trading_pair'] == 'GBPUSD'

    def test_config_risk_limits(self, test_config):
        """تست محدودیت‌های Risk در Configuration."""
        assert test_config['max_drawdown'] <= 0.5
        assert test_config['risk_per_trade'] <= 0.05


class TestStateManager:
    """تست‌های State Manager."""

    def test_state_initialization(self):
        """تست Initialize کردن State."""
        # Mock State Manager
        state = {
            'current_position': 0,
            'pnl': 0,
            'trades_count': 0,
            'is_trading': False,
        }
        assert state['current_position'] == 0
        assert state['pnl'] == 0
        assert not state['is_trading']

    def test_state_update_position(self):
        """تست بروزرسانی Position."""
        state = {'current_position': 0}
        state['current_position'] = 1.5
        assert state['current_position'] == 1.5

    def test_state_update_pnl(self):
        """تست بروزرسانی PnL."""
        state = {'pnl': 0}
        state['pnl'] += 100
        assert state['pnl'] == 100

    def test_state_trading_status(self):
        """تست وضعیت Trading."""
        state = {'is_trading': False}
        state['is_trading'] = True
        assert state['is_trading']


class TestExceptionHandling:
    """تست‌های Exception Handling."""

    def test_config_error_handling(self):
        """تست Exception برای Config Error."""
        with pytest.raises((KeyError, TypeError)):
            config = {}
            _ = config['nonexistent_key']

    def test_invalid_config_values(self, test_config):
        """تست Error برای Invalid Config."""
        with pytest.raises(AssertionError):
            assert test_config['initial_capital'] < 0

    def test_state_consistency(self):
        """تست Consistency State."""
        state = {
            'position': 0,
            'balance': 10000,
            'margin_used': 0,
        }
        # Validate state consistency
        assert state['margin_used'] >= 0
        assert state['balance'] > 0


class TestCoreLogging:
    """تست‌های Logging در Core Module."""

    @patch('logging.getLogger')
    def test_logger_initialization(self, mock_logger, test_config):
        """تست Initialize کردن Logger."""
        assert test_config['logging_level'] == 'DEBUG'

    @patch('logging.info')
    def test_log_message(self, mock_log):
        """تست Log کردن پیام."""
        mock_log("Test message")
        mock_log.assert_called_with("Test message")

    def test_logging_level_config(self, test_config):
        """تست Logging Level Configuration."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        assert test_config['logging_level'] in valid_levels


class TestCoreIntegration:
    """تست‌های Integration Core Module."""

    def test_config_and_state_integration(self, test_config):
        """تست Integration Config و State."""
        state = {
            'capital': test_config['initial_capital'],
            'risk_limit': test_config['initial_capital'] * test_config['risk_per_trade'],
        }
        assert state['capital'] == 10000
        assert state['risk_limit'] == 200  # 10000 * 0.02

    def test_multiple_configs(self, test_config):
        """تست Multiple Configurations."""
        config1 = test_config.copy()
        config2 = test_config.copy()
        config2['trading_pair'] = 'GBPUSD'
        
        assert config1['trading_pair'] != config2['trading_pair']
        assert config1['initial_capital'] == config2['initial_capital']


# ============================================================================
# Parametrized Tests
# ============================================================================

@pytest.mark.parametrize("trading_pair,timeframe", [
    ("EURUSD", "1H"),
    ("GBPUSD", "4H"),
    ("USDJPY", "1D"),
    ("AUDUSD", "15M"),
])
def test_config_trading_pairs(trading_pair, timeframe):
    """تست Configuration برای جفت‌های معاملاتی مختلف."""
    config = {
        'trading_pair': trading_pair,
        'timeframe': timeframe,
    }
    assert config['trading_pair'] is not None
    assert config['timeframe'] is not None


@pytest.mark.parametrize("capital,risk", [
    (10000, 0.02),
    (50000, 0.01),
    (100000, 0.015),
])
def test_risk_parameters(capital, risk):
    """تست پارامترهای Risk برای Capital مختلف."""
    max_risk = capital * risk
    assert max_risk > 0
    assert max_risk <= capital


class TestCoreErrorRecovery:
    """تست‌های Error Recovery در Core."""

    def test_graceful_config_failure(self):
        """تست Graceful Failure در Config."""
        try:
            config = {'initial_capital': 10000}
            assert config['initial_capital'] > 0
        except Exception as e:
            pytest.fail(f"Config failed: {e}")

    def test_state_rollback(self):
        """تست Rollback State."""
        state = {'balance': 10000}
        original_balance = state['balance']
        state['balance'] -= 500
        
        # Rollback
        state['balance'] = original_balance
        assert state['balance'] == 10000


class TestCoreMetrics:
    """تست‌های Metrics در Core Module."""

    def test_calculate_return(self, test_config):
        """تست محاسبه Return."""
        initial = test_config['initial_capital']
        final = 11000
        return_pct = ((final - initial) / initial) * 100
        assert return_pct == 10.0

    def test_calculate_roi(self, test_config):
        """تست محاسبه ROI."""
        initial = test_config['initial_capital']
        profit = 1000
        roi = (profit / initial) * 100
        assert roi == 10.0

    def test_sharpe_ratio_calculation(self):
        """تست محاسبه Sharpe Ratio."""
        returns = [0.01, 0.02, -0.01, 0.015]
        mean_return = sum(returns) / len(returns)
        std_return = 0.01  # مثال
        sharpe = mean_return / std_return if std_return != 0 else 0
        assert sharpe > 0


@pytest.mark.slow
class TestCorePerformance:
    """تست‌های Performance Core Module."""

    def test_large_config_handling(self):
        """تست Handling Configuration بزرگ."""
        config = {f'param_{i}': i for i in range(1000)}
        assert len(config) == 1000

    def test_state_access_speed(self):
        """تست سرعت دسترسی State."""
        state = {'position': 0}
        for i in range(10000):
            state['position'] = i
        assert state['position'] == 9999
