# Main Entry Point - Usage Guide

## Overview

The `main.py` script is the primary entry point for the Trading AI System. It provides both:
1. **Interactive Menu System** - User-friendly graphical menu
2. **CLI Commands** - Command-line interface for automation

## Structure

```
├── main.py                  # Main entry point (executable)
├── cli/
│   ├── __init__.py         # CLI package initialization
│   ├── menu_system.py      # Interactive menu implementation
│   └── commands.py         # All CLI commands
└── trading_ai_system/      # Core system modules
    ├── core/
    ├── data/
    ├── features/
    ├── models/
    ├── strategy/
    ├── risk/
    ├── live/
    └── utils/
```

## Usage

### 1. Interactive Menu (Default)

Simply run with no arguments to show interactive menu:

```bash
python main.py
```

This displays an interactive menu with all options:
```
╔═══════════════════════════════════════════════════════════════════════════╗
║          🤖 TRADING AI SYSTEM v0.79.0                                    ║
║   Production-grade algorithmic trading system with ML models             ║
╚═══════════════════════════════════════════════════════════════════════════╝

┌─ MAIN MENU ──────────────────────────────────────────────────────────────┐
│  1. 🎯 Backtest Strategy                                                 │
│  2. 🏋️  Train Models                                                     │
│  3. 📈 Live Trading                                                      │
│  4. 📊 Data Management                                                   │
│  5. ⚙️  Configuration                                                     │
│  6. 📉 Analysis                                                          │
│  7. ⚡ Settings                                                          │
│  8. ℹ️  Help                                                             │
│  0. ❌ Exit                                                              │
└──────────────────────────────────────────────────────────────────────────┘

Select option: 
```

### 2. CLI Commands

Use CLI for automation and scripting:

```bash
# Show help
python main.py --help

# Backtest with parameters
python main.py backtest -p EURUSD -s 2023-01-01 -e 2023-12-31 -c 10000

# Train model
python main.py train -m eurusd --epochs 100

# Start live trading
python main.py live -p EURUSD --dry-run

# Fetch data
python main.py data fetch -p EURUSD -s 2023-01-01

# Validate data
python main.py data validate -f data/eurusd.csv

# Show configuration
python main.py config show

# Run analysis
python main.py analysis -p EURUSD --type indicators
```

---

## Commands

### Backtest Command

Run strategy backtests:

```bash
python main.py backtest [options]
```

**Options:**
- `-p, --pair` - Trading pair (default: EURUSD)
- `-s, --start` - Start date (YYYY-MM-DD)
- `-e, --end` - End date (YYYY-MM-DD)
- `-c, --capital` - Initial capital (default: 10000)
- `--config` - Backtest config file

**Example:**
```bash
python main.py backtest -p EURUSD -s 2023-01-01 -e 2023-12-31 -c 50000
```

### Train Command

Train machine learning models:

```bash
python main.py train [options]
```

**Options:**
- `-m, --model` - Model name (default: eurusd)
- `-d, --data` - Path to training data
- `--epochs` - Number of epochs (default: 100)

**Example:**
```bash
python main.py train -m eurusd --epochs 200 -d data/training.csv
```

### Live Command

Start live trading:

```bash
python main.py live [options]
```

**Options:**
- `-p, --pair` - Trading pair (default: EURUSD)
- `-a, --account` - Account ID
- `--dry-run` - Dry run mode (no real trades)

**Example:**
```bash
python main.py live -p EURUSD --dry-run
```

### Data Command

Manage data:

```bash
python main.py data <subcommand> [options]
```

**Subcommands:**

#### Fetch
```bash
python main.py data fetch [options]
```

Options:
- `-p, --pair` - Trading pair
- `-s, --start` - Start date
- `-e, --end` - End date

#### Validate
```bash
python main.py data validate [options]
```

Options:
- `-f, --file` - Data file path

**Examples:**
```bash
python main.py data fetch -p EURUSD -s 2023-01-01
python main.py data validate -f data/eurusd.csv
```

### Config Command

Manage configuration:

```bash
python main.py config <subcommand> [options]
```

**Subcommands:**

#### Show
```bash
python main.py config show
```

#### Set
```bash
python main.py config set <key> <value>
```

**Examples:**
```bash
python main.py config show
python main.py config set trading_pair GBPUSD
```

### Analysis Command

Analyze data and results:

```bash
python main.py analysis [options]
```

**Options:**
- `-p, --pair` - Trading pair (default: EURUSD)
- `--type` - Analysis type (indicators, signals, performance)

**Examples:**
```bash
python main.py analysis -p EURUSD --type indicators
python main.py analysis --type performance
```

---

## Global Options

These options work with all commands:

```bash
python main.py [global_options] <command> [command_options]
```

**Global Options:**
- `--version` - Show version
- `--config <file>` - Load config file
- `-v, --verbose` - Verbose output (DEBUG level)
- `-q, --quiet` - Quiet mode (ERROR level only)

**Examples:**
```bash
python main.py --verbose backtest -p EURUSD
python main.py --config config.json train -m eurusd
python main.py --quiet live --dry-run
```

---

## Interactive Menu Structure

### Main Menu
- 1: Backtest Strategy
- 2: Train Models
- 3: Live Trading
- 4: Data Management
- 5: Configuration
- 6: Analysis
- 7: Settings
- 0: Exit

### Backtest Menu (Option 1)
- 1: Run Backtest
- 2: View Results
- 3: Export Report
- 4: Compare Runs

### Train Menu (Option 2)
- 1: Train New Model
- 2: Retrain Existing
- 3: View Models
- 4: Evaluate Model
- 5: Feature Importance

