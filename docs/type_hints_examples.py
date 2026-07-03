"""
Type Hints Examples - Trading AI System
========================================

نمونه‌های عملی و واقعی استفاده از Type Hints در پروژه
"""

from typing import (
    Dict, List, Tuple, Optional, Union, Any, Callable, Set,
    Sequence, Mapping, Final, TypeVar, Generic, Protocol
)
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
from abc import ABC, abstractmethod
import numpy as np
import pandas as pd
from decimal import Decimal
import json
import logging

# ═══════════════════════════════════════════════════════════════════════════
# EXAMPLE 1: Core Configuration Management
# ═══════════════════════════════════════════════════════════════════════════

class ConfigError(Exception):
    """خطای کانفیگ"""
    pass


@dataclass
class TradingConfig:
    """پیکربندی تریدینگ"""
    api_key: str
    api_secret: str
    account_type: str  # "demo" یا "live"
    base_currency: str
    leverage: int
    max_positions: int
    max_drawdown: float
    risk_per_trade: float
    
    def validate(self) -> bool:
        """اعتبارسنجی پیکربندی"""
        if not self.api_key or not self.api_secret:
            raise ConfigError("API credentials required")
        
        if self.leverage < 1 or self.leverage > 100:
            raise ConfigError("Leverage must be between 1 and 100")
        
        if not 0 < self.max_drawdown < 1:
            raise ConfigError("Max drawdown must be between 0 and 1")
        
        if not 0 < self.risk_per_trade < 0.1:
            raise ConfigError("Risk per trade must be between 0 and 10%")
        
        return True
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'TradingConfig':
        """ایجاد از dictionary"""
        return cls(**config_dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """تبدیل به dictionary"""
        return asdict(self)
    
    def save_to_file(self, path: Union[str, Path]) -> None:
        """ذخیره‌سازی در فایل"""
        path = Path(path)
        path.write_text(json.dumps(self.to_dict(), indent=2))
    
    @classmethod
    def load_from_file(cls, path: Union[str, Path]) -> 'TradingConfig':
        """بارگذاری از فایل"""
        path = Path(path)
        data = json.loads(path.read_text())
        return cls.from_dict(data)


# ═══════════════════════════════════════════════════════════════════════════
# EXAMPLE 2: OHLCV Data Management
# ═══════════════════════════════════════════════════════════════════════════

class DataValidator:
    """اعتبارسنجی داده‌های OHLCV"""
    
    @staticmethod
    def validate_ohlcv(data: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        اعتبارسنجی DataFrame
        
        Args:
            data: DataFrame OHLCV
        
        Returns:
            (موفق، لیست خطاها)
        """
        errors: List[str] = []
        
        # بررسی ستون‌های ضروری
        required_cols = {'open', 'high', 'low', 'close', 'volume'}
        missing = required_cols - set(data.columns)
        if missing:
            errors.append(f"Missing columns: {missing}")
        
        # بررسی داده‌های خالی
        if data.empty:
            errors.append("DataFrame is empty")
        
        # بررسی نسبت‌های OHLC
        invalid_ohcl = (data['low'] > data['high']).sum()
        if invalid_ohcl > 0:
            errors.append(f"Invalid OHLC ratio in {invalid_ohcl} rows")
        
        # بررسی حجم
        if (data['volume'] < 0).sum() > 0:
            errors.append("Negative volume found")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def clean_data(data: pd.DataFrame) -> pd.DataFrame:
        """پاک‌سازی داده‌ها"""
        data = data.copy()
        
        # حذف NaN
        data = data.dropna()
        
        # حذف duplicates
        data = data[~data.index.duplicated(keep='first')]
        
        # حذف مقادیر غلط
        data = data[
            (data['low'] <= data['high']) &
            (data['open'] >= data['low']) &
            (data['open'] <= data['high']) &
            (data['close'] >= data['low']) &
            (data['close'] <= data['high']) &
            (data['volume'] >= 0)
        ]
        
        return data


# ═══════════════════════════════════════════════════════════════════════════
# EXAMPLE 3: Feature Engineering
# ═══════════════════════════════════════════════════════════════════════════

class FeatureEngineer:
    """مهندسی فیچر"""
    
    def __init__(self) -> None:
        self.features: Dict[str, np.ndarray] = {}
    
    def calculate_sma(
        self,
        prices: np.ndarray,
        period: int = 20
    ) -> np.ndarray:
        """محاسبه Simple Moving Average"""
        return pd.Series(prices).rolling(period).mean().values
    
    def calculate_rsi(
        self,
        prices: np.ndarray,
        period: int = 14
    ) -> np.ndarray:
        """محاسبه Relative Strength Index"""
        delta = np.diff(prices)
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)
        
        avg_gain = pd.Series(gain).rolling(period).mean().values
        avg_loss = pd.Series(loss).rolling(period).mean().values
        
        rs = np.where(avg_loss != 0, avg_gain / avg_loss, 0)
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def calculate_bollinger_bands(
        self,
        prices: np.ndarray,
        period: int = 20,
        std_dev: float = 2.0
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """محاسبه Bollinger Bands"""
        sma = self.calculate_sma(prices, period)
        std = pd.Series(prices).rolling(period).std().values
        
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        
        return upper, sma, lower
    
    def engineer_features(self, ohlcv: pd.DataFrame) -> pd.DataFrame:
        """مهندسی تمام فیچرها"""
        features = ohlcv.copy()
        
        # Moving averages
        features['sma_20'] = self.calculate_sma(ohlcv['close'].values, 20)
        features['sma_50'] = self.calculate_sma(ohlcv['close'].values, 50)
        
        # RSI
        features['rsi_14'] = self.calculate_rsi(ohlcv['close'].values, 14)
        
        # Bollinger Bands
        upper, middle, lower = self.calculate_bollinger_bands(ohlcv['close'].values)
        features['bb_upper'] = upper
        features['bb_middle'] = middle
        features['bb_lower'] = lower
        
        # Returns
        features['returns'] = ohlcv['close'].pct_change()
        
        # Volume ratio
        features['volume_ratio'] = ohlcv['volume'] / ohlcv['volume'].rolling(20).mean()
        
        return features


# ═══════════════════════════════════════════════════════════════════════════
# EXAMPLE 4: Strategy Signal Generation
# ═══════════════════════════════════════════════════════════════════════════

class Signal(Enum):
    """سیگنال تریدینگ"""
    BUY = 1
    HOLD = 0
    SELL = -1


@dataclass
class TradeSignal:
    """سیگنال تریدینگ جزئیات"""
    timestamp: datetime
    symbol: str
    signal: Signal
    confidence: float  # 0.0 to 1.0
    reason: str
    suggested_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


class StrategySignalGenerator:
    """تولید سیگنال‌های استراتژی"""
    
    def __init__(self, confidence_threshold: float = 0.6) -> None:
        self.confidence_threshold = confidence_threshold
    
    def generate_signals(
        self,
        features: pd.DataFrame
    ) -> List[TradeSignal]:
        """تولید سیگنال‌ها"""
        signals: List[TradeSignal] = []
        
        for idx, row in features.iterrows():
            signal = self._evaluate_row(row)
            if signal is not None:
                signals.append(signal)
        
        return signals
    
    def _evaluate_row(self, row: pd.Series) -> Optional[TradeSignal]:
        """ارزیابی یک ردیف"""
        confidence: float = 0.0
        reasons: List[str] = []
        signal_type: Signal = Signal.HOLD
        
        # Bollinger Bands strategy
        if row['close'] < row['bb_lower']:
            confidence += 0.3
            reasons.append("Price below lower BB")
            signal_type = Signal.BUY
        
        elif row['close'] > row['bb_upper']:
            confidence += 0.3
            reasons.append("Price above upper BB")
            signal_type = Signal.SELL
        
        # RSI strategy
        if row['rsi_14'] < 30:
            confidence += 0.2
            reasons.append("RSI oversold")
            signal_type = Signal.BUY
        
        elif row['rsi_14'] > 70:
            confidence += 0.2
            reasons.append("RSI overbought")
            signal_type = Signal.SELL
        
        # Moving average crossover
        if row['sma_20'] > row['sma_50']:
            confidence += 0.2
            reasons.append("SMA20 > SMA50")
            signal_type = Signal.BUY
        
        elif row['sma_20'] < row['sma_50']:
            confidence += 0.2
            reasons.append("SMA20 < SMA50")
            signal_type = Signal.SELL
        
        if confidence >= self.confidence_threshold:
            return TradeSignal(
                timestamp=row.name,
                symbol="EURUSD",  # Example
                signal=signal_type,
                confidence=min(confidence, 1.0),
                reason="; ".join(reasons),
                stop_loss=row['close'] * 0.98 if signal_type == Signal.BUY else row['close'] * 1.02,
                take_profit=row['close'] * 1.02 if signal_type == Signal.BUY else row['close'] * 0.98
            )
        
        return None


# ═══════════════════════════════════════════════════════════════════════════
# EXAMPLE 5: Position Management
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class Position:
    """پوزیشن تریدینگ"""
    symbol: str
    size: float
    entry_price: float
    entry_time: datetime
    current_price: float = 0.0
    
    @property
    def pnl(self) -> float:
        """سود و زیان"""
        return (self.current_price - self.entry_price) * self.size
    
    @property
    def pnl_percent(self) -> float:
        """درصد سود و زیان"""
        if self.entry_price == 0:
            return 0.0
        return (self.pnl / (self.entry_price * self.size)) * 100
    
    def update_price(self, new_price: float) -> None:
        """بروزرسانی قیمت جاری"""
        self.current_price = new_price


class PositionManager:
    """مدیریت پوزیشن‌ها"""
    
    def __init__(self, initial_capital: float) -> None:
        self.capital: float = initial_capital
        self.positions: Dict[str, Position] = {}
        self.closed_positions: List[Position] = []
    
    def open_position(
        self,
        symbol: str,
        size: float,
        entry_price: float
    ) -> bool:
        """باز کردن پوزیشن"""
        if symbol in self.positions:
            logging.warning(f"Position {symbol} already exists")
            return False
        
        position = Position(
            symbol=symbol,
            size=size,
            entry_price=entry_price,
            entry_time=datetime.now(),
            current_price=entry_price
        )
        self.positions[symbol] = position
        return True
    
    def close_position(self, symbol: str, exit_price: float) -> Optional[float]:
        """بسته کردن پوزیشن"""
        if symbol not in self.positions:
            logging.warning(f"Position {symbol} not found")
            return None
        
        position = self.positions.pop(symbol)
        position.current_price = exit_price
        
        pnl = position.pnl
        self.capital += pnl
        self.closed_positions.append(position)
        
        return pnl
    
    def update_prices(self, prices: Dict[str, float]) -> None:
        """بروزرسانی قیمت‌های موجودی"""
        for symbol, position in self.positions.items():
            if symbol in prices:
                position.update_price(prices[symbol])
    
    def get_portfolio_value(self) -> float:
        """ارزش کل پورتفولیو"""
        portfolio_value = self.capital
        for position in self.positions.values():
            portfolio_value += position.pnl
        return portfolio_value
    
    def get_positions_summary(self) -> List[Dict[str, Any]]:
        """خلاصه پوزیشن‌ها"""
        summary: List[Dict[str, Any]] = []
        for position in self.positions.values():
            summary.append({
                'symbol': position.symbol,
                'size': position.size,
                'entry_price': position.entry_price,
                'current_price': position.current_price,
                'pnl': position.pnl,
                'pnl_percent': position.pnl_percent,
                'entry_time': position.entry_time.isoformat()
            })
        return summary


# ═══════════════════════════════════════════════════════════════════════════
# EXAMPLE 6: Performance Metrics
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class PerformanceMetrics:
    """معیارهای عملکرد"""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    
    def calculate_from_trades(self, trades: List[float]) -> None:
        """محاسبه از لیست معاملات"""
        if not trades:
            return
        
        self.total_trades = len(trades)
        self.total_pnl = sum(trades)
        
        wins = [t for t in trades if t > 0]
        losses = [t for t in trades if t < 0]
        
        self.winning_trades = len(wins)
        self.losing_trades = len(losses)
        
        if self.total_trades > 0:
            self.win_rate = (self.winning_trades / self.total_trades) * 100
        
        if wins:
            self.avg_win = sum(wins) / len(wins)
        
        if losses:
            self.avg_loss = sum(losses) / len(losses)
        
        if self.avg_loss != 0:
            self.profit_factor = self.avg_win / abs(self.avg_loss)
    
    def calculate_sharpe(
        self,
        returns: np.ndarray,
        risk_free_rate: float = 0.02
    ) -> None:
        """محاسبه نسبت شارپ"""
        if len(returns) < 2:
            return
        
        excess_return = np.mean(returns) - risk_free_rate / 252
        volatility = np.std(returns)
        
        if volatility != 0:
            self.sharpe_ratio = excess_return / volatility * np.sqrt(252)
    
    def calculate_max_drawdown_value(self, returns: np.ndarray) -> None:
        """محاسبه maximum drawdown"""
        if len(returns) < 2:
            return
        
        cumulative = np.cumprod(1 + returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        
        self.max_drawdown = np.min(drawdown)


# ═══════════════════════════════════════════════════════════════════════════
# EXAMPLE 7: Backtesting Engine
# ═══════════════════════════════════════════════════════════════════════════

class BacktestEngine:
    """موتور بک‌تست"""
    
    def __init__(
        self,
        initial_capital: float = 10000.0,
        commission: float = 0.0001
    ) -> None:
        self.initial_capital = initial_capital
        self.commission = commission
        self.position_manager = PositionManager(initial_capital)
        self.trades: List[Tuple[datetime, float]] = []
    
    def run_backtest(
        self,
        ohlcv: pd.DataFrame,
        signals: List[TradeSignal]
    ) -> PerformanceMetrics:
        """اجرای بک‌تست"""
        price_series = ohlcv['close']
        
        for signal in signals:
            if signal.timestamp not in price_series.index:
                continue
            
            current_price = price_series[signal.timestamp]
            
            if signal.signal == Signal.BUY:
                position_size = self._calculate_position_size(current_price)
                self.position_manager.open_position(
                    signal.symbol,
                    position_size,
                    current_price
                )
            
            elif signal.signal == Signal.SELL:
                if signal.symbol in self.position_manager.positions:
                    pnl = self.position_manager.close_position(
                        signal.symbol,
                        current_price
                    )
                    if pnl is not None:
                        self.trades.append((signal.timestamp, pnl))
        
        # Calculate metrics
        metrics = PerformanceMetrics()
        if self.trades:
            pnls = [t[1] for t in self.trades]
            metrics.calculate_from_trades(pnls)
        
        return metrics
    
    def _calculate_position_size(self, current_price: float) -> float:
        """محاسبه اندازه پوزیشن"""
        risk_amount = self.position_manager.capital * 0.02  # 2% risk
        position_size = risk_amount / (current_price * 0.01)  # 1% stop loss
        return position_size


# ═══════════════════════════════════════════════════════════════════════════
# EXAMPLE 8: Main Usage
# ═══════════════════════════════════════════════════════════════════════════

def main() -> None:
    """مثال استفاده کامل"""
    print("Trading AI System - Type Hints Examples")
    print("=" * 50)
    
    # 1. Configuration
    config = TradingConfig(
        api_key="test_key",
        api_secret="test_secret",
        account_type="demo",
        base_currency="USD",
        leverage=10,
        max_positions=5,
        max_drawdown=0.20,
        risk_per_trade=0.02
    )
    config.validate()
    print(f"✅ Config validated: {config.account_type}")
    
    # 2. Create sample data
    dates = pd.date_range('2023-01-01', periods=100)
    ohlcv = pd.DataFrame({
        'open': np.random.uniform(1.15, 1.25, 100),
        'high': np.random.uniform(1.20, 1.30, 100),
        'low': np.random.uniform(1.10, 1.20, 100),
        'close': np.random.uniform(1.15, 1.25, 100),
        'volume': np.random.uniform(1000000, 2000000, 100)
    }, index=dates)
    
    # 3. Validate data
    validator = DataValidator()
    is_valid, errors = validator.validate_ohlcv(ohlcv)
    print(f"✅ Data validation: {'PASS' if is_valid else 'FAIL'}")
    
    # 4. Engineer features
    engineer = FeatureEngineer()
    features = engineer.engineer_features(ohlcv)
    print(f"✅ Features engineered: {features.shape}")
    
    # 5. Generate signals
    generator = StrategySignalGenerator()
    signals = generator.generate_signals(features)
    print(f"✅ Signals generated: {len(signals)}")
    
    # 6. Run backtest
    backtest = BacktestEngine(initial_capital=10000)
    metrics = backtest.run_backtest(ohlcv, signals)
    print(f"✅ Backtest completed: {metrics.total_trades} trades")
    print(f"   Total PnL: {metrics.total_pnl:.2f}")
    print(f"   Win Rate: {metrics.win_rate:.2f}%")


if __name__ == "__main__":
    main()
