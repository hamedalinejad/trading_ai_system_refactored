# 📝 راهنمای کامل Type Hints برای Trading AI System

## 📌 مقدمه

این راهنما شامل تمامی نکات مهم **Type Hints** در پروژه است. Type Hints:
- ✅ IDE support بهتر
- ✅ Type checking و validation
- ✅ Documentation خودکار
- ✅ Refactoring آسان‌تر
- ✅ Bug detection در زمان development

---

## 🎯 اهداف Type Hints در این پروژه

### 1️⃣ **تمام توابع باید typed باشند**
```python
# ❌ بد - بدون type hints
def calculate_position_size(capital, risk):
    return capital * risk / 100

# ✅ خوب - با type hints
def calculate_position_size(capital: float, risk: float) -> float:
    return capital * risk / 100
```

### 2️⃣ **تمام پارامترها و return values باید typed باشند**
```python
# ✅ کامل typed
def fetch_ohlcv(
    symbol: str,
    start: datetime,
    end: datetime,
    timeframe: str = "1d"
) -> pd.DataFrame:
    pass
```

### 3️⃣ **از Type Aliases برای readability استفاده کنید**
```python
from typing import TypeVar

Price = float
Volume = float
Symbol = str

def validate_price(price: Price) -> bool:
    return price > 0
```

---

## 📚 Type Hints الگو‌ها

### Pattern 1: Basic Types
```python
from typing import List, Dict, Tuple, Optional, Union

def process_prices(
    prices: List[float],
    multiplier: int = 2
) -> float:
    """
    پردازش قیمت‌ها
    
    Args:
        prices: لیست قیمت‌ها
        multiplier: ضریب ضرب
    
    Returns:
        حاصل پردازش
    """
    return sum(prices) * multiplier
```

### Pattern 2: Optional Values
```python
from typing import Optional

def get_config_value(
    key: str,
    default: Optional[str] = None
) -> Optional[str]:
    """گرفتن مقدار از کانفیگ"""
    config = {"api_key": "secret"}
    return config.get(key, default)
```

### Pattern 3: Union Types
```python
from typing import Union
from pathlib import Path

def load_config(
    path: Union[str, Path]
) -> Dict[str, Any]:
    """بارگذاری کانفیگ از مسیر"""
    if isinstance(path, str):
        path = Path(path)
    return json.loads(path.read_text())
```

### Pattern 4: Callable
```python
from typing import Callable

def apply_strategy(
    features: np.ndarray,
    strategy_func: Callable[[np.ndarray], float]
) -> float:
    """اعمال استراتژی"""
    return strategy_func(features)
```

### Pattern 5: Generic Types
```python
from typing import TypeVar, Generic

T = TypeVar('T')

class Cache(Generic[T]):
    def __init__(self, max_size: int) -> None:
        self.data: Dict[str, T] = {}
    
    def set(self, key: str, value: T) -> None:
        self.data[key] = value
    
    def get(self, key: str) -> Optional[T]:
        return self.data.get(key)

# استفاده
string_cache: Cache[str] = Cache(100)
number_cache: Cache[float] = Cache(100)
```

### Pattern 6: Protocols (Duck Typing)
```python
from typing import Protocol

class DataFetcher(Protocol):
    def fetch(self, symbol: str) -> pd.DataFrame:
        ...
    
    def validate(self, data: pd.DataFrame) -> bool:
        ...

# هر کلاسی که این متودها داشته باشد compatible است
def use_fetcher(fetcher: DataFetcher):
    data = fetcher.fetch("EURUSD")
    if fetcher.validate(data):
        return data
```

### Pattern 7: Overload
```python
from typing import overload, Union

@overload
def aggregate_signals(signals: List[int]) -> int:
    ...

@overload
def aggregate_signals(signals: Dict[str, int]) -> int:
    ...

def aggregate_signals(signals: Union[List[int], Dict[str, int]]) -> int:
    if isinstance(signals, dict):
        signals = list(signals.values())
    return 1 if sum(signals) > 0 else -1
```

---

## 🏗️ Type Hints برای ساختار‌های داده

### Dataclass مثال
```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Trade:
    symbol: str
    entry_price: float
    entry_time: datetime
    size: float
    pnl: float = 0.0
    
    def __post_init__(self) -> None:
        """اعتبارسنجی بعد از ایجاد"""
        if self.entry_price <= 0:
            raise ValueError("Price must be positive")
```

