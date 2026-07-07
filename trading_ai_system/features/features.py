"""
Trading AI System - Features Module (v2.1)
Feature engineering, technical indicators, and pattern detection.

Improvements:
- Feature caching with LiveLiteMode
- Hash-based change detection
- State persistence ready
"""

import sys
import logging
import hashlib
from typing import Dict, Any, Optional, List, Tuple, Union
from dataclasses import dataclass, field
from threading import Lock
from pathlib import Path
import json

import numpy as np
import pandas as pd

try:
    from trading_ai_system.core import get_logger, get_global_config, register_feature
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
    pass

class FeatureRegistrationError(Exception):
    pass


@dataclass
class FeatureMetadata:
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
    def __init__(self):
        self.selected_features: Dict[str, FeatureMetadata] = {}
        self.discovery_enabled = HAS_DISCOVERY
        self._lock = Lock()
    
    def load_discovered_features(self, discovery_file: Path) -> None:
        if not self.discovery_enabled:
            logger.warning("Discovery module not available")
            return
        
        try:
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
        with self._lock:
            return self.selected_features.copy()
    
    def is_feature_selected(self, feature_name: str) -> bool:
        with self._lock:
            return feature_name in self.selected_features


feature_selector = FeatureSelector()


def compute_data_hash(df: pd.DataFrame, columns: Optional[List[str]] = None) -> str:
    """Compute SHA256 hash of dataframe for change detection"""
    try:
        if columns:
            data = df[columns].values
        else:
            data = df.values
        
        hash_obj = hashlib.sha256(pd.util.hash_pandas_object(df, index=True).values)
        return hash_obj.hexdigest()
    except Exception as e:
        logger.warning(f"Error computing data hash: {e}")
        return ""


class FeatureCache:
    """Cache features with hash-based invalidation"""
    
    def __init__(self, enable_caching: bool = True):
        self.enable_caching = enable_caching
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._hash_cache: Dict[str, str] = {}
        self._lock = Lock()
        logger.info(f"FeatureCache initialized (enabled={enable_caching})")
    
    def get(self, key: str, data_hash: str) -> Optional[pd.DataFrame]:
        if not self.enable_caching:
            return None
        
        with self._lock:
            if key in self._cache and self._hash_cache.get(key) == data_hash:
                logger.debug(f"Cache hit for {key}")
                return self._cache[key]['features'].copy()
            return None
    
    def set(self, key: str, features: pd.DataFrame, data_hash: str) -> None:
        if not self.enable_caching:
            return
        
        with self._lock:
            self._cache[key] = {'features': features.copy(), 'timestamp': pd.Timestamp.now()}
            self._hash_cache[key] = data_hash
            logger.debug(f"Cached features for {key}")
    
    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
            self._hash_cache.clear()
            logger.info("Feature cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "cached_keys": len(self._cache),
                "memory_usage": sum(len(v['features']) * v['features'].nbytes for v in self._cache.values()),
            }


feature_cache = FeatureCache(enable_caching=True)


def compute_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    if not isinstance(close, pd.Series) or len(close) < period:
        return pd.Series(np.nan, index=close.index if isinstance(close, pd.Series) else None)
    
    try:
        close = close.astype(float)
        delta = close.diff()
        
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
    if not all(isinstance(s, pd.Series) for s in [high, low, close]):
        return pd.Series(np.nan, index=high.index if isinstance(high, pd.Series) else None)
    
    if len(high) < period:
        return pd.Series(np.nan, index=high.index)
    
    try:
        high = high.astype(float)
        low = low.astype(float)
        close = close.astype(float)
        
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


def detect_engulfing(df: pd.DataFrame) -> pd.DataFrame:
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


def calculate_returns(df: pd.DataFrame, tf: str = "1h") -> pd.DataFrame:
    if not isinstance(df, pd.DataFrame) or df.empty:
        return df
    
    if 'close' not in df.columns:
        return df
    
    try:
        df_work = df[['close']].astype(float)
        
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


