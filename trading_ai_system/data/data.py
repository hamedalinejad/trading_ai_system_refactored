"""
Trading AI System - Data Module
Data loading, cleaning, validation, and management.
"""

import sys
import os
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum

import numpy as np
import pandas as pd

# ✅ Fixed: Proper import paths
try:
    from trading_ai_system.core import (
        logger, TradingSystemError, DataError, ConfigError,
        get_global_config, DATA_PATH_CONFIG, ensure_path,
        validate_dataframe, validate_numeric_columns
    )
except ImportError:
    # Fallback for direct execution
    import logging
    logger = logging.getLogger(__name__)
    
    class DataError(Exception):
        pass
    
    class ConfigError(Exception):
        pass
    
    class TradingSystemError(Exception):
        pass
    
    def get_global_config():
        return {}
    
    DATA_PATH_CONFIG = {}
    
    def ensure_path(path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        return Path(path)
    
    def validate_dataframe(df, **kwargs):
        return True, []
    
    def validate_numeric_columns(df, cols):
        return True, []


# ═══════════════════════════════════════════════════════════════════════════
# EXCEPTION CLASSES
# ═══════════════════════════════════════════════════════════════════════════

class DataLoadError(DataError):
    """Failed to load data from source."""
    pass


class DataValidationError(DataError):
    """Data validation failed."""
    pass


class DataCleaningError(DataError):
    """Data cleaning failed."""
    pass


# ═══════════════════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════════════════

class DataSource(str, Enum):
    """Data source types."""
    CSV = "csv"
    PARQUET = "parquet"
    SQLITE = "sqlite"
    CCXT = "ccxt"
    API = "api"


class DataFrequency(str, Enum):
    """Data frequency/timeframe."""
    M1 = "1min"
    M5 = "5min"
    M15 = "15min"
    M30 = "30min"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"
    W1 = "1w"


# ═══════════════════════════════════════════════════════════════════════════
# DATA QUALITY CLASSES
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class DataQualityReport:
    """Data quality assessment report."""
    passed: bool = True
    row_count: int = 0
    time_span: str = ""
    ohlc_missing_pct: Dict[str, float] = field(default_factory=dict)
    volume_stats: Dict[str, Any] = field(default_factory=dict)
    price_range: Dict[str, Dict[str, float]] = field(default_factory=dict)
    quality_warnings: List[str] = field(default_factory=list)
    quality_score: float = 100.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "passed": self.passed,
            "row_count": self.row_count,
            "time_span": self.time_span,
            "ohlc_missing_pct": self.ohlc_missing_pct,
            "volume_stats": self.volume_stats,
            "price_range": self.price_range,
            "quality_warnings": self.quality_warnings,
            "quality_score": self.quality_score
        }


@dataclass
class TimeGapReport:
    """Time gap detection report."""
    total_gaps: int = 0
    largest_gap: Optional[Dict[str, Any]] = None
    gap_locations: List[Dict[str, Any]] = field(default_factory=list)
    has_anomalies: bool = False
    coverage_pct: float = 100.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_gaps": self.total_gaps,
            "largest_gap": self.largest_gap,
            "gap_locations": self.gap_locations,
            "has_anomalies": self.has_anomalies,
            "coverage_pct": self.coverage_pct
        }


# ═══════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def ensure_naive_utc_timestamp(ts: pd.Timestamp) -> pd.Timestamp:
    """Convert timestamp to UTC-naive datetime."""
    if ts is pd.NaT or pd.isna(ts):
        return pd.NaT
    
    if isinstance(ts, pd.Timestamp):
        if ts.tz is not None:
            ts = ts.tz_convert('UTC').tz_localize(None)
        return ts
    
    return pd.NaT


def ensure_naive_utc_series(ts_series: pd.Series) -> pd.Series:
    """Convert timestamp series to UTC-naive."""
    if not isinstance(ts_series, pd.Series):
        return ts_series
    
    # Already naive
    if ts_series.dtype == 'object' or str(ts_series.dtype).startswith('datetime'):
        if hasattr(ts_series.dtype, 'tz') and ts_series.dtype.tz is not None:
            return pd.to_datetime(ts_series, utc=True).dt.tz_localize(None)
        return pd.to_datetime(ts_series)
    
    return ts_series


