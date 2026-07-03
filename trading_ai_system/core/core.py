"""
Trading AI System - Core Module
Core infrastructure, configuration, state management, and utilities.
"""

import sys
import os
import json
import logging
import hashlib
import warnings
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from contextlib import contextmanager
from contextvars import ContextVar
from threading import Lock

import numpy as np
import pandas as pd

# ═══════════════════════════════════════════════════════════════════════════
# VERSION & METADATA
# ═══════════════════════════════════════════════════════════════════════════

__version__ = "0.79.1"
__author__ = "Trading AI System"
__description__ = "Production-grade algorithmic trading system with ML models"


# ═══════════════════════════════════════════════════════════════════════════
# LOGGING SETUP
# ═══════════════════════════════════════════════════════════════════════════

_log_lock = Lock()


def _get_logger(name: str) -> logging.Logger:
    """Thread-safe logger creation."""
    with _log_lock:
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger


logger = _get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# EXCEPTION CLASSES
# ═══════════════════════════════════════════════════════════════════════════

class TradingSystemError(Exception):
    """Base exception for trading system."""
    pass


class ConfigError(TradingSystemError):
    """Configuration error."""
    pass


class DataError(TradingSystemError):
    """Data validation/processing error."""
    pass


class FeatureError(TradingSystemError):
    """Feature engineering error."""
    pass


class ModelError(TradingSystemError):
    """Model training/prediction error."""
    pass


class ExecutionError(TradingSystemError):
    """Order execution error."""
    pass


class StrategyError(TradingSystemError):
    """Strategy execution error."""
    pass


class RiskError(TradingSystemError):
    """Risk management error."""
    pass


class LiveTradingError(TradingSystemError):
    """Live trading engine error."""
    pass


# ═══════════════════════════════════════════════════════════════════════════
# GLOBAL CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════

HORIZONS: Dict[str, List[str]] = {
    "1m": ["5m", "15m", "1h"],
    "5m": ["15m", "1h", "4h"],
    "15m": ["1h", "4h", "1d"],
    "1h": ["4h", "1d"],
    "4h": ["1d"],
    "1d": [],
}

_CLIP_ZSCORE: List[str] = [
    "rsi_14", "macd", "bb_width", "atr_14", "obv_sma",
    "vpt_signal", "ad_line", "mfi_14", "natr_14", "cci_14"
]

_CLIP_RATIO: List[str] = [
    "close_to_sma", "high_low_ratio", "volume_sma_ratio",
    "roc_ratio", "momentum_ratio"
]

DATA_PATH_CONFIG: Dict[str, str] = {
    "raw_file": os.getenv("RAW_FILE", "data/raw.csv"),
    "clean_dir": os.getenv("CLEAN_DIR", "data/clean"),
    "timestamp_dir": os.getenv("TIMESTAMP_DIR", "data/timestamps"),
    "session_dir": os.getenv("SESSION_DIR", "data/sessions"),
    "timeframe_dir": os.getenv("TIMEFRAME_DIR", "data/timeframes"),
    "train_multi_dir": os.getenv("TRAIN_MULTI_DIR", "data/train_multi"),
    "test_multi_dir": os.getenv("TEST_MULTI_DIR", "data/test_multi"),
}

HORIZON_MIN_BARS: Dict[str, int] = {
    "1min": 5, "5min": 3, "15min": 2, "30min": 2,
    "1h": 1, "4h": 1, "1d": 1, "1w": 1
}

BARS_PER_DAY_BY_TF: Dict[str, float] = {
    "1min": 1440, "5min": 288, "15min": 96, "30min": 48,
    "1h": 24, "4h": 6, "12h": 2, "1d": 1, "1w": 0.2
}

DEFAULT_HORIZONS: List[int] = [1, 2, 4, 8, 12, 24]


# ═══════════════════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════════════════

class MarketType(str, Enum):
    """Market types supported."""
    SPOT = "spot"
    FUTURES = "futures"
    MARGIN = "margin"