def engineer_features_for_timeframe(
    df: pd.DataFrame,
    timeframe: str = "1h",
    compute_advanced: bool = True,
    use_discovery: bool = True,
    discovery_config: Optional[Dict[str, Any]] = None,
    normalize: bool = False,
    use_cache: bool = True
) -> Tuple[pd.DataFrame, Dict[str, FeatureMetadata]]:
    
    if not isinstance(df, pd.DataFrame) or df.empty:
        raise FeatureEngineeringError("Empty or invalid DataFrame")
    
    required_cols = ['open', 'high', 'low', 'close', 'volume']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise FeatureEngineeringError(f"Missing required columns: {missing}")
    
    data_hash = compute_data_hash(df, required_cols)
    cache_key = f"{timeframe}_{compute_advanced}_{use_discovery}"
    
    if use_cache:
        cached = feature_cache.get(cache_key, data_hash)
        if cached is not None:
            logger.info("Using cached features")
            return cached, {}
    
    try:
        df_feat = df.copy()
        df_feat = df_feat.astype({col: float for col in required_cols}, errors='ignore')
        
        logger.info(f"engineer_features: {len(df_feat)} rows, timeframe={timeframe}")
        
        generated_features = []
        
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
        
        try:
            upper_bb, middle_bb, lower_bb = compute_bollinger_bands(df_feat["close"], period=20)
            df_feat["bb_upper"] = upper_bb
            df_feat["bb_middle"] = middle_bb
            df_feat["bb_lower"] = lower_bb
            df_feat["bb_width"] = upper_bb - lower_bb
            
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
        
        try:
            df_feat["volume_sma"] = df_feat["volume"].rolling(20, min_periods=1).mean()
            df_feat["volume_ratio"] = df_feat["volume"] / (df_feat["volume_sma"] + 1e-10)
            df_feat["volume_ratio"] = df_feat["volume_ratio"].replace([np.inf, -np.inf], 1.0).fillna(1.0)
            generated_features.append(("volume_ratio", "volume"))
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to compute volume features: {e}")
        
        if use_discovery and HAS_DISCOVERY:
            try:
                discovery = Discovery(**discovery_config) if discovery_config else Discovery()
                discovered = discovery.discover_indicators(df_feat, target_column="return_1bar", min_score=0.5)
                logger.info(f"Discovery: found {len(discovered)} high-performing indicators")
            except Exception as e:
                logger.warning(f"Indicator discovery failed: {e}")
        
        numeric_cols = df_feat.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if col not in required_cols:
                df_feat[col] = df_feat[col].fillna(method='ffill').fillna(0)
        
        df_feat = df_feat.replace([np.inf, -np.inf], 0)
        
        if normalize:
            try:
                from sklearn.preprocessing import StandardScaler
                scaler = StandardScaler()
                numeric_cols = df_feat.select_dtypes(include=[np.number]).columns
                df_feat[numeric_cols] = scaler.fit_transform(df_feat[numeric_cols])
                logger.info("Features normalized using StandardScaler")
            except ImportError:
                logger.warning("sklearn not available for normalization")
        
        for feat_name, category in generated_features:
            try:
                register_feature(feat_name, category=category, requires_shift=False)
            except Exception as e:
                logger.debug(f"Failed to register {feat_name}: {e}")
        
        feature_count = len([c for c in df_feat.columns if c not in df.columns])
        logger.info(f"engineer_features: generated {feature_count} features")
        
        if use_cache:
            feature_cache.set(cache_key, df_feat, data_hash)
        
        return df_feat, {}
    
    except FeatureEngineeringError:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error in feature engineering: {e}")
        raise FeatureEngineeringError(f"Feature engineering failed: {e}")


__all__ = [
    'FeatureMetadata',
    'FeatureSelector',
    'FeatureCache',
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
    'feature_cache',
    'compute_data_hash',
]
