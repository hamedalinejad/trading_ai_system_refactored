"""
Live Module - Live trading execution and monitoring

v79 Components:
- Order management with state tracking
- Position lifecycle management  
- Risk monitoring and SL/TP handling
- Portfolio reconciliation
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timezone
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════════════════

class OrderState(str, Enum):
    """Order lifecycle states."""
    PENDING = "pending"
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class PositionState(str, Enum):
    """Position states."""
    OPEN = "open"
    CLOSING = "closing"
    CLOSED = "closed"
    ERROR = "error"


class OrderSide(str, Enum):
    """Order direction."""
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    """Order types."""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


# ═══════════════════════════════════════════════════════════════════════════
# EXCEPTION CLASSES
# ═══════════════════════════════════════════════════════════════════════════

class BrokerError(Exception):
    """Broker communication error."""
    pass


class OrderError(Exception):
    """Order management error."""
    pass


class PositionError(Exception):
    """Position tracking error."""
    pass


# ═══════════════════════════════════════════════════════════════════════════
# DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class Order:
    """Represents a single order."""
    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: float
    submitted_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    filled_at: Optional[datetime] = None
    filled_price: Optional[float] = None
    filled_quantity: float = 0.0
    status: OrderState = OrderState.PENDING
    error_message: str = ""
    
    def is_open(self) -> bool:
        """Check if order is still open."""
        return self.status in (OrderState.PENDING, OrderState.SUBMITTED, 
                              OrderState.ACCEPTED, OrderState.PARTIALLY_FILLED)
    
    def is_filled(self) -> bool:
        """Check if order is fully filled."""
        return self.status == OrderState.FILLED
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['side'] = self.side.value
        data['order_type'] = self.order_type.value
        data['status'] = self.status.value
        data['submitted_at'] = self.submitted_at.isoformat()
        data['filled_at'] = self.filled_at.isoformat() if self.filled_at else None
        return data


@dataclass
class Position:
    """Represents an open position."""
    symbol: str
    side: OrderSide
    quantity: float
    entry_price: float
    entry_time: datetime
    current_price: float = 0.0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    status: PositionState = PositionState.OPEN
    
    @property
    def pnl(self) -> float:
        """Calculate P&L in pips."""
        if self.side == OrderSide.BUY:
            return (self.current_price - self.entry_price) * self.quantity * 10000
        else:
            return (self.entry_price - self.current_price) * self.quantity * 10000
    
    @property
    def pnl_pct(self) -> float:
        """Calculate P&L percentage."""
        if self.entry_price == 0:
            return 0.0
        if self.side == OrderSide.BUY:
            return ((self.current_price - self.entry_price) / self.entry_price) * 100
        else:
            return ((self.entry_price - self.current_price) / self.entry_price) * 100
    
    def update_price(self, new_price: float) -> None:
        """Update current price."""
        self.current_price = new_price
    
    def should_close(self) -> Tuple[bool, Optional[str]]:
        """Check if position should be closed (SL/TP triggered)."""
        if self.side == OrderSide.BUY:
            if self.stop_loss and self.current_price <= self.stop_loss:
                return True, "stop_loss"
            if self.take_profit and self.current_price >= self.take_profit:
                return True, "take_profit"
        else:  # SELL
            if self.stop_loss and self.current_price >= self.stop_loss:
                return True, "stop_loss"
            if self.take_profit and self.current_price <= self.take_profit:
                return True, "take_profit"
        
        return False, None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "symbol": self.symbol,
            "side": self.side.value,
            "quantity": self.quantity,
            "entry_price": self.entry_price,
            "entry_time": self.entry_time.isoformat(),
            "current_price": self.current_price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "status": self.status.value,
            "pnl": self.pnl,
            "pnl_pct": self.pnl_pct,
        }


@dataclass
class ExecutionResult:
    """Result of order execution."""
    success: bool
    order: Optional[Order] = None
    position: Optional[Position] = None
    error: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "order": self.order.to_dict() if self.order else None,
            "position": self.position.to_dict() if self.position else None,
            "error": self.error,
        }


# ═══════════════════════════════════════════════════════════════════════════
# ORDER MANAGER
# ═══════════════════════════════════════════════════════════════════════════

class OrderManager:
    """Manage order lifecycle."""
    
    def __init__(self):
        """Initialize order manager."""
        self.orders: Dict[str, Order] = {}
        self._next_order_id = 1
    
    def create_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        price: float,
        order_type: OrderType = OrderType.MARKET
    ) -> Order:
        """Create new order."""
        order_id = f"ORD_{self._next_order_id}"
        self._next_order_id += 1
        
        order = Order(
            order_id=order_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
        )
        
        self.orders[order_id] = order
        return order
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID."""
        return self.orders.get(order_id)
    
    def get_open_orders(self) -> List[Order]:
        """Get all open orders."""
        return [o for o in self.orders.values() if o.is_open()]
    
    def update_order_status(
        self,
        order_id: str,
        status: OrderState,
        filled_price: Optional[float] = None,
        filled_qty: Optional[float] = None
    ) -> bool:
        """Update order status."""
        order = self.get_order(order_id)
        if not order:
            return False
        
        order.status = status
        if filled_price:
            order.filled_price = filled_price
        if filled_qty:
            order.filled_quantity = filled_qty
            if filled_qty >= order.quantity:
                order.status = OrderState.FILLED
                order.filled_at = datetime.now(timezone.utc)
        
        return True
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel order."""
        order = self.get_order(order_id)
        if order and order.is_open():
            order.status = OrderState.CANCELLED
            return True
        return False


# ═══════════════════════════════════════════════════════════════════════════
# POSITION MANAGER
# ═══════════════════════════════════════════════════════════════════════════

class PositionManager:
    """Manage open positions."""
    
    def __init__(self):
        """Initialize position manager."""
        self.positions: Dict[str, Position] = {}
    
    def open_position(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        entry_price: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> Position:
        """Open new position."""
        position = Position(
            symbol=symbol,
            side=side,
            quantity=quantity,
            entry_price=entry_price,
            entry_time=datetime.now(timezone.utc),
            current_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
        )
        
        key = f"{symbol}:{side.value}"
        self.positions[key] = position
        return position
    
    def get_position(self, symbol: str, side: OrderSide) -> Optional[Position]:
        """Get position."""
        key = f"{symbol}:{side.value}"
        return self.positions.get(key)
    
    def get_all_positions(self) -> List[Position]:
        """Get all positions."""
        return list(self.positions.values())
    
    def update_position(self, symbol: str, side: OrderSide, current_price: float) -> bool:
        """Update position price."""
        position = self.get_position(symbol, side)
        if position:
            position.update_price(current_price)
            return True
        return False
    
    def close_position(self, symbol: str, side: OrderSide, exit_price: float) -> bool:
        """Close position."""
        position = self.get_position(symbol, side)
        if position:
            position.current_price = exit_price
            position.status = PositionState.CLOSED
            
            key = f"{symbol}:{side.value}"
            del self.positions[key]
            return True
        return False
    
    def get_portfolio_pnl(self) -> Tuple[float, float]:
        """Get total portfolio P&L."""
        if not self.positions:
            return 0.0, 0.0
        
        total_pnl = sum(p.pnl for p in self.positions.values())
        total_quantity = sum(p.quantity for p in self.positions.values())
        
        total_pnl_pct = (
            sum(p.pnl_pct * p.quantity for p in self.positions.values()) /
            max(total_quantity, 1e-10)
        )
        return total_pnl, total_pnl_pct


# ═══════════════════════════════════════════════════════════════════════════
# LIVE TRADING ENGINE
# ═══════════════════════════════════════════════════════════════════════════

class LiveTradingEngine:
    """Main live trading orchestrator."""
    
    def __init__(self):
        """Initialize engine."""
        self.order_manager = OrderManager()
        self.position_manager = PositionManager()
        self.is_running = False
        self.logger = logger
    
    def start(self) -> None:
        """Start trading engine."""
        self.is_running = True
        self.logger.info("Live trading engine started")
    
    def stop(self) -> None:
        """Stop trading engine."""
        self.is_running = False
        self.logger.info("Live trading engine stopped")
    
    async def submit_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        price: float,
        order_type: OrderType = OrderType.MARKET,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
    ) -> ExecutionResult:
        """Submit order to market."""
        if not self.is_running:
            return ExecutionResult(
                success=False,
                error="Engine not running"
            )
        
        try:
            # Create order
            order = self.order_manager.create_order(
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price,
                order_type=order_type,
            )
            
            # Simulate order execution
            await asyncio.sleep(0.01)  # Simulate broker latency
            self.order_manager.update_order_status(
                order.order_id,
                OrderState.FILLED,
                filled_price=price,
                filled_qty=quantity
            )
            
            # Open position
            position = self.position_manager.open_position(
                symbol=symbol,
                side=side,
                quantity=quantity,
                entry_price=price,
                stop_loss=stop_loss,
                take_profit=take_profit,
            )
            
            return ExecutionResult(
                success=True,
                order=order,
                position=position,
            )
        
        except Exception as e:
            return ExecutionResult(
                success=False,
                error=str(e)
            )
    
    async def close_position(
        self,
        symbol: str,
        side: OrderSide,
        exit_price: float,
    ) -> ExecutionResult:
        """Close position."""
        if not self.is_running:
            return ExecutionResult(
                success=False,
                error="Engine not running"
            )
        
        try:
            # Get position
            position = self.position_manager.get_position(symbol, side)
            if not position:
                return ExecutionResult(
                    success=False,
                    error="Position not found"
                )
            
            # Close position
            self.position_manager.close_position(symbol, side, exit_price)
            
            return ExecutionResult(
                success=True,
                position=position,
            )
        
        except Exception as e:
            return ExecutionResult(
                success=False,
                error=str(e)
            )
    
    def get_positions(self) -> List[Position]:
        """Get all positions."""
        return self.position_manager.get_all_positions()
    
    def get_orders(self) -> List[Order]:
        """Get open orders."""
        return self.order_manager.get_open_orders()
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get portfolio summary."""
        positions = self.get_positions()
        total_pnl, total_pnl_pct = self.position_manager.get_portfolio_pnl()
        
        return {
            "is_running": self.is_running,
            "total_positions": len(positions),
            "total_orders": len(self.get_orders()),
            "total_pnl": total_pnl,
            "total_pnl_pct": total_pnl_pct,
            "positions": [p.to_dict() for p in positions],
            "orders": [o.to_dict() for o in self.get_orders()],
        }


# ═══════════════════════════════════════════════════════════════════════════
# EXPORTS
# ═══════════════════════════════════════════════════════════════════════════

__all__ = [
    # Enums
    "OrderState",
    "PositionState",
    "OrderSide",
    "OrderType",
    
    # Exceptions
    "BrokerError",
    "OrderError",
    "PositionError",
    
    # Classes
    "Order",
    "Position",
    "ExecutionResult",
    "OrderManager",
    "PositionManager",
    "LiveTradingEngine",
]
