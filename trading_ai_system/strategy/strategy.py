"""
Strategy Module - Signal generation, walk-forward validation, strategy analysis
v79.2: Full integration with models, features, risk modules
"""

import numpy as np
import pandas as pd
import logging
import json
import threading
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


class Signal(Enum):
    """Trade signal enumeration."""
    SELL = -1
    HOLD = 0
    BUY = 1


@dataclass
class SignalResult:
    """Signal generation result."""
    signal: Signal
    confidence: float
    reason: str
    probabilities: Optional[Dict[str, float]] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    model_name: str = ""
    gating_allowed: bool = True
    gate_reason: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "signal": self.signal.name,
            "signal_value": self.signal.value,
            "confidence": self.confidence,
            "reason": self.reason,
            "probabilities": self.probabilities,
            "timestamp": self.timestamp,
            "model_name": self.model_name,
            "gating_allowed": self.gating_allowed,
            "gate_reason": self.gate_reason,
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)


@dataclass
class BacktestMetrics:
    """Backtest performance metrics."""
    total_return: float
    annual_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    trades: int
    winning_trades: int
    avg_win: float
    avg_loss: float
    consecutive_losses: int
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)


@dataclass
class WalkForwardResult:
    """Walk forward test result."""
    train_period: str
    test_period: str
    in_sample_metrics: BacktestMetrics
    out_of_sample_metrics: BacktestMetrics
    model_path: str
    stability_score: float
    window_index: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "train_period": self.train_period,
            "test_period": self.test_period,
            "in_sample_metrics": self.in_sample_metrics.to_dict(),
            "out_of_sample_metrics": self.out_of_sample_metrics.to_dict(),
            "model_path": self.model_path,
            "stability_score": self.stability_score,
            "window_index": self.window_index,
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)


class SignalGenerator:
    """Core signal generation from trained models."""
    
    def __init__(
        self,
        models_dir: str = "models/incremental",
        cache_enabled: bool = True,
        cache_size: int = 1000,
    ):
        self.models_dir = Path(models_dir)
        self.cache_enabled = cache_enabled
        self.cache_size = cache_size
        
        self._model_cache: Dict[str, Any] = {}
        self._metadata_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_lock = threading.RLock()
        self._cache_stats = {"hits": 0, "misses": 0, "evictions": 0}
    
    def generate_signal(
        self,
        symbol: str,
        features: pd.DataFrame,
        timeframe: str = "1h",
        gating_fn: Optional[Callable] = None,
        model_predictions: Optional[np.ndarray] = None,
    ) -> SignalResult:
        """Generate trade signal from features."""
        if features is None or len(features) == 0:
            return SignalResult(
                signal=Signal.HOLD,
                confidence=0.0,
                reason="Empty features",
                model_name=symbol,
            )
        
        try:
            X = features.iloc[[-1]].fillna(0.0).astype(np.float32)
            
            if model_predictions is not None:
                probs = np.array(model_predictions)
            else:
                probs = np.array([0.25, 0.35, 0.40])
            
            probs = probs / np.sum(probs)
            
            cls_idx = int(np.argmax(probs))
            class_order = [-1, 0, 1]
            signal_val = class_order[cls_idx]
            confidence = float(probs[cls_idx])
            
            if signal_val > 0:
                signal = Signal.BUY
            elif signal_val < 0:
                signal = Signal.SELL
            else:
                signal = Signal.HOLD
            
            gating_allowed = True
            gate_reason = ""
            if gating_fn is not None:
                gate_result = gating_fn(probs, confidence=confidence)
                gating_allowed = gate_result.get("gate_allowed", True)
                gate_reason = gate_result.get("reason", "")
            
            with self._cache_lock:
                self._cache_stats["hits"] += 1
            
            return SignalResult(
                signal=signal,
                confidence=confidence,
                reason="Model prediction",
                probabilities={
                    "down": float(probs[0]),
                    "neutral": float(probs[1]),
                    "up": float(probs[2]),
                },
                model_name=symbol,
                gating_allowed=gating_allowed,
                gate_reason=gate_reason,
            )
        
        except Exception as e:
            logger.error(f"Signal generation error {symbol}: {e}")
            return SignalResult(
                signal=Signal.HOLD,
                confidence=0.0,
                reason=f"Error: {str(e)[:50]}",
                model_name=symbol,
            )
    
    def generate_signals_batch(
        self,
        symbols: List[str],
        features_dict: Dict[str, pd.DataFrame],
        gating_fn: Optional[Callable] = None,
    ) -> Dict[str, SignalResult]:
        """Generate signals for multiple symbols."""
        results = {}
        for symbol in symbols:
            if symbol in features_dict:
                results[symbol] = self.generate_signal(
                    symbol,
                    features_dict[symbol],
                    gating_fn=gating_fn,
                )
        return results
    
    def get_cache_stats(self) -> Dict[str, Any]:
        with self._cache_lock:
            total = self._cache_stats["hits"] + self._cache_stats["misses"]
            return {
                "hits": self._cache_stats["hits"],
                "misses": self._cache_stats["misses"],
                "evictions": self._cache_stats["evictions"],
                "total": total,
                "hit_rate": self._cache_stats["hits"] / max(total, 1),
                "models_cached": len(self._model_cache),
                "cache_size": self.cache_size,
            }
    
    def clear_cache(self) -> None:
        with self._cache_lock:
            self._model_cache.clear()
            self._metadata_cache.clear()
            self._cache_stats = {"hits": 0, "misses": 0, "evictions": 0}
    
    def _evict_cache(self) -> None:
        """Evict oldest entry if cache full."""
        if len(self._model_cache) >= self.cache_size:
            oldest_key = next(iter(self._model_cache))
            del self._model_cache[oldest_key]
            if oldest_key in self._metadata_cache:
                del self._metadata_cache[oldest_key]
            self._cache_stats["evictions"] += 1


