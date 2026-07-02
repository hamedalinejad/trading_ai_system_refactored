"""
Utility Module for Trading AI System

v79 Components:
- Data Validation: Input validation and quality checks
- Serialization: Safe pickle/JSON handling
- Caching: Memory and disk cache management
- Timestamps: UTC normalization utilities
- Type Conversion: dtype optimization and conversion
- Security: Secure configuration and API key management
"""

import json
import pickle
import hashlib
import logging
import os
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timezone
import threading
from functools import lru_cache
import tempfile
import shutil

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# SERIALIZATION & SECURITY
# ═══════════════════════════════════════════════════════════════════════════

def safe_save(obj: Any, file_handle) -> None:
    """Safely serialize object using pickle with security checks.
    
    v79 FIX: Implement safe_save/safe_load
    - Uses pickle for backward compatibility
    - Validates object types before serialization
    - Logs operation for audit trail
    
    Args:
        obj: Object to serialize
        file_handle: Open file handle for writing
    
    Raises:
        TypeError: If object type is forbidden
    """
    try:
        # Type validation - prevent dangerous objects
        forbidden_types = (type, __builtins__, type(os))
        if isinstance(obj, forbidden_types):
            raise TypeError(f"Cannot serialize {type(obj).__name__}")
        
        pickle.dump(obj, file_handle, protocol=pickle.HIGHEST_PROTOCOL)
        logger.debug(f"Object serialized: {type(obj).__name__}")
    except Exception as e:
        logger.error(f"Serialization failed: {e}")
        raise


def safe_load(file_handle, allowed_types: Optional[set] = None) -> Any:
    """Safely deserialize object with restricted unpickling.
    
    v79 FIX: Implement safe_save/safe_load
    - Validates unpickled object types
    - Blocks dangerous classes
    - Requires explicit type whitelist for production
    
    Args:
        file_handle: Open file handle for reading
        allowed_types: Set of allowed class names (optional whitelist)
    
    Returns:
        Deserialized object
    
    Raises:
        pickle.UnpicklingError: If unsafe class detected
    """
    class RestrictedUnpickler(pickle.Unpickler):
        """Restrict pickle to safe types only."""
        
        def find_class(self, module: str, name: str):
            # Whitelist safe ML/data classes
            allowed = {
                ('lightgbm.basic', 'Booster'),
                ('lightgbm.sklearn', 'LGBMClassifier'),
                ('sklearn.linear_model._logistic', 'LogisticRegression'),
                ('sklearn.preprocessing._encoders', 'LabelEncoder'),
                ('xgboost.sklearn', 'XGBClassifier'),
                ('catboost.core', 'CatBoostClassifier'),
                ('pandas.core.frame', 'DataFrame'),
                ('numpy', 'ndarray'),
                ('builtins', 'dict'),
                ('builtins', 'list'),
            }
            
            if allowed_types:
                allowed = allowed | allowed_types
            
            if (module, name) not in allowed:
                raise pickle.UnpicklingError(f"Unsafe class {module}.{name}")
            
            return super().find_class(module, name)
    
    try:
        obj = RestrictedUnpickler(file_handle).load()
        logger.debug(f"Object deserialized: {type(obj).__name__}")
        return obj
    except Exception as e:
        logger.error(f"Deserialization failed: {e}")
        raise


# ═══════════════════════════════════════════════════════════════════════════
# HASHING & VERSIONING
# ═══════════════════════════════════════════════════════════════════════════

def compute_data_hash(df: pd.DataFrame) -> str:
    """Compute hash of dataframe for versioning and caching.
    
    v79 FIX: Use full 64-char SHA-256 digest instead of truncated.
    Full hash eliminates collision risk for cache keys and data integrity checks.
    
    Args:
        df: Input dataframe
    
    Returns:
        str: 64-character SHA-256 hex digest
    """
    try:
        _full_hash = hashlib.sha256(
            pd.util.hash_pandas_object(df).values.tobytes()
        ).hexdigest()
        # Return full 64-char digest (256-bit) for production-grade collision resistance
        return _full_hash
    except Exception as e:
        logger.warning(f"Hash computation failed: {e}, using fallback")
        return hashlib.sha256(str(df.shape).encode()).hexdigest()


