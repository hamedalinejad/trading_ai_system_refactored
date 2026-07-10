"""
Trading AI System - Core Module
Core infrastructure, configuration, state management, and utilities.
"""

import sys
import os
import json
import logging
import hashlib
from datetime import datetime, timezone
from collections import OrderedDict
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Union
from dataclasses import dataclass
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
__license__ = "Proprietary"

# ═══════════════════════════════════════════════════════════════════════════
# LOGGING SETUP (Thread-safe)
# ═══════════════════════════════════════════════════════════════════════════
from dataclasses import dataclass

_log_lock = Lock()
_loggers: Dict[str, logging.Logger] = {}


class JSONFormatter(logging.Formatter):
    """Format logs as JSON for structured logging (ELK-compatible)."""
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.
        
        Args:
            record: LogRecord to format.
        
        Returns:
            JSON string with timestamp, level, name, module, message.
        """
        log_obj = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "message": record.getMessage(),
        }
        if hasattr(record, 'extra') and isinstance(record.extra, dict):
            log_obj.update(record.extra)
        return json.dumps(log_obj, default=str)


@dataclass
class LoggerConfig:
    """Logger configuration with optional file output and JSON formatting.
    
    Attributes:
        level: Logging level (e.g., logging.INFO, logging.DEBUG).
        format: Log message format string (ignored if json_format=True).
        use_file: Whether to write logs to file.
        file_path: Path to log file (required if use_file=True).
        json_format: Whether to use JSON formatting for structured logging.
    """
    level: int = logging.INFO
    format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    use_file: bool = False
    file_path: Optional[str] = None
    json_format: bool = False


def get_logger(name: str, config: Optional[LoggerConfig] = None) -> logging.Logger:
    """Get or create a logger with optional configuration.
    
    Supports both text and JSON formatted output.
    
    Args:
        name: Logger name (usually __name__).
        config: Optional LoggerConfig for custom settings.
    
    Returns:
        Configured logger instance (thread-safe singleton per name).
    """
    with _log_lock:
        if name in _loggers:
            return _loggers[name]
        
        logger_obj = logging.getLogger(name)
        if not logger_obj.handlers:
            level = config.level if config else LoggerConfig.level
            
            handler = logging.StreamHandler(sys.stdout)
            if config and config.json_format:
                formatter = JSONFormatter()
            else:
                fmt = config.format if config else LoggerConfig.format
                formatter = logging.Formatter(fmt)
            handler.setFormatter(formatter)
            logger_obj.addHandler(handler)
            
            if config and config.use_file and config.file_path:
                file_handler = logging.FileHandler(config.file_path)
                file_handler.setFormatter(formatter)
                logger_obj.addHandler(file_handler)
            
            logger_obj.setLevel(level)
        _loggers[name] = logger_obj
        return logger_obj


logger = get_logger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# CUSTOM EXCEPTIONS
# ═══════════════════════════════════════════════════════════════════════════
class TradingSystemError(Exception):
    """Base exception for the trading system."""
    pass


class ConfigError(TradingSystemError):
    """Configuration related errors."""
    pass


class DataError(TradingSystemError):
    """Data validation/processing errors."""
    pass


class FeatureError(TradingSystemError):
    """Feature engineering errors."""
    pass


class ModelError(TradingSystemError):
    """Model training/inference errors."""
    pass


class ExecutionError(TradingSystemError):
    """Order execution errors."""
    pass


class StrategyError(TradingSystemError):
    """Strategy logic errors."""
    pass


class RiskError(TradingSystemError):
    """Risk management errors."""
    pass


class LiveTradingError(TradingSystemError):
    """Live trading engine errors."""
    pass


# ═══════════════════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════════════════
class PositionSizeMethod(Enum):
    KELLY = "kelly"
    FIXED_FRACTION = "fixed_fraction"
    VOLATILITY_TARGET = "vol_target"
    EQUAL_WEIGHT = "equal_weight"


class ModelType(Enum):
    LGBM = "lgbm"
    XGB = "xgboost"
    CATBOOST = "catboost"
    ENSEMBLE = "ensemble"


class BrokerType(Enum):
    BINANCE = "binance"
    MT5 = "mt5"
    PAPER = "paper"


class TimeFrame(Enum):
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"
    W1 = "1w"


TimeframeType = TimeFrame


# ═══════════════════════════════════════════════════════════════════════════
# SYSTEM CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════
@dataclass
class SystemConfig:
    """System configuration with validation.
    
    Attributes:
        symbol: Trading symbol (e.g., 'EURUSD', 'BTC/USDT').
        market_type: Market type (e.g., 'forex', 'crypto', 'stock').
        base_timeframe: Base timeframe (e.g., '1h', '4h', '1d').
        max_position_size: Max position as fraction of capital (0-1).
        commission_per_side: Commission per trade side (0-1).
        slippage_pct: Expected slippage percentage (0-1).
        max_drawdown: Max allowed drawdown (0-1).
        test_size: Test set fraction for validation (0-1).
        random_seed: Seed for reproducibility.
    """
    symbol: str = "EURUSD"
    market_type: str = "forex"
    base_timeframe: str = "1h"
    max_position_size: float = 0.05
    commission_per_side: float = 0.0001
    slippage_pct: float = 0.0001
    max_drawdown: float = 0.20
    test_size: float = 0.2
    random_seed: int = 42

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SystemConfig':
        """Create from dictionary with full validation.
        
        Args:
            data: Configuration dictionary.
        
        Returns:
            Validated SystemConfig instance.
        
        Raises:
            ConfigError: If validation fails.
        """
        data = data.copy()
        if 'market_type' in data and isinstance(data['market_type'], str):
            data['market_type'] = data['market_type'].lower()
        if 'base_timeframe' in data and isinstance(data['base_timeframe'], str):
            data['base_timeframe'] = data['base_timeframe'].lower()
            try:
                TimeFrame(data['base_timeframe'])
            except ValueError:
                raise ConfigError(f"Invalid timeframe: {data['base_timeframe']}. "
                                 f"Must be one of: {[tf.value for tf in TimeFrame]}")
        config = cls(**data)
        valid, errors = config.validate()
        if not valid:
            raise ConfigError(f"Invalid config: {errors}")
        return config

    def validate(self) -> Tuple[bool, List[str]]:
        """Validate configuration values.
        
        Returns:
            Tuple of (is_valid, error_list).
        """
        errors = []
        if not self.symbol or not isinstance(self.symbol, str) or not self.symbol.strip():
            errors.append("symbol must be non-empty string")
        if not self.market_type or not isinstance(self.market_type, str):
            errors.append("market_type must be non-empty string")
        if not 0 < self.max_position_size <= 1:
            errors.append("max_position_size must be in (0, 1]")
        if not 0 <= self.commission_per_side <= 1:
            errors.append("commission_per_side must be in [0, 1]")
        if not 0 <= self.slippage_pct <= 1:
            errors.append("slippage_pct must be in [0, 1]")
        if not 0 < self.max_drawdown <= 1:
            errors.append("max_drawdown must be in (0, 1]")
        if not 0 < self.test_size < 1:
            errors.append("test_size must be in (0, 1)")
        if not isinstance(self.random_seed, int) or self.random_seed < 0:
            errors.append("random_seed must be non-negative integer")
        return len(errors) == 0, errors


# ═══════════════════════════════════════════════════════════════════════════
# GLOBAL STATE (Thread-safe Singleton)
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
        if getattr(self, '_initialized', False):
            return
        self._initialized = True
        self._config: SystemConfig = SystemConfig()
        self._feature_registry: Dict[str, Dict] = {}
        self._models: Dict = {}
        self._cache: Dict = {}
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
        logger.info(f"Config updated: {config.symbol} / {config.market_type}")

    def register_feature(self, name: str, metadata: Dict[str, Any]) -> None:
        """Register a feature."""
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Feature name must be non-empty string")
        self._feature_registry[name] = metadata

    def get_feature_registry(self) -> Dict[str, Dict]:
        """Get all registered features (thread-safe copy)."""
        return self._feature_registry.copy()

    def get_cached(self, key: str) -> Optional[Any]:
        """Get cached value."""
        with self._cache_lock:
            return self._cache.get(key)

    def set_cached(self, key: str, value: Any) -> None:
        """Cache a value."""
        with self._cache_lock:
            self._cache[key] = value

    def clear_cache(self) -> None:
        """Clear cache."""
        with self._cache_lock:
            self._cache.clear()

    def save_state(self, path: Union[str, Path]) -> None:
        """Save global state to file (JSON format for portability).
        
        Persists config and feature registry for recovery on restart.
        
        Args:
            path: Path to save state file.
        
        Raises:
            Exception: If serialization or file write fails.
        """
        import joblib
        state = {
            'config': {
                'symbol': self._config.symbol,
                'market_type': self._config.market_type,
                'base_timeframe': self._config.base_timeframe,
                'max_position_size': self._config.max_position_size,
                'commission_per_side': self._config.commission_per_side,
                'slippage_pct': self._config.slippage_pct,
                'max_drawdown': self._config.max_drawdown,
                'test_size': self._config.test_size,
                'random_seed': self._config.random_seed,
            },
            'feature_registry': self._feature_registry,
        }
        try:
            path = ensure_path(path)
            joblib.dump(state, path)
            logger.info(f"State saved to {path}")
        except Exception as e:
            logger.error(f"Failed to save state to {path}: {e}")
            raise

    def load_state(self, path: Union[str, Path]) -> None:
        """Load global state from file.
        
        Restores config and feature registry.
        
        Args:
            path: Path to state file.
        
        Raises:
            ConfigError: If state is invalid.
        """
        import joblib
        try:
            state = joblib.load(path)
            if 'config' in state:
                self._config = SystemConfig.from_dict(state['config'])
            if 'feature_registry' in state:
                self._feature_registry = state['feature_registry']
            logger.info(f"State loaded from {path}")
        except Exception as e:
            logger.error(f"Failed to load state from {path}: {e}")
            raise ConfigError(f"Invalid state file: {path}") from e


# ═══════════════════════════════════════════════════════════════════════════
# CONTEXT & REQUEST CONFIG
# ═══════════════════════════════════════════════════════════════════════════
_config_context: ContextVar[Optional[SystemConfig]] = ContextVar("_config_context", default=None)
_request_config: ContextVar[Dict[str, Any]] = ContextVar("_request_config", default={})


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
# GLOBAL STATE ACCESSORS
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
    """Get global system configuration."""
    return get_global_state().get_config()


def set_global_config(config: SystemConfig) -> None:
    """Set global system configuration."""
    get_global_state().set_config(config)


# ═══════════════════════════════════════════════════════════════════════════
# INITIALIZATION & SHUTDOWN
# ═══════════════════════════════════════════════════════════════════════════
def initialize_system(config: Optional[SystemConfig] = None) -> None:
    """Initialize the trading system."""
    if config is None:
        config = SystemConfig()
    try:
        set_global_config(config)
        logger.info(f"System initialized: {config.symbol} / {config.market_type}")
    except Exception as e:
        logger.error(f"System initialization failed: {e}")
        raise


def shutdown_system() -> None:
    """Graceful shutdown."""
    try:
        clear_request_config()
        get_global_state().clear_cache()
        logger.info("System shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# ═══════════════════════════════════════════════════════════════════════════
# CACHE & UTILITIES
# ═══════════════════════════════════════════════════════════════════════════
class LRUCache:
    """True LRU Cache with optional TTL (Time-To-Live).
    
    Features:
        - LRU eviction when max_size exceeded
        - Optional TTL: expired items automatically deleted on access
        - Thread-safe with lock protection
    """
    def __init__(self, max_size: int = 128, ttl_seconds: float = 0):
        """Initialize cache.
        
        Args:
            max_size: Maximum number of items (must be >= 1).
            ttl_seconds: Time-to-live in seconds (0 = no expiration).
        """
        if max_size < 1:
            raise ValueError("max_size must be >= 1")
        self.max_size = max_size
        self.ttl = ttl_seconds
        self.cache: OrderedDict[str, Any] = OrderedDict()
        self._timestamps: Dict[str, datetime] = {}
        self.lock = Lock()

    def get(self, key: str) -> Optional[Any]:
        """Get value and move to end (most recently used).
        
        Expired items (if TTL set) are automatically removed.
        
        Args:
            key: Cache key.
        
        Returns:
            Cached value or None if not found/expired.
        """
        with self.lock:
            if key not in self.cache:
                return None
            
            if self.ttl > 0:
                age = (datetime.now(timezone.utc) - self._timestamps[key]).total_seconds()
                if age >= self.ttl:
                    del self.cache[key]
                    del self._timestamps[key]
                    return None
            
            self.cache.move_to_end(key)
            return self.cache[key]

    def set(self, key: str, value: Any) -> None:
        """Set value in cache with timestamp.
        
        Evicts LRU item if cache exceeds max_size.
        
        Args:
            key: Cache key.
            value: Value to cache.
        """
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            self.cache[key] = value
            self._timestamps[key] = datetime.now(timezone.utc)
            
            if len(self.cache) > self.max_size:
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
                del self._timestamps[oldest_key]

    def get_or_set(self, key: str, factory: 'Callable[[], Any]') -> Any:
        """Get value or compute and cache it.
        
        Useful for lazy initialization pattern.
        
        Args:
            key: Cache key.
            factory: Callable that produces value if not cached.
        
        Returns:
            Cached or newly computed value.
        """
        value = self.get(key)
        if value is None:
            value = factory()
            self.set(key, value)
        return value

    def clear(self) -> None:
        """Clear all cache entries."""
        with self.lock:
            self.cache.clear()
            self._timestamps.clear()


def hash_string(text: str, algorithm: str = "sha256") -> str:
    """Hash a string using specified algorithm.
    
    Args:
        text: String to hash.
        algorithm: Hash algorithm ('sha256', 'md5', 'sha512').
    
    Returns:
        Hexadecimal hash.
    
    Raises:
        ValueError: If algorithm is not supported.
    """
    supported = {"sha256", "md5", "sha512"}
    if algorithm not in supported:
        raise ValueError(f"Unsupported algorithm: {algorithm}. Supported: {supported}")
    
    hasher = hashlib.new(algorithm)
    hasher.update(text.encode())
    return hasher.hexdigest()


def get_timestamp_utc() -> str:
    """Get current UTC timestamp in ISO format.
    
    Returns:
        ISO format timestamp string (UTC).
    """
    return datetime.now(timezone.utc).isoformat()


def timestamp_to_utc(ts: Union[str, int, float]) -> datetime:
    """Convert timestamp to UTC datetime.
    
    Args:
        ts: Timestamp as ISO string, Unix timestamp (int/float).
    
    Returns:
        UTC-aware datetime object.
    
    Raises:
        ValueError: If timestamp format is invalid.
    """
    try:
        if isinstance(ts, str):
            return datetime.fromisoformat(ts).astimezone(timezone.utc)
        return datetime.fromtimestamp(float(ts), tz=timezone.utc)
    except (ValueError, TypeError) as e:
        raise DataError(f"Invalid timestamp: {ts}") from e


def is_utc_aware(dt: datetime) -> bool:
    """Check if datetime is UTC-aware.
    
    Args:
        dt: Datetime object to check.
    
    Returns:
        True if datetime has UTC timezone info.
    """
    return dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None


class DataFrameValidator:
    """Validate pandas DataFrames for trading data."""
    
    @staticmethod
    def validate_ohlcv(df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """Validate OHLCV (candlestick) dataframe structure.
        
        Args:
            df: DataFrame to validate.
        
        Returns:
            Tuple of (is_valid, error_list).
        """
        errors = []
        required = ['open', 'high', 'low', 'close', 'volume']
        missing = [col for col in required if col not in df.columns]
        if missing:
            errors.append(f"Missing columns: {missing}")
        for col in required:
            if col in df.columns and not pd.api.types.is_numeric_dtype(df[col]):
                errors.append(f"{col} must be numeric")
            if col in df.columns and df[col].isna().any():
                errors.append(f"{col} contains NaN values")
        return len(errors) == 0, errors

    @staticmethod
    def validate_index_datetime(df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """Validate dataframe has datetime index.
        
        Args:
            df: DataFrame to validate.
        
        Returns:
            Tuple of (is_valid, error_list).
        """
        errors = []
        if not isinstance(df.index, pd.DatetimeIndex):
            errors.append("Index must be DatetimeIndex")
        elif df.index.duplicated().any():
            errors.append("Index has duplicate timestamps")
        return len(errors) == 0, errors


class HealthCheck:
    """System health monitoring with per-component status tracking."""
    def __init__(self):
        """Initialize health check monitor."""
        self.checks: Dict[str, bool] = {}
        self.lock = Lock()

    def set_status(self, component: str, healthy: bool) -> None:
        """Set component health status.
        
        Args:
            component: Component name.
            healthy: Health status (True = healthy, False = unhealthy).
        """
        with self.lock:
            self.checks[component] = healthy

    def get_status(self, component: Optional[str] = None) -> Dict[str, bool]:
        """Get health status.
        
        Args:
            component: Optional specific component name. If None, returns all.
        
        Returns:
            Dictionary of component -> health status.
        """
        with self.lock:
            if component:
                return {component: self.checks.get(component, False)}
            return self.checks.copy()

    def is_healthy(self) -> bool:
        """Check if entire system is healthy.
        
        Returns:
            True if all registered components are healthy, or if no checks registered.
        """
        with self.lock:
            return all(self.checks.values()) if self.checks else True

    def reset(self) -> None:
        """Reset all health checks (clear all components).
        
        Useful after system recovery or restart.
        """
        with self.lock:
            self.checks.clear()


def load_config_from_env(prefix: str = "TRADING_") -> SystemConfig:
    """Load configuration from environment variables.
    
    Supports 12-factor app pattern. Variable names are uppercased field names
    with optional prefix (default 'TRADING_').
    
    Examples:
        TRADING_SYMBOL=EURUSD -> symbol='EURUSD'
        TRADING_MAX_DRAWDOWN=0.15 -> max_drawdown=0.15
    
    Args:
        prefix: Environment variable prefix (default 'TRADING_').
    
    Returns:
        SystemConfig from environment variables or default if empty.
    
    Raises:
        ConfigError: If environment values fail validation.
    """
    data = {}
    for field_name in SystemConfig.__dataclass_fields__.keys():
        env_key = f"{prefix}{field_name.upper()}"
        value = os.getenv(env_key)
        if value is not None:
            field_info = SystemConfig.__dataclass_fields__[field_name]
            field_type = field_info.type
            
            try:
                if field_type is bool or field_type == bool:
                    data[field_name] = value.lower() in ('true', '1', 'yes', 'on')
                elif field_type is int or field_type == int:
                    data[field_name] = int(value)
                elif field_type is float or field_type == float:
                    data[field_name] = float(value)
                else:
                    data[field_name] = value
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to parse {env_key}={value}: {e}")
    
    if data:
        return SystemConfig.from_dict(data)
    return SystemConfig()


def save_json_config(data: Dict[str, Any], path: Union[str, Path]) -> None:
    """Save JSON configuration file.
    
    Args:
        data: Dictionary to save as JSON.
        path: Path to save JSON config file.
    
    Raises:
        ConfigError: If save fails.
    """
    try:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(data, f, cls=JSONConfigEncoder, indent=2)
        logger.info(f"Config saved to {path}")
    except (IOError, TypeError) as e:
        logger.error(f"Failed to save config to {path}: {e}")
        raise ConfigError(f"Cannot save config file: {path}") from e


def load_json_config(path: Union[str, Path]) -> Dict[str, Any]:
    """Load JSON configuration file.
    
    Args:
        path: Path to JSON config file.
    
    Returns:
        Parsed JSON as dictionary.
    
    Raises:
        ConfigError: If file not found or JSON invalid.
    """
    try:
        with open(path, 'r') as f:
            data = json.load(f)
            if not isinstance(data, dict):
                raise ConfigError("Config root must be a dictionary")
            return data
    except FileNotFoundError:
        logger.warning(f"Config file not found: {path}, returning empty dict")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Failed to load config from {path}: {e}")
        raise ConfigError(f"Invalid config file: {path}") from e


def ensure_path(path: Union[str, Path], create_dirs: bool = True) -> Path:
    """Ensure path exists, optionally create parent directories.
    
    Args:
        path: File or directory path.
        create_dirs: Whether to create parent directories.
    
    Returns:
        Path object.
    """
    p = Path(path)
    if create_dirs:
        p.parent.mkdir(parents=True, exist_ok=True)
    return p


def get_file_hash(path: Union[str, Path]) -> str:
    """Get SHA256 hash of file.
    
    Args:
        path: Path to file.
    
    Returns:
        Hexadecimal SHA256 hash.
    
    Raises:
        FileNotFoundError: If file not found.
    """
    sha256 = hashlib.sha256()
    try:
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    except FileNotFoundError as e:
        raise DataError(f"File not found: {path}") from e


def validate_mapping(data: Any, schema: Dict[str, type]) -> Tuple[bool, List[str]]:
    """Validate mapping against schema.
    
    Args:
        data: Dictionary to validate.
        schema: Dict of {key: expected_type}.
    
    Returns:
        Tuple of (is_valid, error_list).
    """
    errors = []
    if not isinstance(data, dict):
        return False, ["Data must be a mapping (dict)"]
    for key, expected_type in schema.items():
        if key not in data:
            errors.append(f"Missing key: {key}")
        elif not isinstance(data[key], expected_type):
            errors.append(f"{key}: expected {expected_type.__name__}, got {type(data[key]).__name__}")
    return len(errors) == 0, errors


def validate_sequence(data: Any, element_type: type) -> Tuple[bool, List[str]]:
    """Validate all elements in sequence are of expected type.
    
    Args:
        data: Sequence to validate.
        element_type: Expected type for all elements.
    
    Returns:
        Tuple of (is_valid, error_list).
    """
    errors = []
    if not isinstance(data, (list, tuple)):
        return False, ["Data must be a sequence (list or tuple)"]
    for i, item in enumerate(data):
        if not isinstance(item, element_type):
            errors.append(f"Element {i}: expected {element_type.__name__}, got {type(item).__name__}")
    return len(errors) == 0, errors


def validate_mutable_mapping(data: Any) -> Tuple[bool, List[str]]:
    """Validate data is a mutable mapping (dict).
    
    Args:
        data: Data to validate.
    
    Returns:
        Tuple of (is_valid, error_list).
    """
    errors = []
    if not isinstance(data, dict):
        errors.append("Data must be a mutable mapping (dict)")
    return len(errors) == 0, errors


def validate_dataframe(df: Any) -> Tuple[bool, List[str]]:
    """Validate a pandas DataFrame.
    
    Args:
        df: Object to validate as DataFrame.
    
    Returns:
        Tuple of (is_valid, error_list).
    """
    errors = []
    
    if df is None:
        errors.append("DataFrame is None")
        return False, errors
    
    if not isinstance(df, pd.DataFrame):
        errors.append(f"Expected DataFrame, got {type(df).__name__}")
        return False, errors
    
    if df.empty:
        errors.append("DataFrame is empty")
    
    if df.isnull().any().any():
        null_cols = df.columns[df.isnull().any()].tolist()
        errors.append(f"DataFrame contains NaN values in columns: {null_cols}")
    
    return len(errors) == 0, errors


def timeframe_to_minutes(timeframe: str) -> int:
    """Convert timeframe string to minutes.
    
    Args:
        timeframe: Timeframe as string (e.g., '1M', '5M', '1H', '4H', '1D', '1W').
    
    Returns:
        Number of minutes.
    
    Raises:
        ValueError: If timeframe format is invalid.
    """
    timeframe = timeframe.upper().strip()
    
    if not timeframe or len(timeframe) < 2:
        raise ValueError(f"Invalid timeframe: {timeframe}")
    
    number_str = timeframe[:-1]
    unit = timeframe[-1]
    
    try:
        number = int(number_str)
    except ValueError:
        raise ValueError(f"Invalid timeframe number: {number_str}")
    
    multipliers = {
        'M': 1,      # Minutes
        'H': 60,     # Hours
        'D': 24*60,  # Days
        'W': 7*24*60,  # Weeks
    }
    
    if unit not in multipliers:
        raise ValueError(f"Invalid timeframe unit: {unit}. Must be M/H/D/W")
    
    return number * multipliers[unit]


def minutes_to_timeframe(minutes: int) -> str:
    """Convert minutes to timeframe string.
    
    Args:
        minutes: Number of minutes.
    
    Returns:
        Timeframe string (e.g., '1M', '1H', '1D', '1W').
    
    Raises:
        ValueError: If minutes is invalid.
    """
    if minutes <= 0:
        raise ValueError(f"Minutes must be positive, got {minutes}")
    
    # Check for weeks
    if minutes % (7 * 24 * 60) == 0:
        return f"{minutes // (7 * 24 * 60)}W"
    
    # Check for days
    if minutes % (24 * 60) == 0:
        return f"{minutes // (24 * 60)}D"
    
    # Check for hours
    if minutes % 60 == 0:
        return f"{minutes // 60}H"
    
    # Minutes
    return f"{minutes}M"


# Thread-safe feature registry
_feature_registry_lock = Lock()
_feature_registry: Dict[str, Any] = {}


def feature_registry(name: Optional[str] = None, register: bool = False, value: Any = None) -> Union[Dict[str, Any], Any, None]:
    """Get/register features in thread-safe registry.
    
    Args:
        name: Feature name (if None, returns entire registry copy).
        register: If True, register the feature.
        value: Value to register (if register=True).
    
    Returns:
        Registry copy, feature value, or None.
    """
    global _feature_registry
    
    with _feature_registry_lock:
        if name is None:
            return _feature_registry.copy()
        
        if register:
            if not isinstance(name, str):
                raise ValueError("Feature name must be string")
            _feature_registry[name] = value
            return value
        
        return _feature_registry.get(name)


def system_health() -> Dict[str, Any]:
    """Get system health status.
    
    Returns:
        Dictionary with health metrics (copy to prevent external modification).
    """
    try:
        config = get_global_config()
        state = get_global_state()
        
        health = {
            'status': 'healthy',
            'timestamp': get_timestamp_utc(),
            'config_loaded': config is not None,
            'state_initialized': state is not None,
            'memory_usage': sys.getsizeof(_feature_registry),
            'features_registered': len(_feature_registry),
        }
        
        return health.copy()
    except Exception as e:
        return {
            'status': 'error',
            'timestamp': get_timestamp_utc(),
            'error': str(e),
        }


class JSONConfigEncoder(json.JSONEncoder):
    """Custom JSON encoder for config objects."""
    
    def default(self, obj: Any) -> Any:
        """Encode special types to JSON-serializable format."""
        if isinstance(obj, (datetime, pd.Timestamp)):
            return obj.isoformat()
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, Enum):
            return obj.value
        if isinstance(obj, Path):
            return str(obj)
        if isinstance(obj, set):
            return list(obj)
        return super().default(obj)


def json_config_encoder(obj: Any) -> str:
    """Encode object to JSON string with custom encoder.
    
    Args:
        obj: Object to encode.
    
    Returns:
        JSON string.
    
    Raises:
        ValueError: If object cannot be encoded.
    """
    try:
        return json.dumps(obj, cls=JSONConfigEncoder, indent=2)
    except (TypeError, ValueError) as e:
        raise ValueError(f"Cannot encode object to JSON: {e}")


# ═══════════════════════════════════════════════════════════════════════════
# EXPORTS
# ═══════════════════════════════════════════════════════════════════════════
__all__ = [
    "__version__", "__author__", "__license__", "logger", "get_logger", "LoggerConfig", "JSONFormatter",
    "TradingSystemError", "ConfigError", "DataError", "FeatureError",
    "ModelError", "ExecutionError", "StrategyError", "RiskError", "LiveTradingError",
    "PositionSizeMethod", "ModelType", "BrokerType", "TimeFrame", "TimeframeType",
    "SystemConfig", "GlobalState", "get_global_state", "get_global_config",
    "set_global_config", "initialize_system", "shutdown_system",
    "config_context", "get_request_config", "set_request_config", "clear_request_config",
    "LRUCache", "hash_string", "get_timestamp_utc", "timestamp_to_utc", "is_utc_aware",
    "DataFrameValidator", "HealthCheck", 
    "save_json_config", "load_json_config", "load_config_from_env", "ensure_path", "get_file_hash",
    "validate_mapping", "validate_sequence", "validate_mutable_mapping",
    "validate_dataframe", "timeframe_to_minutes", "minutes_to_timeframe",
    "feature_registry", "system_health", "json_config_encoder", "JSONConfigEncoder",
]