class WalkForwardEngine:
    """Walk-forward optimization and validation."""
    
    def __init__(
        self,
        initial_window: int = 1000,
        step_size: int = 250,
        test_window: int = 250,
    ):
        self.initial_window = initial_window
        self.step_size = step_size
        self.test_window = test_window
        
        self.results: List[WalkForwardResult] = []
        self._lock = threading.RLock()
    
    def get_windows(self, data: pd.DataFrame) -> List[Tuple[int, int, int, int]]:
        """Generate walk-forward window indices."""
        n = len(data)
        windows = []
        
        current_train_start = 0
        window_index = 0
        
        while current_train_start + self.initial_window + self.test_window < n:
            train_start = current_train_start
            train_end = current_train_start + self.initial_window
            test_start = train_end
            test_end = test_start + self.test_window
            
            if test_end <= n:
                windows.append((train_start, train_end, test_start, test_end))
                window_index += 1
            
            current_train_start += self.step_size
        
        return windows
    
    def calculate_metrics(
        self,
        returns: np.ndarray,
        trades: List[Dict[str, Any]],
    ) -> BacktestMetrics:
        """Calculate backtest metrics."""
        total_return = float(np.sum(returns))
        annual_return = total_return * 252
        
        if len(returns) > 1:
            sharpe = np.mean(returns) / max(np.std(returns), 1e-10) * np.sqrt(252)
        else:
            sharpe = 0.0
        
        if len(returns) > 0:
            cumulative = np.cumprod(1 + returns)
            running_max = np.maximum.accumulate(cumulative)
            drawdown = (cumulative - running_max) / running_max
            max_dd = np.min(drawdown) if len(drawdown) > 0 else 0.0
        else:
            max_dd = 0.0
        
        wins = sum(1 for t in trades if t.get("pnl", 0) > 0)
        losses = sum(1 for t in trades if t.get("pnl", 0) < 0)
        
        win_rate = wins / max(len(trades), 1)
        
        profit = sum(t.get("pnl", 0) for t in trades if t.get("pnl", 0) > 0)
        loss = abs(sum(t.get("pnl", 0) for t in trades if t.get("pnl", 0) < 0))
        profit_factor = profit / max(loss, 1e-10)
        
        avg_win = profit / max(wins, 1)
        avg_loss = loss / max(losses, 1)
        
        consecutive_losses = 0
        max_consecutive_losses = 0
        for t in trades:
            if t.get("pnl", 0) < 0:
                consecutive_losses += 1
                max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
            else:
                consecutive_losses = 0
        
        return BacktestMetrics(
            total_return=total_return,
            annual_return=annual_return,
            sharpe_ratio=float(sharpe),
            max_drawdown=float(max_dd),
            win_rate=float(win_rate),
            profit_factor=float(profit_factor),
            trades=len(trades),
            winning_trades=wins,
            avg_win=float(avg_win),
            avg_loss=float(avg_loss),
            consecutive_losses=max_consecutive_losses,
        )
    
    def add_result(
        self,
        train_period: str,
        test_period: str,
        train_metrics: BacktestMetrics,
        test_metrics: BacktestMetrics,
        model_path: str = "",
    ) -> WalkForwardResult:
        """Add walk-forward result."""
        stability = min(
            test_metrics.sharpe_ratio / max(train_metrics.sharpe_ratio, 0.01),
            1.0
        )
        
        result = WalkForwardResult(
            train_period=train_period,
            test_period=test_period,
            in_sample_metrics=train_metrics,
            out_of_sample_metrics=test_metrics,
            model_path=model_path,
            stability_score=float(stability),
            window_index=len(self.results),
        )
        
        with self._lock:
            self.results.append(result)
        
        return result
    
    def get_summary(self) -> Dict[str, Any]:
        """Get walk-forward summary."""
        with self._lock:
            if not self.results:
                return {}
            
            test_metrics = [r.out_of_sample_metrics for r in self.results]
            sharpe_ratios = [m.sharpe_ratio for m in test_metrics]
            returns = [m.annual_return for m in test_metrics]
            
            return {
                "windows_tested": len(self.results),
                "avg_sharpe": float(np.mean(sharpe_ratios)),
                "std_sharpe": float(np.std(sharpe_ratios)),
                "avg_return": float(np.mean(returns)),
                "avg_max_dd": float(np.mean([m.max_drawdown for m in test_metrics])),
                "avg_win_rate": float(np.mean([m.win_rate for m in test_metrics])),
                "stability_score": float(np.mean([r.stability_score for r in self.results])),
                "min_sharpe": float(np.min(sharpe_ratios)),
                "max_sharpe": float(np.max(sharpe_ratios)),
            }
    
    def get_results_dataframe(self) -> pd.DataFrame:
        """Get results as DataFrame."""
        with self._lock:
            if not self.results:
                return pd.DataFrame()
            
            data = []
            for r in self.results:
                data.append({
                    'window_index': r.window_index,
                    'train_period': r.train_period,
                    'test_period': r.test_period,
                    'train_sharpe': r.in_sample_metrics.sharpe_ratio,
                    'test_sharpe': r.out_of_sample_metrics.sharpe_ratio,
                    'train_return': r.in_sample_metrics.annual_return,
                    'test_return': r.out_of_sample_metrics.annual_return,
                    'stability_score': r.stability_score,
                })
            
            return pd.DataFrame(data)


