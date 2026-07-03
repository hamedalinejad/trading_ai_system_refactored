"""
Data Module - Data loading, validation, and management

Exports:
- Data fetchers and validators
- OHLCV management
- Data integrity checks
"""

from trading_ai_system.data.data import (
    DataSource, DataFrequency,
    DataQualityReport, TimeGapReport,
    DataLoader, DataSaver,
    DataLoadError, DataValidationError, DataCleaningError,
    ensure_naive_utc_timestamp, ensure_naive_utc_series,
    drop_broker_noise_columns, clean_ohlcv_data,
    validate_data_quality, detect_time_gaps,
)

__all__ = [
    # Enums
    "DataSource", "DataFrequency",
    
    # Classes
    "DataQualityReport", "TimeGapReport", "DataLoader", "DataSaver",
    
    # Exceptions
    "DataLoadError", "DataValidationError", "DataCleaningError",
    
    # Functions
    "ensure_naive_utc_timestamp", "ensure_naive_utc_series",
    "drop_broker_noise_columns", "clean_ohlcv_data",
    "validate_data_quality", "detect_time_gaps",
]
