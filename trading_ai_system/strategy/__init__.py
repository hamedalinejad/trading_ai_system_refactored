"""
Strategy Module - Trading strategies and signal generation

v79.1 Exports:
- Signal generation
- Walk-forward validation
- Strategy validation
- Live trading caching
"""

from .strategy import (
    # Enums
    Signal,
    
    # Data Classes
    SignalResult,
    BacktestMetrics,
    WalkForwardResult,
    
    # Classes
    SignalGenerator,
    WalkForwardEngine,
    StrategyValidator,
    LiveLiteMode,
    
    # Functions
    get_signal_generator,
    get_live_lite_mode,
)

__all__ = [
    # Enums
    "Signal",
    
    # Data Classes
    "SignalResult",
    "BacktestMetrics",
    "WalkForwardResult",
    
    # Classes
    "SignalGenerator",
    "WalkForwardEngine",
    "StrategyValidator",
    "LiveLiteMode",
    
    # Functions
    "get_signal_generator",
    "get_live_lite_mode",
]

__version__ = "0.79.1"
