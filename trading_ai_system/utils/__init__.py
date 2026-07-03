"""
Utils Module - Utilities and helpers

v79.1 Exports:
- Serialization & security
- Hashing & versioning
- Timestamp utilities
- Data validation
- Cache management
- Type conversion
- Configuration management
"""

from .utils import (
    # Serialization
    safe_save,
    safe_load,
    
    # Hashing
    compute_data_hash,
    compute_config_hash,
    
    # Timestamp utilities
    ensure_naive_utc_timestamp,
    ensure_naive_utc_series,
    to_utc_naive,
    compare_timestamps,
    get_utc_now_naive,
    convert_timezone_aware_to_naive,
    
    # Validation
    validate_raw_data,
    validate_data_schema,
    
    # Cache management
    CacheManager,
    
    # Type conversion
    optimize_dataframe_dtypes,
    to_float32_array,
    
    # Security & configuration
    SecureConfigManager,
    
    # Singletons
    get_cache_manager,
    get_secure_config,
)

__all__ = [
    # Serialization
    "safe_save",
    "safe_load",
    
    # Hashing
    "compute_data_hash",
    "compute_config_hash",
    
    # Timestamp utilities
    "ensure_naive_utc_timestamp",
    "ensure_naive_utc_series",
    "to_utc_naive",
    "compare_timestamps",
    "get_utc_now_naive",
    "convert_timezone_aware_to_naive",
    
    # Validation
    "validate_raw_data",
    "validate_data_schema",
    
    # Cache management
    "CacheManager",
    
    # Type conversion
    "optimize_dataframe_dtypes",
    "to_float32_array",
    
    # Security & configuration
    "SecureConfigManager",
    
    # Singletons
    "get_cache_manager",
    "get_secure_config",
]

__version__ = "0.79.1"
