#!/usr/bin/env python3
"""
Trading AI System - Main Entry Point

This is the main entry point for the Trading AI System.
Provides CLI interface for running the system components.

Usage:
    python main.py                  # Show interactive menu
    python main.py --help           # Show help
    python main.py backtest         # Run backtest
    python main.py train            # Train models
    python main.py live             # Start live trading
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.absolute()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from trading_ai_system import __version__
from trading_ai_system.core import CONFIG, StateManager, logger

# Import CLI modules
from cli.menu_system import InteractiveMenu
from cli.commands import (
    BacktestCommand,
    TrainCommand,
    LiveCommand,
    DataCommand,
    ConfigCommand,
    AnalysisCommand,
)


# ═══════════════════════════════════════════════════════════════════════════
# LOGGER SETUP
# ═══════════════════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# ARGUMENT PARSER
# ═══════════════════════════════════════════════════════════════════════════

def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        prog='Trading AI System',
        description=f'Production-grade algorithmic trading system (v{__version__})',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                      # Interactive menu
  python main.py backtest -p EURUSD   # Backtest EUR/USD
  python main.py train -m eurusd      # Train EUR/USD model
  python main.py live -p EURUSD       # Start live trading
  python main.py data fetch -p EURUSD # Fetch data
  python main.py config show          # Show configuration

For more information, visit: https://github.com/yourusername/trading-ai-system
        """,
    )

    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {__version__}',
    )

    parser.add_argument(
        '--config',
        type=str,
        default=None,
        help='Path to config file',
    )

    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Verbose output',
    )

    parser.add_argument(
        '--quiet',
        '-q',
        action='store_true',
        help='Quiet mode (errors only)',
    )

    # Subcommands
    subparsers = parser.add_subparsers(
        dest='command',
        help='Command to execute',
    )

    # Backtest command
    backtest_parser = subparsers.add_parser(
        'backtest',
        help='Run backtesting',
    )
    backtest_parser.add_argument(
        '-p', '--pair',
        type=str,
        default='EURUSD',
        help='Trading pair (default: EURUSD)',
    )
    backtest_parser.add_argument(
        '-s', '--start',
        type=str,
        help='Start date (YYYY-MM-DD)',
    )
    backtest_parser.add_argument(
        '-e', '--end',
        type=str,
        help='End date (YYYY-MM-DD)',
    )
    backtest_parser.add_argument(
        '-c', '--capital',
        type=float,
        default=10000,
        help='Initial capital (default: 10000)',
    )
    backtest_parser.add_argument(
        '--config',
        type=str,
        help='Backtest config file',
    )

    # Train command
    train_parser = subparsers.add_parser(
        'train',
        help='Train models',
    )
    train_parser.add_argument(
        '-m', '--model',
        type=str,
        default='eurusd',
        help='Model name (default: eurusd)',
    )
    train_parser.add_argument(
        '-d', '--data',
        type=str,
        help='Path to training data',
    )
    train_parser.add_argument(
        '--epochs',
        type=int,
        default=100,
        help='Number of epochs (default: 100)',
    )

    # Live command
    live_parser = subparsers.add_parser(
        'live',
        help='Start live trading',
    )
    live_parser.add_argument(
        '-p', '--pair',
        type=str,
        default='EURUSD',
        help='Trading pair (default: EURUSD)',
    )
    live_parser.add_argument(
        '-a', '--account',
        type=str,
        help='Account ID',
    )
    live_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Dry run (no actual trades)',
    )

    # Data command
    data_parser = subparsers.add_parser(
        'data',
        help='Data management',
    )
    data_subparsers = data_parser.add_subparsers(
        dest='data_command',
        help='Data subcommand',
    )

    # Data fetch
    fetch_parser = data_subparsers.add_parser(
        'fetch',
        help='Fetch data',
    )
    fetch_parser.add_argument(
        '-p', '--pair',
        type=str,
        default='EURUSD',
        help='Trading pair',
    )
    fetch_parser.add_argument(
        '-s', '--start',
        type=str,
        help='Start date',
    )
    fetch_parser.add_argument(
        '-e', '--end',
        type=str,
        help='End date',
    )

    # Data validate
    validate_parser = data_subparsers.add_parser(
        'validate',
        help='Validate data',
    )
    validate_parser.add_argument(
        '-f', '--file',
        type=str,
        required=True,
        help='Data file path',
    )

    # Config command
    config_parser = subparsers.add_parser(
        'config',
        help='Configuration management',
    )
    config_subparsers = config_parser.add_subparsers(
        dest='config_command',
        help='Config subcommand',
    )

    # Config show
    config_subparsers.add_parser(
        'show',
        help='Show configuration',
    )

    # Config set
    set_parser = config_subparsers.add_parser(
        'set',
        help='Set configuration value',
    )
    set_parser.add_argument(
        'key',
        type=str,
        help='Config key',
    )
    set_parser.add_argument(
        'value',
        type=str,
        help='Config value',
    )

    # Analysis command
    analysis_parser = subparsers.add_parser(
        'analysis',
        help='Data analysis and visualization',
    )
    analysis_parser.add_argument(
        '-p', '--pair',
        type=str,
        default='EURUSD',
        help='Trading pair',
    )
    analysis_parser.add_argument(
        '--type',
        type=str,
        choices=['indicators', 'signals', 'performance'],
        default='indicators',
        help='Analysis type',
    )

    return parser


# ═══════════════════════════════════════════════════════════════════════════
# MAIN FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def run_interactive_menu() -> None:
    """Run interactive menu system."""
    logger.info(f"Starting Trading AI System v{__version__}")
    menu = InteractiveMenu()
    menu.run()


def run_command(args: argparse.Namespace) -> int:
    """Run CLI command."""
    try:
        # Configure logging
        if args.quiet:
            logging.getLogger().setLevel(logging.ERROR)
        elif args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)

        # Load config
        if args.config:
            CONFIG.load_from_file(args.config)

        logger.info(f"Trading AI System v{__version__}")

        # Route to appropriate command
        if args.command == 'backtest':
            cmd = BacktestCommand(args)
            return cmd.execute()

        elif args.command == 'train':
            cmd = TrainCommand(args)
            return cmd.execute()

        elif args.command == 'live':
            cmd = LiveCommand(args)
            return cmd.execute()

        elif args.command == 'data':
            cmd = DataCommand(args)
            return cmd.execute()

        elif args.command == 'config':
            cmd = ConfigCommand(args)
            return cmd.execute()

        elif args.command == 'analysis':
            cmd = AnalysisCommand(args)
            return cmd.execute()

        else:
            logger.error(f"Unknown command: {args.command}")
            return 1

    except Exception as e:
        logger.error(f"Command failed: {e}", exc_info=args.verbose)
        return 1


def main() -> int:
    """Main entry point."""
    # If no arguments, show interactive menu
    if len(sys.argv) == 1:
        run_interactive_menu()
        return 0

    # Parse arguments
    parser = create_parser()
    args = parser.parse_args()

    # If no command specified, show interactive menu
    if not args.command:
        run_interactive_menu()
        return 0

    # Execute command
    return run_command(args)


if __name__ == '__main__':
    sys.exit(main())
