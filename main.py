#!/usr/bin/env python3
"""
Trading AI System - Main Entry Point

Production-grade entry point with CLI interface for system components.
Supports backtesting, model training, live trading, and analysis.

v79.4 Enhancements:
- Better error handling
- Improved logging
- Configuration validation
- Exit codes for automation
- Signal handling for graceful shutdown
- Discovery integration
- Feature caching
- Model persistence

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

PROJECT_ROOT = Path(__file__).parent.absolute()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    import trading_ai_system
    from trading_ai_system import (
        __version__,
        initialize_system,
        verify_modules,
        get_system_info,
        get_module_errors,
    )
except ImportError as e:
    print(f"Failed to import trading_ai_system: {e}", file=sys.stderr)
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

_is_running = True


def signal_handler(signum, frame):
    """Handle termination signals gracefully"""
    global _is_running
    _is_running = False
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser"""
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
  python main.py system info          # System information
  python main.py discovery -p EURUSD  # Run discovery

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

    subparsers = parser.add_subparsers(
        dest='command',
        help='Command to execute',
    )

    backtest_parser = subparsers.add_parser(
        'backtest',
        help='Run backtesting',
    )
    backtest_parser.add_argument('-p', '--pair', type=str, default='EURUSD', help='Trading pair')
    backtest_parser.add_argument('-s', '--start', type=str, help='Start date (YYYY-MM-DD)')
    backtest_parser.add_argument('-e', '--end', type=str, help='End date (YYYY-MM-DD)')
    backtest_parser.add_argument('-c', '--capital', type=float, default=10000, help='Initial capital')
    backtest_parser.add_argument('--config', type=str, help='Backtest config file')

    train_parser = subparsers.add_parser('train', help='Train models')
    train_parser.add_argument('-m', '--model', type=str, default='eurusd', help='Model name')
    train_parser.add_argument('-d', '--data', type=str, help='Path to training data')
    train_parser.add_argument('--epochs', type=int, default=100, help='Number of epochs')
    train_parser.add_argument('--enable-discovery', action='store_true', help='Enable discovery')
    train_parser.add_argument('--enable-caching', action='store_true', help='Enable feature caching')

    live_parser = subparsers.add_parser('live', help='Start live trading')
    live_parser.add_argument('-p', '--pair', type=str, default='EURUSD', help='Trading pair')
    live_parser.add_argument('-a', '--account', type=str, help='Account ID')
    live_parser.add_argument('--dry-run', action='store_true', help='Dry run mode')

    data_parser = subparsers.add_parser('data', help='Data management')
    data_subparsers = data_parser.add_subparsers(dest='data_command', help='Data subcommand')
    
    fetch_parser = data_subparsers.add_parser('fetch', help='Fetch data')
    fetch_parser.add_argument('-p', '--pair', type=str, default='EURUSD', help='Trading pair')
    fetch_parser.add_argument('-s', '--start', type=str, help='Start date')
    fetch_parser.add_argument('-e', '--end', type=str, help='End date')
    
    validate_parser = data_subparsers.add_parser('validate', help='Validate data')
    validate_parser.add_argument('-f', '--file', type=str, required=True, help='Data file path')

    config_parser = subparsers.add_parser('config', help='Configuration management')
    config_subparsers = config_parser.add_subparsers(dest='config_command', help='Config subcommand')
    config_subparsers.add_parser('show', help='Show configuration')
    
    set_parser = config_subparsers.add_parser('set', help='Set configuration value')
    set_parser.add_argument('key', type=str, help='Config key')
    set_parser.add_argument('value', type=str, help='Config value')

    analysis_parser = subparsers.add_parser('analysis', help='Data analysis')
    analysis_parser.add_argument('-p', '--pair', type=str, default='EURUSD', help='Trading pair')
    analysis_parser.add_argument(
        '--type',
        type=str,
        choices=['indicators', 'signals', 'performance'],
        default='indicators',
        help='Analysis type'
    )

    discovery_parser = subparsers.add_parser('discovery', help='Indicator discovery')
    discovery_parser.add_argument('-p', '--pair', type=str, default='EURUSD', help='Trading pair')
    discovery_parser.add_argument('-d', '--data', type=str, help='Path to data file')
    discovery_parser.add_argument('-t', '--top', type=int, default=10, help='Top N indicators')

    system_parser = subparsers.add_parser('system', help='System information')
    system_subparsers = system_parser.add_subparsers(dest='system_command', help='System subcommand')
    system_subparsers.add_parser('info', help='Show system info')
    system_subparsers.add_parser('verify', help='Verify modules')
    system_subparsers.add_parser('errors', help='Show module errors')

    return parser


