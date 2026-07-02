═══════════════════════════════════════════════════════════════════════════
LIVE TRADING MODULE - trading_ai_system.live
═══════════════════════════════════════════════════════════════════════════

FILE: trading_ai_system/live/__init__.py (or live.py as standalone)
SIZE: 555 lines
SYNTAX: ✓ Valid

PURPOSE:
═════════
Real-time trading execution, order management, and position tracking.
Complete live trading infrastructure for:
  • Order submission and lifecycle management
  • Position tracking and P&L calculation
  • Risk management (SL/TP monitoring)
  • Portfolio summary and reporting


MODULES INCLUDED:
════════════════

1. ENUMS
   OrderState: PENDING, SUBMITTED, ACCEPTED, PARTIALLY_FILLED,
              FILLED, CANCELLED, REJECTED, EXPIRED
   
   PositionState: OPEN, CLOSING, CLOSED, ERROR

2. EXCEPTION CLASSES
   • BrokerError - Broker connection/communication error
   • OrderError - Order submission/management error
   • PositionError - Position tracking/reconciliation error

3. DATA CLASSES

   @dataclass Order:
     - order_id, symbol, side, order_type
     - quantity, price, submitted_at
     - filled_at, filled_price, filled_quantity
     - status, error_message
     Methods: is_open(), is_filled(), to_dict()
   
   @dataclass Position:
     - symbol, side, quantity, entry_price, entry_time
     - current_price, stop_loss, take_profit
     - status, pnl, pnl_pct
     Methods: update_price(), should_close(), to_dict()
   
   @dataclass ExecutionResult:
     - success, order, position, error
     Methods: to_dict()

4. ORDER MANAGEMENT
   class OrderManager:
     • create_order(symbol, side, quantity, price, order_type)
     • get_order(order_id)
     • get_open_orders()
     • update_order_status(order_id, status, filled_price, filled_qty)
     • cancel_order(order_id)

5. POSITION MANAGEMENT
   class PositionManager:
     • open_position(symbol, side, quantity, entry_price, SL, TP)
     • get_position(symbol, side)
     • get_all_positions()
     • update_position(symbol, side, current_price)
     • close_position(symbol, side, exit_price)
     • get_portfolio_pnl() → (total_pnl, total_pnl_pct)

6. LIVE TRADING ENGINE
   class LiveTradingEngine:
     Main orchestrator for live trading
     
     • start() - Start trading engine
     • stop() - Stop trading engine
     • async submit_order(...) - Submit order to broker
     • async close_position(symbol, side, exit_price) - Close position
     • get_positions() - Get all open positions
     • get_orders() - Get all open orders
     • get_portfolio_summary() - Get complete portfolio snapshot


USAGE EXAMPLES:
═══════════════

# Import live trading components
from trading_ai_system.live import (
    LiveTradingEngine, OrderSide, OrderType,
    Order, Position, ExecutionResult
)
from core import OrderSide, OrderType

# Initialize engine
engine = LiveTradingEngine()

# Start trading
engine.start()

# Submit a BUY order with risk management
result = await engine.submit_order(
    symbol="EURUSD",
    side=OrderSide.BUY,
    quantity=1.0,
    price=1.0850,
    order_type=OrderType.LIMIT,
    stop_loss=1.0800,
    take_profit=1.0900
)

if result.success:
    order = result.order
    position = result.position
    print(f"Order {order.order_id} filled at {order.filled_price}")
    print(f"Position P&L: {position.pnl:.2f} ({position.pnl_pct:.2f}%)")
else:
    print(f"Order failed: {result.error}")

# Update position with current price
engine.position_manager.update_position("EURUSD", OrderSide.BUY, 1.0870)
position = engine.position_manager.get_position("EURUSD", OrderSide.BUY)
print(f"Current P&L: {position.pnl:.2f}")

# Check if position should close (SL/TP)
should_close, reason = position.should_close()
if should_close:
    result = await engine.close_position(
        symbol="EURUSD",
        side=OrderSide.BUY,
        exit_price=1.0900  # TP triggered
    )

# Get portfolio summary
summary = engine.get_portfolio_summary()
print(f"Total Positions: {summary['total_positions']}")
print(f"Total P&L: {summary['total_pnl']:.2f}")
print(f"Total P&L %: {summary['total_pnl_pct']:.2f}%")

# Get open orders
open_orders = engine.get_orders()
for order in open_orders:
    print(f"{order.order_id}: {order.side.value} {order.quantity} @ {order.price}")

# Get all positions
positions = engine.get_positions()
for pos in positions:
    print(f"{pos.symbol}: {pos.side.value} {pos.quantity} PnL={pos.pnl:.2f}")

# Stop trading
engine.stop()


ORDER LIFECYCLE:
════════════════

BUY/SELL SIGNAL
    ↓
CREATE ORDER (PENDING)
    ↓
SUBMIT TO BROKER (SUBMITTED)
    ↓
BROKER ACCEPTS (ACCEPTED)
    ↓
PARTIAL FILL? → PARTIALLY_FILLED → (wait more fills)
    ↓
FULLY FILLED (FILLED)
    ↓
OPEN POSITION
    ↓
UPDATE PRICE (monitor SL/TP)
    ↓
