═══════════════════════════════════════════════════════════════════════════
DATA MODULE - trading_ai_system.data
═══════════════════════════════════════════════════════════════════════════

FILE: trading_ai_system/data/__init__.py (or data.py as standalone)
SIZE: 609 lines
SYNTAX: ✓ Valid

PURPOSE:
═════════
Data loading, cleaning, validation, and management for the trading system.
Complete pipeline for:
  • Loading data from various sources
  • Data cleaning and outlier removal
  • Quality validation and reporting
  • Time gap detection
  • Data saving in multiple formats


MODULES INCLUDED:
════════════════

1. EXCEPTION CLASSES
   • DataLoadError - Failed to load data
   • DataValidationError - Validation failed
   • DataCleaningError - Cleaning failed

2. ENUMS
   • DataSource: CSV, PARQUET, SQLITE, CCXT, API
   • DataFrequency: M1, M5, M15, M30, H1, H4, D1, W1

3. DATA QUALITY CLASSES
   @dataclass DataQualityReport:
     - passed, row_count, time_span
     - ohlc_missing_pct, volume_stats, price_range
     - quality_warnings, quality_score
   
   @dataclass TimeGapReport:
     - total_gaps, largest_gap, gap_locations
     - has_anomalies, coverage_pct

4. UTILITY FUNCTIONS
   • ensure_naive_utc_timestamp(ts) - Convert to UTC-naive
   • ensure_naive_utc_series(ts_series) - Convert series
   • drop_broker_noise_columns(df) - Remove noise columns

5. DATA CLEANING
   clean_ohlcv_data(df, max_ffill_periods=3, zscore_threshold=5.0)
     Stage 1: Timestamp & structure validation
     Stage 2: Convert & validate OHLC types
     Stage 3: Limited forward-fill (max 3 bars)
     Stage 4: Structural OHLC validation
     Stage 5: Outlier clipping via z-score (5σ)
     Stage 6: Volume cleaning
   
   Returns: Cleaned DataFrame

6. DATA VALIDATION
   validate_data_quality(df, min_rows=100, max_missing_pct=5.0)
     • Checks: row count, time span, missing data
     • Analyzes: price ranges, volume stats, inf values
     • Returns: DataQualityReport with quality_score (0-100)
     
   Quality Score Deductions:
     -20: Insufficient rows
     -15: Data span < 1 hour
     -10: High missing %, inf values, sparse volume
     -5: Other warnings

7. TIME GAP DETECTION
   detect_time_gaps(df, expected_interval_minutes=60, gap_threshold=1.5)
     • Identifies missing candles
     • Classifies as normal/anomaly (> 1.5x expected)
     • Calculates coverage percentage
     • Returns: TimeGapReport

8. DATA LOADING
   class DataLoader:
     • load_csv(path, **kwargs)
     • load_parquet(path, **kwargs)
     • load(path, source=DataSource.CSV, **kwargs)

9. DATA SAVING
   class DataSaver:
     • save_csv(df, path, **kwargs)
     • save_parquet(df, path, **kwargs)
     • save(df, path, fmt="csv", **kwargs)


USAGE EXAMPLES:
═══════════════

# Import data components
from trading_ai_system.data import (
    DataLoader, DataSaver, clean_ohlcv_data,
    validate_data_quality, detect_time_gaps,
    DataSource, DataQualityReport
)

# Load raw data
loader = DataLoader()
df_raw = loader.load("data/eurusd_1h.csv", source=DataSource.CSV)

# Clean data (6-stage pipeline)
df_clean = clean_ohlcv_data(
    df_raw,
    max_ffill_periods=3,        # Max 3-bar forward fill
    zscore_threshold=5.0,        # Clip outliers > 5σ
    volume_min_pct=0.01          # Flag micro-volume
)

# Validate quality
quality = validate_data_quality(
    df_clean,
    min_rows=100,
    max_missing_pct=5.0,
    warn_on_sparse=True
)

print(f"Quality Score: {quality.quality_score:.0f}/100")
print(f"Passed: {quality.passed}")
print(f"Warnings: {quality.quality_warnings}")
print(f"Time Span: {quality.time_span}")
print(f"Missing: {quality.ohlc_missing_pct}")

# Check for time gaps
gaps = detect_time_gaps(
    df_clean,
    expected_interval_minutes=60,
    gap_threshold_multiplier=1.5
)

print(f"Total gaps: {gaps.total_gaps}")
print(f"Has anomalies: {gaps.has_anomalies}")
print(f"Coverage: {gaps.coverage_pct:.1f}%")

if gaps.largest_gap:
    print(f"Largest gap: {gaps.largest_gap['duration_hours']} hours")

# Save cleaned data
saver = DataSaver()
saver.save(df_clean, "data/eurusd_1h_clean.parquet", fmt="parquet")
saver.save(df_clean, "data/eurusd_1h_clean.csv", fmt="csv")

