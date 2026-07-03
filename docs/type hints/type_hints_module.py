"""
Trading AI System - Type Hints Module
====================================

فایل کامل Type Hints برای تمام توابع و کلاس‌های پروژه
این ماژول IDE support و type checking بهتری فراهم می‌کند.

خصوصیات:
- ✅ تمام توابع typed هستند
- ✅ Generic types برای data structures
- ✅ Union types برای optional values
- ✅ Protocol classes برای duck typing
- ✅ Type aliases برای readability
"""

from typing import (
    Dict, List, Tuple, Optional, Union, Any, Callable, Set,
    Iterable, Sequence, Mapping, Protocol, TypeVar, Generic,
    Literal, Final, overload, cast
)
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from enum import Enum
from abc import ABC, abstractmethod
import numpy as np
import pandas as pd
from decimal import Decimal

# ═══════════════════════════════════════════════════════════════════════════
# TYPE ALIASES
# ═══════════════════════════════════════════════════════════════════════════

# بازار و قیمت‌ها
Price: TypeVar = float  # قیمت
Volume: TypeVar = float  # حجم تراکنش
Symbol: TypeVar = str  # نماد جفت ارزی (EURUSD, GBPUSD, ...)
Timeframe: TypeVar = Literal["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w", "1M"]
Timestamp: TypeVar = datetime

# داده‌های OHLCV
OHLCV = Dict[str, Union[Price, Volume, Timestamp]]
OHLCVSeries = pd.DataFrame  # DataFrame با ستون‌های open, high, low, close, volume

# فیچرها و سیگنال‌ها
Feature = Union[float, int, np.ndarray]
FeatureVector = Dict[str, Feature]
Signal = Literal[-1, 0, 1]  # -1: sell, 0: hold, 1: buy
SignalVector = Dict[str, Signal]

# تریدینگ
Position = Decimal  # اندازه پوزیشن
PnL = float  # سود و زیان
Leverage = float  # اهرم

# مدل
Prediction = float
Confidence = float  # 0.0 تا 1.0
ModelWeights = Dict[str, float]

# اعدادی و پیکربندی
ConfigDict = Dict[str, Any]
ParameterGrid = List[Dict[str, Any]]

# ═══════════════════════════════════════════════════════════════════════════
# PROTOCOL CLASSES (Duck Typing)
# ═══════════════════════════════════════════════════════════════════════════

class DataSource(Protocol):
    """پروتکل برای منابع داده"""
    
    def fetch(
        self,
        symbol: Symbol,
        start: datetime,
        end: datetime,
        timeframe: Timeframe
    ) -> OHLCVSeries:
        """دریافت داده‌های OHLCV"""
        ...
    
    def validate(self, data: OHLCVSeries) -> bool:
        """اعتبارسنجی داده‌ها"""
        ...


class FeatureCalculator(Protocol):
    """پروتکل برای محاسبه فیچرها"""
    
    def calculate(self, ohlcv: OHLCVSeries) -> OHLCVSeries:
        """محاسبه فیچرها از OHLCV"""
        ...
    
    def requires_lookback(self) -> int:
        """تعداد بارهای قبلی مورد نیاز"""
        ...


class TradingModel(Protocol):
    """پروتکل برای مدل‌های تریدینگ"""
    
    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        **kwargs: Any
    ) -> None:
        """آموزش مدل"""
        ...
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """پیش‌بینی"""
        ...
    
    def get_feature_importance(self) -> Dict[str, float]:
        """گرفتن اهمیت فیچرها"""
        ...


class Broker(Protocol):
    """پروتکل برای کانکتور‌های بروکر"""
    
    def connect(self) -> None:
        """اتصال به بروکر"""
        ...
    
    def place_order(
        self,
        symbol: Symbol,
        size: Position,
        side: Literal["buy", "sell"],
        **kwargs: Any
    ) -> str:
        """ثبت سفارش"""
        ...
    
    def get_balance(self) -> float:
        """دریافت موجودی حساب"""
        ...


# ═══════════════════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════════════════

class TimeframeEnum(Enum):
    """تایم‌فریم‌های معمول"""
    ONE_MIN = "1m"
    FIVE_MIN = "5m"
    FIFTEEN_MIN = "15m"
    THIRTY_MIN = "30m"
    ONE_HOUR = "1h"
    FOUR_HOUR = "4h"
    ONE_DAY = "1d"
    ONE_WEEK = "1w"
    ONE_MONTH = "1M"


