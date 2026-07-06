"""
Trading AI System - Data Module (v2.0)
Data loading, cleaning, validation, and management.

Key Improvements:
- Fixed deprecated fillna(method='ffill') -> ffill()
- Added inf control for volume
- Added volume >= 0 validation
- Implemented load_sqlite support
- Added CSV compression support
- Added resample_ohlcv for timeframe conversion
- Enhanced validation with spikes and gaps
- Complete docstrings and type hints
- Improved error handling
"""

import sys
import os
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from threading import Lock
import sqlite3

import numpy as np
import pandas as pd

try:
    from trading_ai_system.core import (
        get_logger,
        TradingSystemError,
        ensure_path,
    )
    logger = get_logger(__name__)
except ImportError:
    logger = logging.getLogger(__name__)
    
    class TradingSystemError(Exception):
        pass
    
    def ensure_path(path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        return Path(path)


class DataError(TradingSystemError):
    """Base data error"""
    pass


class DataLoadError(DataError):
    """Data loading error"""
    pass


class DataValidationError(DataError):
    """Data validation error"""
    pass


class DataCleaningError(DataError):
    """Data cleaning error"""
    pass


class DataSource(str, Enum):
    """Data source types"""
    CSV = "csv"
    PARQUET = "parquet"
    SQLITE = "sqlite"
    CCXT = "ccxt"
    API = "api"


class DataFrequency(str, Enum):
    """Data frequency/timeframe types"""
    M1 = "1min"
    M5 = "5min"
    M15 = "15min"
    M30 = "30min"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"
    W1 = "1w"


@dataclass
class DataQualityReport:
    """Data quality analysis report"""
    passed: bool = True
    row_count: int = 0
    time_span: str = ""
    ohlc_missing_pct: Dict[str, float] = field(default_factory=dict)
    volume_stats: Dict[str, Any] = field(default_factory=dict)
    price_range: Dict[str, Dict[str, float]] = field(default_factory=dict)
    spike_stats: Dict[str, Any] = field(default_factory=dict)
    gap_stats: Dict[str, Any] = field(default_factory=dict)
    quality_warnings: List[str] = field(default_factory=list)
    quality_score: float = 100.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "passed": self.passed,
            "row_count": self.row_count,
            "time_span": self.time_span,
            "ohlc_missing_pct": self.ohlc_missing_pct.copy(),
            "volume_stats": self.volume_stats.copy(),
            "price_range": {k: v.copy() for k, v in self.price_range.items()},
            "spike_stats": self.spike_stats.copy(),
            "gap_stats": self.gap_stats.copy(),
            "quality_warnings": self.quality_warnings.copy(),
            "quality_score": self.quality_score
        }


@dataclass
class TimeGapReport:
    """Time gap analysis report"""
    total_gaps: int = 0
    largest_gap: Optional[Dict[str, Any]] = None
    gap_locations: List[Dict[str, Any]] = field(default_factory=list)
    has_anomalies: bool = False
    coverage_pct: float = 100.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "total_gaps": self.total_gaps,
            "largest_gap": self.largest_gap.copy() if self.largest_gap else None,
            "gap_locations": [g.copy() for g in self.gap_locations],
            "has_anomalies": self.has_anomalies,
            "coverage_pct": self.coverage_pct
        }


# ==================== TIMESTAMP UTILITIES ====================

def ensure_naive_utc_timestamp(ts: pd.Timestamp) -> pd.Timestamp:
    """
    Convert timestamp to naive UTC.
    
    Args:
        ts: Pandas Timestamp
        
    Returns:
        Naive UTC timestamp
    """
    if ts is pd.NaT or pd.isna(ts):
        return pd.NaT
    
    if isinstance(ts, pd.Timestamp):
        try:
            if ts.tz is not None:
                ts = ts.tz_convert('UTC').tz_localize(None)
            return ts
        except Exception as e:
            logger.warning(f"Failed to convert timestamp: {e}")
            return pd.NaT
    
    return pd.NaT


def ensure_naive_utc_series(ts_series: pd.Series) -> pd.Series:
    """
    Convert timestamp series to naive UTC.
    
    Fix #1.5: Improved timezone handling with error coercion
    
    Args:
        ts_series: Pandas Series with timestamps
        
    Returns:
        Series with naive UTC timestamps
    """
    if not isinstance(ts_series, pd.Series):
        return ts_series
    
    try:
        # Fix #1.5: Use errors='coerce' for object dtype
        if ts_series.dtype == 'object':
            ts_series = pd.to_datetime(ts_series, errors='coerce')
        
        # Handle timezone-aware series
        if hasattr(ts_series.dtype, 'tz') and ts_series.dtype.tz is not None:
            try:
                ts_series = ts_series.dt.tz_convert('UTC').dt.tz_localize(None)
            except Exception as e:
                logger.warning(f"Failed to convert timezone: {e}")
        
        return ts_series
    except Exception as e:
        logger.error(f"Failed to convert timestamp series: {e}")
        return ts_series