### Dict Type Hints
```python
# Simple dict
config: Dict[str, Any] = {}

# Nested dict
settings: Dict[str, Dict[str, float]] = {
    "risk": {"max_drawdown": 0.20, "position_size": 0.02}
}

# TypedDict (Python 3.8+)
from typing import TypedDict

class Config(TypedDict):
    api_key: str
    max_drawdown: float
    leverage: int

config: Config = {
    "api_key": "secret",
    "max_drawdown": 0.20,
    "leverage": 10
}
```

---

## 🔍 Type Checking Tools

### 1. mypy - Static Type Checker
```bash
# نصب
pip install mypy

# بررسی فایل
mypy trading_ai_system/core.py

# بررسی کل پروژه
mypy trading_ai_system/

# تنظیم configuration
# mypy.ini یا setup.cfg:
[mypy]
python_version = 3.9
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
```

### 2. pyright - Microsoft's Type Checker
```bash
# نصب
pip install pyright

# بررسی
pyright trading_ai_system/
```

### 3. IDE Support
```python
# VSCode + Pylance
# محیط توصیه شده برای best IDE support

# PyCharm
# داخلی type checking دارد

# vim/neovim
# با plugin‌های مختلف
```

---

## 📋 Type Hints Checklist

قبل از commit:

- [ ] تمام توابع typed هستند
- [ ] تمام پارامترها typed هستند
- [ ] تمام return values typed هستند
- [ ] از Type Aliases برای readability استفاده شده
- [ ] mypy بدون error اجرا شده
- [ ] Protocol/ABC برای inheritance استفاده شده
- [ ] Generic types جایی که لازم است استفاده شده
- [ ] Docstrings با type info نوشته شده

---

## 🚀 Best Practices

### 1. Type Aliases برای Clarity
```python
from typing import TypeVar

# ❌ نامفهوم
def process(x: float, y: float) -> float:
    pass

# ✅ واضح
Price = float
Volume = float

def calculate_value(price: Price, volume: Volume) -> Price:
    return price * volume
```

### 2. Optional vs Union[X, None]
```python
from typing import Optional, Union

# ✅ ترجیح داده می‌شود
def get_value(key: str) -> Optional[str]:
    return config.get(key)

# این هم درست است
def get_value(key: str) -> Union[str, None]:
    return config.get(key)
```

### 3. List vs Sequence
```python
from typing import List, Sequence

# اگر modify می‌کنیم: List
def sort_prices(prices: List[float]) -> List[float]:
    return sorted(prices)

# اگر فقط read می‌کنیم: Sequence
def sum_prices(prices: Sequence[float]) -> float:
    return sum(prices)
```

### 4. Any کو تجنب کنید
```python
from typing import Any

# ❌ نه استفاده نکنید
def process(data: Any) -> Any:
    return data

# ✅ کمتر Any استفاده کنید
def process(data: Dict[str, float]) -> float:
    return sum(data.values())
```

### 5. Type Comments برای Older Python
```python
# Python 3.5 style (قدیمی)
def calculate(x, y):
    # type: (float, float) -> float
    return x + y

# Python 3.9+ style (جدید - ترجیح داده می‌شود)
def calculate(x: float, y: float) -> float:
    return x + y
```

---

## 📊 Type Hints در Testing

```python
import pytest
from typing import List

class TestCalculations:
    @pytest.fixture
    def prices(self) -> List[float]:
        """قیمت‌های نمونه"""
        return [1.20, 1.25, 1.22]
    
    def test_average_price(self, prices: List[float]) -> None:
        """تست میانگین قیمت"""
        avg: float = sum(prices) / len(prices)
        assert abs(avg - 1.223) < 0.001
    
    def test_price_range(self, prices: List[float]) -> None:
        """تست دامنه قیمت‌ها"""
        min_price: float = min(prices)
        max_price: float = max(prices)
        assert min_price < max_price
```

---

## 🔗 Type Hints در Module Integration

### core.py مثال
```python
from typing import Dict, Any, Optional
from datetime import datetime
import pandas as pd

class Config:
    def __init__(self) -> None:
        self.settings: Dict[str, Any] = {}
    
    def load(self, path: str) -> bool:
        """بارگذاری کانفیگ"""
        try:
            import json
            with open(path, 'r') as f:
                self.settings = json.load(f)
            return True
        except Exception as e:
            print(f"Error loading config: {e}")
            return False
    
    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """گرفتن مقدار از کانفیگ"""
        return self.settings.get(key, default)
```