class OrderType(Enum):
    """انواع سفارش"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderSide(Enum):
    """جهت سفارش"""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    """وضعیت سفارش"""
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELED = "canceled"
    REJECTED = "rejected"


class RiskLevel(Enum):
    """سطح ریسک"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"


# ═══════════════════════════════════════════════════════════════════════════
# DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class OHLCVBar:
    """نوار OHLCV منفرد"""
    timestamp: Timestamp
    open: Price
    high: Price
    low: Price
    close: Price
    volume: Volume
    
    def __post_init__(self) -> None:
        """اعتبارسنجی بعد از ایجاد"""
        if not (self.low <= self.close <= self.high and
                self.low <= self.open <= self.high):
            raise ValueError("Invalid OHLCV bar: prices not in valid range")


@dataclass
class Order:
    """سفارش تریدینگ"""
    symbol: Symbol
    side: OrderSide
    type: OrderType
    size: Position
    price: Optional[Price] = None
    stop_price: Optional[Price] = None
    created_at: Timestamp = field(default_factory=datetime.now)
    status: OrderStatus = OrderStatus.PENDING
    filled_size: Position = 0
    filled_price: Optional[Price] = None
    commission: float = 0.0
    
    def is_filled(self) -> bool:
        """آیا سفارش انجام شده است"""
        return self.status == OrderStatus.FILLED or \
               self.filled_size == self.size


@dataclass
class Position:
    """پوزیشن باز"""
    symbol: Symbol
    size: Position
    entry_price: Price
    entry_time: Timestamp
    pnl: PnL = 0.0
    pnl_percent: float = 0.0
    current_price: Optional[Price] = None
    
    def calculate_pnl(self, current_price: Price) -> Tuple[PnL, float]:
        """محاسبه سود و زیان"""
        self.current_price = current_price
        self.pnl = (current_price - self.entry_price) * self.size
        self.pnl_percent = (self.pnl / (self.entry_price * self.size)) * 100
        return self.pnl, self.pnl_percent


@dataclass
class TradeMetrics:
    """معیارهای تریدینگ"""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: PnL = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    consecutive_wins: int = 0
    consecutive_losses: int = 0
    
    def calculate_win_rate(self) -> float:
        """محاسبه نرخ برد"""
        if self.total_trades == 0:
            return 0.0
        self.win_rate = (self.winning_trades / self.total_trades) * 100
        return self.win_rate
    
    def calculate_profit_factor(self) -> float:
        """محاسبه ضریب سود"""
        if self.avg_loss == 0:
            return 0.0
        self.profit_factor = self.avg_win / abs(self.avg_loss) if self.avg_loss != 0 else 0.0
        return self.profit_factor


@dataclass
class RiskMetrics:
    """معیارهای ریسک"""
    value_at_risk: float = 0.0  # VaR
    expected_shortfall: float = 0.0  # CVaR
    beta: float = 0.0
    correlation: float = 0.0
    volatility: float = 0.0
    risk_level: RiskLevel = RiskLevel.MEDIUM


# ═══════════════════════════════════════════════════════════════════════════
# ABSTRACT BASE CLASSES (ABC)
# ═══════════════════════════════════════════════════════════════════════════

class BaseDataFetcher(ABC):
    """کلاس پایه برای دریافت داده‌ها"""
    
    @abstractmethod
    def fetch(
        self,
        symbol: Symbol,
        start: datetime,
        end: datetime,
        timeframe: Timeframe = "1d"
    ) -> OHLCVSeries:
        """دریافت داده‌های OHLCV"""
        pass
    
    @abstractmethod
    def validate(self, data: OHLCVSeries) -> bool:
        """اعتبارسنجی داده‌ها"""
        pass


class BaseFeatureEngineer(ABC):
    """کلاس پایه برای مهندسی فیچر"""
    
    @abstractmethod
    def calculate(self, ohlcv: OHLCVSeries) -> OHLCVSeries:
        """محاسبه فیچرها"""
        pass
    
    @abstractmethod
    def get_feature_names(self) -> List[str]:
        """لیست نام‌های فیچرها"""
        pass


class BaseModel(ABC):
    """کلاس پایه برای مدل‌های ML"""
    
    @abstractmethod
    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        **kwargs: Any
    ) -> None:
        """آموزش مدل"""
        pass
    
    @abstractmethod
    def predict(self, X: np.ndarray) -> np.ndarray:
        """پیش‌بینی"""
        pass
    
    @abstractmethod
    def save(self, path: Union[str, Path]) -> None:
        """ذخیره‌سازی مدل"""
        pass
    
    @abstractmethod
    def load(self, path: Union[str, Path]) -> None:
        """بارگذاری مدل"""
        pass


