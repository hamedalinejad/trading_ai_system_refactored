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
from threading import Lock

import numpy as np
import pandas as pd

try:
    from trading_ai_system.core import (
        logger, TradingSystemError, DataError, ConfigError,
        get_global_config, DATA_PATH_CONFIG, ensure_path,
        validate_dataframe, validate_numeric_columns
    )
except ImportError:
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


class DataLoadError(DataError):
    pass

class DataValidationError(DataError):
    pass

class DataCleaningError(DataError):
    pass


class DataSource(str, Enum):
    CSV = "csv"
    PARQUET = "parquet"
    SQLITE = "sqlite"
    CCXT = "ccxt"
    API = "api"


class DataFrequency(str, Enum):
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
    passed: bool = True
    row_count: int = 0
    time_span: str = ""
    ohlc_missing_pct: Dict[str, float] = field(default_factory=dict)
    volume_stats: Dict[str, Any] = field(default_factory=dict)
    price_range: Dict[str, Dict[str, float]] = field(default_factory=dict)
    quality_warnings: List[str] = field(default_factory=list)
    quality_score: float = 100.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "row_count": self.row_count,
            "time_span": self.time_span,
            "ohlc_missing_pct": self.ohlc_missing_pct.copy(),
            "volume_stats": self.volume_stats.copy(),
            "price_range": {k: v.copy() for k, v in self.price_range.items()},
            "quality_warnings": self.quality_warnings.copy(),
            "quality_score": self.quality_score
        }


@dataclass
class TimeGapReport:
    total_gaps: int = 0
    largest_gap: Optional[Dict[str, Any]] = None
    gap_locations: List[Dict[str, Any]] = field(default_factory=list)
    has_anomalies: bool = False
    coverage_pct: float = 100.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_gaps": self.total_gaps,
            "largest_gap": self.largest_gap.copy() if self.largest_gap else None,
            "gap_locations": [g.copy() for g in self.gap_locations],
            "has_anomalies": self.has_anomalies,
            "coverage_pct": self.coverage_pct
        }


def ensure_naive_utc_timestamp(ts: pd.Timestamp) -> pd.Timestamp:
    if ts is pd.NaT or pd.isna(ts):
        return pd.NaT
    
    if isinstance(ts, pd.Timestamp):
        if ts.tz is not None:
            ts = ts.tz_convert('UTC').tz_localize(None)
        return ts
    
    return pd.NaT


def ensure_naive_utc_series(ts_series: pd.Series) -> pd.Series:
    if not isinstance(ts_series, pd.Series):
        return ts_series
    
    try:
        if ts_series.dtype == 'object':
            ts_series = pd.to_datetime(ts_series)
        
        if hasattr(ts_series.dtype, 'tz') and ts_series.dtype.tz is not None:
            ts_series = ts_series.dt.tz_convert('UTC').dt.tz_localize(None)
        
        return ts_series
    except Exception as e:
        logger.warning(f"Failed to convert timestamp series: {e}")
        return ts_series


def drop_broker_noise_columns(df: pd.DataFrame) -> pd.DataFrame:
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


def clean_ohlcv_data(
    df: pd.DataFrame,
    max_ffill_periods: int = 3,
    zscore_threshold: float = 5.0,
    volume_min_pct: float = 0.01,
) -> pd.DataFrame:
    if not isinstance(df, pd.DataFrame) or df.empty:
        raise DataCleaningError("Input DataFrame is empty or invalid")
    
    df_clean = df.copy()
    df_clean = drop_broker_noise_columns(df_clean)
    
    required_cols = ['timestamp', 'open', 'high', 'low', 'close']
    missing_cols = [col for col in required_cols if col not in df_clean.columns]
    if missing_cols:
        raise DataCleaningError(f"Required columns missing: {missing_cols}")
    
    initial_count = len(df_clean)
    logger.info(f"clean_ohlcv_data: processing {initial_count:,} rows")
    
    df_clean['timestamp'] = ensure_naive_utc_series(df_clean['timestamp'])
    
    df_clean = df_clean.drop_duplicates(subset=['timestamp'], keep='first')
    removed_dups = initial_count - len(df_clean)
    if removed_dups > 0:
        logger.debug(f"Removed {removed_dups} duplicate rows")
    
    valid_ohlc = (df_clean['low'] <= df_clean['close']) & \
                 (df_clean['high'] >= df_clean['close']) & \
                 (df_clean['low'] <= df_clean['open']) & \
                 (df_clean['high'] >= df_clean['open']) & \
                 (df_clean['low'] <= df_clean['high'])
    
    invalid_count = (~valid_ohlc).sum()
    if invalid_count > 0:
        df_clean = df_clean[valid_ohlc].copy()
        logger.warning(f"Removed {invalid_count} structurally invalid OHLC rows")
    
    for col in ['open', 'high', 'low', 'close']:
        if col in df_clean.columns:
            nan_count = df_clean[col].isna().sum()
            if nan_count > 0:
                df_clean[col] = df_clean[col].fillna(method='ffill', limit=max_ffill_periods)
                remaining_nan = df_clean[col].isna().sum()
                if remaining_nan > 0:
                    df_clean = df_clean[df_clean[col].notna()].copy()
                    logger.warning(f"Removed {remaining_nan} rows with irreplaceable NaN in '{col}'")
    
    for col in ['open', 'high', 'low', 'close']:
        if col in df_clean.columns:
            numeric_df = df_clean[[col]].apply(pd.to_numeric, errors='coerce')
            mean = numeric_df[col].mean()
            std = numeric_df[col].std()
            
            if std > 0:
                z_scores = np.abs((numeric_df[col] - mean) / std)
                outliers = z_scores > zscore_threshold
                if outliers.any():
                    df_clean.loc[outliers, col] = mean
                    logger.debug(f"Clipped {outliers.sum()} outliers in '{col}'")
    
    if 'volume' in df_clean.columns:
        vol_median = df_clean['volume'][df_clean['volume'] > 0].median()
        if pd.isna(vol_median) or vol_median == 0:
            vol_median = 1.0
        
        vol_min_threshold = vol_median * volume_min_pct
        df_clean.loc[(df_clean['volume'] > 0) & (df_clean['volume'] < vol_min_threshold), 'volume'] = 0
        df_clean.loc[df_clean['volume'].isna(), 'volume'] = 0
        
        logger.debug(f"Cleaned volume data: median={vol_median:.2f}, min_threshold={vol_min_threshold:.2f}")
    
    df_clean = df_clean.sort_values('timestamp').reset_index(drop=True)
    
    final_count = len(df_clean)
    removed_total = initial_count - final_count
    logger.info(f"clean_ohlcv_data complete: {final_count:,} rows remaining ({removed_total:,} removed)")
    
    return df_clean


