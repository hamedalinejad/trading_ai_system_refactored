# 🚀 راهنمای سریع شروع (Quick Start Guide)

---

## 📦 نصب و راه‌اندازی

### 1. نصب پروژه

```bash
# کلون کردن Repository
git clone https://github.com/hamedalinejad/trading_ai_system_refactored.git
cd trading_ai_system_refactored

# نصب وابستگی‌ها
pip install -e .

# یا با اختیارات
pip install -e ".[dev,live]"
```

### 2. اجرای اولیه

```bash
# اجرای منوی تعاملی
python main.py

# یا اجرای یک دستور
python main.py backtest -p EURUSD
```

---

## 🎯 استفاده‌های متداول

### الف. Backtesting (آزمایش عملکرد)

```bash
# کل سال 2023
python main.py backtest -p EURUSD -s 2023-01-01 -e 2023-12-31

# با سرمایه مختلف
python main.py backtest -p EURUSD -c 50000

# Verbose output
python main.py backtest -p EURUSD -v
```

**در Python:**
```python
from trading_ai_system import core, data, features, models, strategy, risk

# Initialize
config = core.SystemConfig(symbol="EURUSD")
core.initialize_system(config)

# Backtest logic
# ... (see full documentation)
```

---

### ب. Training Models

```bash
# Train model
python main.py train -m eurusd -d data/train.csv

# With epochs
python main.py train -m eurusd --epochs 200

# With data path
python main.py train -m eurusd -d /path/to/data.csv
```

**در Python:**
```python
from trading_ai_system.models import LGBModel

model = LGBModel("eurusd_model")
model.train(X_train, y_train)

# Save
model.save("models/eurusd.pkl")

# Load
model.load("models/eurusd.pkl")
```

---

### ج. Live Trading

```bash
# Dry Run (بدون پول واقعی)
python main.py live -p EURUSD --dry-run

# With Account ID
python main.py live -p EURUSD -a ACC12345

# Verbose
python main.py live -p EURUSD --dry-run -v
```

**در Python:**
```python
from trading_ai_system import live, strategy, risk

# Connect to broker
broker = live.BrokerConnector(api_key="your_key")
executor = live.OrderExecutor(broker=broker)

# Execute trades
# ... (see full documentation)
```

---

### د. Data Management

```bash
# Fetch data
python main.py data fetch -p EURUSD -s 2023-01-01 -e 2023-12-31

# Validate data
python main.py data validate -f data/eurusd.csv

# Analyze data
python main.py analysis -p EURUSD --type indicators
```

---

### ه. Configuration

```bash
# Show current config
python main.py config show

# Set config value
python main.py config set symbol GBPUSD
python main.py config set commission_per_side 0.002
python main.py config set max_position_size 0.10
```

**در Python:**
```python
from trading_ai_system.core import SystemConfig, set_global_config

config = SystemConfig(
    symbol="EURUSD",
    commission_per_side=0.001,
    max_position_size=0.05,
    max_drawdown=0.20
)

set_global_config(config)
```

---

## 📊 فایل‌های داده‌ای

### Format پشتیبانی شده

```
OHLCV CSV:
timestamp,open,high,low,close,volume
2023-01-01T00:00:00,1.0500,1.0600,1.0400,1.0550,100000
2023-01-01T01:00:00,1.0550,1.0700,1.0500,1.0650,120000
...
```

### Paths

```
data/
├── raw.csv                 # Raw data
├── clean/                  # Cleaned data
├── timestamps/             # Timestamp indexed
├── sessions/               # Session-based
├── timeframes/             # Multi-timeframe
├── train_multi/            # Training sets
└── test_multi/             # Test sets
```

---

## 🔧 Configuration File

**config.json**:
```json
{
  "symbol": "EURUSD",
  "market_type": "spot",
  "commission_per_side": 0.001,
  "max_position_size": 0.05,
  "max_drawdown": 0.20,
  "lookback_periods": {
    "rsi": 14,
    "macd": 26,
    "bb": 20,
    "atr": 14
  },
  "model_type": "lightgbm",
  "validation_method": "walk_forward",
  "paper_trading": true
}
```

**Load:**
```bash
python main.py --config config.json backtest
```

---

## 🧪 Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=trading_ai_system

# Specific file
pytest tests/test_data.py

# Verbose
pytest -v

# Stop on first failure
pytest -x
```

---

## 📋 Project Structure Overview

```
📦 trading_ai_system/
├── 🔷 core/              # System infrastructure
├── 📊 data/              # Data management
├── 🔍 features/          # Technical indicators
├── 🤖 models/            # ML models
├── 📈 strategy/          # Trading strategies
├── ⚠️ risk/              # Risk management
├── 🚀 live/              # Live trading
└── 🛠️ utils/             # Utilities

📁 cli/                   # Command-line interface
📁 tests/                 # Unit tests
🎯 main.py               # Entry point
```

---

## ⚠️ Common Issues & Solutions

### مسئله: Import Error
```
ModuleNotFoundError: No module named 'trading_ai_system'
```

**راه‌حل:**
```bash
pip install -e .
# یا
export PYTHONPATH="${PYTHONPATH}:/path/to/project"
```

---

### مسئله: Data Not Found
```
FileNotFoundError: data/raw.csv not found
```

**راه‌حل:**
```bash
# Create data directory
mkdir -p data

# Fetch data
python main.py data fetch -p EURUSD -s 2023-01-01
```

---

### مسئله: Model Training Failed
```
ModelError: Training data has NaN values
```

**راه‌حل:**
```python
# Validate and clean data
from trading_ai_system.utils import validate_dataframe

is_valid, errors = validate_dataframe(train_data)
if not is_valid:
    print(f"Errors: {errors}")
    # Clean data
    train_data = train_data.dropna()
```

---

## 🚀 Next Steps

### برای مبتدیان:
1. ✅ Read README.md
2. ✅ Run `python main.py` (interactive menu)
3. ✅ Explore `examples/` folder
4. ✅ Run tests: `pytest`

### برای توسعه‌دهندگان:
1. ✅ Read ARCHITECTURE.md
2. ✅ Study core modules
3. ✅ Add Type Hints
4. ✅ Write Unit Tests
5. ✅ Create custom indicators

### برای معامله‌کنان:
1. ✅ Read MAIN_ENTRY_GUIDE.md
2. ✅ Backtest strategy
3. ✅ Paper trade
4. ✅ Monitor performance
5. ✅ Live trade (small)

---

## 📚 مستندات تکمیلی

| فایل | توضیح |
|------|-------|
| README.md | مقدمه و نمای کلی |
| ARCHITECTURE_AND_DIAGRAMS_FA.md | معماری سیستم |
| PROJECT_ANALYSIS_FA.md | تجزیه تفصیلی |
| IMPROVEMENT_RECOMMENDATIONS_FA.md | توصیه‌های بهبود |

---

## 📞 دریافت کمک

```bash
# Show help
python main.py --help

# Command help
python main.py backtest --help
python main.py train --help
python main.py live --help
```

---

**نسخه**: 0.79.0  
**تاریخ**: تیر 1405

