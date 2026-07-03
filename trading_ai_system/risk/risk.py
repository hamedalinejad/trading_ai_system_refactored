"""
Risk Management Module for Trading AI System

v79.1 Enhancements:
- Thread-safe risk engine with RLock
- Enhanced monitoring and alerting
- Volatility-adjusted position sizing
- Comprehensive risk tracking
- Better logging and metrics collection
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone
import asyncio
from threading import RLock

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk assessment levels."""
    SAFE = 0
    MODERATE = 1
    WARNING = 2
    DANGER = 3
    HALT = 4


@dataclass
class RiskMetrics:
    """Risk assessment results."""
    level: RiskLevel
    drawdown_pct: float
    margin_utilization: float
    position_concentration: float
    volatility_regime: str
    confidence_score: float
    allow_trade: bool
    reason: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "level": self.level.name,
            "drawdown_pct": self.drawdown_pct,
            "margin_utilization": self.margin_utilization,
            "position_concentration": self.position_concentration,
            "volatility_regime": self.volatility_regime,
            "confidence_score": self.confidence_score,
            "allow_trade": self.allow_trade,
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class PositionSizeResult:
    """Position sizing calculation result."""
    size: float
    kelly_size: float
    vol_size: float
    confidence_factor: float
    constraints: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "size": self.size,
            "kelly_size": self.kelly_size,
            "vol_size": self.vol_size,
            "confidence_factor": self.confidence_factor,
            "constraints": self.constraints,
        }


def calculate_position_size(
    confidence: float,
    current_atr_ratio: float,
    target_volatility: float = 0.10,
    max_position: float = 0.05,
    kelly_fraction: float = 0.25,
    win_rate: float = 0.55,
    avg_win_loss_ratio: float = 1.5,
    max_position_pct: float = 0.10,
) -> float:
    """Calculate position size using volatility targeting and fractional Kelly.
    
    Args:
        confidence: Model confidence (0.0 to 1.0)
        current_atr_ratio: Current ATR as % of price
        target_volatility: Target daily volatility
        max_position: Position as % of capital
        kelly_fraction: Fraction of Kelly criterion
        win_rate: Historical win rate
        avg_win_loss_ratio: Avg win / avg loss
        max_position_pct: Hard cap on position
    
    Returns:
        float: Position size as fraction of capital
    """
    effective_atr = max(current_atr_ratio, 0.0005)
    
    vol_position = target_volatility / (effective_atr * np.sqrt(252) + 1e-10)
    vol_position = min(vol_position, max_position)
    
    if win_rate > 0 and avg_win_loss_ratio > 0:
        kelly = (win_rate * avg_win_loss_ratio - (1 - win_rate)) / avg_win_loss_ratio
        kelly = max(0, kelly) * kelly_fraction
    else:
        kelly = 0.01
    
    confidence_factor = np.clip((confidence - 0.5) * 2, 0.1, 1.0)
    position = min(vol_position, kelly, max_position) * confidence_factor
    
    return float(np.clip(position, 0, max_position_pct))


def fractional_kelly_with_vol_target(
    win_rate: float,
    payoff_ratio: float,
    kelly_fraction: float = 0.25,
    target_volatility: float = 0.10,
    current_atr_ratio: float = 0.01,
    max_leverage: float = 2.0,
) -> Dict[str, float]:
    """Calculate position size using Kelly + volatility targeting.
    
    Args:
        win_rate: Probability of win
        payoff_ratio: Avg win / Avg loss
        kelly_fraction: Fraction of full Kelly
        target_volatility: Target daily volatility
        current_atr_ratio: Current ATR as % of price
        max_leverage: Maximum leverage
    
    Returns:
        Dict with sizing results
    """
    if win_rate <= 0 or payoff_ratio <= 0:
        kelly_size = 0.0
    else:
        kelly_edge = (win_rate * payoff_ratio - (1 - win_rate)) / payoff_ratio
        kelly_size = max(0, kelly_edge * kelly_fraction)
    
    effective_atr = max(current_atr_ratio, 0.0005)
    vol_size = target_volatility / (effective_atr * np.sqrt(252) + 1e-10)
    
    recommended = min(kelly_size, vol_size, max_leverage)
    
    return {
        "kelly_size": float(kelly_size),
        "vol_size": float(vol_size),
        "recommended_size": float(recommended),
        "leverage": float(recommended),
        "kelly_edge": float((win_rate * payoff_ratio - (1 - win_rate)) / max(payoff_ratio, 1e-10)),
    }


