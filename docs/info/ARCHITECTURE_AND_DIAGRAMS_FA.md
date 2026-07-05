# 🏛️ معماری و نمودار‌های Trading AI System

---

## 📐 معماری سیستم (System Architecture)

### Layered Architecture

```
┌────────────────────────────────────────────────────────────┐
│                     🎯 PRESENTATION LAYER                  │
│          CLI Commands | Interactive Menu | Reports          │
└────────────────────────────────────────────────────────────┘
                              ↑ ↓
┌────────────────────────────────────────────────────────────┐
│                    🔧 APPLICATION LAYER                    │
│     Backtest | Training | Live Trading | Analysis           │
│    (BacktestCommand, TrainCommand, LiveCommand, etc)        │
└────────────────────────────────────────────────────────────┘
                              ↑ ↓
┌────────────────────────────────────────────────────────────┐
│                      💼 BUSINESS LOGIC LAYER               │
│  Strategy | Risk Management | Signal Generation             │
│  (strategy.py | risk.py | core.py logic)                    │
└────────────────────────────────────────────────────────────┘
                              ↑ ↓
┌────────────────────────────────────────────────────────────┐
│                      🔬 DATA PROCESSING LAYER              │
│   Features | Models | Data Validation                       │
│   (features.py | models.py | data.py)                       │
└────────────────────────────────────────────────────────────┘
                              ↑ ↓
┌────────────────────────────────────────────────────────────┐
│                      📊 DATA ACCESS LAYER                  │
│    Data Fetcher | Data Cache | Data Broker Connection      │
│    (DataFetcher, DataCache, BrokerConnector)                │
└────────────────────────────────────────────────────────────┘
```

---

## 🔄 Trading Pipeline (جریان معاملات)

### Complete Trading Workflow

```
START
  ↓
┌─────────────────────────────────────────────────────────┐
│ 1. DATA ACQUISITION (دریافت داده)                        │
├─────────────────────────────────────────────────────────┤
│ • DataFetcher.fetch()                                   │
│ • دریافت OHLCV bars از Broker                           │
│ • TimeFrame: 1m, 5m, 15m, 1h, 4h, 1d                    │
│ • Data Caching برای کارایی                             │
└─────────────────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────────────────┐
│ 2. DATA VALIDATION (اعتبارسنجی داده)                     │
├─────────────────────────────────────────────────────────┤
│ • DataValidator.validate()                              │
│ • بررسی NaN/Inf values                                  │
│ • بررسی Data Integrity                                  │
│ • بررسی OHLC Logic (High >= Open, Close <= High)       │
└─────────────────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────────────────┐
│ 3. FEATURE ENGINEERING (مهندسی ویژگی)                    │
├─────────────────────────────────────────────────────────┤
│ • FeatureEngineer.calculate()                           │
│ • محاسبه 20+ تکنیکال اندیکاتور                          │
│ • Normalization و Standardization                       │
│ • Feature Scaling (Min-Max, Z-Score)                   │
│ • Multi-timeframe features                              │
└─────────────────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────────────────┐
│ 4. MODEL PREDICTION (پیش‌بینی مدل)                       │
├─────────────────────────────────────────────────────────┤
│ • LGBModel.predict()                                    │
│ • مدل LightGBM برای پیش‌بینی جهت                        │
│ • Probability یا Class Output                           │
│ • Ensemble Predictions (چند مدل)                       │
└─────────────────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────────────────┐
│ 5. SIGNAL GENERATION (تولید سیگنال)                      │
├─────────────────────────────────────────────────────────┤
│ • MLStrategy.generate_signals()                         │
│ • تولید سیگنال: +1 (BUY), 0 (HOLD), -1 (SELL)          │
│ • Apply Entry Filters                                   │
│ • Apply Exit Filters                                    │
│ • Confidence Scoring                                    │
└─────────────────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────────────────┐
│ 6. RISK MANAGEMENT (مدیریت ریسک)                         │
├─────────────────────────────────────────────────────────┤
│ • RiskManager.calculate_positions()                     │
│ • Position Sizing (Kelly, Fixed, Volatility)           │
│ • Portfolio Constraints Check                           │
│ • Max Drawdown Check                                    │
│ • Stop Loss & Take Profit Setup                         │
│ • Correlation Check                                     │
└─────────────────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────────────────┐
│ 7. ORDER EXECUTION (اجرای سفارش)                         │
├─────────────────────────────────────────────────────────┤
│ • OrderExecutor.execute()                               │
│ • Market/Limit Order Creation                           │
│ • Order Submission to Broker                            │
│ • Execution Confirmation                                │
│ • Slippage و Commission Calculation                    │
└─────────────────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────────────────┐
│ 8. MONITORING & RECONCILIATION (نظارت و تطبیق)           │
├─────────────────────────────────────────────────────────┤
│ • LiveMonitor.update()                                  │
│ • Track Open Positions                                  │
│ • Monitor P&L                                           │
│ • BrokerReconciler.reconcile()                          │
│ • Verify Orders with Broker                             │
└─────────────────────────────────────────────────────────┘
  ↓
END

⏱️ تکرار هر X دقیقه (بر اساس Timeframe)
```

