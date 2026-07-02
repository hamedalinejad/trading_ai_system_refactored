"""
Risk Management Module for Trading AI System

v79 Components:
- TradeGatingEngine: Multi-layer trade filtering (regime, volatility, confidence)
- RiskBrain: Integrated risk scoring and decision making
- ProductionRiskEngine: Position sizing, drawdown monitoring, margin management
- PositionSizer: Kelly criterion with volatility targeting
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timezone
import asyncio

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# ENUMS & DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════════

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


@dataclass
class PositionSizeResult:
    """Position sizing calculation result."""
    size: float
    kelly_size: float
    vol_size: float
    confidence_factor: float
    constraints: List[str]


# ═══════════════════════════════════════════════════════════════════════════
# POSITION SIZING
# ═══════════════════════════════════════════════════════════════════════════

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
    
    v79 FIX: Position sizing with multiple safety bounds
    - ATR-based volatility targeting
    - Fractional Kelly criterion (25% default)
    - Confidence scaling
    - Hard cap at max_position_pct
    
    Args:
        confidence: Model confidence (0.0 to 1.0)
        current_atr_ratio: Current ATR as % of price
        target_volatility: Target daily volatility (default 10%)
        max_position: Position as % of capital
        kelly_fraction: Fraction of Kelly criterion (0.25 = 25%)
        win_rate: Historical win rate
        avg_win_loss_ratio: Avg win / avg loss ratio
        max_position_pct: Hard cap on position size
    
    Returns:
        float: Position size as fraction of capital (0 to max_position)
    """
    # Effective ATR (minimum 0.05% to prevent division errors)
    effective_atr = max(current_atr_ratio, 0.0005)
    
    # Volatility-based sizing
    vol_position = target_volatility / (effective_atr * np.sqrt(252) + 1e-10)
    vol_position = min(vol_position, max_position)
    
    # Kelly criterion (fractional)
    if win_rate > 0 and avg_win_loss_ratio > 0:
        kelly = (win_rate * avg_win_loss_ratio - (1 - win_rate)) / avg_win_loss_ratio
        kelly = max(0, kelly) * kelly_fraction
    else:
        kelly = 0.01
    
    # Confidence scaling (0.5→0.1, 1.0→1.0)
    confidence_factor = np.clip((confidence - 0.5) * 2, 0.1, 1.0)
    
    # Final position size: min(vol, kelly, max) * confidence
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
    
    v79 FIX: Combines Kelly criterion with volatility targeting
    - Kelly size based on edge (win_rate, payoff_ratio)
    - Vol target to keep daily risk constant
    - Leverage cap for safety
    
    Args:
        win_rate: Probability of win (0.0 to 1.0)
        payoff_ratio: Avg win / Avg loss
        kelly_fraction: Fraction of full Kelly (0.25 default)
        target_volatility: Target daily volatility
        current_atr_ratio: Current ATR as % of price
        max_leverage: Maximum leverage multiplier
    
    Returns:
        Dict with keys: kelly_size, vol_size, recommended_size, leverage
    """
    # Kelly criterion
    if win_rate <= 0 or payoff_ratio <= 0:
        kelly_size = 0.0
    else:
        kelly_edge = (win_rate * payoff_ratio - (1 - win_rate)) / payoff_ratio
        kelly_size = max(0, kelly_edge * kelly_fraction)
    
    # Volatility targeting
    effective_atr = max(current_atr_ratio, 0.0005)
    vol_size = target_volatility / (effective_atr * np.sqrt(252) + 1e-10)
    
    # Recommended size: minimum of both approaches
    recommended = min(kelly_size, vol_size, max_leverage)
    
    return {
        "kelly_size": float(kelly_size),
        "vol_size": float(vol_size),
        "recommended_size": float(recommended),
        "leverage": float(recommended),
        "kelly_edge": float((win_rate * payoff_ratio - (1 - win_rate)) / max(payoff_ratio, 1e-10)),
    }


# ═══════════════════════════════════════════════════════════════════════════
# TRADE GATING ENGINE
# ═══════════════════════════════════════════════════════════════════════════

class TradeGatingEngine:
    """Multi-layer trade filtering system.
    
    v79 FIX: Prevent bad trades through multiple validation layers:
    1. Regime filter (volatility, trend conditions)
    2. Volatility bounds (avoid extreme regimes)
    3. Confidence threshold (model certainty)
    4. Risk metrics (drawdown, margin, concentration)
    """
    
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
        """Initialize trade gating engine.
        
        Args:
            regime_threshold: Minimum regime confidence (0.0-1.0)
            volatility_min: Minimum acceptable volatility
            volatility_max: Maximum acceptable volatility
            confidence_threshold: Model confidence threshold
            max_uncertainty: Maximum prediction uncertainty
            max_drawdown: Maximum drawdown allowed (e.g., -0.10 = -10%)
            max_margin_util: Maximum margin utilization (e.g., 0.80 = 80%)
            max_concentration: Maximum position concentration
        """
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
        """Evaluate trade through multiple gates.
        
        Args:
            probabilities: Model output probabilities [P_down, P_neutral, P_up]
            regime: Current market regime name
            regime_confidence: Confidence in regime classification
            volatility: Current volatility (as decimal, e.g., 0.02 = 2%)
            drawdown: Current drawdown (e.g., -0.05 = -5%)
            margin_utilization: Margin used / available
            concentration: Largest position as % of capital
            uncertainty: Model prediction uncertainty
        
        Returns:
            Dict with gate_allowed (bool) and reason for any block
        """
        self.trade_count += 1
        result = {
            "gate_allowed": True,
            "gates_triggered": [],
            "confidence": float(np.max(probabilities)) if len(probabilities) > 0 else 0.0,
            "reason": "ALLOWED",
        }
        
        # Gate 1: Confidence threshold
        if result["confidence"] < self.confidence_threshold:
            result["gate_allowed"] = False
            result["gates_triggered"].append("low_confidence")
            result["reason"] = f"Confidence {result['confidence']:.2%} < {self.confidence_threshold:.2%}"
            self.gates_triggered["low_confidence"] = self.gates_triggered.get("low_confidence", 0) + 1
            return result
        
        # Gate 2: Uncertainty threshold
        if uncertainty > self.max_uncertainty:
            result["gate_allowed"] = False
            result["gates_triggered"].append("high_uncertainty")
            result["reason"] = f"Uncertainty {uncertainty:.2%} > {self.max_uncertainty:.2%}"
            self.gates_triggered["high_uncertainty"] = self.gates_triggered.get("high_uncertainty", 0) + 1
            return result
        
        # Gate 3: Volatility bounds
        if volatility < self.volatility_min or volatility > self.volatility_max:
            result["gate_allowed"] = False
            result["gates_triggered"].append("volatility_extreme")
            result["reason"] = f"Vol {volatility:.2%} outside [{self.volatility_min:.2%}, {self.volatility_max:.2%}]"
            self.gates_triggered["volatility_extreme"] = self.gates_triggered.get("volatility_extreme", 0) + 1
            return result
        
        # Gate 4: Regime filter
        if regime_confidence < self.regime_threshold:
            result["gate_allowed"] = False
            result["gates_triggered"].append("low_regime_confidence")
            result["reason"] = f"Regime confidence {regime_confidence:.2%} < {self.regime_threshold:.2%}"
            self.gates_triggered["low_regime_confidence"] = self.gates_triggered.get("low_regime_confidence", 0) + 1
            return result
        
        # Gate 5: Drawdown limit
        if drawdown < self.max_drawdown:
            result["gate_allowed"] = False
            result["gates_triggered"].append("max_drawdown_exceeded")
            result["reason"] = f"Drawdown {drawdown:.2%} < {self.max_drawdown:.2%}"
            self.gates_triggered["max_drawdown_exceeded"] = self.gates_triggered.get("max_drawdown_exceeded", 0) + 1
            return result
        
        # Gate 6: Margin utilization
        if margin_utilization > self.max_margin_util:
            result["gate_allowed"] = False
            result["gates_triggered"].append("high_margin_utilization")
            result["reason"] = f"Margin {margin_utilization:.2%} > {self.max_margin_util:.2%}"
            self.gates_triggered["high_margin_utilization"] = self.gates_triggered.get("high_margin_utilization", 0) + 1
            return result
        
        # Gate 7: Position concentration
        if concentration > self.max_concentration:
            result["gate_allowed"] = False
            result["gates_triggered"].append("high_concentration")
            result["reason"] = f"Concentration {concentration:.2%} > {self.max_concentration:.2%}"
            self.gates_triggered["high_concentration"] = self.gates_triggered.get("high_concentration", 0) + 1
            return result
        
        return result
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get gating statistics."""
        total_gates = sum(self.gates_triggered.values())
        return {
            "total_trades_evaluated": self.trade_count,
            "total_trades_blocked": total_gates,
            "block_rate": total_gates / max(self.trade_count, 1),
            "gates_triggered": self.gates_triggered.copy(),
        }