class TradeGatingEngine:
    """Multi-layer trade filtering system with thread safety."""
    
    def __init__(
        self,
        regime_threshold: float = 0.5,
        volatility_min: float = 0.001,
        volatility_max: float = 0.05,
        confidence_threshold: float = 0.55,
        max_uncertainty: float = 0.10,
        max_drawdown: float = -0.10,
        max_margin_util: float = 0.80,
        max_concentration: float = 0.30,
    ):
        """Initialize trade gating engine."""
        self.regime_threshold = regime_threshold
        self.volatility_min = volatility_min
        self.volatility_max = volatility_max
        self.confidence_threshold = confidence_threshold
        self.max_uncertainty = max_uncertainty
        self.max_drawdown = max_drawdown
        self.max_margin_util = max_margin_util
        self.max_concentration = max_concentration
        
        self.trade_count = 0
        self.gates_triggered = {}
        self._lock = RLock()
    
    def gate(
        self,
        probabilities: np.ndarray,
        regime: str = "UNKNOWN",
        regime_confidence: float = 0.5,
        volatility: float = 0.01,
        drawdown: float = 0.0,
        margin_utilization: float = 0.5,
        concentration: float = 0.1,
        uncertainty: float = 0.0,
    ) -> Dict[str, Any]:
        """Evaluate trade through multiple gates."""
        with self._lock:
            gates_passed = []
            gates_failed = []
            
            max_prob = np.max(probabilities) if len(probabilities) > 0 else 0.0
            
            if regime_confidence >= self.regime_threshold:
                gates_passed.append("regime")
            else:
                gates_failed.append("regime")
            
            if self.volatility_min <= volatility <= self.volatility_max:
                gates_passed.append("volatility")
            else:
                gates_failed.append("volatility")
            
            if max_prob >= self.confidence_threshold:
                gates_passed.append("confidence")
            else:
                gates_failed.append("confidence")
            
            if uncertainty <= self.max_uncertainty:
                gates_passed.append("uncertainty")
            else:
                gates_failed.append("uncertainty")
            
            if drawdown >= self.max_drawdown:
                gates_passed.append("drawdown")
            else:
                gates_failed.append("drawdown")
            
            if margin_utilization <= self.max_margin_util:
                gates_passed.append("margin")
            else:
                gates_failed.append("margin")
            
            if concentration <= self.max_concentration:
                gates_passed.append("concentration")
            else:
                gates_failed.append("concentration")
            
            allow_trade = len(gates_failed) == 0
            
            if allow_trade:
                self.trade_count += 1
            
            for gate in gates_failed:
                self.gates_triggered[gate] = self.gates_triggered.get(gate, 0) + 1
            
            return {
                "allow_trade": allow_trade,
                "gates_passed": gates_passed,
                "gates_failed": gates_failed,
                "regime": regime,
                "volatility": volatility,
                "confidence": max_prob,
                "uncertainty": uncertainty,
                "drawdown": drawdown,
                "margin_utilization": margin_utilization,
                "concentration": concentration,
                "trade_count": self.trade_count,
            }


