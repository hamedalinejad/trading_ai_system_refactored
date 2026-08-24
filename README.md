# Trading AI System (Refactored) v0.79.4

Production-grade algorithmic trading system with automated indicator/strategy discovery, feature engineering, ML models (LightGBM), backtesting, risk management and live-ready structure.

Optimized for **CPU laptops** and multi-timeframe Parquet data (5-year history).

## Supported Data Format

Parquet or CSV with columns:

```
timestamp, open, high, low, close, volume, spread, symbol, timeframe, is_market_open
```

Example (multi-timeframe in one file is supported):

```
1/2/2020 12:00 AM,1.12188,1.12189,1.12178,1.12182,68930000,5,EURUSD,1min,1
1/2/2020 12:00 AM,1.12188,1.1219,1.12178,1.12189,130850000,4,EURUSD,5min,1
...
```

## Quick Start (CPU Laptop)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Verify system
python main.py system info
python main.py system verify

# 3. Run discovery on your 5-year parquet (recommended timeframe for discovery: 1h or 4h)
python main.py discovery \
  -p EURUSD \
  -d /path/to/your_5y_data.parquet \
  --timeframe 1h \
  --top 20 \
  --workers 2

# 4. Interactive menu
python main.py
```

### Recommended settings for 5-year 1-min data on laptop

- Use higher timeframes for discovery (`1h`, `4h`, `1d`) to keep memory under control.
- Filter is automatic: symbol + timeframe + is_market_open.
- `n_workers=2` (or leave default) is safe on dual-core machines.
- Results are saved to `outputs/discovery_EURUSD_1h.json`.

## Main Commands

| Command | Description |
|---------|-------------|
| `python main.py discovery -d data.parquet --timeframe 1h` | Discover best indicators |
| `python main.py backtest -p EURUSD` | Run backtest |
| `python main.py train -m eurusd` | Train models |
| `python main.py system info` | System status |
| `python main.py` | Interactive menu |

## Project Structure

```
trading_ai_system/
├── core/          # Config, logging, errors
├── data/          # Load/clean parquet/csv, validation, resampling
├── features/      # Technical indicators + feature cache
├── discovery/     # Automated indicator ranking & combination search
├── strategy/      # Signal generation, walk-forward, backtest metrics
├── models/        # LightGBM / sklearn models
├── risk/          # Position sizing & risk limits
├── live/          # Live trading stubs
└── utils/         # Helpers
```

## Notes for large datasets

- 5 years of 1-minute EURUSD ≈ 1.8–2.6 M rows. Prefer loading only the needed timeframe.
- The discovery command automatically filters `symbol` and `timeframe` columns.
- Feature cache is enabled by default to avoid recomputation.
- For very large files use `--timeframe 4h` or `1d` first.

## License

MIT