---

## 🌳 Class Hierarchy (سلسله‌مراتب کلاس‌ها)

### Core Module Hierarchy

```
TradingSystemError (Exception)
├── ConfigError
├── DataError
├── FeatureError
├── ModelError
├── ExecutionError
└── LiveTradingError

SystemConfig (dataclass)
├── symbol: str
├── market_type: MarketType
├── commission_per_side: float
├── max_position_size: float
└── ...

GlobalState (Singleton)
├── _config: SystemConfig
├── _feature_registry: Dict
├── _models: Dict
└── _cache: Dict

SystemHealth (dataclass)
├── status: str
├── uptime_hours: float
├── error_count: int
└── ...
```

### Models Module Hierarchy

```
BaseModel (Abstract)
├── train(data, labels)
├── predict(X)
├── evaluate(X, y)
└── save/load()

LGBModel (extends BaseModel)
├── LightGBM specific training
├── Hyperparameter tuning
├── Cross-validation
└── Feature importance

ModelEnsemble
├── models: List[BaseModel]
├── weights: Dict[str, float]
└── predict(X) → ensemble average

ModelEvaluator
├── calculate_metrics()
├── generate_report()
└── plot_results()
```

### Strategy Module Hierarchy

```
BaseStrategy (Abstract)
├── generate_signals(features_df)
├── validate_signals(signals)
├── get_parameters()
└── set_parameters()

MLStrategy (extends BaseStrategy)
├── model: BaseModel
├── confidence_threshold: float
├── generate_signals()
└── apply_filters()

SignalGenerator
├── entry_filters: List[Callable]
├── exit_filters: List[Callable]
├── generate(predictions)
└── apply_risk_filters()

StrategyPerformance
├── calculate_metrics()
├── track_pnl()
└── calculate_sharpe_ratio()
```

### Risk Module Hierarchy

```
RiskManager
├── position_sizer: PositionSizer
├── constraints: PortfolioConstraints
├── calculate_positions(signals, capital)
└── check_limits()

PositionSizer
├── method: str (kelly/fixed/volatility)
├── calculate_size(...)
└── validate_size()

PortfolioConstraints
├── max_position_size: float
├── max_drawdown: float
├── max_correlation: float
└── check(positions)

RiskMetrics
├── calculate_var()
├── calculate_cvar()
├── calculate_sharpe_ratio()
└── calculate_sortino_ratio()
```

---

## 📊 State Diagram (نمودار حالت‌ها)

### System State Machine

```
                    START
                      ↓
            ┌─────────────────┐
            │ INITIALIZING    │
            └────────┬────────┘
                     ↓
            ┌─────────────────┐
            │ READY           │
            └────┬────────┬───┘
                 │        │
         ┌───────┘        └────────┐
         ↓                         ↓
  ┌─────────────┐        ┌────────────────┐
  │ BACKTESTING │        │ LIVE_TRADING   │
  └─────────────┘        └────────────────┘
         ↓                         ↓
  ┌─────────────┐        ┌────────────────┐
  │ COMPLETED   │        │ RUNNING        │
  └─────────────┘        └─────┬──────────┘
                                │
                          ┌─────┴────────┐
                          ↓              ↓
                    ┌──────────┐    ┌────────┐
                    │ PAUSED   │    │ ERROR  │
                    └────┬─────┘    └────┬───┘
                         │               │
                         └───────┬───────┘
                                 ↓
                          ┌─────────────┐
                          │ SHUTDOWN    │
                          └─────────────┘
```

### Trading State During Session

