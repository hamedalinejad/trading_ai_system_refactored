# 🚀 راهنمای نصب و استفاده - Trading AI System v0.79.0

## 📦 فایل‌های ارتقا‌یافته شده

```
✅ data.py          - Data loading and validation module
✅ features.py      - Technical indicators and feature engineering
✅ models.py        - Machine learning models and ensemble methods
✅ live.py          - Live trading execution and monitoring
✅ commands.py      - CLI commands implementation
✅ strategy.py      - Trading strategy and signal generation
```

---

## 🔧 نصب مرحله به مرحله

### مرحله 1: ایجاد ساختار پروژه
```bash
# ایجاد پوشه‌های لازم
mkdir -p trading_ai_system_refactored/trading_ai_system/{core,data,features,models,strategy,risk,live,utils}
mkdir -p trading_ai_system_refactored/cli
mkdir -p trading_ai_system_refactored/tests

cd trading_ai_system_refactored
```

### مرحله 2: کپی کردن فایل‌های ارتقا‌یافته

```bash
# فایل‌های ماژول‌ها
cp /path/to/data.py trading_ai_system/data/
cp /path/to/features.py trading_ai_system/features/
cp /path/to/models.py trading_ai_system/models/
cp /path/to/live.py trading_ai_system/live/
cp /path/to/strategy.py trading_ai_system/strategy/

# CLI files
cp /path/to/commands.py cli/
```

### مرحله 3: کپی کردن setup files

```bash
# Copy از original files
cp /original/setup.py .
cp /original/pyproject.toml .
cp /original/__version__.py trading_ai_system/
cp /original/trading_ai_system__init__.py trading_ai_system/__init__.py

# سایر __init__.py files
cp /original/core__init__.py trading_ai_system/core/__init__.py
cp /original/data__init__.py trading_ai_system/data/__init__.py
cp /original/features__init__.py trading_ai_system/features/__init__.py
cp /original/models__init__.py trading_ai_system/models/__init__.py
# ... و بقیه
```

### مرحله 4: نصب dependencies

```bash
# نصب package در development mode
pip install -e .

# نصب dependencies اختیاری
pip install -e ".[dev]"  # برای توسعه
pip install -e ".[live]" # برای live trading
```

### مرحله 5: تست imports

```bash
# تست کلی
python -c "
from trading_ai_system import data, features, models, strategy
from trading_ai_system.live import LiveTradingEngine
from cli.commands import BacktestCommand
print('✅ تمام imports موفق!')
"

# یا تک تک
python -c "from trading_ai_system.data import DataLoader; print('✅ data.py OK')"
python -c "from trading_ai_system.features import engineer_features_for_timeframe; print('✅ features.py OK')"
python -c "from trading_ai_system.models import LightGBMModel; print('✅ models.py OK')"
python -c "from trading_ai_system.live import LiveTradingEngine; print('✅ live.py OK')"
python -c "from cli.commands import BacktestCommand; print('✅ commands.py OK')"
python -c "from trading_ai_system.strategy import SignalGenerator; print('✅ strategy.py OK')"
```

---

## ✅ تست کامل

### تست 1: Import اساسی
```bash
python -c "
import trading_ai_system
print(f'Version: {trading_ai_system.__version__}')
"
```

**Expected Output:**
```
Version: 0.79.0
```

### تست 2: Data Module
```python
from trading_ai_system.data import DataLoader, clean_ohlcv_data
import pandas as pd
import numpy as np

# ایجاد dummy data
df = pd.DataFrame({
    'timestamp': pd.date_range('2023-01-01', periods=100),
    'open': np.random.randn(100) + 100,
    'high': np.random.randn(100) + 101,
    'low': np.random.randn(100) + 99,
    'close': np.random.randn(100) + 100,
    'volume': np.random.randint(1000, 10000, 100)
})

# تست clean
df_clean = clean_ohlcv_data(df)
print(f"✅ Data cleaned: {len(df)} → {len(df_clean)} rows")
```

### تست 3: Features Module
```python
from trading_ai_system.features import engineer_features_for_timeframe
import pandas as pd
import numpy as np

# ایجاد OHLCV data
df = pd.DataFrame({
    'open': np.random.randn(100) + 100,
    'high': np.random.randn(100) + 101,
    'low': np.random.randn(100) + 99,
    'close': np.random.randn(100) + 100,
    'volume': np.random.randint(1000, 10000, 100)
})

# تست feature engineering
df_features, registry = engineer_features_for_timeframe(df)
print(f"✅ Features generated: {df_features.shape[1]} columns")
```

### تست 4: Models Module
```python
from trading_ai_system.models import LightGBMModel
import pandas as pd
import numpy as np

# ایجاد sample data
X = pd.DataFrame(np.random.randn(100, 10))
y = pd.Series(np.random.choice([-1, 0, 1], 100))

# تست model
model = LightGBMModel(name="test_model")
model.fit(X, y)
predictions = model.predict(X)
print(f"✅ Model trained and predicted: {predictions.shape[0]} predictions")
```