### Live Menu (Option 3)
- 1: Start Live Trading
- 2: View Active Orders
- 3: Close Position
- 4: Portfolio Status
- 5: Risk Settings

### Data Menu (Option 4)
- 1: Fetch Data
- 2: Validate Data
- 3: View Data
- 4: Data Statistics
- 5: Clear Cache

### Config Menu (Option 5)
- 1: Show Configuration
- 2: Edit Configuration
- 3: Load Config File
- 4: Save Configuration
- 5: Reset to Defaults

### Analysis Menu (Option 6)
- 1: Technical Indicators
- 2: Trading Signals
- 3: Performance Metrics
- 4: Risk Analysis
- 5: Correlation Analysis

---

## Installation

### 1. Place Files

```
project_root/
├── main.py                          # Main entry point
├── cli/
│   ├── __init__.py
│   ├── menu_system.py
│   └── commands.py
├── trading_ai_system/               # Core system
├── setup.py
└── pyproject.toml
```

### 2. Install Package

```bash
pip install -e .
```

### 3. Run

```bash
python main.py
```

---

## Examples

### Complete Backtest Workflow

```bash
# Interactive menu
python main.py
# Select: 1 (Backtest)
# Select: 1 (Run Backtest)
# Enter pair, dates, capital

# OR CLI
python main.py backtest -p EURUSD -s 2023-01-01 -e 2023-12-31 -c 10000
```

### Complete Training Workflow

```bash
# Fetch data first
python main.py data fetch -p EURUSD -s 2023-01-01 -e 2023-12-31

# Validate data
python main.py data validate -f data/eurusd.csv

# Train model
python main.py train -m eurusd --epochs 200
```

### Complete Live Trading Setup

```bash
# Show current config
python main.py config show

# Update risk settings
python main.py config set max_daily_loss 0.05

# Start dry run
python main.py live -p EURUSD --dry-run

# View live menu in interactive mode
python main.py
# Select: 3 (Live Trading)
```

---

## Environment Variables

Set environment variables for defaults:

```bash
export TRADING_PAIR=EURUSD
export TRADING_CAPITAL=10000
export TRADING_MODE=demo
```

---

## Configuration

### Configuration File

Create `config.json`:

```json
{
  "trading_pair": "EURUSD",
  "timeframe": "H1",
  "strategy": "MLStrategy",
  "risk_per_trade": 0.02,
  "max_daily_loss": 0.05,
  "use_stop_loss": true,
  "use_take_profit": true,
  "model_name": "eurusd",
  "broker": "oanda"
}
```

Load configuration:

```bash
python main.py --config config.json backtest -p EURUSD
```

---

## Logging

### Verbose Mode

```bash
python main.py --verbose backtest -p EURUSD
```

Shows DEBUG level logs.

### Quiet Mode

```bash
python main.py --quiet backtest -p EURUSD
```

Shows only ERROR level logs.

### Log File

Logs are saved to:
```
logs/trading_ai_system.log
```

---

## Troubleshooting

### ImportError

```
ImportError: No module named 'cli'
```

**Solution:** Ensure you're in the project root directory and the package is installed:

```bash
cd project_root
pip install -e .
python main.py
```

### ModuleNotFoundError

```
ModuleNotFoundError: No module named 'trading_ai_system'
```

**Solution:** Install the package in development mode:

```bash
pip install -e .
```

### Permission Denied

```
PermissionError: [Errno 13] Permission denied: 'main.py'
```

**Solution:** Make script executable:

```bash
chmod +x main.py
```

Then run:

```bash
./main.py
```

---

## Performance Tips

### Use CLI for Batch Processing

For automated workflows, use CLI commands:

```bash
#!/bin/bash
# backtest.sh

python main.py data fetch -p EURUSD -s 2023-01-01 -e 2023-12-31
python main.py train -m eurusd --epochs 100
python main.py backtest -p EURUSD -s 2023-01-01 -e 2023-12-31
```

### Parallel Backtests

```bash
python main.py backtest -p EURUSD -s 2023-01-01 -e 2023-12-31 &
python main.py backtest -p GBPUSD -s 2023-01-01 -e 2023-12-31 &
wait
```

---

## API Integration

For programmatic usage, import directly:

```python
from trading_ai_system import core, data, models, strategy

# Initialize
config = core.CONFIG
config['data_dir'] = './data'

# Use components
fetcher = data.DataFetcher()
ohlcv = fetcher.fetch('EURUSD', start='2023-01-01', end='2023-12-31')

# Train
model = models.LGBModel(name='eurusd')
model.train(features, labels)

# Strategy
strat = strategy.MLStrategy(model=model)
signals = strat.generate_signals(features)
```

---

## File Placement

```
project_root/
├── main.py                          ← Executable entry point
├── cli/                             ← CLI package
│   ├── __init__.py
│   ├── menu_system.py              ← Interactive menu
│   └── commands.py                 ← CLI commands
├── trading_ai_system/              ← Core system
├── configs/                        ← Configuration files
├── data/                           ← Data directory
├── models/                         ← Trained models
├── logs/                           ← Log files
├── setup.py
├── pyproject.toml
└── README.md
```

---

## Next Steps

1. **Place files** - Copy main.py and cli/ to project root
2. **Install** - Run `pip install -e .`
3. **Run** - Execute `python main.py`
4. **Explore** - Try different menu options or CLI commands

For detailed setup, see: SETUP_PLACEMENT_GUIDE.md

---

**Version:** 0.79.0
**Created:** 2024
**Last Updated:** 2024