### data.py مثال
```python
from typing import Optional, Tuple
from datetime import datetime
import pandas as pd

class DataFetcher:
    def fetch(
        self,
        symbol: str,
        start: datetime,
        end: datetime
    ) -> Optional[pd.DataFrame]:
        """دریافت داده‌های OHLCV"""
        try:
            # Fetch logic
            return pd.DataFrame()
        except Exception:
            return None
    
    def validate(self, data: pd.DataFrame) -> Tuple[bool, str]:
        """اعتبارسنجی داده‌ها"""
        if data.empty:
            return False, "Empty dataframe"
        
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in data.columns for col in required_cols):
            return False, "Missing required columns"
        
        return True, "Valid"
```

---

## ⚠️ Common Mistakes

### Mistake 1: Forgetting Return Type
```python
# ❌ نادرست
def calculate_position_size(capital: float, risk: float):
    return capital * risk

# ✅ درست
def calculate_position_size(capital: float, risk: float) -> float:
    return capital * risk
```

### Mistake 2: Using mutable defaults
```python
# ❌ نادرست و خطرناک
def add_signal(signals: List[int] = []) -> List[int]:
    signals.append(1)
    return signals

# ✅ درست
def add_signal(signals: Optional[List[int]] = None) -> List[int]:
    if signals is None:
        signals = []
    signals.append(1)
    return signals
```

### Mistake 3: Not importing from typing
```python
# ❌ در Python < 3.9
def process(items: list[int]) -> dict[str, int]:
    pass

# ✅ درست
from typing import List, Dict

def process(items: List[int]) -> Dict[str, int]:
    pass
```

### Mistake 4: Too broad types
```python
# ❌ خیلی عمومی
def process(data: Any) -> Any:
    pass

# ✅ خاص‌تر
def process(data: Dict[str, float]) -> float:
    return sum(data.values())
```

---

## 📚 مثال کامل: Position Manager

```python
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class PositionSide(Enum):
    LONG = "long"
    SHORT = "short"

@dataclass
class Position:
    symbol: str
    side: PositionSide
    size: float
    entry_price: float
    entry_time: datetime
    pnl: float = 0.0

class PositionManager:
    def __init__(self, initial_capital: float) -> None:
        self.capital: float = initial_capital
        self.positions: Dict[str, Position] = {}
    
    def open_position(
        self,
        symbol: str,
        side: PositionSide,
        size: float,
        price: float
    ) -> bool:
        """باز کردن پوزیشن"""
        if symbol in self.positions:
            return False
        
        position = Position(
            symbol=symbol,
            side=side,
            size=size,
            entry_price=price,
            entry_time=datetime.now()
        )
        self.positions[symbol] = position
        return True
    
    def close_position(
        self,
        symbol: str,
        exit_price: float
    ) -> Optional[float]:
        """بسته کردن پوزیشن"""
        if symbol not in self.positions:
            return None
        
        position = self.positions.pop(symbol)
        pnl = (exit_price - position.entry_price) * position.size
        self.capital += pnl
        
        return pnl
    
    def get_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """گرفتن ارزش پورتفولیو"""
        portfolio_value: float = self.capital
        
        for symbol, position in self.positions.items():
            if symbol in current_prices:
                current_price = current_prices[symbol]
                position_value = (current_price - position.entry_price) * position.size
                portfolio_value += position_value
        
        return portfolio_value
    
    def get_positions_summary(self) -> List[Dict[str, any]]:
        """خلاصه پوزیشن‌ها"""
        summary: List[Dict[str, any]] = []
        
        for symbol, position in self.positions.items():
            summary.append({
                "symbol": symbol,
                "side": position.side.value,
                "size": position.size,
                "entry_price": position.entry_price,
                "pnl": position.pnl
            })
        
        return summary
```

---

## 🎓 لینک‌های مفید

- **PEP 484**: https://www.python.org/dev/peps/pep-0484/
- **PEP 585**: https://www.python.org/dev/peps/pep-0585/
- **mypy**: https://mypy.readthedocs.io/
- **typing module**: https://docs.python.org/3/library/typing.html

---

## ✅ نتیجه‌گیری

**Type Hints** بخش جدایی‌ناپذیر از توسعه کد حرفه‌ای هستند:

1. ✅ IDE support بهتر → productivity بیشتر
2. ✅ Type checking → bugs کمتر
3. ✅ Documentation → maintenance آسان‌تر
4. ✅ Refactoring → ریسک کمتر

**توصیه:** تمام کد جدید با Type Hints بنویسید!

---

**نسخه**: 0.79.0  
**تاریخ**: تیر 1405  
**نویسنده**: Hamed