def drop_broker_noise_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Remove broker-specific noise columns."""
    noise_cols = {
        'bid', 'ask', 'bid_volume', 'ask_volume',
        'spread', 'real_volume', 'vwap', 'twap',
        'symbol', 'exchange', 'broker'
    }
    
    cols_to_drop = [c for c in df.columns if c.lower() in noise_cols]
    if cols_to_drop:
        logger.debug(f"Dropping noise columns: {cols_to_drop}")
        df = df.drop(columns=cols_to_drop)
    
    return df


# ═══════════════════════════════════════════════════════════════════════════
# DATA CLEANING
# ═══════════════════════════════════════════════════════════════════════════

def clean_ohlcv_data(
    df: pd.DataFrame,
    max_ffill_periods: int = 3,
    zscore_threshold: float = 5.0,
    volume_min_pct: float = 0.01,
) -> pd.DataFrame:
    """v79: Clean raw OHLCV data with NaN handling and outlier clipping.
    
    Performs comprehensive data validation and cleaning:
    - Removes invalid timestamps & duplicate candles
    - Detects & removes structurally invalid OHLC patterns
    - Handles NaN values via limited ffill (max 3 bars)
    - Clips outliers using z-score (default: 5σ threshold)
    - Cleans volume data with sensible defaults
    
    Parameters
    ----------
    df : pd.DataFrame
        Raw OHLCV data
    max_ffill_periods : int, default=3
        Max consecutive bars to forward-fill
    zscore_threshold : float, default=5.0
        Outlier clipping threshold (σ units)
    volume_min_pct : float, default=0.01
        Minimum volume as % of median
    
    Returns
    -------
    pd.DataFrame
        Cleaned OHLCV data
    """
    df_clean = df.copy()
    df_clean = drop_broker_noise_columns(df_clean)
    
    required_cols = ['timestamp', 'open', 'high', 'low', 'close']
    missing_cols = [col for col in required_cols if col not in df_clean.columns]
    if missing_cols:
        raise DataCleaningError(f"Required columns missing: {missing_cols}")
    
    initial_count = len(df_clean)
    logger.info(f"clean_ohlcv_data: processing {initial_count:,} rows")
    
    # Stage 1: TIMESTAMP & STRUCTURE VALIDATION
    df_clean['timestamp'] = ensure_naive_utc_series(df_clean['timestamp'])
    
    invalid_ts = df_clean['timestamp'].isna()
    if invalid_ts.sum() > 0:
        logger.warning(f"  Removing {invalid_ts.sum():,} invalid timestamps")
        df_clean = df_clean[~invalid_ts].copy()
    
    dups = df_clean['timestamp'].duplicated()
    if dups.sum() > 0:
        logger.warning(f"  Removing {dups.sum():,} duplicate timestamps")
        df_clean = df_clean[~dups].copy()
    
    # Stage 2: CONVERT & VALIDATE OHLC
    for col in ['open', 'high', 'low', 'close']:
        df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
    
    critical_nan = df_clean[required_cols].isna().all(axis=1)
    if critical_nan.sum() > 0:
        logger.warning(f"  Removing {critical_nan.sum():,} all-NaN rows")
        df_clean = df_clean[~critical_nan].copy()
    
    # Stage 3: LIMITED FORWARD-FILL
    for col in ['open', 'high', 'low', 'close']:
        nan_mask = df_clean[col].isna()
        if nan_mask.sum() > 0:
            df_clean[col] = df_clean[col].fillna(method='ffill', limit=max_ffill_periods)
            still_nan = df_clean[col].isna().sum()
            filled = nan_mask.sum() - still_nan
            if filled > 0:
                logger.debug(f"  Forward-filled {filled} NaN in '{col}'")
    
    remaining_nan = df_clean[required_cols].isna().any(axis=1)
    if remaining_nan.sum() > 0:
        logger.warning(f"  Removing {remaining_nan.sum():,} unfillable NaN rows")
        df_clean = df_clean[~remaining_nan].copy()
    
    # Stage 4: STRUCTURAL OHLC VALIDATION
    invalid_patterns = (
        (df_clean['high'] < df_clean['low']) |
        (df_clean['high'] < df_clean['open']) |
        (df_clean['high'] < df_clean['close']) |
        (df_clean['low'] > df_clean['open']) |
        (df_clean['low'] > df_clean['close'])
    )
    
    if invalid_patterns.sum() > 0:
        logger.warning(f"  Removing {invalid_patterns.sum():,} invalid candles")
        df_clean = df_clean[~invalid_patterns].copy()
    
    # Stage 5: OUTLIER CLIPPING VIA Z-SCORE
    for col in ['open', 'high', 'low', 'close']:
        prices = df_clean[col]
        mean = prices.mean()
        std = prices.std()
        
        if std > 0:
            z_scores = np.abs((prices - mean) / std)
            outliers = z_scores > zscore_threshold
            
            if outliers.sum() > 0:
                lower_bound = mean - zscore_threshold * std
                upper_bound = mean + zscore_threshold * std
                df_clean[col] = df_clean[col].clip(lower_bound, upper_bound)
                logger.debug(f"  Clipped {outliers.sum():,} outliers in '{col}'")
    
    # Stage 6: VOLUME CLEANING
    if 'volume' in df_clean.columns:
        df_clean['volume'] = pd.to_numeric(df_clean['volume'], errors='coerce')
        df_clean['volume'] = df_clean['volume'].fillna(method='ffill', limit=2)
        df_clean['volume'] = df_clean['volume'].fillna(0.0)
        
        if df_clean['volume'].sum() > 0:
            median_vol = df_clean['volume'].median()
            min_vol = median_vol * volume_min_pct
            micro_vol = (df_clean['volume'] > 0) & (df_clean['volume'] < min_vol)
            
            if micro_vol.sum() > 0:
                logger.debug(f"  Flagged {micro_vol.sum():,} micro-volume candles")
    else:
        df_clean['volume'] = 0.0
    
    final_count = len(df_clean)
    removed = initial_count - final_count
    pct_removed = (removed / initial_count * 100) if initial_count > 0 else 0.0
    
    logger.info(
        f"clean_ohlcv_data: completed. "
        f"Initial: {initial_count:,} → Final: {final_count:,} "
        f"(Removed: {removed:,} | {pct_removed:.1f}%)"
    )
    
    return df_clean


# ═══════════════════════════════════════════════════════════════════════════
# DATA VALIDATION
# ═══════════════════════════════════════════════════════════════════════════

def validate_data_quality(
    df: pd.DataFrame,
    min_rows: int = 100,
    max_missing_pct: float = 5.0,
    warn_on_sparse: bool = True,
) -> DataQualityReport:
    """v79: Comprehensive data quality report (read-only).
    
    Validates cleaned OHLCV data against quality thresholds.
    
    Parameters
    ----------
    df : pd.DataFrame
        Cleaned OHLCV data
    min_rows : int, default=100
        Minimum acceptable row count
    max_missing_pct : float, default=5.0
        Max missing % per column before warning
    warn_on_sparse : bool, default=True
        Warn if volume sparse
    
    Returns
    -------
    DataQualityReport
        Quality assessment with score and warnings
    """
    report = DataQualityReport(
        passed=True,
        row_count=len(df),
        quality_score=100.0
    )
    
    if len(df) == 0:
        report.passed = False
        report.quality_warnings.append("Empty DataFrame")
        report.quality_score = 0.0
        return report
    
    # Check row count
    if len(df) < min_rows:
        report.passed = False
        report.quality_warnings.append(f"Insufficient rows: {len(df)} < {min_rows}")
        report.quality_score -= 20.0
    
    # Check time span
    if "timestamp" in df.columns:
        try:
            ts_min = df["timestamp"].min()
            ts_max = df["timestamp"].max()
            td = ts_max - ts_min
            
            if td.days > 0:
                report.time_span = f"{td.days} days, {td.seconds // 3600} hours"
            else:
                report.time_span = f"{td.seconds // 3600} hours"
            
            if td.total_seconds() < 3600:
                report.quality_warnings.append("Data span < 1 hour")
                report.quality_score -= 15.0
        except Exception as e:
            report.quality_warnings.append(f"Timestamp parsing error: {e}")
    
    # Check OHLC missing %
    for col in ["open", "high", "low", "close"]:
        if col in df.columns:
            missing_pct = (df[col].isna().sum() / len(df)) * 100
            report.ohlc_missing_pct[col] = round(missing_pct, 2)
            
            if missing_pct > max_missing_pct:
                report.passed = False
                report.quality_warnings.append(f"High missing in '{col}': {missing_pct:.1f}%")
                report.quality_score -= 10.0
            
            if col in df.columns and df[col].notna().any():
                report.price_range[col] = {
                    "min": float(df[col].min()),
                    "max": float(df[col].max()),
                }
    
    # Check volume stats
    if "volume" in df.columns:
        vol_data = df["volume"][df["volume"] > 0]
        report.volume_stats = {
            "min": float(vol_data.min()) if len(vol_data) > 0 else 0.0,
            "max": float(vol_data.max()) if len(vol_data) > 0 else 0.0,
            "median": float(vol_data.median()) if len(vol_data) > 0 else 0.0,
            "zero_count": int((df["volume"] == 0).sum()),
        }
        
        if warn_on_sparse and vol_data.median() < 1.0:
            report.quality_warnings.append("Sparse volume (median < 1.0)")
            report.quality_score -= 5.0
    
    # Check for inf values
    for col in ["open", "high", "low", "close"]:
        if col in df.columns and np.isinf(df[col]).any():
            report.quality_warnings.append(f"Infinity values in '{col}'")
            report.quality_score -= 10.0
    
    report.quality_score = max(0.0, min(100.0, report.quality_score))
    report.passed = report.quality_score >= 60.0
    
    logger.info(
        f"validate_data_quality: {len(df):,} rows, "
        f"score={report.quality_score:.0f}, "
        f"warnings={len(report.quality_warnings)}"
    )
    
    return report


# ═══════════════════════════════════════════════════════════════════════════
# TIME GAP DETECTION
# ═══════════════════════════════════════════════════════════════════════════

def detect_time_gaps(
    df: pd.DataFrame,
    expected_interval_minutes: int = 60,
    gap_threshold_multiplier: float = 1.5,
) -> TimeGapReport:
    """v79: Detect missing candles (time gaps) in OHLCV data.
    
    Identifies breaks in continuous time series (market closures, errors).
    
    Parameters
    ----------
    df : pd.DataFrame
        OHLCV data with timestamp column
    expected_interval_minutes : int, default=60
        Expected time between consecutive candles
    gap_threshold_multiplier : float, default=1.5
        Flag gaps > N * expected_interval as anomalies
    
    Returns
    -------
    TimeGapReport
        Gap analysis with anomaly classification
    """
    report = TimeGapReport()
    
    if len(df) < 2 or "timestamp" not in df.columns:
        return report
    
    try:
        timestamps = pd.to_datetime(df["timestamp"])
        diffs = timestamps.diff().dt.total_seconds() / 60
        
        expected_gap_threshold = expected_interval_minutes * gap_threshold_multiplier
        gap_indices = np.where(diffs > expected_interval_minutes)[0]
        
        if len(gap_indices) == 0:
            report.coverage_pct = 100.0
            return report
        
        report.total_gaps = len(gap_indices)
        
        for idx in gap_indices:
            gap_minutes = float(diffs.iloc[idx])
            is_anomaly = gap_minutes > expected_gap_threshold
            
            gap_info = {
                "index": int(idx),
                "start_ts": str(timestamps.iloc[idx - 1]),
                "end_ts": str(timestamps.iloc[idx]),
                "duration_minutes": round(gap_minutes, 1),
                "duration_hours": round(gap_minutes / 60, 2),
                "is_anomaly": is_anomaly,
            }
            
            report.gap_locations.append(gap_info)
            
            if is_anomaly:
                report.has_anomalies = True
            
            if (report.largest_gap is None or 
                gap_minutes > report.largest_gap["duration_minutes"]):
                report.largest_gap = gap_info
        
        # Calculate coverage %
        total_time_span = (timestamps.iloc[-1] - timestamps.iloc[0]).total_seconds() / 60
        expected_candles = total_time_span / expected_interval_minutes
        actual_candles = len(df) - 1
        if expected_candles > 0:
            report.coverage_pct = (actual_candles / expected_candles) * 100.0
        
        if report.has_anomalies:
            logger.warning(
                f"detect_time_gaps: Found {report.total_gaps} gaps, "
                f"{sum(1 for g in report.gap_locations if g['is_anomaly'])} anomalies"
            )
        
    except Exception as e:
        logger.error(f"detect_time_gaps error: {e}")
    
    return report


# ═══════════════════════════════════════════════════════════════════════════
# DATA LOADING
# ═══════════════════════════════════════════════════════════════════════════

class DataLoader:
    """Load data from various sources."""
    
    @staticmethod
    def load_csv(path: str, **kwargs) -> pd.DataFrame:
        """Load data from CSV file."""
        try:
            df = pd.read_csv(path, **kwargs)
            logger.info(f"Loaded {len(df):,} rows from {path}")
            return df
        except FileNotFoundError:
            raise DataLoadError(f"CSV file not found: {path}")
        except Exception as e:
            raise DataLoadError(f"Failed to load CSV {path}: {e}")
    
    @staticmethod
    def load_parquet(path: str, **kwargs) -> pd.DataFrame:
        """Load data from Parquet file."""
        try:
            df = pd.read_parquet(path, **kwargs)
            logger.info(f"Loaded {len(df):,} rows from {path}")
            return df
        except FileNotFoundError:
            raise DataLoadError(f"Parquet file not found: {path}")
        except Exception as e:
            raise DataLoadError(f"Failed to load Parquet {path}: {e}")
    
    @staticmethod
    def load(path: str, source: DataSource = DataSource.CSV, **kwargs) -> pd.DataFrame:
        """Load data from any supported source."""
        path = str(path)
        
        if source == DataSource.CSV:
            return DataLoader.load_csv(path, **kwargs)
        elif source == DataSource.PARQUET:
            return DataLoader.load_parquet(path, **kwargs)
        else:
            raise DataLoadError(f"Unsupported data source: {source}")


# ═══════════════════════════════════════════════════════════════════════════
# DATA SAVING
# ═══════════════════════════════════════════════════════════════════════════

class DataSaver:
    """Save data to various formats."""
    
    @staticmethod
    def save_csv(df: pd.DataFrame, path: str, index: bool = False, **kwargs) -> None:
        """Save data to CSV file."""
        try:
            ensure_path(path)
            df.to_csv(path, index=index, **kwargs)
            logger.info(f"Saved {len(df):,} rows to {path}")
        except Exception as e:
            raise DataError(f"Failed to save CSV {path}: {e}")
    
    @staticmethod
    def save_parquet(df: pd.DataFrame, path: str, **kwargs) -> None:
        """Save data to Parquet file."""
        try:
            ensure_path(path)
            df.to_parquet(path, **kwargs)
            logger.info(f"Saved {len(df):,} rows to {path}")
        except Exception as e:
            raise DataError(f"Failed to save Parquet {path}: {e}")
    
    @staticmethod
    def save(df: pd.DataFrame, path: str, fmt: str = "csv", **kwargs) -> None:
        """Save data to file in specified format."""
        if fmt.lower() == "csv":
            DataSaver.save_csv(df, path, **kwargs)
        elif fmt.lower() == "parquet":
            DataSaver.save_parquet(df, path, **kwargs)
        else:
            raise DataError(f"Unsupported format: {fmt}")


# ═══════════════════════════════════════════════════════════════════════════
# EXPORTS
# ═══════════════════════════════════════════════════════════════════════════

__all__ = [
    # Enums
    'DataSource', 'DataFrequency',
    
    # Classes & Reports
    'DataQualityReport', 'TimeGapReport', 'DataLoader', 'DataSaver',
    
    # Exceptions
    'DataLoadError', 'DataValidationError', 'DataCleaningError',
    
    # Functions
    'ensure_naive_utc_timestamp', 'ensure_naive_utc_series',
    'drop_broker_noise_columns', 'clean_ohlcv_data',
    'validate_data_quality', 'detect_time_gaps',
]