# ═══════════════════════════════════════════════════════════════════════════
# RISK BRAIN
# ═══════════════════════════════════════════════════════════════════════════

class RiskBrain:
    """Integrated risk assessment and decision making.
    
    v79 FIX: Comprehensive risk evaluation combining:
    - Position sizing
    - Risk metrics
    - Trade gating
    - Portfolio constraints
    """
    
    def __init__(
        self,
        initial_capital: float = 10000.0,
        max_drawdown_pct: float = 0.15,
        max_position_pct: float = 0.05,
        target_volatility: float = 0.10,
    ):
        """Initialize risk brain.
        
        Args:
            initial_capital: Starting capital
            max_drawdown_pct: Maximum tolerated drawdown
            max_position_pct: Maximum position size
            target_volatility: Target daily volatility
        """
        self.initial_capital = initial_capital
        self.max_drawdown_pct = max_drawdown_pct
        self.max_position_pct = max_position_pct
        self.target_volatility = target_volatility
        
        self.current_capital = initial_capital
        self.peak_capital = initial_capital
        self.positions = {}  # symbol -> qty
        
        self.gating_engine = TradeGatingEngine()
    
    def assess_risk(
        self,
        symbol: str,
        signal: int,
        confidence: float,
        atr_ratio: float,
        market_volatility: float = 0.01,
        current_positions: Optional[Dict[str, float]] = None,
    ) -> RiskMetrics:
        """Comprehensive risk assessment for a potential trade.
        
        Args:
            symbol: Trading symbol
            signal: -1 (sell), 0 (hold), 1 (buy)
            confidence: Model confidence
            atr_ratio: Current ATR ratio
            market_volatility: Current market volatility
            current_positions: Current open positions
        
        Returns:
            RiskMetrics with assessment result
        """
        if current_positions is None:
            current_positions = self.positions
        
        # Calculate drawdown
        drawdown_pct = (self.current_capital - self.peak_capital) / self.peak_capital
        
        # Calculate position concentration
        total_exposure = sum(abs(qty) for qty in current_positions.values())
        concentration = abs(current_positions.get(symbol, 0)) / max(total_exposure, 1e-10)
        
        # Calculate margin utilization (simplified)
        margin_util = min(total_exposure * 2, 1.0)
        
        # Determine risk level
        if drawdown_pct < -self.max_drawdown_pct:
            level = RiskLevel.HALT
            allow = False
            reason = f"Drawdown {drawdown_pct:.2%} exceeds max {self.max_drawdown_pct:.2%}"
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
        """Calculate position size for trade.
        
        Args:
            symbol: Trading symbol
            signal: Trade signal (-1, 0, 1)
            confidence: Model confidence
            atr_ratio: Current ATR ratio
            account_balance: Current account balance
        
        Returns:
            float: Position size as % of capital
        """
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
        """Update current and peak capital.
        
        Args:
            new_capital: New capital value
        """
        self.current_capital = new_capital
        self.peak_capital = max(self.peak_capital, new_capital)