class RiskBrain:
    """Integrated risk scoring and decision making engine."""
    
    def __init__(
        self,
        initial_capital: float = 100000.0,
        max_drawdown_pct: float = 0.20,
        max_position_pct: float = 0.05,
        target_volatility: float = 0.10,
    ):
        """Initialize risk brain."""
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.peak_capital = initial_capital
        self.max_drawdown_pct = max_drawdown_pct
        self.max_position_pct = max_position_pct
        self.target_volatility = target_volatility
        
        self.positions = {}
        self.gating_engine = TradeGatingEngine()
        self._lock = RLock()
    
    def assess_risk(
        self,
        symbol: str,
        signal: int,
        confidence: float,
        atr_ratio: float,
        market_volatility: float = 0.01,
        current_positions: Optional[Dict[str, float]] = None,
    ) -> RiskMetrics:
        """Comprehensive risk assessment for a trade."""
        with self._lock:
            if current_positions is None:
                current_positions = self.positions
            
            drawdown_pct = (self.current_capital - self.peak_capital) / max(self.peak_capital, 1e-10)
            
            total_exposure = sum(abs(qty) for qty in current_positions.values())
            concentration = abs(current_positions.get(symbol, 0)) / max(total_exposure, 1e-10)
            
            margin_util = min(total_exposure * 2, 1.0)
            
            if drawdown_pct < -self.max_drawdown_pct:
                level = RiskLevel.HALT
                allow = False
                reason = f"Drawdown {drawdown_pct:.2%} exceeds max"
            elif confidence < 0.55:
                level = RiskLevel.DANGER
                allow = False
                reason = f"Low confidence {confidence:.2%}"
            elif market_volatility > 0.05:
                level = RiskLevel.WARNING
                allow = True
                reason = "High volatility"
            else:
                level = RiskLevel.SAFE
                allow = True
                reason = "Conditions favorable"
            
            return RiskMetrics(
                level=level,
                drawdown_pct=drawdown_pct,
                margin_utilization=margin_util,
                position_concentration=concentration,
                volatility_regime="HIGH" if market_volatility > 0.02 else "NORMAL",
                confidence_score=confidence,
                allow_trade=allow,
                reason=reason,
            )
    
    def size_position(
        self,
        symbol: str,
        signal: int,
        confidence: float,
        atr_ratio: float,
        account_balance: float,
    ) -> float:
        """Calculate position size for trade."""
        with self._lock:
            if signal == 0:
                return 0.0
            
            size = calculate_position_size(
                confidence=confidence,
                current_atr_ratio=atr_ratio,
                target_volatility=self.target_volatility,
                max_position=self.max_position_pct,
                kelly_fraction=0.25,
                win_rate=0.55,
                avg_win_loss_ratio=1.5,
                max_position_pct=self.max_position_pct,
            )
            
            return size * account_balance
    
    def update_capital(self, new_capital: float) -> None:
        """Update current and peak capital."""
        with self._lock:
            self.current_capital = new_capital
            self.peak_capital = max(self.peak_capital, new_capital)


class ProductionRiskEngine:
    """Production-grade risk management system."""
    
    def __init__(
        self,
        initial_balance: float = 100000.0,
        max_daily_loss: float = 0.02,
        max_drawdown: float = 0.10,
        max_position_size: float = 0.05,
    ):
        """Initialize production risk engine."""
        self.initial_balance = initial_balance
        self.max_daily_loss = max_daily_loss
        self.max_drawdown = max_drawdown
        self.max_position_size = max_position_size
        
        self.current_balance = initial_balance
        self.daily_start_balance = initial_balance
        self.peak_balance = initial_balance
        
        self.positions = {}
        self.trades = []
        self.risk_alerts = []
        self._lock = RLock()
    
    def check_trade_allowed(
        self,
        position_size: float,
        current_price: float,
        portfolio_value: float,
    ) -> Tuple[bool, str]:
        """Check if trade is allowed based on risk constraints."""
        with self._lock:
            daily_loss = (self.daily_start_balance - self.current_balance) / max(self.daily_start_balance, 1e-10)
            if daily_loss > self.max_daily_loss:
                return False, f"Daily loss limit exceeded: {daily_loss:.2%}"
            
            drawdown = (self.peak_balance - self.current_balance) / max(self.peak_balance, 1e-10)
            if drawdown > self.max_drawdown:
                return False, f"Drawdown limit exceeded: {drawdown:.2%}"
            
            if portfolio_value > 0 and position_size / portfolio_value > self.max_position_size:
                return False, f"Position size exceeds limit"
            
            return True, "Trade allowed"
    
    def update_balance(self, new_balance: float) -> None:
        """Update current balance and track metrics."""
        with self._lock:
            self.current_balance = new_balance
            self.peak_balance = max(self.peak_balance, new_balance)
    
    def get_risk_metrics(self) -> Dict[str, float]:
        """Get current risk metrics."""
        with self._lock:
            daily_loss = (self.daily_start_balance - self.current_balance) / max(self.daily_start_balance, 1e-10)
            drawdown = (self.peak_balance - self.current_balance) / max(self.peak_balance, 1e-10)
            
            return {
                "current_balance": self.current_balance,
                "daily_loss_pct": daily_loss,
                "max_daily_loss_pct": self.max_daily_loss,
                "drawdown_pct": drawdown,
                "max_drawdown_pct": self.max_drawdown,
                "daily_loss_remaining": self.max_daily_loss - daily_loss,
                "drawdown_remaining": self.max_drawdown - drawdown,
            }
    
    def add_alert(self, alert: str) -> None:
        """Add risk alert."""
        with self._lock:
            timestamp = datetime.now(timezone.utc)
            self.risk_alerts.append({
                "timestamp": timestamp,
                "message": alert,
            })
            logger.warning(f"Risk Alert: {alert}")


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
