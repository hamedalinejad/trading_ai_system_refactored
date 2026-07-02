"""
Trading AI System - Features Module
Feature engineering, technical indicators, and pattern detection.
"""

import sys
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

# ✅ Fixed: Proper import paths
try:
    from trading_ai_system.core import (
        logger, TradingSystemError, FeatureError,
        get_global_config, register_feature,
        HORIZONS, HORIZON_MIN_BARS, BARS_PER_DAY_BY_TF
    )
except ImportError:
    # Fallback for direct execution
    import logging
    logger = logging.getLogger(__name__)
    
    class FeatureError(Exception):
        pass
    
    class TradingSystemError(Exception):
        pass
    
    def get_global_config():
        return {}
    
    def register_feature(*args, **kwargs):
        pass
    
    HORIZONS = {}
    HORIZON_MIN_BARS = {}
    BARS_PER_DAY_BY_TF = {}


# ═══════════════════════════════════════════════════════════════════════════
# EXCEPTION CLASSES
# ═══════════════════════════════════════════════════════════════════════════

class FeatureEngineeringError(FeatureError):
    """Feature engineering error."""
    pass


class FeatureRegistrationError(FeatureError):
    """Feature registration error."""
    pass


# ═══════════════════════════════════════════════════════════════════════════
# FEATURE REGISTRY
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class FeatureMetadata:
    """Metadata for a feature."""
    name: str
    category: str
    requires_shift: bool = False
    lookback: int = 1
    description: str = ""
    min_bars: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "category": self.category,
            "requires_shift": self.requires_shift,
            "lookback": self.lookback,
            "description": self.description,
            "min_bars": self.min_bars
        }


# ═══════════════════════════════════════════════════════════════════════════
# TECHNICAL INDICATORS - CORE CALCULATIONS
# ═══════════════════════════════════════════════════════════════════════════

def compute_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Relative Strength Index (RSI)."""
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / (loss + 1e-10)
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def compute_macd(
    close: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate MACD (Moving Average Convergence Divergence).
    
    Returns: (macd, signal, histogram)
    """
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    
    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    histogram = macd - signal_line
    
    return macd, signal_line, histogram