def validate_data_quality(
    df: pd.DataFrame,
    max_missing_pct: float = 5.0,
    warn_on_sparse: bool = True,
) -> DataQualityReport:
    report = DataQualityReport()
    
    if not isinstance(df, pd.DataFrame) or df.empty:
        report.passed = False
        report.quality_warnings.append("DataFrame is empty or invalid")
        return report
    
    report.row_count = len(df)
    
    try:
        if 'timestamp' in df.columns:
            ts = pd.to_datetime(df['timestamp'], errors='coerce')
            if ts.notna().sum() > 0:
                valid_ts = ts[ts.notna()]
                if len(valid_ts) > 1:
                    report.time_span = str(valid_ts.max() - valid_ts.min())
                    td = valid_ts.max() - valid_ts.min()
                    
                    if td.total_seconds() < 3600:
                        report.quality_warnings.append("Data span < 1 hour")
                        report.quality_score -= 15.0
    except Exception as e:
        report.quality_warnings.append(f"Timestamp parsing error: {e}")
    
    for col in ["open", "high", "low", "close"]:
        if col in df.columns:
            missing_pct = (df[col].isna().sum() / len(df)) * 100
            report.ohlc_missing_pct[col] = round(missing_pct, 2)
            
            if missing_pct > max_missing_pct:
                report.passed = False
                report.quality_warnings.append(f"High missing in '{col}': {missing_pct:.1f}%")
                report.quality_score -= 10.0
            
            valid_vals = df[col][df[col].notna()]
            if len(valid_vals) > 0:
                report.price_range[col] = {
                    "min": float(valid_vals.min()),
                    "max": float(valid_vals.max()),
                }
    
    if "volume" in df.columns:
        vol_data = df["volume"][(df["volume"] > 0) & (df["volume"].notna())]
        report.volume_stats = {
            "min": float(vol_data.min()) if len(vol_data) > 0 else 0.0,
            "max": float(vol_data.max()) if len(vol_data) > 0 else 0.0,
            "median": float(vol_data.median()) if len(vol_data) > 0 else 0.0,
            "zero_count": int((df["volume"] == 0).sum()),
        }
        
        if warn_on_sparse and len(vol_data) > 0 and vol_data.median() < 1.0:
            report.quality_warnings.append("Sparse volume (median < 1.0)")
            report.quality_score -= 5.0
    
    for col in ["open", "high", "low", "close"]:
        if col in df.columns:
            if np.isinf(df[col]).any():
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