class OrderSide(str, Enum):
    """Order direction."""
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    """Order types."""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class TimeFrame(str, Enum):
    """Supported timeframes."""
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"
    W1 = "1w"


# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION CLASSES
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class SystemConfig:
    """System-wide configuration."""
    
    symbol: str = "EURUSD"
    market_type: MarketType = MarketType.SPOT
    base_timeframe: TimeFrame = TimeFrame.H1
    
    # Commission & fees
    commission_per_side: float = 0.001  # 0.1% per side
    slippage_pct: float = 0.0005  # 0.05%
    
    # Risk parameters
    max_position_size: float = 0.05  # 5% of account
    max_drawdown: float = 0.20  # 20%
    position_size_method: str = "kelly"  # kelly, fixed, volatility
    
    # Feature engineering
    lookback_periods: Dict[str, int] = field(default_factory=lambda: {
        "rsi": 14, "macd": 26, "bb": 20, "atr": 14
    })
    
    # Model parameters
    model_type: str = "lightgbm"
    validation_method: str = "walk_forward"
    test_size: float = 0.2
    
    # Logging & output
    log_level: str = "INFO"
    save_features: bool = False
    save_predictions: bool = False
    
    # API/Broker config
    broker: str = "ccxt"  # ccxt, interactive_brokers, etc.
    paper_trading: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        d = asdict(self)
        d['market_type'] = self.market_type.value
        d['base_timeframe'] = self.base_timeframe.value
        return d
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SystemConfig':
        """Create from dictionary."""
        data = data.copy()  # BUG FIX #1: Avoid modifying original dict
        if 'market_type' in data and isinstance(data['market_type'], str):
            data['market_type'] = MarketType(data['market_type'])
        if 'base_timeframe' in data and isinstance(data['base_timeframe'], str):
            data['base_timeframe'] = TimeFrame(data['base_timeframe'])
        return cls(**data)
    
    def validate(self) -> Tuple[bool, List[str]]:
        """Validate configuration values."""
        errors = []
        
        if not self.symbol:
            errors.append("symbol cannot be empty")
        if self.commission_per_side < 0 or self.commission_per_side > 1:
            errors.append("commission_per_side must be between 0 and 1")
        if self.slippage_pct < 0 or self.slippage_pct > 1:
            errors.append("slippage_pct must be between 0 and 1")
        if self.max_position_size <= 0 or self.max_position_size > 1:
            errors.append("max_position_size must be between 0 and 1")
        if self.max_drawdown <= 0 or self.max_drawdown > 1:
            errors.append("max_drawdown must be between 0 and 1")
        if self.test_size <= 0 or self.test_size >= 1:
            errors.append("test_size must be between 0 and 1")
        
        return len(errors) == 0, errors


# ═══════════════════════════════════════════════════════════════════════════
# GLOBAL STATE MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════

class GlobalState:
    """Singleton for global system state."""
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        with self._lock:
            if self._initialized:
                return
                
            self._initialized = True
            self._config = SystemConfig()
            self._feature_registry = {}
            self._models = {}
            self._cache = {}
            self._cache_lock = Lock()
    
    def get_config(self) -> SystemConfig:
        """Get system configuration."""
        return self._config
    
    def set_config(self, config: SystemConfig) -> None:
        """Set system configuration."""
        if not isinstance(config, SystemConfig):
            raise ConfigError("Configuration must be SystemConfig instance")
        
        valid, errors = config.validate()
        if not valid:
            raise ConfigError(f"Invalid configuration: {errors}")
        
        self._config = config
        logger.info(f"Config updated: {config.symbol} {config.market_type}")
    
    def register_feature(self, name: str, metadata: Dict[str, Any]) -> None:
        """Register a feature."""
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Feature name must be non-empty string")
        if not isinstance(metadata, dict):
            raise ValueError("Feature metadata must be dictionary")
        
        self._feature_registry[name] = metadata
    
    def get_feature_registry(self) -> Dict[str, Any]:
        """Get all registered features."""
        return self._feature_registry.copy()
    
    def get_cached(self, key: str) -> Optional[Any]:
        """Get cached value with thread-safe access."""
        with self._cache_lock:
            return self._cache.get(key)
    
    def set_cached(self, key: str, value: Any) -> None:
        """Cache a value with thread-safe access."""
        with self._cache_lock:
            self._cache[key] = value
    
    def clear_cache(self) -> None:
        """Clear cache."""
        with self._cache_lock:
            self._cache.clear()