class BaseStrategy(ABC):
    """کلاس پایه برای استراتژی‌های تریدینگ"""
    
    @abstractmethod
    def generate_signals(self, features: OHLCVSeries) -> SignalVector:
        """تولید سیگنال‌های تریدینگ"""
        pass
    
    @abstractmethod
    def validate_signals(self, signals: SignalVector) -> bool:
        """اعتبارسنجی سیگنال‌ها"""
        pass


class BaseRiskManager(ABC):
    """کلاس پایه برای مدیریت ریسک"""
    
    @abstractmethod
    def calculate_position_size(
        self,
        capital: float,
        risk_percent: float,
        stop_loss_points: float
    ) -> Position:
        """محاسبه اندازه پوزیشن"""
        pass
    
    @abstractmethod
    def check_portfolio_constraints(
        self,
        positions: List[Position],
        capital: float
    ) -> bool:
        """بررسی محدودیت‌های پورتفولیو"""
        pass


class BaseBroker(ABC):
    """کلاس پایه برای کانکتور‌های بروکر"""
    
    @abstractmethod
    def connect(self) -> bool:
        """اتصال به بروکر"""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """قطع اتصال از بروکر"""
        pass
    
    @abstractmethod
    def place_order(
        self,
        symbol: Symbol,
        side: OrderSide,
        size: Position,
        **kwargs: Any
    ) -> str:
        """ثبت سفارش"""
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """لغو سفارش"""
        pass
    
    @abstractmethod
    def get_account_info(self) -> Dict[str, Any]:
        """گرفتن اطلاعات حساب"""
        pass


# ═══════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS WITH TYPE HINTS
# ═══════════════════════════════════════════════════════════════════════════

def validate_price(price: float) -> bool:
    """اعتبارسنجی قیمت"""
    return isinstance(price, (int, float)) and price > 0


def validate_volume(volume: float) -> bool:
    """اعتبارسنجی حجم"""
    return isinstance(volume, (int, float)) and volume >= 0


def validate_symbol(symbol: Symbol) -> bool:
    """اعتبارسنجی نماد"""
    return isinstance(symbol, str) and len(symbol) >= 3


def validate_dataframe(
    df: pd.DataFrame,
    required_columns: Optional[List[str]] = None
) -> bool:
    """اعتبارسنجی DataFrame"""
    if not isinstance(df, pd.DataFrame):
        return False
    
    if required_columns is None:
        required_columns = ['open', 'high', 'low', 'close', 'volume']
    
    return all(col in df.columns for col in required_columns)


def calculate_returns(prices: np.ndarray) -> np.ndarray:
    """محاسبه بازده‌های روزانه"""
    if len(prices) < 2:
        return np.array([])
    return np.diff(prices) / prices[:-1]


def calculate_sharpe_ratio(
    returns: np.ndarray,
    risk_free_rate: float = 0.02,
    periods_per_year: int = 252
) -> float:
    """محاسبه نسبت شارپ"""
    if len(returns) == 0:
        return 0.0
    
    excess_returns = np.mean(returns) - risk_free_rate / periods_per_year
    std_returns = np.std(returns)
    
    if std_returns == 0:
        return 0.0
    
    return excess_returns / std_returns * np.sqrt(periods_per_year)


def calculate_max_drawdown(returns: np.ndarray) -> float:
    """محاسبه maximum drawdown"""
    if len(returns) == 0:
        return 0.0
    
    cumulative = np.cumprod(1 + returns)
    running_max = np.maximum.accumulate(cumulative)
    drawdown = (cumulative - running_max) / running_max
    
    return np.min(drawdown)


def format_price(price: float, decimals: int = 4) -> str:
    """فرمت‌کردن قیمت برای نمایش"""
    return f"{price:.{decimals}f}"


def normalize_features(
    features: np.ndarray,
    method: Literal["zscore", "minmax"] = "zscore"
) -> Tuple[np.ndarray, Dict[str, float]]:
    """نرمال‌سازی فیچرها"""
    stats: Dict[str, float] = {}
    
    if method == "zscore":
        mean = np.mean(features, axis=0)
        std = np.std(features, axis=0)
        normalized = (features - mean) / (std + 1e-8)
        stats = {"mean": float(mean), "std": float(std)}
    
    elif method == "minmax":
        min_val = np.min(features, axis=0)
        max_val = np.max(features, axis=0)
        normalized = (features - min_val) / (max_val - min_val + 1e-8)
        stats = {"min": float(min_val), "max": float(max_val)}
    
    else:
        raise ValueError(f"Unknown normalization method: {method}")
    
    return normalized, stats


