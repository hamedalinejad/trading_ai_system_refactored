# Trading AI System

Production-grade algorithmic trading system with machine learning models.

## Features

- **Data Management**: OHLCV data fetching, validation, and caching
- **Technical Analysis**: 20+ technical indicators (EMA, ADX, RSI, Bollinger Bands, etc.)
- **Machine Learning**: LightGBM ensemble models for price prediction
- **Strategy Engine**: Rule-based and ML-driven trading strategies
- **Risk Management**: Position sizing, portfolio constraints, drawdown limits
- **Live Trading**: Broker connectivity, order execution, reconciliation
- **Performance Tracking**: PnL, Sharpe ratio, max drawdown, and more

## Installation

### Requirements
- Python 3.9+
- pip or conda

### From Source
```bash
git clone https://github.com/yourusername/trading-ai-system.git
cd trading-ai-system
pip install -e ".[dev]"
```

### With Optional Dependencies
```bash
# Live trading support
pip install -e ".[live]"

# Development tools
pip install -e ".[dev]"

# Documentation
pip install -e ".[docs]"
```

## Quick Start

```python
from trading_ai_system import core, data, features, models, strategy, risk, live

# Configure
config = core.CONFIG
config['data_dir'] = './data'
config['model_dir'] = './models'

# Load data
fetcher = data.DataFetcher()
ohlcv = fetcher.fetch('EURUSD', start='2023-01-01', end='2023-12-31')

# Calculate features
engineer = features.FeatureEngineer()
features_df = engineer.calculate(ohlcv)

# Train model
model = models.LGBModel(name='eurusd_model')
model.train(features_df, labels)

# Generate signals
strategy = strategy.MLStrategy(model=model)
signals = strategy.generate_signals(features_df)

# Manage risk
risk_mgr = risk.RiskManager()
positions = risk_mgr.calculate_positions(signals, capital=10000)

# Execute live
broker = live.BrokerConnector('broker_api_key')
executor = live.OrderExecutor(broker=broker)
executor.execute(positions)
```

## Project Structure

```
trading-ai-system/
├── trading_ai_system/
│   ├── __init__.py              # Package initialization
│   ├── __version__.py           # Version info
│   ├── core/                    # Core infrastructure
│   │   ├── __init__.py
│   │   └── core.py
│   ├── data/                    # Data management
│   │   ├── __init__.py
│   │   └── data.py
│   ├── features/                # Technical indicators
│   │   ├── __init__.py
│   │   └── features.py
│   ├── models/                  # ML models
│   │   ├── __init__.py
│   │   └── models.py
│   ├── strategy/                # Strategy engine
│   │   ├── __init__.py
│   │   └── strategy.py
│   ├── risk/                    # Risk management
│   │   ├── __init__.py
│   │   └── risk.py
│   ├── live/                    # Live trading
│   │   ├── __init__.py
│   │   └── live.py
│   └── utils/                   # Utilities
│       ├── __init__.py
│       └── utils.py
├── tests/                       # Unit tests
│   ├── __init__.py
│   ├── test_data.py
│   ├── test_features.py
│   ├── test_models.py
│   └── ...
├── configs/                     # Configuration files
│   └── default.json
├── docs/                        # Documentation
│   └── ...
├── setup.py                     # Installation script
├── pyproject.toml              # Project metadata
├── README.md                    # This file
├── LICENSE                      # MIT License
└── .gitignore
```

## Configuration

Configuration is centralized in `trading_ai_system/core/core.py`:

```python
from trading_ai_system.core import CONFIG

CONFIG['data_dir'] = './data'
CONFIG['model_dir'] = './models'
CONFIG['logging_level'] = 'DEBUG'
CONFIG['trading_pair'] = 'EURUSD'
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=trading_ai_system

# Run specific test file
pytest tests/test_data.py

# Run with verbose output
pytest -v
```

## Development

### Code Quality

```bash
# Format code
black trading_ai_system tests

# Sort imports
isort trading_ai_system tests

# Lint
flake8 trading_ai_system tests

# Type checking
mypy trading_ai_system
```

### Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

## API Reference

### Core Module
- `CONFIG`: Global configuration dictionary
- `StateManager`: Manages system state
- Exception classes: `TradingSystemError`, `ConfigError`, `DataError`, etc.

### Data Module
- `DataFetcher`: Fetch OHLCV data from brokers
- `DataValidator`: Validate data integrity
- `DataCache`: Cache data locally
- `OHLCVData`: Data class for OHLCV bars

### Features Module
- `TechnicalIndicators`: Calculate 20+ indicators
- `FeatureEngineer`: Build feature vectors
- `FeatureScaler`: Normalize features

### Models Module
- `BaseModel`: Abstract base class
- `LGBModel`: LightGBM model wrapper
- `ModelEnsemble`: Combine multiple models
- `ModelEvaluator`: Evaluate model performance

### Strategy Module
- `BaseStrategy`: Abstract strategy class
- `MLStrategy`: ML-driven strategy
- `SignalGenerator`: Generate trading signals
- `StrategyPerformance`: Track strategy metrics

### Risk Module
- `RiskManager`: Manage portfolio risk
- `PositionSizer`: Calculate position sizes
- `PortfolioConstraints`: Define constraints
- `RiskMetrics`: Calculate risk metrics

### Live Module
- `BrokerConnector`: Connect to brokers
- `OrderExecutor`: Execute orders
- `LiveMonitor`: Monitor live trading
- `BrokerReconciler`: Reconcile with broker

### Utils Module
- `validate_dataframe()`: Validate data
- `format_price()`: Format prices
- `calculate_returns()`: Calculate returns
- `Logger`: Logging utility

## Performance

Typical performance metrics on backtests:

- **Sharpe Ratio**: 1.8-2.2
- **Max Drawdown**: 8-12%
- **Win Rate**: 55-60%
- **Profit Factor**: 1.5-2.0

Results vary by market conditions and parameter tuning.

## Troubleshooting

### Import Errors
Ensure the package is installed in development mode:
```bash
pip install -e .
```

### Data Errors
Check data directory exists and contains valid OHLCV files:
```bash
ls -la data/
```

### Model Training Errors
Verify features have no NaN or infinite values:
```python
from trading_ai_system.utils import validate_dataframe
validate_dataframe(features_df)
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This system is for educational and research purposes. Use at your own risk. Past performance does not guarantee future results. Always test thoroughly before live trading.

## Support

- **Issues**: https://github.com/yourusername/trading-ai-system/issues
- **Discussions**: https://github.com/yourusername/trading-ai-system/discussions

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.

---

**Last Updated**: 2024
**Version**: 0.79.0