# Full pipeline with error handling
from trading_ai_system.data import DataLoadError, DataCleaningError

try:
    # Load
    df = loader.load("data/raw_data.csv")
    
    # Clean
    df = clean_ohlcv_data(df)
    
    # Validate
    quality = validate_data_quality(df)
    if not quality.passed:
        logger.warning(f"Quality issues: {quality.quality_warnings}")
    
    # Check gaps
    gaps = detect_time_gaps(df)
    if gaps.has_anomalies:
        logger.warning(f"Time gap anomalies detected")
    
    # Save
    saver.save(df, "data/processed.parquet", fmt="parquet")
    
except DataLoadError as e:
    logger.error(f"Failed to load data: {e}")
except DataCleaningError as e:
    logger.error(f"Data cleaning failed: {e}")


DATA CLEANING PIPELINE (6 STAGES):
════════════════════════════════════

Stage 1: TIMESTAMP & STRUCTURE VALIDATION
  ✓ Remove invalid timestamps
  ✓ Remove duplicate timestamps
  ✓ Convert to UTC-naive

Stage 2: CONVERT & VALIDATE OHLC
  ✓ Convert to numeric (errors='coerce')
  ✓ Remove all-NaN rows

Stage 3: LIMITED FORWARD-FILL
  ✓ Forward-fill NaN values (max 3 bars)
  ✓ Prevents stale data propagation
  ✓ Remove unfillable NaN rows

Stage 4: STRUCTURAL OHLC VALIDATION
  ✓ Remove invalid patterns:
    - high < low
    - high < open
    - high < close
    - low > open
    - low > close

Stage 5: OUTLIER CLIPPING (Z-SCORE)
  ✓ Clip beyond 5σ (99.9999% confidence)
  ✓ Formula: clipped = clip(val, mean-5*std, mean+5*std)
  ✓ Applied per column (open, high, low, close)

Stage 6: VOLUME CLEANING
  ✓ Forward-fill missing volume (limit=2)
  ✓ Replace remaining NaN with 0
  ✓ Flag micro-volume candles (< 1% of median)


DATA QUALITY SCORING:
══════════════════════

Quality Score = 100 - deductions

Deductions:
  -20: Row count < minimum
  -15: Time span < 1 hour
  -10: High missing % (> max_missing_pct)
  -10: Infinity values detected
  -10: Invalid OHLC pattern
  -5: Sparse volume (median < 1.0)

Thresholds:
  Passed: quality_score >= 60.0
  Degraded: 30.0-60.0
  Critical: < 30.0


TIME GAP DETECTION:
═══════════════════

Expected Gap: Equal to expected_interval_minutes
  Example: 1h timeframe → 60 minutes expected

Anomalous Gap: > gap_threshold_multiplier * expected
  Default: > 1.5 * 60 = 90 minutes for 1h timeframe

Classification:
  Normal gaps: Market closure, scheduled breaks (OK)
  Anomalies: Transmission errors, data corruption (Alert)

Coverage %: Actual candles / Expected candles * 100
  Example: 480 actual / 500 expected = 96% coverage


INTEGRATION WITH OTHER MODULES:
════════════════════════════════

features/ module:
  ✓ Receives cleaned DataFrame from data.clean_ohlcv_data()
  ✓ Uses OHLCV data to generate features

models/ module:
  ✓ Uses validated quality reports
  ✓ Requires quality_score >= 60.0 for training

strategy/ module:
  ✓ Uses gap reports to identify trading windows
  ✓ Skips anomalous periods if needed

analysis/ module:
  ✓ Uses time gap reports for backtest analysis
  ✓ Adjusts performance metrics for gaps


EXTENDING THE DATA MODULE:
════════════════════════════

To add new DataSource:
  1. Add to DataSource enum
  2. Add method to DataLoader class
  3. Add method to DataSaver class

To add new data format:
  1. Create load_format() method
  2. Create save_format() method
  3. Update load()/save() dispatch

To add new quality check:
  1. Add to validate_data_quality()
  2. Add to DataQualityReport if needed
  3. Update quality_score logic


PERFORMANCE NOTES:
═══════════════════

• clean_ohlcv_data: O(n) with 6 passes
• validate_data_quality: O(n) single pass
• detect_time_gaps: O(n) with diff operation
• All operations work in-memory

For large datasets (10M+ rows):
  ✓ Use Parquet format (faster I/O)
  ✓ Process in chunks if memory-constrained
  ✓ Consider database backend (SQLite, DuckDB)


REQUIRED IMPORTS:
═════════════════

From core:
  logger, DataError, ensure_path, validate_dataframe,
  validate_numeric_columns

Standard Library:
  os, logging, datetime, pathlib, typing, dataclasses, enum

Third-Party:
  numpy, pandas

═══════════════════════════════════════════════════════════════════════════
