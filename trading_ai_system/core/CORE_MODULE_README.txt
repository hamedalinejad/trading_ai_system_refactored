═══════════════════════════════════════════════════════════════════════════
CORE MODULE - trading_ai_system.core
═══════════════════════════════════════════════════════════════════════════

FILE: trading_ai_system/core/__init__.py (or core.py as standalone)
SIZE: 565 lines
SYNTAX: ✓ Valid

PURPOSE:
═════════
Central infrastructure and configuration for the entire trading system.
Single source of truth for:
  • Configuration management
  • Global state
  • Exception classes
  • Constants and enums
  • Utility functions
  • Feature registry


MODULES INCLUDED:
════════════════

1. VERSION & METADATA
   • __version__ = "0.79.0"
   • __author__, __description__

2. LOGGING
   • logger setup with standard format
   • Available to all modules

3. EXCEPTION CLASSES (Hierarchy)
   ├─ TradingSystemError (base)
   ├─ ConfigError
   ├─ DataError
   ├─ FeatureError
   ├─ ModelError
   ├─ ExecutionError
   └─ LiveTradingError

4. GLOBAL CONSTANTS
   • HORIZONS: Dict[timeframe → prediction horizons]
   • _CLIP_ZSCORE: List of columns for z-score clipping
   • _CLIP_RATIO: List of columns for ratio clipping
   • DATA_PATH_CONFIG: Dict of file paths (env-backed)
   • HORIZON_MIN_BARS: Dict of min bars per timeframe
   • BARS_PER_DAY_BY_TF: Dict of bars per day per timeframe
   • DEFAULT_HORIZONS: List[int] = [1, 2, 4, 8, 12, 24]

5. ENUMS
   • MarketType: SPOT, FUTURES, MARGIN
   • OrderSide: BUY, SELL
   • OrderType: MARKET, LIMIT, STOP, STOP_LIMIT
   • TimeFrame: M1, M5, M15, M30, H1, H4, D1, W1

6. CONFIGURATION
   @dataclass SystemConfig:
     - symbol, market_type, base_timeframe
     - commission, slippage, risk parameters
     - lookback_periods, model parameters
     - logging, broker config
     Methods: to_dict(), from_dict()

7. GLOBAL STATE MANAGEMENT
   class GlobalState (Singleton):
     - get_config() / set_config()
     - register_feature() / get_feature_registry()
     - get_cached() / set_cached()

8. CONTEXT VARIABLES (async-safe)
   - _config_context: Request-specific config
   - _request_config: Per-request settings

9. GLOBAL ACCESSORS
   • get_global_state() → GlobalState
   • get_global_config() → SystemConfig
   • set_global_config(config)
   • config_context(config) → Context manager
   • get/set/clear_request_config()

10. UTILITY FUNCTIONS
    • get_timestamp_utc()
    • hash_string(s)
    • ensure_path(path)
    • load_json_config(path)
    • save_json_config(data, path)

11. DATA VALIDATION
    • validate_dataframe(df, required_cols, min_rows)
    • validate_numeric_columns(df, columns)

12. FEATURE REGISTRY
    • register_feature(name, category, requires_shift, lookback)
    • get_feature_registry()
    • get_features_by_category(category)

13. SYSTEM HEALTH
    @dataclass SystemHealth:
      - status, uptime, last_check, error_count, warning_count
    • get_system_health()
    • update_system_health(status, error)

14. INITIALIZATION
    • initialize_system(config)
    • shutdown_system()


USAGE EXAMPLES:
═══════════════

# Import core components
from trading_ai_system.core import (
    SystemConfig, MarketType, get_global_config, initialize_system,
    register_feature, TradingSystemError
)

# Initialize system
config = SystemConfig(
    symbol="EURUSD",
    market_type=MarketType.SPOT,
    commission_per_side=0.001
)
initialize_system(config)

# Get global config (anywhere in codebase)
cfg = get_global_config()
print(f"Trading {cfg.symbol} on {cfg.market_type}")

# Register features
register_feature("rsi_14", category="technical", requires_shift=False)
register_feature("macd", category="technical", requires_shift=False)

# Temporary config override (context manager)
from trading_ai_system.core import config_context
test_config = SystemConfig(symbol="BTCUSD", paper_trading=True)
with config_context(test_config):
    # All code here uses test_config
    cfg = get_global_config()
    assert cfg.symbol == "BTCUSD"
# Back to original config

# Validate data
from trading_ai_system.core import validate_dataframe
valid, errors = validate_dataframe(
    df, 
    required_columns=['timestamp', 'open', 'high', 'low', 'close'],
    min_rows=100
)
if not valid:
    for error in errors:
        print(f"Error: {error}")

# System health monitoring
from trading_ai_system.core import get_system_health, update_system_health
try:
    # Do something
    pass
except Exception as e:
    update_system_health("degraded", error=e)

health = get_system_health()
print(f"Status: {health.status}, Errors: {health.error_count}")

# Load config from file
from trading_ai_system.core import load_json_config, SystemConfig
cfg_dict = load_json_config("configs/trading.json")
config = SystemConfig.from_dict(cfg_dict)


INTEGRATION WITH OTHER MODULES:
════════════════════════════════

data/ module:
  • Uses validate_dataframe() for quality checks
  • Uses DATA_PATH_CONFIG for file paths
  • Uses get_global_config() for symbol/timeframe

features/ module:
  • Uses register_feature() to register features
  • Uses HORIZON_MIN_BARS, BARS_PER_DAY_BY_TF constants
  • Uses get_global_config() for lookback periods

models/ module:
  • Uses SystemConfig.model_type for architecture selection
  • Uses logger for training logs
  • Raises ModelError on failures

strategy/ module:
  • Uses get_global_config() for symbol/position size
  • Uses OrderType, OrderSide enums
  • Uses get_feature_registry() for available features

risk/ module:
  • Uses SystemConfig.max_drawdown, max_position_size
  • Uses get_system_health() for monitoring

live/ module:
  • Uses config_context() for paper trading toggle
  • Uses get_request_config() for per-trade settings
  • Uses ExecutionError, LiveTradingError exceptions


EXTENDING THE CORE:
════════════════════

To add new configuration option:
  1. Add to SystemConfig @dataclass
  2. Provide default value
  3. Update docstring

To add new exception:
  1. Create class inheriting from TradingSystemError
  2. Add to __all__ exports

To add new enum:
  1. Create class inheriting from (str, Enum)
  2. Define members
  3. Add to __all__ exports

To add new utility function:
  1. Define function with type hints
  2. Add docstring
  3. Add to __all__ exports


IMPORTS REQUIRED:
═════════════════

Standard Library:
  sys, os, json, logging, hashlib, warnings, datetime, pathlib,
  typing, dataclasses, enum, contextlib, contextvars

Third-Party:
  numpy, pandas

All other imports are optional per-module.


KEY DESIGN PRINCIPLES:
═══════════════════════

✓ Single Responsibility: Core handles config & state only
✓ No Circular Dependencies: Core imports nothing from other modules
✓ Async-Safe: Uses ContextVar for thread/async safety
✓ Extensible: Easy to add new config, exceptions, constants
✓ Testable: Pure functions, no side effects in utilities
✓ Documented: Every class/function has docstring

═══════════════════════════════════════════════════════════════════════════