# ═══════════════════════════════════════════════════════════════════════════
# PRODUCTION RISK ENGINE
# ═══════════════════════════════════════════════════════════════════════════

class ProductionRiskEngine:
    """Production-grade risk management system.
    
    v79 FIX: Enterprise-level risk controls:
    - Real-time position monitoring
    - Drawdown and margin tracking
    - Automatic trade halts
    - Risk metrics collection
    """
    
    def __init__(
        self,
        initial_balance: float = 100000.0,
        max_daily_loss: float = 0.02,
        max_drawdown: float = 0.10,
        max_position_size: float = 0.05,
    ):
        """Initialize production risk engine.
        
        Args:
            initial_balance: Starting account balance
            max_daily_loss: Maximum daily loss (2% default)
            max_drawdown: Maximum drawdown (10% default)
            max_position_size: Maximum single position (5% default)
        """
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
    
    def check_trade_allowed(
        self,
        position_size: float,
        current_price: float,
        portfolio_value: float,
    ) -> Tuple[bool, str]:
        """Check if trade is allowed based on risk constraints.
        
        Args:
            position_size: Proposed position size
            current_price: Current asset price
            portfolio_value: Total portfolio value
        
        Returns:
            (allowed, reason)
        """
        # Check daily loss limit
        daily_loss = (self.daily_start_balance - self.current_balance) / self.daily_start_balance
        if daily_loss > self.max_daily_loss:
            return False, f"Daily loss limit exceeded: {daily_loss:.2%}"
        
        # Check drawdown limit
        drawdown = (self.peak_balance - self.current_balance) / self.peak_balance
        if drawdown > self.max_drawdown:
            return False, f"Drawdown limit exceeded: {drawdown:.2%}"
        
        # Check position size limit
        if position_size / portfolio_value > self.max_position_size:
            return False, f"Position size exceeds limit: {position_size/portfolio_value:.2%}"
        
        return True, "Trade allowed"
    
    def update_balance(self, new_balance: float) -> None:
        """Update current balance and track metrics.
        
        Args:
            new_balance: New balance value
        """
        self.current_balance = new_balance
        self.peak_balance = max(self.peak_balance, new_balance)
    
    def get_risk_metrics(self) -> Dict[str, float]:
        """Get current risk metrics.
        
        Returns:
            Dict with risk statistics
        """
        daily_loss = (self.daily_start_balance - self.current_balance) / self.daily_start_balance
        drawdown = (self.peak_balance - self.current_balance) / self.peak_balance
        
        return {
            "current_balance": self.current_balance,
            "daily_loss_pct": daily_loss,
            "max_daily_loss_pct": self.max_daily_loss,
            "drawdown_pct": drawdown,
            "max_drawdown_pct": self.max_drawdown,
            "daily_loss_remaining": self.max_daily_loss - daily_loss,
            "drawdown_remaining": self.max_drawdown - drawdown,
        }


if __name__ == "__main__":
    # Test suite
    logger.info("Risk module loaded successfully")
    
    # Test position sizing
    size = calculate_position_size(
        confidence=0.65,
        current_atr_ratio=0.01,
        target_volatility=0.10,
    )
    logger.info(f"Position size: {size:.2%}")
    
    # Test trade gating
    gating = TradeGatingEngine()
    probs = np.array([0.2, 0.1, 0.7])
    result = gating.gate(probs, volatility=0.015, confidence_threshold=0.55)
    logger.info(f"Trade gate result: {result}")