SL/TP TRIGGERED
    ↓
SUBMIT CLOSING ORDER
    ↓
CLOSE POSITION (CLOSED)


POSITION MONITORING:
═════════════════════

Open Position:
  • symbol: "EURUSD"
  • side: BUY
  • quantity: 1.0
  • entry_price: 1.0850
  • current_price: 1.0870
  • stop_loss: 1.0800
  • take_profit: 1.0900
  • pnl: 20.0 (pips)
  • pnl_pct: 0.18%

P&L Calculation:
  BUY:  pnl = (current - entry) * quantity
        pnl_pct = ((current - entry) / entry) * 100
  
  SELL: pnl = (entry - current) * quantity
        pnl_pct = ((entry - current) / entry) * 100


RISK MANAGEMENT FEATURES:
═════════════════════════

1. STOP LOSS (SL)
   • Automatic exit at loss limit
   • Triggered when price hits SL level
   • Triggered by: position.should_close()

2. TAKE PROFIT (TP)
   • Automatic exit at profit target
   • Triggered when price hits TP level
   • Triggered by: position.should_close()

3. ORDER STATES
   • PENDING: Order created, not submitted
   • SUBMITTED: Sent to broker, waiting confirmation
   • ACCEPTED: Broker accepted, waiting fill
   • PARTIALLY_FILLED: Partial execution
   • FILLED: Complete execution
   • CANCELLED: User cancelled
   • REJECTED: Broker rejected
   • EXPIRED: Order expired (time-based)

4. POSITION STATES
   • OPEN: Active position
   • CLOSING: Close order submitted
   • CLOSED: Position closed
   • ERROR: Error during operation


ASYNC OPERATIONS:
═════════════════

Both order submission and position closing are async:

async def run_trading():
    engine = LiveTradingEngine()
    engine.start()
    
    # Submit order
    result = await engine.submit_order(
        symbol="EURUSD",
        side=OrderSide.BUY,
        quantity=1.0,
        price=1.0850
    )
    
    # Close position
    result = await engine.close_position(
        symbol="EURUSD",
        side=OrderSide.BUY,
        exit_price=1.0900
    )
    
    engine.stop()

# Run async function
asyncio.run(run_trading())


PORTFOLIO SUMMARY:
═══════════════════

{
    "is_running": true,
    "total_positions": 2,
    "total_orders": 1,
    "total_pnl": 250.50,
    "total_pnl_pct": 2.45,
    "positions": [
        {
            "symbol": "EURUSD",
            "side": "buy",
            "quantity": 1.0,
            "entry_price": 1.0850,
            "current_price": 1.0900,
            "pnl": 50.00,
            "pnl_pct": 0.46
        },
        {
            "symbol": "GBPUSD",
            "side": "sell",
            "quantity": 2.0,
            "entry_price": 1.2750,
            "current_price": 1.2700,
            "pnl": 100.00,
            "pnl_pct": 0.39
        }
    ],
    "orders": [...]
}


INTEGRATION WITH OTHER MODULES:
════════════════════════════════

features/ module:
  ✓ Provides signals for order submission
  ✓ Uses indicators for SL/TP calculation

models/ module:
  ✓ Generates trading signals
  ✓ Confidence scores for order sizing

strategy/ module:
  ✓ Defines entry/exit rules
  ✓ Uses position data for adjustments

risk/ module:
  ✓ Monitors positions for risk limits
  ✓ Enforces position sizing

core/ module:
  ✓ Provides OrderSide, OrderType enums
  ✓ System health tracking


ERROR HANDLING:
════════════════

try:
    result = await engine.submit_order(...)
    
    if result.success:
        print(f"Order {result.order.order_id} filled")
    else:
        print(f"Order failed: {result.error}")

except BrokerError as e:
    logger.error(f"Broker error: {e}")
    update_system_health("degraded", error=e)

except OrderError as e:
    logger.error(f"Order error: {e}")

except PositionError as e:
    logger.error(f"Position error: {e}")


EXTENDING THE LIVE MODULE:
═════════════════════════════

To add broker connector:
  1. Create BrokerConnector class
  2. Implement submit_order(), cancel_order(), get_status()
  3. Integrate with LiveTradingEngine

To add position reconciliation:
  1. Implement reconciliation logic
  2. Compare broker positions vs internal state
  3. Handle discrepancies

To add advanced risk management:
  1. Add trailing stop functionality
  2. Add dynamic position sizing
  3. Add portfolio-level risk limits


PERFORMANCE NOTES:
═══════════════════

• Order submission: ~100ms (simulated, real broker varies)
• Position update: O(1)
• Portfolio calculation: O(n) where n = number of positions
• Typical portfolio: <10 positions, <1ms update time

For production:
  ✓ Replace simulated broker with real API
  ✓ Implement order callbacks from broker
  ✓ Add database persistence
  ✓ Implement audit logging


REQUIRED IMPORTS:
═════════════════

From core:
  logger, ExecutionError, LiveTradingError, get_global_config,
  get_system_health, update_system_health, OrderType, OrderSide

Standard Library:
  asyncio, logging, datetime, typing, dataclasses, enum

Third-Party:
  numpy, pandas

═══════════════════════════════════════════════════════════════════════════