def resample_ohlcv(
    ohlcv: OHLCVSeries,
    target_timeframe: Timeframe
) -> OHLCVSeries:
    """تغییر مقیاس OHLCV"""
    ohlcv_copy = ohlcv.copy()
    ohlcv_copy.index = pd.to_datetime(ohlcv_copy.index)
    
    resampled = ohlcv_copy.resample(target_timeframe).agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    })
    
    return resampled.dropna()


def merge_features(
    base_features: OHLCVSeries,
    additional_features: Dict[str, np.ndarray]
) -> OHLCVSeries:
    """ترکیب فیچرهای اضافی"""
    result = base_features.copy()
    
    for feature_name, feature_values in additional_features.items():
        if len(feature_values) == len(result):
            result[feature_name] = feature_values
    
    return result


def create_feature_window(
    data: OHLCVSeries,
    window_size: int
) -> Sequence[FeatureVector]:
    """ایجاد پنجره‌های فیچر برای sequence models"""
    windows: List[FeatureVector] = []
    
    for i in range(len(data) - window_size + 1):
        window = data.iloc[i:i + window_size]
        feature_dict: FeatureVector = {}
        
        for col in window.columns:
            feature_dict[col] = window[col].values
        
        windows.append(feature_dict)
    
    return windows


def backtest_strategy(
    signals: SignalVector,
    prices: pd.Series,
    initial_capital: float = 10000.0
) -> Tuple[TradeMetrics, pd.Series]:
    """بک‌تست استراتژی"""
    capital = initial_capital
    equity_curve: List[float] = [capital]
    trades: List[Dict[str, Any]] = []
    
    for i in range(1, len(prices)):
        signal = signals.get(i, 0)
        price = prices.iloc[i]
        
        if signal == 1:  # Buy signal
            trade = {"entry_price": price, "entry_index": i}
            trades.append(trade)
        
        elif signal == -1 and trades:  # Sell signal
            trade = trades.pop()
            pnl = (price - trade["entry_price"]) * 100
            capital += pnl
        
        equity_curve.append(capital)
    
    metrics = TradeMetrics(
        total_trades=len(trades),
        total_pnl=capital - initial_capital
    )
    
    equity_series = pd.Series(equity_curve, index=prices.index[:len(equity_curve)])
    
    return metrics, equity_series


# ═══════════════════════════════════════════════════════════════════════════
# GENERIC CLASSES
# ═══════════════════════════════════════════════════════════════════════════

T = TypeVar('T')  # Type variable


class Cache(Generic[T]):
    """کیش عمومی برای ذخیره‌سازی داده‌ها"""
    
    def __init__(self, max_size: int = 1000) -> None:
        self.max_size = max_size
        self._cache: Dict[str, T] = {}
        self._access_count: Dict[str, int] = {}
    
    def get(self, key: str) -> Optional[T]:
        """دریافت از کیش"""
        if key in self._cache:
            self._access_count[key] = self._access_count.get(key, 0) + 1
            return self._cache[key]
        return None
    
    def set(self, key: str, value: T) -> None:
        """ذخیره‌سازی در کیش"""
        if len(self._cache) >= self.max_size:
            lru_key = min(self._access_count, key=self._access_count.get)
            del self._cache[lru_key]
            del self._access_count[lru_key]
        
        self._cache[key] = value
    
    def clear(self) -> None:
        """پاک کردن کیش"""
        self._cache.clear()
        self._access_count.clear()


class TimeSeries(Generic[T]):
    """سری‌های زمانی عمومی"""
    
    def __init__(self, data: Optional[Dict[Timestamp, T]] = None) -> None:
        self.data: Dict[Timestamp, T] = data or {}
    
    def add(self, timestamp: Timestamp, value: T) -> None:
        """افزودن مقدار"""
        self.data[timestamp] = value
    
    def get(self, timestamp: Timestamp) -> Optional[T]:
        """دریافت مقدار"""
        return self.data.get(timestamp)
    
    def get_range(
        self,
        start: Timestamp,
        end: Timestamp
    ) -> Dict[Timestamp, T]:
        """دریافت دامنه‌ای از داده‌ها"""
        return {
            ts: val for ts, val in self.data.items()
            if start <= ts <= end
        }
    
    def to_series(self) -> pd.Series:
        """تبدیل به pandas Series"""
        return pd.Series(self.data)


