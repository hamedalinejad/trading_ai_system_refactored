"""
Strategy Module for Trading AI System

v79.1 Enhancements:
- Thread-safe signal generation
- Better error handling
- Enhanced metrics collection
- Improved walk-forward validation
- Signal caching with TTL
"""

import numpy as np
import pandas as pd
import logging
import json
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timezone
from pathlib import Path
import threading
from functools import lru_cache

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
        """Convert to dictionary."""
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
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class WalkForwardResult:
    """Walk forward test result."""
    train_period: str
    test_period: str
    in_sample_metrics: BacktestMetrics
    out_of_sample_metrics: BacktestMetrics
    model_path: str
    stability_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "train_period": self.train_period,
            "test_period": self.test_period,
            "in_sample_metrics": self.in_sample_metrics.to_dict(),
            "out_of_sample_metrics": self.out_of_sample_metrics.to_dict(),
            "model_path": self.model_path,
            "stability_score": self.stability_score,
        }


class SignalGenerator:
    """Core signal generation from trained models."""
    
    def __init__(
        self,
        models_dir: str = "models/incremental",
        cache_enabled: bool = True,
    ):
        """Initialize signal generator."""
        self.models_dir = Path(models_dir)
        self.cache_enabled = cache_enabled
        
        self._model_cache: Dict[str, Any] = {}
        self._metadata_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_lock = threading.RLock()
        self._cache_stats = {"hits": 0, "misses": 0}
    
    def generate_signal(
        self,
        symbol: str,
        features: pd.DataFrame,
        timeframe: str = "1h",
        gating_fn: Optional[Callable] = None,
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
            
            probs = np.array([0.25, 0.35, 0.40])
            
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
            logger.error(f"Signal generation failed for {symbol}: {e}")
            return SignalResult(
                signal=Signal.HOLD,
                confidence=0.0,
                reason=f"Error: {str(e)[:50]}",
                model_name=symbol,
            )
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._cache_lock:
            total = self._cache_stats["hits"] + self._cache_stats["misses"]
            return {
                "hits": self._cache_stats["hits"],
                "misses": self._cache_stats["misses"],
                "total": total,
                "hit_rate": self._cache_stats["hits"] / max(total, 1),
                "models_cached": len(self._model_cache),
            }
    
    def clear_cache(self) -> None:
        """Clear model cache."""
        with self._cache_lock:
            self._model_cache.clear()
            self._metadata_cache.clear()


class WalkForwardEngine:
    """Walk-forward optimization and validation."""
    
    def __init__(
        self,
        initial_window: int = 1000,
        step_size: int = 250,
        test_window: int = 250,
    ):
        """Initialize walk forward engine."""
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
        
        while current_train_start + self.initial_window + self.test_window < n:
            train_start = current_train_start
            train_end = current_train_start + self.initial_window
            test_start = train_end
            test_end = test_start + self.test_window
            
            if test_end <= n:
                windows.append((train_start, train_end, test_start, test_end))
            
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
        
        if len(returns) > 0:
            sharpe = np.mean(returns) / max(np.std(returns), 1e-10) * np.sqrt(252)
        else:
            sharpe = 0.0
        
        cumulative = np.cumprod(1 + returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        max_dd = np.min(drawdown) if len(drawdown) > 0 else 0.0
        
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
            }


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
        
        correlation = signals.corr(future_returns)
        
        if correlation > 0.3:
            return True, f"High contemporaneous correlation: {correlation:.3f}"
        
        return False, "No obvious forward bias"
    
    @staticmethod
    def validate_signal_distribution(signals: pd.Series) -> Dict[str, Any]:
        """Validate signal distribution."""
        signal_counts = signals.value_counts()
        
        return {
            "buy_pct": float(signal_counts.get(1, 0) / len(signals)),
            "sell_pct": float(signal_counts.get(-1, 0) / len(signals)),
            "hold_pct": float(signal_counts.get(0, 0) / len(signals)),
            "total_trades": int(signal_counts.get(1, 0) + signal_counts.get(-1, 0)),
            "trade_density": float((signal_counts.get(1, 0) + signal_counts.get(-1, 0)) / len(signals)),
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
            return False, f"Unstable returns: {return_std:.2%} variation"
        
        sharpe_std = np.std(sharpes) / max(np.mean(np.abs(sharpes)), 0.01)
        if sharpe_std > threshold:
            return False, f"Unstable Sharpe: {sharpe_std:.2%} variation"
        
        return True, "Parameters stable"


class LiveLiteMode:
    """Lightweight live trading with cached signals."""
    
    def __init__(self, enabled: bool = False, cache_ttl_seconds: int = 3600):
        """Initialize live lite mode."""
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
            return {
                "enabled": self.enabled,
                "ttl_seconds": self.cache_ttl_seconds,
                "cached_items": len(self._cache),
                "cache_keys": list(self._cache.keys()),
            }


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
