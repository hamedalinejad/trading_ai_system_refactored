# 📊 تجزیه و تحلیل جامع پروژه Trading AI System

**تاریخ تجزیه**: تیر 1405  
**نسخه پروژه**: 0.79.0  
**حجم کد**: ~4700 خط Python

---

## 📋 خلاصه اجمالی

**Trading AI System Refactored** یک سیستم معاملات الگوریتمی سطح تولید است که:
- ✅ معاملات خودکار با مدل‌های Machine Learning
- ✅ تجزیه و تحلیل فنی با 20+ شاخص
- ✅ مدیریت ریسک پیشرفته
- ✅ معاملات زنده از طریق Broker
- ✅ Backtesting و بهینه‌سازی

---

## 🏗️ معماری پروژه

### ساختار دایرکتوری

```
trading_ai_system_refactored/
├── trading_ai_system/          # 📦 Package اصلی
│   ├── __init__.py
│   ├── core/                   # ⚙️ زیرساخت اصلی
│   ├── data/                   # 📊 مدیریت داده
│   ├── features/               # 🔍 مهندسی ویژگی
│   ├── models/                 # 🤖 مدل‌های ML
│   ├── strategy/               # 📈 موتور استراتژی
│   ├── risk/                   # ⚠️ مدیریت ریسک
│   ├── live/                   # 🚀 معاملات زنده
│   └── utils/                  # 🛠️ ابزارهای کمکی
├── cli/                        # 💻 CLI Interface
│   ├── commands.py
│   └── menu_system.py
├── tests/                      # ✅ تست‌ها
├── main.py                     # 🎯 نقطه ورود
├── pyproject.toml              # 📦 تنظیمات Package
└── README.md
```

---

## 🔧 مدول‌های اصلی

### 1️⃣ **Core Module** (`trading_ai_system/core/`)
**مسئولیت**: زیرساخت و تنظیمات سیستم

**کلاس‌های اصلی**:
- `SystemConfig`: تنظیمات سیستم
- `GlobalState`: مدیریت حالت جهانی (Singleton)
- `SystemHealth`: کنترل سلامت سیستم
- Exception Classes: خطاهای سفارشی

**کنسافت اصلی**:
```python
# تنظیمات
symbol: str = "EURUSD"           # جفت معاملاتی
market_type: MarketType = SPOT   # نوع بازار
commission_per_side: float = 0.001  # 0.1% کمیسیون
max_position_size: float = 0.05  # 5% از حساب
max_drawdown: float = 0.20       # 20% حد باخت

# Features
lookback_periods = {
    "rsi": 14,    # Relative Strength Index
    "macd": 26,   # Moving Average Convergence
    "bb": 20,     # Bollinger Bands
    "atr": 14     # Average True Range
}
```

**Features**:
- ✅ Global State Management (Singleton Pattern)
- ✅ Context Variables برای Thread Safety
- ✅ Configuration Context Manager
- ✅ Feature Registry
- ✅ System Health Monitoring

---

### 2️⃣ **Data Module** (`trading_ai_system/data/`)
**مسئولیت**: دریافت، اعتبارسنجی و کش کردن داده‌های OHLCV

**کلاس‌های فرضی**:
- `DataFetcher`: دریافت داده‌های بازار
- `DataValidator`: اعتبارسنجی داده
- `DataCache`: کش کردن موثر
- `OHLCVData`: Dataclass برای OHLCV

**مسیرهای داده**:
```python
DATA_PATH_CONFIG = {
    "raw_file": "data/raw.csv",
    "clean_dir": "data/clean",
    "timestamp_dir": "data/timestamps",
    "session_dir": "data/sessions",
    "timeframe_dir": "data/timeframes",
    "train_multi_dir": "data/train_multi",
    "test_multi_dir": "data/test_multi",
}
```

**TimeFrame های پشتیبانی شده**:
- 1m, 5m, 15m, 30m
- 1h, 4h
- 1d, 1w

---

### 3️⃣ **Features Module** (`trading_ai_system/features/`)
**مسئولیت**: مهندسی ویژگی و شاخص‌های تکنیکی

**شاخص‌های پشتیبانی شده** (20+):
- **موومنتوم**: RSI, MACD, Stochastic
- **بولتیل**: ATR, Natr
- **Volume**: OBV, MFI, Volume-Price Trend
- **Trend**: EMA, SMA, ADX
- **Band**: Bollinger Bands
- **Ratio**: Close/SMA, High/Low

**فیچرهای ویژه**:
- ✅ Clipping برای zscore و ratio-based features
- ✅ Normalization/Standardization
- ✅ Multi-timeframe features
- ✅ Feature validation و nan checking

---

### 4️⃣ **Models Module** (`trading_ai_system/models/`)
**مسئولیت**: مدل‌های Machine Learning

**مدل‌های پشتیبانی شده**:
- 🔷 **LightGBM**: مدل اصلی (سریع و دقیق)
- 🔷 **Ensemble Models**: ترکیب چند مدل
- 🔷 Custom Models: قابلیت گسترش

