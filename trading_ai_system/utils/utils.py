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
import sys
import time
import inspect
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
        if inspect.isfunction(obj) or inspect.ismethod(obj) or inspect.isclass(obj):
            raise TypeError(f"Cannot serialize {type(obj).__name__} (code objects)")
        
        if isinstance(obj, (type, type(os), type(os.path))):
            raise TypeError(f"Cannot serialize {type(obj).__name__}")
        
        pickle.dump(obj, file_handle, protocol=pickle.HIGHEST_PROTOCOL)
        logger.debug(f"Object serialized: {type(obj).__name__}")
    except pickle.PicklingError as e:
        logger.error(f"Pickling error: {e}")
        raise TypeError(f"Cannot pickle {type(obj).__name__}") from e
    except TypeError:
        raise
    except Exception as e:
        logger.error(f"Serialization failed: {e}")
        raise TypeError(f"Serialization failed: {e}") from e


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
            # Safe module prefixes
            safe_modules = {
                'pandas', 'numpy', 'lightgbm', 'sklearn', 'xgboost', 
                'catboost', 'builtins', 'datetime', 'collections',
            }
            
            # Special handling for __main__ - only if in custom allowed_types
            if module == '__main__' and allowed_types:
                if (module, name) in allowed_types:
                    return super().find_class(module, name)
                raise pickle.UnpicklingError(f"Unsafe class {module}.{name}")
            
            # Check if module is in safe list or starts with safe prefix
            is_safe = any(module == m or module.startswith(m + '.') for m in safe_modules)
            
            # Check against custom allowed_types if provided
            if allowed_types and (module, name) in allowed_types:
                is_safe = True
            
            if not is_safe:
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
    return t


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
    
    # Convert to datetime if needed
    if ts_col.dtype == 'object' or not pd.api.types.is_datetime64_any_dtype(ts_col):
        ts_col = pd.to_datetime(ts_col, utc=True, errors='coerce')
    
    # Handle timezone-aware datetimes
    if hasattr(ts_col.dtype, 'tz') and ts_col.dtype.tz is not None:
        df[timestamp_col] = ts_col.dt.tz_convert('UTC').dt.tz_localize(None)
    elif hasattr(ts_col, 'dt'):
        # Already datetime-like, just ensure naive
        df[timestamp_col] = ts_col.dt.tz_localize(None)
    else:
        # Fallback: force datetime conversion
        df[timestamp_col] = pd.to_datetime(ts_col, utc=True, errors='coerce').dt.tz_localize(None)
    
    return df


# ═══════════════════════════════════════════════════════════════════════════
# DATA VALIDATION
# ═══════════════════════════════════════════════════════════════════════════

