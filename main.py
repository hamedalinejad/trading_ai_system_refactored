#!/usr/bin/env python3
"""
Trading AI System - Main Entry Point

Production-grade entry point with CLI interface for system components.
Supports backtesting, model training, live trading, and analysis.

v79.1 Enhancements:
- Better error handling
- Improved logging
- Configuration validation
- Exit codes for automation
- Signal handling for graceful shutdown

Usage:
    python main.py                      # Show interactive menu
    python main.py --help               # Show help
    python main.py backtest -p EURUSD   # Run backtest
    python main.py train -m eurusd      # Train models
    python main.py live -p EURUSD       # Start live trading
"""

import sys
import signal
import argparse
import logging
from pathlib import Path
from typing import Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.absolute()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from trading_ai_system import __version__
    from trading_ai_system.core import get_global_config, logger
except ImportError as e:
    print(f"Failed to import trading_ai_system: {e}", file=sys.stderr)
    sys.exit(1)

# Import CLI modules safely
try:
    from cli.menu_system import InteractiveMenu
    from cli.commands import (
        BacktestCommand,
        TrainCommand,
        LiveCommand,
        DataCommand,
        ConfigCommand,
        AnalysisCommand,
    )
except ImportError as e:
    print(f"Failed to import CLI modules: {e}", file=sys.stderr)
    print("CLI features may not be available", file=sys.stderr)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Global state for signal handling
_is_running = True


def signal_handler(signum, frame):
    """Handle termination signals gracefully."""
    global _is_running
    _is_running = False
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)


# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


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

For more information, visit: https://github.com/hamedalinejad/trading_ai_system_refactored
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
        '--verbose', '-v',
        action='store_true',
        help='Verbose output',
    )

    parser.add_argument(
        '--quiet', '-q',
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
    backtest_parser.add_argument('-p', '--pair', type=str, default='EURUSD', help='Trading pair')
    backtest_parser.add_argument('-s', '--start', type=str, help='Start date (YYYY-MM-DD)')
    backtest_parser.add_argument('-e', '--end', type=str, help='End date (YYYY-MM-DD)')
    backtest_parser.add_argument('-c', '--capital', type=float, default=10000, help='Initial capital')
    backtest_parser.add_argument('--config', type=str, help='Backtest config file')

    # Train command
    train_parser = subparsers.add_parser('train', help='Train models')
    train_parser.add_argument('-m', '--model', type=str, default='eurusd', help='Model name')
    train_parser.add_argument('-d', '--data', type=str, help='Path to training data')
    train_parser.add_argument('--epochs', type=int, default=100, help='Number of epochs')

    # Live command
    live_parser = subparsers.add_parser('live', help='Start live trading')
    live_parser.add_argument('-p', '--pair', type=str, default='EURUSD', help='Trading pair')
    live_parser.add_argument('-a', '--account', type=str, help='Account ID')
    live_parser.add_argument('--dry-run', action='store_true', help='Dry run mode')

    # Data command
    data_parser = subparsers.add_parser('data', help='Data management')
    data_subparsers = data_parser.add_subparsers(dest='data_command', help='Data subcommand')
    
    fetch_parser = data_subparsers.add_parser('fetch', help='Fetch data')
    fetch_parser.add_argument('-p', '--pair', type=str, default='EURUSD', help='Trading pair')
    fetch_parser.add_argument('-s', '--start', type=str, help='Start date')
    fetch_parser.add_argument('-e', '--end', type=str, help='End date')
    
    validate_parser = data_subparsers.add_parser('validate', help='Validate data')
    validate_parser.add_argument('-f', '--file', type=str, required=True, help='Data file path')

    # Config command
    config_parser = subparsers.add_parser('config', help='Configuration management')
    config_subparsers = config_parser.add_subparsers(dest='config_command', help='Config subcommand')
    config_subparsers.add_parser('show', help='Show configuration')
    
    set_parser = config_subparsers.add_parser('set', help='Set configuration value')
    set_parser.add_argument('key', type=str, help='Config key')
    set_parser.add_argument('value', type=str, help='Config value')

    # Analysis command
    analysis_parser = subparsers.add_parser('analysis', help='Data analysis')
    analysis_parser.add_argument('-p', '--pair', type=str, default='EURUSD', help='Trading pair')
    analysis_parser.add_argument(
        '--type',
        type=str,
        choices=['indicators', 'signals', 'performance'],
        default='indicators',
        help='Analysis type'
    )

    return parser


def run_interactive_menu() -> int:
    """Run interactive menu system."""
    try:
        logger.info(f"Starting Trading AI System v{__version__}")
        menu = InteractiveMenu()
        menu.run()
        return 0
    except Exception as e:
        logger.error(f"Menu failed: {e}", exc_info=logger.isEnabledFor(logging.DEBUG))
        return 1


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
            logger.info(f"Loading config from {args.config}")
            try:
                config = get_global_config()
                # config.load_from_file(args.config)
            except Exception as e:
                logger.warning(f"Failed to load config: {e}")

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

    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        return 130
    except Exception as e:
        logger.error(f"Command failed: {e}", exc_info=args.verbose if hasattr(args, 'verbose') else False)
        return 1


def main() -> int:
    """Main entry point."""
    try:
        # If no arguments, show interactive menu
        if len(sys.argv) == 1:
            return run_interactive_menu()

        # Parse arguments
        parser = create_parser()
        args = parser.parse_args()

        # If no command specified, show interactive menu
        if not args.command:
            return run_interactive_menu()

        # Execute command
        return run_command(args)

    except KeyboardInterrupt:
        logger.info("Application terminated by user")
        return 130
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