def run_interactive_menu() -> int:
    """Run interactive menu system"""
    try:
        logger.info(f"Starting Trading AI System v{__version__}")
        
        try:
            from cli.menu_system import InteractiveMenu
            menu = InteractiveMenu()
            menu.run()
            return 0
        except ImportError:
            logger.error("CLI modules not available")
            return 1
    except Exception as e:
        logger.error(f"Menu failed: {e}", exc_info=logger.isEnabledFor(logging.DEBUG))
        return 1


def handle_discovery_command(args: argparse.Namespace) -> int:
    """Handle discovery command"""
    try:
        from trading_ai_system import discovery, data, features
        
        if not discovery or not data or not features:
            logger.error("Required modules not available")
            return 1
        
        logger.info(f"Running discovery for {args.pair}")
        
        if args.data:
            df = data.DataLoader().load_csv(args.data)
        else:
            logger.error("Data file required")
            return 1
        
        df = data.clean_ohlcv_data(df)
        df = features.engineer_features_for_timeframe(df, use_discovery=False)[0]
        
        disc = discovery.Discovery()
        discovered = disc.discover_indicators(df)
        
        top = list(discovered.values())[:args.top]
        for ind in top:
            logger.info(f"  {ind.name}: {ind.composite_score():.4f} (wr={ind.win_rate:.2%})")
        
        return 0
    except Exception as e:
        logger.error(f"Discovery failed: {e}", exc_info=args.verbose)
        return 1


def handle_system_command(args: argparse.Namespace) -> int:
    """Handle system command"""
    try:
        if args.system_command == 'info':
            info = get_system_info()
            logger.info(f"System Info:")
            logger.info(f"  Version: {info['version']}")
            logger.info(f"  Author: {info['author']}")
            logger.info(f"  Python: {info['python_version'].split()[0]}")
            loaded = sum(1 for v in info['modules'].values() if v)
            total = len(info['modules'])
            logger.info(f"  Modules: {loaded}/{total} loaded")
            return 0
        
        elif args.system_command == 'verify':
            if verify_modules():
                logger.info("All modules verified")
                return 0
            else:
                logger.error("Module verification failed")
                return 1
        
        elif args.system_command == 'errors':
            errors = get_module_errors()
            if errors:
                logger.error("Module loading errors:")
                for module, error in errors.items():
                    logger.error(f"  {module}: {error}")
                return 1
            else:
                logger.info("No module errors")
                return 0
        
        return 1
    except Exception as e:
        logger.error(f"System command failed: {e}")
        return 1


def run_command(args: argparse.Namespace) -> int:
    """Run CLI command"""
    try:
        if args.quiet:
            logging.getLogger().setLevel(logging.ERROR)
        elif args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)

        logger.info(f"Trading AI System v{__version__}")

        if args.command == 'discovery':
            return handle_discovery_command(args)
        
        elif args.command == 'system':
            return handle_system_command(args)
        
        elif args.command == 'backtest':
            logger.info(f"Backtest: {args.pair}")
            try:
                from cli.commands import BacktestCommand
                cmd = BacktestCommand(args)
                return cmd.execute()
            except ImportError:
                logger.error("Backtest command not available")
                return 1

        elif args.command == 'train':
            logger.info(f"Training: {args.model}")
            initialize_system(
                enable_discovery=getattr(args, 'enable_discovery', False),
                enable_caching=getattr(args, 'enable_caching', False),
            )
            try:
                from cli.commands import TrainCommand
                cmd = TrainCommand(args)
                return cmd.execute()
            except ImportError:
                logger.error("Train command not available")
                return 1

        elif args.command == 'live':
            logger.info(f"Live trading: {args.pair}")
            try:
                from cli.commands import LiveCommand
                cmd = LiveCommand(args)
                return cmd.execute()
            except ImportError:
                logger.error("Live command not available")
                return 1

        elif args.command == 'data':
            try:
                from cli.commands import DataCommand
                cmd = DataCommand(args)
                return cmd.execute()
            except ImportError:
                logger.error("Data command not available")
                return 1

        elif args.command == 'config':
            try:
                from cli.commands import ConfigCommand
                cmd = ConfigCommand(args)
                return cmd.execute()
            except ImportError:
                logger.error("Config command not available")
                return 1

        elif args.command == 'analysis':
            try:
                from cli.commands import AnalysisCommand
                cmd = AnalysisCommand(args)
                return cmd.execute()
            except ImportError:
                logger.error("Analysis command not available")
                return 1

        else:
            logger.error(f"Unknown command: {args.command}")
            return 1

    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        return 130
    except Exception as e:
        logger.error(f"Command failed: {e}", exc_info=getattr(args, 'verbose', False))
        return 1


def main() -> int:
    """Main entry point"""
    try:
        if len(sys.argv) == 1:
            return run_interactive_menu()

        parser = create_parser()
        args = parser.parse_args()

        if not args.command:
            return run_interactive_menu()

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
