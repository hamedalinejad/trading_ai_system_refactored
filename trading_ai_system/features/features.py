"""
Trading AI System - Features Module (v2.0)
Feature engineering, technical indicators, and pattern detection.

Key Improvements:
- Fixed RSI min_periods issue
- Proper NaN/Inf handling
- Optimized copy operations
- Centralized feature registration
- Timeframe-aware period calculation
- Comprehensive error handling
- Full documentation
"""

import sys
import logging
from typing import Dict, Any, Optional, List, Tuple, Union
from dataclasses import dataclass, field
from threading import Lock
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from trading_ai_system.core import (
        get_logger, 
        get_global_config,
        register_feature,
    )
    logger = get_logger(__name__)
except ImportError:
    logger = logging.getLogger(__name__)
    
    def get_global_config():
        return {}
    
    def register_feature(*args, **kwargs):
        pass

try:
    from trading_ai_system.discovery import Discovery
    HAS_DISCOVERY = True
except ImportError:
    HAS_DISCOVERY = False
    logger.warning("Discovery module not available")


class FeatureEngineeringError(Exception):
    """Feature engineering error"""
    pass


def _get_scaler(scaler_type: str = 'standard'):
    """Get scaler instance based on type"""
    if scaler_type == 'robust':
        from sklearn.preprocessing import RobustScaler
        return RobustScaler()
    elif scaler_type == 'minmax':
        from sklearn.preprocessing import MinMaxScaler
        return MinMaxScaler()
    else:
        from sklearn.preprocessing import StandardScaler
        return StandardScaler()


def _interpolate_missing_values(df: pd.DataFrame, timeframe: str = '1h', fill_method: str = 'interpolate') -> pd.DataFrame:
    """Handle missing values with reindex and interpolation"""
    if df.empty:
        return df
    
    try:
        if fill_method == 'interpolate':
            freq_map = {
                '1m': '1min', '5m': '5min', '15m': '15min', '30m': '30min',
                '1h': '1h', '4h': '4h', '1d': '1d', '1w': '1w', '1M': '1MS'
            }
            freq = freq_map.get(timeframe, '1h')
            
            full_index = pd.date_range(start=df.index.min(), end=df.index.max(), freq=freq)
            df_reindexed = df.reindex(full_index)
            
            ohlcv_cols = ['open', 'high', 'low', 'close', 'volume']
            available_cols = [c for c in ohlcv_cols if c in df_reindexed.columns]
            
            for col in available_cols:
                df_reindexed[col] = df_reindexed[col].interpolate(method='time', limit_direction='both')
            
            return df_reindexed
    except Exception as e:
        logger.warning(f"Interpolation failed: {e}")
    
    return df


class FeatureRegistrationError(Exception):
    """Feature registration error"""
    pass


@dataclass
class FeatureMetadata:
    """Feature metadata for tracking"""
    name: str
    category: str
    requires_shift: bool = False
    lookback: int = 1
    description: str = ""
    min_bars: int = 1
    discovery_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category,
            "requires_shift": self.requires_shift,
            "lookback": self.lookback,
            "description": self.description,
            "min_bars": self.min_bars,
            "discovery_score": self.discovery_score
        }


class FeatureSelector:
    """Select best features based on discovery results"""
    
    def __init__(self):
        self.selected_features: Dict[str, FeatureMetadata] = {}
        self.discovery_enabled = HAS_DISCOVERY
        self._lock = Lock()
    
    def load_discovered_features(self, discovery_file: Path) -> None:
        """Load features from discovery analysis file"""
        if not self.discovery_enabled:
            logger.warning("Discovery module not available")
            return
        
        try:
            import json
            with open(discovery_file, 'r') as f:
                data = json.load(f)
            
            top_indicators = data.get('top_indicators', [])
            
            with self._lock:
                for indicator_data in top_indicators:
                    name = indicator_data.get('name')
                    score = indicator_data.get('composite_score', 0.0)
                    category = indicator_data.get('category', 'momentum')
                    
                    if name and score > 0:
                        meta = FeatureMetadata(
                            name=name,
                            category=category,
                            discovery_score=score
                        )
                        self.selected_features[name] = meta
            
            logger.info(f"Loaded {len(self.selected_features)} discovered features")
        except FileNotFoundError:
            logger.warning(f"Discovery file not found: {discovery_file}")
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error loading discovered features: {e}")
    
    def get_selected_features(self) -> Dict[str, FeatureMetadata]:
        """Get selected features"""
        with self._lock:
            return self.selected_features.copy()
    
    def is_feature_selected(self, feature_name: str) -> bool:
        """Check if feature was selected by discovery"""
        with self._lock:
            return feature_name in self.selected_features
    
    def sync_with_discovery(self, discovery: 'Discovery') -> None:
        """Sync selected features from Discovery instance"""
        if not hasattr(discovery, '_indicator_metrics'):
            return
        
        with self._lock:
            for name, metric in discovery._indicator_metrics.items():
                meta = FeatureMetadata(
                    name=name,
                    category=metric.category.value if hasattr(metric.category, 'value') else str(metric.category),
                    discovery_score=metric.composite_score()
                )
                self.selected_features[name] = meta
        
        logger.info(f"Synced {len(self.selected_features)} features from Discovery")


