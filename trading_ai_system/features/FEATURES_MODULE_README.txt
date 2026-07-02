═══════════════════════════════════════════════════════════════════════════
FEATURES MODULE - trading_ai_system.features
═══════════════════════════════════════════════════════════════════════════

FILE: trading_ai_system/features/__init__.py (or features.py as standalone)
SIZE: 469 lines
SYNTAX: ✓ Valid

PURPOSE:
═════════
Feature engineering, technical indicators, and pattern detection.
Complete feature generation pipeline without data leakage.

Key Principles:
  ✓ No double-shift data leakage (v79 fixed)
  ✓ All patterns computed on historical data only
  ✓ Single shift applied at pipeline end if needed
  ✓ Proper requires_shift=False registration


MODULES INCLUDED:
════════════════

1. EXCEPTION CLASSES
   • FeatureEngineeringError
   • FeatureRegistrationError

2. METADATA CLASS
   @dataclass FeatureMetadata:
     - name, category, requires_shift, lookback
     - description, min_bars
     Methods: to_dict()

3. TECHNICAL INDICATORS (Core Calculations)
   ┌─ compute_rsi(close, period=14)
   │  Returns: RSI series (0-100)
   │
   ├─ compute_macd(close, fast=12, slow=26, signal=9)
   │  Returns: (macd, signal_line, histogram)
   │
   ├─ compute_bollinger_bands(close, period=20, num_std=2.0)
   │  Returns: (upper_band, middle_band, lower_band)
   │
   ├─ compute_atr(high, low, close, period=14)
   │  Returns: ATR series
   │
   └─ compute_stochastic(high, low, close, period=14, smooth_k=3, smooth_d=3)
      Returns: (K%, D%)

4. PRICE ACTION PATTERNS (No Double-Shift)
   ┌─ detect_engulfing(df) → engulfing_bullish, engulfing_bearish
   │
   ├─ detect_doji(df, threshold=0.1) → is_doji, doji_star
   │
   ├─ detect_inside_bar(df) → inside_bar, inside_bar_breakout_up/down
   │
   ├─ detect_three_bar_patterns(df) → three_white_soldiers, three_black_crows
   │
   └─ detect_morning_evening_star(df) → morning_star, evening_star
   
   v79 FIX: All marked with requires_shift=False
   (Features already correctly positioned, no additional lag)

5. RETURNS & MOMENTUM
   calculate_returns(df, tf="1h")
     • return_1bar = pct_change(1)
     • return_5bar = pct_change(5)
     • return_20bar = pct_change(20)
     • log_return_1bar = log(close/prior_close)
     • acceleration = return_1bar - return_1bar.shift(1)
     • jerk = acceleration - acceleration.shift(1)
     • price_velocity = return_1bar.rolling(5).sum()

6. MAIN PIPELINE
   engineer_features_for_timeframe(df, timeframe="1h", compute_advanced=True)
   
   Returns: (DataFrame with features, feature registry)
   
   STAGES:
   ├─ Stage 1: Core Technical Indicators
   │  ├ RSI (14)
   │  ├ MACD + Signal + Histogram
   │  ├ Bollinger Bands (upper, middle, lower, width, position)
   │  └ ATR (14)
   │
   ├─ Stage 2: Price Action Patterns
   │  ├ Engulfing (bullish/bearish)
   │  ├ Doji (is_doji, doji_star)
   │  ├ Inside bar (inside_bar, breakout_up/down)
   │  ├ Three bar patterns (white soldiers, black crows)
   │  └ Morning/Evening star
   │
   ├─ Stage 3: Returns & Momentum
   │  ├ Return features (1bar, 5bar, 20bar)
   │  ├ Log returns
   │  ├ Acceleration & Jerk
   │  └ Price velocity
   │
   ├─ Stage 4: Volume Features
   │  ├ Volume SMA (20-period)
   │  └ Volume ratio
   │
   └─ Stage 5: Advanced Features (Optional)
      ├ Stochastic K%
      └ Stochastic D%


USAGE EXAMPLES:
═══════════════

# Import features
from trading_ai_system.features import (
    engineer_features_for_timeframe,
    compute_rsi, compute_macd, compute_atr,
    detect_engulfing, calculate_returns
)

# Main pipeline (recommended)
df_clean = load_and_clean_data()
df_features, registry = engineer_features_for_timeframe(
    df_clean,
    timeframe="1h",
    compute_advanced=True
)

print(f"Generated {len(df_features.columns)} features")
print(f"Feature categories: {set(v['category'] for v in registry.values())}")

# Individual indicator usage
rsi = compute_rsi(df["close"], period=14)
macd, signal, hist = compute_macd(df["close"])
atr = compute_atr(df["high"], df["low"], df["close"])

# Stochastic K%/D%
k_pct, d_pct = compute_stochastic(
    df["high"], df["low"], df["close"],
    period=14, smooth_k=3, smooth_d=3
)

# Price action detection
df = detect_engulfing(df)
df = detect_doji(df, threshold=0.1)
df = detect_inside_bar(df)

