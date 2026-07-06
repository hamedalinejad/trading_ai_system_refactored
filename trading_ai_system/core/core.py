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
from datetime import datetime, timezone
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
_log_lock = Lock()

def _get_logger(name: str) -> logging.Logger:
    """Thread-safe logger creation."""
    with _log_lock:
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger


logger = _get_logger(__name__)

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


# ═══════════════════════════════════════════════════════════════════════════
# SYSTEM CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════
@dataclass
class SystemConfig:
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
        """Create from dictionary with validation."""
        data = data.copy()
        # Convert string enums if needed
        if 'market_type' in data and isinstance(data['market_type'], str):
            data['market_type'] = data['market_type'].lower()
        if 'base_timeframe' in data and isinstance(data['base_timeframe'], str):
            data['base_timeframe'] = data['base_timeframe'].lower()
        return cls(**data)

    def validate(self) -> Tuple[bool, List[str]]:
        """Validate configuration values."""
        errors = []
        if not self.symbol or not isinstance(self.symbol, str):
            errors.append("symbol cannot be empty")
        if not 0 < self.max_position_size <= 1:
            errors.append("max_position_size must be between 0 and 1")
        if not 0 <= self.commission_per_side <= 1:
            errors.append("commission_per_side must be between 0 and 1")
        if not 0 <= self.slippage_pct <= 1:
            errors.append("slippage_pct must be between 0 and 1")
        if not 0 < self.max_drawdown <= 1:
            errors.append("max_drawdown must be between 0 and 1")
        if not 0 < self.test_size < 1:
            errors.append("test_size must be between 0 and 1")
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
# EXPORTS
# ═══════════════════════════════════════════════════════════════════════════
__all__ = [
    "__version__", "__author__", "logger",
    "TradingSystemError", "ConfigError", "DataError", "FeatureError",
    "ModelError", "ExecutionError", "StrategyError", "RiskError", "LiveTradingError",
    "SystemConfig", "GlobalState", "get_global_state", "get_global_config",
    "set_global_config", "initialize_system", "shutdown_system",
    "config_context", "get_request_config", "set_request_config", "clear_request_config",
]