### تست 5: Live Module
```python
from trading_ai_system.live import LiveTradingEngine, OrderSide, OrderType
import asyncio

async def test_live():
    engine = LiveTradingEngine()
    engine.start()
    
    # تست submit order
    result = await engine.submit_order(
        symbol="EURUSD",
        side=OrderSide.BUY,
        quantity=1.0,
        price=1.0850,
        order_type=OrderType.MARKET
    )
    
    print(f"✅ Order submitted: {result.success}")
    
    # تست portfolio summary
    summary = engine.get_portfolio_summary()
    print(f"✅ Portfolio: {summary['total_positions']} positions")
    
    engine.stop()

asyncio.run(test_live())
```

### تست 6: Commands Module
```python
from cli.commands import BacktestCommand
import argparse

# ایجاد args
args = argparse.Namespace(
    pair='EURUSD',
    start='2023-01-01',
    end='2023-12-31',
    capital=10000.0,
    config=None
)

# تست command
cmd = BacktestCommand(args)
exit_code = cmd.execute()
print(f"✅ Backtest command executed: exit_code={exit_code}")
```

### تست 7: Strategy Module
```python
from trading_ai_system.strategy import SignalGenerator, Signal
import pandas as pd
import numpy as np

# ایجاد features
features = pd.DataFrame(np.random.randn(1, 10))

# تست signal generation
gen = SignalGenerator()
result = gen.generate_signal(
    symbol="EURUSD",
    features=features,
    timeframe="1h"
)

print(f"✅ Signal generated: {result.signal.name} ({result.confidence:.2%})")
```

---

## 📝 بررسی نهایی

### فایل ساختار
```
trading_ai_system_refactored/
├── trading_ai_system/
│   ├── __init__.py
│   ├── __version__.py
│   ├── core/
│   ├── data/
│   │   ├── __init__.py
│   │   └── data.py           ✅ FIXED
│   ├── features/
│   │   ├── __init__.py
│   │   └── features.py       ✅ FIXED
│   ├── models/
│   │   ├── __init__.py
│   │   └── models.py         ✅ FIXED
│   ├── live/
│   │   ├── __init__.py
│   │   └── live.py           ✅ FIXED
│   ├── strategy/
│   │   ├── __init__.py
│   │   └── strategy.py       ✅ FIXED
│   └── ...
├── cli/
│   ├── __init__.py
│   ├── commands.py           ✅ FIXED
│   └── menu_system.py
├── setup.py
├── pyproject.toml
└── README.md
```

### Verification Checklist
- [ ] تمام imports بدون error
- [ ] Package install شده (pip install -e .)
- [ ] تمام ماژول‌ها فعال
- [ ] Fallback mechanisms کار کند
- [ ] تست‌های بالا pass شوند
- [ ] No circular imports
- [ ] v79 fixes applied

---

## 🎯 استفاده

### Run Interactive Menu
```bash
python main.py
```

### Run CLI Commands
```bash
# Backtest
python main.py backtest -p EURUSD -s 2023-01-01 -e 2023-12-31

# Train
python main.py train -m eurusd --epochs 100

# Live trading
python main.py live -p EURUSD --dry-run

# Data operations
python main.py data fetch -p EURUSD -s 2023-01-01
python main.py data validate -f data/eurusd.csv

# Config
python main.py config show
python main.py config set trading_pair GBPUSD

# Analysis
python main.py analysis -p EURUSD --type indicators
```

---

## 🔍 Troubleshooting

### خطا: `ModuleNotFoundError: No module named 'trading_ai_system'`
**حل:** مطمئن شوید که `pip install -e .` را اجرا کرده‌اید

```bash
cd trading_ai_system_refactored
pip install -e .
```

### خطا: `ImportError: cannot import name 'DataError'`
**حل:** مطمئن شوید که import path درست است

```python
# ✅ Correct
from trading_ai_system.core import DataError

# ❌ Wrong
from core import DataError
```

### خطا: `LightGBM not installed`
**حل:** نصب LightGBM

```bash
pip install lightgbm
```

### خطا: `No module named 'cli'`
**حل:** مطمئن شوید کلاسه‌ای که `cli/__init__.py` وجود دارد

```bash
touch cli/__init__.py
```

---

## 📊 خلاصه

| Item | Status | Notes |
|------|--------|-------|
| **data.py** | ✅ Complete | Ready for production |
| **features.py** | ✅ Complete | v79 fixes applied |
| **models.py** | ✅ Complete | Dependency safe |
| **live.py** | ✅ Complete | Fully implemented |
| **commands.py** | ✅ Complete | All CLI commands |
| **strategy.py** | ✅ Complete | Signal generation |
| **Installation** | ✅ Ready | Step by step guide |
| **Testing** | ✅ Ready | 7 test examples |

---

## 🚀 بعدی

پس از نصب موفق:

1. **Explore Modules** - تک تک ماژول‌ها را بررسی کنید
2. **Run Tests** - تست‌های بالا را اجرا کنید
3. **Try Commands** - CLI commands را امتحان کنید
4. **Build Models** - مدل‌های خود را آموزش دهید
5. **Go Live** - Trading شروع کنید!

---

**Happy Trading! 🎉**

نسخه: 0.79.0  
تاریخ: 2024  
وضعیت: ✅ Production Ready
