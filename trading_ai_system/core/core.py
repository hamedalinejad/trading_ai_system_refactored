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
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from contextlib import contextmanager
from contextvars import ContextVar

import numpy as np
import pandas as pd

# ═══════════════════════════════════════════════════════════════════════════
# VERSION & METADATA
# ═══════════════════════════════════════════════════════════════════════════

__version__ = "0.79.0"
__author__ = "Trading AI System"
__description__ = "Production-grade algorithmic trading system with ML models"


# ═══════════════════════════════════════════════════════════════════════════
# LOGGING SETUP
# ═══════════════════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


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
        if 'market_type' in data and isinstance(data['market_type'], str):
            data['market_type'] = MarketType(data['market_type'])
        if 'base_timeframe' in data and isinstance(data['base_timeframe'], str):
            data['base_timeframe'] = TimeFrame(data['base_timeframe'])
        return cls(**data)


# ═══════════════════════════════════════════════════════════════════════════
# GLOBAL STATE MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════

class GlobalState:
    """Singleton for global system state."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._config = SystemConfig()
        self._feature_registry = {}
        self._models = {}
        self._cache = {}
    
    def get_config(self) -> SystemConfig:
        """Get system configuration."""
        return self._config
    
    def set_config(self, config: SystemConfig) -> None:
        """Set system configuration."""
        self._config = config
        logger.info(f"Config updated: {config.symbol} {config.market_type}")
    
    def register_feature(self, name: str, metadata: Dict[str, Any]) -> None:
        """Register a feature."""
        self._feature_registry[name] = metadata
    
    def get_feature_registry(self) -> Dict[str, Any]:
        """Get all registered features."""
        return self._feature_registry
    
    def get_cached(self, key: str) -> Optional[Any]:
        """Get cached value."""
        return self._cache.get(key)
    
    def set_cached(self, key: str, value: Any) -> None:
        """Cache a value."""
        self._cache[key] = value
    
    def clear_cache(self) -> None:
        """Clear cache."""
        self._cache.clear()


# ═══════════════════════════════════════════════════════════════════════════
# CONTEXT VARIABLES (for async/thread safety)
# ═══════════════════════════════════════════════════════════════════════════

_config_context: ContextVar[Optional[SystemConfig]] = ContextVar(
    "config_context", default=None
)
_request_config: ContextVar[Dict[str, Any]] = ContextVar(
    "request_config", default={}
)


# ═══════════════════════════════════════════════════════════════════════════
# GLOBAL ACCESSORS
# ═══════════════════════════════════════════════════════════════════════════

_global_state = None


def get_global_state() -> GlobalState:
    """Get or create global state singleton."""
    global _global_state
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
    get_global_state().set_config(config)


@contextmanager
def config_context(config: SystemConfig):
    """Context manager for temporary config override."""
    token = _config_context.set(config)
    try:
        yield config
    finally:
        _config_context.reset(token)


def get_request_config() -> Dict[str, Any]:
    """Get request-specific configuration."""
    return _request_config.get()


def set_request_config(config: Dict[str, Any]) -> None:
    """Set request-specific configuration."""
    _request_config.set(config)


def clear_request_config() -> None:
    """Clear request-specific configuration."""
    _request_config.set({})


# ═══════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def get_timestamp_utc() -> datetime:
    """Get current UTC timestamp."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def hash_string(s: str) -> str:
    """Hash a string (SHA256)."""
    return hashlib.sha256(s.encode()).hexdigest()[:16]