def drop_broker_noise_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Drop broker-specific noise columns.
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with noise columns removed
    """
    if not isinstance(df, pd.DataFrame) or df.empty:
        return df
    
    noise_cols = {
        'bid', 'ask', 'bid_volume', 'ask_volume',
        'spread', 'real_volume', 'vwap', 'twap',
        'symbol', 'exchange', 'broker'
    }
    
    cols_to_drop = [c for c in df.columns if c.lower() in noise_cols]
    if cols_to_drop:
        logger.debug(f"Dropping noise columns: {cols_to_drop}")
        df = df.drop(columns=cols_to_drop, errors='ignore')
    
    return df


# ==================== DATA CLEANING ====================

def clean_ohlcv_data(
    df: pd.DataFrame,
    max_ffill_periods: int = 3,
    zscore_threshold: float = 5.0,
    volume_min_pct: float = 0.01,
    remove_negative_volume: bool = True,
) -> pd.DataFrame:
    """
    Clean and normalize OHLCV data.
    
    Key improvements:
    - Fix #1.1: Use ffill() instead of deprecated fillna(method='ffill')
    - Fix #1.2: Control inf in volume
    - Fix #1.6: Validate volume >= 0
    
    Args:
        df: Input DataFrame
        max_ffill_periods: Max forward-fill periods for NaN
        zscore_threshold: Z-score threshold for outlier detection
        volume_min_pct: Minimum volume percentage
        remove_negative_volume: Whether to remove negative volumes
        
    Returns:
        Cleaned DataFrame
        
    Raises:
        DataCleaningError: If cleaning fails
    """
    if not isinstance(df, pd.DataFrame) or df.empty:
        raise DataCleaningError("Input DataFrame is empty or invalid")
    
    # Fix #2.2: Use deep=False for lighter copy
    df_clean = df.copy(deep=False)
    df_clean = drop_broker_noise_columns(df_clean)
    
    required_cols = ['timestamp', 'open', 'high', 'low', 'close']
    missing_cols = [col for col in required_cols if col not in df_clean.columns]
    if missing_cols:
        raise DataCleaningError(f"Required columns missing: {missing_cols}")
    
    initial_count = len(df_clean)
    logger.info(f"clean_ohlcv_data: processing {initial_count:,} rows")
    
    try:
        # Ensure timestamp is naive UTC
        df_clean['timestamp'] = ensure_naive_utc_series(df_clean['timestamp'])
        
        # Remove duplicates
        df_clean = df_clean.drop_duplicates(subset=['timestamp'], keep='first')
        removed_dups = initial_count - len(df_clean)
        if removed_dups > 0:
            logger.debug(f"Removed {removed_dups} duplicate rows")
        
        # Fix #1.6: Validate OHLC structure
        valid_ohlc = (
            (df_clean['low'] <= df_clean['close']) &
            (df_clean['high'] >= df_clean['close']) &
            (df_clean['low'] <= df_clean['open']) &
            (df_clean['high'] >= df_clean['open']) &
            (df_clean['low'] <= df_clean['high']) &
            (df_clean['low'] > 0) &
            (df_clean['high'] > 0)
        )
        
        invalid_count = (~valid_ohlc).sum()
        if invalid_count > 0:
            df_clean = df_clean[valid_ohlc].copy()
            logger.warning(f"Removed {invalid_count} structurally invalid OHLC rows")
        
        # Fix #1.1: Use ffill() instead of deprecated fillna(method='ffill')
        for col in ['open', 'high', 'low', 'close']:
            if col in df_clean.columns:
                nan_count = df_clean[col].isna().sum()
                if nan_count > 0:
                    df_clean[col] = df_clean[col].ffill(limit=max_ffill_periods)
                    remaining_nan = df_clean[col].isna().sum()
                    if remaining_nan > 0:
                        df_clean = df_clean[df_clean[col].notna()].copy()
                        logger.warning(f"Removed {remaining_nan} rows with irreplaceable NaN in '{col}'")
        
        # Handle outliers with z-score
        for col in ['open', 'high', 'low', 'close']:
            if col in df_clean.columns:
                try:
                    numeric_series = pd.to_numeric(df_clean[col], errors='coerce')
                    mean = numeric_series.mean()
                    std = numeric_series.std()
                    
                    # Fix #1.3: Log when std == 0
                    if std == 0:
                        logger.debug(f"Zero standard deviation in '{col}' - all values uniform")
                    elif std > 0:
                        z_scores = np.abs((numeric_series - mean) / std)
                        outliers = z_scores > zscore_threshold
                        if outliers.any():
                            df_clean.loc[outliers, col] = mean
                            logger.debug(f"Clipped {outliers.sum()} outliers in '{col}'")
                except ValueError as e:
                    logger.warning(f"Error detecting outliers in '{col}': {e}")
        
        # Fix #1.2, #1.6: Clean volume data
        if 'volume' in df_clean.columns:
            # Control inf values
            df_clean['volume'] = df_clean['volume'].replace([np.inf, -np.inf], 0)
            
            # Remove negative volumes
            if remove_negative_volume:
                neg_vol = (df_clean['volume'] < 0).sum()
                if neg_vol > 0:
                    df_clean.loc[df_clean['volume'] < 0, 'volume'] = 0
                    logger.warning(f"Removed {neg_vol} rows with negative volume")
            
            # Handle zero/NaN volume
            vol_valid = df_clean['volume'][(df_clean['volume'] > 0) & (df_clean['volume'].notna())]
            
            if len(vol_valid) > 0:
                vol_median = vol_valid.median()
                vol_min_threshold = vol_median * volume_min_pct
                
                # Set small volumes to zero
                small_vol = (df_clean['volume'] > 0) & (df_clean['volume'] < vol_min_threshold)
                if small_vol.any():
                    df_clean.loc[small_vol, 'volume'] = 0
                    logger.debug(f"Set {small_vol.sum()} small volumes to zero")
            
            # Fill remaining NaN in volume
            df_clean['volume'] = df_clean['volume'].fillna(0)
            
            logger.debug(f"Cleaned volume data: {len(vol_valid)} valid volumes")
        
        # Sort and reset index
        df_clean = df_clean.sort_values('timestamp').reset_index(drop=True)
        
        final_count = len(df_clean)
        removed_total = initial_count - final_count
        logger.info(f"clean_ohlcv_data complete: {final_count:,} rows ({removed_total:,} removed)")
        
        return df_clean
    
    except DataCleaningError:
        raise
    except KeyError as e:
        raise DataCleaningError(f"KeyError during cleaning: {e}")
    except ValueError as e:
        raise DataCleaningError(f"ValueError during cleaning: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error in clean_ohlcv_data: {e}")
        raise DataCleaningError(f"Cleaning failed: {e}")


# ==================== VALIDATION ====================

def detect_spikes(
    df: pd.DataFrame,
    pct_threshold: float = 5.0,
    lookback: int = 20
) -> Dict[str, int]:
    """
    Detect price spikes (sudden large price movements).
    
    Fix #3.4: Added spike detection
    
    Args:
        df: Input DataFrame
        pct_threshold: Spike threshold in percentage
        lookback: Lookback window for average
        
    Returns:
        Dictionary with spike counts by OHLC column
    """
    spikes = {}
    
    try:
        for col in ['open', 'high', 'low', 'close']:
            if col not in df.columns:
                continue
            
            prices = df[col].astype(float)
            ma = prices.rolling(lookback, min_periods=1).mean()
            pct_change = ((prices - ma) / (ma + 1e-10)).abs() * 100
            
            spike_count = (pct_change > pct_threshold).sum()
            spikes[col] = int(spike_count)
        
        return spikes
    except Exception as e:
        logger.warning(f"Error detecting spikes: {e}")
        return {}


def validate_data_quality(
    df: pd.DataFrame,
    max_missing_pct: float = 5.0,
    warn_on_sparse: bool = True,
    check_spikes: bool = True,
    check_gaps: bool = True,
) -> DataQualityReport:
    """
    Validate data quality.
    
    Fix #3.4: Added spike and gap detection
    
    Args:
        df: Input DataFrame
        max_missing_pct: Maximum acceptable missing percentage
        warn_on_sparse: Whether to warn on sparse data
        check_spikes: Check for price spikes
        check_gaps: Check for time gaps
        
    Returns:
        DataQualityReport with validation results
    """
    report = DataQualityReport()
    
    if not isinstance(df, pd.DataFrame) or df.empty:
        report.passed = False
        report.quality_warnings.append("DataFrame is empty or invalid")
        return report
    
    report.row_count = len(df)
    
    try:
        # Validate timestamp
        if 'timestamp' in df.columns:
            ts = pd.to_datetime(df['timestamp'], errors='coerce')
            valid_ts = ts[ts.notna()]
            
            if len(valid_ts) > 1:
                report.time_span = str(valid_ts.max() - valid_ts.min())
                td = valid_ts.max() - valid_ts.min()
                
                if td.total_seconds() < 3600:
                    report.quality_warnings.append("Data span < 1 hour")
                    report.quality_score -= 15.0
        
        # Validate OHLC columns
        for col in ["open", "high", "low", "close"]:
            if col in df.columns:
                missing_pct = (df[col].isna().sum() / len(df)) * 100
                report.ohlc_missing_pct[col] = round(missing_pct, 2)
                
                if missing_pct > max_missing_pct:
                    report.passed = False
                    report.quality_warnings.append(
                        f"High missing in '{col}': {missing_pct:.1f}%"
                    )
                    report.quality_score -= 10.0
                
                # Check for inf values
                if np.isinf(df[col]).any():
                    inf_count = np.isinf(df[col]).sum()
                    report.quality_warnings.append(f"Found {inf_count} inf values in '{col}'")
                    report.quality_score -= 5.0
                
                # Price range
                valid_vals = df[col][df[col].notna() & np.isfinite(df[col])]
                if len(valid_vals) > 0:
                    report.price_range[col] = {
                        "min": float(valid_vals.min()),
                        "max": float(valid_vals.max()),
                        "median": float(valid_vals.median()),
                    }
        
        # Validate volume
        if "volume" in df.columns:
            vol_data = df["volume"][(df["volume"] > 0) & (df["volume"].notna())]
            
            # Check for inf in volume
            if np.isinf(df["volume"]).any():
                inf_count = np.isinf(df["volume"]).sum()
                report.quality_warnings.append(f"Found {inf_count} inf values in volume")
                report.quality_score -= 5.0
            
            if len(vol_data) > 0:
                report.volume_stats = {
                    "count": int(len(vol_data)),
                    "min": float(vol_data.min()),
                    "max": float(vol_data.max()),
                    "median": float(vol_data.median()),
                    "mean": float(vol_data.mean()),
                }
        
        # Spike detection
        if check_spikes:
            spikes = detect_spikes(df)
            if spikes:
                report.spike_stats = spikes
                total_spikes = sum(spikes.values())
                if total_spikes > len(df) * 0.01:
                    report.quality_warnings.append(f"High spike count: {total_spikes}")
                    report.quality_score -= 5.0
        
        # Gap detection
        if check_gaps and 'timestamp' in df.columns:
            gap_report = detect_time_gaps(df)
            if gap_report.total_gaps > 0:
                report.gap_stats = gap_report.to_dict()
                if not gap_report.has_anomalies:
                    report.quality_score -= 2.0
        
        logger.info(f"Data quality report: score={report.quality_score:.1f}, passed={report.passed}")
        return report
    
    except Exception as e:
        logger.error(f"Error validating data quality: {e}")
        report.passed = False
        report.quality_warnings.append(f"Validation error: {e}")
        return report


def detect_time_gaps(
    df: pd.DataFrame,
    expected_interval: Optional[timedelta] = None,
    max_gaps_to_report: int = 10
) -> TimeGapReport:
    """
    Detect time gaps in data.
    
    Fix #1.4: Added boundary check for idx > 0
    
    Args:
        df: Input DataFrame with timestamp column
        expected_interval: Expected interval between bars
        max_gaps_to_report: Maximum gaps to include in report
        
    Returns:
        TimeGapReport with gap analysis
    """
    report = TimeGapReport()
    
    if 'timestamp' not in df.columns or df.empty:
        return report
    
    try:
        timestamps = pd.to_datetime(df['timestamp'], errors='coerce')
        timestamps = timestamps[timestamps.notna()].sort_values()
        
        if len(timestamps) < 2:
            return report
        
        diffs = timestamps.diff()
        
        if expected_interval is None:
            expected_interval = diffs[diffs > timedelta(0)].median()
        
        if expected_interval is None or expected_interval == timedelta(0):
            return report
        
        gap_indices = np.where(diffs > expected_interval * 1.5)[0]
        report.total_gaps = len(gap_indices)
        
        if report.total_gaps > 0:
            max_gap = diffs.max()
            report.largest_gap = {
                "duration": str(max_gap),
                "hours": max_gap.total_seconds() / 3600
            }
            
            # Fix #1.4: Check idx > 0 before using idx-1
            for idx in gap_indices[:max_gaps_to_report]:
                if idx > 0:
                    gap_info = {
                        "start": timestamps.iloc[idx - 1].isoformat(),
                        "end": timestamps.iloc[idx].isoformat(),
                        "duration": str(diffs.iloc[idx]),
                    }
                    report.gap_locations.append(gap_info)
            
            # Calculate coverage
            if len(timestamps) > 1:
                total_span = timestamps.iloc[-1] - timestamps.iloc[0]
                gap_duration = diffs[diffs > expected_interval].sum()
                coverage = 1.0 - (gap_duration / total_span) if total_span.total_seconds() > 0 else 1.0
                report.coverage_pct = max(0.0, min(coverage, 1.0)) * 100
        
        else:
            report.coverage_pct = 100.0
        
        logger.debug(f"Time gap analysis: {report.total_gaps} gaps, coverage={report.coverage_pct:.1f}%")
        return report
    
    except Exception as e:
        logger.error(f"Error detecting time gaps: {e}")
        return report


# ==================== RESAMPLING ====================

def resample_ohlcv(
    df: pd.DataFrame,
    target_freq: str,
    agg_dict: Optional[Dict[str, str]] = None
) -> pd.DataFrame:
    """
    Resample OHLCV data to different timeframe.
    
    Fix #3.3: Added resample functionality
    
    Args:
        df: Input OHLCV DataFrame with timestamp index
        target_freq: Target frequency (e.g., '1h', '4h', '1d')
        agg_dict: Custom aggregation rules
        
    Returns:
        Resampled DataFrame
    """
    if not isinstance(df, pd.DataFrame) or df.empty:
        raise DataCleaningError("Input DataFrame is empty")
    
    try:
        df_resample = df.copy()
        
        # Ensure timestamp is index
        if 'timestamp' in df_resample.columns:
            df_resample = df_resample.set_index('timestamp')
        
        df_resample.index = pd.to_datetime(df_resample.index)
        
        # Default OHLCV aggregation
        if agg_dict is None:
            agg_dict = {
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum',
            }
        
        # Resample with custom aggregation
        resampled = df_resample.resample(target_freq).agg(agg_dict)
        
        # Remove bars with no data
        resampled = resampled.dropna(subset=['open', 'close'])
        
        # Reset index
        resampled = resampled.reset_index()
        
        logger.info(f"Resampled from {len(df)} to {len(resampled)} bars at {target_freq}")
        return resampled
    
    except Exception as e:
        logger.error(f"Error resampling data: {e}")
        raise DataCleaningError(f"Resampling failed: {e}")


# ==================== DATA LOADING ====================

class DataLoader:
    """Load data from various sources"""
    
    def __init__(self):
        self._lock = Lock()
        logger.info("DataLoader initialized")
    
    def load_csv(
        self,
        filepath: Path,
        compression: str = 'infer'  # Fix #3.2: Support compression
    ) -> pd.DataFrame:
        """
        Load data from CSV file.
        
        Fix #3.2: Support automatic compression detection
        
        Args:
            filepath: Path to CSV file
            compression: Compression type ('infer', 'gzip', 'bz2', 'zip', 'xz', None)
            
        Returns:
            DataFrame
        """
        try:
            filepath = Path(filepath)
            logger.info(f"Loading CSV: {filepath}")
            
            df = pd.read_csv(filepath, compression=compression)
            logger.info(f"Loaded {len(df)} rows from {filepath}")
            return df
        
        except FileNotFoundError:
            raise DataLoadError(f"File not found: {filepath}")
        except Exception as e:
            raise DataLoadError(f"Failed to load CSV {filepath}: {e}")
    
    def load_parquet(self, filepath: Path) -> pd.DataFrame:
        """Load data from Parquet file"""
        try:
            filepath = Path(filepath)
            logger.info(f"Loading Parquet: {filepath}")
            
            df = pd.read_parquet(filepath)
            logger.info(f"Loaded {len(df)} rows from {filepath}")
            return df
        
        except FileNotFoundError:
            raise DataLoadError(f"File not found: {filepath}")
        except Exception as e:
            raise DataLoadError(f"Failed to load Parquet {filepath}: {e}")
    
    def load_sqlite(
        self,
        db_path: Path,
        query: str,
        params: Optional[List] = None
    ) -> pd.DataFrame:
        """
        Load data from SQLite database.
        
        Fix #3.1: Implemented SQLite support
        
        Args:
            db_path: Path to SQLite database
            query: SQL query to execute
            params: Query parameters
            
        Returns:
            DataFrame
        """
        try:
            db_path = Path(db_path)
            if not db_path.exists():
                raise DataLoadError(f"Database not found: {db_path}")
            
            logger.info(f"Loading from SQLite: {db_path}")
            
            with sqlite3.connect(db_path) as conn:
                df = pd.read_sql_query(query, conn, params=params)
            
            logger.info(f"Loaded {len(df)} rows from SQLite")
            return df
        
        except sqlite3.Error as e:
            raise DataLoadError(f"SQLite error: {e}")
        except Exception as e:
            raise DataLoadError(f"Failed to load from SQLite: {e}")
    
    def load(self, source: DataSource, **kwargs) -> pd.DataFrame:
        """
        Load data from source.
        
        Args:
            source: DataSource enum value
            **kwargs: Source-specific arguments
            
        Returns:
            DataFrame
        """
        if source == DataSource.CSV:
            return self.load_csv(**kwargs)
        elif source == DataSource.PARQUET:
            return self.load_parquet(**kwargs)
        elif source == DataSource.SQLITE:
            return self.load_sqlite(**kwargs)
        else:
            raise DataLoadError(f"Unsupported data source: {source}")


class DataSaver:
    """Save data to various formats"""
    
    def __init__(self):
        self._lock = Lock()
        logger.info("DataSaver initialized")
    
    def save_csv(self, df: pd.DataFrame, filepath: Path, **kwargs) -> None:
        """Save to CSV"""
        try:
            filepath = Path(filepath)
            ensure_path(filepath)
            df.to_csv(filepath, index=False, **kwargs)
            logger.info(f"Saved {len(df)} rows to {filepath}")
        except Exception as e:
            raise DataError(f"Failed to save CSV: {e}")
    
    def save_parquet(self, df: pd.DataFrame, filepath: Path, **kwargs) -> None:
        """Save to Parquet"""
        try:
            filepath = Path(filepath)
            ensure_path(filepath)
            df.to_parquet(filepath, index=False, **kwargs)
            logger.info(f"Saved {len(df)} rows to {filepath}")
        except Exception as e:
            raise DataError(f"Failed to save Parquet: {e}")
    
    def save_sqlite(
        self,
        df: pd.DataFrame,
        db_path: Path,
        table_name: str,
        if_exists: str = 'replace'
    ) -> None:
        """
        Save to SQLite.
        
        Args:
            df: DataFrame to save
            db_path: Path to database
            table_name: Table name
            if_exists: How to behave if table exists ('fail', 'replace', 'append')
        """
        try:
            db_path = Path(db_path)
            ensure_path(db_path)
            
            with sqlite3.connect(db_path) as conn:
                df.to_sql(table_name, conn, if_exists=if_exists, index=False)
            
            logger.info(f"Saved {len(df)} rows to SQLite table '{table_name}'")
        except Exception as e:
            raise DataError(f"Failed to save to SQLite: {e}")
    
    def save(
        self,
        df: pd.DataFrame,
        filepath: Path,
        format: str = 'parquet',
        **kwargs
    ) -> None:
        """
        Save data to file.
        
        Args:
            df: DataFrame
            filepath: Output filepath
            format: Format ('csv', 'parquet', 'sqlite')
            **kwargs: Format-specific arguments
        """
        if format == 'csv':
            self.save_csv(df, filepath, **kwargs)
        elif format == 'parquet':
            self.save_parquet(df, filepath, **kwargs)
        elif format == 'sqlite':
            self.save_sqlite(df, filepath, **kwargs)
        else:
            raise DataError(f"Unsupported format: {format}")


__all__ = [
    # Classes
    'DataLoader',
    'DataSaver',
    'DataQualityReport',
    'TimeGapReport',
    'DataSource',
    'DataFrequency',
    
    # Exceptions
    'DataError',
    'DataLoadError',
    'DataValidationError',
    'DataCleaningError',
    
    # Functions
    'ensure_naive_utc_timestamp',
    'ensure_naive_utc_series',
    'drop_broker_noise_columns',
    'clean_ohlcv_data',
    'validate_data_quality',
    'detect_time_gaps',
    'detect_spikes',
    'resample_ohlcv',
]