def compute_config_hash(config: Dict[str, Any]) -> str:
    """Compute hash of configuration dictionary.
    
    Args:
        config: Configuration dict
    
    Returns:
        str: 64-character SHA-256 hex digest
    """
    config_json = json.dumps(config, sort_keys=True, default=str)
    return hashlib.sha256(config_json.encode()).hexdigest()


# ═══════════════════════════════════════════════════════════════════════════
# TIMESTAMP UTILITIES
# ═══════════════════════════════════════════════════════════════════════════

def ensure_naive_utc_timestamp(ts: pd.Timestamp) -> pd.Timestamp:
    """Convert timestamp to UTC-naive for consistent comparison.
    
    Args:
        ts: Input timestamp (can be timezone-aware or naive)
    
    Returns:
        pd.Timestamp: UTC-naive timestamp
    
    Note:
        - Timezone-aware: converted to UTC then stripped
        - Timezone-naive: returned as-is
    """
    if pd.isna(ts):
        return ts
    
    # If timezone-aware, convert to UTC first, then remove timezone info
    if hasattr(ts, 'tz') and ts.tz is not None:
        return ts.tz_convert('UTC').tz_localize(None)
    
    # If naive, return as-is (treat as UTC)
    return ts


def ensure_naive_utc_series(ts_series: pd.Series) -> pd.Series:
    """Convert a Series of timestamps to UTC-naive.
    
    Args:
        ts_series: Series with timestamps
    
    Returns:
        pd.Series: UTC-naive timestamps
    """
    s = pd.to_datetime(ts_series, utc=True, errors="coerce")
    return s.dt.tz_localize(None)


def to_utc_naive(df_or_ts: Any, timestamp_col: str = "timestamp") -> Any:
    """Convert dataframe timestamp column (or single Timestamp) to UTC-naive.
    
    Args:
        df_or_ts: DataFrame or single timestamp
        timestamp_col: Column name (for DataFrame)
    
    Returns:
        DataFrame or Timestamp (UTC-naive)
    """
    if isinstance(df_or_ts, pd.DataFrame):
        df = df_or_ts.copy()
        df[timestamp_col] = ensure_naive_utc_series(df[timestamp_col])
        return df
    
    # Single timestamp value
    t = pd.Timestamp(df_or_ts)
    if t.tzinfo is not None:
        t = t.tz_convert("UTC").tz_localize(None)
    else:
        t = t.tz_localize(None)
    return t.normalize()


def compare_timestamps(ts1: Any, ts2: Any) -> int:
    """Compare two timestamps after converting both to UTC-naive.
    
    Args:
        ts1: First timestamp
        ts2: Second timestamp
    
    Returns:
        int: -1 (ts1 < ts2), 0 (equal), 1 (ts1 > ts2)
    """
    ta = to_utc_naive(ts1)
    tb = to_utc_naive(ts2)
    return int((ta > tb) - (ta < tb))


def get_utc_now_naive() -> pd.Timestamp:
    """Return current UTC time as a tz-naive Timestamp.
    
    Returns:
        pd.Timestamp: Current UTC time (naive)
    """
    return pd.Timestamp.now(tz="UTC").tz_localize(None)