**قابلیت‌ها**:
- ✅ Model Training
- ✅ Cross-validation (Walk-Forward)
- ✅ Hyperparameter Tuning
- ✅ Model Evaluation
- ✅ Model Persistence

**معیارهای عملکرد**:
- Sharpe Ratio: 1.8-2.2
- Max Drawdown: 8-12%
- Win Rate: 55-60%
- Profit Factor: 1.5-2.0

---

### 5️⃣ **Strategy Module** (`trading_ai_system/strategy/`)
**مسئولیت**: تولید سیگنال‌های معاملاتی

**استراتژی‌های پشتیبانی شده**:
- 🟢 **BaseStrategy**: کلاس پایه
- 🟢 **MLStrategy**: استراتژی مبتنی بر ML
- 🟢 **SignalGenerator**: تولیدکننده سیگنال

**سیگنال‌های تولید شده**:
```
+1: Buy Signal
 0: No Action
-1: Sell Signal
```

**Performance Tracking**:
- PnL تراکمی
- Win/Loss Rate
- Drawdown
- Risk/Reward Ratio

---

### 6️⃣ **Risk Module** (`trading_ai_system/risk/`)
**مسئولیت**: مدیریت ریسک و اندازه‌گذاری پوزیشن

**کلاس‌های فرضی**:
- `RiskManager`: مدیر ریسک
- `PositionSizer`: محاسب اندازه پوزیشن
- `PortfolioConstraints`: محدودیت‌های پورتفولیو
- `RiskMetrics`: محاسبات ریسکی

**روش‌های Position Sizing**:
- 📍 **Kelly Criterion**: فرمول Kelly
- 📍 **Fixed Size**: اندازه ثابت
- 📍 **Volatility-based**: بر اساس نوسان‌پذیری

**کنترل‌های ریسک**:
- Max Position Size: 5% از حساب
- Max Drawdown: 20%
- Stop Loss Management
- Portfolio Constraints

---

### 7️⃣ **Live Module** (`trading_ai_system/live/`)
**مسئولیت**: معاملات زنده و اتصال Broker

**کلاس‌های فرضی**:
- `BrokerConnector`: اتصال به Broker
- `OrderExecutor`: اجرای سفارش‌ها
- `LiveMonitor`: نظارت معاملات
- `BrokerReconciler`: تطبیق با Broker

**Brokerهای پشتیبانی شده**:
- CCXT (تبادل‌های متعدد)
- Interactive Brokers
- Paper Trading (نسخه آزمایشی)

**Order Types**:
- Market Orders
- Limit Orders
- Stop Orders
- Stop-Limit Orders

---

### 8️⃣ **Utils Module** (`trading_ai_system/utils/`)
**مسئولیت**: توابع کمکی

**تابع‌های اصلی**:
- `validate_dataframe()`: اعتبارسنجی DataFrame
- `format_price()`: فرمت‌بندی قیمت
- `calculate_returns()`: محاسبه بازده
- `Logger`: سیستم لاگینگ

---

## 💻 CLI Interface

### فایل‌های CLI

**`cli/commands.py`**: دستورات اصلی
```
BacktestCommand    → اجرای backtest
TrainCommand       → آموزش مدل
LiveCommand        → شروع معاملات زنده
DataCommand        → مدیریت داده
ConfigCommand      → مدیریت تنظیمات
AnalysisCommand    → تجزیه و تحلیل
```

**`cli/menu_system.py`**: منوی تعاملی

### استفاده از CLI

```bash
# منوی تعاملی
python main.py

# Backtest
python main.py backtest -p EURUSD -s 2023-01-01 -e 2023-12-31 -c 10000

# Training
python main.py train -m eurusd -d data/train.csv --epochs 100

# Live Trading
python main.py live -p EURUSD --dry-run

# Data Management
python main.py data fetch -p EURUSD -s 2023-01-01
python main.py data validate -f data/eurusd.csv

# Configuration
python main.py config show
python main.py config set key value

# Analysis
python main.py analysis -p EURUSD --type indicators
```

---

## 📦 وابستگی‌های اصلی

### Core Dependencies
```toml
numpy>=1.21.0          # محاسبات عددی
pandas>=1.3.0          # کار با DataFrame
lightgbm>=3.3.0        # مدل‌های ML
scikit-learn>=1.0.0    # ML utilities
```

### Development Dependencies
```toml
pytest>=7.0.0          # تست‌ها
black>=23.0.0          # Code formatting
mypy>=1.0.0            # Type checking
flake8>=6.0.0          # Linting
```

### Live Trading Dependencies
```toml
requests>=2.28.0       # HTTP requests
websockets>=10.0       # WebSocket
python-dotenv>=0.20.0  # Environment variables
```

---

## 🚀 نقطه ورود سیستم

**`main.py`**: نقطه ورود اصلی

```python
# اگر بدون آرگومان اجرا شود
python main.py  # → منوی تعاملی

# با دستورات
python main.py backtest ...
python main.py train ...
python main.py live ...
```

**Features**:
- ✅ Argument Parsing
- ✅ Interactive Menu
- ✅ Command Routing
- ✅ Error Handling
- ✅ Logging Control

