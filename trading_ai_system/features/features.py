"""
Trading AI System - Features Module
Feature engineering, technical indicators, and pattern detection.
"""

import sys
import logging
from typing import Dict, Any, Optional, List, Tuple, Union
from dataclasses import dataclass, field
from threading import Lock

import numpy as np
import pandas as pd

try:
    from trading_ai_system.core import (
        logger, TradingSystemError, FeatureError,
        get_global_config, register_feature,
        HORIZONS, HORIZON_MIN_BARS, BARS_PER_DAY_BY_TF
    )
except ImportError:
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


class FeatureEngineeringError(FeatureError):
    pass

class FeatureRegistrationError(FeatureError):
    pass


@dataclass
class FeatureMetadata:
    name: str
    category: str
    requires_shift: bool = False
    lookback: int = 1
    description: str = ""
    min_bars: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category,
            "requires_shift": self.requires_shift,
            "lookback": self.lookback,
            "description": self.description,
            "min_bars": self.min_bars
        }


def compute_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    if not isinstance(close, pd.Series) or len(close) < period:
        return pd.Series(np.nan, index=close.index if isinstance(close, pd.Series) else None)
    
    close = close.astype(float)
    delta = close.diff()
    
    gain = delta.where(delta > 0, 0).rolling(window=period, min_periods=1).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period, min_periods=1).mean()
    
    rs = gain / (loss + 1e-10)
    rsi = 100 - (100 / (1 + rs))
    
    return rsi.fillna(50.0)


def compute_macd(
    close: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    if not isinstance(close, pd.Series) or len(close) < slow:
        idx = close.index if isinstance(close, pd.Series) else None
        return pd.Series(np.nan, index=idx), pd.Series(np.nan, index=idx), pd.Series(np.nan, index=idx)
    
    close = close.astype(float)
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
    if not isinstance(close, pd.Series) or len(close) < period:
        idx = close.index if isinstance(close, pd.Series) else None
        return pd.Series(np.nan, index=idx), pd.Series(np.nan, index=idx), pd.Series(np.nan, index=idx)
    
    close = close.astype(float)
    middle = close.rolling(window=period, min_periods=1).mean()
    std = close.rolling(window=period, min_periods=1).std()
    std = std.fillna(0)
    
    upper = middle + (std * num_std)
    lower = middle - (std * num_std)
    
    return upper, middle, lower


def compute_atr(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14
) -> pd.Series:
    if not isinstance(high, pd.Series) or not isinstance(low, pd.Series) or not isinstance(close, pd.Series):
        return pd.Series(np.nan, index=high.index if isinstance(high, pd.Series) else None)
    
    if len(high) < period:
        return pd.Series(np.nan, index=high.index)
    
    high = high.astype(float)
    low = low.astype(float)
    close = close.astype(float)
    
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period, min_periods=1).mean()
    
    return atr.fillna(tr.mean()) if tr.mean() > 0 else atr


def compute_stochastic(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14,
    smooth_k: int = 3,
    smooth_d: int = 3
) -> Tuple[pd.Series, pd.Series]:
    if not isinstance(high, pd.Series) or not isinstance(low, pd.Series) or not isinstance(close, pd.Series):
        idx = high.index if isinstance(high, pd.Series) else None
        return pd.Series(np.nan, index=idx), pd.Series(np.nan, index=idx)
    
    if len(high) < period:
        idx = high.index
        return pd.Series(np.nan, index=idx), pd.Series(np.nan, index=idx)
    
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