feature_selector = FeatureSelector()


# ==================== INDICATOR CALCULATION FUNCTIONS ====================

def compute_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate Relative Strength Index (RSI).
    
    Args:
        close: Close price series
        period: RSI period (default 14)
        
    Returns:
        RSI values (0-100)
        
    Note:
        Uses min_periods=period for accurate RSI calculation (Fix #1.1)
    """
    if not isinstance(close, pd.Series) or len(close) < period:
        return pd.Series(np.nan, index=close.index if isinstance(close, pd.Series) else None)
    
    try:
        close = close.astype(float)
        delta = close.diff()
        
        # Fix #1.1: Use min_periods=period for accurate calculation
        gain = delta.where(delta > 0, 0).rolling(window=period, min_periods=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period, min_periods=period).mean()
        
        rs = gain / (loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.fillna(50.0)
    except (ValueError, TypeError) as e:
        logger.error(f"Error computing RSI: {e}")
        return pd.Series(np.nan, index=close.index)


def compute_macd(
    close: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate MACD (Moving Average Convergence Divergence).
    
    Args:
        close: Close price series
        fast: Fast EMA period (default 12)
        slow: Slow EMA period (default 26)
        signal: Signal line period (default 9)
        
    Returns:
        Tuple of (MACD, Signal line, Histogram)
    """
    if not isinstance(close, pd.Series) or len(close) < slow:
        idx = close.index if isinstance(close, pd.Series) else None
        return (
            pd.Series(np.nan, index=idx),
            pd.Series(np.nan, index=idx),
            pd.Series(np.nan, index=idx)
        )
    
    try:
        close = close.astype(float)
        ema_fast = close.ewm(span=fast, adjust=False).mean()
        ema_slow = close.ewm(span=slow, adjust=False).mean()
        
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line
        
        return macd, signal_line, histogram
    except (ValueError, TypeError) as e:
        logger.error(f"Error computing MACD: {e}")
        idx = close.index if isinstance(close, pd.Series) else None
        return (
            pd.Series(np.nan, index=idx),
            pd.Series(np.nan, index=idx),
            pd.Series(np.nan, index=idx)
        )


def compute_bollinger_bands(
    close: pd.Series,
    period: int = 20,
    num_std: float = 2.0
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate Bollinger Bands.
    
    Args:
        close: Close price series
        period: Rolling window period (default 20)
        num_std: Number of standard deviations (default 2.0)
        
    Returns:
        Tuple of (Upper band, Middle band, Lower band)
    """
    if not isinstance(close, pd.Series) or len(close) < period:
        idx = close.index if isinstance(close, pd.Series) else None
        return (
            pd.Series(np.nan, index=idx),
            pd.Series(np.nan, index=idx),
            pd.Series(np.nan, index=idx)
        )
    
    try:
        close = close.astype(float)
        middle = close.rolling(window=period, min_periods=1).mean()
        std = close.rolling(window=period, min_periods=1).std()
        std = std.fillna(0)
        
        upper = middle + (std * num_std)
        lower = middle - (std * num_std)
        
        return upper, middle, lower
    except (ValueError, TypeError) as e:
        logger.error(f"Error computing Bollinger Bands: {e}")
        idx = close.index if isinstance(close, pd.Series) else None
        return (
            pd.Series(np.nan, index=idx),
            pd.Series(np.nan, index=idx),
            pd.Series(np.nan, index=idx)
        )


def compute_atr(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14
) -> pd.Series:
    """
    Calculate Average True Range (ATR).
    
    Args:
        high: High price series
        low: Low price series
        close: Close price series
        period: ATR period (default 14)
        
    Returns:
        ATR values
    """
    if not all(isinstance(s, pd.Series) for s in [high, low, close]):
        return pd.Series(np.nan, index=high.index if isinstance(high, pd.Series) else None)
    
    if len(high) < period:
        return pd.Series(np.nan, index=high.index)
    
    try:
        high = high.astype(float)
        low = low.astype(float)
        close = close.astype(float)
        
        # Fix #2.2: Use np.maximum instead of pd.concat for efficiency
        tr1 = high - low
        tr2 = (high - close.shift(1)).abs()
        tr3 = (low - close.shift(1)).abs()
        
        tr = np.maximum(tr1.values, np.maximum(tr2.values, tr3.values))
        tr = pd.Series(tr, index=high.index)
        
        atr = tr.rolling(window=period, min_periods=1).mean()
        
        return atr.fillna(tr.mean()) if tr.mean() > 0 else atr
    except (ValueError, TypeError) as e:
        logger.error(f"Error computing ATR: {e}")
        return pd.Series(np.nan, index=high.index)


def compute_stochastic(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14,
    smooth_k: int = 3,
    smooth_d: int = 3
) -> Tuple[pd.Series, pd.Series]:
    """
    Calculate Stochastic Oscillator.
    
    Args:
        high: High price series
        low: Low price series
        close: Close price series
        period: Stochastic period (default 14)
        smooth_k: K line smoothing period (default 3)
        smooth_d: D line smoothing period (default 3)
        
    Returns:
        Tuple of (K%, D%)
    """
    if not all(isinstance(s, pd.Series) for s in [high, low, close]):
        idx = high.index if isinstance(high, pd.Series) else None
        return pd.Series(np.nan, index=idx), pd.Series(np.nan, index=idx)
    
    if len(high) < period:
        idx = high.index
        return pd.Series(np.nan, index=idx), pd.Series(np.nan, index=idx)
    
    try:
        high = high.astype(float)
        low = low.astype(float)
        close = close.astype(float)
        
        lowest_low = low.rolling(window=period, min_periods=1).min()
        highest_high = high.rolling(window=period, min_periods=1).max()
        
        range_val = highest_high - lowest_low
        range_val = range_val.replace(0, 1e-10)
        
        k_percent = 100 * (close - lowest_low) / (range_val + 1e-10)
        k_smooth = k_percent.rolling(window=smooth_k, min_periods=1).mean()
        d_smooth = k_smooth.rolling(window=smooth_d, min_periods=1).mean()
        
        return k_smooth.fillna(50.0), d_smooth.fillna(50.0)
    except (ValueError, TypeError) as e:
        logger.error(f"Error computing Stochastic: {e}")
        idx = high.index if isinstance(high, pd.Series) else None
        return pd.Series(np.nan, index=idx), pd.Series(np.nan, index=idx)


# ==================== PATTERN DETECTION FUNCTIONS ====================

def detect_engulfing(df: pd.DataFrame) -> pd.DataFrame:
    """
    Detect engulfing candlestick patterns.
    
    Args:
        df: DataFrame with OHLC data
        
    Returns:
        DataFrame with engulfing pattern columns added
    """
    if not isinstance(df, pd.DataFrame) or df.empty:
        return df
    
    if not all(c in df.columns for c in ['open', 'close', 'high', 'low']):
        return df
    
    try:
        df_work = df[['open', 'close', 'high', 'low']].astype(float)
        
        prev_open = df_work["open"].shift(1)
        prev_close = df_work["close"].shift(1)
        prev_body = (prev_close - prev_open).abs()
        curr_body = (df_work["close"] - df_work["open"]).abs()
        
        bullish = (
            (prev_close < prev_open) &
            (df_work["close"] > df_work["open"]) &
            (df_work["open"] <= prev_close) &
            (df_work["close"] >= prev_open) &
            (curr_body > prev_body)
        ).astype(int).fillna(0)
        
        bearish = (
            (prev_close > prev_open) &
            (df_work["close"] < df_work["open"]) &
            (df_work["open"] >= prev_close) &
            (df_work["close"] <= prev_open) &
            (curr_body > prev_body)
        ).astype(int).fillna(0)
        
        df["engulfing_bullish"] = bullish
        df["engulfing_bearish"] = bearish
        
        return df
    except (ValueError, TypeError, KeyError) as e:
        logger.error(f"Error in engulfing detection: {e}")
        return df


def detect_doji(df: pd.DataFrame, threshold: float = 0.1) -> pd.DataFrame:
    """
    Detect doji candlestick patterns.
    
    Args:
        df: DataFrame with OHLC data
        threshold: Body-to-range ratio threshold (default 0.1)
        
    Returns:
        DataFrame with doji pattern columns added
    """
    if not isinstance(df, pd.DataFrame) or df.empty:
        return df
    
    if not all(c in df.columns for c in ['open', 'close', 'high', 'low']):
        return df
    
    if threshold <= 0 or threshold > 1:
        threshold = 0.1
    
    try:
        df_work = df[['open', 'close', 'high', 'low']].astype(float)
        
        body = (df_work["close"] - df_work["open"]).abs()
        range_ = df_work["high"] - df_work["low"]
        range_ = range_.replace(0, 1e-10)
        
        df["is_doji"] = ((body / (range_ + 1e-10)) < threshold).astype(int).fillna(0)
        df["doji_star"] = (
            (df["is_doji"] == 1) &
            (df_work["low"] < df_work["low"].shift(1))
        ).astype(int).fillna(0)
        
        return df
    except (ValueError, TypeError, KeyError) as e:
        logger.error(f"Error in doji detection: {e}")
        return df


def detect_inside_bar(df: pd.DataFrame) -> pd.DataFrame:
    """
    Detect inside bar (narrow range) patterns.
    
    Args:
        df: DataFrame with OHLC data
        
    Returns:
        DataFrame with inside bar pattern columns added
    """
    if not isinstance(df, pd.DataFrame) or df.empty:
        return df
    
    if not all(c in df.columns for c in ['high', 'low', 'close']):
        return df
    
    try:
        df_work = df[['high', 'low', 'close']].astype(float)
        
        prev_high = df_work["high"].shift(1)
        prev_low = df_work["low"].shift(1)
        
        df["inside_bar"] = (
            (df_work["high"] <= prev_high) &
            (df_work["low"] >= prev_low)
        ).astype(int).fillna(0)
        
        inside_bar_prev = df["inside_bar"].shift(1).fillna(0)
        
        df["inside_bar_breakout_up"] = (
            (inside_bar_prev == 1) &
            (df_work["close"] > prev_high)
        ).astype(int).fillna(0)
        
        df["inside_bar_breakout_down"] = (
            (inside_bar_prev == 1) &
            (df_work["close"] < prev_low)
        ).astype(int).fillna(0)
        
        return df
    except (ValueError, TypeError, KeyError) as e:
        logger.error(f"Error in inside bar detection: {e}")
        return df


def detect_three_bar_patterns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Detect three-bar patterns (three white soldiers, three black crows).
    
    Args:
        df: DataFrame with OHLC data
        
    Returns:
        DataFrame with pattern columns added
    """
    if not isinstance(df, pd.DataFrame) or df.empty:
        return df
    
    if not all(c in df.columns for c in ['open', 'close']):
        return df
    
    try:
        df_work = df[['open', 'close']].astype(float)
        
        bullish_1 = df_work["close"] > df_work["open"]
        bullish_2 = df_work["close"].shift(1) > df_work["open"].shift(1)
        bullish_3 = df_work["close"].shift(2) > df_work["open"].shift(2)
        
        higher_close_1 = df_work["close"] > df_work["close"].shift(1)
        higher_close_2 = df_work["close"].shift(1) > df_work["close"].shift(2)
        
        df["three_white_soldiers"] = (
            bullish_1 & bullish_2 & bullish_3 &
            higher_close_1 & higher_close_2
        ).astype(int).fillna(0)
        
        bearish_1 = df_work["close"] < df_work["open"]
        bearish_2 = df_work["close"].shift(1) < df_work["open"].shift(1)
        bearish_3 = df_work["close"].shift(2) < df_work["open"].shift(2)
        
        lower_close_1 = df_work["close"] < df_work["close"].shift(1)
        lower_close_2 = df_work["close"].shift(1) < df_work["close"].shift(2)
        
        df["three_black_crows"] = (
            bearish_1 & bearish_2 & bearish_3 &
            lower_close_1 & lower_close_2
        ).astype(int).fillna(0)
        
        return df
    except (ValueError, TypeError, KeyError) as e:
        logger.error(f"Error in three bar pattern detection: {e}")
        return df


def detect_morning_evening_star(df: pd.DataFrame) -> pd.DataFrame:
    """
    Detect morning star and evening star patterns.
    
    Args:
        df: DataFrame with OHLC data
        
    Returns:
        DataFrame with star pattern columns added
    """
    if not isinstance(df, pd.DataFrame) or df.empty:
        return df
    
    if not all(c in df.columns for c in ['open', 'close']):
        return df
    
    try:
        df_work = df[['open', 'close']].astype(float)
        
        body_1 = (df_work["close"].shift(2) - df_work["open"].shift(2)).abs()
        body_2 = (df_work["close"].shift(1) - df_work["open"].shift(1)).abs()
        
        df["morning_star"] = (
            (df_work["close"].shift(2) < df_work["open"].shift(2)) &
            (body_2 < body_1 * 0.3) &
            (df_work["close"] > df_work["open"]) &
            (df_work["close"] > (df_work["open"].shift(2) + df_work["close"].shift(2)) / 2)
        ).astype(int).fillna(0)
        
        df["evening_star"] = (
            (df_work["close"].shift(2) > df_work["open"].shift(2)) &
            (body_2 < body_1 * 0.3) &
            (df_work["close"] < df_work["open"]) &
            (df_work["close"] < (df_work["open"].shift(2) + df_work["close"].shift(2)) / 2)
        ).astype(int).fillna(0)
        
        return df
    except (ValueError, TypeError, KeyError) as e:
        logger.error(f"Error in star pattern detection: {e}")
        return df


# ==================== RETURNS & MOMENTUM FEATURES ====================

def calculate_returns(df: pd.DataFrame, tf: str = "1h") -> pd.DataFrame:
    """
    Calculate return-based features with timeframe adaptation.
    
    Args:
        df: DataFrame with close prices
        tf: Timeframe (default "1h")
        
    Returns:
        DataFrame with return features added
        
    Note:
        Fix #1.5: Uses timeframe to calculate adaptive periods
    """
    if not isinstance(df, pd.DataFrame) or df.empty:
        return df
    
    if 'close' not in df.columns:
        return df
    
    try:
        df_work = df[['close']].astype(float)
        
        # Fix #1.5: Adapt periods based on timeframe
        bars_per_day = {
            '1m': 1440, '5m': 288, '15m': 96, '30m': 48, '1h': 24,
            '4h': 6, '1d': 1, '1w': 0.2, '1M': 0.043
        }.get(tf, 24)
        
        period_5bar = max(5, int(bars_per_day * 5 / 24))
        period_20bar = max(20, int(bars_per_day * 20 / 24))
        
        df["return_1bar"] = df_work["close"].pct_change(1).fillna(0)
        df["return_5bar"] = df_work["close"].pct_change(period_5bar).fillna(0)
        df["return_20bar"] = df_work["close"].pct_change(period_20bar).fillna(0)
        
        log_ret = np.log(df_work["close"] / df_work["close"].shift(1))
        df["log_return_1bar"] = log_ret.replace([np.inf, -np.inf], 0).fillna(0)
        
        df["acceleration"] = df["return_1bar"] - df["return_1bar"].shift(1)
        df["acceleration"] = df["acceleration"].fillna(0)
        
        df["jerk"] = df["acceleration"] - df["acceleration"].shift(1)
        df["jerk"] = df["jerk"].fillna(0)
        
        df["price_velocity"] = df["return_1bar"].rolling(5, min_periods=1).sum().fillna(0)
        
        return df
    except (ValueError, TypeError, KeyError) as e:
        logger.error(f"Error computing returns: {e}")
        return df


# ==================== MAIN FEATURE ENGINEERING FUNCTION ====================

def engineer_features_for_timeframe(
    df: pd.DataFrame,
    timeframe: str = "1h",
    compute_advanced: bool = True,
    use_discovery: bool = True,
    discovery_config: Optional[Dict[str, Any]] = None,
    normalize: bool = False,
    scaler_type: str = 'standard',
    fill_missing: str = 'interpolate',
    discovery_top_n: int = 10
) -> Tuple[pd.DataFrame, Dict[str, FeatureMetadata]]:
    """
    Engineer all features for a given timeframe.
    
    Args:
        df: Input DataFrame with OHLCV data
        timeframe: Trading timeframe (default "1h")
        compute_advanced: Whether to compute advanced indicators (default True)
        use_discovery: Whether to use discovery module (default True)
        discovery_config: Discovery configuration dict
        normalize: Whether to normalize features (default False)
        scaler_type: Type of scaler ('standard', 'robust', 'minmax') (default 'standard')
        fill_missing: Method for filling missing values ('interpolate', 'ffill') (default 'interpolate')
        discovery_top_n: Top N features to select from discovery (default 10)
        
    Returns:
        Tuple of (enhanced DataFrame, feature metadata dict with discovery scores)
        
    Raises:
        FeatureEngineeringError: If required columns missing or invalid data
        
    Note:
        Implements multiple bug fixes and improvements:
        - Fix #1.2: Proper NaN handling with fillna
        - Fix #1.3: Single df.copy() at start
        - Fix #1.4: Centralized register_feature calls
        - Fix #1.6: Epsilon in divisions to prevent Inf
        - Enhancement #1: Discovery-driven feature selection
        - Enhancement #2: Advanced normalization with RobustScaler
        - Enhancement #3: Intelligent missing value handling with interpolation
    """
    
    if not isinstance(df, pd.DataFrame) or df.empty:
        raise FeatureEngineeringError("Empty or invalid DataFrame")
    
    required_cols = ['open', 'high', 'low', 'close', 'volume']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise FeatureEngineeringError(f"Missing required columns: {missing}")
    
    try:
        # Fix #1.3: Single copy operation at start
        df_feat = df.copy()
        df_feat = df_feat.astype({col: float for col in required_cols}, errors='ignore')
        
        # Enhancement #3: Handle missing values with interpolation
        if fill_missing == 'interpolate' and df_feat.index.dtype == 'datetime64[ns]':
            df_feat = _interpolate_missing_values(df_feat, timeframe, fill_missing)
        
        logger.info(f"engineer_features: {len(df_feat)} rows, timeframe={timeframe}")
        
        # Track generated features for centralized registration
        generated_features = []
        
        # Pre-phase: Discover indicators first if enabled
        discovered_features = {}
        if use_discovery and HAS_DISCOVERY:
            try:
                discovery = Discovery(**discovery_config) if discovery_config else Discovery()
                logger.info("Running discovery phase to identify best features...")
                
                # First compute basic features for discovery analysis
                df_discovery = df_feat.copy()
                
                # Add basic indicators for discovery
                df_discovery["rsi_14"] = compute_rsi(df_discovery["close"], period=14)
                macd, signal, hist = compute_macd(df_discovery["close"])
                df_discovery["macd"] = macd
                df_discovery["macd_signal"] = signal
                df_discovery["macd_histogram"] = hist
                
                if compute_advanced:
                    k, d = compute_stochastic(df_discovery["high"], df_discovery["low"], df_discovery["close"])
                    df_discovery["stoch_k"] = k
                    df_discovery["stoch_d"] = d
                
                # Run discovery
                discovered = discovery.discover_indicators(df_discovery, target_column="return_1bar", min_score=0.4)
                feature_selector.sync_with_discovery(discovery)
                
                # Select top N features
                top_features = sorted(discovered.items(), key=lambda x: x[1].composite_score(), reverse=True)[:discovery_top_n]
                for name, metric in top_features:
                    discovered_features[name] = metric.composite_score()
                
                logger.info(f"Discovery: identified {len(discovered_features)} top features")
                for name, score in discovered_features.items():
                    logger.debug(f"  {name}: {score:.4f}")
            
            except Exception as e:
                logger.warning(f"Indicator discovery failed, continuing without optimization: {e}")
                discovered_features = {}
        
        # ==================== MOMENTUM INDICATORS ====================
        
        try:
            df_feat["rsi_14"] = compute_rsi(df_feat["close"], period=14)
            generated_features.append(("rsi_14", "momentum"))
        except ValueError as e:
            logger.warning(f"Failed to compute RSI: {e}")
        
        try:
            macd, signal, histogram = compute_macd(df_feat["close"])
            df_feat["macd"] = macd
            df_feat["macd_signal"] = signal
            df_feat["macd_histogram"] = histogram
            generated_features.extend([
                ("macd", "momentum"),
                ("macd_signal", "momentum"),
                ("macd_histogram", "momentum")
            ])
        except ValueError as e:
            logger.warning(f"Failed to compute MACD: {e}")
        
        if compute_advanced:
            try:
                k_pct, d_pct = compute_stochastic(df_feat["high"], df_feat["low"], df_feat["close"])
                df_feat["stoch_k"] = k_pct
                df_feat["stoch_d"] = d_pct
                generated_features.extend([
                    ("stoch_k", "momentum"),
                    ("stoch_d", "momentum")
                ])
            except ValueError as e:
                logger.warning(f"Failed to compute Stochastic: {e}")
        
        # ==================== VOLATILITY INDICATORS ====================
        
        try:
            upper_bb, middle_bb, lower_bb = compute_bollinger_bands(df_feat["close"], period=20)
            df_feat["bb_upper"] = upper_bb
            df_feat["bb_middle"] = middle_bb
            df_feat["bb_lower"] = lower_bb
            df_feat["bb_width"] = upper_bb - lower_bb
            
            # Fix #1.6: Add epsilon to prevent Inf
            df_feat["bb_position"] = (df_feat["close"] - lower_bb) / (upper_bb - lower_bb + 1e-10)
            df_feat["bb_position"] = df_feat["bb_position"].replace([np.inf, -np.inf], 0).fillna(0)
            
            generated_features.extend([
                ("bb_width", "volatility"),
                ("bb_position", "volatility")
            ])
        except ValueError as e:
            logger.warning(f"Failed to compute Bollinger Bands: {e}")
        
        try:
            df_feat["atr_14"] = compute_atr(df_feat["high"], df_feat["low"], df_feat["close"], period=14)
            generated_features.append(("atr_14", "volatility"))
        except ValueError as e:
            logger.warning(f"Failed to compute ATR: {e}")
        
        # ==================== PRICE ACTION PATTERNS ====================
        
        try:
            df_feat = detect_engulfing(df_feat)
            generated_features.extend([
                ("engulfing_bullish", "price_action"),
                ("engulfing_bearish", "price_action")
            ])
        except ValueError as e:
            logger.warning(f"Failed to detect engulfing patterns: {e}")
        
        try:
            df_feat = detect_doji(df_feat)
            generated_features.extend([
                ("is_doji", "price_action"),
                ("doji_star", "price_action")
            ])
        except ValueError as e:
            logger.warning(f"Failed to detect doji patterns: {e}")
        
        try:
            df_feat = detect_inside_bar(df_feat)
            generated_features.extend([
                ("inside_bar", "price_action"),
                ("inside_bar_breakout_up", "price_action"),
                ("inside_bar_breakout_down", "price_action")
            ])
        except ValueError as e:
            logger.warning(f"Failed to detect inside bar patterns: {e}")
        
        try:
            df_feat = detect_three_bar_patterns(df_feat)
            generated_features.extend([
                ("three_white_soldiers", "price_action"),
                ("three_black_crows", "price_action")
            ])
        except ValueError as e:
            logger.warning(f"Failed to detect three bar patterns: {e}")
        
        try:
            df_feat = detect_morning_evening_star(df_feat)
            generated_features.extend([
                ("morning_star", "price_action"),
                ("evening_star", "price_action")
            ])
        except ValueError as e:
            logger.warning(f"Failed to detect star patterns: {e}")
        
        # ==================== RETURNS & MOMENTUM ====================
        
        try:
            df_feat = calculate_returns(df_feat, tf=timeframe)
            generated_features.extend([
                ("return_1bar", "returns"),
                ("return_5bar", "returns"),
                ("return_20bar", "returns"),
                ("log_return_1bar", "returns"),
                ("acceleration", "returns"),
                ("jerk", "returns"),
                ("price_velocity", "returns")
            ])
        except ValueError as e:
            logger.warning(f"Failed to calculate returns: {e}")
        
        # ==================== VOLUME FEATURES ====================
        
        try:
            df_feat["volume_sma"] = df_feat["volume"].rolling(20, min_periods=1).mean()
            df_feat["volume_ratio"] = df_feat["volume"] / (df_feat["volume_sma"] + 1e-10)
            # Fix #1.6: Handle Inf values
            df_feat["volume_ratio"] = df_feat["volume_ratio"].replace([np.inf, -np.inf], 1.0).fillna(1.0)
            generated_features.append(("volume_ratio", "volume"))
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to compute volume features: {e}")
        
        # ==================== DISCOVERY-DRIVEN FEATURE FILTERING ====================
        
        # If discovery was used, only keep selected features + OHLCV
        if discovered_features:
            discovery_feature_names = list(discovered_features.keys())
            generated_feature_names = [f[0] for f in generated_features]
            
            cols_to_keep = required_cols.copy()
            for feat in generated_feature_names:
                if feat in discovery_feature_names or feat in discovered_features:
                    cols_to_keep.append(feat)
            
            cols_to_keep = list(set(cols_to_keep))
            cols_to_keep = [c for c in cols_to_keep if c in df_feat.columns]
            
            if cols_to_keep:
                df_feat = df_feat[cols_to_keep]
                logger.info(f"Filtered to {len(cols_to_keep)} features based on discovery results")
        
        # ==================== FIX #1.2: COMPREHENSIVE NAN/INF HANDLING ====================
        
        # Fill NaN values
        numeric_cols = df_feat.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if col not in required_cols:
                df_feat[col] = df_feat[col].fillna(method='ffill').fillna(0)
        
        # Replace any remaining Inf values
        df_feat = df_feat.replace([np.inf, -np.inf], 0)
        
        # ==================== OPTIONAL NORMALIZATION ====================
        
        if normalize:
            try:
                scaler = _get_scaler(scaler_type)
                numeric_cols = df_feat.select_dtypes(include=[np.number]).columns
                df_feat[numeric_cols] = scaler.fit_transform(df_feat[numeric_cols])
                logger.info(f"Features normalized using {scaler_type.capitalize()}Scaler")
            except Exception as e:
                logger.warning(f"Normalization failed: {e}")
        
        # ==================== FIX #1.4: CENTRALIZED FEATURE REGISTRATION ====================
        
        # Build metadata dictionary
        feature_metadata = {}
        for feat_name, category in generated_features:
            try:
                register_feature(feat_name, category=category, requires_shift=False)
                discovery_score = discovered_features.get(feat_name, 0.0)
                feature_metadata[feat_name] = FeatureMetadata(
                    name=feat_name,
                    category=category,
                    discovery_score=discovery_score
                )
            except Exception as e:
                logger.debug(f"Failed to register {feat_name}: {e}")
        
        # Add selected features from discovery
        for feat_name, score in discovered_features.items():
            if feat_name not in feature_metadata:
                feature_metadata[feat_name] = FeatureMetadata(
                    name=feat_name,
                    category='discovered',
                    discovery_score=score
                )
        
        feature_count = len([c for c in df_feat.columns if c not in df.columns])
        logger.info(f"engineer_features: generated {feature_count} features with {len(feature_metadata)} metadata entries")
        
        return df_feat, feature_metadata
    
    except FeatureEngineeringError:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error in feature engineering: {e}")
        raise FeatureEngineeringError(f"Feature engineering failed: {e}")


__all__ = [
    'FeatureMetadata',
    'FeatureSelector',
    'FeatureEngineeringError',
    'FeatureRegistrationError',
    'compute_rsi',
    'compute_macd',
    'compute_bollinger_bands',
    'compute_atr',
    'compute_stochastic',
    'detect_engulfing',
    'detect_doji',
    'detect_inside_bar',
    'detect_three_bar_patterns',
    'detect_morning_evening_star',
    'calculate_returns',
    'engineer_features_for_timeframe',
    'feature_selector',
]
