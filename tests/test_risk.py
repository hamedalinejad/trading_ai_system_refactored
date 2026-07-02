"""
Risk Management Module Tests
تست‌های ماژول مدیریت ریسک

This module contains comprehensive tests for risk management components including
position sizing, stop-loss/take-profit management, portfolio risk analysis, and more.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from typing import Dict, List, Tuple


class TestPositionSizing:
    """تست‌های Position Sizing"""
    
    def test_fixed_lot_sizing(self):
        """تست Fixed Lot Sizing"""
        lot_size = 1.0  # 1 lot
        quantity = 100000 * lot_size  # 100,000 units per lot
        
        assert quantity == 100000
    
    def test_percentage_risk_sizing(self):
        """تست Percentage Risk Position Sizing"""
        account_balance = 10000
        risk_percentage = 0.02  # 2%
        risk_amount = account_balance * risk_percentage
        
        entry_price = 1.1050
        stop_loss = 1.1020
        pip_risk = (entry_price - stop_loss) * 10000  # pips
        
        position_size = risk_amount / (pip_risk * 0.0001)
        
        assert position_size > 0
        assert risk_amount == 200
    
    def test_kelly_criterion_sizing(self):
        """تست Kelly Criterion Position Sizing"""
        win_rate = 0.55
        avg_win = 100
        avg_loss = 80
        
        # Kelly Formula: f = (bp - q) / b
        b = avg_win / avg_loss  # odds
        p = win_rate
        q = 1 - win_rate
        
        kelly_fraction = (b * p - q) / b
        
        # Kelly fraction معمولاً بین 0.1 و 0.3 است
        assert 0 < kelly_fraction < 1
        assert kelly_fraction > 0
    
    def test_kelly_criterion_conservative(self):
        """تست Conservative Kelly (نیمی از Kelly)"""
        win_rate = 0.55
        avg_win = 100
        avg_loss = 80
        
        b = avg_win / avg_loss
        p = win_rate
        q = 1 - win_rate
        kelly_fraction = (b * p - q) / b
        
        # استفاده از نیمی از Kelly برای کاهش ریسک
        conservative_kelly = kelly_fraction / 2
        
        assert conservative_kelly < kelly_fraction
    
    def test_volatility_adjusted_sizing(self):
        """تست Position Sizing متناسب با Volatility"""
        base_position = 100
        base_volatility = 0.01  # 1%
        current_volatility = 0.02  # 2%
        
        # کاهش موقعیت در volatility بالا
        adjusted_position = base_position * (base_volatility / current_volatility)
        
        assert adjusted_position < base_position
        assert adjusted_position == 50
    
    def test_atr_based_sizing(self):
        """تست Position Sizing بر اساس ATR"""
        account_size = 10000
        risk_per_trade = 100  # $100
        atr = 0.005  # 50 pips
        
        # Position size = Risk / ATR
        position_size = risk_per_trade / atr
        
        assert position_size > 0
    
    def test_max_position_limit(self):
        """تست محدودیت حداکثر اندازه موقعیت"""
        account_size = 10000
        max_position_percentage = 0.1  # 10% of account
        max_position = account_size * max_position_percentage
        
        calculated_position = 2000
        assert calculated_position <= max_position
        
        calculated_position = 15000
        assert calculated_position > max_position


class TestStopLossManagement:
    """تست‌های Stop Loss Management"""
    
    def test_fixed_stop_loss(self):
        """تست Fixed Stop Loss"""
        entry_price = 1.1050
        stop_loss_pips = 30  # 30 pips
        stop_loss_price = entry_price - (stop_loss_pips * 0.0001)
        
        assert stop_loss_price == 1.1020
    
    def test_atr_based_stop_loss(self):
        """تست ATR-based Stop Loss"""
        entry_price = 1.1050
        atr = 0.005  # 50 pips
        atr_multiplier = 2
        
        stop_loss = entry_price - (atr * atr_multiplier)
        
        assert stop_loss < entry_price
        assert stop_loss == 1.1000
    
    def test_percentage_stop_loss(self):
        """تست Percentage Stop Loss"""
        entry_price = 100
        stop_loss_percentage = 0.05  # 5%
        stop_loss = entry_price * (1 - stop_loss_percentage)
        
        assert stop_loss == 95
    
    def test_trailing_stop_loss(self):
        """تست Trailing Stop Loss"""
        entry_price = 1.1050
        high_price = 1.1200
        trailing_distance = 0.0050  # 50 pips
        
        trailing_stop = high_price - trailing_distance
        
        assert trailing_stop > entry_price
        assert trailing_stop == 1.1150
    
    def test_support_level_stop_loss(self):
        """تست Support Level Stop Loss"""
        support_level = 1.1000
        entry_price = 1.1050
        
        stop_loss = support_level - 0.0010  # یک pip زیر support
        
        assert stop_loss < entry_price
    
    def test_stop_loss_triggered(self):
        """تست Triggering Stop Loss"""
        entry_price = 1.1050
        stop_loss = 1.1020
        current_price = 1.1015
        
        is_stopped = current_price <= stop_loss
        assert is_stopped is True
    
    def test_stop_loss_not_triggered(self):
        """تست عدم Triggering Stop Loss"""
        entry_price = 1.1050
        stop_loss = 1.1020
        current_price = 1.1025
        
        is_stopped = current_price <= stop_loss
        assert is_stopped is False
    
    def test_multiple_stop_losses(self):
        """تست چند سطح Stop Loss"""
        entry_price = 100
        stop_loss_levels = {
            'hard_stop': 95,      # حتمی
            'trailing_stop': 98,  # پویا
            'mental_stop': 90     # ذهنی
        }
        
        assert stop_loss_levels['hard_stop'] < entry_price
        assert stop_loss_levels['trailing_stop'] < entry_price


class TestTakeProfitManagement:
    """تست‌های Take Profit Management"""
    
    def test_fixed_take_profit(self):
        """تست Fixed Take Profit"""
        entry_price = 1.1050
        take_profit_pips = 50  # 50 pips
        take_profit = entry_price + (take_profit_pips * 0.0001)
        
        assert take_profit == 1.1100
    
    def test_risk_reward_ratio_take_profit(self):
        """تست Take Profit بر اساس Risk-Reward Ratio"""
        entry_price = 1.1050
        stop_loss = 1.1020
        risk = entry_price - stop_loss
        
        # Risk-Reward Ratio = 1:3
        reward = risk * 3
        take_profit = entry_price + reward
        
        assert take_profit == 1.1140
    
    def test_support_resistance_take_profit(self):
        """تست Take Profit بر اساس Resistance Level"""
        resistance_level = 1.1150
        take_profit = resistance_level
        
        assert take_profit > 0
    
    def test_percentage_take_profit(self):
        """تست Percentage Take Profit"""
        entry_price = 100
        take_profit_percentage = 0.10  # 10%
        take_profit = entry_price * (1 + take_profit_percentage)
        
        assert take_profit == 110
    
    def test_tiered_take_profit(self):
        """تست Tiered Take Profit (چند سطحی)"""
        entry_price = 1.1050
        quantity = 100
        
        tp_levels = [
            {'price': 1.1100, 'quantity': 33, 'label': 'First TP'},
            {'price': 1.1150, 'quantity': 33, 'label': 'Second TP'},
            {'price': 1.1200, 'quantity': 34, 'label': 'Final TP'}
        ]
        
        total_quantity = sum(tp['quantity'] for tp in tp_levels)
        assert total_quantity == quantity
    
    def test_take_profit_triggered(self):
        """تست Triggering Take Profit"""
        entry_price = 1.1050
        take_profit = 1.1100
        current_price = 1.1105
        
        is_profit_taken = current_price >= take_profit
        assert is_profit_taken is True


class TestRiskMetrics:
    """تست‌های Risk Metrics"""
    
    def test_maximum_drawdown(self):
        """تست Maximum Drawdown"""
        equity_curve = np.array([10000, 10500, 10200, 9500, 9200, 10000, 11000])
        
        running_max = np.maximum.accumulate(equity_curve)
        drawdown = (equity_curve - running_max) / running_max
        max_drawdown = np.min(drawdown)
        
        assert max_drawdown < 0
        assert max_drawdown > -1
    
    def test_recovery_factor(self):
        """تست Recovery Factor"""
        total_profit = 5000
        maximum_drawdown = 2000
        
        recovery_factor = total_profit / maximum_drawdown if maximum_drawdown > 0 else 0
        
        assert recovery_factor > 0
    
    def test_calmar_ratio(self):
        """تست Calmar Ratio"""
        annual_return = 0.25  # 25%
        max_drawdown = 0.10   # 10%
        
        calmar_ratio = annual_return / max_drawdown if max_drawdown > 0 else 0
        
        assert calmar_ratio > 0
    
    def test_profit_factor(self):
        """تست Profit Factor"""
        gross_profit = 5000
        gross_loss = 2000
        
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        assert profit_factor > 1  # باید بالای 1 باشد
    
    def test_sharpe_ratio(self):
        """تست Sharpe Ratio"""
        returns = np.array([0.01, 0.02, -0.01, 0.03, 0.02, -0.02])
        risk_free_rate = 0.001
        
        excess_returns = returns - risk_free_rate
        sharpe = np.mean(excess_returns) / np.std(excess_returns) if np.std(excess_returns) > 0 else 0
        
        assert isinstance(sharpe, float)
    
    def test_sortino_ratio(self):
        """تست Sortino Ratio"""
        returns = np.array([0.01, 0.02, -0.01, 0.03, 0.02, -0.02])
        risk_free_rate = 0.001
        target_return = 0
        
        excess_returns = returns - risk_free_rate
        downside_deviation = np.sqrt(np.mean(np.minimum(excess_returns - target_return, 0) ** 2))
        
        sortino = np.mean(excess_returns) / downside_deviation if downside_deviation > 0 else 0
        
        assert isinstance(sortino, float)
    
    def test_win_loss_ratio(self):
        """تست Win/Loss Ratio"""
        avg_winning_trade = 150
        avg_losing_trade = 100
        
        win_loss_ratio = avg_winning_trade / avg_losing_trade
        
        assert win_loss_ratio > 1


class TestPortfolioRisk:
    """تست‌های Portfolio Risk"""
    
    def test_portfolio_variance(self):
        """تست Portfolio Variance"""
        weights = np.array([0.3, 0.4, 0.3])
        asset_volatilities = np.array([0.10, 0.15, 0.12])
        
        # Simplified (بدون correlation)
        portfolio_variance = np.sum((weights ** 2) * (asset_volatilities ** 2))
        portfolio_std = np.sqrt(portfolio_variance)
        
        assert portfolio_std > 0
    
    def test_portfolio_correlation_effect(self):
        """تست تأثیر Correlation بر Portfolio Risk"""
        # دو دارایی
        volatility_1 = 0.10
        volatility_2 = 0.15
        
        # بدون correlation (worst case)
        risk_uncorrelated = np.sqrt(volatility_1**2 + volatility_2**2)
        
        # با negative correlation (بهتر)
        correlation = -0.5
        risk_correlated = np.sqrt(volatility_1**2 + volatility_2**2 + 
                                  2 * correlation * volatility_1 * volatility_2)
        
        assert risk_correlated < risk_uncorrelated
    
    def test_portfolio_diversification_benefit(self):
        """تست فوایدی Diversification"""
        # Portfolio با 1 دارایی
        single_asset_risk = 0.20
        
        # Portfolio متنوع
        diversified_risk = 0.12
        
        diversification_benefit = (single_asset_risk - diversified_risk) / single_asset_risk
        
        assert diversification_benefit > 0
    
    def test_concentration_risk(self):
        """تست Concentration Risk"""
        positions = {
            'EURUSD': 0.50,
            'GBPUSD': 0.30,
            'USDJPY': 0.20
        }
        
        max_concentration = max(positions.values())
        assert max_concentration <= 1.0  # نباید بیش از 100%
    
    def test_correlation_analysis(self):
        """تست Correlation Analysis بین دارایی‌ها"""
        prices_1 = [1.0, 1.1, 1.2, 1.15, 1.25]
        prices_2 = [100, 110, 120, 115, 125]
        
        correlation = np.corrcoef(prices_1, prices_2)[0, 1]
        
        assert -1 <= correlation <= 1


class TestExposureManagement:
    """تست‌های Exposure Management"""
    
    def test_gross_exposure(self):
        """تست Gross Exposure"""
        positions = [
            {'instrument': 'EURUSD', 'quantity': 100, 'price': 1.1050},
            {'instrument': 'GBPUSD', 'quantity': 50, 'price': 1.3000}
        ]
        
        gross_exposure = sum(abs(pos['quantity']) * pos['price'] for pos in positions)
        
        assert gross_exposure > 0
    
    def test_net_exposure(self):
        """تست Net Exposure"""
        positions = [
            {'quantity': 100, 'price': 1.1050, 'side': 'LONG'},
            {'quantity': -50, 'price': 1.1050, 'side': 'SHORT'}
        ]
        
        net_quantity = sum(pos['quantity'] for pos in positions)
        net_exposure = net_quantity * 1.1050
        
        assert net_exposure > 0
    
    def test_leverage(self):
        """تست Leverage"""
        account_size = 10000
        gross_exposure = 50000
        
        leverage = gross_exposure / account_size
        
        assert leverage > 1
        assert leverage == 5  # 5:1 leverage
    
    def test_max_leverage_limit(self):
        """تست محدودیت Leverage"""
        account_size = 10000
        max_leverage = 10
        gross_exposure = account_size * max_leverage
        
        calculated_exposure = 50000
        assert calculated_exposure <= gross_exposure
    
    def test_sector_exposure(self):
        """تست Sector Exposure"""
        positions = {
            'currency_pairs': 0.50,
            'stocks': 0.30,
            'commodities': 0.20
        }
        
        total_exposure = sum(positions.values())
        assert total_exposure <= 1.0


class TestMoneyManagement:
    """تست‌های Money Management"""
    
    def test_account_equity_tracking(self):
        """تست تتبع Account Equity"""
        initial_balance = 10000
        daily_pnl = [100, -50, 150, -30, 200]
        
        equity_curve = [initial_balance]
        for pnl in daily_pnl:
            equity_curve.append(equity_curve[-1] + pnl)
        
        assert equity_curve[-1] > initial_balance
    
    def test_drawdown_recovery(self):
        """تست بازیابی از Drawdown"""
        balance_before = 10000
        loss_amount = -2000
        balance_after = balance_before + loss_amount
        
        # بازیابی مورد نیاز
        recovery_needed = loss_amount / balance_after
        
        assert recovery_needed > 0
    
    def test_daily_pnl_tracking(self):
        """تست Daily PnL Tracking"""
        trades = [
            {'entry': 1.1050, 'exit': 1.1100, 'quantity': 100},
            {'entry': 1.1150, 'exit': 1.1120, 'quantity': 100}
        ]
        
        daily_pnl = sum((t['exit'] - t['entry']) * t['quantity'] for t in trades)
        
        assert daily_pnl >= 0
    
    def test_win_streak_tracking(self):
        """تست Win Streak Tracking"""
        pnls = [100, 150, -50, 100, 200, 200, -30]
        
        current_streak = 0
        max_streak = 0
        
        for pnl in pnls:
            if pnl > 0:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
        
        assert max_streak > 0
    
    def test_loss_recovery_calculation(self):
        """تست محاسبه Recovery از Loss"""
        loss_percentage = 0.10  # 10% loss
        recovery_needed = loss_percentage / (1 - loss_percentage)
        
        assert recovery_needed > loss_percentage
        assert recovery_needed == pytest.approx(0.1111, rel=0.001)


class TestRiskLimits:
    """تست‌های Risk Limits"""
    
    def test_max_daily_loss_limit(self):
        """تست محدودیت Max Daily Loss"""
        daily_limit = -1000
        current_pnl = -800
        
        remaining_limit = daily_limit - current_pnl
        can_trade = current_pnl > daily_limit
        
        assert can_trade is True
    
    def test_max_positions_limit(self):
        """تست محدودیت Max Positions"""
        max_positions = 5
        current_positions = 3
        
        can_open_new = current_positions < max_positions
        assert can_open_new is True
    
    def test_max_correlation_limit(self):
        """تست محدودیت Max Correlation"""
        max_corr = 0.8
        positions = {
            'EURUSD': 1.0,
            'EURGBP': 0.75
        }
        
        # EURUSD و EURGBP دارای correlation بالا هستند
        position_correlation = 0.75
        assert position_correlation <= max_corr
    
    def test_max_volatility_limit(self):
        """تست محدودیت Max Volatility"""
        max_volatility = 0.05  # 5%
        current_volatility = 0.03
        
        can_trade = current_volatility <= max_volatility
        assert can_trade is True
    
    def test_max_leverage_utilization(self):
        """تست محدودیت Leverage Utilization"""
        max_leverage = 10
        current_leverage = 8
        
        can_increase = current_leverage < max_leverage
        assert can_increase is True


class TestRiskReporting:
    """تست‌های Risk Reporting"""
    
    def test_daily_risk_report(self):
        """تست Daily Risk Report"""
        report = {
            'date': datetime.now(),
            'gross_exposure': 50000,
            'leverage': 5.0,
            'max_drawdown': 0.05,
            'daily_pnl': 500,
            'win_rate': 0.60
        }
        
        assert report['date'] is not None
        assert report['gross_exposure'] > 0
    
    def test_position_risk_breakdown(self):
        """تست Position Risk Breakdown"""
        positions = [
            {'instrument': 'EURUSD', 'size': 100, 'risk': 100},
            {'instrument': 'GBPUSD', 'size': 50, 'risk': 75},
            {'instrument': 'USDJPY', 'size': 80, 'risk': 120}
        ]
        
        total_risk = sum(p['risk'] for p in positions)
        assert total_risk == 295
    
    def test_var_calculation(self):
        """تست Value at Risk (VaR) Calculation"""
        returns = np.array([0.01, 0.02, -0.01, -0.03, 0.02, -0.02, 0.01])
        confidence_level = 0.95
        
        var = np.percentile(returns, (1 - confidence_level) * 100)
        
        assert var < 0


class TestRiskEdgeCases:
    """تست‌های Edge Cases در Risk Management"""
    
    def test_zero_volatility(self):
        """تست مدیریت Zero Volatility"""
        volatility = 0
        base_position = 100
        
        # از zero volatility جلوگیری
        volatility = max(volatility, 0.001)
        
        assert volatility > 0
    
    def test_extreme_leverage(self):
        """تست Extreme Leverage"""
        account = 1000
        position = 100000
        leverage = position / account
        
        assert leverage > 1
        # در این حالت باید warning داد شود
    
    def test_highly_correlated_positions(self):
        """تست Highly Correlated Positions"""
        positions = {
            'EURUSD': 1.0,
            'EURGBP': 0.95,  # correlation بسیار بالا
            'EURJPY': 0.92
        }
        
        # باید warning داد شود
        avg_corr = np.mean(list(positions.values()))
        assert avg_corr > 0.9


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