# ═══════════════════════════════════════════════════════════════════════════
# CONTEXT VARIABLES (for async/thread safety)
# ═══════════════════════════════════════════════════════════════════════════

_config_context: ContextVar[Optional[SystemConfig]] = ContextVar(
    '_config_context', 
    default=None
)
_request_config: ContextVar[Dict[str, Any]] = ContextVar(
    '_request_config', 
    default={}
)


# ═══════════════════════════════════════════════════════════════════════════
# GLOBAL ACCESSORS
# ═══════════════════════════════════════════════════════════════════════════

_global_state = None
_state_lock = Lock()


def get_global_state() -> GlobalState:
    """Get or create global state singleton (thread-safe)."""
    global _global_state
    if _global_state is None:
        with _state_lock:
            if _global_state is None:
                _global_state = GlobalState()
    return _global_state


def get_global_config() -> SystemConfig:
    """Get current system configuration."""
    # Check context first (for request-specific config)
    ctx_config = _config_context.get()
    if ctx_config is not None:
        return ctx_config
    
    # Fall back to global state
    return get_global_state().get_config()


def set_global_config(config: SystemConfig) -> None:
    """Set global system configuration."""
    if not isinstance(config, SystemConfig):
        raise ConfigError("Configuration must be SystemConfig instance")
    get_global_state().set_config(config)


@contextmanager
def config_context(config: SystemConfig):
    """Context manager for temporary config override."""
    if not isinstance(config, SystemConfig):
        raise ConfigError("Configuration must be SystemConfig instance")
    token = _config_context.set(config)
    try:
        yield config
    finally:
        _config_context.reset(token)


def get_request_config() -> Dict[str, Any]:
    """Get request-specific configuration."""
    return _request_config.get().copy()


def set_request_config(config: Dict[str, Any]) -> None:
    """Set request-specific configuration."""
    if not isinstance(config, dict):
        raise ValueError("Request config must be dictionary")
    _request_config.set(config.copy())


def clear_request_config() -> None:
    """Clear request-specific configuration."""
    _request_config.set({})


