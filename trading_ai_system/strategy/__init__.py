"""
Strategy Module - Signal generation, walk-forward validation, strategy analysis
v79.2: Full integration with models, features, risk modules
"""

from .strategy import (
    Signal,
    SignalResult,
    BacktestMetrics,
    WalkForwardResult,
    SignalGenerator,
    WalkForwardEngine,
    StrategyValidator,
    LiveLiteMode,
    get_signal_generator,
    get_live_lite_mode,
)

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

__version__ = "0.79.2"