def detect_engulfing(df: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(df, pd.DataFrame) or df.empty:
        return df
    
    if not all(c in df.columns for c in ['open', 'close', 'high', 'low']):
        return df
    
    df = df.copy()
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
    
    try:
        register_feature("engulfing_bullish", category="price_action", requires_shift=False)
        register_feature("engulfing_bearish", category="price_action", requires_shift=False)
    except Exception as e:
        logger.warning(f"Failed to register engulfing features: {e}")
    
    return df


def detect_doji(df: pd.DataFrame, threshold: float = 0.1) -> pd.DataFrame:
    if not isinstance(df, pd.DataFrame) or df.empty:
        return df
    
    if not all(c in df.columns for c in ['open', 'close', 'high', 'low']):
        return df
    
    if threshold <= 0 or threshold > 1:
        threshold = 0.1
    
    df = df.copy()
    df_work = df[['open', 'close', 'high', 'low']].astype(float)
    
    body = (df_work["close"] - df_work["open"]).abs()
    range_ = df_work["high"] - df_work["low"]
    
    range_ = range_.replace(0, 1e-10)
    
    df["is_doji"] = ((body / (range_ + 1e-10)) < threshold).astype(int).fillna(0)
    df["doji_star"] = (
        (df["is_doji"] == 1) &
        (df_work["low"] < df_work["low"].shift(1))
    ).astype(int).fillna(0)
    
    try:
        register_feature("is_doji", category="price_action", requires_shift=False)
        register_feature("doji_star", category="price_action", requires_shift=False)
    except Exception as e:
        logger.warning(f"Failed to register doji features: {e}")
    
    return df


def detect_inside_bar(df: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(df, pd.DataFrame) or df.empty:
        return df
    
    if not all(c in df.columns for c in ['high', 'low', 'close']):
        return df
    
    df = df.copy()
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
    
    try:
        register_feature("inside_bar", category="price_action", requires_shift=False)
        register_feature("inside_bar_breakout_up", category="price_action", requires_shift=False)
        register_feature("inside_bar_breakout_down", category="price_action", requires_shift=False)
    except Exception as e:
        logger.warning(f"Failed to register inside_bar features: {e}")
    
    return df


def detect_three_bar_patterns(df: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(df, pd.DataFrame) or df.empty:
        return df
    
    if not all(c in df.columns for c in ['open', 'close']):
        return df
    
    df = df.copy()
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
    
    try:
        register_feature("three_white_soldiers", category="price_action", requires_shift=False)
        register_feature("three_black_crows", category="price_action", requires_shift=False)
    except Exception as e:
        logger.warning(f"Failed to register three_bar features: {e}")
    
    return df


def detect_morning_evening_star(df: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(df, pd.DataFrame) or df.empty:
        return df
    
    if not all(c in df.columns for c in ['open', 'close']):
        return df
    
    df = df.copy()
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
    
    try:
        register_feature("morning_star", category="price_action", requires_shift=False)
        register_feature("evening_star", category="price_action", requires_shift=False)
    except Exception as e:
        logger.warning(f"Failed to register star features: {e}")
    
    return df


def calculate_returns(df: pd.DataFrame, tf: str = "1h") -> pd.DataFrame:
    if not isinstance(df, pd.DataFrame) or df.empty:
        return df
    
    if 'close' not in df.columns:
        return df
    
    df = df.copy()
    df_work = df[['close']].astype(float)
    
    df["return_1bar"] = df_work["close"].pct_change(1).fillna(0)
    df["return_5bar"] = df_work["close"].pct_change(5).fillna(0)
    df["return_20bar"] = df_work["close"].pct_change(20).fillna(0)
    
    log_ret = np.log(df_work["close"] / df_work["close"].shift(1))
    df["log_return_1bar"] = log_ret.replace([np.inf, -np.inf], 0).fillna(0)
    
    df["acceleration"] = df["return_1bar"] - df["return_1bar"].shift(1)
    df["acceleration"] = df["acceleration"].fillna(0)
    
    df["jerk"] = df["acceleration"] - df["acceleration"].shift(1)
    df["jerk"] = df["jerk"].fillna(0)
    
    df["price_velocity"] = df["return_1bar"].rolling(5, min_periods=1).sum().fillna(0)
    
    for feat in ["return_1bar", "return_5bar", "return_20bar", 
                 "log_return_1bar", "acceleration", "jerk", "price_velocity"]:
        try:
            register_feature(feat, category="returns", requires_shift=False)
        except Exception as e:
            logger.warning(f"Failed to register {feat}: {e}")
    
    return df


def engineer_features_for_timeframe(
    df: pd.DataFrame,
    timeframe: str = "1h",
    compute_advanced: bool = True
) -> Tuple[pd.DataFrame, Dict[str, FeatureMetadata]]:
    
    if not isinstance(df, pd.DataFrame) or df.empty:
        raise FeatureEngineeringError("Empty or invalid DataFrame")
    
    required_cols = ['open', 'high', 'low', 'close', 'volume']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise FeatureEngineeringError(f"Missing required columns: {missing}")
    
    try:
        df_feat = df.copy()
        df_feat = df_feat.astype({col: float for col in ['open', 'high', 'low', 'close', 'volume']}, errors='ignore')
    except Exception as e:
        raise FeatureEngineeringError(f"Failed to convert columns to float: {e}")
    
    logger.info(f"engineer_features_for_timeframe: {len(df_feat)} rows, timeframe={timeframe}")
    
    try:
        df_feat["rsi_14"] = compute_rsi(df_feat["close"], period=14)
        register_feature("rsi_14", category="momentum", requires_shift=False)
    except Exception as e:
        logger.warning(f"Failed to compute RSI: {e}")
    
    try:
        macd, signal, histogram = compute_macd(df_feat["close"])
        df_feat["macd"] = macd
        df_feat["macd_signal"] = signal
        df_feat["macd_histogram"] = histogram
        register_feature("macd", category="momentum", requires_shift=False)
        register_feature("macd_signal", category="momentum", requires_shift=False)
        register_feature("macd_histogram", category="momentum", requires_shift=False)
    except Exception as e:
        logger.warning(f"Failed to compute MACD: {e}")
    
    try:
        upper_bb, middle_bb, lower_bb = compute_bollinger_bands(df_feat["close"], period=20)
        df_feat["bb_upper"] = upper_bb
        df_feat["bb_middle"] = middle_bb
        df_feat["bb_lower"] = lower_bb
        df_feat["bb_width"] = upper_bb - lower_bb
        df_feat["bb_position"] = (df_feat["close"] - lower_bb) / (upper_bb - lower_bb + 1e-10)
        register_feature("bb_width", category="volatility", requires_shift=False)
        register_feature("bb_position", category="volatility", requires_shift=False)
    except Exception as e:
        logger.warning(f"Failed to compute Bollinger Bands: {e}")
    
    try:
        df_feat["atr_14"] = compute_atr(df_feat["high"], df_feat["low"], df_feat["close"], period=14)
        register_feature("atr_14", category="volatility", requires_shift=False)
    except Exception as e:
        logger.warning(f"Failed to compute ATR: {e}")
    
    try:
        df_feat = detect_engulfing(df_feat)
        df_feat = detect_doji(df_feat)
        df_feat = detect_inside_bar(df_feat)
        df_feat = detect_three_bar_patterns(df_feat)
        df_feat = detect_morning_evening_star(df_feat)
    except Exception as e:
        logger.warning(f"Failed to detect price patterns: {e}")
    
    try:
        df_feat = calculate_returns(df_feat, tf=timeframe)
    except Exception as e:
        logger.warning(f"Failed to calculate returns: {e}")
    
    try:
        df_feat["volume_sma"] = df_feat["volume"].rolling(20, min_periods=1).mean()
        df_feat["volume_ratio"] = df_feat["volume"] / (df_feat["volume_sma"] + 1e-10)
        df_feat["volume_ratio"] = df_feat["volume_ratio"].replace([np.inf, -np.inf], 1.0).fillna(1.0)
        register_feature("volume_ratio", category="volume", requires_shift=False)
    except Exception as e:
        logger.warning(f"Failed to compute volume features: {e}")
    
    if compute_advanced:
        try:
            k_pct, d_pct = compute_stochastic(df_feat["high"], df_feat["low"], df_feat["close"])
            df_feat["stoch_k"] = k_pct
            df_feat["stoch_d"] = d_pct
            register_feature("stoch_k", category="momentum", requires_shift=False)
            register_feature("stoch_d", category="momentum", requires_shift=False)
        except Exception as e:
            logger.warning(f"Failed to compute Stochastic: {e}")
    
    feature_cols = [c for c in df_feat.columns if c not in df.columns]
    logger.info(f"engineer_features_for_timeframe: generated {len(feature_cols)} features")
    
    return df_feat, {}


__all__ = [
    'FeatureMetadata',
    'FeatureEngineeringError', 'FeatureRegistrationError',
    'compute_rsi', 'compute_macd', 'compute_bollinger_bands',
    'compute_atr', 'compute_stochastic',
    'detect_engulfing', 'detect_doji', 'detect_inside_bar',
    'detect_three_bar_patterns', 'detect_morning_evening_star',
    'calculate_returns',
    'engineer_features_for_timeframe',
]
