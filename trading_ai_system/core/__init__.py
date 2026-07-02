"""
Core Module - Infrastructure, configuration, state management

Exports:
- Configuration and setup classes
- Exception classes
- Core utilities
"""

from trading_ai_system.core.core import (
    TradingSystemError,
    ConfigError,
    DataError,
    ModelError,
    StrategyError,
    RiskError,
    LiveTradingError,
    CONFIG,
    StateManager,
)

__all__ = [
    "TradingSystemError",
    "ConfigError",
    "DataError",
    "ModelError",
    "StrategyError",
    "RiskError",
    "LiveTradingError",
    "CONFIG",
    "StateManager",
]