def compute_bollinger_bands(
    close: pd.Series,
    period: int = 20,
    num_std: float = 2.0
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate Bollinger Bands.
    
    Returns: (upper, middle, lower)
    """
    middle = close.rolling(window=period).mean()
    std = close.rolling(window=period).std()
    
    upper = middle + (std * num_std)
    lower = middle - (std * num_std)
    
    return upper, middle, lower


def compute_atr(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14
) -> pd.Series:
    """Calculate Average True Range (ATR)."""
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    
    return atr


def compute_stochastic(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14,
    smooth_k: int = 3,
    smooth_d: int = 3
) -> Tuple[pd.Series, pd.Series]:
    """Calculate Stochastic Oscillator.
    
    Returns: (K%, D%)
    """
    lowest_low = low.rolling(window=period).min()
    highest_high = high.rolling(window=period).max()
    
    k_percent = 100 * (close - lowest_low) / (highest_high - lowest_low + 1e-10)
    k_smooth = k_percent.rolling(window=smooth_k).mean()
    d_smooth = k_smooth.rolling(window=smooth_d).mean()
    
    return k_smooth, d_smooth


# ═══════════════════════════════════════════════════════════════════════════
# PRICE ACTION PATTERNS
# ═══════════════════════════════════════════════════════════════════════════

def detect_engulfing(df: pd.DataFrame) -> pd.DataFrame:
    """v79: Detect bullish and bearish engulfing patterns (no internal shift).
    
    Engulfing patterns are already correctly positioned without double-shift.
    """
    prev_open = df["open"].shift(1)
    prev_close = df["close"].shift(1)
    prev_body = (prev_close - prev_open).abs()
    curr_body = (df["close"] - df["open"]).abs()
    
    # Bullish engulfing
    bullish = (
        (prev_close < prev_open) &
        (df["close"] > df["open"]) &
        (df["open"] <= prev_close) &
        (df["close"] >= prev_open) &
        (curr_body > prev_body)
    ).astype(int)
    
    # Bearish engulfing
    bearish = (
        (prev_close > prev_open) &
        (df["close"] < df["open"]) &
        (df["open"] >= prev_close) &
        (df["close"] <= prev_open) &
        (curr_body > prev_body)
    ).astype(int)
    
    df["engulfing_bullish"] = bullish
    df["engulfing_bearish"] = bearish
    
    register_feature("engulfing_bullish", category="price_action", requires_shift=False)
    register_feature("engulfing_bearish", category="price_action", requires_shift=False)
    
    return df


def detect_doji(df: pd.DataFrame, threshold: float = 0.1) -> pd.DataFrame:
    """v79: Detect doji patterns (no internal shift)."""
    body = (df["close"] - df["open"]).abs()
    range_ = df["high"] - df["low"]
    
    df["is_doji"] = ((body / (range_ + 1e-10)) < threshold).astype(int)
    df["doji_star"] = (
        df["is_doji"] &
        (df["low"] < df["low"].shift(1))
    ).astype(int)
    
    register_feature("is_doji", category="price_action", requires_shift=False)
    register_feature("doji_star", category="price_action", requires_shift=False)
    
    return df


def detect_inside_bar(df: pd.DataFrame) -> pd.DataFrame:
    """v79: Detect inside bar patterns (no double-shift)."""
    prev_high = df["high"].shift(1)
    prev_low = df["low"].shift(1)
    
    df["inside_bar"] = (
        (df["high"] <= prev_high) &
        (df["low"] >= prev_low)
    ).astype(int)
    
    df["inside_bar_breakout_up"] = (
        df["inside_bar"].shift(1).fillna(0) &
        (df["close"] > prev_high)
    ).astype(int)
    
    df["inside_bar_breakout_down"] = (
        df["inside_bar"].shift(1).fillna(0) &
        (df["close"] < prev_low)
    ).astype(int)
    
    register_feature("inside_bar", category="price_action", requires_shift=False)
    register_feature("inside_bar_breakout_up", category="price_action", requires_shift=False)
    register_feature("inside_bar_breakout_down", category="price_action", requires_shift=False)
    
    return df


def detect_three_bar_patterns(df: pd.DataFrame) -> pd.DataFrame:
    """v79: Detect three bar reversal patterns (requires_shift=False)."""
    bullish_1 = df["close"] > df["open"]
    bullish_2 = df["close"].shift(1) > df["open"].shift(1)
    bullish_3 = df["close"].shift(2) > df["open"].shift(2)
    
    higher_close_1 = df["close"] > df["close"].shift(1)
    higher_close_2 = df["close"].shift(1) > df["close"].shift(2)
    
    df["three_white_soldiers"] = (
        bullish_1 & bullish_2 & bullish_3 &
        higher_close_1 & higher_close_2
    ).astype(int)
    
    bearish_1 = df["close"] < df["open"]
    bearish_2 = df["close"].shift(1) < df["open"].shift(1)
    bearish_3 = df["close"].shift(2) < df["open"].shift(2)
    
    lower_close_1 = df["close"] < df["close"].shift(1)
    lower_close_2 = df["close"].shift(1) < df["close"].shift(2)
    
    df["three_black_crows"] = (
        bearish_1 & bearish_2 & bearish_3 &
        lower_close_1 & lower_close_2
    ).astype(int)
    
    register_feature("three_white_soldiers", category="price_action", requires_shift=False)
    register_feature("three_black_crows", category="price_action", requires_shift=False)
    
    return df


def detect_morning_evening_star(df: pd.DataFrame) -> pd.DataFrame:
    """v79: Detect morning/evening star patterns (requires_shift=False)."""
    body_1 = (df["close"].shift(2) - df["open"].shift(2)).abs()
    body_2 = (df["close"].shift(1) - df["open"].shift(1)).abs()
    
    # Morning star (bullish)
    df["morning_star"] = (
        (df["close"].shift(2) < df["open"].shift(2)) &
        (body_2 < body_1 * 0.3) &
        (df["close"] > df["open"]) &
        (df["close"] > (df["open"].shift(2) + df["close"].shift(2)) / 2)
    ).astype(int)
    
    # Evening star (bearish)
    df["evening_star"] = (
        (df["close"].shift(2) > df["open"].shift(2)) &
        (body_2 < body_1 * 0.3) &
        (df["close"] < df["open"]) &
        (df["close"] < (df["open"].shift(2) + df["close"].shift(2)) / 2)
    ).astype(int)
    
    register_feature("morning_star", category="price_action", requires_shift=False)
    register_feature("evening_star", category="price_action", requires_shift=False)
    
    return df


# ═══════════════════════════════════════════════════════════════════════════
# RETURNS & MOMENTUM
# ═══════════════════════════════════════════════════════════════════════════

def calculate_returns(df: pd.DataFrame, tf: str = "1h") -> pd.DataFrame:
    """v79: Calculate return features (requires_shift=False)."""
    df["return_1bar"] = df["close"].pct_change(1)
    df["return_5bar"] = df["close"].pct_change(5)
    df["return_20bar"] = df["close"].pct_change(20)
    df["log_return_1bar"] = np.log(df["close"] / df["close"].shift(1))
    df["acceleration"] = df["return_1bar"] - df["return_1bar"].shift(1)
    df["jerk"] = df["acceleration"] - df["acceleration"].shift(1)
    df["price_velocity"] = df["return_1bar"].rolling(5).sum()
    
    for feat in ["return_1bar", "return_5bar", "return_20bar", 
                 "log_return_1bar", "acceleration", "jerk", "price_velocity"]:
        register_feature(feat, category="returns", requires_shift=False)
    
    return df


# ═══════════════════════════════════════════════════════════════════════════
# MAIN FEATURE ENGINEERING PIPELINE
# ═══════════════════════════════════════════════════════════════════════════

def engineer_features_for_timeframe(
    df: pd.DataFrame,
    timeframe: str = "1h",
    compute_advanced: bool = True
) -> Tuple[pd.DataFrame, Dict[str, FeatureMetadata]]:
    """v79: Complete feature engineering pipeline.
    
    Generates technical indicators, price action patterns, and momentum features.
    All features properly aligned without double-shift data leakage.
    
    Parameters
    ----------
    df : pd.DataFrame
        Clean OHLCV data with timestamp, open, high, low, close, volume
    timeframe : str, default="1h"
        Timeframe of data (used for lookback calculations)
    compute_advanced : bool, default=True
        Include advanced features (slower but more comprehensive)
    
    Returns
    -------
    Tuple[pd.DataFrame, Dict[str, FeatureMetadata]]
        (Features DataFrame, Feature registry)
    
    Raises
    ------
    FeatureEngineeringError
        If feature engineering fails
    """
    if df is None or df.empty:
        raise FeatureEngineeringError("Empty DataFrame")
    
    required_cols = ['open', 'high', 'low', 'close', 'volume']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise FeatureEngineeringError(f"Missing columns: {missing}")
    
    df_feat = df.copy()
    logger.info(f"engineer_features_for_timeframe: {len(df_feat)} rows, {timeframe}")
    
    # ─────────────────────────────────────────────────────────────────────────
    # STAGE 1: CORE TECHNICAL INDICATORS
    # ─────────────────────────────────────────────────────────────────────────
    
    # RSI (14-period)
    df_feat["rsi_14"] = compute_rsi(df_feat["close"], period=14)
    register_feature("rsi_14", category="momentum", requires_shift=False)
    
    # MACD
    macd, signal, histogram = compute_macd(df_feat["close"])
    df_feat["macd"] = macd
    df_feat["macd_signal"] = signal
    df_feat["macd_histogram"] = histogram
    register_feature("macd", category="momentum", requires_shift=False)
    register_feature("macd_signal", category="momentum", requires_shift=False)
    register_feature("macd_histogram", category="momentum", requires_shift=False)
    
    # Bollinger Bands
    upper_bb, middle_bb, lower_bb = compute_bollinger_bands(df_feat["close"], period=20)
    df_feat["bb_upper"] = upper_bb
    df_feat["bb_middle"] = middle_bb
    df_feat["bb_lower"] = lower_bb
    df_feat["bb_width"] = upper_bb - lower_bb
    df_feat["bb_position"] = (df_feat["close"] - lower_bb) / (upper_bb - lower_bb + 1e-10)
    register_feature("bb_width", category="volatility", requires_shift=False)
    register_feature("bb_position", category="volatility", requires_shift=False)
    
    # ATR (14-period)
    df_feat["atr_14"] = compute_atr(df_feat["high"], df_feat["low"], df_feat["close"], period=14)
    register_feature("atr_14", category="volatility", requires_shift=False)
    
    # ─────────────────────────────────────────────────────────────────────────
    # STAGE 2: PRICE ACTION PATTERNS
    # ─────────────────────────────────────────────────────────────────────────
    
    df_feat = detect_engulfing(df_feat)
    df_feat = detect_doji(df_feat)
    df_feat = detect_inside_bar(df_feat)
    df_feat = detect_three_bar_patterns(df_feat)
    df_feat = detect_morning_evening_star(df_feat)
    
    # ─────────────────────────────────────────────────────────────────────────
    # STAGE 3: RETURNS & MOMENTUM
    # ─────────────────────────────────────────────────────────────────────────
    
    df_feat = calculate_returns(df_feat, tf=timeframe)
    
    # ─────────────────────────────────────────────────────────────────────────
    # STAGE 4: VOLUME FEATURES
    # ─────────────────────────────────────────────────────────────────────────
    
    df_feat["volume_sma"] = df_feat["volume"].rolling(20).mean()
    df_feat["volume_ratio"] = df_feat["volume"] / (df_feat["volume_sma"] + 1e-10)
    register_feature("volume_ratio", category="volume", requires_shift=False)
    
    # ─────────────────────────────────────────────────────────────────────────
    # STAGE 5: ADVANCED FEATURES (Optional)
    # ─────────────────────────────────────────────────────────────────────────
    
    if compute_advanced:
        # Stochastic
        k_pct, d_pct = compute_stochastic(df_feat["high"], df_feat["low"], df_feat["close"])
        df_feat["stoch_k"] = k_pct
        df_feat["stoch_d"] = d_pct
        register_feature("stoch_k", category="momentum", requires_shift=False)
        register_feature("stoch_d", category="momentum", requires_shift=False)
    
    # ─────────────────────────────────────────────────────────────────────────
    # FINAL: APPLY SINGLE SHIFT FOR INFERENCE CAUSALITY (v79 FIX)
    # ─────────────────────────────────────────────────────────────────────────
    
    # All features already aligned correctly from their calculations
    # No additional shift needed - they already use past/current bar data
    
    final_count = len(df_feat)
    feature_cols = [c for c in df_feat.columns if c not in df.columns]
    logger.info(f"engineer_features_for_timeframe: generated {len(feature_cols)} features")
    
    return df_feat, {}


# ═══════════════════════════════════════════════════════════════════════════
# EXPORTS
# ═══════════════════════════════════════════════════════════════════════════

__all__ = [
    # Classes
    'FeatureMetadata',
    
    # Exceptions
    'FeatureEngineeringError', 'FeatureRegistrationError',
    
    # Technical Indicators
    'compute_rsi', 'compute_macd', 'compute_bollinger_bands',
    'compute_atr', 'compute_stochastic',
    
    # Price Action Patterns
    'detect_engulfing', 'detect_doji', 'detect_inside_bar',
    'detect_three_bar_patterns', 'detect_morning_evening_star',
    
    # Returns & Momentum
    'calculate_returns',
    
    # Main Pipeline
    'engineer_features_for_timeframe',
]
