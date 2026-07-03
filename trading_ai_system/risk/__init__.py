"""
Risk Module - Risk management and position sizing

v79.1 Exports:
- Risk assessment and gating
- Position sizing calculators
- Production risk engine
- Risk metrics and monitoring
"""

from .risk import (
    # Enums
    RiskLevel,
    
    # Data Classes
    RiskMetrics,
    PositionSizeResult,
    
    # Functions
    calculate_position_size,
    fractional_kelly_with_vol_target,
    
    # Classes
    TradeGatingEngine,
    RiskBrain,
    ProductionRiskEngine,
)

__all__ = [
    # Enums
    "RiskLevel",
    
    # Data Classes
    "RiskMetrics",
    "PositionSizeResult",
    
    # Functions
    "calculate_position_size",
    "fractional_kelly_with_vol_target",
    
    # Classes
    "TradeGatingEngine",
    "RiskBrain",
    "ProductionRiskEngine",
]

__version__ = "0.79.1"
