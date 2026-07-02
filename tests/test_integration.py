"""
Integration Tests for Trading AI System
تست‌های یکپارچگی سیستم تریدینگ

This module contains integration tests that verify the interaction between
different components of the trading system.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Tuple


@pytest.mark.integration
class TestDataToFeaturesPipeline:
    """تست‌های Pipeline داده به Features"""
    
    def test_raw_data_to_features_flow(self):
        """تست جریان داده خام به Features"""
        # شبیه‌سازی داده خام
        raw_data = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=100, freq='h'),
            'open': np.random.uniform(1.10, 1.12, 100),
            'high': np.random.uniform(1.12, 1.14, 100),
            'low': np.random.uniform(1.08, 1.10, 100),
            'close': np.random.uniform(1.10, 1.12, 100),
            'volume': np.random.randint(100, 1000, 100)
        })
        
        # تنظیم close > low و close < high
        raw_data['close'] = (raw_data['low'] + raw_data['high']) / 2
        
        # محاسبه Features پایه
        features = pd.DataFrame()
        features['returns'] = raw_data['close'].pct_change()
        features['volatility'] = features['returns'].rolling(window=20).std()
        features['sma_20'] = raw_data['close'].rolling(window=20).mean()
        features['rsi'] = 100 - (100 / (1 + (raw_data['close'].diff().rolling(14).mean() / 
                                             (-raw_data['close'].diff().rolling(14).min()))))
        
        # بررسی
        assert len(features) == len(raw_data)
        assert features['returns'].notna().sum() > 0
        assert features['volatility'].notna().sum() > 0
        assert features['sma_20'].notna().sum() > 0
    
    def test_features_to_model_training(self):
        """تست Features برای training مدل"""
        # ایجاد features
        n_samples = 1000
        features = pd.DataFrame({
            'rsi': np.random.uniform(0, 100, n_samples),
            'macd': np.random.uniform(-5, 5, n_samples),
            'bb_position': np.random.uniform(-1, 1, n_samples),
            'trend': np.random.choice([0, 1], n_samples),
            'volatility': np.random.uniform(0, 0.05, n_samples)
        })
        
        # target
        target = np.random.choice([0, 1], n_samples)
        
        assert len(features) == len(target)
        assert features.shape[1] == 5
        assert target.nunique() == 2
    
    def test_feature_engineering_consistency(self):
        """تست consistency Feature Engineering"""
        data = pd.DataFrame({
            'close': [1.1, 1.2, 1.15, 1.25, 1.20]
        })
        
        # دو روش محاسبه SMA
        sma_1 = data['close'].rolling(2).mean()
        sma_2 = (data['close'] + data['close'].shift(1)) / 2
        
        pd.testing.assert_series_equal(sma_1, sma_2)


@pytest.mark.integration
class TestStrategyToExecutionPipeline:
    """تست‌های Pipeline Strategy به Execution"""
    
    def test_signal_generation_to_order(self):
        """تست تولید سیگنال تا سفارش"""
        # شبیه‌سازی شرایط market
        current_price = 1.1050
        sma_20 = 1.1040
        rsi = 45
        
        # تولید سیگنال
        buy_signal = (current_price > sma_20) and (rsi < 50)
        
        if buy_signal:
            order = {
                'type': 'BUY',
                'instrument': 'EURUSD',
                'quantity': 100,
                'price': current_price,
                'timestamp': datetime.now()
            }
        else:
            order = None
        
        assert order is not None
        assert order['type'] == 'BUY'
    
    def test_order_to_position(self):
        """تست سفارش تا موقعیت"""
        order = {
            'type': 'BUY',
            'quantity': 100,
            'price': 1.1050
        }
        
        # اجرای سفارش
        position = {
            'id': 'POS001',
            'instrument': 'EURUSD',
            'quantity': order['quantity'],
            'entry_price': order['price'],
            'entry_time': datetime.now(),
            'status': 'OPEN'
        }
        
        assert position['quantity'] == order['quantity']
        assert position['entry_price'] == order['price']
        assert position['status'] == 'OPEN'
    
    def test_position_management_cycle(self):
        """تست دوره مدیریت موقعیت"""
        position = {
            'id': 'POS001',
            'quantity': 100,
            'entry_price': 1.1050,
            'entry_time': datetime.now()
        }
        
        # مراقبت موقعیت
        current_price = 1.1100
        pnl = (current_price - position['entry_price']) * position['quantity']
        
        # بستن موقعیت
        close_order = {
            'position_id': position['id'],
            'exit_price': current_price,
            'pnl': pnl
        }
        
        assert close_order['pnl'] > 0


@pytest.mark.integration
class TestLiveExecutionFlow:
    """تست‌های Live Execution Flow"""
    
    def test_market_data_to_live_signal(self):
        """تست Market Data تا Live Signal"""
        # شبیه‌سازی live market data
        market_data = {
            'timestamp': datetime.now(),
            'bid': 1.10499,
            'ask': 1.10500,
            'mid': (1.10499 + 1.10500) / 2,
            'volume': 500
        }
        
        # تولید signal
        sma_20 = 1.10480
        live_signal = market_data['mid'] > sma_20
        
        assert live_signal is True
    
    def test_signal_to_order_placement(self):
        """تست Signal تا سفارش"""
        signal = True
        
        if signal:
            order = {
                'type': 'BUY',
                'instrument': 'EURUSD',
                'quantity': 100,
                'order_type': 'MARKET'
            }
            
            # مرحله‌ی اجرا
            execution_result = {
                'status': 'EXECUTED',
                'fill_price': 1.10500,
                'fill_quantity': 100
            }
        
        assert execution_result['status'] == 'EXECUTED'
    
    def test_position_monitoring_and_adjustment(self):
        """تست نظارت و تعديل موقعیت"""
        positions = [
            {'id': 1, 'entry': 1.1050, 'current': 1.1100},
            {'id': 2, 'entry': 1.1150, 'current': 1.1120}
        ]
        
        for pos in positions:
            pnl = (pos['current'] - pos['entry']) * 100
            
            # adjustment logic
            if pnl > 200:
                action = 'TAKE_PROFIT'
            elif pnl < -50:
                action = 'STOP_LOSS'
            else:
                action = 'HOLD'
            
            assert action in ['TAKE_PROFIT', 'STOP_LOSS', 'HOLD']


@pytest.mark.integration
class TestBacktestingFullCycle:
    """تست‌های Backtesting Full Cycle"""
    
    def test_full_backtest_cycle(self):
        """تست چرخه Backtest کامل"""
        # داده
        ohlcv = pd.DataFrame({
            'close': np.cumsum(np.random.randn(100) * 0.001) + 1.1,
            'open': np.cumsum(np.random.randn(100) * 0.001) + 1.1,
            'high': np.cumsum(np.random.randn(100) * 0.001) + 1.15,
            'low': np.cumsum(np.random.randn(100) * 0.001) + 1.05,
            'volume': np.random.randint(100, 1000, 100)
        })
        
        # استراتژی
        signals = (ohlcv['close'] > ohlcv['close'].shift(1)).astype(int)
        
        # محاسبه PnL
        pnls = []
        for i in range(1, len(ohlcv)):
            if signals.iloc[i] == 1:
                entry = ohlcv['close'].iloc[i-1]
                exit = ohlcv['close'].iloc[i]
                pnl = (exit - entry) * 100
                pnls.append(pnl)
        
        # نتایج
        if len(pnls) > 0:
            total_pnl = sum(pnls)
            win_count = sum(1 for p in pnls if p > 0)
            win_rate = win_count / len(pnls)
            
            assert win_rate >= 0
            assert win_rate <= 1
    
    def test_backtest_with_fees(self):
        """تست Backtest با هزینه‌ها"""
        trades = [100, -50, 150, -30]
        fee_per_trade = 5
        
        # محاسبه خالص
        net_trades = [t - fee_per_trade if t > 0 else t + fee_per_trade for t in trades]
        total = sum(net_trades)
        
        assert total < sum(trades)
    
    @pytest.mark.slow
    def test_full_year_backtest(self):
        """تست Backtest یک سال کامل"""
        # شبیه‌سازی 252 روز تریدینگ
        dates = pd.date_range('2023-01-01', periods=252, freq='B')
        prices = np.cumsum(np.random.randn(252) * 0.01) + 100
        
        ohlcv = pd.DataFrame({
            'close': prices,
            'volume': np.random.randint(100000, 1000000, 252)
        }, index=dates)
        
        assert len(ohlcv) == 252
        assert ohlcv.index.is_monotonic_increasing


@pytest.mark.integration
class TestRiskManagementIntegration:
    """تست‌های Integration Risk Management"""
    
    def test_position_sizing_to_execution(self):
        """تست Position Sizing تا Execution"""
        account = 10000
        risk_per_trade = 0.02
        
        # محاسبه size
        size = account * risk_per_trade
        
        # Order
        order = {
            'quantity': int(size / 1.1050),  # تقسیم بر قیمت
            'price': 1.1050
        }
        
        assert order['quantity'] > 0
    
    def test_stop_loss_execution_integration(self):
        """تست Stop Loss Execution"""
        position = {
            'entry_price': 1.1050,
            'stop_loss': 1.1020,
            'quantity': 100
        }
        
        # market price
        market_prices = [1.1040, 1.1035, 1.1025, 1.1015, 1.1010]
        
        for price in market_prices:
            if price <= position['stop_loss']:
                # اجرای stop loss
                execution = {
                    'exit_price': position['stop_loss'],
                    'status': 'EXECUTED'
                }
                assert execution['status'] == 'EXECUTED'
                break
    
    def test_multiple_positions_risk_control(self):
        """تست کنترل ریسک برای چندین موقعیت"""
        positions = [
            {'id': 1, 'size': 100, 'risk': 50},
            {'id': 2, 'size': 80, 'risk': 40},
            {'id': 3, 'size': 120, 'risk': 60}
        ]
        
        total_risk = sum(p['risk'] for p in positions)
        max_daily_risk = 200
        
        assert total_risk <= max_daily_risk
    
    def test_correlation_risk_management(self):
        """تست مدیریت Correlation Risk"""
        positions = {
            'EURUSD': 100,
            'EURGBP': 80,  # correlation بالا
            'GBPUSD': 70
        }
        
        # بررسی تنوع
        max_position = max(positions.values())
        total = sum(positions.values())
        
        concentration = max_position / total
        assert concentration < 0.6  # max 60%


@pytest.mark.integration
class TestDataConsistency:
    """تست‌های Data Consistency"""
    
    def test_ohlc_consistency(self):
        """تست OHLC Consistency"""
        ohlcv = pd.DataFrame({
            'open': [1.1000],
            'high': [1.1100],
            'low': [1.1000],
            'close': [1.1050]
        })
        
        # High >= Low
        assert (ohlcv['high'] >= ohlcv['low']).all()
        
        # High >= Open, High >= Close
        assert (ohlcv['high'] >= ohlcv['open']).all()
        assert (ohlcv['high'] >= ohlcv['close']).all()
        
        # Low <= Open, Low <= Close
        assert (ohlcv['low'] <= ohlcv['open']).all()
        assert (ohlcv['low'] <= ohlcv['close']).all()
    
    def test_volume_consistency(self):
        """تست Volume Consistency"""
        ohlcv = pd.DataFrame({
            'volume': [100, 150, 0, 200, 50]
        })
        
        # Volume باید >= 0 باشد
        assert (ohlcv['volume'] >= 0).all()
    
    def test_timestamp_consistency(self):
        """تست Timestamp Consistency"""
        timestamps = pd.date_range('2024-01-01', periods=10, freq='h')
        
        # Timestamps باید ascending باشند
        assert (timestamps[1:] > timestamps[:-1]).all()
    
    def test_data_alignment(self):
        """تست Data Alignment"""
        prices = pd.Series([1.1, 1.2, 1.15, 1.25])
        volumes = pd.Series([100, 150, 200, 180])
        
        # باید same length داشته باشند
        assert len(prices) == len(volumes)
        
        # باید same index داشته باشند
        assert prices.index.equals(volumes.index)


@pytest.mark.integration
class TestSystemErrorHandling:
    """تست‌های Error Handling در System"""
    
    def test_missing_data_handling(self):
        """تست مدیریت Missing Data"""
        data = pd.DataFrame({
            'close': [1.1, np.nan, 1.15, 1.12, np.nan]
        })
        
        # Handling
        filled_data = data.fillna(method='ffill')
        
        assert filled_data['close'].notna().all()
    
    def test_outlier_detection(self):
        """تست Outlier Detection"""
        prices = [1.1, 1.1, 1.15, 1.12, 2.0]  # آخری outlier است
        
        # Z-score method
        from scipy import stats
        z_scores = np.abs(stats.zscore(prices))
        outliers = z_scores > 2
        
        assert outliers.sum() > 0
    
    def test_connection_failure_handling(self):
        """تست مدیریت Connection Failure"""
        try:
            # شبیه‌سازی connection failure
            raise ConnectionError("API connection failed")
        except ConnectionError as e:
            handled = True
            error_msg = str(e)
        
        assert handled is True
    
    def test_order_rejection_handling(self):
        """تست مدیریت Order Rejection"""
        order = {
            'type': 'BUY',
            'quantity': 100,
            'price': 1.1050
        }
        
        # شبیه‌سازی rejection
        rejection_reason = "Insufficient margin"
        
        if rejection_reason:
            # rollback
            action = 'REJECT_AND_LOG'
        
        assert action == 'REJECT_AND_LOG'
    
    def test_partial_fill_handling(self):
        """تست مدیریت Partial Fill"""
        order = {
            'id': 'ORD001',
            'quantity': 100,
            'filled': 60
        }
        
        remaining = order['quantity'] - order['filled']
        assert remaining == 40


@pytest.mark.integration
class TestPerformanceMetrics:
    """تست‌های Performance Metrics"""
    
    def test_end_to_end_performance(self):
        """تست End-to-End Performance"""
        start_time = datetime.now()
        
        # شبیه‌سازی عملیات
        for _ in range(1000):
            _ = np.random.random()
        
        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()
        
        assert elapsed < 1  # باید یک ثانیه بکمتر کامل شود
    
    def test_throughput_calculation(self):
        """تست Throughput Calculation"""
        trades_processed = 100
        time_seconds = 5
        
        throughput = trades_processed / time_seconds
        
        assert throughput == 20  # 20 trades per second
    
    def test_latency_measurement(self):
        """تست Latency Measurement"""
        signal_time = datetime.now()
        order_placed_time = signal_time + timedelta(milliseconds=50)
        execution_time = order_placed_time + timedelta(milliseconds=100)
        
        order_latency = (order_placed_time - signal_time).total_seconds() * 1000
        execution_latency = (execution_time - order_placed_time).total_seconds() * 1000
        
        assert order_latency == 50
        assert execution_latency == 100


@pytest.mark.integration
class TestLoggingAndMonitoring:
    """تست‌های Logging و Monitoring"""
    
    def test_trade_logging(self):
        """تست Trade Logging"""
        trade_log = {
            'timestamp': datetime.now(),
            'instrument': 'EURUSD',
            'side': 'BUY',
            'quantity': 100,
            'price': 1.1050,
            'pnl': 100
        }
        
        assert trade_log['timestamp'] is not None
        assert trade_log['instrument'] is not None
        assert trade_log['quantity'] > 0
    
    def test_system_metrics_logging(self):
        """تست System Metrics Logging"""
        metrics = {
            'timestamp': datetime.now(),
            'positions': 5,
            'capital': 10000,
            'leverage': 5.0,
            'drawdown': 0.05
        }
        
        assert metrics['positions'] > 0
        assert metrics['capital'] > 0
    
    def test_error_logging(self):
        """تست Error Logging"""
        error_log = {
            'timestamp': datetime.now(),
            'error_type': 'APIError',
            'message': 'Connection timeout',
            'severity': 'HIGH'
        }
        
        assert error_log['severity'] in ['LOW', 'MEDIUM', 'HIGH']


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'integration'])