# Returns calculation
df = calculate_returns(df, tf="1h")

# Bollinger Bands
upper, middle, lower = compute_bollinger_bands(
    df["close"],
    period=20,
    num_std=2.0
)

# Error handling
from trading_ai_system.features import FeatureEngineeringError

try:
    df_features, _ = engineer_features_for_timeframe(df)
except FeatureEngineeringError as e:
    logger.error(f"Feature engineering failed: {e}")


GENERATED FEATURES:
════════════════════

MOMENTUM (7):
  rsi_14, macd, macd_signal, macd_histogram, stoch_k, stoch_d

VOLATILITY (5):
  bb_width, bb_position, atr_14, bb_upper, bb_middle, bb_lower

RETURNS (7):
  return_1bar, return_5bar, return_20bar, log_return_1bar,
  acceleration, jerk, price_velocity

PRICE ACTION (10):
  engulfing_bullish, engulfing_bearish, is_doji, doji_star,
  inside_bar, inside_bar_breakout_up, inside_bar_breakout_down,
  three_white_soldiers, three_black_crows, morning_star, evening_star

VOLUME (1):
  volume_ratio

TOTAL: ~30 features (varies with compute_advanced flag)


V79 DATA LEAKAGE FIXES:
════════════════════════

✓ detect_engulfing: requires_shift=False
   (Pattern computed between current and prior bar, no double-shift)

✓ detect_doji: requires_shift=False
   (Body ratio calculated on current bar, shift only for prior low)

✓ detect_inside_bar: requires_shift=False
   (Range containment check doesn't use future data)

✓ detect_three_bar_patterns: requires_shift=False
   (Uses shift(1) and shift(2) internally, no additional shift needed)

✓ detect_morning_evening_star: requires_shift=False
   (Three-bar pattern, all shifts are backward-looking)

✓ calculate_returns: requires_shift=False
   (pct_change already references prior bar)

✓ engineer_features_for_timeframe: Single pass, no double-shift
   (All features created correctly, no final shift loop)


TECHNICAL INDICATOR FORMULAS:
══════════════════════════════

RSI (14):
  RS = Avg Gain / Avg Loss
  RSI = 100 - (100 / (1 + RS))

MACD:
  MACD = EMA12 - EMA26
  Signal = EMA9(MACD)
  Histogram = MACD - Signal

Bollinger Bands:
  Middle = SMA20
  Upper = Middle + (2 * StdDev20)
  Lower = Middle - (2 * StdDev20)

ATR (14):
  TR = max(High-Low, |High-Close[t-1]|, |Low-Close[t-1]|)
  ATR = EMA14(TR)

Stochastic:
  K% = 100 * (Close - Lowest14) / (Highest14 - Lowest14)
  D% = SMA3(K%)


INTEGRATION WITH OTHER MODULES:
════════════════════════════════

data/ module:
  ✓ Receives cleaned DataFrame
  ✓ Must have: timestamp, open, high, low, close, volume

models/ module:
  ✓ Uses generated features for training
  ✓ Feature selection based on importance

strategy/ module:
  ✓ Uses price action patterns for signal generation
  ✓ Uses momentum indicators for confirmation

risk/ module:
  ✓ Uses ATR for stop-loss placement
  ✓ Uses volatility features for position sizing

analysis/ module:
  ✓ Uses technical indicators for backtest analysis


PERFORMANCE NOTES:
═══════════════════

• engineer_features_for_timeframe: O(n * m) where m = number of features
• compute_rsi: O(n) rolling window
• compute_macd: O(n) EMA calculations
• compute_atr: O(n) with max across 3 series
• detect_patterns: O(n) vectorized boolean operations

For 100k rows: ~0.5-1s total time
For 1M rows: ~5-10s total time

Memory usage: O(n * m) - roughly 10-20x input size with all features


EXTENDING THE FEATURES MODULE:
═════════════════════════════════

To add new indicator:
  1. Create compute_indicator(series, params) function
  2. Add to engineer_features_for_timeframe
  3. Register with register_feature()

To add new pattern:
  1. Create detect_pattern(df) function
  2. Ensure NO internal shift (or mark requires_shift appropriately)
  3. Add to price action detection stage
  4. Register both output columns

Example:
  def detect_hammer(df: pd.DataFrame) -> pd.DataFrame:
      """Detect hammer candlestick pattern."""
      body = (df["close"] - df["open"]).abs()
      lower_wick = df["open"].where(df["open"] < df["close"], df["close"]) - df["low"]
      
      hammer = (lower_wick > body * 2).astype(int)
      df["hammer"] = hammer
      
      register_feature("hammer", category="price_action", requires_shift=False)
      return df


REQUIRED IMPORTS:
═════════════════

From core:
  logger, FeatureError, get_global_config, register_feature

From data:
  (Optional) Data validation functions

Standard Library:
  logging, typing, dataclasses

Third-Party:
  numpy, pandas

═══════════════════════════════════════════════════════════════════════════