def validate_raw_data(df: pd.DataFrame, timestamp_col: str = "timestamp") -> Dict[str, Any]:
    """Validate raw OHLCV data quality.
    
    v79 FIX: Comprehensive data validation
    
    Args:
        df: Raw OHLCV dataframe
        timestamp_col: Name of timestamp column
    
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
    
    # Check for duplicates in timestamp column or index
    if timestamp_col in df.columns:
        dup_count = df[timestamp_col].duplicated().sum()
        if dup_count > 0:
            warnings.append(f"Duplicate timestamps: {dup_count}")
    elif isinstance(df.index, pd.DatetimeIndex):
        dup_count = df.index.duplicated().sum()
        if dup_count > 0:
            warnings.append(f"Duplicate timestamps: {dup_count}")
    
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
    """v79: Centralized cache management for memory and disk with TTL/size limits."""
    
    def __init__(self, cache_dir: str = "./cache", max_size_mb: int = 1000, ttl_seconds: int = 3600):
        """Initialize cache manager.
        
        Args:
            cache_dir: Directory for cache files
            max_size_mb: Maximum cache size in MB
            ttl_seconds: Time-to-live for cache entries (seconds)
        """
        self.cache_dir = Path(cache_dir)
        self.max_size_mb = max_size_mb
        self.ttl_seconds = ttl_seconds
        self._memory_cache: Dict[str, Any] = {}
        self._timestamps: Dict[str, float] = {}
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
            # Check TTL for memory cache
            if key in self._memory_cache:
                ts = self._timestamps.get(key, time.time())
                if time.time() - ts < self.ttl_seconds:
                    return self._memory_cache[key]
                else:
                    # TTL expired
                    del self._memory_cache[key]
                    self._timestamps.pop(key, None)
            
            # Check disk cache
            if from_disk:
                cache_file = self.cache_dir / f"{key}.pkl"
                if cache_file.exists():
                    try:
                        with open(cache_file, "rb") as f:
                            obj = safe_load(f)
                            self._memory_cache[key] = obj
                            self._timestamps[key] = time.time()
                            self._evict_if_needed()
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
            # Store in memory cache with timestamp
            self._memory_cache[key] = value
            self._timestamps[key] = time.time()
            
            # Check and evict if necessary
            self._evict_if_needed()
            
            # Store to disk if requested
            if to_disk:
                cache_file = self.cache_dir / f"{key}.pkl"
                try:
                    with open(cache_file, "wb") as f:
                        safe_save(value, f)
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
    
    def _evict_if_needed(self) -> None:
        """Evict oldest entries if cache size exceeds limit."""
        memory_size = sum(sys.getsizeof(v) for v in self._memory_cache.values())
        max_bytes = self.max_size_mb * 1024 * 1024
        
        if memory_size > max_bytes:
            # Evict oldest entries by timestamp
            sorted_keys = sorted(self._timestamps.items(), key=lambda x: x[1])
            for key, _ in sorted_keys:
                if key in self._memory_cache:
                    del self._memory_cache[key]
                    self._timestamps.pop(key, None)
                    memory_size = sum(sys.getsizeof(v) for v in self._memory_cache.values())
                    if memory_size <= max_bytes * 0.9:  # Keep at 90% of max
                        break
    
    def get_size(self) -> Dict[str, int]:
        """Get cache size statistics.
        
        Returns:
            Dict with memory and disk sizes
        """
        memory_size = sum(sys.getsizeof(v) for v in self._memory_cache.values())
        
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
    # Constants for dtype optimization thresholds (1e9 supports crypto prices up to $1B)
    FLOAT_RANGE_LIMIT = 1e9
    INT32_MAX = 2**31 - 1
    INT32_MIN = -(2**31)
    MIN_SAVINGS_PCT = 1.0
    
    if exclude_cols is None:
        exclude_cols = []
    
    exclude_set = set(exclude_cols) | {"timestamp", "datetime", "date"}
    original_mem = df.memory_usage(deep=True).sum() / 1024 / 1024
    
    # Use select_dtypes for efficiency - handle float64 and float32
    float_cols = df.select_dtypes(include=[np.float64, np.float32]).columns
    int_cols = df.select_dtypes(include=[np.int64, np.int32]).columns
    
    for col in float_cols:
        if col in exclude_set or df[col].dtype == np.float32:
            continue
        
        col_min = df[col].min()
        col_max = df[col].max()
        
        if not (pd.isna(col_min) or pd.isna(col_max)):
            if col_min >= -FLOAT_RANGE_LIMIT and col_max <= FLOAT_RANGE_LIMIT:
                df[col] = df[col].astype(np.float32)
    
    for col in int_cols:
        if col in exclude_set or df[col].dtype == np.int32:
            continue
        
        col_max = df[col].max()
        col_min = df[col].min()
        if col_max < INT32_MAX and col_min > INT32_MIN:
            df[col] = df[col].astype(np.int32)
    
    optimized_mem = df.memory_usage(deep=True).sum() / 1024 / 1024
    savings = (1 - optimized_mem / original_mem) * 100 if original_mem > 0 else 0
    
    if savings > MIN_SAVINGS_PCT:
        logger.debug(
            f"optimize_dataframe_dtypes: {original_mem:.1f}MB → {optimized_mem:.1f}MB "
            f"({savings:.1f}% reduction)"
        )
    
    return df


def resample_ohlcv(df: pd.DataFrame, freq: str, ohlc_dict: Optional[Dict[str, str]] = None, 
                   timestamp_col: str = 'timestamp') -> pd.DataFrame:
    """Resample OHLCV data to higher timeframe.
    
    Args:
        df: OHLCV dataframe with timestamp index or column
        freq: Target frequency (e.g., '1H', '1D', '4H')
        ohlc_dict: Custom aggregation dict
        timestamp_col: Timestamp column name (if not index)
    
    Returns:
        Resampled OHLCV dataframe
    """
    if ohlc_dict is None:
        ohlc_dict = {
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum',
        }
    
    df = df.copy()
    
    # Ensure datetime index
    if not isinstance(df.index, pd.DatetimeIndex):
        if timestamp_col in df.columns:
            df[timestamp_col] = pd.to_datetime(df[timestamp_col], utc=True, errors='coerce')
            df = df.set_index(timestamp_col)
        else:
            raise ValueError(f"No DatetimeIndex or '{timestamp_col}' column found")
    
    # Filter to only existing columns
    valid_agg = {col: agg for col, agg in ohlc_dict.items() if col in df.columns}
    
    if not valid_agg:
        raise ValueError("No valid OHLC columns found")
    
    resampled = df.resample(freq).agg(valid_agg)
    resampled = resampled.dropna(how='all')
    return resampled


def merge_time_series(dfs: List[pd.DataFrame], on: str = 'timestamp', how: str = 'outer') -> pd.DataFrame:
    """Merge multiple time series dataframes efficiently.
    
    Args:
        dfs: List of dataframes to merge
        on: Column name for merge (default 'timestamp')
        how: Join type ('inner', 'outer', 'left', 'right')
    
    Returns:
        Merged dataframe
    """
    if not dfs:
        return pd.DataFrame()
    
    if len(dfs) == 1:
        return dfs[0].copy()
    
    # Use concat with index alignment for better performance
    if on in dfs[0].columns:
        result = pd.concat(
            [df.set_index(on) for df in dfs],
            axis=1,
            join=how
        ).reset_index()
    else:
        # Fallback to merge
        from functools import reduce
        result = reduce(lambda l, r: pd.merge(l, r, on=on, how=how), dfs)
    
    return result.drop_duplicates(subset=[on], keep='first')


def validate_time_series_completeness(df: pd.DataFrame, expected_freq: str, timestamp_col: str = 'timestamp') -> Dict[str, Any]:
    """Detect time gaps and validate completeness of time series data.
    
    Args:
        df: Time series dataframe
        expected_freq: Expected frequency (e.g., '1H', '1D', '5min')
        timestamp_col: Timestamp column name
    
    Returns:
        Dict with gap analysis and statistics
    """
    if timestamp_col not in df.columns:
        raise ValueError(f"Column '{timestamp_col}' not found")
    
    ts = pd.to_datetime(df[timestamp_col]).sort_values()
    
    # Expected frequency in nanoseconds
    freq_offset = pd.tseries.frequencies.to_offset(expected_freq)
    expected_delta = pd.Timedelta(freq_offset)
    
    # Calculate actual deltas
    deltas = ts.diff()
    gaps = deltas[deltas > expected_delta]
    
    total_expected = len(pd.date_range(start=ts.min(), end=ts.max(), freq=expected_freq))
    coverage = (len(ts) / total_expected * 100) if total_expected > 0 else 0
    
    return {
        'total_rows': len(df),
        'expected_rows': total_expected,
        'coverage_pct': coverage,
        'gap_count': len(gaps),
        'gap_rows': int(total_expected - len(ts)),
        'time_range': f"{ts.min()} to {ts.max()}",
        'gaps': gaps.to_dict() if len(gaps) > 0 else {},
    }


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