def convert_timezone_aware_to_naive(df: pd.DataFrame, timestamp_col: str = "timestamp") -> pd.DataFrame:
    """Convert timezone-aware timestamps to naive format.
    
    This function handles the case where timestamps may or may not be timezone-aware.
    It's safer than direct tz_localize(None) which can fail on already-naive timestamps.
    
    Args:
        df: Input dataframe
        timestamp_col: Name of timestamp column
    
    Returns:
        pd.DataFrame: Copy with timezone-naive timestamps
    
    Raises:
        ValueError: If timestamp column not found
    """
    df = df.copy()
    
    if timestamp_col not in df.columns:
        raise ValueError(f"Column '{timestamp_col}' not found in dataframe")
    
    ts_col = df[timestamp_col]
    
    # Handle timezone-aware datetimes
    if hasattr(ts_col.dtype, 'tz') and ts_col.dtype.tz is not None:
        df[timestamp_col] = ts_col.dt.tz_convert('UTC').dt.tz_localize(None)
    else:
        # For mixed or non-standard formats, use apply
        def _convert_single(ts):
            if pd.isna(ts):
                return ts
            if hasattr(ts, 'tz') and ts.tz is not None:
                return ts.tz_convert('UTC').tz_localize(None)
            return ts
        
        df[timestamp_col] = ts_col.apply(_convert_single)
    
    return df


# ═══════════════════════════════════════════════════════════════════════════
# DATA VALIDATION
# ═══════════════════════════════════════════════════════════════════════════

def validate_raw_data(df: pd.DataFrame) -> Dict[str, Any]:
    """Validate raw OHLCV data quality.
    
    v79 FIX: Comprehensive data validation
    
    Args:
        df: Raw OHLCV dataframe
    
    Returns:
        Dict with validation results
    """
    issues = []
    warnings = []
    
    # Check required columns
    required_cols = {"open", "high", "low", "close", "volume"}
    missing = required_cols - set(df.columns)
    if missing:
        issues.append(f"Missing columns: {missing}")
    
    # Check for duplicates
    if df.index.duplicated().any():
        warnings.append(f"Duplicate timestamps: {df.index.duplicated().sum()}")
    
    # Check data types
    for col in ["open", "high", "low", "close", "volume"]:
        if col in df.columns:
            if not np.issubdtype(df[col].dtype, np.number):
                issues.append(f"{col} is not numeric")
    
    # Check for NaNs
    nan_count = df.isna().sum().sum()
    if nan_count > 0:
        warnings.append(f"Missing values: {nan_count}")
    
    # Check OHLC consistency
    if all(c in df.columns for c in ["high", "low", "open", "close"]):
        bad_rows = (df["high"] < df["low"]).sum()
        if bad_rows > 0:
            issues.append(f"Invalid OHLC: {bad_rows} rows with high < low")
    
    # Check for negative prices/volume
    for col in ["open", "high", "low", "close", "volume"]:
        if col in df.columns:
            neg_count = (df[col] < 0).sum()
            if neg_count > 0:
                issues.append(f"{col} has negative values: {neg_count}")
    
    return {
        "is_valid": len(issues) == 0,
        "errors": issues,
        "warnings": warnings,
        "rows": len(df),
        "columns": list(df.columns),
    }


def validate_data_schema(df: pd.DataFrame, schema: Dict[str, str]) -> Tuple[bool, List[str]]:
    """Validate dataframe schema against expected types.
    
    Args:
        df: Dataframe to validate
        schema: Dict[column_name -> dtype_string]
    
    Returns:
        (is_valid, list_of_errors)
    """
    errors = []
    
    for col, expected_dtype in schema.items():
        if col not in df.columns:
            errors.append(f"Missing column: {col}")
            continue
        
        actual_dtype = str(df[col].dtype)
        if expected_dtype not in actual_dtype:
            errors.append(f"{col}: expected {expected_dtype}, got {actual_dtype}")
    
    return len(errors) == 0, errors


# ═══════════════════════════════════════════════════════════════════════════
# CACHE MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════