def ensure_path(path: str) -> Path:
    """Ensure path exists, create if needed."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def load_json_config(path: str) -> Dict[str, Any]:
    """Load JSON configuration file."""
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"Config file not found: {path}")
        return {}
    except json.JSONDecodeError as e:
        raise ConfigError(f"Invalid JSON in {path}: {e}")


def save_json_config(data: Dict[str, Any], path: str) -> None:
    """Save configuration to JSON file."""
    ensure_path(path)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    logger.info(f"Config saved: {path}")


# ═══════════════════════════════════════════════════════════════════════════
# DATA VALIDATION
# ═══════════════════════════════════════════════════════════════════════════

def validate_dataframe(
    df: pd.DataFrame,
    required_columns: List[str] = None,
    min_rows: int = 10
) -> Tuple[bool, List[str]]:
    """Validate DataFrame integrity."""
    errors = []
    
    if df is None or df.empty:
        errors.append("DataFrame is empty")
        return False, errors
    
    if len(df) < min_rows:
        errors.append(f"DataFrame has {len(df)} rows, need {min_rows}")
    
    if required_columns:
        missing = [c for c in required_columns if c not in df.columns]
        if missing:
            errors.append(f"Missing columns: {missing}")
    
    return len(errors) == 0, errors


def validate_numeric_columns(
    df: pd.DataFrame,
    columns: List[str]
) -> Tuple[bool, List[str]]:
    """Validate that columns are numeric."""
    errors = []
    
    for col in columns:
        if col not in df.columns:
            errors.append(f"Column not found: {col}")
            continue
        
        if not pd.api.types.is_numeric_dtype(df[col]):
            errors.append(f"Column not numeric: {col}")
    
    return len(errors) == 0, errors


# ═══════════════════════════════════════════════════════════════════════════
# FEATURE REGISTRY
# ═══════════════════════════════════════════════════════════════════════════

_feature_registry = {}


def register_feature(
    name: str,
    category: str = "technical",
    requires_shift: bool = False,
    lookback: int = 1
) -> None:
    """Register a feature in global registry."""
    _feature_registry[name] = {
        "category": category,
        "requires_shift": requires_shift,
        "lookback": lookback,
        "registered_at": get_timestamp_utc()
    }


def get_feature_registry() -> Dict[str, Dict[str, Any]]:
    """Get all registered features."""
    return _feature_registry.copy()


def get_features_by_category(category: str) -> List[str]:
    """Get all features in a category."""
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
            "last_check": self.last_check.isoformat(),
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "details": self.details
        }


_system_health = SystemHealth()


def get_system_health() -> SystemHealth:
    """Get current system health status."""
    return _system_health


def update_system_health(status: str, error: Optional[Exception] = None) -> None:
    """Update system health status."""
    _system_health.status = status
    _system_health.last_check = get_timestamp_utc()
    
    if error:
        _system_health.error_count += 1
        logger.error(f"System error: {error}")
    
    logger.info(f"System health: {status}")


# ═══════════════════════════════════════════════════════════════════════════
# INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════

def initialize_system(config: Optional[SystemConfig] = None) -> None:
    """Initialize system with configuration."""
    if config is None:
        config = SystemConfig()
    
    set_global_config(config)
    logger.info(f"System initialized: {config.symbol} on {config.market_type}")
    update_system_health("healthy")


def shutdown_system() -> None:
    """Gracefully shutdown system."""
    clear_request_config()
    get_global_state().clear_cache()
    logger.info("System shutdown complete")


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
    'ModelError', 'ExecutionError', 'LiveTradingError',
    
    # Functions
    'get_global_state', 'get_global_config', 'set_global_config',
    'config_context', 'get_request_config', 'set_request_config',
    'clear_request_config', 'initialize_system', 'shutdown_system',
    'get_timestamp_utc', 'hash_string', 'ensure_path',
    'load_json_config', 'save_json_config',
    'validate_dataframe', 'validate_numeric_columns',
    'register_feature', 'get_feature_registry', 'get_features_by_category',
    'get_system_health', 'update_system_health',
    
    # Constants
    'HORIZONS', '_CLIP_ZSCORE', '_CLIP_RATIO', 'DATA_PATH_CONFIG',
    'HORIZON_MIN_BARS', 'BARS_PER_DAY_BY_TF', 'DEFAULT_HORIZONS',
    
    # Logging
    'logger',
]