# ═══════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def get_timestamp_utc() -> datetime:
    """Get current UTC timestamp."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def hash_string(s: str, algorithm: str = "sha256") -> str:
    """Hash a string with specified algorithm."""
    if not isinstance(s, str):
        s = str(s)
    
    if algorithm == "sha256":
        return hashlib.sha256(s.encode()).hexdigest()[:16]
    elif algorithm == "md5":
        return hashlib.md5(s.encode()).hexdigest()[:16]
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")


def ensure_path(path: str) -> Path:
    """Ensure path exists, create if needed."""
    if not isinstance(path, (str, Path)):
        raise ValueError("Path must be string or Path object")
    
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def load_json_config(path: str) -> Dict[str, Any]:
    """Load JSON configuration file safely."""
    try:
        p = Path(path)
        if not p.exists():
            logger.warning(f"Config file not found: {path}")
            return {}
        
        with open(p, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ConfigError(f"Invalid JSON in {path}: {e}")
    except OSError as e:
        raise ConfigError(f"Cannot read config file {path}: {e}")


def save_json_config(data: Dict[str, Any], path: str) -> None:
    """Save configuration to JSON file safely."""
    try:
        p = ensure_path(path)
        with open(p, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
        logger.info(f"Config saved: {path}")
    except (OSError, TypeError) as e:
        raise ConfigError(f"Cannot save config to {path}: {e}")


# ═══════════════════════════════════════════════════════════════════════════
# DATA VALIDATION
# ═══════════════════════════════════════════════════════════════════════════

def validate_dataframe(
    df: Optional[pd.DataFrame],
    required_columns: Optional[List[str]] = None,
    min_rows: int = 10
) -> Tuple[bool, List[str]]:
    """Validate DataFrame integrity."""
    errors = []
    
    if df is None:
        errors.append("DataFrame is None")
        return False, errors
    
    if not isinstance(df, pd.DataFrame):
        errors.append("Object is not a pandas DataFrame")
        return False, errors
    
    if df.empty:
        errors.append("DataFrame is empty")
        return False, errors
    
    if len(df) < min_rows:
        errors.append(f"DataFrame has {len(df)} rows, need at least {min_rows}")
    
    if required_columns:
        missing = [c for c in required_columns if c not in df.columns]
        if missing:
            errors.append(f"Missing columns: {missing}")
    
    # Check for NaN in critical columns
    if required_columns:
        for col in required_columns:
            if col in df.columns and df[col].isna().any():
                errors.append(f"Column '{col}' contains NaN values")
    
    return len(errors) == 0, errors


def validate_numeric_columns(
    df: pd.DataFrame,
    columns: List[str]
) -> Tuple[bool, List[str]]:
    """Validate that columns are numeric."""
    errors = []
    
    if not isinstance(df, pd.DataFrame):
        errors.append("Object is not a pandas DataFrame")
        return False, errors
    
    for col in columns:
        if col not in df.columns:
            errors.append(f"Column not found: {col}")
            continue
        
        if not pd.api.types.is_numeric_dtype(df[col]):
            errors.append(f"Column '{col}' is not numeric")
    
    return len(errors) == 0, errors


# ═══════════════════════════════════════════════════════════════════════════
# FEATURE REGISTRY
# ═══════════════════════════════════════════════════════════════════════════

_feature_registry = {}
_registry_lock = Lock()


def register_feature(
    name: str,
    category: str = "technical",
    requires_shift: bool = False,
    lookback: int = 1
) -> None:
    """Register a feature in global registry."""
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Feature name must be non-empty string")
    if not isinstance(category, str):
        raise ValueError("Category must be string")
    if not isinstance(lookback, int) or lookback < 1:
        raise ValueError("Lookback must be positive integer")
    
    with _registry_lock:
        _feature_registry[name] = {
            "category": category,
            "requires_shift": bool(requires_shift),
            "lookback": lookback,
            "registered_at": get_timestamp_utc()
        }


def get_feature_registry() -> Dict[str, Dict[str, Any]]:
    """Get all registered features (thread-safe)."""
    with _registry_lock:
        return {k: v.copy() for k, v in _feature_registry.items()}


def get_features_by_category(category: str) -> List[str]:
    """Get all features in a category."""
    with _registry_lock:
        return [
            name for name, meta in _feature_registry.items()
            if meta.get("category") == category
        ]


# ═══════════════════════════════════════════════════════════════════════════
# STATUS & HEALTH
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class SystemHealth:
    """System health status."""
    status: str = "healthy"  # healthy, degraded, critical
    uptime_hours: float = 0.0
    last_check: datetime = field(default_factory=get_timestamp_utc)
    error_count: int = 0
    warning_count: int = 0
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "status": self.status,
            "uptime_hours": self.uptime_hours,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "details": self.details.copy()
        }


_system_health = SystemHealth()
_health_lock = Lock()


def get_system_health() -> SystemHealth:
    """Get current system health status."""
    with _health_lock:
        return SystemHealth(
            status=_system_health.status,
            uptime_hours=_system_health.uptime_hours,
            last_check=_system_health.last_check,
            error_count=_system_health.error_count,
            warning_count=_system_health.warning_count,
            details=_system_health.details.copy()
        )


def update_system_health(
    status: str, 
    error: Optional[Exception] = None,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """Update system health status."""
    if status not in ("healthy", "degraded", "critical"):
        raise ValueError(f"Invalid status: {status}")
    
    with _health_lock:
        _system_health.status = status
        _system_health.last_check = get_timestamp_utc()
        
        if error:
            _system_health.error_count += 1
            logger.error(f"System error: {error}")
        
        if details:
            _system_health.details.update(details)
        
        logger.info(f"System health: {status}")


# ═══════════════════════════════════════════════════════════════════════════
# INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════

def initialize_system(config: Optional[SystemConfig] = None) -> None:
    """Initialize system with configuration."""
    if config is None:
        config = SystemConfig()
    
    try:
        set_global_config(config)
        logger.info(f"System initialized: {config.symbol} on {config.market_type}")
        update_system_health("healthy")
    except Exception as e:
        logger.error(f"Failed to initialize system: {e}")
        raise


def shutdown_system() -> None:
    """Gracefully shutdown system."""
    try:
        clear_request_config()
        get_global_state().clear_cache()
        logger.info("System shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# ═══════════════════════════════════════════════════════════════════════════
# UTILITIES FOR TIME & CONVERSION
# ═══════════════════════════════════════════════════════════════════════════

def timeframe_to_minutes(tf: Union[str, TimeFrame]) -> int:
    """Convert timeframe to minutes."""
    if isinstance(tf, TimeFrame):
        tf = tf.value
    
    timeframe_map = {
        "1m": 1, "5m": 5, "15m": 15, "30m": 30,
        "1h": 60, "4h": 240, "1d": 1440, "1w": 10080
    }
    
    if tf not in timeframe_map:
        raise ValueError(f"Unknown timeframe: {tf}")
    
    return timeframe_map[tf]


def minutes_to_timeframe(minutes: int) -> str:
    """Convert minutes to timeframe string."""
    if not isinstance(minutes, int) or minutes < 1:
        raise ValueError("Minutes must be positive integer")
    
    minutes_map = {
        1: "1m", 5: "5m", 15: "15m", 30: "30m",
        60: "1h", 240: "4h", 1440: "1d", 10080: "1w"
    }
    
    if minutes not in minutes_map:
        raise ValueError(f"No timeframe for {minutes} minutes")
    
    return minutes_map[minutes]


# ═══════════════════════════════════════════════════════════════════════════
# EXPORTS
# ═══════════════════════════════════════════════════════════════════════════

__all__ = [
    # Enums
    'MarketType', 'OrderSide', 'OrderType', 'TimeFrame',
    
    # Classes
    'SystemConfig', 'GlobalState', 'SystemHealth',
    
    # Exceptions
    'TradingSystemError', 'ConfigError', 'DataError', 'FeatureError',
    'ModelError', 'ExecutionError', 'StrategyError', 'RiskError', 'LiveTradingError',
    
    # Functions
    'get_global_state', 'get_global_config', 'set_global_config',
    'config_context', 'get_request_config', 'set_request_config',
    'clear_request_config', 'initialize_system', 'shutdown_system',
    'get_timestamp_utc', 'hash_string', 'ensure_path',
    'load_json_config', 'save_json_config',
    'validate_dataframe', 'validate_numeric_columns',
    'register_feature', 'get_feature_registry', 'get_features_by_category',
    'get_system_health', 'update_system_health',
    'timeframe_to_minutes', 'minutes_to_timeframe',
    
    # Constants
    'HORIZONS', '_CLIP_ZSCORE', '_CLIP_RATIO', 'DATA_PATH_CONFIG',
    'HORIZON_MIN_BARS', 'BARS_PER_DAY_BY_TF', 'DEFAULT_HORIZONS',
    
    # Logging
    'logger',
]