def detect_time_gaps(
    df: pd.DataFrame,
    expected_interval_minutes: int = 60,
    gap_threshold_multiplier: float = 1.5,
) -> TimeGapReport:
    report = TimeGapReport()
    
    if not isinstance(df, pd.DataFrame) or len(df) < 2:
        return report
    
    if "timestamp" not in df.columns:
        return report
    
    try:
        timestamps = pd.to_datetime(df["timestamp"], errors='coerce')
        valid_mask = timestamps.notna()
        
        if valid_mask.sum() < 2:
            return report
        
        timestamps = timestamps[valid_mask]
        diffs = timestamps.diff().dt.total_seconds() / 60
        
        if expected_interval_minutes <= 0:
            expected_interval_minutes = 60
        
        expected_gap_threshold = expected_interval_minutes * gap_threshold_multiplier
        gap_indices = np.where((diffs > expected_interval_minutes) & (diffs.notna()))[0]
        
        if len(gap_indices) == 0:
            report.coverage_pct = 100.0
            return report
        
        report.total_gaps = len(gap_indices)
        
        for idx in gap_indices:
            gap_minutes = float(diffs.iloc[idx])
            is_anomaly = gap_minutes > expected_gap_threshold
            
            gap_info = {
                "index": int(idx),
                "start_ts": str(timestamps.iloc[idx - 1]) if idx > 0 else "N/A",
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
                report.largest_gap = gap_info.copy()
        
        total_time_span = (timestamps.iloc[-1] - timestamps.iloc[0]).total_seconds() / 60
        if total_time_span > 0:
            expected_candles = total_time_span / expected_interval_minutes
            actual_candles = len(timestamps) - 1
            if expected_candles > 0:
                report.coverage_pct = (actual_candles / expected_candles) * 100.0
        
        if report.has_anomalies:
            anomaly_count = sum(1 for g in report.gap_locations if g['is_anomaly'])
            logger.warning(
                f"detect_time_gaps: Found {report.total_gaps} gaps, "
                f"{anomaly_count} anomalies"
            )
        
    except Exception as e:
        logger.error(f"detect_time_gaps error: {e}")
    
    return report


class DataLoader:
    _lock = Lock()
    
    @staticmethod
    def load_csv(path: str, **kwargs) -> pd.DataFrame:
        try:
            p = Path(path)
            if not p.exists():
                raise DataLoadError(f"CSV file not found: {path}")
            
            df = pd.read_csv(p, **kwargs)
            if df.empty:
                logger.warning(f"CSV file is empty: {path}")
            else:
                logger.info(f"Loaded {len(df):,} rows from {path}")
            return df
        except FileNotFoundError:
            raise DataLoadError(f"CSV file not found: {path}")
        except Exception as e:
            raise DataLoadError(f"Failed to load CSV {path}: {e}")
    
    @staticmethod
    def load_parquet(path: str, **kwargs) -> pd.DataFrame:
        try:
            p = Path(path)
            if not p.exists():
                raise DataLoadError(f"Parquet file not found: {path}")
            
            df = pd.read_parquet(p, **kwargs)
            if df.empty:
                logger.warning(f"Parquet file is empty: {path}")
            else:
                logger.info(f"Loaded {len(df):,} rows from {path}")
            return df
        except FileNotFoundError:
            raise DataLoadError(f"Parquet file not found: {path}")
        except Exception as e:
            raise DataLoadError(f"Failed to load Parquet {path}: {e}")
    
    @staticmethod
    def load(path: str, source: Union[DataSource, str] = DataSource.CSV, **kwargs) -> pd.DataFrame:
        path = str(path)
        
        if isinstance(source, str):
            try:
                source = DataSource(source.lower())
            except ValueError:
                raise DataLoadError(f"Unsupported data source: {source}")
        
        if source == DataSource.CSV:
            return DataLoader.load_csv(path, **kwargs)
        elif source == DataSource.PARQUET:
            return DataLoader.load_parquet(path, **kwargs)
        else:
            raise DataLoadError(f"Unsupported data source: {source}")


class DataSaver:
    _lock = Lock()
    
    @staticmethod
    def save_csv(df: pd.DataFrame, path: str, index: bool = False, **kwargs) -> None:
        if not isinstance(df, pd.DataFrame):
            raise DataError("Input must be a pandas DataFrame")
        
        try:
            ensure_path(path)
            df.to_csv(path, index=index, **kwargs)
            logger.info(f"Saved {len(df):,} rows to {path}")
        except Exception as e:
            raise DataError(f"Failed to save CSV {path}: {e}")
    
    @staticmethod
    def save_parquet(df: pd.DataFrame, path: str, **kwargs) -> None:
        if not isinstance(df, pd.DataFrame):
            raise DataError("Input must be a pandas DataFrame")
        
        try:
            ensure_path(path)
            df.to_parquet(path, **kwargs)
            logger.info(f"Saved {len(df):,} rows to {path}")
        except Exception as e:
            raise DataError(f"Failed to save Parquet {path}: {e}")
    
    @staticmethod
    def save(df: pd.DataFrame, path: str, fmt: str = "csv", **kwargs) -> None:
        if not isinstance(df, pd.DataFrame):
            raise DataError("Input must be a pandas DataFrame")
        
        if fmt.lower() == "csv":
            DataSaver.save_csv(df, path, **kwargs)
        elif fmt.lower() == "parquet":
            DataSaver.save_parquet(df, path, **kwargs)
        else:
            raise DataError(f"Unsupported format: {fmt}")


__all__ = [
    'DataSource', 'DataFrequency',
    'DataQualityReport', 'TimeGapReport', 'DataLoader', 'DataSaver',
    'DataLoadError', 'DataValidationError', 'DataCleaningError',
    'ensure_naive_utc_timestamp', 'ensure_naive_utc_series',
    'drop_broker_noise_columns', 'clean_ohlcv_data',
    'validate_data_quality', 'detect_time_gaps',
]