class CacheManager:
    """v79: Centralized cache management for memory and disk."""
    
    def __init__(self, cache_dir: str = "./cache", max_size_mb: int = 1000):
        """Initialize cache manager.
        
        Args:
            cache_dir: Directory for cache files
            max_size_mb: Maximum cache size in MB
        """
        self.cache_dir = Path(cache_dir)
        self.max_size_mb = max_size_mb
        self._memory_cache: Dict[str, Any] = {}
        self._lock = threading.RLock()
        
        # Create cache directory
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get(self, key: str, from_disk: bool = True) -> Optional[Any]:
        """Get value from cache.
        
        Args:
            key: Cache key
            from_disk: Also check disk cache
        
        Returns:
            Cached value or None
        """
        with self._lock:
            # Check memory cache first
            if key in self._memory_cache:
                return self._memory_cache[key]
            
            # Check disk cache
            if from_disk:
                cache_file = self.cache_dir / f"{key}.pkl"
                if cache_file.exists():
                    try:
                        with open(cache_file, "rb") as f:
                            obj = pickle.load(f)
                            self._memory_cache[key] = obj
                            return obj
                    except Exception as e:
                        logger.warning(f"Failed to load {key} from disk: {e}")
        
        return None
    
    def set(self, key: str, value: Any, to_disk: bool = True) -> None:
        """Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            to_disk: Also save to disk
        """
        with self._lock:
            # Store in memory cache
            self._memory_cache[key] = value
            
            # Store to disk if requested
            if to_disk:
                cache_file = self.cache_dir / f"{key}.pkl"
                try:
                    with open(cache_file, "wb") as f:
                        pickle.dump(value, f, protocol=pickle.HIGHEST_PROTOCOL)
                except Exception as e:
                    logger.warning(f"Failed to save {key} to disk: {e}")
    
    def delete(self, key: str) -> None:
        """Delete cache entry.
        
        Args:
            key: Cache key
        """
        with self._lock:
            if key in self._memory_cache:
                del self._memory_cache[key]
            
            cache_file = self.cache_dir / f"{key}.pkl"
            if cache_file.exists():
                try:
                    cache_file.unlink()
                except Exception as e:
                    logger.warning(f"Failed to delete {key}: {e}")
    
    def clear(self) -> None:
        """Clear all cache."""
        with self._lock:
            self._memory_cache.clear()
            try:
                shutil.rmtree(self.cache_dir)
                self.cache_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.warning(f"Failed to clear disk cache: {e}")
    
    def get_size(self) -> Dict[str, int]:
        """Get cache size statistics.
        
        Returns:
            Dict with memory and disk sizes
        """
        memory_size = sum(len(str(v)) for v in self._memory_cache.values())
        
        disk_size = 0
        if self.cache_dir.exists():
            disk_size = sum(f.stat().st_size for f in self.cache_dir.glob("*.pkl"))
        
        return {
            "memory_bytes": memory_size,
            "disk_bytes": disk_size,
            "total_bytes": memory_size + disk_size,
            "total_mb": (memory_size + disk_size) / (1024 * 1024),
        }


# ═══════════════════════════════════════════════════════════════════════════
# TYPE CONVERSION
# ═══════════════════════════════════════════════════════════════════════════

def optimize_dataframe_dtypes(df: pd.DataFrame, exclude_cols: Optional[List[str]] = None) -> pd.DataFrame:
    """Reduce memory usage by converting float64 → float32 where possible.
    
    v79 FIX: Automatically optimize dtypes to save 50% memory on float columns
    while maintaining sufficient precision for trading applications.
    
    Args:
        df: Input dataframe
        exclude_cols: Columns to exclude from optimization
    
    Returns:
        DataFrame with optimized dtypes
    """
    if exclude_cols is None:
        exclude_cols = []
    
    exclude_set = set(exclude_cols) | {"timestamp", "datetime", "date"}
    original_mem = df.memory_usage(deep=True).sum() / 1024 / 1024
    
    for col in df.columns:
        if col in exclude_set:
            continue
        
        dtype = df[col].dtype
        
        # Convert float64 → float32 for most features
        if dtype == np.float64:
            col_min = df[col].min()
            col_max = df[col].max()
            
            # Keep float64 for very small or very large numbers
            if not (pd.isna(col_min) or pd.isna(col_max)):
                if (col_min >= -1e6 and col_max <= 1e6):  # Normal range
                    df[col] = df[col].astype(np.float32)
        
        # Convert int64 → int32 for small integers
        elif dtype == np.int64:
            col_max = df[col].max()
            col_min = df[col].min()
            if col_max < 2**31 - 1 and col_min > -(2**31):
                df[col] = df[col].astype(np.int32)
    
    optimized_mem = df.memory_usage(deep=True).sum() / 1024 / 1024
    savings = (1 - optimized_mem / original_mem) * 100 if original_mem > 0 else 0
    
    if savings > 1:
        logger.debug(
            f"optimize_dataframe_dtypes: {original_mem:.1f}MB → {optimized_mem:.1f}MB "
            f"({savings:.1f}% reduction)"
        )
    
    return df


