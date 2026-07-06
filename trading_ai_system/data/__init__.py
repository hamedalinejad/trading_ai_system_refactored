"""
Data Module - Data loading, validation, and management (v2.0)

Exports:
- Data fetchers and validators
- OHLCV management
- Data integrity checks
- Resampling and conversion utilities

Key Features:
- Multiple data source support (CSV, Parquet, SQLite)
- Comprehensive OHLCV cleaning
- Advanced data quality validation
- Spike and gap detection
- Timeframe resampling
"""

from trading_ai_system.data.data import (
    # Enums
    DataSource,
    DataFrequency,
    
    # Classes
    DataQualityReport,
    TimeGapReport,
    DataLoader,
    DataSaver,
    
    # Exceptions
    DataError,
    DataLoadError,
    DataValidationError,
    DataCleaningError,
    
    # Utility Functions
    ensure_naive_utc_timestamp,
    ensure_naive_utc_series,
    drop_broker_noise_columns,
    
    # Data Processing
    clean_ohlcv_data,
    validate_data_quality,
    detect_time_gaps,
    detect_spikes,
    resample_ohlcv,
)

__all__ = [
    # Enums
    "DataSource",
    "DataFrequency",
    
    # Classes
    "DataQualityReport",
    "TimeGapReport",
    "DataLoader",
    "DataSaver",
    
    # Exceptions
    "DataError",
    "DataLoadError",
    "DataValidationError",
    "DataCleaningError",
    
    # Utility Functions
    "ensure_naive_utc_timestamp",
    "ensure_naive_utc_series",
    "drop_broker_noise_columns",
    
    # Data Processing
    "clean_ohlcv_data",
    "validate_data_quality",
    "detect_time_gaps",
    "detect_spikes",
    "resample_ohlcv",
]

__version__ = "0.2.0"
