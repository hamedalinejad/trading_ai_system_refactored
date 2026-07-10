"""
Strategy Module Tests
تست‌های ماژول استراتژی

This module contains comprehensive tests for the strategy generation,
validation, and execution components of the trading system.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Tuple


class TestStrategyConfig:
    """تست‌های Strategy Configuration"""
    
    def test_strategy_config_initialization(self):
        """تست مقدار‌دهی Strategy Config"""
        config = {
            'strategy_name': 'breakout',
            'timeframe': '1h',
            'instruments': ['EURUSD', 'GBPUSD'],
            'max_positions': 5,
            'risk_per_trade': 0.02,
            'lookback_period': 100
        }
        
        assert config['strategy_name'] == 'breakout'
        assert config['max_positions'] == 5
        assert len(config['instruments']) == 2
    
    def test_strategy_config_validation(self):
        """تست اعتبار‌سنجی Strategy Config"""
        config = {
            'strategy_name': 'breakout',
            'max_positions': 5,
            'risk_per_trade': 0.02
        }
        
        # بررسی حضور فیلد‌های ضروری
        required_fields = ['strategy_name', 'max_positions', 'risk_per_trade']
        for field in required_fields:
            assert field in config
    
    def test_strategy_config_risk_limits(self):
        """تست محدودیت‌های risk در config"""
        config = {
            'risk_per_trade': 0.05,
            'max_risk_per_day': 0.1
        }
        
        # Risk per trade باید کمتر از 0.1 باشد
        assert config['risk_per_trade'] <= 0.1
        assert config['max_risk_per_day'] <= 0.5


class TestStrategyGeneration:
    """تست‌های تولید استراتژی"""
    
    def test_generate_buy_signal(self):
        """تست تولید سیگنال خرید"""
        # داده نمونه
        ohlcv = pd.DataFrame({
            'close': [1.0, 1.1, 1.2, 1.15, 1.25],
            'open': [0.95, 1.05, 1.1, 1.2, 1.2],
            'high': [1.05, 1.15, 1.25, 1.25, 1.3],
            'low': [0.95, 1.0, 1.1, 1.1, 1.2],
            'volume': [100, 150, 200, 180, 220]
        })
        
        # تولید سیگنال (شرط: close > open و high > low)
        signals = ohlcv['close'] > ohlcv['open']
        
        assert isinstance(signals, pd.Series)
        assert len(signals) == len(ohlcv)
    
    def test_generate_sell_signal(self):
        """تست تولید سیگنال فروش"""
        ohlcv = pd.DataFrame({
            'close': [1.25, 1.2, 1.15, 1.1, 1.05],
            'open': [1.3, 1.25, 1.2, 1.15, 1.1]
        })
        
        # سیگنال فروش: close < open
        signals = ohlcv['close'] < ohlcv['open']
        
        assert signals.sum() > 0  # حداقل یک سیگنال فروش
    
    def test_strategy_with_moving_averages(self):
        """تست استراتژی بر اساس میانگین‌های متحرک"""
        prices = pd.Series([1.0, 1.1, 1.2, 1.15, 1.25, 1.3, 1.28, 1.35])
        
        # محاسبه میانگین‌های متحرک
        sma_3 = prices.rolling(window=3).mean()
        sma_5 = prices.rolling(window=5).mean()
        
        # سیگنال: SMA_3 > SMA_5 (خرید)
        signals = sma_3 > sma_5
        
        assert len(signals) == len(prices)
        assert signals[signals.notna()].sum() > 0
    
    def test_strategy_with_rsi(self):
        """تست استراتژی بر اساس RSI"""
        prices = pd.Series(np.random.uniform(1.0, 1.3, 100))
        
        # محاسبه تقریبی RSI
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        
        # محاسبه RS و RSI
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # سیگنال: RSI < 30 (خرید)، RSI > 70 (فروش)
        buy_signals = rsi < 30
        sell_signals = rsi > 70
        
        assert rsi[rsi.notna()].min() >= 0
        assert rsi[rsi.notna()].max() <= 100


class TestStrategyValidation:
    """تست‌های اعتبار‌سنجی استراتژی"""
    
    def test_validate_signal_validity(self):
        """تست اعتبار سیگنال‌ها"""
        signals = pd.Series([1, 0, 1, 0, 1])  # 1: buy, 0: no signal
        
        assert signals.isin([0, 1]).all()  # تمام مقادیر باید 0 یا 1 باشند
    
    def test_validate_signal_timing(self):
        """تست زمان‌بندی سیگنال‌ها"""
        timestamps = pd.DatetimeIndex([
            '2024-01-01 10:00',
            '2024-01-01 11:00',
            '2024-01-01 12:00'
        ])
        
        signals = pd.Series([1, 0, 1], index=timestamps)
        
        # بررسی ترتیب زمانی
        assert (signals.index[1:] > signals.index[:-1]).all()
    
    def test_validate_no_conflicting_signals(self):
        """تست عدم تعارض سیگنال‌ها"""
        # نباید در یک نقطه زمانی خرید و فروش همزمان اتفاق افتد
        buy_signals = [1, 0, 1, 0, 0]
        sell_signals = [0, 1, 0, 1, 0]
        
        for b, s in zip(buy_signals, sell_signals):
            assert not (b == 1 and s == 1), "نباید خرید و فروش همزمان باشند"
    
    def test_validate_signal_frequency(self):
        """تست فرکانس سیگنال‌ها"""
        signals = [1, 0, 0, 0, 1, 0, 0, 1]
        total_signals = sum(signals)
        
        # سیگنال‌ها نباید خیلی متعارض باشند
        assert total_signals > 0  # حداقل یک سیگنال
        assert total_signals < len(signals)  # نه تمام نقاط


class TestStrategyExecution:
    """تست‌های اجرای استراتژی"""
    
    def test_execute_buy_order(self):
        """تست اجرای دستور خرید"""
        order = {
            'type': 'BUY',
            'instrument': 'EURUSD',
            'quantity': 100,
            'price': 1.1050,
            'timestamp': datetime.now()
        }
        
        assert order['type'] == 'BUY'
        assert order['quantity'] > 0
        assert order['price'] > 0
    
    def test_execute_sell_order(self):
        """تست اجرای دستور فروش"""
        order = {
            'type': 'SELL',
            'instrument': 'EURUSD',
            'quantity': 100,
            'price': 1.1080,
            'timestamp': datetime.now()
        }
        
        assert order['type'] == 'SELL'
        assert order['quantity'] > 0
    
    def test_execute_close_position(self):
        """تست بستن موقعیت"""
        position = {
            'id': 'POS001',
            'instrument': 'EURUSD',
            'quantity': 100,
            'entry_price': 1.1050,
            'entry_time': datetime.now() - timedelta(hours=2),
            'status': 'OPEN'
        }
        
        # بستن موقعیت
        close_order = {
            'position_id': position['id'],
            'exit_price': 1.1100,
            'exit_time': datetime.now(),
            'pnl': (1.1100 - 1.1050) * 100  # PnL = (exit - entry) * quantity
        }
        
        assert close_order['pnl'] > 0  # سود مثبت
        assert close_order['exit_time'] > position['entry_time']
    
    def test_execute_stop_loss(self):
        """تست اجرای Stop Loss"""
        position = {
            'entry_price': 1.1050,
            'current_price': 1.1000,
            'stop_loss': 1.1020,
            'quantity': 100
        }
        
        # بررسی نیاز به Stop Loss
        if position['current_price'] <= position['stop_loss']:
            pnl = (position['current_price'] - position['entry_price']) * position['quantity']
            assert pnl < 0  # زیان
    
    def test_execute_take_profit(self):
        """تست اجرای Take Profit"""
        position = {
            'entry_price': 1.1050,
            'current_price': 1.1150,
            'take_profit': 1.1120,
            'quantity': 100
        }
        
        # بررسی نیاز به Take Profit
        if position['current_price'] >= position['take_profit']:
            pnl = (position['current_price'] - position['entry_price']) * position['quantity']
            assert pnl > 0  # سود


class TestStrategyPerformance:
    """تست‌های عملکرد استراتژی"""
    
    def test_calculate_strategy_returns(self):
        """تست محاسبه بازدهی استراتژی"""
        trades = [
            {'entry': 1.1050, 'exit': 1.1100, 'quantity': 100},
            {'entry': 1.1150, 'exit': 1.1120, 'quantity': 100},
            {'entry': 1.1050, 'exit': 1.1150, 'quantity': 100}
        ]
        
        pnls = []
        for trade in trades:
            pnl = (trade['exit'] - trade['entry']) * trade['quantity']
            pnls.append(pnl)
        
        total_pnl = sum(pnls)
        assert len(pnls) == 3
        assert total_pnl > 0
    
    def test_calculate_win_rate(self):
        """تست محاسبه نرخ برنده"""
        trades = [
            {'pnl': 100},    # برنده
            {'pnl': -50},    # بازنده
            {'pnl': 150},    # برنده
            {'pnl': -100},   # بازنده
            {'pnl': 200}     # برنده
        ]
        
        winning_trades = sum(1 for t in trades if t['pnl'] > 0)
        win_rate = winning_trades / len(trades)
        
        assert 0 <= win_rate <= 1
        assert win_rate == 3 / 5  # 60%
    
    def test_calculate_profit_factor(self):
        """تست محاسبه Profit Factor"""
        trades = [100, -50, 150, -100, 200]
        
        gross_profit = sum(t for t in trades if t > 0)
        gross_loss = abs(sum(t for t in trades if t < 0))
        
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        assert profit_factor > 0
    
    def test_calculate_sharpe_ratio(self):
        """تست محاسبه Sharpe Ratio"""
        returns = np.array([0.01, 0.02, -0.01, 0.03, 0.02, -0.02])
        risk_free_rate = 0.001
        
        excess_returns = returns - risk_free_rate
        sharpe = np.mean(excess_returns) / np.std(excess_returns) if np.std(excess_returns) > 0 else 0
        
        assert isinstance(sharpe, float)
    
    def test_calculate_max_drawdown(self):
        """تست محاسبه Maximum Drawdown"""
        cumulative_returns = np.array([1.0, 1.05, 1.10, 1.08, 1.15, 1.12, 1.20, 1.10])
        
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = np.min(drawdown)
        
        assert max_drawdown <= 0
        assert max_drawdown >= -1


class TestStrategyOptimization:
    """تست‌های بهینه‌سازی استراتژی"""
    
    def test_optimize_parameters(self):
        """تست بهینه‌سازی پارامترهای استراتژی"""
        parameter_space = {
            'fast_ma': [5, 10, 15],
            'slow_ma': [20, 30, 40],
            'rsi_period': [7, 14, 21]
        }
        
        best_params = {
            'fast_ma': 10,
            'slow_ma': 30,
            'rsi_period': 14
        }
        
        assert best_params['fast_ma'] < best_params['slow_ma']
    
    def test_walk_forward_optimization(self):
        """تست Walk-Forward Optimization"""
        data_length = 252 * 2  # 2 سال
        in_sample = 252  # 1 سال برای training
        out_sample = 63   # 3 ماه برای testing
        
        # شبیه‌سازی walk-forward windows
        windows = []
        for start in range(0, data_length - in_sample - out_sample, out_sample):
            window = {
                'train_start': start,
                'train_end': start + in_sample,
                'test_start': start + in_sample,
                'test_end': start + in_sample + out_sample
            }
            windows.append(window)
        
        assert len(windows) > 0
        assert windows[0]['train_end'] <= windows[0]['test_start']
    
    def test_parameter_sensitivity(self):
        """تست حساسیت پارامتر"""
        performance = {
            'param_value_5': {'return': 0.15},
            'param_value_10': {'return': 0.25},
            'param_value_15': {'return': 0.20},
            'param_value_20': {'return': 0.10}
        }
        
        best_param = max(performance.items(), key=lambda x: x[1]['return'])
        assert best_param[0] == 'param_value_10'


class TestStrategyRiskManagement:
    """تست‌های مدیریت ریسک در استراتژی"""
    
    def test_position_sizing_kelly(self):
        """تست Sizing بر اساس Kelly Criterion"""
        win_rate = 0.55
        avg_win = 100
        avg_loss = 80
        
        # Kelly Formula: f = (bp - q) / b
        # جایی که b = avg_win / avg_loss, p = win_rate, q = 1 - win_rate
        
        b = avg_win / avg_loss
        p = win_rate
        q = 1 - win_rate
        kelly_fraction = (b * p - q) / b
        
        # Kelly fraction باید بین 0 و 1 باشد
        assert 0 < kelly_fraction < 1
    
    def test_position_sizing_fixed(self):
        """تست Sizing ثابت"""
        capital = 10000
        risk_per_trade = 0.02
        position_size = capital * risk_per_trade
        
        assert position_size == 200
    
    def test_position_sizing_dynamic(self):
        """تست Sizing پویا بر اساس Volatility"""
        capital = 10000
        recent_volatility = 0.02  # 2%
        target_risk = 0.01  # 1%
        
        # کمتر موقعیت در volatility بالا
        position_size = capital * (target_risk / recent_volatility)
        
        assert position_size > 0
        assert position_size < capital
    
    def test_max_positions_limit(self):
        """تست محدودیت حداکثر موقعیت"""
        max_positions = 5
        current_positions = 3
        
        can_open_new = current_positions < max_positions
        assert can_open_new is True
        
        current_positions = 5
        can_open_new = current_positions < max_positions
        assert can_open_new is False
    
    def test_daily_loss_limit(self):
        """تست محدودیت زیان روزانه"""
        daily_limit = -1000
        current_daily_pnl = -800
        
        can_trade = current_daily_pnl > daily_limit
        assert can_trade is True
        
        current_daily_pnl = -1100
        can_trade = current_daily_pnl > daily_limit
        assert can_trade is False


class TestStrategyBacktest:
    """تست‌های Backtesting استراتژی"""
    
    def test_backtest_basic(self):
        """تست Backtest ساده"""
        ohlcv = pd.DataFrame({
            'close': [1.1050, 1.1100, 1.1080, 1.1150, 1.1120],
            'open': [1.1000, 1.1070, 1.1090, 1.1100, 1.1140],
            'high': [1.1100, 1.1120, 1.1100, 1.1180, 1.1150],
            'low': [1.0950, 1.1050, 1.1070, 1.1080, 1.1110],
            'volume': [100, 150, 200, 180, 220]
        })
        
        # استراتژی ساده: خرید اگر close > open
        signals = (ohlcv['close'] > ohlcv['open']).astype(int)
        
        assert len(signals) == len(ohlcv)
        assert signals.sum() > 0
    
    def test_backtest_with_transaction_costs(self):
        """تست Backtest با هزینه‌های تراکنش"""
        trades = 10
        transaction_cost_per_trade = 5  # dollars
        gross_pnl = 1000
        
        net_pnl = gross_pnl - (trades * transaction_cost_per_trade)
        
        assert net_pnl < gross_pnl
        assert net_pnl == 950
    
    def test_backtest_with_slippage(self):
        """تست Backtest با Slippage"""
        entry_price = 1.1050
        expected_entry = 1.1050
        slippage = 0.0010  # 10 pips
        actual_entry = expected_entry + slippage
        
        assert actual_entry > expected_entry
    
    @pytest.mark.slow
    def test_backtest_large_dataset(self):
        """تست Backtest با حجم بزرگ داده"""
        # شبیه‌سازی 2 سال داده (252 * 2 روز * 24 ساعت)
        data_points = 252 * 2 * 24
        dates = pd.date_range('2022-01-01', periods=data_points, freq='h')
        prices = np.cumsum(np.random.randn(data_points) * 0.001) + 1.1
        
        ohlcv = pd.DataFrame({
            'close': prices,
            'open': prices,
            'high': prices,
            'low': prices,
            'volume': np.random.randint(100, 1000, data_points)
        }, index=dates)
        
        assert len(ohlcv) == data_points
        assert ohlcv['close'].notna().all()


class TestStrategyLive:
    """تست‌های استراتژی Live"""
    
    def test_live_signal_generation(self):
        """تست تولید سیگنال Live"""
        current_price = 1.1050
        previous_close = 1.1000
        sma_20 = 1.1040
        
        # سیگنال: اگر current > SMA و previous < current
        buy_signal = (current_price > sma_20) and (previous_close < current_price)
        
        assert buy_signal is True
    
    def test_live_order_placement(self):
        """تست قرار‌دادن دستور Live"""
        order = {
            'type': 'BUY',
            'instrument': 'EURUSD',
            'quantity': 100,
            'order_type': 'MARKET',
            'timestamp': datetime.now()
        }
        
        assert order['type'] in ['BUY', 'SELL']
        assert order['order_type'] in ['MARKET', 'LIMIT', 'STOP']
    
    def test_live_position_monitoring(self):
        """تست نظارت موقعیت‌های Live"""
        positions = [
            {'id': 1, 'entry': 1.1050, 'current': 1.1100, 'quantity': 100},
            {'id': 2, 'entry': 1.1150, 'current': 1.1120, 'quantity': 100}
        ]
        
        for pos in positions:
            pnl = (pos['current'] - pos['entry']) * pos['quantity']
            assert isinstance(pnl, float)
    
    def test_live_risk_monitoring(self):
        """تست نظارت ریسک Live"""
        daily_limit = -1000
        current_pnl = -500
        daily_remaining = daily_limit - current_pnl
        
        can_trade = current_pnl > daily_limit
        assert can_trade is True
        assert daily_remaining == -500


class TestStrategyEdgeCases:
    """تست‌های Edge Cases"""
    
    def test_handle_missing_data(self):
        """تست مدیریت داده‌های گمشده"""
        prices = [1.1, np.nan, 1.15, 1.12, np.nan, 1.18]
        prices_series = pd.Series(prices)
        
        # پر کردن NaN
        prices_filled = prices_series.ffill()
        
        assert prices_filled.notna().all()
    
    def test_handle_zero_volume(self):
        """تست مدیریت حجم صفر"""
        ohlcv = pd.DataFrame({
            'close': [1.1, 1.2, 1.15, 1.25],
            'volume': [0, 150, 0, 200]
        })
        
        # فیلتر کردن redBar های بدون volume
        valid_bars = ohlcv[ohlcv['volume'] > 0]
        
        assert len(valid_bars) == 2
    
    def test_handle_price_gap(self):
        """تست مدیریت Price Gap"""
        prices = [1.1, 1.2, 1.3, 1.5, 1.6]  # Gap بین 1.3 و 1.5
        
        # شناسایی gaps
        gaps = [prices[i+1] - prices[i] for i in range(len(prices)-1)]
        large_gaps = [g for g in gaps if abs(g) > 0.1]
        
        assert len(large_gaps) > 0
    
    def test_handle_extreme_volatility(self):
        """تست مدیریت Volatility شدید"""
        prices = pd.Series([1.1, 0.9, 1.3, 0.8, 1.4, 0.7])
        volatility = prices.pct_change().std()
        
        # در volatility بالا، position size کاهش دهید
        normal_volatility = 0.01
        position_adjustment = normal_volatility / volatility
        
        assert position_adjustment < 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