# ═══════════════════════════════════════════════════════════════════════════
# OVERLOADED FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

@overload
def aggregate_signals(signals: List[Signal]) -> Signal:
    ...

@overload
def aggregate_signals(signals: Dict[str, Signal]) -> Signal:
    ...

def aggregate_signals(
    signals: Union[List[Signal], Dict[str, Signal]]
) -> Signal:
    """ترکیب سیگنال‌ها"""
    if isinstance(signals, dict):
        signals = list(signals.values())
    
    if not signals:
        return 0
    
    avg_signal = sum(signals) / len(signals)
    
    if avg_signal > 0.5:
        return 1
    elif avg_signal < -0.5:
        return -1
    else:
        return 0


@overload
def validate_config(config: Dict[str, Any]) -> bool:
    ...

@overload
def validate_config(config: str) -> bool:
    ...

def validate_config(config: Union[Dict[str, Any], str]) -> bool:
    """اعتبارسنجی پیکربندی"""
    if isinstance(config, str):
        try:
            import json
            config = json.loads(config)
        except json.JSONDecodeError:
            return False
    
    required_keys = {'data_dir', 'model_dir', 'api_key'}
    return all(key in config for key in required_keys)


# ═══════════════════════════════════════════════════════════════════════════
# CONTEXT MANAGERS
# ═══════════════════════════════════════════════════════════════════════════

class BrokerContext:
    """Context manager برای اتصال بروکر"""
    
    def __init__(self, broker: Broker) -> None:
        self.broker = broker
    
    def __enter__(self) -> Broker:
        self.broker.connect()
        return self.broker
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.broker.disconnect()


class DataFetcherContext:
    """Context manager برای دریافت داده‌ها"""
    
    def __init__(
        self,
        fetcher: DataSource,
        symbol: Symbol,
        start: datetime,
        end: datetime
    ) -> None:
        self.fetcher = fetcher
        self.symbol = symbol
        self.start = start
        self.end = end
        self.data: Optional[OHLCVSeries] = None
    
    def __enter__(self) -> OHLCVSeries:
        self.data = self.fetcher.fetch(
            self.symbol,
            self.start,
            self.end,
            "1d"
        )
        return self.data
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        # Cleanup if needed
        pass


# ═══════════════════════════════════════════════════════════════════════════
# FINAL CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════

DEFAULT_RISK_PERCENT: Final[float] = 2.0
DEFAULT_MAX_DRAWDOWN: Final[float] = 0.20
DEFAULT_MIN_WIN_RATE: Final[float] = 0.45
MAX_LEVERAGE: Final[float] = 10.0
MIN_POSITION_SIZE: Final[float] = 0.01


# ═══════════════════════════════════════════════════════════════════════════
# MODULE DOCSTRING EXAMPLE
# ═══════════════════════════════════════════════════════════════════════════

"""
استفاده از Type Hints:

>>> from type_hints_module import *
>>> 
>>> # استفاده با توابع
>>> price: Price = 1.2345
>>> symbol: Symbol = "EURUSD"
>>> timeframe: Timeframe = "1h"
>>> 
>>> # استفاده با کلاس‌ها
>>> bar = OHLCVBar(
...     timestamp=datetime.now(),
...     open=1.20,
...     high=1.25,
...     low=1.19,
...     close=1.23,
...     volume=1000000
... )
>>> 
>>> # استفاده با توابع typed
>>> returns = calculate_returns(np.array([1.20, 1.22, 1.21]))
>>> sharpe = calculate_sharpe_ratio(returns)
>>> 
>>> # استفاده با Generics
>>> cache: Cache[str] = Cache(max_size=100)
>>> cache.set("key1", "value1")
>>> value = cache.get("key1")
>>> 
>>> # استفاده با Context Managers
>>> with BrokerContext(my_broker) as broker:
...     account = broker.get_account_info()
...     print(account)
"""

if __name__ == "__main__":
    print("Type Hints Module - Trading AI System")
    print("=" * 50)
    print("\n✅ تمام توابع Type Hints دارند")
    print("✅ Generic Types پشتیبانی شده‌اند")
    print("✅ Protocol Classes برای Duck Typing")
    print("✅ Abstract Base Classes برای Inheritance")
    print("✅ Data Classes برای ساختار‌های داده")
    print("\nبرای استفاده:")
    print(">>> from type_hints_module import *")