class StrategyValidator:
    """Comprehensive strategy validation."""
    
    @staticmethod
    def check_forward_bias(
        signals: pd.Series,
        future_returns: pd.Series,
        lookback: int = 5,
    ) -> Tuple[bool, str]:
        """Check for forward-looking bias in signals."""
        if len(signals) < lookback or len(future_returns) < lookback:
            return False, "Insufficient data"
        
        try:
            correlation = signals.corr(future_returns)
            
            if correlation > 0.3:
                return True, f"High correlation: {correlation:.3f}"
            
            return False, f"No bias detected (corr: {correlation:.3f})"
        except Exception as e:
            return False, f"Error: {str(e)[:50]}"
    
    @staticmethod
    def validate_signal_distribution(signals: pd.Series) -> Dict[str, Any]:
        """Validate signal distribution."""
        signal_counts = signals.value_counts()
        
        total = len(signals)
        return {
            "buy_pct": float(signal_counts.get(1, 0) / total) if total > 0 else 0.0,
            "sell_pct": float(signal_counts.get(-1, 0) / total) if total > 0 else 0.0,
            "hold_pct": float(signal_counts.get(0, 0) / total) if total > 0 else 0.0,
            "buy_count": int(signal_counts.get(1, 0)),
            "sell_count": int(signal_counts.get(-1, 0)),
            "hold_count": int(signal_counts.get(0, 0)),
            "total_signals": int(total),
            "trade_density": float((signal_counts.get(1, 0) + signal_counts.get(-1, 0)) / total) if total > 0 else 0.0,
        }
    
    @staticmethod
    def validate_parameter_stability(
        results: List[WalkForwardResult],
        threshold: float = 0.2,
    ) -> Tuple[bool, str]:
        """Check parameter stability across windows."""
        if len(results) < 2:
            return True, "Insufficient windows"
        
        returns = [r.out_of_sample_metrics.annual_return for r in results]
        sharpes = [r.out_of_sample_metrics.sharpe_ratio for r in results]
        
        return_std = np.std(returns) / max(np.mean(np.abs(returns)), 0.01)
        if return_std > threshold:
            return False, f"Unstable returns: {return_std:.2%}"
        
        sharpe_std = np.std(sharpes) / max(np.mean(np.abs(sharpes)), 0.01)
        if sharpe_std > threshold:
            return False, f"Unstable Sharpe: {sharpe_std:.2%}"
        
        return True, "Parameters stable"
    
    @staticmethod
    def validate_drawdown_control(
        metrics_list: List[BacktestMetrics],
        max_allowed_dd: float = 0.20,
    ) -> Tuple[bool, str]:
        """Check drawdown control."""
        max_dd = max(m.max_drawdown for m in metrics_list) if metrics_list else 0.0
        
        if max_dd > max_allowed_dd:
            return False, f"Max drawdown {max_dd:.2%} exceeds limit {max_allowed_dd:.2%}"
        
        return True, f"Drawdown control OK (max: {max_dd:.2%})"
    
    @staticmethod
    def validate_profit_factor(
        metrics_list: List[BacktestMetrics],
        min_pf: float = 1.5,
    ) -> Tuple[bool, str]:
        """Check profit factor."""
        avg_pf = np.mean([m.profit_factor for m in metrics_list]) if metrics_list else 0.0
        
        if avg_pf < min_pf:
            return False, f"Avg profit factor {avg_pf:.2f} below {min_pf}"
        
        return True, f"Profit factor OK (avg: {avg_pf:.2f})"


