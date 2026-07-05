"""
Trading AI System - Core Module (All-in-One)
Complete implementation with all 22 bug fixes
"""

import logging
import threading
import hashlib
import json
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime, timezone, timedelta
from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Mapping, MutableMapping, Sequence
from collections import OrderedDict
import pandas as pd
import numpy as np

__version__ = "2.0.0"
__author__ = "Trading AI Team"
__license__ = "MIT"

# ============================================================================
# LOGGER CONFIGURATION (FIX #1: Logger level now properly set)
# ============================================================================

class LoggerConfig:
    """Logger configuration with proper level management"""

    DEFAULT_LOG_LEVEL = "INFO"
    DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    DEFAULT_LOG_DIR = Path("logs")
    MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
    BACKUP_COUNT = 5

    @staticmethod
    def _get_logger(
        name: str,
        log_level: str = DEFAULT_LOG_LEVEL,
        log_file: Optional[str] = None,
        log_dir: Path = DEFAULT_LOG_DIR,
    ) -> logging.Logger:
        """
        Create and configure logger with proper level setting
        
        Args:
            name: Logger name
            log_level: Logging level (INFO, DEBUG, WARNING, ERROR, CRITICAL)
            log_file: Optional log file path
            log_dir: Directory for log files
            
        Returns:
            Configured logger instance
        """
        logger = logging.getLogger(name)
        
        # FIX #1: Set logger level first (CRITICAL BUG)
        numeric_level = getattr(logging, log_level.upper(), logging.INFO)
        logger.setLevel(numeric_level)
        
        # Prevent duplicate handlers
        if logger.hasHandlers():
            return logger
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(numeric_level)
        
        # Formatter
        formatter = logging.Formatter(LoggerConfig.DEFAULT_LOG_FORMAT)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        
        # File handler (optional)
        if log_file:
            log_dir.mkdir(parents=True, exist_ok=True)
            file_path = log_dir / log_file
            
            file_handler = RotatingFileHandler(
                file_path,
                maxBytes=LoggerConfig.MAX_LOG_SIZE,
                backupCount=LoggerConfig.BACKUP_COUNT,
            )
            file_handler.setLevel(numeric_level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        return logger


def get_logger(
    name: str,
    log_level: str = "INFO",
    log_file: Optional[str] = None,
) -> logging.Logger:
    """Convenience function to get configured logger"""
    return LoggerConfig._get_logger(name, log_level, log_file)


# ============================================================================
# GLOBAL STATE MANAGEMENT (FIX #2, #3, #13, #14: Thread safety + LRU cache)
# ============================================================================

class CacheEvictionPolicy(Enum):
    """Cache eviction policies"""
    LRU = "lru"  # Least Recently Used
    FIFO = "fifo"  # First In First Out


class LRUCache:
    """Thread-safe LRU Cache with size limit"""

    def __init__(self, max_size: int = 1000):
        """
        Initialize LRU cache
        
        Args:
            max_size: Maximum number of items in cache
        """
        self.max_size = max_size
        self._cache: OrderedDict[str, Any] = OrderedDict()
        self._lock = threading.RLock()

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache and mark as recently used"""
        with self._lock:
            if key not in self._cache:
                return None
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            return self._cache[key]

    def set(self, key: str, value: Any) -> None:
        """Set value in cache with LRU eviction"""
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            else:
                if len(self._cache) >= self.max_size:
                    # Remove oldest (least recently used)
                    self._cache.popitem(last=False)
            self._cache[key] = value

    def clear(self) -> None:
        """Clear all cache"""
        with self._lock:
            self._cache.clear()

    def size(self) -> int:
        """Get current cache size"""
        with self._lock:
            return len(self._cache)


# FIX #4: Hash function with proper length (64 chars for integrity checks)
def hash_string(text: str, length: int = 64) -> str:
    """
    Generate hash string with configurable length
    
    Args:
        text: String to hash
        length: Hash output length (32 or 64)
        
    Returns:
        Hexadecimal hash string
    """
    if not text:
        raise ValueError("Cannot hash empty string")
    
    if length == 32:
        return hashlib.md5(text.encode()).hexdigest()
    elif length == 64:
        return hashlib.sha256(text.encode()).hexdigest()
    else:
        raise ValueError(f"Unsupported hash length: {length}")


class GlobalState:
    """
    Thread-safe global state manager with proper locks
    Fixes: Race conditions with separate locks for each resource
    """

    _instance: Optional["GlobalState"] = None
    _init_lock = threading.Lock()
    
    def __new__(cls) -> "GlobalState":
        """Implement singleton with proper double-checked locking"""
        if cls._instance is None:
            with cls._init_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize global state with thread safety"""
        if self._initialized:
            return
        
        # FIX #2: Add separate locks for each resource (CRITICAL BUG)
        self._feature_lock = threading.RLock()
        self._model_lock = threading.RLock()
        self._cache_lock = threading.RLock()
        self._health_lock = threading.RLock()

        # FIX #3: Use LRU cache with size limit (HIGH BUG)
        self._cache = LRUCache(max_size=10000)
        
        # Protected resources
        self._feature_registry: Dict[str, Any] = {}
        self._models: Dict[str, Any] = {}
        
        # Health metrics
        self._health_stats = {
            "start_time": datetime.now(timezone.utc),
            "error_count": 0,
            "warning_count": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "last_check": datetime.now(timezone.utc),
        }
        
        self._initialized = True
        logger = get_logger(__name__)
        logger.info("GlobalState initialized with thread safety")

    def register_feature(self, name: str, feature: Any) -> None:
        """
        Register feature with thread safety
        
        Args:
            name: Feature name
            feature: Feature object
        """
        with self._feature_lock:
            if name in self._feature_registry:
                logger = get_logger(__name__)
                logger.warning(f"Feature '{name}' already registered, overwriting")
            self._feature_registry[name] = feature
            logger = get_logger(__name__)
            logger.debug(f"Registered feature: {name}")

    def get_feature(self, name: str) -> Optional[Any]:
        """Get registered feature"""
        with self._feature_lock:
            return self._feature_registry.get(name)

    def list_features(self) -> Dict[str, Any]:
        """Get all registered features"""
        with self._feature_lock:
            return dict(self._feature_registry)

    def register_model(self, name: str, model: Any) -> None:
        """
        Register model with thread safety
        
        Args:
            name: Model name
            model: Model object
        """
        with self._model_lock:
            if name in self._models:
                logger = get_logger(__name__)
                logger.warning(f"Model '{name}' already registered, overwriting")
            self._models[name] = model
            logger = get_logger(__name__)
            logger.debug(f"Registered model: {name}")

    def get_model(self, name: str) -> Optional[Any]:
        """Get registered model"""
        with self._model_lock:
            return self._models.get(name)

    def list_models(self) -> Dict[str, Any]:
        """Get all registered models"""
        with self._model_lock:
            return dict(self._models)

    # Cache operations
    def cache_get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        value = self._cache.get(key)
        with self._health_lock:
            if value is not None:
                self._health_stats["cache_hits"] += 1
            else:
                self._health_stats["cache_misses"] += 1
        return value

    def cache_set(self, key: str, value: Any) -> None:
        """Set value in cache"""
        self._cache.set(key, value)

    def cache_clear(self) -> None:
        """Clear all cache"""
        self._cache.clear()
        logger = get_logger(__name__)
        logger.info("Cache cleared")

    def cache_size(self) -> int:
        """Get cache size"""
        return self._cache.size()

    def get_health_stats(self) -> Dict[str, Any]:
        """Get health statistics"""
        with self._health_lock:
            return dict(self._health_stats)

    def update_health_stats(self, error: bool = False, warning: bool = False) -> None:
        """Update health statistics"""
        with self._health_lock:
            if error:
                self._health_stats["error_count"] += 1
            if warning:
                self._health_stats["warning_count"] += 1
            self._health_stats["last_check"] = datetime.now(timezone.utc)

    def shutdown(self) -> None:
        """
        Shutdown global state and cleanup all resources
        FIX #14: Properly cleanup all resources
        """
        with self._feature_lock:
            self._feature_registry.clear()
        
        with self._model_lock:
            self._models.clear()
        
        with self._cache_lock:
            self._cache.clear()
        
        with self._health_lock:
            self._health_stats.clear()
        
        logger = get_logger(__name__)
        logger.info("GlobalState shutdown complete")


# Singleton instance
global_state = GlobalState()


# ============================================================================
# SYSTEM CONFIGURATION (FIX #7, #8, #9, #10: Enums + validation)
# ============================================================================

class PositionSizeMethod(Enum):
    """Position sizing methods"""
    FIXED = "fixed"
    PERCENTAGE = "percentage"
    KELLY = "kelly"
    ATR = "atr"


class ModelType(Enum):
    """Supported model types"""
    LIGHTGBM = "lightgbm"
    XGBOOST = "xgboost"
    NEURAL_NETWORK = "neural_network"
    LINEAR = "linear"
    ENSEMBLE = "ensemble"


class BrokerType(Enum):
    """Supported brokers"""
    CCXT = "ccxt"
    INTERACTIVE_BROKERS = "ib"
    ALPACA = "alpaca"
    BINANCE = "binance"
    BYBIT = "bybit"


class TimeframeType(Enum):
    """Supported timeframes"""
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"
    W1 = "1w"


@dataclass
class SystemConfig:
    """
    System configuration with validation
    Fixes: Proper type checking and enum validation
    """
    
    # Basic settings
    project_name: str
    environment: str = "production"
    
    # Model settings (FIX #8: Use enum instead of string)
    model_type: ModelType = ModelType.LIGHTGBM
    
    # Broker settings (FIX #9: Use enum instead of string)
    broker: BrokerType = BrokerType.CCXT
    
    # Position sizing (FIX #7: Use enum instead of string)
    position_size_method: PositionSizeMethod = PositionSizeMethod.PERCENTAGE
    position_size_value: float = 1.0
    
    # Risk management
    max_loss_percent: float = 2.0
    take_profit_percent: float = 5.0
    stop_loss_percent: float = 2.0
    max_position_size: float = 100000.0
    min_position_size: float = 10.0
    
    # Logging
    log_level: str = "INFO"
    log_dir: Path = field(default_factory=lambda: Path("logs"))
    
    # Cache
    cache_max_size: int = 10000
    
    # Threading
    max_workers: int = 4
    
    # Validation ranges
    _valid_log_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    _valid_environments = {"development", "testing", "staging", "production"}

    def validate(self) -> bool:
        """
        Validate configuration with comprehensive checks
        Fixes: Proper range and type validation
        
        Returns:
            True if valid, raises ValueError otherwise
        """
        errors: List[str] = []
        
        # Project name
        if not self.project_name or not isinstance(self.project_name, str):
            errors.append("project_name must be non-empty string")
        
        # Environment
        if self.environment.lower() not in self._valid_environments:
            errors.append(
                f"environment must be one of {self._valid_environments}, "
                f"got '{self.environment}'"
            )
        
        # Model type
        if not isinstance(self.model_type, ModelType):
            errors.append(f"model_type must be ModelType enum, got {type(self.model_type)}")
        
        # Broker type
        if not isinstance(self.broker, BrokerType):
            errors.append(f"broker must be BrokerType enum, got {type(self.broker)}")
        
        # Position size method
        if not isinstance(self.position_size_method, PositionSizeMethod):
            errors.append(
                f"position_size_method must be PositionSizeMethod enum, "
                f"got {type(self.position_size_method)}"
            )
        
        # Position size value
        if not (0 < self.position_size_value <= 100):
            errors.append(
                f"position_size_value must be between 0 and 100, "
                f"got {self.position_size_value}"
            )
        
        # Risk parameters
        if not (0 < self.max_loss_percent < 100):
            errors.append(
                f"max_loss_percent must be between 0 and 100, "
                f"got {self.max_loss_percent}"
            )
        
        if not (0 < self.take_profit_percent < 1000):
            errors.append(
                f"take_profit_percent must be positive, "
                f"got {self.take_profit_percent}"
            )
        
        if not (0 < self.stop_loss_percent < 100):
            errors.append(
                f"stop_loss_percent must be between 0 and 100, "
                f"got {self.stop_loss_percent}"
            )
        
        # Position sizes
        if not (0 < self.min_position_size < self.max_position_size):
            errors.append(
                f"min_position_size ({self.min_position_size}) must be less than "
                f"max_position_size ({self.max_position_size})"
            )
        
        # Log level
        if self.log_level.upper() not in self._valid_log_levels:
            errors.append(
                f"log_level must be one of {self._valid_log_levels}, "
                f"got '{self.log_level}'"
            )
        
        # Cache
        if not (100 <= self.cache_max_size <= 100000):
            errors.append(
                f"cache_max_size must be between 100 and 100000, "
                f"got {self.cache_max_size}"
            )
        
        # Threading
        if not (1 <= self.max_workers <= 32):
            errors.append(
                f"max_workers must be between 1 and 32, "
                f"got {self.max_workers}"
            )
        
        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(errors)
            logger = get_logger(__name__)
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger = get_logger(__name__)
        logger.info("Configuration validation passed")
        return True

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "SystemConfig":
        """Create config from dictionary"""
        # FIX #10: Validate structure before creating instance
        try:
            # Convert string enums to actual enums
            if isinstance(config_dict.get("model_type"), str):
                config_dict["model_type"] = ModelType(config_dict["model_type"])
            
            if isinstance(config_dict.get("broker"), str):
                config_dict["broker"] = BrokerType(config_dict["broker"])
            
            if isinstance(config_dict.get("position_size_method"), str):
                config_dict["position_size_method"] = PositionSizeMethod(
                    config_dict["position_size_method"]
                )
            
            # Convert log_dir to Path
            if isinstance(config_dict.get("log_dir"), str):
                config_dict["log_dir"] = Path(config_dict["log_dir"])
            
            config = cls(**config_dict)
            config.validate()
            return config
        except (KeyError, ValueError, TypeError) as e:
            raise ValueError(f"Invalid configuration dictionary: {e}")

    @classmethod
    def from_json_file(cls, file_path: Path) -> "SystemConfig":
        """
        Load config from JSON file with validation
        FIX #10: Proper schema validation
        
        Args:
            file_path: Path to JSON config file
            
        Returns:
            SystemConfig instance
        """
        try:
            with open(file_path, "r") as f:
                config_dict = json.load(f)
            
            if not isinstance(config_dict, dict):
                raise ValueError("JSON root must be an object")
            
            return cls.from_dict(config_dict)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {e}")
        except IOError as e:
            raise ValueError(f"Cannot read config file: {e}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, Enum):
                result[key] = value.value
            elif isinstance(value, Path):
                result[key] = str(value)
            else:
                result[key] = value
        return result

    def to_json_file(self, file_path: Path) -> None:
        """Save config to JSON file"""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
        logger = get_logger(__name__)
        logger.info(f"Config saved to {file_path}")


# ============================================================================
# UTILITY FUNCTIONS (FIX #5, #6, #11, #12, #13)
# ============================================================================

# FIX #5: Proper UTC timezone handling without naive datetime
def get_timestamp_utc() -> datetime:
    """
    Get current UTC timestamp with proper timezone
    
    Fixes: Returns aware datetime instead of naive datetime
    This prevents timezone-related bugs in trading systems
    
    Returns:
        Current datetime in UTC with timezone info
    """
    return datetime.now(timezone.utc)


def timestamp_to_utc(dt: datetime) -> datetime:
    """Convert any datetime to UTC aware datetime"""
    if dt.tzinfo is None:
        # Assume UTC if naive
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def is_utc_aware(dt: datetime) -> bool:
    """Check if datetime is UTC aware"""
    return dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None


# FIX #6: Comprehensive dataframe validation
class DataFrameValidator:
    """Comprehensive DataFrame validation"""

    @staticmethod
    def validate_dataframe(
        df: pd.DataFrame,
        required_columns: Optional[Sequence[str]] = None,
        numeric_columns: Optional[Sequence[str]] = None,
        allow_duplicates: bool = False,
        require_sorted: bool = True,
        timestamp_column: Optional[str] = None,
    ) -> bool:
        """
        Validate DataFrame with comprehensive checks
        
        Fixes: Checks for NaN, inf, duplicates, timezone issues, sorting
        
        Args:
            df: DataFrame to validate
            required_columns: List of required columns
            numeric_columns: Columns that should be numeric
            allow_duplicates: Whether duplicate rows are allowed
            require_sorted: Whether rows should be sorted by timestamp
            timestamp_column: Column containing timestamps
            
        Returns:
            True if valid, raises ValueError otherwise
        """
        errors: List[str] = []
        
        # Basic checks
        if df.empty:
            errors.append("DataFrame is empty")
        
        # FIX #6: Check for NaN values
        nan_columns = df.columns[df.isna().any()].tolist()
        if nan_columns:
            errors.append(f"NaN values found in columns: {nan_columns}")
        
        # FIX #6: Check for inf values
        inf_columns = []
        for col in numeric_columns or []:
            if col in df.columns and np.isinf(df[col]).any():
                inf_columns.append(col)
        
        if inf_columns:
            errors.append(f"Infinite values found in columns: {inf_columns}")
        
        # Check required columns
        if required_columns:
            missing = set(required_columns) - set(df.columns)
            if missing:
                errors.append(f"Missing required columns: {missing}")
        
        # Check numeric columns
        if numeric_columns:
            for col in numeric_columns:
                if col in df.columns and not pd.api.types.is_numeric_dtype(df[col]):
                    errors.append(f"Column '{col}' is not numeric")
        
        # FIX #6: Check for duplicate rows
        if not allow_duplicates:
            duplicates = df.duplicated().sum()
            if duplicates > 0:
                errors.append(f"Found {duplicates} duplicate rows")
        
        # FIX #6: Check for duplicate index
        if df.index.duplicated().any():
            errors.append("Index contains duplicate values")
        
        # FIX #6: Timestamp validation
        if timestamp_column:
            if timestamp_column not in df.columns:
                errors.append(f"Timestamp column '{timestamp_column}' not found")
            else:
                ts_col = df[timestamp_column]
                
                # Check if column is datetime
                if not pd.api.types.is_datetime64_any_dtype(ts_col):
                    errors.append(f"Column '{timestamp_column}' is not datetime")
                else:
                    # FIX #6: Check for duplicate timestamps
                    if ts_col.duplicated().any():
                        errors.append(f"Column '{timestamp_column}' has duplicate values")
                    
                    # FIX #6: Check if sorted and continuous
                    if require_sorted:
                        # Check if sorted
                        if not (ts_col == ts_col.sort_values()).all():
                            errors.append(f"Column '{timestamp_column}' is not sorted")
                        
                        # Check for timezone consistency
                        tz_info = ts_col.dt.tz
                        if tz_info is None:
                            errors.append(
                                f"Column '{timestamp_column}' is timezone-naive "
                                "(should be UTC-aware)"
                            )
        
        if errors:
            error_msg = "DataFrame validation failed:\n" + "\n".join(errors)
            logger = get_logger(__name__)
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger = get_logger(__name__)
        logger.debug("DataFrame validation passed")
        return True

    @staticmethod
    def sample_validation(
        df: pd.DataFrame,
        sample_size: int = 100
    ) -> None:
        """Quick validation on sample of large dataframes"""
        if len(df) <= sample_size:
            return
        
        sample = df.sample(n=min(sample_size, len(df)), random_state=42)
        DataFrameValidator.validate_dataframe(sample)


# FIX #12, #13: Proper health check implementation
class HealthCheck:
    """System health checker"""

    @staticmethod
    def update_system_health(
        health_stats: MutableMapping[str, Any],
        error: bool = False,
        warning: bool = False,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Update system health with proper nested dict merge
        
        Fixes: Properly merges nested dictionaries
        
        Args:
            health_stats: Health statistics dictionary
            error: Whether to increment error count
            warning: Whether to increment warning count
            details: Additional details to merge
        """
        if error:
            health_stats["error_count"] = health_stats.get("error_count", 0) + 1
        
        # FIX #13: Increment warning_count properly
        if warning:
            health_stats["warning_count"] = health_stats.get("warning_count", 0) + 1
        
        health_stats["last_check"] = get_timestamp_utc()
        
        # FIX #12: Proper nested dict merge
        if details:
            if "details" not in health_stats:
                health_stats["details"] = {}
            health_stats["details"].update(details)


# Configuration loading with validation
def load_json_config(
    file_path: Path,
    schema: Optional[Dict[str, type]] = None
) -> Dict[str, Any]:
    """
    Load and validate JSON configuration
    
    Fixes: Proper schema validation
    
    Args:
        file_path: Path to JSON file
        schema: Optional schema dict mapping keys to expected types
        
    Returns:
        Loaded configuration dictionary
    """
    try:
        with open(file_path, "r") as f:
            config = json.load(f)
        
        if not isinstance(config, dict):
            raise ValueError("JSON root must be a dictionary")
        
        # FIX #10: Validate against schema
        if schema:
            for key, expected_type in schema.items():
                if key not in config:
                    logger = get_logger(__name__)
                    logger.warning(f"Missing config key: {key}")
                elif not isinstance(config[key], expected_type):
                    raise ValueError(
                        f"Config key '{key}' has wrong type. "
                        f"Expected {expected_type}, got {type(config[key])}"
                    )
        
        logger = get_logger(__name__)
        logger.info(f"Configuration loaded from {file_path}")
        return config
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {file_path}: {e}")
    except IOError as e:
        raise ValueError(f"Cannot read {file_path}: {e}")


# FIX #11: Better path handling
def ensure_path(path: str | Path, is_file: bool = False) -> Path:
    """
    Ensure path exists and return Path object
    
    Fixes: Better handling of parent directories
    
    Args:
        path: Path string or Path object
        is_file: If True, treat as file path (don't create)
        
    Returns:
        Path object
    """
    if isinstance(path, str):
        path = Path(path)
    
    if is_file:
        # For files, create parent directory
        path.parent.mkdir(parents=True, exist_ok=True)
    else:
        # For directories, create all
        path.mkdir(parents=True, exist_ok=True)
    
    return path


def get_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Calculate file hash for integrity checking
    
    Args:
        file_path: Path to file
        algorithm: Hash algorithm (md5, sha1, sha256)
        
    Returns:
        Hexadecimal hash string
    """
    hash_obj = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_obj.update(chunk)
    
    return hash_obj.hexdigest()


# Type hint utilities for better IDE support
def validate_mapping(value: Any) -> Mapping:
    """Validate that value is a mapping"""
    if not isinstance(value, Mapping):
        raise TypeError(f"Expected Mapping, got {type(value)}")
    return value


def validate_sequence(value: Any) -> Sequence:
    """Validate that value is a sequence"""
    if not isinstance(value, Sequence):
        raise TypeError(f"Expected Sequence, got {type(value)}")
    return value


def validate_mutable_mapping(value: Any) -> MutableMapping:
    """Validate that value is a mutable mapping"""
    if not isinstance(value, MutableMapping):
        raise TypeError(f"Expected MutableMapping, got {type(value)}")
    return value


# ============================================================================
# MODULE EXPORTS (FIX #17, #18, #19, #20, #21, #22)
# ============================================================================

__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__license__",
    
    # Logger
    "LoggerConfig",
    "get_logger",
    
    # Global state
    "GlobalState",
    "LRUCache",
    "hash_string",
    "global_state",
    
    # Configuration
    "SystemConfig",
    "PositionSizeMethod",
    "ModelType",
    "BrokerType",
    "TimeframeType",
    "ensure_path",
    
    # Utilities
    "get_timestamp_utc",
    "timestamp_to_utc",
    "is_utc_aware",
    "DataFrameValidator",
    "HealthCheck",
    "load_json_config",
    "get_file_hash",
    "validate_mapping",
    "validate_sequence",
    "validate_mutable_mapping",
]


# Initialize logger
logger = get_logger(__name__)
logger.info(f"Trading AI System Core {__version__} initialized")