```
Open Bar
  ↓
CHECK_SIGNALS
  ↓
  ├─→ NO_SIGNAL → Wait
  ├─→ BUY_SIGNAL
  │    ├─→ Check Risk
  │    ├─→ Create Order
  │    └─→ POSITION_OPENED
  │         ├─→ Monitor Position
  │         ├─→ Check Stop Loss
  │         ├─→ Check Take Profit
  │         └─→ Close/Hold
  │
  └─→ SELL_SIGNAL
       ├─→ Check Risk
       ├─→ Create Order
       └─→ POSITION_CLOSED
```

---

## 🔌 Component Interaction Diagram

### High-Level Interaction

```
┌──────────────────────────────────────────────────────────────┐
│                      USER / CLI                              │
│              (main.py → CLI Commands)                        │
└──────────────────────────────────────────────────────────────┘
                           ↑ ↓
┌──────────────────────────────────────────────────────────────┐
│                      CORE                                    │
│     (Config, State, Logger, Health Management)               │
└──────────────────────────────────────────────────────────────┘
                           ↑ ↓
        ┌──────────────────┼──────────────────┐
        ↓                  ↓                  ↓
    ┌────────┐        ┌────────┐        ┌────────┐
    │  DATA  │        │ FEATURES│       │ MODELS │
    │ Fetcher│───────→│Engineer │───────→│ Train  │
    │Validator       │ & Scale │        │Predict │
    │ Cache  │        │         │        │        │
    └────────┘        └────────┘        └────────┘
        ↓                  ↓                  ↓
        └──────────────────┼──────────────────┘
                           ↓
                    ┌──────────────┐
                    │   STRATEGY   │
                    │   Generator  │
                    │   Signals    │
                    └──────┬───────┘
                           ↓
                    ┌──────────────┐
                    │   RISK MGR   │
                    │   Position   │
                    │   Sizing     │
                    └──────┬───────┘
                           ↓
    ┌──────────────────────┼──────────────────────┐
    │                      │                      │
    ↓                      ↓                      ↓
┌─────────┐          ┌──────────┐           ┌────────┐
│  LIVE   │          │BACKTEST  │           │ANALYSIS│
│ Trading │          │ Engine   │           │Reports │
│Executor │          │          │           │        │
└─────────┘          └──────────┘           └────────┘
    ↓
┌─────────────────┐
│  BROKER API     │
│ (Place Orders)  │
└─────────────────┘
```

---

## 🔄 Data Flow Diagram (نمودار جریان داده)

### Detailed Data Flow

```
MARKET DATA (Historical & Real-time)
        ↓
    [DataFetcher]
        ↓ (raw OHLCV)
    [DataValidator]
        ↓ (validated)
    [DataCache]
        ↓ (cached)
    [FeatureEngineer]
        ├─→ RSI, MACD, BB, ATR, EMA, SMA, ...
        ├─→ Normalization
        ├─→ Scaling
        └─→ Feature Validation
        ↓ (features matrix)
    [LGBModel]
        ├─→ Feature Importance
        ├─→ Probability/Class
        └─→ Confidence Score
        ↓ (predictions)
    [SignalGenerator]
        ├─→ Entry Filter
        ├─→ Exit Filter
        ├─→ Confidence Check
        └─→ +1, 0, -1 signals
        ↓ (signals)
    [RiskManager]
        ├─→ Position Size Calc
        ├─→ Portfolio Check
        ├─→ Drawdown Check
        └─→ Risk Score
        ↓ (sized positions)
    [OrderExecutor]
        ├─→ Create Orders
        ├─→ Submit to Broker
        ├─→ Confirm Execution
        └─→ Track Slippage
        ↓
    [Position Monitor]
        ├─→ Track P&L
        ├─→ Monitor Drawdown
        ├─→ Check Exits
        └─→ Reconcile with Broker
        ↓
    [Performance Tracker]
        ├─→ Sharpe Ratio
        ├─→ Max Drawdown
        ├─→ Win Rate
        └─→ Profit Factor
        ↓
    RESULTS & REPORTS
```

---

## 🎯 Module Dependencies (وابستگی‌های مدول‌ها)

### Dependency Graph

```
           main.py
             ↓
    ┌─────────┴─────────┐
    ↓                   ↓
  CLI/          CORE/core.py
commands.py     (centerpiece)
  menu.py           ↑
    │               │
    └───────┬───────┘
            ↓
    ┌───────────────────────┐
    │ core.py provides      │
    │ ├── Config            │
    │ ├── Exceptions        │
    │ ├── Global State      │
    │ └── Enums             │
    └───────────────────────┘
            ↑
    ┌───────┴──────┬───────┬───────┬───────┐
    ↓              ↓       ↓       ↓       ↓
  DATA/         FEATURES/MODELS/ STRATEGY/RISK/
  data.py       features.py models.py strategy.py risk.py
  │             │           │        │          │
  └─────────────┴───────────┴────────┴──────────┘
            ↑
      ┌─────┴─────┐
      ↓           ↓
    LIVE/        UTILS/
    live.py      utils.py
```