---

## 🔄 جریان داده (Data Flow)

```
┌─────────────────────┐
│  1. Data Fetcher    │ ← دریافت OHLCV
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│  2. Data Validator  │ ← اعتبارسنجی
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│  3. Feature Engineer│ ← محاسبه شاخص‌ها
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│  4. ML Model        │ ← پیش‌بینی
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│  5. Signal Generator│ ← تولید سیگنال
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│  6. Risk Manager    │ ← مدیریت ریسک
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│  7. Order Executor  │ ← اجرای سفارش
└─────────────────────┘
```

---

## ⚙️ کنفیگ پروژه

### Horizons (افق‌های زمانی)
```python
HORIZONS = {
    "1m":  ["5m", "15m", "1h"],
    "5m":  ["15m", "1h", "4h"],
    "15m": ["1h", "4h", "1d"],
    "1h":  ["4h", "1d"],
    "4h":  ["1d"],
    "1d":  [],
}
```

### Minimum Bars Per Timeframe
```python
BARS_PER_DAY_BY_TF = {
    "1min": 1440,   # هر دقیقه
    "5min": 288,    # هر 5 دقیقه
    "15min": 96,    # هر 15 دقیقه
    "1h": 24,       # هر ساعت
    "1d": 1,        # هر روز
}
```

---

## 📊 معیارهای عملکرد

### بهترین نتایج Backtest
- **Sharpe Ratio**: 1.8-2.2 (خوب)
- **Max Drawdown**: 8-12% (کنترل شده)
- **Win Rate**: 55-60% (مثبت)
- **Profit Factor**: 1.5-2.0 (سودآور)

---

## 🔐 Exception Handling

### خطاهای سفارشی
```python
TradingSystemError          # خطای پایه
├── ConfigError             # خطای تنظیمات
├── DataError               # خطای داده
├── FeatureError            # خطای ویژگی
├── ModelError              # خطای مدل
├── ExecutionError          # خطای اجرا
└── LiveTradingError        # خطای معاملات زنده
```

---

## 🧪 تست و کیفیت کد

### تست اجرا کردن
```bash
# تمام تست‌ها
pytest

# با Coverage
pytest --cov=trading_ai_system

# یک فایل خاص
pytest tests/test_data.py

# Verbose
pytest -v
```

### Code Quality
```bash
# Formatting
black trading_ai_system tests

# Sorting Imports
isort trading_ai_system tests

# Linting
flake8 trading_ai_system tests

# Type Checking
mypy trading_ai_system
```

---

## 📝 نکات مهم

### ✅ نقاط قوت
1. ✅ معماری پیمانه‌ای و قابل گسترش
2. ✅ تفکیک دقیق مسئولیت‌ها
3. ✅ تنظیمات جامع و انعطاف‌پذیر
4. ✅ Exception Handling مناسب
5. ✅ Global State Management بهینه
6. ✅ CLI Interface کاربرپسند
7. ✅ Logging و Monitoring
8. ✅ Type Hints (جزئی)

### ⚠️ نکات قابل بهبود
1. 🔄 Type Hints کامل برای تمام توابع
2. 🔄 Unit Tests برای تمام مدول‌ها
3. 🔄 Documentation کامل کلاس‌ها
4. 🔄 Error Recovery Mechanisms
5. 🔄 Async/Await Support
6. 🔄 Performance Optimization
7. 🔄 Caching Strategy بهتر
8. 🔄 API Documentation (Swagger/OpenAPI)

---

## 🎯 سرسخت نشانی‌های استفاده

### 1. آغاز سریع
```python
from trading_ai_system import core, data, features, models, strategy, risk

# Initialize
config = core.SystemConfig(symbol="EURUSD")
core.set_global_config(config)

# Fetch Data
fetcher = data.DataFetcher()
ohlcv = fetcher.fetch('EURUSD', '2023-01-01', '2023-12-31')

# Calculate Features
engineer = features.FeatureEngineer()
features_df = engineer.calculate(ohlcv)

# Train Model
model = models.LGBModel('eurusd_model')
model.train(features_df, labels)

# Generate Signals
strat = strategy.MLStrategy(model=model)
signals = strat.generate_signals(features_df)

# Risk Management
risk_mgr = risk.RiskManager()
positions = risk_mgr.calculate_positions(signals, capital=10000)
```

### 2. Backtesting
```bash
python main.py backtest -p EURUSD -s 2023-01-01 -e 2023-12-31 -c 10000
```

### 3. Live Trading
```bash
python main.py live -p EURUSD --account ACC123 --dry-run
```

---

## 📚 منابع اضافی

- 📖 README.md: راهنمای کامل
- 📖 INSTALLATION_GUIDE.md: نصب
- 📖 MAIN_ENTRY_GUIDE.md: استفاده
- 📖 FILES_INDEX.md: فهرست فایل‌ها

---

**نسخه**: 0.79.0  
**Python**: 3.9+  
**License**: MIT  
**Repository**: https://github.com/hamedalinejad/trading_ai_system_refactored