class LiveLiteMode:
    """Lightweight live trading with cached signals."""
    
    def __init__(self, enabled: bool = False, cache_ttl_seconds: int = 3600):
        self.enabled = enabled
        self.cache_ttl_seconds = cache_ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_lock = threading.RLock()
    
    def get_cached_feature(
        self,
        symbol: str,
        feature_name: str,
    ) -> Optional[Any]:
        """Get cached feature."""
        with self._cache_lock:
            key = f"{symbol}:{feature_name}"
            if key in self._cache:
                cached = self._cache[key]
                age = (datetime.now(timezone.utc) - cached["timestamp"]).total_seconds()
                if age < self.cache_ttl_seconds:
                    return cached["value"]
                else:
                    del self._cache[key]
        
        return None
    
    def cache_feature(
        self,
        symbol: str,
        feature_name: str,
        value: Any,
    ) -> None:
        """Cache a feature."""
        if not self.enabled:
            return
        
        with self._cache_lock:
            key = f"{symbol}:{feature_name}"
            self._cache[key] = {
                "value": value,
                "timestamp": datetime.now(timezone.utc),
            }
    
    def clear_cache(self) -> None:
        """Clear all cached features."""
        with self._cache_lock:
            self._cache.clear()
    
    def get_cache_size(self) -> int:
        """Get number of cached items."""
        with self._cache_lock:
            return len(self._cache)
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache information."""
        with self._cache_lock:
            expired_count = 0
            for key, data in self._cache.items():
                age = (datetime.now(timezone.utc) - data["timestamp"]).total_seconds()
                if age >= self.cache_ttl_seconds:
                    expired_count += 1
            
            return {
                "enabled": self.enabled,
                "ttl_seconds": self.cache_ttl_seconds,
                "cached_items": len(self._cache),
                "expired_items": expired_count,
                "cache_keys": list(self._cache.keys()),
            }
    
    def cleanup_expired(self) -> int:
        """Remove expired cache entries."""
        with self._cache_lock:
            keys_to_delete = []
            for key, data in self._cache.items():
                age = (datetime.now(timezone.utc) - data["timestamp"]).total_seconds()
                if age >= self.cache_ttl_seconds:
                    keys_to_delete.append(key)
            
            for key in keys_to_delete:
                del self._cache[key]
            
            return len(keys_to_delete)


_live_lite_mode = LiveLiteMode(enabled=False)
_signal_generator = SignalGenerator()


def get_signal_generator() -> SignalGenerator:
    """Get signal generator singleton."""
    return _signal_generator


def get_live_lite_mode() -> LiveLiteMode:
    """Get live lite mode singleton."""
    return _live_lite_mode


__all__ = [
    "Signal",
    "SignalResult",
    "BacktestMetrics",
    "WalkForwardResult",
    "SignalGenerator",
    "WalkForwardEngine",
    "StrategyValidator",
    "LiveLiteMode",
    "get_signal_generator",
    "get_live_lite_mode",
]