### Import Structure

```python
# Core must NOT import from other modules
core/
  └─ No imports from data, features, models, strategy, risk, live

# Service modules CAN import from core
data/
  └─ imports from core/

features/
  └─ imports from core/, utils/

models/
  └─ imports from core/, utils/

strategy/
  └─ imports from core/, features/, models/, utils/

risk/
  └─ imports from core/, models/, utils/

live/
  └─ imports from core/, strategy/, risk/, utils/

CLI/
  └─ imports from all modules
```

---

## 🌐 Configuration Management Flow

```
START
  ↓
┌─────────────────────────────────┐
│ Parse CLI Arguments             │
│ (main.py → argparse)            │
└────────────┬────────────────────┘
             ↓
┌─────────────────────────────────┐
│ Load Config File (if provided)  │
│ (JSON/YAML)                     │
└────────────┬────────────────────┘
             ↓
┌─────────────────────────────────┐
│ Create SystemConfig Object      │
│ (dataclass)                     │
└────────────┬────────────────────┘
             ↓
┌─────────────────────────────────┐
│ Set Global Config               │
│ (GlobalState.set_config)        │
└────────────┬────────────────────┘
             ↓
┌─────────────────────────────────┐
│ Override with Context (if local)│
│ (config_context manager)        │
└────────────┬────────────────────┘
             ↓
┌─────────────────────────────────┐
│ All Components Access Config    │
│ (get_global_config())           │
└────────────────────────────────┘
```

---

## ⚠️ Error Handling Strategy

### Exception Hierarchy & Handling

```
Exception
    │
    └── TradingSystemError (custom base)
        ├── ConfigError
        │   └─ ValueError → wrap in ConfigError
        │
        ├── DataError
        │   ├─ FileNotFoundError → wrap
        │   └─ ValueError → wrap
        │
        ├── FeatureError
        │   ├─ NaN/Inf → wrap
        │   └─ Dimension mismatch → wrap
        │
        ├── ModelError
        │   ├─ Training failure → wrap
        │   └─ Prediction error → wrap
        │
        ├── ExecutionError
        │   ├─ Order submission → wrap
        │   └─ Broker connection → wrap
        │
        └── LiveTradingError
            ├─ Connection loss → wrap
            └─ Order rejection → wrap
```

### Error Recovery Pattern

```
TRY:
  1. Attempt operation
  2. Log info
  
EXCEPT TradingSystemError as e:
  1. Log error with context
  2. Update health status
  3. Recovery attempt
  4. Re-raise if critical
  
EXCEPT Exception as e:
  1. Wrap in TradingSystemError
  2. Log with traceback
  3. Update health status
  4. Re-raise
  
FINALLY:
  1. Cleanup resources
  2. Update state
```

---

## 📈 Performance Optimization Points

### Caching Strategy

```
┌─────────────────────────────┐
│ Level 1: In-Memory Cache    │
│ (GlobalState._cache)        │
│ ├─ TTL: 1-5 minutes         │
│ ├─ Features/Predictions     │
│ └─ Registry Data            │
└─────────────────────────────┘
        ↓
┌─────────────────────────────┐
│ Level 2: File Cache         │
│ (data/cache/)               │
│ ├─ OHLCV Data              │
│ ├─ Calculated Features      │
│ └─ Model Predictions        │
└─────────────────────────────┘
        ↓
┌─────────────────────────────┐
│ Level 3: Broker Cache       │
│ (Live Data)                 │
│ ├─ Position Cache           │
│ ├─ Order Cache              │
│ └─ Balance Cache            │
└─────────────────────────────┘
```

### Parallelization Opportunities

```
1. Multi-Timeframe Analysis
   ├─ Process each TF in parallel
   └─ Merge results

2. Ensemble Predictions
   ├─ Run each model in parallel
   └─ Combine predictions

3. Backtesting
   ├─ Test multiple symbols
   └─ Test parameter combinations

4. Data Validation
   ├─ Validate in chunks
   └─ Parallel processing
```

---

**نسخه**: 0.79.0  
**سطح تفصیل**: معماری سیستم