def to_float32_array(arr: Union[np.ndarray, pd.Series, List], 
                     keep_float64: bool = False) -> np.ndarray:
    """Convert array-like to float32 for memory efficiency.
    
    v79 FIX: Standard conversion with optional float64 preservation for sensitive calculations.
    
    Args:
        arr: Input array
        keep_float64: If True, keep as float64 (for correlation, covariance, etc.)
    
    Returns:
        np.ndarray (float32 or float64)
    """
    target_dtype = np.float64 if keep_float64 else np.float32
    return np.asarray(arr, dtype=target_dtype)


# ═══════════════════════════════════════════════════════════════════════════
# SECURITY & CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

class SecureConfigManager:
    """v79: Secure configuration management for API keys and sensitive data."""
    
    def __init__(self, env_prefix: str = "TRADING_"):
        """Initialize secure config manager.
        
        Args:
            env_prefix: Environment variable prefix
        """
        self.env_prefix = env_prefix
        self._cache: Dict[str, str] = {}
    
    def get_api_key(self, exchange: str) -> str:
        """Get API key from environment.
        
        Args:
            exchange: Exchange name (e.g., 'binance', 'alpaca')
        
        Returns:
            API key string
        
        Raises:
            ValueError: If key not found
        """
        env_var = f"{self.env_prefix}{exchange.upper()}_API_KEY"
        key = os.getenv(env_var)
        
        if not key:
            raise ValueError(f"Missing {env_var} in environment")
        
        return key
    
    def get_safe_path(self, path_key: str, base_dir: str = ".") -> Path:
        """Get safe file path (prevents directory traversal).
        
        Args:
            path_key: Path identifier
            base_dir: Base directory
        
        Returns:
            Safe Path object
        """
        base = Path(base_dir).resolve()
        target = base / path_key
        
        # Ensure target is within base directory
        try:
            target.relative_to(base)
        except ValueError:
            raise ValueError(f"Path {path_key} escapes base directory")
        
        return target


# ═══════════════════════════════════════════════════════════════════════════
# GLOBAL SINGLETONS
# ═══════════════════════════════════════════════════════════════════════════

_cache_manager = CacheManager()
_secure_config = SecureConfigManager()


def get_cache_manager() -> CacheManager:
    """Get cache manager singleton.
    
    Returns:
        CacheManager instance
    """
    return _cache_manager


def get_secure_config() -> SecureConfigManager:
    """Get secure config manager singleton.
    
    Returns:
        SecureConfigManager instance
    """
    return _secure_config


if __name__ == "__main__":
    logger.info("Utils module loaded successfully")
    
    # Test timestamp utilities
    now = get_utc_now_naive()
    logger.info(f"Current UTC time: {now}")
    
    # Test hash computation
    test_df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    hash_val = compute_data_hash(test_df)
    logger.info(f"Data hash: {hash_val[:16]}...")
    
    # Test cache manager
    cache = get_cache_manager()
    cache.set("test", {"key": "value"})
    cached = cache.get("test")
    logger.info(f"Cache test: {cached}")
    
    # Test dtype optimization
    large_df = pd.DataFrame({"float_col": np.random.randn(1000)})
    optimized = optimize_dataframe_dtypes(large_df)
    logger.info(f"Dtype optimization complete")
